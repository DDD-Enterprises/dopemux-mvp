"""Dopemux TUI Dashboard — ADHD-optimized monitoring.

Launch via ``dopemux dashboard`` or ``dopemux dashboard --demo``.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Static

from .service_endpoints import (
    ResolvedEndpoint,
    refresh_age_label,
    resolve_dashboard_endpoints,
)
from .theme import Glyphs, StatusChip, styled_gauge, styled_panel, styled_table
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
    ("ConPort", "✓ LIVE", "3ms", "v2.1", "demo", "just now"),
    ("ADHD Engine", "✓ LIVE", "12ms", "v1.4", "demo", "just now"),
    ("Serena", "✓ LIVE", "5ms", "v2.0", "demo", "just now"),
    ("MCP Bridge", "✗ BLOCKER", "timeout", "—", "demo", "just now"),
]

DEMO_COGNITIVE_HISTORY = [
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.6,
    0.5,
    0.42,
    0.38,
    0.35,
    0.40,
]
DEMO_VELOCITY_HISTORY = [3, 4, 5, 5, 6, 7, 6, 5, 4, 6, 7, 8]
DEMO_SWITCHES_HISTORY = [2, 1, 2, 3, 5, 3, 2, 1, 2, 1, 1, 0]

VOICE = VoiceEngine(mode=VoiceMode.CLINICAL_FORENSICS, is_scattered=True)


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
    source_label = reactive("unresolved")
    endpoint_label = reactive("unresolved")
    last_sampled_at = reactive(None)

    async def on_mount(self) -> None:
        self.set_interval(1.0, self.update_state)

    async def update_state(self) -> None:
        app: DopemuxDashboard = self.app  # type: ignore[assignment]
        if app.demo:
            self._apply(DEMO_ADHD_STATE)
            self.source_label = "demo"
            self.endpoint_label = "demo://adhd-state"
            self.last_sampled_at = datetime.now(timezone.utc)
            return
        endpoint = app.dashboard_endpoints()["adhd"]
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    endpoint.url("/api/v1/state?user_id=default"),
                    timeout=0.5,
                )
                if resp.status_code == 200:
                    self._apply(resp.json())
                    self.source_label = endpoint.source
                    self.endpoint_label = endpoint.base_url
                    self.last_sampled_at = datetime.now(timezone.utc)
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
                    f"[text.dim]source=[/] {self.source_label}\n"
                    f"[text.dim]endpoint=[/] {self.endpoint_label}\n"
                    f"[text.dim]NEXT:[/] Verify the resolved ADHD Engine endpoint or restart the service."
                ),
                title="ADHD STATE",
                border_style="error",
            )

        energy_style, border_style, energy_icon = _energy_state(
            self.energy, self.cognitive_load
        )
        attention_style, attention_label = _attention_state(self.attention)
        load_style, load_label = _load_state(self.cognitive_load)
        load_bar = styled_gauge(self.cognitive_load, complete_style=load_style)
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
            f"[{load_style}]{load_label}[/] {load_bar} [text.dim]{int(self.cognitive_load * 100)}%[/]",
        )
        table.add_row(
            "[label]👁 Attention[/]",
            f"[{attention_style}]{attention_label}[/]",
        )
        table.add_row("[label]Flow[/]", flow_status)
        table.add_row("[label]Aftercare[/]", break_warning)
        table.add_row("[label]Endpoint[/]", f"[text.dim]{self.endpoint_label}[/]")
        table.add_row("[label]Source[/]", f"[text.dim]{self.source_label}[/]")
        table.add_row(
            "[label]Updated[/]",
            f"[text.dim]{refresh_age_label(self.last_sampled_at)}[/]",
        )

        return styled_panel(table, title="🧠 ADHD STATE", border_style=border_style)


class ProductivityPanel(Static):
    """Tasks and velocity metrics (Tier 2)."""

    tasks_completed = reactive(0)
    tasks_total = reactive(0)
    decisions_today = reactive(0)
    velocity = reactive([0, 0, 0, 0, 0, 0, 0, 0, 0])
    source_label = reactive("unresolved")
    last_sampled_at = reactive(None)

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
            self.source_label = "demo"
            self.last_sampled_at = datetime.now(timezone.utc)
            return
        endpoints = app.dashboard_endpoints()
        adhd_endpoint = endpoints["adhd"]
        bridge_endpoint = endpoints["bridge"]
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(adhd_endpoint.url("/api/v1/tasks"), timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json()
                    self.tasks_completed = data.get("completed", 0)
                    self.tasks_total = data.get("total", 0)
            except Exception:
                pass
            try:
                resp = await client.get(
                    bridge_endpoint.url("/ddg/decisions?limit=20"), timeout=1.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.decisions_today = int(
                        data.get("count", len(data.get("items", [])))
                    )
            except Exception:
                pass
        self.source_label = (
            f"tasks:{adhd_endpoint.source}; decisions:{bridge_endpoint.source}"
        )
        self.last_sampled_at = datetime.now(timezone.utc)

    def render(self) -> object:
        is_complete = self.tasks_completed >= self.tasks_total and self.tasks_total > 0
        rate = self.tasks_completed / self.tasks_total if self.tasks_total > 0 else 0
        bar = styled_gauge(rate)
        sparkline = "".join("▁▂▃▄▅▆▇█"[min(v, 7)] for v in self.velocity)

        table = _grid_table()
        task_label = (
            f"[success]{Glyphs.SUCCESS} RITUAL COMPLETE[/]"
            if is_complete
            else f"[label]{Glyphs.CODE} Tasks[/]"
        )
        table.add_row(
            task_label,
            f"[mint.soft]{self.tasks_completed}/{self.tasks_total}[/] {bar} [text.dim]({int(rate * 100)}%)[/]",
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
        table.add_row("[label]Source[/]", f"[text.dim]{self.source_label}[/]")
        table.add_row(
            "[label]Updated[/]",
            f"[text.dim]{refresh_age_label(self.last_sampled_at)}[/]",
        )

        return styled_panel(table, title="🚀 MISSION VELOCITY", border_style="info")


class ServicesGrid(Static):
    """Service health matrix (Tier 2)."""

    last_sampled_at = reactive(None)

    def compose(self) -> ComposeResult:
        yield DataTable(id="services-table")

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(
            "Service", "Status", "Latency", "Version", "Source", "Updated"
        )
        self.set_interval(30.0, self.update_services)
        await self.update_services()

    async def update_services(self) -> None:
        table = self.query_one(DataTable)
        table.clear()

        app: DopemuxDashboard = self.app  # type: ignore[assignment]
        if app.demo:
            for row in DEMO_SERVICES:
                table.add_row(*row)
            self.last_sampled_at = datetime.now(timezone.utc)
            return

        endpoints = app.dashboard_endpoints()
        services = [
            (endpoints["conport"], "/health"),
            (endpoints["adhd"], "/health"),
            (endpoints["serena"], "/health"),
            (endpoints["bridge"], "/kg/health"),
        ]

        async with httpx.AsyncClient() as client:
            for endpoint, health_path in services:
                try:
                    resp = await client.get(endpoint.url(health_path), timeout=2.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        status = (
                            f"{Glyphs.SUCCESS} LIVE"
                            if data.get("status") == "healthy"
                            else f"{Glyphs.ERROR} BLOCKER"
                        )
                        latency = f"{data.get('latency_ms', 0)}ms"
                        version = data.get("version", "—")
                        table.add_row(
                            endpoint.name,
                            status,
                            latency,
                            version,
                            endpoint.source,
                            refresh_age_label(datetime.now(timezone.utc)),
                        )
                    else:
                        table.add_row(
                            endpoint.name,
                            f"{Glyphs.ERROR} BLOCKER",
                            "error",
                            str(resp.status_code),
                            endpoint.source,
                            refresh_age_label(datetime.now(timezone.utc)),
                        )
                except Exception as exc:
                    table.add_row(
                        endpoint.name,
                        f"{Glyphs.ERROR} BLOCKER",
                        "timeout",
                        str(exc)[:20],
                        endpoint.source,
                        refresh_age_label(datetime.now(timezone.utc)),
                    )
        self.last_sampled_at = datetime.now(timezone.utc)


class TrendsPanel(Static):
    """Sparkline trends (Tier 3)."""

    cognitive_history = reactive([])
    velocity_history = reactive([])
    switches_history = reactive([])
    source_label = reactive("unavailable")
    last_sampled_at = reactive(None)

    async def on_mount(self) -> None:
        self.set_interval(30.0, self.update_trends)
        await self.update_trends()

    async def update_trends(self) -> None:
        app: DopemuxDashboard = self.app  # type: ignore[assignment]
        if app.demo:
            self.apply_demo_trends()
            return

        self.cognitive_history = []
        self.velocity_history = []
        self.switches_history = []
        self.source_label = "unavailable"
        self.last_sampled_at = None

    def apply_demo_trends(self) -> None:
        self.cognitive_history = list(DEMO_COGNITIVE_HISTORY)
        self.velocity_history = list(DEMO_VELOCITY_HISTORY)
        self.switches_history = list(DEMO_SWITCHES_HISTORY)
        self.source_label = "demo"
        self.last_sampled_at = datetime.now(timezone.utc)

    def render(self) -> object:
        def sparkline(data: list[float | int]) -> str:
            chars = "▁▂▃▄▅▆▇█"
            mx = max(data) or 1
            return "".join(chars[min(int((v / mx) * 7), 7)] for v in data)

        def trend_value(data: list[float | int], style: str) -> str:
            if not data:
                return "[warning]UNAVAILABLE no live trend data[/]"
            return f"[{style}]{sparkline(data)}[/]"

        table = _grid_table()
        table.add_row(
            "[label]Cognitive load[/]",
            f"{trend_value(self.cognitive_history, 'mint.soft')} [text.dim](last 2h)[/]",
        )
        table.add_row(
            "[label]Task velocity[/]",
            f"{trend_value(self.velocity_history, 'info')} [text.dim](last 7d)[/]",
        )
        table.add_row(
            "[label]Context switches[/]",
            f"{trend_value(self.switches_history, 'warning')} [text.dim](last 24h)[/]",
        )
        table.add_row("[label]Source[/]", f"[text.dim]{self.source_label}[/]")
        table.add_row(
            "[label]Updated[/]",
            f"[text.dim]{refresh_age_label(self.last_sampled_at)}[/]",
        )

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

    def __init__(self) -> None:
        super().__init__()
        self._endpoints_cache: dict[str, ResolvedEndpoint] | None = None

    def dashboard_endpoints(self) -> dict[str, ResolvedEndpoint]:
        """Lazily resolve endpoints once and return cached values thereafter.

        Textual drives app callbacks on a single event-loop thread, so this
        cache is intentionally initialized without a lock and persists for the
        app instance lifetime.
        """
        if self._endpoints_cache is None:
            self._endpoints_cache = resolve_dashboard_endpoints()
        return self._endpoints_cache

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
            self.notify(
                "[OVERRIDE] tmux required for detail popup.", severity="warning"
            )
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
        for panel in self.query(TrendsPanel):
            panel.call_later(panel.update_trends)
        self.notify("[LIVE] Refreshing cockpit telemetry.", severity="information")


def run_dashboard(*, demo: bool = False) -> None:
    """Entry point called by ``dopemux dashboard``."""
    app = DopemuxDashboard()
    app.demo = demo
    app.run()


if __name__ == "__main__":
    run_dashboard(demo="--demo" in sys.argv)
