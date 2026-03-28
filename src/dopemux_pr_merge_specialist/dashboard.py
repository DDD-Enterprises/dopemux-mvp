from __future__ import annotations

import argparse
import difflib
import json
import os
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
from .strategy_library import STRATEGY_LIBRARY
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
    queue_scan_internal,
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
    autopilot_strategy: str = ""
    autopilot_stall_counts: Dict[str, int] = field(default_factory=dict)
    exit_outcome: str = "running"
    exit_reason: str = ""

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

    def _set_exit_state(self, outcome: str, reason: str) -> None:
        if not self.state:
            return
        self.state.exit_outcome = outcome
        self.state.exit_reason = reason
        self.state.status_message = reason

    def _mission_banner(self) -> tuple[str, str]:
        if not self.state:
            return ("MISSION ENDED. NO DASHBOARD STATE AVAILABLE.", "yellow")

        outcome = str(self.state.exit_outcome or "running")
        reason = str(self.state.exit_reason or self.state.status_message or "").strip()
        if outcome == "complete":
            return (
                "MISSION COMPLETE. FLIGHT DATA SAVED TO PROOF BUNDLE.",
                "green",
            )
        if outcome == "aborted":
            return (
                f"MISSION ABORTED. {reason or 'Operator ended the session.'} FLIGHT DATA SAVED TO PROOF BUNDLE.",
                "yellow",
            )
        if outcome == "detached":
            return (
                f"MISSION ENDED EARLY. {reason or 'Interactive input was unavailable.'} FLIGHT DATA SAVED TO PROOF BUNDLE.",
                "yellow",
            )
        return (
            f"MISSION ENDED WITHOUT COMPLETION. {reason or 'Queue processing stopped before merge completion.'} FLIGHT DATA SAVED TO PROOF BUNDLE.",
            "yellow",
        )

    def _default_queue_plan(self, pr_queue: List[Dict[str, Any]]) -> Dict[str, Any]:
        ordered_ids = [int(pr.get("pr_id")) for pr in pr_queue if pr.get("pr_id") is not None]
        return {
            "ordered_pr_ids": ordered_ids,
            "layers": [{"layer": 0, "pr_ids": ordered_ids}],
            "edges": {},
            "cycle_detected": False,
            "strategy": getattr(self.args, "strategy", "hybrid"),
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

    def _load_ordering_plan(self) -> Dict[str, Any]:
        _, queue_dir, _ = build_run_paths(self.args.out_dir, self.state.run_id)
        ordering_plan_path = queue_dir / "ORDERING_PLAN.json"
        if ordering_plan_path.exists():
            return json.loads(ordering_plan_path.read_text(encoding="utf-8"))
        return self._default_queue_plan(self.state.prs)

    def _candidate_tactics_for_snapshot(self, snapshot: Dict[str, Any]) -> List[str]:
        blockers = {
            str(item.get("type") or item.get("finding_type") or "")
            for item in snapshot.get("blockers", [])
            if isinstance(item, dict)
        }
        operator_state = str(snapshot.get("operator_state", "") or "")
        conflict_blocked = (
            bool(blockers & {"manual_conflict_required", "semantic_conflict_blocked"})
            or operator_state in {"manual_conflict_required", "semantic_conflict_blocked"}
        )
        tactics: List[str] = []
        if bool(snapshot.get("is_draft")):
            tactics.append("R")
        if "approval_missing" in blockers:
            tactics.append("A")
        if "validation_failed" in blockers:
            tactics.append("F")
        if "required_check_failed" in blockers or str(
            snapshot.get("ci_status", "")
        ).upper() == "FAILURE":
            tactics.append("C")
        if (
            int(snapshot.get("unresolved_threads", 0) or 0) > 0
            or "active_thread" in blockers
        ):
            tactics.append("T")
        if (
            "conflict_detected" in blockers
            or str(snapshot.get("mergeable", "")).upper() == "CONFLICTING"
            or str(snapshot.get("merge_state_status", "")).upper() in {"DIRTY", "HAS_HOOKS"}
        ) and not conflict_blocked:
            tactics.append("P")
        if blockers & {"validation_not_executed", "required_check_pending"}:
            tactics.append("V")
        allowed = set(snapshot.get("allowed_actions", []) or [])
        if "APPLY_FIX" in allowed:
            tactics.append("P")
        if "MERGE" in allowed:
            tactics.append("I")
        if "READY" in allowed:
            tactics.append("R")
        if "APPROVE" in allowed:
            tactics.append("A")
        seen = set()
        ordered = []
        for tactic in tactics:
            if tactic not in seen:
                ordered.append(tactic)
                seen.add(tactic)
        return ordered

    def _select_advanced_strategy(
        self, snapshot: Dict[str, Any], *, queue_plan: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str, List[str]]:
        blockers = {
            str(item.get("type") or item.get("finding_type") or "")
            for item in snapshot.get("blockers", [])
            if isinstance(item, dict)
        }
        unresolved_threads = int(snapshot.get("unresolved_threads", 0) or 0)
        ci_status = str(snapshot.get("ci_status", "")).upper()
        validation_status = str(
            (snapshot.get("validation_report") or {}).get("status", "")
        ).lower()
        mergeable = str(snapshot.get("mergeable", "")).upper()
        merge_state_status = str(snapshot.get("merge_state_status", "")).upper()
        operator_state = str(snapshot.get("operator_state", "") or "")
        layer = None
        pr_id = int(snapshot.get("pr_id", 0) or 0)
        plan = queue_plan or {}
        for item in plan.get("layers", []):
            pr_ids = {int(pid) for pid in item.get("pr_ids", []) if str(pid).isdigit()}
            if pr_id in pr_ids:
                layer = int(item.get("layer", 0) or 0)
                break

        if (
            "semantic_conflict_blocked" in blockers
            or operator_state == "semantic_conflict_blocked"
        ):
            return (
                "SPLIT_DECISION_REQUIRED",
                "Conflict surface is explicitly marked semantic; skip autopilot patching and require human resolution.",
                ["S"],
            )
        if (
            "manual_conflict_required" in blockers
            or operator_state == "manual_conflict_required"
        ):
            return (
                "SPLIT_DECISION_REQUIRED",
                "Conflict auto-recovery requires explicit opt-in before patching can run safely.",
                ["S"],
            )
        if mergeable == "CONFLICTING" or merge_state_status in {"DIRTY", "HAS_HOOKS"}:
            return (
                "STAGED_SEQUENCE_MERGE",
                "Conflict or branch divergence detected; use staged remediation before merge.",
                ["P", "T", "V", "A", "I"],
            )
        if ci_status == "FAILURE" or "required_check_failed" in blockers or validation_status == "failed":
            return (
                "PATCH_ISOLATION_PLAN",
                "Broken validation or CI should be isolated and repaired before broader actions.",
                ["F", "C", "P", "V", "A", "I"],
            )
        if unresolved_threads > 0 or "active_thread" in blockers:
            return (
                "OURS_THEN_PORT_SELECTIVE",
                "Reviewer deltas can be ported onto the current branch before verification.",
                ["T", "P", "V", "A", "I"],
            )
        if layer is not None and layer > 0:
            return (
                "STAGED_SEQUENCE_MERGE",
                "Stacked PR position requires ordered integration through queue layers.",
                ["V", "A", "I"],
            )
        return (
            "PATCH_ISOLATION_PLAN",
            "Default to the smallest safe change set and verify before merge.",
            ["V", "A", "I"],
        )

    def _decorate_snapshots_with_strategy(
        self, pr_queue: List[Dict[str, Any]], queue_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        decorated = []
        for snapshot in pr_queue:
            strategy_id, rationale, steps = self._select_advanced_strategy(
                snapshot, queue_plan=queue_plan
            )
            strategy = STRATEGY_LIBRARY.get(strategy_id)
            enriched = dict(snapshot)
            enriched["advanced_strategy_id"] = strategy_id
            enriched["advanced_strategy_name"] = (
                strategy.name if strategy is not None else strategy_id
            )
            enriched["advanced_strategy_reason"] = rationale
            enriched["advanced_strategy_steps"] = steps
            decorated.append(enriched)
        return decorated

    def _autopilot_tactic_for_snapshot(self, snapshot: Dict[str, Any]) -> str:
        steps = snapshot.get("advanced_strategy_steps") or []
        candidates = set(self._candidate_tactics_for_snapshot(snapshot))
        for tactic in steps:
            if tactic in candidates:
                return tactic
        return dashboard_tactic_for_snapshot(snapshot)

    def _set_queue_state(
        self,
        pr_queue: List[Dict[str, Any]],
        ordering_plan: Dict[str, Any],
        *,
        preserve_pr_id: Optional[int] = None,
        prefer_top: bool = False,
    ) -> None:
        queue_plan = dict(ordering_plan or self._default_queue_plan(pr_queue))
        if self.state.autopilot_strategy:
            queue_plan["autopilot_strategy"] = self.state.autopilot_strategy
        self.state.queue_plan = queue_plan
        self.state.prs = self._decorate_snapshots_with_strategy(pr_queue, queue_plan)
        if not pr_queue:
            self.state.active_index = 0
        elif prefer_top:
            self.state.active_index = 0
        elif preserve_pr_id is not None:
            for index, snapshot in enumerate(pr_queue):
                if int(snapshot.get("pr_id", 0) or 0) == preserve_pr_id:
                    self.state.active_index = index
                    break
            else:
                self.state.active_index = 0
        else:
            self.state.active_index = 0
        self._sync_active_phase()

    def _choose_autopilot_strategy(self, pr_queue: List[Dict[str, Any]]) -> tuple[str, str]:
        head_refs = {
            str(pr.get("head_ref") or "")
            for pr in pr_queue
            if pr.get("head_ref")
        }
        has_stack = any(
            str(pr.get("base_ref") or "") in head_refs
            for pr in pr_queue
            if pr.get("base_ref")
        )
        if len(pr_queue) <= 3 and not has_stack:
            return (
                "simple",
                "small independent queue detected; prioritize direct sequencing.",
            )
        return (
            "hybrid",
            "stacked or larger queue detected; use DAG/WSEMT prioritization.",
        )

    def _refresh_queue_state(
        self, *, strategy_override: Optional[str] = None, prefer_top: bool = False
    ) -> bool:
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
        scan_args = argparse.Namespace(**vars(self.args))
        if strategy_override:
            scan_args.strategy = strategy_override
        preserve_pr_id = (
            None if prefer_top or self.state.active_pr is None else int(self.state.active_pr.get("pr_id", 0) or 0)
        )
        results = queue_scan_internal(scan_args, client, policy, self.state.run_id)
        pr_queue = [result_to_dashboard_entry(result) for result in results]
        ordering_plan = self._load_ordering_plan()
        ordering_plan["strategy"] = getattr(scan_args, "strategy", getattr(self.args, "strategy", "hybrid"))
        self._set_queue_state(
            pr_queue,
            ordering_plan,
            preserve_pr_id=preserve_pr_id,
            prefer_top=prefer_top,
        )
        return bool(pr_queue)

    def _engage_autopilot(self) -> None:
        strategy, reason = self._choose_autopilot_strategy(self.state.prs)
        self.state.autopilot_strategy = strategy
        self.state.auto_pilot = True
        self.state.active_phase = "Assessment"
        self.log_step(
            f"AUTOPILOT ASSESSMENT: selecting {strategy.upper()} queue strategy; {reason}",
            "START",
        )
        has_queue = self._refresh_queue_state(strategy_override=strategy, prefer_top=True)
        ordered_ids = self.state.queue_plan.get("ordered_pr_ids", [])
        if has_queue and ordered_ids:
            sequence = " -> ".join(f"#{pr_id}" for pr_id in ordered_ids[:5])
            self.log_step(f"Autopilot sequence: {sequence}", "INFO")
            if self.state.active_pr:
                self.log_step(
                    f"Autopilot strategy for PR #{self.state.active_pr.get('pr_id')}: {self.state.active_pr.get('advanced_strategy_name')}."
                    f" {self.state.active_pr.get('advanced_strategy_reason')}",
                    "INFO",
                )
        self.state.status_message = f"AUTO-PILOT: ENGAGED ({strategy.upper()})"

    def _reassess_autopilot_after_action(
        self, *, target_pr_id: str, initial_state: Any, initial_tactic: str
    ) -> None:
        strategy = self.state.autopilot_strategy or getattr(
            self.args, "strategy", "hybrid"
        )
        self._refresh_queue_state(strategy_override=strategy, prefer_top=True)
        active = self.state.active_pr
        if not active:
            self.state.status_message = "Autopilot: queue exhausted after reassessment."
            return
        active_pr_id = str(active.get("pr_id"))
        new_state = active.get("lifecycle_state")
        new_tactic = self._autopilot_tactic_for_snapshot(active)
        if (
            active_pr_id == str(target_pr_id)
            and self.state.last_action_result == "ERROR"
        ) or (
            active_pr_id == str(target_pr_id)
            and new_state == initial_state
            and new_tactic == initial_tactic
        ):
            self.state.autopilot_stall_counts[active_pr_id] = (
                self.state.autopilot_stall_counts.get(active_pr_id, 0) + 1
            )
            if len(self.state.prs) > 1:
                self.state.active_index = (self.state.active_index + 1) % len(
                    self.state.prs
                )
                self._sync_active_phase()
                next_pr_id = self.state.active_pr.get("pr_id")
                self.state.status_message = (
                    f"Autopilot: PR #{target_pr_id} stalled under {initial_tactic}; advancing to PR #{next_pr_id}."
                )
            else:
                self.state.status_message = (
                    f"Autopilot: PR #{target_pr_id} remains blocked under {initial_tactic}."
                )
            return
        self.state.autopilot_stall_counts.pop(str(target_pr_id), None)
        self.state.status_message = (
            f"Autopilot: reassessed queue using {strategy.upper()} strategy."
        )

    def _decode_input_choice(self, char: str) -> Optional[str]:
        if char in {"\x03", "\x04"}:
            return "Q"
        if char == "\x1b":
            if self._input_fd is None:
                return "Q"
            suffix = ""
            deadline = time.monotonic() + 0.2
            while len(suffix) < 8 and time.monotonic() < deadline:
                timeout = max(0.0, min(0.05, deadline - time.monotonic()))
                rlist, _, _ = select.select([self._input_fd], [], [], timeout)
                if not rlist:
                    break
                suffix += os.read(self._input_fd, 1).decode(
                    "utf-8", errors="ignore"
                )
                if suffix.startswith("O") and len(suffix) >= 2 and suffix[-1:].isalpha():
                    break
                if suffix.startswith("[") and len(suffix) >= 2 and (
                    suffix[-1:].isalpha() or suffix.endswith("~")
                ):
                    break
            if not suffix:
                return "Q"
            if suffix[0] in {"[", "O"}:
                if suffix.endswith("A"):
                    return "UP"
                if suffix.endswith("B"):
                    return "DOWN"
            return None
        return char.upper()

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
                        self._set_exit_state(
                            "detached",
                            "Interactive input is unavailable; dashboard exited before queue completion.",
                        )
                        break

                    timeout = 0.5 if not self.state.auto_pilot else 2.5
                    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                    
                    choice = None
                    if rlist:
                        char = sys.stdin.read(1)
                        choice = self._decode_input_choice(char)
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
                                self._refresh_queue_state(
                                    strategy_override=self.state.autopilot_strategy
                                    or getattr(self.args, "strategy", "hybrid"),
                                    prefer_top=True,
                                )
                                time.sleep(2)
                                continue

                        active = self.state.active_pr
                        if active:
                            self.state.active_phase = dashboard_phase_for_snapshot(active)
                            choice = self._autopilot_tactic_for_snapshot(active)

                    if choice == "Q":
                        self._set_exit_state("aborted", "Mission aborted by operator.")
                        break
                    elif choice == "X":
                        if self.state.auto_pilot:
                            self.state.auto_pilot = False
                            self.state.autopilot_strategy = ""
                            self.state.train_progress = {}
                            self.state.status_message = "AUTO-PILOT: DISENGAGED"
                        else:
                            self._engage_autopilot()
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
                        initial_tactic = choice
                        
                        updated_pr = self._execute_tactic(choice, active_pr_id)
                        
                        if updated_pr:
                            self.state.prs[self.state.active_index] = updated_pr
                            live.update(self.render())
                        
                        if self.state.auto_pilot:
                            time.sleep(3.0)
                            self._reassess_autopilot_after_action(
                                target_pr_id=active_pr_id,
                                initial_state=initial_state,
                                initial_tactic=initial_tactic,
                            )
        finally:
            self._restore_terminal_mode()

        banner, color = self._mission_banner()
        self.console.print(f"\n[bold {color}]{banner}[/bold {color}]")
