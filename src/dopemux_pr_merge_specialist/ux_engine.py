import sys
from enum import Enum, auto
from typing import Any, Dict, List, Mapping, Optional

from rich.console import Console
from dopemux.ui.theme import DOPEMUX_THEME


class RenderMode(Enum):
    RICH = auto()
    FULL = auto()
    COMPACT = auto()
    PLAIN = auto()


def detect_render_mode() -> RenderMode:
    """Determine the best rendering mode based on terminal capabilities."""
    if not sys.stdout.isatty():
        return RenderMode.PLAIN


VALIDATION_BLOCKER_TYPES = {"validation_not_executed", "required_check_pending"}


def dashboard_status_kind(snapshot: Mapping[str, Any]) -> str:
    blockers = {
        str(item.get("type") or item.get("finding_type") or "")
        for item in (snapshot.get("blockers") or [])
        if isinstance(item, Mapping)
    }
    lifecycle_state = str(snapshot.get("lifecycle_state") or "").upper()
    operator_state = str(snapshot.get("operator_state") or "")
    mergeable = str(snapshot.get("mergeable") or "").upper()
    merge_state_status = str(snapshot.get("merge_state_status") or "").upper()

    if bool(snapshot.get("is_draft")):
        return "draft"
    if operator_state == "queued_for_merge" or lifecycle_state == "QUEUED_FOR_MERGE":
        return "queued"
    if blockers == {"approval_missing"}:
        return "approval_required"
    if blockers and blockers <= VALIDATION_BLOCKER_TYPES:
        return "validation_pending"
    if mergeable == "CONFLICTING" or merge_state_status in {"DIRTY", "HAS_HOOKS"}:
        return "conflict"
    if "MERGED" in lifecycle_state:
        return "merged"
    if "READY" in lifecycle_state:
        return "ready"
    if "BLOCKED" in lifecycle_state:
        return "blocked"
    return "pending"


def dashboard_status_icon(snapshot: Mapping[str, Any]) -> str:
    status = dashboard_status_kind(snapshot)
    return {
        "draft": "📝",
        "queued": "🔵",
        "approval_required": "🟣",
        "validation_pending": "🟡",
        "conflict": "🔴",
        "blocked": "🔴",
        "ready": "🟢",
        "merged": "🟢",
        "pending": "⏳",
    }.get(status, "⏳")

    # Check for Rich support
    try:

        console = Console()
        if console.width < 80:
            return RenderMode.COMPACT
        return RenderMode.RICH
    except ImportError:
        return RenderMode.PLAIN


class TerminalRenderer:
    """Base class for all terminal output."""

    def __init__(self, mode: Optional[RenderMode] = None):
        self.mode = mode or detect_render_mode()

    def print_header(self, text: str):
        pass

    def print_success(self, text: str):
        print(f"✅ {text}")

    def print_error(self, text: str):
        print(f"❌ {text}")

    def print_warning(self, text: str):
        print(f"⚠️ {text}")

    def print_info(self, text: str):
        print(f"ℹ️ {text}")


