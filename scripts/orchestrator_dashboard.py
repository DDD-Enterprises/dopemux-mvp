#!/usr/bin/env python3
"""
Rich Orchestrator Dashboard for DOPE Layout

This version wires the panels to live collectors:
- Implementation data via the Neon dashboard `ImplementationCollector`
- PM/conport data via the `PMCollector`
- Prometheus metrics via the shared `PrometheusClient`

It gracefully degrades when services are unavailable so the dashboard
can still launch during partial outages.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dopemux.config import ConfigManager
from prometheus_client import PrometheusClient, PrometheusConfig
from scripts.neon_dashboard.collectors.impl_collector import ImplementationCollector
from scripts.neon_dashboard.collectors.pm_collector import PMCollector
from scripts.neon_dashboard.config.settings import DopeLayoutSettings

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)


def load_settings() -> DopeLayoutSettings:
    """Read Dopemux config and extract dashboard settings."""
    cfg_manager = ConfigManager()
    config = cfg_manager.load_config()
    raw = {}
    if hasattr(config, "dope_layout"):
        raw = config.dope_layout.model_dump()  # type: ignore[attr-defined]
    return DopeLayoutSettings.from_dict(raw)


def format_duration(minutes: Optional[float]) -> str:
    """Convert minutes to a compact human readable string."""
    if not minutes:
        return "0m"
    total_minutes = int(minutes)
    hours, mins = divmod(total_minutes, 60)
    parts: List[str] = []
    if hours:
        parts.append(f"{hours}h")
    if mins or not parts:
        parts.append(f"{mins}m")
    return " ".join(parts)


STATUS_STYLE = {
    "IN_PROGRESS": ("#f5f26d", "IN PROGRESS"),
    "BLOCKED": ("#ff6b6b", "BLOCKED"),
    "TODO": ("#7dfbf6", "TODO"),
    "REVIEW": ("#ff8bd1", "REVIEW"),
    "DONE": ("#a6e3a1", "DONE"),
}


class DashboardFetcher:
    """Pulls operational, PM, and Prometheus data for the dashboard."""

    def __init__(self, settings: DopeLayoutSettings):
        self.settings = settings
        self.impl_collector = ImplementationCollector(settings.services)
        self.pm_collector = PMCollector(settings.pm_mode)
        prom_base = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
        self.prometheus = PrometheusClient(PrometheusConfig(base_url=prom_base))

    async def collect(self) -> Dict[str, Any]:
        impl_task = asyncio.create_task(self.impl_collector.get("impl"))
        pm_task = asyncio.create_task(self.pm_collector.get("pm"))
        prom_task = asyncio.create_task(self._prom_snapshot())

        impl = await self._safe_await(impl_task, {})
        pm = await self._safe_await(pm_task, {"epics": [], "sprint": {}})
        prom = await self._safe_await(prom_task, {"healthy": False})

        return {
            "impl": impl or {},
            "pm": pm or {"epics": [], "sprint": {}},
            "prom": prom,
        }

    async def close(self) -> None:
        await asyncio.gather(
            self.impl_collector.close(),
            self.pm_collector.close(),
            self.prometheus.close(),
            return_exceptions=True,
        )

    async def _safe_await(self, task: "asyncio.Task[Any]", fallback: Any) -> Any:
        try:
            return await task
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Collector failed: %s", exc, exc_info=True)
            return fallback

    async def _prom_snapshot(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {
            "healthy": False,
            "cognitive_load": None,
            "task_velocity": None,
            "flow_state": None,
        }
        try:
            healthy = await self.prometheus.health_check()
        except Exception as exc:
            logger.debug("Prometheus health check failed: %s", exc, exc_info=True)
            return snapshot

        snapshot["healthy"] = bool(healthy)
        if not healthy:
            return snapshot

        queries = await asyncio.gather(
            self.prometheus.query_instant("max(adhd_cognitive_load)"),
            self.prometheus.query_instant("adhd_task_velocity_per_day"),
            self.prometheus.query_instant("adhd_current_flow_state"),
            return_exceptions=True,
        )

        if not isinstance(queries[0], Exception):
            snapshot["cognitive_load"] = queries[0]
        if not isinstance(queries[1], Exception):
            snapshot["task_velocity"] = queries[1]
        if not isinstance(queries[2], Exception):
            snapshot["flow_state"] = queries[2]
        return snapshot


def create_layout() -> Layout:
    """Build the Rich layout scaffold."""
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


def render_header(prom_data: Dict[str, Any], sprint: Dict[str, Any]) -> Panel:
    """Header with branding and flow snapshot."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="center")
    grid.add_column(justify="right")

    flow_state = prom_data.get("flow_state")
    flow_label = "FLOW" if flow_state and flow_state >= 1 else "FOCUS"
    flow_style = "#a6e3a1" if flow_state and flow_state >= 1 else "#ff8bd1"
    sprint_name = sprint.get("name") or "Sprint"

    load = prom_data.get("cognitive_load")
    if load is None:
        load_text = "Load: N/A"
    else:
        load_text = f"Load: {load * 100:.0f}%"

    grid.add_row(
        "🎯 [bold #7dfbf6]ORCHESTRATOR[/]",
        f"[bold {flow_style}]{flow_label}[/] • {load_text}",
        f"[#94fadb]{datetime.now().strftime('%H:%M:%S')}[/]",
    )
    grid.add_row(
        "[dim]DOPE Layout[/]",
        f"[dim]{sprint_name}[/]",
        "[dim]Ctrl+C to exit[/]",
    )

    return Panel(grid, style="bold on #0a1628", border_style="#7dfbf6")


