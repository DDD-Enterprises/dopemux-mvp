from __future__ import annotations

import argparse
import difflib
import select
import sys
import termios
import time
import tty
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from dopemux.ui.theme import DOPEMUX_THEME

from .action_model import (
    dashboard_phase_for_snapshot,
    dashboard_tactic_for_snapshot,
    result_to_dashboard_entry,
)
from .metrics import MetricsEngine
from .plan_builder import build_plan_result
from .preflight import preflight
from .schema import PRMergeReport, PRResult, ValidationReport, ValidationStatus
from .thread_resolution import latest_comment
from .ux_engine import RenderMode, RichTerminalRenderer
from .conflict import apply_suggestion_to_file
from .queue_drain import (
    GitHubClient,
    _ignite_speculative_train,
    _inflate_pr_result,
    _load_pr_context,
    _refresh_client_state,
    build_run_paths,
    cleanup_worktree,
    load_effective_policy,
    pr_apply,
    pr_approve,
    pr_merge,
    pr_ready,
    prepare_worktree,
    stage_and_push_if_needed,
)


@dataclass
class QueueState:
    """State of the entire PR queue for the dashboard."""

    run_id: str
    prs: List[Dict[str, Any]] = field(default_factory=list)
    active_index: int = 0
    status_message: str = "Ready for mission orders."
    start_time: float = field(default_factory=time.time)
    auto_pilot: bool = False
    execution_log: List[Dict[str, str]] = field(default_factory=list)
    last_action_result: Optional[str] = None
    resolved_threads_in_session: int = 0
    queue_plan: Dict[str, Any] = field(default_factory=dict)
    active_phase: str = "Monitor"
    train_progress: Dict[str, Any] = field(default_factory=dict)

    @property
    def active_pr(self) -> Optional[Dict[str, Any]]:
        if 0 <= self.active_index < len(self.prs):
            return self.prs[self.active_index]
        return None