class RichTerminalRenderer(TerminalRenderer):
    """Advanced UI rendering using the Rich library."""

    def __init__(self, mode: Optional[RenderMode] = None):
        super().__init__(mode)

        self.console = Console(theme=DOPEMUX_THEME)

    def print_header(self, text: str):
        from rich.panel import Panel

        self.console.print(Panel(text, style="bold cyan", border_style="cyan"))

    def print_success(self, text: str):
        self.console.print(f"[bold green]✅ {text}[/bold green]")

    def print_error(self, text: str):
        self.console.print(f"[bold red]❌ {text}[/bold red]")

    def print_warning(self, text: str):
        self.console.print(f"[yellow]⚠️ {text}[/yellow]")

    def print_info(self, text: str):
        self.console.print(f"[blue]ℹ️ {text}[/blue]")

    def next_action_card(self, command: str, reason: str, severity: str):
        """Render the next recommended action."""
        from rich.panel import Panel
        from rich.text import Text

        color = (
            "red"
            if severity == "HIGH"
            else "yellow" if severity == "MEDIUM" else "green"
        )
        content = Text.assemble(
            ("COMMAND : ", "bold cyan"),
            f"{command}\n",
            ("REASON  : ", "bold cyan"),
            reason,
        )
        print(Panel(content, title="NEXT ACTION", border_style=color))

    def render_dashboard_layout(self, state: Any, console: Optional[Console] = None) -> Any:
        """Assemble the entire Grand Dashboard layout using rich.layout.Layout."""
        from rich.layout import Layout
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        from rich.align import Align
        import time

        con = console or self.console
        term_height = con.height

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        
        # Header
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        
        title = Text.assemble(
            ("🚀 ", "bold warning"),
            ("DOPEMUX ", "heading"),
            ("PR-MERGE ", "magenta"),
            ("GRAND ORCHESTRATOR", "text.emphasis")
        )
        
        elapsed = int(time.time() - state.start_time)
        timer = Text(f"MISSION TIME: {elapsed//60:02d}:{elapsed%60:02d}", style="text.dim")
        grid.add_row(title, timer)
        layout["header"].update(Panel(grid, style="on surface.black"))

        # Body
        layout["body"].split_row(
            Layout(name="queue", ratio=2),
            Layout(name="cockpit", ratio=3)
        )

        # Queue Table with Viewport logic
        table = Table(expand=True, box=None)
        table.add_column("PR#", style="mint", width=6)
        table.add_column("Title", ratio=1, no_wrap=True, overflow="ellipsis")
        table.add_column("Status", justify="center")

        # Deduct space for header (3), footer (3), panel borders (2), and some padding
        max_visible = max(5, term_height - 12)

        total_prs = len(state.prs)
        
        start_idx = 0
        if total_prs > max_visible:
            start_idx = max(0, state.active_index - (max_visible // 2))
            if start_idx + max_visible > total_prs:
                start_idx = total_prs - max_visible
        
        end_idx = min(total_prs, start_idx + max_visible)

        for i in range(start_idx, end_idx):
            pr = state.prs[i]
            is_active = i == state.active_index
            row_style = "bold text.emphasis on surface.navy" if is_active else "text.dim"
            
            status_icon = dashboard_status_icon(pr)
            
            table.add_row(
                f"{'> ' if is_active else '  '}{pr.get('pr_id', '???')}",
                pr.get("title", "Unknown Title"),
                status_icon,
                style=row_style
            )
        
        q_title = f"[ QUEUE STATUS ({total_prs}) ]"
        if total_prs > max_visible:
            q_title = f"[ QUEUE STATUS ({start_idx+1}-{end_idx} of {total_prs}) ]"
            
        layout["queue"].update(Panel(table, title=q_title, border_style="mint"))

        # Cockpit
        active = state.active_pr
        if active:
            cockpit = Layout()
            cockpit.split_column(
                Layout(name="top", ratio=3),
                Layout(name="middle", size=3),
                Layout(name="bottom", ratio=2)
            )
            cockpit["top"].split_row(
                Layout(name="intel", ratio=3),
                Layout(name="blockers", ratio=2)
            )
            
            # Intel
            intel_text = Text()
            intel_text.append(f"#{active.get('pr_id')} | ", style="mint")
            intel_text.append(f"{active.get('title', 'Unknown')[:60]}...\n", style="text")
            intel_text.append(f"STRATEGY : {active.get('merge_strategy', 'MECHANICAL')}\n", style="magenta")
            intel_text.append(f"RATIONALE: {active.get('rationale', 'Standard rebase.')[:150]}...", style="text.dim")
            cockpit["top"]["intel"].update(Panel(intel_text, title="MISSION INTEL", border_style="magenta"))
            
            # Blockers & Warnings -> Tactical Checklist
            blocker_text = Text()
            blockers = active.get("blockers", [])
            warnings = active.get("warnings", [])
            history = active.get("history", [])
            blocker_types = {
                str(item.get("type") or item.get("finding_type") or "")
                for item in blockers
                if isinstance(item, dict)
            }
            approval_blocked = blocker_types == {"approval_missing"}
            validation_only_blocked = bool(blocker_types) and blocker_types <= VALIDATION_BLOCKER_TYPES
            queued_for_merge = (
                str(active.get("operator_state", "")) == "queued_for_merge"
                or str(active.get("lifecycle_state", "")).upper() == "QUEUED_FOR_MERGE"
            )
            
            # 1. CI Status
            ci = active.get("ci_status", "UNKNOWN")
            if ci == "SUCCESS":
                blocker_text.append("✅ CI Checks Passed\n", style="success")
            elif ci == "PENDING":
                blocker_text.append("⏳ CI Checks Pending\n", style="warning")
            else:
                blocker_text.append("❌ CI Checks Failed\n", style="error")

            # 1.5 Approval status
            review_decision = str(active.get("review_decision", "") or "")
            if approval_blocked:
                blocker_text.append("🟣 Approval Required\n", style="magenta")
            elif review_decision == "APPROVED":
                blocker_text.append("✅ Approval Satisfied\n", style="success")
            elif review_decision == "CHANGES_REQUESTED":
                blocker_text.append("❌ Changes Requested\n", style="error")
                
            # 2. Local Validation
            v_report = active.get("validation_report", {})
            v_status = v_report.get("status", "NOT_EXECUTED").upper() if isinstance(v_report, dict) else "NOT_EXECUTED"
            if "PASSED" in v_status:
                blocker_text.append("✅ Local Validation Passed\n", style="success")
            elif "FAILED" in v_status:
                blocker_text.append("❌ Local Validation Failed\n", style="error")
            else:
                blocker_text.append("⏳ Local Validation Pending\n", style="text.dim")

            if queued_for_merge:
                blocker_text.append("🔵 Auto-merge Queued\n", style="info")
                
            # 3. Conflicts
            mergeable = str(active.get("mergeable", "")).upper()
            state_status = str(active.get("merge_state_status", "")).upper()
            if mergeable == "CONFLICTING" or state_status in ("DIRTY", "HAS_HOOKS"):
                blocker_text.append("❌ Merge Conflicts\n", style="error")
            else:
                blocker_text.append("✅ No Merge Conflicts\n", style="success")
                
            # 4. Threads
            threads = active.get("unresolved_threads", 0)
            if threads == 0:
                blocker_text.append("✅ All Threads Resolved\n", style="success")
            else:
                blocker_text.append(f"❌ {threads} Unresolved Threads\n", style="error")
                
            # 5. Draft Status
            if active.get("is_draft"):
                blocker_text.append("❌ PR is Draft\n", style="warning")
                
            # Other blockers
            other_blockers = [b for b in blockers if b.get("type") not in ("validation_not_executed", "required_check_pending", "required_check_failed", "active_thread", "conflict_detected", "draft_pr")]
            if other_blockers:
                blocker_text.append("\n⚠️ Other Blockers:\n", style="warning")
                for b in other_blockers[:2]:
                    b_name = b.get('name', b.get('type', 'Blocker'))
                    blocker_text.append(f"  • {b_name[:40]}\n", style="error")

            if history:
                blocker_text.append("\n📜 MISSION HISTORY:\n", style="bold info")
                for h in history[-2:]:
                    blocker_text.append(f"  • {h.get('event')} ", style="text.dim")
                    blocker_text.append(f"({h.get('timestamp')})\n", style="text.dim")
            
            cockpit["top"]["blockers"].update(Panel(blocker_text, title="TACTICAL INSIGHTS", border_style="error" if blockers else "success"))

            # Middle row: Integrated Metrics & Stats
            middle_grid = Table.grid(expand=True)
            middle_grid.add_column(ratio=1)
            middle_grid.add_column(ratio=1)
            middle_grid.add_column(ratio=1)
            middle_grid.add_column(ratio=1)
            
            ci = active.get("ci_status", "UNKNOWN")
            ci_text = Text.assemble(("CI: ", "bold"), (ci, "success" if ci == "SUCCESS" else "error" if ci == "FAILURE" else "warning"))
            
            v_report = active.get("validation_report", {})
            v_status = v_report.get("status", "NOT_EXECUTED").upper() if isinstance(v_report, dict) else "NOT_EXECUTED"
            v_text = Text.assemble(("VERIFY: ", "bold"), (v_status, "success" if "PASSED" in v_status else "error" if "FAILED" in v_status else "text.dim"))
            
            threads_text = Text.assemble(("THREADS: ", "bold"), (f"{active.get('unresolved_threads', 0)}", "info"))
            
            is_draft = bool(active.get("is_draft", False))
            draft_text = Text.assemble(("DRAFT: ", "bold"), ("YES" if is_draft else "NO", "warning" if is_draft else "text.dim"))
            
            middle_grid.add_row(Align.center(ci_text), Align.center(v_text), Align.center(threads_text), Align.center(draft_text))
            cockpit["middle"].update(Panel(middle_grid, title="SYSTEM METRICS", border_style="info"))

            # Bottom row: Objective or Execution Log
            log_text = Text()
            execution_log = getattr(state, "execution_log", [])
            if not execution_log:
                lc_state = str(active.get("lifecycle_state", "discovered")).upper()
                obj_text = Text()
                if is_draft:
                    obj_text.append("🎯 OBJECTIVE: Transition PR out of DRAFT mode.\n", style="bold warning")
                    obj_text.append("NEXT STEP: Press [R] to mark as READY FOR REVIEW.", style="text")
                elif queued_for_merge:
                    obj_text.append("🎯 OBJECTIVE: Wait for GitHub to complete queued auto-merge.\n", style="bold info")
                    obj_text.append("NEXT STEP: No local verification needed here; monitor checks/queue state.", style="text")
                elif approval_blocked:
                    obj_text.append("🎯 OBJECTIVE: Satisfy the missing approval gate.\n", style="bold magenta")
                    obj_text.append("NEXT STEP: Press [A] to approve. Auto-merge should proceed after approval if all other gates stay green.", style="text")
                elif validation_only_blocked:
                    obj_text.append("🎯 OBJECTIVE: Run local verification before merge readiness.\n", style="bold warning")
                    obj_text.append("NEXT STEP: Press [V] to execute validation. Merge follows only after validation passes.", style="text")
                elif "READY" in lc_state:
                    obj_text.append("🎯 OBJECTIVE: Final sign-off and integration.\n", style="bold success")
                    obj_text.append("NEXT STEP: Press [A] to Approve or [I] to Implement Merge.", style="text")
                elif "THREAD" in lc_state or "COMMENT" in lc_state:
                    obj_text.append("🎯 OBJECTIVE: Resolve outstanding reviewer feedback.\n", style="bold warning")
                    obj_text.append("NEXT STEP: Press [T] to review threads or [P] to auto-patch trivial suggestions.", style="text")
                elif "CONFLICT" in lc_state:
                    obj_text.append("🎯 OBJECTIVE: Reconcile branch divergence.\n", style="bold error")
                    obj_text.append("NEXT STEP: Press [I] to launch the Fusion Engine.", style="text")
                elif "MERGED" in lc_state:
                    obj_text.append("🏁 MISSION ACCOMPLISHED\n", style="bold success")
                    obj_text.append("PR has been successfully integrated.", style="text")
                else:
                    obj_text.append(f"🎯 OBJECTIVE: Advance PR from {lc_state} state.\n", style="bold info")
                    obj_text.append("NEXT STEP: Perform system verification [V] to refresh state.", style="text")
                
                cockpit["bottom"].update(Panel(obj_text, title="MISSION OBJECTIVE", border_style="info"))
            else:
                for step in execution_log[-5:]:
                    s_type = step.get("type", "INFO")
                    s_msg = step.get("message", "")
                    s_ts = step.get("timestamp", "")
                    color = "success" if s_type == "SUCCESS" else "error" if s_type == "ERROR" else "warning" if s_type == "START" else "text"
                    log_text.append(f"[{s_ts}] {s_msg}\n", style=color)
                
                cockpit["bottom"].update(Panel(log_text, title="EXECUTION LOG", border_style="warning"))
            
            layout["cockpit"].update(cockpit)
        else:
            layout["cockpit"].update(
                Panel("No PR selected", border_style="text.disabled")
            )

        # Footer
        controls = Text.assemble(
            ("[A] ", "bold info"), "Approve  ",
            ("[B] ", "bold info"), "Bulk Approve  ",
            ("[R] ", "bold success"), "Ready  ",
            ("[P] ", "bold magenta"), "Patch  ",
            ("[I] ", "bold warning"), "Implement  ",
            ("[T] ", "bold info"), "Threads  ",
            ("[V] ", "bold success"), "Verify  ",
            ("[S] ", "bold text"), "Skip  ",
            ("[X] ", "bold orange"), "Auto-Pilot  ",
            ("[Q] ", "bold error"), "Quit"
        )
        footer_grid = Table.grid(expand=True)
        
        ap_status = Text("AUTO-PILOT: ", style="bold")
        if getattr(state, "auto_pilot", False):
            ap_status.append("ENGAGED", style="blink bold success")
        else:
            ap_status.append("DISENGAGED", style="text.disabled")

        footer_grid.add_row(
            controls,
            Align.right(
                Text.assemble(
                    ap_status,
                    ("  |  ", "text.disabled"),
                    (state.status_message, "italic text.disabled")
                )
            ),
        )
        layout["footer"].update(
            Panel(
                footer_grid,
                title="TACTICAL CONTROLS",
                border_style="text.disabled",
            )
        )

        return layout
