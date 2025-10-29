"""Rich-powered metrics bar for the Dope layout."""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dopemux.config import ConfigManager  # noqa: E402

from scripts.neon_dashboard.collectors.impl_collector import ImplementationCollector  # noqa: E402
from scripts.neon_dashboard.collectors.pm_collector import PMCollector  # noqa: E402
from scripts.neon_dashboard.config.settings import DopeLayoutSettings  # noqa: E402
from scripts.neon_dashboard.core.state import DashboardStateStore  # noqa: E402


def load_settings() -> DopeLayoutSettings:
    cfg_manager = ConfigManager()
    config = cfg_manager.load_config()
    raw = {}
    if hasattr(config, "dope_layout"):
        raw = config.dope_layout.model_dump()  # type: ignore[attr-defined]
    return DopeLayoutSettings.from_dict(raw)


def format_impl_metrics(payload: Dict[str, Any]) -> Text:
    adhd = payload.get("adhd") or {}
    activity = payload.get("activity") or {}
    serena = payload.get("serena") or {}
    docker = payload.get("docker") or {}
    mcp = payload.get("mcp") or {}
    litellm = payload.get("litellm") or {}

    parts = [
        f"Energy {adhd.get('energy', 'N/A')}",
        f"Session {adhd.get('session_minutes', 0)}m",
        f"Switches {activity.get('switches_15m', 0)}",
        f"Uncommitted {payload.get('git', {}).get('uncommitted', 0)}",
        f"Untracked {serena.get('file_count', 0)}",
        f"MCP {mcp.get('healthy', 'N/A')}",
        f"Docker {docker.get('healthy', 0)}/{docker.get('total', 0)}",
    ]
    cost = litellm.get("hourly_cost")
    if cost is not None:
        parts.append(f"Cost ${cost:.2f}/h")
    latency = litellm.get("latency_ms")
    if latency is not None:
        parts.append(f"Latency {latency:.0f}ms")
    text = Text(" | ".join(parts), style="bold cyan")
    return text


def format_pm_metrics(payload: Dict[str, Any]) -> Text:
    sprint = payload.get("sprint") or {}
    parts = [
        f"Sprint {sprint.get('progress', 0)}%",
        f"Today {sprint.get('today_focus', '—')}",
        f"Overdue {sprint.get('overdue_tasks', 0)}",
        f"Active {sprint.get('active_tasks', 0)}",
        f"Blocked {sprint.get('blocked_tasks', 0)}",
        f"Completed {sprint.get('completed_tasks', 0)}",
        f"Est {sprint.get('estimate_hours', 0)}h",
        f"Spent {sprint.get('spent_hours', 0)}h",
    ]
    return Text(" | ".join(parts), style="bold magenta")


async def run_metrics_bar(settings: DopeLayoutSettings) -> None:
    state_store = DashboardStateStore(settings)
    await state_store.load()

    impl_collector = ImplementationCollector(settings.services)
    pm_collector = PMCollector(settings.pm_mode)

    console = Console()

    stop_event = asyncio.Event()

    def _handle_signal(*_: object) -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except NotImplementedError:  # pragma: no cover
            signal.signal(sig, lambda *_: stop_event.set())

    refresh_interval = 5.0
    with Live(console=console, refresh_per_second=4) as live:
        while not stop_event.is_set():
            state = state_store.state
            if state.mode == "implementation":
                impl_data = await impl_collector.get("impl")
                text = format_impl_metrics(impl_data or {})
                panel = Panel(text, style="bold", border_style="#7dfbf6")
            else:
                pm_data = await pm_collector.get("pm")
                text = format_pm_metrics(pm_data or {})
                panel = Panel(text, style="bold", border_style="#ff8bd1")
            live.update(panel)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=refresh_interval)
            except asyncio.TimeoutError:
                continue

    await impl_collector.close()
    await pm_collector.close()


def main() -> None:
    settings = load_settings()
    asyncio.run(run_metrics_bar(settings))


if __name__ == "__main__":
    main()
