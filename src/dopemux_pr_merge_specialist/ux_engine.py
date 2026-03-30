import sys
from enum import Enum, auto
from typing import Any, Mapping, Optional

from rich.console import Console


from .action_model import (
    blocker_types_from_snapshot,
    is_passive_queued_state,
    validation_status_from_snapshot,
)


VALIDATION_BLOCKER_TYPES = {"validation_not_executed", "validation_failed"}


def dashboard_status_kind(snapshot: Mapping[str, Any]) -> str:
    """Return a stable status classifier for dashboard rows."""
    blockers = blocker_types_from_snapshot(snapshot)
    validation_status = validation_status_from_snapshot(snapshot)
    ci_status = str(snapshot.get("ci_status", "") or "").upper()

    if is_passive_queued_state(snapshot):
        return "queued"
    if "approval_missing" in blockers:
        return "approval_required"
    if validation_status == "failed" or "validation_failed" in blockers:
        return "validation_failed"
    if validation_status == "not_executed" or "validation_not_executed" in blockers:
        return "validation_pending"
    if ci_status == "FAILURE" or "required_check_failed" in blockers:
        return "ci_failed"
    if str(snapshot.get("mergeable", "")).upper() == "CONFLICTING":
        return "conflicting"
    return "ready"


def dashboard_status_icon(snapshot: Mapping[str, Any]) -> str:
    """Map dashboard row status to the icon the TUI expects."""
    return {
        "approval_required": "🟣",
        "queued": "🔵",
        "validation_failed": "🔴",
        "validation_pending": "🟡",
        "ci_failed": "❌",
        "conflicting": "⚔️",
        "ready": "✅",
    }.get(dashboard_status_kind(snapshot), "⚪")


class RenderMode(Enum):
    RICH = auto()
    FULL = auto()
    COMPACT = auto()
    PLAIN = auto()


