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
        table.add_row("Docker containers", docker_text)

        mcp_val = mcp.get("healthy")
        if mcp_val is None:
            mcp_text = Text("N/A", style="dim")
        else:
            mcp_text = Text(str(mcp_val), style="cyan")
        table.add_row("MCP servers", mcp_text)

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

