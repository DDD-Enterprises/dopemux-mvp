"""Dopemux TUI Dashboard — ADHD-optimized monitoring.

Launch via ``dopemux dashboard`` or ``dopemux dashboard --demo``.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import httpx
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Static

from .theme import Glyphs, StatusChip, styled_panel, styled_table
from .voice import VoiceEngine, VoiceMode

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

VOICE = VoiceEngine(mode=VoiceMode.UX_SCOLD, is_scattered=True)


def _grid_table() -> object:
    """Return a borderless themed table for compact dashboard facts."""
    return styled_table("", "Signal", "State", show_header=False, box=None, expand=True)


def _energy_state(energy: str, cognitive_load: float) -> tuple[str, str, str]:
    """Map dashboard energy/load state to branded glyphs and styles."""
    if cognitive_load >= 0.85:
        return "error", "error", "🚨"
    mapping = {
        "low": ("mint.soft", "panel.border", "💧"),
        "medium": ("info", "info", "⚡"),
        "high": ("warning", "warning", "🔥"),
    }
    return mapping.get(energy, ("text.dim", "panel.border", "⚡"))


def _attention_state(attention: str) -> tuple[str, str]:
    mapping = {
        "focused": ("info", "Focused"),
        "scattered": ("magenta", "Scattered"),
    }
    return mapping.get(attention, ("text.dim", attention.title()))


def _load_state(value: float) -> tuple[str, str]:
    if value >= 0.85:
        return "error", "Critical"
    if value >= 0.65:
        return "warning", "Elevated"
    return "mint.soft", "Stable"


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

    def render(self) -> object:
        if not self.is_connected:
            return styled_panel(
                (
                    f"{StatusChip.BLOCKER.render('ADHD Engine disconnected.')}\n\n"
                    f"[magenta]{VOICE.get_roast()}[/]\n"
                    f"[text.dim]NEXT:[/] Bring the telemetry service back online."
                ),
                title="ADHD STATE",
                border_style="error",
            )

        energy_style, border_style, energy_icon = _energy_state(self.energy, self.cognitive_load)
        attention_style, attention_label = _attention_state(self.attention)
        load_style, load_label = _load_state(self.cognitive_load)
        load_bar = self._make_gauge(self.cognitive_load)
        flow_status = (
            f"[info]{Glyphs.RUNNING} Flow ritual active[/]"
            if self.in_flow
            else "[text.dim]No active flow lock[/]"
        )
        break_warning = (
            f"[violet]{StatusChip.AFTERCARE.render(f'Break in {self.break_in}m.')}[/]\n"
            f"[violet]{VOICE.get_aftercare()}[/]"
            if self.break_in < 20
            else "[text.dim]No break pressure yet[/]"
        )

        table = _grid_table()
        table.add_row(
            f"[label]{energy_icon} Energy[/]",
            f"[{energy_style}]{self.energy.title()}[/]",
        )
        table.add_row(
            "[label]🧠 Cognitive load[/]",
            f"[{load_style}]{load_label}[/] [text.dim]{load_bar} {int(self.cognitive_load * 100)}%[/]",
        )
        table.add_row(
            "[label]👁 Attention[/]",
            f"[{attention_style}]{attention_label}[/]",
        )
        table.add_row("[label]Flow[/]", flow_status)
        table.add_row("[label]Aftercare[/]", break_warning)

        return styled_panel(table, title="[blink]🧠 ADHD STATE[/blink]", border_style=border_style)

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

    def render(self) -> object:
        rate = self.tasks_completed / self.tasks_total if self.tasks_total > 0 else 0
        bar = "█" * int(rate * 10) + "░" * (10 - int(rate * 10))
        sparkline = "".join("▁▂▃▄▅▆▇█"[min(v, 7)] for v in self.velocity)

        table = _grid_table()
        table.add_row(
            f"[label]{Glyphs.CODE} Tasks[/]",
            f"[mint.soft]{self.tasks_completed}/{self.tasks_total}[/] [text.dim]({int(rate * 100)}%) {bar}[/]",
        )
        table.add_row(
            f"[label]{Glyphs.INFO} Decisions[/]",
            f"[info]{self.decisions_today}[/] [text.dim]logged today[/]",
        )
        table.add_row("[label]Velocity[/]", f"[info]{sparkline}[/]")
        table.add_row(
            "[label]Completion[/]",
            f"{StatusChip.LOGGED.render(f'{int(rate * 100)}% locked')} [text.dim](target: 85%)[/]",
        )

        return styled_panel(table, title="🚀 MISSION VELOCITY", border_style="info")


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
                        status = (
                            f"{Glyphs.SUCCESS} LIVE"
                            if data.get("status") == "healthy"
                            else f"{Glyphs.ERROR} BLOCKER"
                        )
                        latency = f"{data.get('latency_ms', 0)}ms"
                        version = data.get("version", "—")
                        table.add_row(name, status, latency, version)
                    else:
                        table.add_row(name, f"{Glyphs.ERROR} BLOCKER", "error", str(resp.status_code))
                except Exception as exc:
                    table.add_row(name, f"{Glyphs.ERROR} BLOCKER", "timeout", str(exc)[:20])


class TrendsPanel(Static):
    """Sparkline trends (Tier 3)."""

    cognitive_history = reactive(DEMO_COGNITIVE_HISTORY)
    velocity_history = reactive(DEMO_VELOCITY_HISTORY)
    switches_history = reactive(DEMO_SWITCHES_HISTORY)

    def render(self) -> object:
        def sparkline(data: list[float | int]) -> str:
            chars = "▁▂▃▄▅▆▇█"
            mx = max(data) or 1
            return "".join(chars[min(int((v / mx) * 7), 7)] for v in data)

        table = _grid_table()
        table.add_row("[label]Cognitive load[/]", f"[mint.soft]{sparkline(self.cognitive_history)}[/] [text.dim](last 2h)[/]")
        table.add_row("[label]Task velocity[/]", f"[info]{sparkline(self.velocity_history)}[/] [text.dim](last 7d)[/]")
        table.add_row("[label]Context switches[/]", f"[warning]{sparkline(self.switches_history)}[/] [text.dim](last 24h)[/]")

        return styled_panel(table, title="📈 COGNITIVE TRENDS", border_style="warning")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# App
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class DopemuxDashboard(App):
    """Main Textual dashboard app."""

    CSS_PATH = "dopemux.tcss"
    TITLE = f"{Glyphs.BRAND_MARK} Dopemux Dashboard"
    SUB_TITLE = "ADHD-HUD telemetry"

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
            self.notify("[BLOCKER] Detail popup script missing.", severity="error")
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
            self.notify("[OVERRIDE] tmux required for detail popup.", severity="warning")
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
        self.notify("[LIVE] Refreshing cockpit telemetry.", severity="information")


def run_dashboard(*, demo: bool = False) -> None:
    """Entry point called by ``dopemux dashboard``."""
    app = DopemuxDashboard()
    app.demo = demo
    app.run()


if __name__ == "__main__":
    run_dashboard(demo="--demo" in sys.argv)
