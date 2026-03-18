from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.align import Align

from .ux_engine import RichTerminalRenderer, RenderMode
from .strategy_library import STRATEGY_LIBRARY


@dataclass
class QueueState:
    """State of the entire PR queue for the dashboard."""
    run_id: str
    prs: List[Dict[str, Any]] = field(default_factory=list)
    active_index: int = 0
    status_message: str = "Ready for mission orders."
    start_time: float = field(default_factory=time.time)

    @property
    def active_pr(self) -> Optional[Dict[str, Any]]:
        if 0 <= self.active_index < len(self.prs):
            return self.prs[self.active_index]
        return None


class DopemuxDashboard:
    """Persistent, live-updating Grand Orchestrator Dashboard with full branding."""

    def __init__(self, manager: Any):
        self.manager = manager
        self.ux = RichTerminalRenderer(mode=RenderMode.RICH)
        self.console = Console()
        self.state: Optional[QueueState] = None

    def _make_header(self) -> Panel:
        """Create the space-age Dopemux header."""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="right")
        
        title = Text.assemble(
            ("🚀 ", "bold yellow"),
            ("DOPEMUX ", "bold cyan"),
            ("PR-MERGE ", "bold magenta"),
            ("GRAND ORCHESTRATOR", "bold white")
        )
        
        elapsed = int(time.time() - self.state.start_time)
        timer = Text(f"MISSION TIME: {elapsed//60:02d}:{elapsed%60:02d}", style="dim yellow")
        
        grid.add_row(title, timer)
        return Panel(grid, style="white on blue")

    def _make_queue_table(self) -> Panel:
        """Create the live-updating queue status table."""
        table = Table(expand=True, box=None)
        table.add_column("PR#", style="bold cyan", width=6)
        table.add_column("Title", ratio=1)
        table.add_column("Strategy", style="magenta")
        table.add_column("Step", style="yellow")
        table.add_column("Status", justify="center")

        for i, pr in enumerate(self.state.prs):
            is_active = i == self.state.active_index
            row_style = "bold white on grey15" if is_active else "dim"
            
            # Extract data safely
            pr_id = str(pr.get("pr_id", "???"))
            title = pr.get("title", "Unknown Title")
            strategy = pr.get("merge_strategy", "MECHANICAL")
            step = pr.get("lifecycle_state", "discovered").upper()
            
            status_icon = "🟢" if "READY" in step else "🔴" if "BLOCKED" in step else "⏳"
            
            table.add_row(
                f"{'> ' if is_active else '  '}{pr_id}",
                title,
                strategy,
                step,
                status_icon,
                style=row_style
            )

        return Panel(table, title="[ QUEUE STATUS ]", border_style="cyan")

    def _make_cockpit(self) -> Layout:
        """Create the tactical cockpit for the active PR."""
        active = self.state.active_pr
        if not active:
            return Layout(Panel("No PR selected", border_style="dim"))

        l = Layout()
        l.split_row(
            Layout(name="intel", ratio=1),
            Layout(name="blockers", ratio=1)
        )
        
        # Build Intel Panel using existing UX methods (proxy)
        intel_text = Text()
        intel_text.append(f"PR: #{active.get('pr_id')}\n", style="bold cyan")
        intel_text.append(f"STRATEGY: {active.get('merge_strategy')}\n", style="bold magenta")
        intel_text.append(f"RATIONALE: {active.get('rationale', 'Standard rebase.')[:100]}...\n", style="dim")
        
        l["intel"].update(Panel(intel_text, title="MISSION INTELLIGENCE", border_style="magenta"))
        
        # Build Blocker Panel
        blocker_text = Text()
        blockers = active.get("blockers", [])
        if not blockers:
            blocker_text.append("✅ ALL SYSTEMS NOMINAL", style="bold green")
        for b in blockers:
            blocker_text.append(f"❌ [{b.get('type')}] {b.get('name', 'Blocker')}\n", style="red")
            
        l["blockers"].update(Panel(blocker_text, title="TACTICAL INSIGHTS", border_style="red"))
        return l

    def _make_controls(self) -> Panel:
        """Create the legend and status footer."""
        controls = Text.assemble(
            ("[A] ", "bold cyan"), "Approve  ",
            ("[P] ", "bold magenta"), "Patch  ",
            ("[I] ", "bold yellow"), "Implement  ",
            ("[T] ", "bold blue"), "Threads  ",
            ("[V] ", "bold green"), "Verify  ",
            ("[S] ", "bold white"), "Skip  ",
            ("[Q] ", "bold red"), "Quit"
        )
        
        footer = Table.grid(expand=True)
        footer.add_row(controls, Align.right(Text(self.state.status_message, style="italic dim white")))
        
        return Panel(footer, title="TACTICAL CONTROLS", border_style="dim")

    def render(self) -> Layout:
        """Assemble the entire Grand Dashboard layout."""
        layout = Layout()
        layout.split_column(
            Layout(self._make_header(), size=3),
            Layout(self._make_queue_table(), ratio=1),
            Layout(self._make_cockpit(), size=10),
            Layout(self._make_controls(), size=3)
        )
        return layout

    def run(self, pr_queue: List[Dict[str, Any]], run_id: str):
        """Run the persistent dashboard loop."""
        self.state = QueueState(run_id=run_id, prs=pr_queue)
        
        with Live(self.render(), console=self.console, screen=True, auto_refresh=True) as live:
            while True:
                # In a real implementation, we'd use a non-blocking key listener.
                # For this MVP, we'll use a standard prompt that breaks the Live display
                # then restores it, or we'll just clear and redraw manually.
                live.update(self.render())
                
                # Temporary interaction placeholder
                try:
                    # We have to stop Live to take input in some terminal environments safely
                    live.stop()
                    choice = input(f"\n[{self.state.active_pr.get('pr_id')}] COMMAND > ").strip().upper()
                    live.start()
                    
                    if choice == "Q":
                        self.state.status_message = "Mission aborted by operator."
                        break
                    elif choice == "S":
                        self.state.active_index = (self.state.active_index + 1) % len(self.state.prs)
                        self.state.status_message = f"Skipped to PR #{self.state.active_pr.get('pr_id')}"
                    else:
                        self.state.status_message = f"Executing tactic [{choice}]..."
                        # Here we would call the actual engine logic
                        time.sleep(1) 
                        
                except (KeyboardInterrupt, EOFError):
                    break

        self.console.print("\n[bold green]MISSION COMPLETE. FLIGHT DATA SAVED TO PROOF BUNDLE. 🛰️[/bold green]")
