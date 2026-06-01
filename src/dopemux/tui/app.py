"""Main Textual TUI dashboard app for Task Orchestrator."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header

from dopemux.tui.widgets.today import TodayPanel
from dopemux.tui.widgets.authority import AuthorityPanel
from dopemux.tui.widgets.packets import PacketsPanel
from dopemux.tui.widgets.proof import ProofPanel
from dopemux.tui.widgets.risks import RisksPanel
from dopemux.tui.widgets.pr_queue import PRQueuePanel
from dopemux.tui.widgets.context import ContextPanel
from dopemux.tui.widgets.do_not_touch import DoNotTouchPanel
from dopemux.ui.theme import Glyphs


class OrchestratorTUI(App):
    """Orchestrator HUD Telemetry Dashboard."""

    TITLE = f"{Glyphs.BRAND_MARK} Orchestrator HUD"
    SUB_TITLE = "ADHD-optimized Task Plan Telemetry"
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    CSS = """
    #dashboard-grid {
        layout: grid;
        grid-size: 2 4;
        grid-columns: 1fr 1fr;
        grid-gutter: 1;
        padding: 1;
        background: #020617;
    }
    
    TodayPanel, AuthorityPanel, PacketsPanel, ProofPanel, RisksPanel, PRQueuePanel, ContextPanel, DoNotTouchPanel {
        height: auto;
        min-height: 8;
        background: #041628;
    }
    """

    def __init__(self, *, once: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.once = once

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="dashboard-grid"):
            yield TodayPanel(id="tui-today")
            yield AuthorityPanel(id="tui-authority")
            yield PacketsPanel(id="tui-packets")
            yield ProofPanel(id="tui-proof")
            yield RisksPanel(id="tui-risks")
            yield PRQueuePanel(id="tui-pr-queue")
            yield ContextPanel(id="tui-context")
            yield DoNotTouchPanel(id="tui-do-not-touch")
        yield Footer()

    async def on_mount(self) -> None:
        if self.once:
            self.set_timer(0.1, self.exit)

    def action_refresh(self) -> None:
        """Force reactive refresh by calling update on all widgets."""
        for panel in self.query("TodayPanel, AuthorityPanel, PacketsPanel, ProofPanel, RisksPanel, PRQueuePanel, ContextPanel, DoNotTouchPanel"):
            panel.refresh()
