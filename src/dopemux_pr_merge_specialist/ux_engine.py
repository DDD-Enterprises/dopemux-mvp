import sys
from enum import Enum, auto
from typing import Any, Dict, List, Optional


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
        from rich.console import Console

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
        from rich.console import Console

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

    def render_dashboard_layout(self, state: Any) -> Any:
        """Assemble the entire Grand Dashboard layout using rich.layout.Layout."""
        from rich.layout import Layout
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text
        from rich.align import Align
        import time

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
            ("🚀 ", "bold yellow"),
            ("DOPEMUX ", "bold cyan"),
            ("PR-MERGE ", "bold magenta"),
            ("GRAND ORCHESTRATOR", "bold white")
        )
        
        elapsed = int(time.time() - state.start_time)
        timer = Text(f"MISSION TIME: {elapsed//60:02d}:{elapsed%60:02d}", style="dim yellow")
        grid.add_row(title, timer)
        layout["header"].update(Panel(grid, style="white on blue"))

        # Body
        layout["body"].split_row(
            Layout(name="queue", ratio=2),
            Layout(name="cockpit", ratio=3)
        )

        # Queue Table with Viewport logic
        table = Table(expand=True, box=None)
        table.add_column("PR#", style="bold cyan", width=6)
        table.add_column("Title", ratio=1)
        table.add_column("Status", justify="center")

        total_prs = len(state.prs)
        max_visible = 15
        
        start_idx = 0
        if total_prs > max_visible:
            start_idx = max(0, state.active_index - (max_visible // 2))
            if start_idx + max_visible > total_prs:
                start_idx = total_prs - max_visible
        
        end_idx = min(total_prs, start_idx + max_visible)

        for i in range(start_idx, end_idx):
            pr = state.prs[i]
            is_active = i == state.active_index
            row_style = "bold white on grey15" if is_active else "dim"
            
            step = str(pr.get("lifecycle_state", "discovered")).upper()
            is_draft = bool(pr.get("is_draft", False))
            
            if is_draft:
                status_icon = "📝"
            elif "READY" in step or "MERGED" in step:
                status_icon = "🟢"
            elif "BLOCKED" in step or "CONFLICT" in step:
                status_icon = "🔴"
            else:
                status_icon = "⏳"
            
            table.add_row(
                f"{'> ' if is_active else '  '}{pr.get('pr_id', '???')}",
                pr.get("title", "Unknown Title"),
                status_icon,
                style=row_style
            )
        
        q_title = f"[ QUEUE STATUS ({total_prs}) ]"
        if total_prs > max_visible:
            q_title = f"[ QUEUE STATUS ({start_idx+1}-{end_idx} of {total_prs}) ]"
            
        layout["queue"].update(Panel(table, title=q_title, border_style="cyan"))

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
                Layout(name="intel", ratio=2),
                Layout(name="stats", ratio=1),
                Layout(name="blockers", ratio=2)
            )
            
            # Intel
            intel_text = Text()
            intel_text.append(f"#{active.get('pr_id')} | ", style="bold cyan")
            intel_text.append(f"{active.get('title', 'Unknown')[:60]}...\n", style="white")
            intel_text.append(f"STRATEGY : {active.get('merge_strategy', 'MECHANICAL')}\n", style="bold magenta")
            intel_text.append(f"RATIONALE: {active.get('rationale', 'Standard rebase.')[:150]}...", style="dim")
            cockpit["top"]["intel"].update(Panel(intel_text, title="MISSION INTEL", border_style="magenta"))
            
            # Stats
            stats_text = Text()
            stats_text.append("CI STATUS: ", style="bold")
            ci = active.get("ci_status", "UNKNOWN")
            stats_text.append(f"{ci}\n", style="green" if ci == "SUCCESS" else "red" if ci == "FAILURE" else "yellow")
            stats_text.append(f"THREADS  : {active.get('unresolved_threads', 0)} unresolved\n", style="cyan")
            stats_text.append(f"RISK     : {active.get('risk_score', 0.0):.1f}", style="orange")
            cockpit["top"]["stats"].update(Panel(stats_text, title="QUICK STATS", border_style="blue"))

            # Blockers & Warnings
            blocker_text = Text()
            blockers = active.get("blockers", [])
            warnings = active.get("warnings", [])
            history = active.get("history", [])
            
            if not blockers:
                blocker_text.append("✅ ALL SYSTEMS NOMINAL\n", style="bold green")
                if warnings:
                    blocker_text.append(f"⚠️ {len(warnings)} Advisory Warnings\n", style="yellow")
                else:
                    blocker_text.append("Ready for integration.\n", style="dim green")
            else:
                for b in blockers[:3]:
                    b_type = str(b.get('type', '???')).replace('_', ' ').upper()
                    b_name = b.get('name', b.get('description', 'Blocker'))
                    blocker_text.append(f"❌ {b_type}: ", style="bold red")
                    blocker_text.append(f"{b_name[:40]}\n", style="white")
            
            if history:
                blocker_text.append("\n📜 MISSION HISTORY:\n", style="bold cyan")
                for h in history[-3:]:
                    blocker_text.append(f"  • {h.get('event')} ", style="dim white")
                    blocker_text.append(f"({h.get('timestamp')})\n", style="dim cyan")
            
            cockpit["top"]["blockers"].update(Panel(blocker_text, title="TACTICAL INSIGHTS", border_style="red" if blockers else "green"))

            # Middle row: Horizontal Stats
            middle_grid = Table.grid(expand=True)
            middle_grid.add_column(ratio=1)
            middle_grid.add_column(ratio=1)
            
            is_draft = bool(active.get("is_draft", False))
            draft_text = Text.assemble(("DRAFT MODE: ", "bold"), ("ENABLED" if is_draft else "DISABLED", "yellow" if is_draft else "dim white"))
            
            middle_grid.add_row(Align.center(draft_text), Align.center(Text("")))
            cockpit["middle"].update(Panel(middle_grid, border_style="blue"))

            # Bottom row: Objective or Execution Log
            log_text = Text()
            execution_log = getattr(state, "execution_log", [])
            if not execution_log:
                lc_state = str(active.get("lifecycle_state", "discovered")).upper()
                obj_text = Text()
                if is_draft:
                    obj_text.append("🎯 OBJECTIVE: Transition PR out of DRAFT mode.\n", style="bold yellow")
                    obj_text.append("NEXT STEP: Press [R] to mark as READY FOR REVIEW.", style="white")
                elif "READY" in lc_state:
                    obj_text.append("🎯 OBJECTIVE: Final sign-off and integration.\n", style="bold green")
                    obj_text.append("NEXT STEP: Press [A] to Approve or [I] to Implement Merge.", style="white")
                elif "THREAD" in lc_state or "COMMENT" in lc_state:
                    obj_text.append("🎯 OBJECTIVE: Resolve outstanding reviewer feedback.\n", style="bold yellow")
                    obj_text.append("NEXT STEP: Press [T] to review threads or [P] to auto-patch trivial suggestions.", style="white")
                elif "CONFLICT" in lc_state:
                    obj_text.append("🎯 OBJECTIVE: Reconcile branch divergence.\n", style="bold red")
                    obj_text.append("NEXT STEP: Press [I] to launch the Fusion Engine.", style="white")
                elif "MERGED" in lc_state:
                    obj_text.append("🏁 MISSION ACCOMPLISHED\n", style="bold green")
                    obj_text.append("PR has been successfully integrated.", style="white")
                else:
                    obj_text.append(f"🎯 OBJECTIVE: Advance PR from {lc_state} state.\n", style="bold cyan")
                    obj_text.append("NEXT STEP: Perform system verification [V] to refresh state.", style="white")
                
                cockpit["bottom"].update(Panel(obj_text, title="MISSION OBJECTIVE", border_style="cyan"))
            else:
                for step in execution_log[-5:]:
                    s_type = step.get("type", "INFO")
                    s_msg = step.get("message", "")
                    s_ts = step.get("timestamp", "")
                    color = "green" if s_type == "SUCCESS" else "red" if s_type == "ERROR" else "yellow" if s_type == "START" else "white"
                    log_text.append(f"[{s_ts}] {s_msg}\n", style=color)
                
                cockpit["bottom"].update(Panel(log_text, title="EXECUTION LOG", border_style="yellow"))
            
            layout["cockpit"].update(cockpit)
        else:
            layout["cockpit"].update(
                Panel("No PR selected", border_style="dim")
            )

        # Footer
        controls = Text.assemble(
            ("[A] ", "bold cyan"), "Approve  ",
            ("[B] ", "bold blue"), "Bulk Approve  ",
            ("[R] ", "bold green"), "Ready  ",
            ("[P] ", "bold magenta"), "Patch  ",
            ("[I] ", "bold yellow"), "Implement  ",
            ("[T] ", "bold blue"), "Threads  ",
            ("[V] ", "bold green"), "Verify  ",
            ("[S] ", "bold white"), "Skip  ",
            ("[X] ", "bold orange"), "Auto-Pilot  ",
            ("[Q] ", "bold red"), "Quit"
        )
        footer_grid = Table.grid(expand=True)
        
        ap_status = Text("AUTO-PILOT: ", style="bold")
        if getattr(state, "auto_pilot", False):
            ap_status.append("ENGAGED", style="blink bold green")
        else:
            ap_status.append("DISENGAGED", style="dim white")

        footer_grid.add_row(
            controls,
            Align.right(
                Text.assemble(
                    ap_status,
                    ("  |  ", "dim"),
                    (state.status_message, "italic dim white")
                )
            ),
        )
        layout["footer"].update(
            Panel(
                footer_grid,
                title="TACTICAL CONTROLS",
                border_style="dim",
            )
        )

        return layout
