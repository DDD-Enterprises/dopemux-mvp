"""Implementation-mode monitor pane."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widgets import Static


@dataclass(slots=True)
class ADHDMonitorPayload:
    energy: Any
    session_minutes: int
    health: Optional[Any]
    focus: Optional[Any]
    switches_15m: int
    untracked_files: int
    untracked_age: int
    untracked_confidence: float
    files: List[str]


class ADHDMonitorPane(Static):
    """Displays ADHD engine metrics + Serena untracked work."""

    DEFAULT_CSS = """
    ADHDMonitorPane {
        padding: 1 1;
        height: 100%;
        overflow-y: auto;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._last_payload: Optional[ADHDMonitorPayload] = None

    def compose_renderable(self, payload: ADHDMonitorPayload):
        metrics = Table.grid(expand=True)
        metrics.add_column(justify="left")
        metrics.add_column(justify="right")
        metrics.add_row("Energy", Text(str(payload.energy), style="bold magenta"))
        metrics.add_row("Session", Text(f"{payload.session_minutes}m", style="cyan"))
        metrics.add_row("Focus", Text(str(payload.focus or "—"), style="bold cyan"))
        metrics.add_row(
            "Context Switches (15m)",
            Text(str(payload.switches_15m), style="yellow"),
        )

        untracked = Table.grid(expand=True)
        untracked.add_column(justify="left", ratio=1)
        untracked.add_column(justify="right", ratio=1)
        untracked.add_row("Files", Text(str(payload.untracked_files), style="yellow"))
        untracked.add_row("Age", Text(f"{payload.untracked_age}d", style="yellow"))
        untracked.add_row(
            "Confidence",
            Text(f"{payload.untracked_confidence:.2f}", style="yellow"),
        )

        files_table = Table.grid(expand=True)
        files_table.add_column(justify="left")
        if payload.files:
            for f in payload.files[:20]:
                files_table.add_row(Text(f, style="dim"))
        else:
            files_table.add_row(Text("No untracked files", style="dim"))

        layout = Table.grid(expand=True, padding=(0, 1))
        layout.add_column(ratio=1)
        layout.add_column(ratio=1)
        layout.add_row(metrics, Panel(untracked, title="Untracked Work", border_style="yellow"))
        layout.add_row(Panel(files_table, title="Untracked Files", border_style="cyan"), Text(""))

        return Panel(
            layout,
            title="[bold #7dfbf6]Implementation Monitor[/bold #7dfbf6]",
            border_style="bright_magenta",
        )

    def update_from_sources(self, data: Dict[str, Any]) -> None:
        adhd = data.get("adhd") or {}
        activity = data.get("activity") or {}
        serena = data.get("serena") or {}
        payload = ADHDMonitorPayload(
            energy=adhd.get("energy", "N/A"),
            session_minutes=int(adhd.get("session_minutes") or 0),
            health=adhd.get("health"),
            focus=adhd.get("focus"),
            switches_15m=int(activity.get("switches_15m") or 0),
            untracked_files=int(serena.get("file_count") or 0),
            untracked_age=int(serena.get("age_days") or 0),
            untracked_confidence=float(serena.get("confidence") or 0.0),
            files=list(serena.get("files") or []),
        )
        self._last_payload = payload
        self.update(self.compose_renderable(payload))