def render_status(
    impl_data: Dict[str, Any],
    prom_data: Dict[str, Any],
    mode: str,
) -> Panel:
    """Implementation status details."""
    table = Table.grid(padding=(0, 2))
    table.add_column(style="#94fadb", justify="right")
    table.add_column(style="bold")

    adhd = impl_data.get("adhd") or {}
    activity = impl_data.get("activity") or {}

    session = format_duration(adhd.get("session_minutes"))
    energy = adhd.get("energy") or "unknown"
    focus = adhd.get("focus") or "—"
    health = adhd.get("health")
    health_str = f"{health:.0%}" if isinstance(health, (int, float)) else "—"

    table.add_row("Mode:", f"[#ff8bd1]{mode.title()}[/]")
    table.add_row("Session:", f"[#7dfbf6]{session}[/]")
    table.add_row("Energy:", f"[#94fadb]{energy}[/]")
    table.add_row("Focus:", f"[#a6e3a1]{focus}[/]")
    table.add_row("Health:", f"[#94fadb]{health_str}[/]")

    context = activity.get("current_context")
    if context:
        table.add_row("Context:", f"[#ff8bd1]{context}[/]")

    if prom_data.get("healthy"):
        velocity = prom_data.get("task_velocity")
        if isinstance(velocity, (int, float)):
            table.add_row("Velocity:", f"[#a6e3a1]{velocity:.1f}/day[/]")

    return Panel(table, title="[bold #7dfbf6]Status[/]", border_style="#7dfbf6")