def detect_render_mode() -> RenderMode:
    """Determine the best rendering mode based on terminal capabilities."""
    if not sys.stdout.isatty():
        return RenderMode.PLAIN
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

        try:
            from dopemux.ui.theme import DOPEMUX_THEME
            self.console = Console(theme=DOPEMUX_THEME)
        except ImportError:
            self.console = Console()

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
        layout["header"].update(Panel(grid, style="bg.black"))

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
            row_style = "row.active" if is_active else "text.dim"
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
            queue_plan = getattr(state, "queue_plan", {}) or {}
            ordered_ids = [
                int(pr_id)
                for pr_id in queue_plan.get("ordered_pr_ids", [])
                if str(pr_id).isdigit()
            ]
            active_id = int(active.get("pr_id", 0) or 0)
            if not ordered_ids:
                ordered_ids = [
                    int(pr.get("pr_id", 0) or 0)
                    for pr in state.prs
                    if pr.get("pr_id") is not None
                ]
            queue_position = (
                ordered_ids.index(active_id) + 1
                if active_id in ordered_ids
                else state.active_index + 1
            )
            active_layer = None
            for layer in queue_plan.get("layers", []):
                pr_ids = {
                    int(pr_id) for pr_id in layer.get("pr_ids", []) if str(pr_id).isdigit()
                }
                if active_id in pr_ids:
                    active_layer = layer.get("layer")
                    break
            next_ids = ordered_ids[queue_position:queue_position + 3]
            active_phase = getattr(state, "active_phase", "Monitor")
            train_progress = getattr(state, "train_progress", {}) or {}
            ordering_strategy = (
                queue_plan.get("autopilot_strategy")
                or queue_plan.get("strategy")
                or "hybrid"
            )
            advanced_strategy = str(
                active.get("advanced_strategy_name")
                or active.get("advanced_strategy_id")
                or "UNSPECIFIED"
            )
            advanced_reason = str(active.get("advanced_strategy_reason") or "")
            advanced_steps = list(active.get("advanced_strategy_steps") or [])
            intel_text.append(f"#{active.get('pr_id')} | ", style="mint")
            intel_text.append(f"{active.get('title', 'Unknown')[:60]}...\n", style="text")
            intel_text.append(f"PHASE    : {active_phase}\n", style="info")
            intel_text.append(
                f"ORDERING : {str(ordering_strategy).upper()}\n",
                style="magenta",
            )
            intel_text.append(f"ADVANCED : {advanced_strategy}\n", style="magenta")
            intel_text.append(
                f"QUEUE    : {queue_position}/{max(len(ordered_ids), len(state.prs))}",
                style="text",
            )
            if active_layer is not None:
                intel_text.append(f" | LAYER {active_layer}", style="mint")
            if queue_plan.get("cycle_detected"):
                intel_text.append(" | CYCLE DETECTED", style="warning")
            intel_text.append("\n")
            if next_ids:
                intel_text.append(
                    f"NEXT     : {' -> '.join(f'#{pr_id}' for pr_id in next_ids)}\n",
                    style="text.dim",
                )
            if advanced_reason:
                intel_text.append(
                    f"WHY      : {advanced_reason[:150]}\n",
                    style="text.dim",
                )
            if advanced_steps:
                intel_text.append(
                    f"STEPS    : {' -> '.join(advanced_steps)}\n",
                    style="info",
                )
            intel_text.append(f"STRATEGY : {active.get('merge_strategy', 'MECHANICAL')}\n", style="magenta")
            intel_text.append(f"RATIONALE: {active.get('rationale', 'Standard rebase.')[:150]}...", style="text.dim")
            if train_progress:
                train_status = str(train_progress.get("status", "active")).upper()
                intel_text.append(f"\nTRAIN    : {train_status}\n", style="warning")
                candidate_ids = train_progress.get("candidate_pr_ids", [])[:5]
                if candidate_ids:
                    intel_text.append(
                        f"CANDIDATES: {' '.join(f'#{pr_id}' for pr_id in candidate_ids)}\n",
                        style="text.dim",
                    )
                merged_ids = train_progress.get("merged_pr_ids", [])
                if merged_ids:
                    intel_text.append(
                        f"MERGED   : {' '.join(f'#{pr_id}' for pr_id in merged_ids)}\n",
                        style="success",
                    )
                queued_ids = train_progress.get("queued_pr_ids", [])
                if queued_ids:
                    intel_text.append(
                        f"QUEUED   : {' '.join(f'#{pr_id}' for pr_id in queued_ids)}\n",
                        style="info",
                    )
            cockpit["top"]["intel"].update(Panel(intel_text, title="MISSION INTEL", border_style="magenta"))
            
            # Blockers & Warnings -> Tactical Checklist
            blocker_text = Text()
            blockers = active.get("blockers", [])
            history = active.get("history", [])
            blocker_types = {
                str(item.get("type") or item.get("finding_type") or "")
                for item in blockers
                if isinstance(item, dict)
            }
            operator_state = str(active.get("operator_state", "") or "")
            approval_blocked = blocker_types == {"approval_missing"}
            validation_only_blocked = bool(blocker_types) and blocker_types <= VALIDATION_BLOCKER_TYPES
            queued_for_merge = (
                operator_state == "queued_for_merge"
                or str(active.get("lifecycle_state", "")).upper() == "QUEUED_FOR_MERGE"
            )
            
            ci = active.get("ci_status", "UNKNOWN")
            if ci == "SUCCESS":
                blocker_text.append("✅ CI Checks Passed\n", style="success")
            elif ci == "PENDING":
                blocker_text.append("⏳ CI Checks Pending\n", style="warning")
            else:
                blocker_text.append("❌ CI Checks Failed\n", style="error")

            review_decision = str(active.get("review_decision", "") or "")
            if approval_blocked:
                blocker_text.append("🟣 Approval Required\n", style="magenta")
            elif review_decision == "APPROVED":
                blocker_text.append("✅ Approval Satisfied\n", style="success")
            elif review_decision == "CHANGES_REQUESTED":
                blocker_text.append("❌ Changes Requested\n", style="error")
                
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
                
            mergeable = str(active.get("mergeable", "")).upper()
            state_status = str(active.get("merge_state_status", "")).upper()
            if mergeable == "CONFLICTING" or state_status in ("DIRTY", "HAS_HOOKS"):
                blocker_text.append("❌ Merge Conflicts\n", style="error")
            else:
                blocker_text.append("✅ No Merge Conflicts\n", style="success")
                
            threads_count = active.get("unresolved_threads", 0)
            if threads_count == 0:
                blocker_text.append("✅ All Threads Resolved\n", style="success")
            else:
                blocker_text.append(f"❌ {threads_count} Unresolved Threads\n", style="error")
                
            if active.get("is_draft"):
                blocker_text.append("❌ PR is Draft\n", style="warning")
                
            other_blockers = [b for b in blockers if b.get("type") not in ("validation_not_executed", "required_check_pending", "required_check_failed", "active_thread", "conflict_detected", "draft_pr")]
            if other_blockers:
                blocker_text.append("\n⚠️ Other Blockers:\n", style="warning")
                for b in other_blockers[:2]:
                    label = (
                        str(b.get("message") or "")
                        or str(b.get("name") or "")
                        or str(b.get("type") or "Blocker")
                    )
                    blocker_text.append(f"  • {label}\n", style="error")

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
            resolved_session = state.resolved_threads_in_session if hasattr(state, "resolved_threads_in_session") else 0
            if resolved_session > 0:
                threads_text.append(f" (+{resolved_session})", style="success")
            blockers_metric = Text.assemble(
                ("BLOCKERS: ", "bold"),
                (str(len(blockers)), "error" if blockers else "success"),
            )
            middle_grid.add_row(ci_text, v_text, threads_text, blockers_metric)
            cockpit["middle"].update(
                Panel(middle_grid, title="MISSION METRICS", border_style="text.disabled")
            )

            obj_text = Text()
            is_draft = bool(active.get("is_draft"))
            lc_state = str(active.get("lifecycle_state", "")).upper()
            semantic_conflict = any(
                str(item.get("type") or item.get("finding_type") or "") == "conflict_detected"
                and str(item.get("scope") or item.get("category") or "").lower() == "semantic"
                for item in blockers
                if isinstance(item, dict)
            )
            conflict_blocked = mergeable == "CONFLICTING" or state_status in ("DIRTY", "HAS_HOOKS")

            if resolved_session > 0:
                obj_text.append(
                    f"✅ Resolved {resolved_session} thread(s) in this session.\n",
                    style="success",
                )

            if validation_only_blocked and v_status == "NOT_EXECUTED":
                obj_text.append(
                    "🎯 OBJECTIVE: Run local verification to clear validation blockers.\n",
                    style="bold warning",
                )
                obj_text.append(
                    "NEXT STEP: Press [V] to execute verification and refresh blocker state.",
                    style="text",
                )
            elif is_draft:
                obj_text.append("🎯 OBJECTIVE: Transition PR out of DRAFT mode.\n", style="bold warning")
                obj_text.append("NEXT STEP: Press [R] to mark as READY FOR REVIEW.", style="text")
            elif queued_for_merge:
                obj_text.append("🎯 OBJECTIVE: Wait for GitHub to complete queued auto-merge.\n", style="bold info")
                obj_text.append("NEXT STEP: No local verification needed here; monitor checks/queue state.", style="text")
            elif semantic_conflict:
                obj_text.append("🎯 OBJECTIVE: Defer semantic conflict to human review.\n", style="bold error")
                obj_text.append("NEXT STEP: Resolve manually or remove the `conflict:semantic` label only after confirming the conflict is mechanically safe.", style="text")
            elif conflict_blocked:
                obj_text.append("🎯 OBJECTIVE: Decide whether conflict recovery is safe.\n", style="bold error")
                obj_text.append("NEXT STEP: Add `conflict:mechanical` only for safe docs/tests/lockfile conflicts, otherwise resolve manually.", style="text")
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
                obj_text.append(
                    f"🎯 OBJECTIVE: Advance PR from {lc_state or 'UNKNOWN'} state.\n",
                    style="bold info",
                )
                obj_text.append(
                    "NEXT STEP: Perform system verification [V] to refresh state.",
                    style="text",
                )

            cockpit["bottom"].update(
                Panel(obj_text, title="MISSION OBJECTIVE", border_style="info")
            )
            layout["cockpit"].update(cockpit)
        else:
            layout["cockpit"].update(
                Panel(
                    Text("No active PR selected.", style="text.dim"),
                    title="MISSION OBJECTIVE",
                    border_style="text.disabled",
                )
            )

        controls = Text.assemble(
            ("[A] ", "bold info"), "Approve  ",
            ("[B] ", "bold cyan"), "Bulk Approve  ",
            ("[C] ", "bold warning"), "Remediate  ",
            ("[F] ", "bold error"), "Fix  ",
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
