"""Task detail pane for PM mode."""

from __future__ import annotations

from typing import Any, Dict, Optional

from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widgets import Static


class TaskDetailPane(Static):
    """Shows details for the currently selected task."""

    DEFAULT_CSS = """
    TaskDetailPane {
        padding: 1 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._task: Optional[Dict[str, Any]] = None
        self.show_placeholder("Select a task from the hierarchy (← → ↑ ↓, Enter)")

    def show_placeholder(self, message: str) -> None:
        text = Align.center(Text(message, style="dim"), vertical="middle")
        self.update(Panel(text, border_style="cyan"))

    def update_task(self, task: Optional[Dict[str, Any]]) -> None:
        if not task:
            self.show_placeholder("No task selected")
            return
        self._task = task
        table = Table.grid(padding=(0, 1), expand=True)
        table.add_column(justify="left", ratio=1)
        table.add_column(justify="right", ratio=1)

        status = (task.get("status") or "TODO").upper()
        table.add_row("Status", Text(status, style=self._status_style(status)))
        table.add_row("Estimate", Text(f"{task.get('estimate', 0)}h", style="bold"))
        table.add_row("Spent", Text(f"{task.get('spent', 0)}h", style="bold cyan"))

        description = task.get("description") or "No description provided."
        files = task.get("files") or []
        file_text = "\n".join(f"- {path}" for path in files) if files else "No linked files."

        body = Table.grid(padding=(1, 0), expand=True)
        body.add_column(justify="left")
        body.add_row(Text(description, overflow="fold"))
        body.add_row(Text(file_text, style="dim"))

        content = Table.grid(expand=True)
        content.add_row(table)
        content.add_row(body)

        panel = Panel(
            Align.center(content, vertical="top"),
            title=f"[bold #ff8bd1]{task.get('name', 'Task')}[/bold #ff8bd1]",
            border_style="#ff8bd1",
        )
        self.update(panel)

    @staticmethod
    def _status_style(status: str) -> str:
        return {
            "DONE": "green",
            "IN_PROGRESS": "yellow",
            "BLOCKED": "red",
        }.get(status, "dim")
