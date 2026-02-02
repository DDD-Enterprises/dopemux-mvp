"""System health monitor pane."""

from __future__ import annotations

from typing import Any, Dict

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widgets import Static


class SystemMonitorPane(Static):
    """Displays Docker, MCP, LiteLLM, and log hints."""

    DEFAULT_CSS = """
    SystemMonitorPane {
        padding: 1 1;
        height: 100%;
        overflow-y: auto;
    }
    """

    def update_from_sources(self, data: Dict[str, Any]) -> None:
        docker = data.get("docker") or {}
        mcp = data.get("mcp") or {}
        litellm = data.get("litellm") or {}

        table = Table.grid(expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="right", ratio=1)

        total = docker.get("total") or 0
        healthy = docker.get("healthy") or 0
        docker_text = Text(f"{healthy}/{total}", style="green" if healthy == total else "red")
        table.add_row("Docker", docker_text)
        for c in docker.get("containers", [])[:25]:
            state_style = "green" if c["state"].startswith("up") else "red"
            table.add_row(f"  {c['name']}", Text(c['state'], style=state_style))
        # Compose services (normalized view)
        compose = docker.get("compose") or {}
        if compose:
            table.add_row("Compose Services", Text("", style="dim"))
            for svc, meta in compose.items():
                s = meta.get("state", "missing")
                style = "green" if s.startswith("up") else ("yellow" if s != "missing" else "red")
                table.add_row(f"  {svc}", Text(s, style=style))

        mcp_services = (mcp.get("services") or {})
        for server, info in mcp_services.items():
            style = "green" if info.get("healthy") else "red"
            latency = info.get("latency_ms")
            lat_text = f" {latency}ms" if latency is not None else ""
            table.add_row(f"MCP {server}", Text(("up" if info.get("healthy") else "down") + lat_text, style=style))

        cost = litellm.get("hourly_cost")
        if cost is None:
            cost_text = Text("N/A", style="dim")
        else:
            cost_text = Text(f"${cost:.2f}/hr", style="magenta")
        latency = litellm.get("latency_ms")
        latency_text = Text("N/A", style="dim") if latency is None else Text(f"{latency:.0f} ms", style="yellow")
        table.add_row("LiteLLM cost", cost_text)
        table.add_row("LiteLLM latency", latency_text)

        panel = Panel(
            table,
            title="[bold #9b78ff]Systems Monitor[/bold #9b78ff]",
            border_style="#9b78ff",
        )
        self.update(panel)

