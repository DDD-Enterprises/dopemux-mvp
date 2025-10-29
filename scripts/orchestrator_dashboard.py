#!/usr/bin/env python3
"""
Rich Orchestrator Dashboard for DOPE Layout
Displays live status, tasks, and metrics in a beautiful TUI
"""

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
import time
from datetime import datetime

def create_header() -> Panel:
    """Create the header with branding"""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="center")
    grid.add_column(justify="right")
    
    grid.add_row(
        "🎯 [bold #7dfbf6]ORCHESTRATOR[/]",
        "[bold #ff8bd1]DOPEMUX[/] [dim]DOPE Layout[/]",
        f"[#94fadb]{datetime.now().strftime('%H:%M:%S')}[/]"
    )
    
    return Panel(grid, style="bold on #0a1628", border_style="#7dfbf6")

def create_status() -> Panel:
    """Create status panel"""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="#94fadb", justify="right")
    table.add_column(style="bold")
    
    table.add_row("Mode:", "[#ff8bd1]Implementation[/]")
    table.add_row("Session:", "[#7dfbf6]23m 45s[/]")
    table.add_row("Energy:", "[#94fadb]●●●○○[/] MEDIUM")
    table.add_row("Focus:", "[#a6e3a1]●●●●○[/] PEAK")
    
    return Panel(table, title="[bold #7dfbf6]Status[/]", border_style="#7dfbf6")

def create_active_tasks() -> Panel:
    """Create active tasks panel"""
    table = Table(show_header=True, header_style="bold #7dfbf6", border_style="#7dfbf6")
    table.add_column("Task", style="#ff8bd1")
    table.add_column("Progress", justify="center")
    table.add_column("ETA", justify="right", style="#94fadb")
    
    table.add_row(
        "Code panes",
        "[#a6e3a1]████████░░[/] 80%",
        "15m"
    )
    table.add_row(
        "Integration testing",
        "[#f5f26d]███░░░░░░░[/] 30%",
        "45m"
    )
    
    return Panel(table, title="[bold #7dfbf6]Active Tasks[/]", border_style="#7dfbf6")

def create_agent_status() -> Panel:
    """Create agent status panel"""
    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold")
    table.add_column()
    
    table.add_row(
        "🤖 Primary Agent:",
        "[#a6e3a1]ACTIVE[/] - Analyzing codebase"
    )
    table.add_row(
        "🤖 Secondary Agent:",
        "[dim]IDLE[/]"
    )
    table.add_row(
        "📊 Docker:",
        "[#a6e3a1]12/12 running[/]"
    )
    table.add_row(
        "⚡ MCP:",
        "[#a6e3a1]8/8 healthy[/]"
    )
    
    return Panel(table, title="[bold #7dfbf6]Services[/]", border_style="#7dfbf6")

def create_alerts() -> Panel:
    """Create alerts/notifications panel"""
    text = Text()
    text.append("⚠️  ", style="bold #f5f26d")
    text.append("2 untracked work items detected\n", style="#f5f26d")
    text.append("💡 ", style="bold #7dfbf6")
    text.append("Press 'P' to plan work", style="dim")
    
    return Panel(text, title="[bold #ff8bd1]Alerts[/]", border_style="#ff8bd1")

def create_metrics() -> Panel:
    """Create metrics panel"""
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right", style="#94fadb")
    table.add_column()
    
    table.add_row("Files Changed:", "[bold]24[/]")
    table.add_row("Context Switches:", "[bold]3[/]")
    table.add_row("LiteLLM Cost:", "[bold]$0.23/hr[/]")
    table.add_row("Latency:", "[bold]1.2s[/]")
    
    return Panel(table, title="[bold #7dfbf6]Metrics[/]", border_style="#7dfbf6")

def create_footer() -> Panel:
    """Create footer with hotkeys"""
    text = Text.from_markup(
        "[#7dfbf6]M[/] Mode  [#7dfbf6]P[/] Plan  [#7dfbf6]C[/] Commit  "
        "[#7dfbf6]D[/] Dismiss  [#7dfbf6]?[/] Help  [#7dfbf6]Q[/] Quit"
    )
    return Panel(text, style="dim on #0a1628", border_style="#7dfbf6")

def create_layout() -> Layout:
    """Create the main layout"""
    layout = Layout()
    
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right", ratio=2),
    )
    
    layout["left"].split(
        Layout(name="status"),
        Layout(name="services"),
        Layout(name="metrics"),
    )
    
    layout["right"].split(
        Layout(name="tasks"),
        Layout(name="alerts"),
    )
    
    return layout

def main():
    """Run the dashboard"""
    console = Console()
    layout = create_layout()
    
    with Live(layout, console=console, screen=True, refresh_per_second=4):
        while True:
            # Update components
            layout["header"].update(create_header())
            layout["status"].update(create_status())
            layout["services"].update(create_agent_status())
            layout["metrics"].update(create_metrics())
            layout["tasks"].update(create_active_tasks())
            layout["alerts"].update(create_alerts())
            layout["footer"].update(create_footer())
            
            time.sleep(0.25)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Dashboard closed")