def render_services(impl_data: Dict[str, Any]) -> Panel:
    """Docker/MCP/LiteLLM health summary."""
    table = Table.grid(padding=(0, 1))
    table.add_column(style="bold")
    table.add_column()

    docker = impl_data.get("docker") or {}
    litellm = impl_data.get("litellm") or {}
    mcp = impl_data.get("mcp") or {}

    docker_total = docker.get("total")
    docker_healthy = docker.get("healthy")
    if docker_total is None:
        docker_text = "[dim]N/A[/]"
    elif docker_total == 0:
        docker_text = "[dim]0 containers[/]"
    else:
        style = "#a6e3a1" if docker_healthy == docker_total else "#f5f26d"
        docker_text = f"[{style}]{docker_healthy}/{docker_total} running[/]"

    mcp_healthy = mcp.get("healthy")
    mcp_text = (
        "[dim]N/A[/]"
        if mcp_healthy is None
        else f"[#7dfbf6]{mcp_healthy} healthy[/]"
    )

    cost = litellm.get("hourly_cost")
    latency = litellm.get("latency_ms")
    cost_text = "[dim]N/A[/]" if cost is None else f"[#ff8bd1]${cost:.2f}/hr[/]"
    latency_text = (
        "[dim]N/A[/]" if latency is None else f"[#f5f26d]{latency:.0f} ms[/]"
    )

    table.add_row("🤖 LiteLLM:", f"{cost_text} • {latency_text}")
    table.add_row("🐳 Docker:", docker_text)
    table.add_row("⚡ MCP:", mcp_text)

    return Panel(table, title="[bold #7dfbf6]Services[/]", border_style="#7dfbf6")


def render_metrics(impl_data: Dict[str, Any], prom_data: Dict[str, Any]) -> Panel:
    """Files, switches, and cost metrics."""
    table = Table.grid(padding=(0, 2))
    table.add_column(justify="right", style="#94fadb")
    table.add_column()

    git = impl_data.get("git") or {}
    activity = impl_data.get("activity") or {}
    litellm = impl_data.get("litellm") or {}

    files_changed = git.get("uncommitted")
    switches = activity.get("switches_15m")
    cost = litellm.get("hourly_cost")
    latency = litellm.get("latency_ms")
    load = prom_data.get("cognitive_load")

    files_str = str(files_changed) if files_changed is not None else "0"
    switches_str = str(switches) if switches is not None else "0"
    cost_str = f"${cost:.2f}/hr" if cost is not None else "N/A"
    latency_str = f"{latency:.0f} ms" if latency is not None else "N/A"
    load_str = f"{load * 100:.0f}%" if isinstance(load, (int, float)) else "N/A"

    table.add_row("Files Changed:", f"[bold]{files_str}[/]")
    table.add_row("Context Switches (15m):", f"[bold]{switches_str}[/]")
    table.add_row("LiteLLM Cost:", f"[bold]{cost_str}[/]")
    table.add_row("Latency:", f"[bold]{latency_str}[/]")
    table.add_row("Cognitive Load:", f"[bold]{load_str}[/]")

    if not prom_data.get("healthy"):
        table.add_row("", "[dim]Prometheus unreachable[/dim]")

    return Panel(table, title="[bold #7dfbf6]Metrics[/]", border_style="#7dfbf6")


def _task_sort_key(task: Dict[str, Any]) -> tuple[int, str]:
    status = (task.get("status") or "TODO").upper()
    order_map = {"IN_PROGRESS": 0, "BLOCKED": 1, "TODO": 2, "REVIEW": 3, "DONE": 4}
    return (order_map.get(status, 5), task.get("name") or "")