class DopemuxDashboard:
    """Persistent, live-updating Grand Orchestrator Dashboard."""

    def __init__(
        self,
        manager: Any,
        args: Optional[argparse.Namespace] = None,
        policy: Optional[Dict[str, Any]] = None,
    ):
        self.manager = manager
        self.args = args
        self.policy = policy
        self.ux = RichTerminalRenderer(mode=RenderMode.RICH)
        self.console = Console(theme=DOPEMUX_THEME)
        self.metrics = MetricsEngine(Path("proof/pr_merge/metrics"))
        self.state: Optional[QueueState] = None
        self._live: Optional[Live] = None
        self._input_fd: Optional[int] = None
        self._terminal_settings: Optional[List[Any]] = None

    def render(self) -> Any:
        """Assemble the entire Grand Dashboard layout."""
        if hasattr(self.ux, "render_dashboard_layout"):
            return self.ux.render_dashboard_layout(self.state, console=self.console)
        return Layout()

    def log_step(self, message: str, step_type: str = "INFO"):
        """Add a step to the execution log and update display."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.state.execution_log.append({
            "timestamp": ts,
            "type": step_type,
            "message": message
        })
        if self._live:
            self._live.update(self.render())

    def _default_queue_plan(self, pr_queue: List[Dict[str, Any]]) -> Dict[str, Any]:
        ordered_ids = [int(pr.get("pr_id")) for pr in pr_queue if pr.get("pr_id") is not None]
        return {
            "ordered_pr_ids": ordered_ids,
            "layers": [{"layer": 0, "pr_ids": ordered_ids}],
            "edges": {},
            "cycle_detected": False,
        }

    def _restore_terminal_mode(self) -> None:
        if self._input_fd is not None and self._terminal_settings is not None:
            termios.tcsetattr(
                self._input_fd, termios.TCSADRAIN, self._terminal_settings
            )

    def _enter_cbreak_mode(self) -> None:
        if self._input_fd is not None and self._terminal_settings is not None:
            tty.setcbreak(self._input_fd)

    @contextmanager
    def _paused_live_prompt(self):
        if self._live:
            self._live.stop()
        self._restore_terminal_mode()
        try:
            yield
        finally:
            self._enter_cbreak_mode()
            if self._live:
                self._live.start()
                self._live.update(self.render())

    def _validation_report_from_snapshot(
        self, snapshot: Optional[Dict[str, Any]]
    ) -> ValidationReport:
        report = snapshot.get("validation_report") if snapshot else {}
        if not isinstance(report, dict):
            report = {}
        raw_status = str(
            report.get("status", ValidationStatus.NOT_EXECUTED.value)
        ).lower()
        status = ValidationStatus(raw_status)
        steps = [
            {
                "name": str(item.get("name", "")),
                "command": str(item.get("command", "")),
                "status": str(item.get("status", "")),
                "returncode": item.get("returncode"),
                "stdout": str(item.get("stdout", "")),
                "stderr": str(item.get("stderr", "")),
            }
            for item in report.get("steps", [])
            if isinstance(item, dict)
        ]
        from .schema import ValidationStepResult

        return ValidationReport(
            status=status,
            required_for_merge_ready=bool(
                report.get("required_for_merge_ready", True)
            ),
            steps=[ValidationStepResult(**step) for step in steps],
            attempts=int(report.get("attempts", 0) or 0),
            remediation_applied=bool(report.get("remediation_applied", False)),
        )

    def _sync_active_phase(self) -> None:
        if self.state is None or self.state.active_pr is None:
            return
        self.state.active_phase = dashboard_phase_for_snapshot(self.state.active_pr)

    def _refresh_dashboard_result(self, pr_id: str) -> PRResult:
        repo_root = Path.cwd()
        policy = self.policy or load_effective_policy(
            repo_root, explicit_path=getattr(self.args, "policy", None)
        )
        client = self.manager
        if not isinstance(client, GitHubClient):
            client = GitHubClient(
                repo=getattr(self.args, "repo", None),
                repo_root=repo_root,
                policy=policy,
            )
        _raw, threads, pr, check_payload = _load_pr_context(
            client=client, pr_id=int(pr_id)
        )
        current_snapshot = self.state.active_pr if self.state else None
        validation_report = self._validation_report_from_snapshot(current_snapshot)
        return build_plan_result(
            active_run_id=self.state.run_id,
            pr=pr,
            threads=threads,
            check_payload=check_payload,
            validation_report=validation_report,
            policy=policy,
        )

    def _review_threads_interactively(self, pr_id: str) -> bool:
        """Interactively review and apply thread suggestions."""
        self.log_step(f"Starting interactive thread review for PR #{pr_id}...", "START")

        repo_root = Path.cwd()
        active_run_id = self.state.run_id
        policy = self.policy or load_effective_policy(
            repo_root, explicit_path=getattr(self.args, "policy", None)
        )
        client = self.manager
        if not isinstance(client, GitHubClient):
            client = GitHubClient(
                repo=getattr(self.args, "repo", None),
                repo_root=repo_root,
                policy=policy,
            )

        _, _, pr_root = build_run_paths(self.args.out_dir, active_run_id)
        pr_dir = pr_root / f"PR-{pr_id}"
        commands_log = pr_dir / "COMMANDS_RUN.txt"

        _raw, threads, pr, _ = _load_pr_context(client=client, pr_id=int(pr_id))
        unresolved = [t for t in threads if not t.is_resolved]
        if not unresolved:
            self.log_step("No unresolved threads found.", "SUCCESS")
            return False

        worktree_path, branch, err = prepare_worktree(
            repo_root=repo_root,
            pr_id=int(pr_id),
            active_run_id=active_run_id,
            commands_log=commands_log,
            policy=policy,
        )
        if err:
            self.log_step(f"Error preparing worktree: {err}", "ERROR")
            return False

        threads_resolved_count = 0
        try:
            for thread in unresolved:
                comment = latest_comment(thread)
                if not comment:
                    self.log_step(
                        f"Skipping thread {thread.id[:8]}: no latest comment payload.",
                        "INFO",
                    )
                    continue
                target = comment.path or thread.path or "<unknown>"
                preview = " ".join(comment.body.split())
                self.log_step(
                    f"Reviewing thread {thread.id[:8]} on {target}: {preview[:120]}",
                    "INFO",
                )

                ok, reason, new_text = apply_suggestion_to_file(
                    worktree_path=worktree_path,
                    thread=thread,
                    comment=comment,
                    base_ref=pr.base_ref,
                    policy=policy,
                    dry_run=True
                )

                if not ok or new_text is None:
                    self.log_step(f"Skipping thread {thread.id[:8]}: {reason}", "INFO")
                    continue

                orig_text = (worktree_path / target).read_text(encoding="utf-8")

                diff = "".join(difflib.unified_diff(
                    orig_text.splitlines(keepends=True),
                    new_text.splitlines(keepends=True),
                    fromfile=f"a/{target}",
                    tofile=f"b/{target}"
                ))

                info_panel = Panel(
                    Text.assemble(
                        ("COMMENT: ", "bold cyan"), f"{comment.body}\n",
                        ("AUTHOR : ", "bold"), f"{comment.author}\n",
                        ("FILE   : ", "bold"), f"{target}"
                    ),
                    title=f"THREAD {thread.id[:8]}",
                    border_style="magenta"
                )
                diff_syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)

                with self._paused_live_prompt():
                    self.console.print(info_panel)
                    self.console.print(
                        Panel(
                            diff_syntax,
                            title="PROPOSED CHANGE",
                            border_style="green",
                        )
                    )

                    try:
                        choice = input(
                            "\nApply this fix? [y]es, [n]o, [q]uit: "
                        ).strip().lower()
                    except (EOFError, KeyboardInterrupt):
                        choice = "q"
                        self.log_step(
                            "Interactive prompt interrupted; aborting thread review.",
                            "WARNING",
                        )

                if choice == "y":
                    applied, apply_reason, _ = apply_suggestion_to_file(
                        worktree_path=worktree_path,
                        thread=thread,
                        comment=comment,
                        base_ref=pr.base_ref,
                        policy=policy,
                        dry_run=False
                    )
                    if not applied:
                        self.log_step(
                            f"Failed to apply fix for thread {thread.id[:8]}: {apply_reason}",
                            "ERROR",
                        )
                        continue
                    threads_resolved_count += 1
                    self.log_step(
                        f"Applied fix for thread {thread.id[:8]}: {apply_reason}",
                        "SUCCESS",
                    )
                elif choice == "q":
                    self.log_step("Operator ended the thread review session.", "INFO")
                    break
                else:
                    self.log_step(f"Skipped thread {thread.id[:8]}", "INFO")

            if threads_resolved_count > 0:
                self.log_step(f"Pushing {threads_resolved_count} thread fixes...", "INFO")
                pushed = stage_and_push_if_needed(
                    worktree_path=worktree_path,
                    head_ref=pr.head_ref,
                    active_run_id=active_run_id,
                    pr_id=int(pr_id),
                    execute=True,
                    commands_log=commands_log,
                    policy=policy,
                )
                if pushed:
                    _refresh_client_state(client, int(pr_id))
                    self.state.resolved_threads_in_session += threads_resolved_count
                    return True
                self.log_step("Thread fixes were not pushed successfully.", "ERROR")
        finally:
            cleanup_worktree(
                repo_root=repo_root,
                worktree_path=worktree_path,
                branch=branch,
                commands_log=commands_log,
                policy=policy,
            )

        return False

    def _log_metrics(self, result: PRResult):
        """Translate PRResult to PRMergeReport and log to MetricsEngine."""
        report = PRMergeReport(
            pr_id=str(result.pr_state.pr_id),
            status=result.lifecycle_state,
            initial_state=result.pr_state,
            blockers=[b.as_blocker() for b in result.findings if hasattr(b, "as_blocker")],
            telemetry=result.decision_basis
        )
        self.metrics.log_event(
            report=report,
            resolved_threads=self.state.resolved_threads_in_session
        )

    def _execute_tactic(self, tactic: str, pr_id: str) -> Optional[Dict[str, Any]]:
        """Execute the actual logic for a tactic and return updated data."""
        if not self.args:
            return None
            
        self.state.execution_log = []
        cmd_args = argparse.Namespace(**{**vars(self.args), "id": pr_id, "execute": True, "allow_dirty": True})
        if preflight(cmd_args) != 0:
            self.log_step("EXECUTION BLOCKED BY PREFLIGHT", "ERROR")
            self.state.status_message = f"Preflight failed for PR #{pr_id}."
            self.state.last_action_result = "ERROR"
            return None
        
        try:
            result = None
            self.state.active_phase = {
                "A": "Approval",
                "C": "CI Remediation",
                "F": "Validation Remediation",
                "I": "Merge",
                "P": "Patch",
                "R": "Ready For Review",
                "T": "Thread Review",
                "V": "Verification",
            }.get(tactic, "Monitor")
            if tactic == "P":
                self.log_step(f"ENGAGING PATCH ENGINE: PR #{pr_id}", "START")
                result = pr_apply(cmd_args, progress_callback=self.log_step)
                self.log_step("Patch Engine finished.", "SUCCESS")
                self.state.status_message = f"Patch applied for PR #{pr_id}."
            
            elif tactic == "T":
                self.log_step(f"ENGAGING THREAD RESOLUTION: PR #{pr_id}", "START")
                changed = self._review_threads_interactively(pr_id)
                if changed:
                    self.log_step("Refreshing PR state from GitHub...", "INFO")
                    result = self._refresh_dashboard_result(pr_id)
                    self.log_step("Thread resolution sequence complete and pushed.", "SUCCESS")
                    self.state.status_message = f"Threads resolved for PR #{pr_id}."
                else:
                    self.log_step("No threads were modified.", "INFO")
                    self.state.status_message = f"Thread review finished for PR #{pr_id}."
                    result = self._refresh_dashboard_result(pr_id)

            elif tactic == "C":
                self.log_step(f"ENGAGING CI REMEDIATION: PR #{pr_id}", "START")
                self.log_step(
                    "Routing through pr-apply so CI remediation uses the specialist-backed validation path.",
                    "INFO",
                )
                result = pr_apply(cmd_args, progress_callback=self.log_step)
                self.log_step("CI Remediation agent cycle complete.", "SUCCESS")
                self.state.status_message = f"CI Remediation attempt finished for PR #{pr_id}."

            elif tactic == "F":
                self.log_step(f"ENGAGING VALIDATION FIX: PR #{pr_id}", "START")
                result = pr_apply(cmd_args, progress_callback=self.log_step)
                self.log_step("Validation fix attempt complete.", "SUCCESS")
                self.state.status_message = f"Validation remediation complete for PR #{pr_id}."
                    
            elif tactic == "I":
                self.log_step(f"ENGAGING MERGE ENGINE: PR #{pr_id}", "START")
                result = pr_merge(cmd_args, progress_callback=self.log_step)
                self.log_step("PR integrated or auto-merge enabled.", "SUCCESS")
                self.state.status_message = f"Merge action complete for PR #{pr_id}."

            elif tactic == "V":
                self.log_step(f"ENGAGING VERIFICATION: PR #{pr_id}", "START")
                result = pr_apply(cmd_args, progress_callback=self.log_step)
                self.log_step("Verification sequence complete.", "SUCCESS")
                self.state.status_message = f"Verification complete for PR #{pr_id}."
            
            elif tactic == "A":
                self.log_step(f"ENGAGING APPROVAL: PR #{pr_id}", "START")
                result = pr_approve(cmd_args, progress_callback=self.log_step)
                self.log_step("Approval process complete.", "SUCCESS")
                self.state.status_message = f"Approval action finished for PR #{pr_id}."
                
            elif tactic == "R":
                self.log_step(f"ENGAGING READY: PR #{pr_id}", "START")
                result = pr_ready(cmd_args, progress_callback=self.log_step)
                self.log_step("PR is now OPEN.", "SUCCESS")
                self.state.status_message = f"PR #{pr_id} marked as READY."
            else:
                self.log_step(f"Tactic [{tactic}] not yet dashboard-instrumented.", "INFO")
                time.sleep(1)
                
            if result:
                self._log_metrics(result)
                self.state.last_action_result = result.lifecycle_state
                # Preserve history if it exists
                history = self.state.active_pr.get("history", [])
                entry = result_to_dashboard_entry(result)
                entry["history"] = history
                self.state.active_phase = dashboard_phase_for_snapshot(entry)
                return entry
        except Exception as e:
            self.log_step("CRITICAL EXECUTION ERROR", "ERROR")
            self.log_step(f"REASON: {str(e)[:150]}", "ERROR")
            self.state.status_message = f"Error executing {tactic}."
            self.state.last_action_result = "ERROR"
            time.sleep(2)
        return None

    def run(
        self,
        pr_queue: List[Dict[str, Any]],
        run_id: str,
        ordering_plan: Optional[Dict[str, Any]] = None,
    ):
        """Run the persistent dashboard loop."""
        self.state = QueueState(
            run_id=run_id,
            prs=pr_queue,
            queue_plan=ordering_plan or self._default_queue_plan(pr_queue),
        )
        self._sync_active_phase()

        if sys.stdin.isatty():
            self._input_fd = sys.stdin.fileno()
            self._terminal_settings = termios.tcgetattr(self._input_fd)
        else:
            self._input_fd = None
            self._terminal_settings = None

        try:
            if self._terminal_settings is not None:
                self._enter_cbreak_mode()

            with Live(self.render(), console=self.console, screen=False, auto_refresh=True) as live:
                self._live = live
                while True:
                    live.update(self.render())
                    if self._terminal_settings is None:
                        break

                    timeout = 0.5 if not self.state.auto_pilot else 2.5
                    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                    
                    choice = None
                    if rlist:
                        char = sys.stdin.read(1)
                        if char == "\x1b":
                            next_char = sys.stdin.read(2)
                            if next_char == "[A":
                                choice = "UP"
                            elif next_char == "[B":
                                choice = "DOWN"
                        else:
                            choice = char.upper()
                    elif self.state.auto_pilot:
                        ready_pr_ids = [
                            int(pr["pr_id"])
                            for pr in self.state.prs
                            if pr.get("pr_id") is not None
                            and dashboard_tactic_for_snapshot(pr) in ("I", "R")
                        ]
                        ready_count = len(ready_pr_ids)
                        if ready_count >= 2:
                            self.state.active_phase = "Train Planning"
                            self.state.train_progress = {
                                "status": "planning",
                                "candidate_pr_ids": ready_pr_ids,
                            }
                            self.state.status_message = (
                                f"🚂 Autopilot: Train opportunity detected ({ready_count} PRs)..."
                            )
                            live.update(self.render())

                            results_to_train = [_inflate_pr_result(pr) for pr in self.state.prs]
                            repo_root = Path.cwd()
                            _, _, pr_root = build_run_paths(self.args.out_dir, self.state.run_id)
                            commands_log = pr_root / "AUTOPILOT_TRAIN_COMMANDS.txt"

                            train_merged, train_queued = _ignite_speculative_train(
                                results_to_train, self.manager, repo_root, self.state.run_id, commands_log, self.policy, True
                            )

                            if train_merged or train_queued:
                                self.state.train_progress = {
                                    "status": "active",
                                    "candidate_pr_ids": ready_pr_ids,
                                    "merged_pr_ids": train_merged,
                                    "queued_pr_ids": train_queued,
                                    "current_pr_id": self.state.active_pr.get("pr_id"),
                                }
                                self.state.status_message = (
                                    f"🚂 Train integration successful. {len(train_merged)+len(train_queued)} PRs moving."
                                )
                                time.sleep(2)
                                continue

                        active = self.state.active_pr
                        if active:
                            self.state.active_phase = dashboard_phase_for_snapshot(active)
                            choice = dashboard_tactic_for_snapshot(active)

                    if choice == "Q":
                        self.state.status_message = "Mission aborted by operator."
                        break
                    elif choice == "X":
                        self.state.auto_pilot = not self.state.auto_pilot
                        self.state.status_message = f"AUTO-PILOT: {'ENGAGED' if self.state.auto_pilot else 'DISENGAGED'}"
                    elif choice == "B":
                        self.state.status_message = "ENGAGING BULK APPROVAL..."
                        live.update(self.render())
                        for i, pr in enumerate(self.state.prs):
                            self.state.active_index = i
                            active_pr_id = str(pr.get('pr_id'))
                            self.state.status_message = f"Bulk: Approving PR #{active_pr_id}..."
                            updated = self._execute_tactic("A", active_pr_id)
                            if updated:
                                self.state.prs[i] = updated
                            live.update(self.render())
                            time.sleep(0.5)
                        self.state.status_message = "BULK APPROVAL COMPLETE."
                    elif choice in ("UP", "DOWN", "S"):
                        self.state.active_index = (self.state.active_index + (1 if choice != "UP" else -1)) % len(self.state.prs)
                        self.state.status_message = f"Cycled to PR #{self.state.active_pr.get('pr_id')}"
                        self.state.execution_log = []
                        self.state.last_action_result = None
                        self._sync_active_phase()
                    elif choice in ("A", "P", "I", "T", "V", "R", "C", "F"):
                        active_pr_id = str(self.state.active_pr.get('pr_id'))
                        initial_state = self.state.active_pr.get("lifecycle_state")
                        
                        updated_pr = self._execute_tactic(choice, active_pr_id)
                        
                        if updated_pr:
                            self.state.prs[self.state.active_index] = updated_pr
                            live.update(self.render())
                        
                        if self.state.auto_pilot:
                            time.sleep(3.0)
                            
                            new_state = updated_pr.get("lifecycle_state") if updated_pr else None
                            if new_state and "MERGED" in str(new_state).upper():
                                self.state.active_index = (self.state.active_index + 1) % len(self.state.prs)
                                self.state.status_message = f"Integrated PR #{active_pr_id}. Advancing."
                            elif self.state.last_action_result == "ERROR" or new_state == initial_state:
                                self.state.active_index = (self.state.active_index + 1) % len(self.state.prs)
                                self.state.status_message = f"PR #{active_pr_id} stalled. Advancing."
        finally:
            self._restore_terminal_mode()

        self.console.print("\n[bold green]MISSION COMPLETE. FLIGHT DATA SAVED TO PROOF BUNDLE. 🛰️[/bold green]")
