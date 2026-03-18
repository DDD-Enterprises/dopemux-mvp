"""Dopemux TUI Dashboard — ADHD-optimized monitoring.

Launch via ``dopemux dashboard`` or ``dopemux dashboard --demo``.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import httpx
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Static

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Demo data (used when --demo is active)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEMO_ADHD_STATE = {
    "energy_level": "high",
    "attention_state": "focused",
    "cognitive_load": 0.42,
    "flow_state": {"active": True},
    "break_warning": {"minutes_until": 8},
}

DEMO_SERVICES = [
    ("ConPort", "✓", "3ms", "v2.1"),
    ("ADHD Engine", "✓", "12ms", "v1.4"),
    ("Serena", "✓", "5ms", "v2.0"),
    ("MCP Bridge", "✗", "timeout", "—"),
]

DEMO_COGNITIVE_HISTORY = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.6, 0.5, 0.42, 0.38, 0.35, 0.40]
DEMO_VELOCITY_HISTORY = [3, 4, 5, 5, 6, 7, 6, 5, 4, 6, 7, 8]
DEMO_SWITCHES_HISTORY = [2, 1, 2, 3, 5, 3, 2, 1, 2, 1, 1, 0]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Panels
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ADHDStatePanel(Static):
    """Top panel — critical ADHD state (Tier 1)."""

    energy = reactive("medium")
    attention = reactive("focused")
    cognitive_load = reactive(0.65)
    in_flow = reactive(False)
    break_in = reactive(15)
    is_connected = reactive(True)

    async def on_mount(self) -> None:
        self.set_interval(1.0, self.update_state)

    async def update_state(self) -> None:
        app: DopemuxDashboard = self.app  # type: ignore[assignment]
        if app.demo:
            self._apply(DEMO_ADHD_STATE)
            return
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    "http://localhost:8001/api/v1/state?user_id=default",
                    timeout=0.5,
                )
                if resp.status_code == 200:
                    self._apply(resp.json())
                else:
                    self.is_connected = False
            except Exception:
                self.is_connected = False

    def _apply(self, data: dict) -> None:
        self.energy = data.get("energy_level", "medium")
        self.attention = data.get("attention_state", "focused")
        self.cognitive_load = data.get("cognitive_load", 0.5)
        self.in_flow = data.get("flow_state", {}).get("active", False)
        self.break_in = data.get("break_warning", {}).get("minutes_until", 99)
        self.is_connected = True

    def render(self) -> Panel:
        if not self.is_connected:
            return Panel(
                Text("⚠️  ADHD Engine Disconnected", style="bold #FF8BD1", justify="center"),
                title="ADHD STATE",
                border_style="#FF8BD1",
            )

        energy_icon = {"high": "⚡↑", "medium": "⚡=", "low": "⚡↓"}.get(self.energy, "⚡")
        attention_icon = {"focused": "👁️●", "scattered": "👁️🌀"}.get(self.attention, "👁️")
        load_bar = self._make_gauge(self.cognitive_load)
        flow_status = "🌊 Active" if self.in_flow else ""
        break_warning = f"☕ in {self.break_in}m" if self.break_in < 20 else ""

        table = Table.grid(padding=1)
        table.add_column(style="bold #94FADB")
        table.add_column(style="bold #9B78FF")
        table.add_column(style="bold #F5F26D")

        table.add_row(
            f"{energy_icon} {self.energy.title()}",
            f"{attention_icon} {self.attention.title()}",
            f"🧠 {load_bar} {int(self.cognitive_load * 100)}%",
        )
        table.add_row(flow_status, break_warning, "")

        return Panel(table, title="ADHD STATE", border_style="#94FADB")

    @staticmethod
    def _make_gauge(value: float) -> str:
        filled = int(value * 10)
        return f"[{'|' * filled}{'·' * (10 - filled)}]"


class ProductivityPanel(Static):
    """Tasks and velocity metrics (Tier 2)."""

    tasks_completed = reactive(0)
    tasks_total = reactive(0)
    decisions_today = reactive(0)
    velocity = reactive([0, 0, 0, 0, 0, 0, 0, 0, 0])

    async def on_mount(self) -> None:
        self.set_interval(30.0, self.update_metrics)
        await self.update_metrics()

    async def update_metrics(self) -> None:
        app: DopemuxDashboard = self.app  # type: ignore[assignment]
        if app.demo:
            self.tasks_completed = 8
            self.tasks_total = 10
            self.decisions_today = 23
            self.velocity = DEMO_VELOCITY_HISTORY
            return
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get("http://localhost:8001/api/v1/tasks", timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self.tasks_completed = data.get("completed", 0)
                    self.tasks_total = data.get("total", 0)
            except Exception:
                pass
            try:
                resp = await client.get(
                    "http://localhost:8005/api/adhd/decisions/recent", timeout=1.0
                )
                if resp.status_code == 200:
                    self.decisions_today = len(resp.json().get("today", []))
            except Exception:
                pass

    def render(self) -> Panel:
        rate = self.tasks_completed / self.tasks_total if self.tasks_total > 0 else 0
        bar = "█" * int(rate * 10) + "░" * (10 - int(rate * 10))
        sparkline = "".join("▁▂▃▄▅▆▇█"[min(v, 7)] for v in self.velocity)

        table = Table.grid(padding=1)
        table.add_column()
        table.add_column()
        table.add_row(
            f"Tasks: {self.tasks_completed}/{self.tasks_total} ({int(rate * 100)}%) {bar}",
            f"Decisions: {self.decisions_today} today",
        )
        table.add_row(
            f"Velocity: {sparkline}",
            f"Completion: {int(rate * 100)}% (target: 85%)",
        )

        return Panel(table, title="PRODUCTIVITY", border_style="#7DFBF6")


class ServicesGrid(Static):
    """Service health matrix (Tier 2)."""

    def compose(self) -> ComposeResult:
        yield DataTable(id="services-table")

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Service", "Status", "Latency", "Version")
        self.set_interval(30.0, self.update_services)
        await self.update_services()

    async def update_services(self) -> None:
        table = self.query_one(DataTable)
        table.clear()

        app: DopemuxDashboard = self.app  # type: ignore[assignment]
        if app.demo:
            for row in DEMO_SERVICES:
                table.add_row(*row)
            return

        services = [
            ("ConPort", "http://localhost:8005/health"),
            ("ADHD Engine", "http://localhost:8001/health"),
            ("Serena", "http://localhost:8003/health"),
            ("MCP Bridge", "http://localhost:3016/health"),
        ]

        async with httpx.AsyncClient() as client:
            for name, url in services:
                try:
                    resp = await client.get(url, timeout=2.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        status = "✓" if data.get("status") == "healthy" else "✗"
                        latency = f"{data.get('latency_ms', 0)}ms"
                        version = data.get("version", "—")
                        table.add_row(name, status, latency, version)
                    else:
                        table.add_row(name, "✗", "error", str(resp.status_code))
                except Exception as exc:
                    table.add_row(name, "✗", "timeout", str(exc)[:20])


class TrendsPanel(Static):
    """Sparkline trends (Tier 3)."""

    cognitive_history = reactive(DEMO_COGNITIVE_HISTORY)
    velocity_history = reactive(DEMO_VELOCITY_HISTORY)
    switches_history = reactive(DEMO_SWITCHES_HISTORY)

    def render(self) -> Panel:
        def sparkline(data: list[float | int]) -> str:
            chars = "▁▂▃▄▅▆▇█"
            mx = max(data) or 1
            return "".join(chars[min(int((v / mx) * 7), 7)] for v in data)

        table = Table.grid(padding=1)
        table.add_column(style="#94A3B8")
        table.add_column()
        table.add_column(style="#94A3B8")

        table.add_row("Cognitive Load:", sparkline(self.cognitive_history), "(last 2h)")
        table.add_row("Task Velocity:", sparkline(self.velocity_history), "(last 7d)")
        table.add_row("Context Switches:", sparkline(self.switches_history), "(last 24h)")

        return Panel(table, title="TRENDS", border_style="#F5F26D")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# App
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class DopemuxDashboard(App):
    """Main Textual dashboard app."""

    CSS_PATH = "dopemux.tcss"
    TITLE = "Dopemux Dashboard"
    SUB_TITLE = "ADHD-optimized monitoring"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_tasks", "Tasks"),
        ("s", "toggle_services", "Services"),
        ("p", "toggle_patterns", "Patterns"),
        ("d", "show_detail", "Detail"),
        ("r", "refresh_all", "Refresh"),
    ]

    demo: bool = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        if self.demo:
            yield Static("DEMO MODE — using mock data", id="demo-banner")
        yield ADHDStatePanel(id="adhd-state")
        yield ProductivityPanel(id="productivity")
        yield ServicesGrid(id="services")
        yield TrendsPanel(id="trends")
        yield Footer()

    # ── Actions ──

    def action_show_detail(self) -> None:
        """Open tmux popup with detailed view."""
        detail_script = Path(__file__).parent.resolve() / "dashboard_detail.py"
        if not detail_script.exists():
            self.notify("Detail script not found", severity="error")
            return

        try:
            subprocess.run(
                [
                    "tmux",
                    "display-popup",
                    "-E",
                    "-w",
                    "95%",
                    "-h",
                    "90%",
                    "-T",
                    "Dopemux Details",
                    f"{sys.executable} {detail_script}",
                ],
                check=False,
            )
        except FileNotFoundError:
            self.notify("tmux not found — detail popup requires tmux", severity="warning")
        except Exception:
            pass

    def action_toggle_tasks(self) -> None:
        """Toggle productivity panel."""
        widget = self.query_one("#productivity")
        widget.display = not widget.display

    def action_toggle_services(self) -> None:
        """Toggle services panel."""
        widget = self.query_one("#services")
        widget.display = not widget.display

    def action_toggle_patterns(self) -> None:
        """Toggle trends panel."""
        widget = self.query_one("#trends")
        widget.display = not widget.display

    def action_refresh_all(self) -> None:
        """Force-refresh all panels."""
        for panel in self.query(ADHDStatePanel):
            panel.call_later(panel.update_state)
        for panel in self.query(ProductivityPanel):
            panel.call_later(panel.update_metrics)
        for panel in self.query(ServicesGrid):
            panel.call_later(panel.update_services)
        self.notify("Refreshing all panels…")


def run_dashboard(*, demo: bool = False) -> None:
    """Entry point called by ``dopemux dashboard``."""
    app = DopemuxDashboard()
    app.demo = demo
    app.run()


if __name__ == "__main__":
    run_dashboard(demo="--demo" in sys.argv)