def render_active_tasks(pm_data: Dict[str, Any]) -> Panel:
    """Active task list from ConPort / Leantime feed."""
    table = Table(show_header=True, header_style="bold #7dfbf6", border_style="#7dfbf6")
    table.add_column("Task", style="#ff8bd1", overflow="fold")
    table.add_column("Progress", justify="center")
    table.add_column("ETA", justify="right", style="#94fadb")

    epics = pm_data.get("epics") or []
    tasks: List[Dict[str, Any]] = []
    for epic in epics:
        for task in epic.get("tasks", []):
            status = (task.get("status") or "TODO").upper()
            if status == "DONE":
                continue
            tasks.append(
                {
                    "name": task.get("name") or "Task",
                    "status": status,
                    "estimate": task.get("estimate"),
                    "spent": task.get("spent"),
                }
            )

    tasks.sort(key=_task_sort_key)
    if not tasks:
        table.add_row("[dim]No active tasks[/dim]", "—", "—")
    else:
        for task in tasks[:6]:
            status = task["status"]
            color, label = STATUS_STYLE.get(status, ("#7dfbf6", status.title()))
            name = task["name"]
            estimate = task.get("estimate")
            spent = task.get("spent")

            spent_val = spent if isinstance(spent, (int, float)) else 0.0
            estimate_val = estimate if isinstance(estimate, (int, float)) else None

            if estimate_val and estimate_val > 0:
                progress = max(min(spent_val / estimate_val * 100, 999), 0)
                progress_text = f"{spent_val:.1f}h / {estimate_val:.1f}h ({progress:.0f}%)"
                remaining = max(estimate_val - spent_val, 0.0)
                eta = f"{remaining:.1f}h" if remaining > 0 else "–"
            else:
                progress_text = f"{spent_val:.1f}h logged"
                eta = "—"

            table.add_row(
                f"[{color}]{label}[/{color}] {name}",
                progress_text,
                eta,
            )

    return Panel(table, title="[bold #7dfbf6]Active Tasks[/]", border_style="#7dfbf6")


def render_alerts(impl_data: Dict[str, Any]) -> Panel:
    """Alert block fed by Serena and git state."""
    serena = impl_data.get("serena") or {}
    git = impl_data.get("git") or {}

    text = Text()
    alerts: List[str] = []

    file_count = serena.get("file_count") or 0
    if file_count:
        age = serena.get("age_days")
        detail = f"{file_count} untracked files"
        if age:
            detail += f" • oldest {age}d"
        alerts.append(detail)

    uncommitted = git.get("uncommitted") or 0
    if uncommitted:
        alerts.append(f"{uncommitted} files pending commit")

    if alerts:
        for alert in alerts:
            text.append("⚠️  ", style="bold #f5f26d")
            text.append(f"{alert}\n", style="#f5f26d")
        text.append("💡 Press 'P' to plan work", style="dim")
    else:
        text.append("✅ No active alerts", style="#a6e3a1")

    return Panel(text, title="[bold #ff8bd1]Alerts[/]", border_style="#ff8bd1")


def render_footer() -> Panel:
    """Hotkey legend."""
    text = Text.from_markup(
        "[#7dfbf6]M[/] Mode  [#7dfbf6]P[/] Plan  [#7dfbf6]C[/] Commit  "
        "[#7dfbf6]D[/] Dismiss  [#7dfbf6]?[/] Help  [#7dfbf6]Q[/] Quit"
    )
    return Panel(text, style="dim on #0a1628", border_style="#7dfbf6")


def update_layout(layout: Layout, data: Dict[str, Any], mode: str) -> None:
    """Refresh every pane with the latest data snapshot."""
    impl = data.get("impl") or {}
    pm = data.get("pm") or {}
    prom = data.get("prom") or {}
    sprint = pm.get("sprint") or {}

    layout["header"].update(render_header(prom, sprint))
    layout["status"].update(render_status(impl, prom, mode))
    layout["services"].update(render_services(impl))
    layout["metrics"].update(render_metrics(impl, prom))
    layout["tasks"].update(render_active_tasks(pm))
    layout["alerts"].update(render_alerts(impl))
    layout["footer"].update(render_footer())


async def run_dashboard() -> None:
    """Async entrypoint for the Rich live dashboard."""
    settings = load_settings()
    fetcher = DashboardFetcher(settings)
    layout = create_layout()
    console = Console()

    initial_state = {"impl": {}, "pm": {"epics": [], "sprint": {}}, "prom": {"healthy": False}}
    update_layout(layout, initial_state, settings.default_mode)

    try:
        with Live(layout, console=console, screen=True, refresh_per_second=4):
            while True:
                snapshot = await fetcher.collect()
                update_layout(layout, snapshot, settings.default_mode)
                await asyncio.sleep(1.0)
    finally:
        await fetcher.close()


def main() -> None:
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        print("\n👋 Dashboard closed")


if __name__ == "__main__":
    main()
