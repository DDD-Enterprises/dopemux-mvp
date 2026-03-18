from __future__ import annotations

import argparse
import select
import sys
import termios
import time
import tty
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from rich.console import Console
from rich.layout import Layout
from rich.live import Live

from .ux_engine import RenderMode, RichTerminalRenderer
from .queue_drain import pr_apply, pr_merge, pr_approve, pr_ready


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
        self.console = Console()
        self.state: Optional[QueueState] = None
        self._live: Optional[Live] = None

    def render(self) -> Any:
        """Assemble the entire Grand Dashboard layout."""
        if hasattr(self.ux, "render_dashboard_layout"):
            return self.ux.render_dashboard_layout(self.state)
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

    def _execute_tactic(self, tactic: str, pr_id: str) -> Optional[Dict[str, Any]]:
        """Execute the actual logic for a tactic and return updated data."""
        if not self.args:
            return None
            
        self.state.execution_log = []
        cmd_args = argparse.Namespace(**{**vars(self.args), "id": pr_id, "execute": True})
        
        try:
            result = None
            if tactic == "P":
                self.log_step(f"ENGAGING PATCH ENGINE: PR #{pr_id}", "START")
                result = pr_apply(cmd_args, progress_callback=self.log_step)
                self.log_step("Patch Engine finished.", "SUCCESS")
                self.state.status_message = f"Patch complete for PR #{pr_id}."
                    
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
                self.state.last_action_result = result.lifecycle_state
                # Preserve history if it exists
                history = self.state.prs[self.state.active_index].get("history", [])
                
                return {
                    "pr_id": result.pr_state.pr_id,
                    "title": result.pr_state.title,
                    "lifecycle_state": result.lifecycle_state,
                    "ci_status": getattr(result.pr_state, "ci_status", "UNKNOWN"),
                    "unresolved_threads": getattr(result.pr_state, "unresolved_threads", 0),
                    "risk_score": getattr(result.pr_state, "risk_score", 0.0),
                    "is_draft": getattr(result.pr_state, "is_draft", False),
                    "history": history,
                    "merge_strategy": result.merge_decision.action if result.merge_decision else "UNKNOWN",
                    "rationale": result.merge_decision.reason if result.merge_decision else "",
                    "blockers": [b.to_dict() for b in result.findings if str(b.kind) == "blocker"],
                    "warnings": [b.to_dict() for b in result.findings if str(b.kind) == "warning"],
                }
        except Exception as e:
            self.log_step(f"CRITICAL EXECUTION ERROR", "ERROR")
            self.log_step(f"REASON: {str(e)[:150]}", "ERROR")
            self.state.status_message = f"Error executing {tactic}."
            self.state.last_action_result = "ERROR"
            time.sleep(2)
        return None

    def run(self, pr_queue: List[Dict[str, Any]], run_id: str):
        """Run the persistent dashboard loop."""
        self.state = QueueState(run_id=run_id, prs=pr_queue)

        if sys.stdin.isatty():
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
        else:
            old_settings = None

        try:
            if old_settings:
                tty.setcbreak(fd)

            with Live(self.render(), console=self.console, screen=False, auto_refresh=True) as live:
                self._live = live
                while True:
                    live.update(self.render())
                    if not old_settings: break

                    timeout = 0.5 if not self.state.auto_pilot else 2.5
                    rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                    
                    choice = None
                    if rlist:
                        char = sys.stdin.read(1)
                        if char == '\x1b':
                            next_char = sys.stdin.read(2)
                            if next_char == "[A": choice = "UP"
                            elif next_char == "[B": choice = "DOWN"
                        else:
                            choice = char.upper()
                    elif self.state.auto_pilot:
                        active = self.state.active_pr
                        if active:
                            lc_state = str(active.get("lifecycle_state", "discovered")).upper()
                            unresolved = int(active.get("unresolved_threads", 0))
                            is_draft = bool(active.get("is_draft", False))
                            
                            if is_draft:
                                choice = "R"
                            elif "READY" in lc_state or active.get("merge_strategy") == "auto_merge_fallback":
                                choice = "I"
                            elif unresolved > 0:
                                choice = "P"
                            elif "CONFLICT" in lc_state:
                                choice = "S"
                            else:
                                choice = "V"

                    if choice == "Q":
                        self.state.status_message = "Mission aborted by operator."
                        break
                    elif choice == "X":
                        self.state.auto_pilot = not self.state.auto_pilot
                        self.state.status_message = f"AUTO-PILOT: {'ENGAGED' if self.state.auto_pilot else 'DISENGAGED'}"
                    elif choice == "B": # BULK APPROVE
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
                    elif choice in ("A", "P", "I", "T", "V", "R"):
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
            if old_settings:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        self.console.print("\n[bold green]MISSION COMPLETE. FLIGHT DATA SAVED TO PROOF BUNDLE. 🛰️[/bold green]")
