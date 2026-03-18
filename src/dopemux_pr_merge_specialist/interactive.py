"""Interactive Merge Wizard — operator-facing interactive terminal UI.

Implements the spaceage cockpit layout with 8 UX components rendered via
RichTerminalRenderer.  Gracefully degrades to PLAIN/COMPACT modes.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .closed_loop_engine import ClosedLoopEngine
from .strategy_library import STRATEGY_LIBRARY
from .ux_engine import RenderMode, RichTerminalRenderer, detect_render_mode

try:
    from rich.layout import Layout as _RLayout
    from rich.live import Live as _RLive
    from rich.panel import Panel as _RPanel
    from rich.text import Text as _RText

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class InteractiveMergeWizard:
    """Interactive PR Merge Wizard.

    Renders a spaceage cockpit using 8 UX components from RichTerminalRenderer.
    Falls back gracefully to PLAIN mode when Rich is unavailable or TTY is absent.
    """

    def __init__(self, manager: Any, mode: Optional[RenderMode] = None):
        self.manager = manager
        if mode is None:
            mode = detect_render_mode()
        self.mode = mode
        self.ux = RichTerminalRenderer(mode=mode)
        # Ops engine reference (set by run() if available)
        self.ops: Optional[Any] = getattr(manager, "ops_engine", None)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Launch the interactive wizard."""
        # Auto-pilot bypass
        auto_pilot = getattr(self, "auto_pilot", False)
        focus_pr_id = getattr(self, "focus_pr_id", None)
        
        if auto_pilot:
            if focus_pr_id:
                self._render_pr(str(focus_pr_id))
            else:
                # Process all PRs from queue
                print("📡 Auto-pilot scanning queue...")
                try:
                    from .remediation_orchestrator import RemediationOrchestrator
                    orchestrator = RemediationOrchestrator(self.manager)
                    # Use a dummy scan if no direct method, or just get list from manager
                    prs = getattr(self.manager, "fetch_open_prs", lambda x: [])(10)
                    for pr in prs:
                        pr_id = str(pr.get("number"))
                        print(f"🎯 Auto-pilot focusing on PR #{pr_id}")
                        self._render_pr(pr_id)
                        time.sleep(2)
                except Exception as e:
                    print(f"Auto-pilot error: {e}")
            return

        # Use full RICH cockpit if possible
        if RICH_AVAILABLE and self.mode in (RenderMode.RICH, RenderMode.FULL):
            self._run_rich()
        else:
            self._run_plain()

    # ------------------------------------------------------------------
    # Rich cockpit mode
    # ------------------------------------------------------------------

    def _run_rich(self) -> None:
        """Render the full Rich cockpit layout."""
        print("\n🚀 PR Merge Specialist — Interactive Cockpit")
        print("=" * 60)

        # Prompt for PR ID
        try:
            pr_id = input("Enter PR ID (number or 'q' to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return

        if pr_id.lower() in ("q", "quit", "exit", ""):
            print("Exiting.")
            return

        self._render_pr(pr_id)

    def _render_pr(self, pr_id: str) -> None:
        """Fetch and render a single PR."""
        report = self._fetch_report(pr_id)
        if report is None:
            print(f"Could not load report for PR #{pr_id}.")
            return

        # --- Closed-loop cycle (monitoring health panel) ---
        loop_trace = None
        if self.ops and isinstance(self.ops, type(self.ops)):
            try:
                from .ops_engine import FlightDeckOpsEngine

                if isinstance(self.ops, FlightDeckOpsEngine):
                    loop_engine = ClosedLoopEngine(self.ops, STRATEGY_LIBRARY)
                    report_dict = report.to_dict() if hasattr(report, "to_dict") else {}
                    loop_trace = loop_engine.run_cycle(pr_id, report_dict)
                    print(
                        f"\n[CLOSED-LOOP] Cycle complete. Next tactic: {loop_trace.next_tactic} | Posture: {loop_trace.posture}"
                    )
            except Exception as _e:
                pass  # Non-fatal; degrade gracefully

        # 1. Mission header card (replaces plain header)
        state = getattr(report, "status", "UNKNOWN").upper()
        confidence = ""
        if hasattr(report, "consensus_decision") and report.consensus_decision:
            confidence = str(getattr(report.consensus_decision, "confidence", ""))

        posture = "GO_SUPERVISED_ONLY"
        strategy_label = ""
        if hasattr(report, "consensus_decision") and report.consensus_decision:
            strategy_label = getattr(report.consensus_decision, "merge_strategy", "")

        mission_line = getattr(report, "status_reason", "Awaiting operator decision.")
        repo = self._get_repo()
        risk = self._get_risk(report)

        header_obj = self.ux.mission_header_card(
            pr_id=pr_id,
            repo=repo,
            state=state,
            posture=posture,
            risk=risk,
            confidence=confidence,
            mission_line=mission_line,
            return_obj=True,
        )
        if (
            RICH_AVAILABLE
            and header_obj is not None
            and not isinstance(header_obj, str)
        ):
            from rich.console import Console

            Console().print(header_obj)
        else:
            print(header_obj or "")

        # 2. Strategy comparison table
        if strategy_label and STRATEGY_LIBRARY:
            strat_obj = self.ux.strategy_comparison_table(
                STRATEGY_LIBRARY, strategy_label, return_obj=True
            )
            if (
                RICH_AVAILABLE
                and strat_obj is not None
                and not isinstance(strat_obj, str)
            ):
                from rich.console import Console

                Console().print(strat_obj)
            else:
                print(strat_obj or "")

        # 3. Blocker table
        blockers = getattr(report, "blockers", [])
        if blockers:
            blocker_obj = self.ux.blocker_table(blockers, return_obj=True)
            if (
                RICH_AVAILABLE
                and blocker_obj is not None
                and not isinstance(blocker_obj, str)
            ):
                from rich.console import Console

                Console().print(blocker_obj)
            else:
                print(blocker_obj or "")

        # 4. Stage progress rail (from flow_trace)
        flow_trace = getattr(report, "remediation_flow_trace", None)
        if flow_trace and getattr(flow_trace, "stages", None):
            self.ux.stage_progress_rail(flow_trace.stages)

        # 5. Signoff panel (latest signoff from ops for this PR)
        if self.ops:
            signoff_entry = self._latest_signoff(pr_id)
            if signoff_entry:
                self.ux.signoff_panel(
                    action_class=signoff_entry.get("action", "UNKNOWN"),
                    required=True,
                    owner=signoff_entry.get("operator", "operator"),
                    state="APPROVED",
                    last_timestamp=str(signoff_entry.get("ts", "")),
                )

        # 6. Next action card — prefer closed-loop tactic when available
        next_action = self._derive_next_action(report)
        if loop_trace is not None and loop_trace.next_tactic != "DEFER":
            # Overlay loop-selected tactic into next action reason
            if next_action is None:
                next_action = {
                    "command": "queue-scan",
                    "reason": f"Loop tactic: {loop_trace.next_tactic}",
                    "severity": "INFO",
                }
            else:
                next_action["reason"] = (
                    f"[{loop_trace.next_tactic}] {next_action['reason']}"
                )
        if next_action:
            self.ux.next_action_card(
                command=next_action["command"],
                reason=next_action["reason"],
                severity=next_action["severity"],
            )

    # ------------------------------------------------------------------
    # Plain fallback mode
    # ------------------------------------------------------------------

    def _run_plain(self) -> None:
        """Plain text interactive mode."""
        print("\n=== PR Merge Specialist — Interactive Mode ===")
        try:
            pr_id = input("Enter PR ID (number or 'q' to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return

        if pr_id.lower() in ("q", "quit", "exit", ""):
            print("Exiting.")
            return

        self._render_pr(pr_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_report(self, pr_id: str) -> Optional[Any]:
        """Fetch a remediation report for the given PR ID."""
        try:
            from .remediation_orchestrator import RemediationOrchestrator

            run_id = time.strftime("%Y%m%d_%H%M%S")
            orchestrator = RemediationOrchestrator(self.manager)
            return orchestrator.run_flow(pr_id, run_id)
        except Exception as e:
            print(f"Warning: could not fetch report for PR #{pr_id}: {e}")
            return None

    def _get_repo(self) -> str:
        """Get repo name from manager."""
        owner = getattr(self.manager, "_owner", "")
        repo = getattr(self.manager, "_repo", "")
        if owner and repo:
            return f"{owner}/{repo}"
        return "unknown/repo"

    def _get_risk(self, report: Any) -> str:
        """Derive risk label from report."""
        if not report:
            return "UNKNOWN"
        blockers = getattr(report, "blockers", [])
        if not blockers:
            return "LOW"
        severities = []
        for b in blockers:
            if hasattr(b, "type"):
                t = b.type
            else:
                t = b.get("type", "")
            if t in ("CI_FAIL", "CONFLICTS", "POLICY_BLOCK"):
                severities.append("HIGH")
            elif t in ("MISSING_APPROVALS",):
                severities.append("MEDIUM")
        if "HIGH" in severities:
            return "HIGH"
        if "MEDIUM" in severities:
            return "MEDIUM"
        return "LOW"

    def _latest_signoff(self, pr_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent signoff entry for this PR."""
        if not self.ops:
            return None
        signoffs = getattr(self.ops, "signoff_log", [])
        matching = [s for s in signoffs if s.get("pr_id") == pr_id]
        return matching[-1] if matching else None

    def _derive_next_action(self, report: Any) -> Optional[Dict[str, str]]:
        """Derive the most important next action from report."""
        if not report:
            return None
        status = getattr(report, "status", "")
        if status == "merge_ready":
            return {
                "command": "pr-fix --id {pr_id} --tier 1",
                "reason": "PR is ready for merge queue.",
                "severity": "LOW",
            }
        elif status == "blocked":
            blockers = getattr(report, "blockers", [])
            if blockers:
                b = blockers[0]
                desc = (
                    getattr(b, "description", b.get("description", ""))
                    if isinstance(b, dict)
                    else b.description
                )
                return {
                    "command": "queue-scan",
                    "reason": f"Resolve blocker: {desc[:60]}",
                    "severity": "HIGH",
                }
        return {
            "command": "queue-scan",
            "reason": "Review PR queue.",
            "severity": "INFO",
        }
