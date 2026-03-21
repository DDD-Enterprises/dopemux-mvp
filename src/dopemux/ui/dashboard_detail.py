"""Dopemux Dashboard Detail View — tmux popup companion.

Opened via the ``d`` keybinding in the main dashboard (tmux display-popup).
"""

from __future__ import annotations

import sys

import httpx
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Log, TabbedContent, TabPane

from .theme import Glyphs
from .voice import VoiceEngine, VoiceMode


VOICE = VoiceEngine(mode=VoiceMode.CLINICAL_FORENSICS, is_scattered=True)


class DetailApp(App):
    """Detailed view for Dopemux popup."""

    CSS_PATH = "dopemux.tcss"
    TITLE = f"{Glyphs.BRAND_MARK} Dopemux Details"
    SUB_TITLE = "Flight deck detail feed"

    BINDINGS = [
        ("q", "quit", "Close Popup"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._warned_feeds: set[str] = set()

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="tasks"):
            with TabPane("Tasks & Decisions", id="tasks"):
                yield DataTable(id="task_table")
            with TabPane("Recent Activity", id="activity"):
                yield Log(id="activity_log")
            with TabPane("System Health", id="health"):
                yield DataTable(id="health_table")
        yield Footer()

    async def on_mount(self) -> None:
        task_table = self.query_one("#task_table", DataTable)
        task_table.add_columns("ID", "Type", "Summary", "Status")

        health_table = self.query_one("#health_table", DataTable)
        health_table.add_columns("Service", "Status", "Latency (ms)", "Version")

        activity_log = self.query_one("#activity_log", Log)
        activity_log.write_line(VOICE.banner("detail"))
        activity_log.write_line("[LOGGED] Detail cockpit live. Receipt: data refresh every 2s.")
        activity_log.write_line(f"[AFTERCARE] {VOICE.get_aftercare()}")

        self.set_interval(2.0, self.refresh_data)
        await self.refresh_data()

    async def refresh_data(self) -> None:
        async with httpx.AsyncClient() as client:
            # Tasks
            try:
                resp = await client.get("http://localhost:8001/api/v1/tasks", timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json().get("recent_tasks", [])
                    table = self.query_one("#task_table", DataTable)
                    table.clear()
                    for t in data[:20]:
                        table.add_row(
                            t.get("id", "")[:8],
                            "Task",
                            t.get("description", ""),
                            t.get("status", ""),
                        )
            except Exception:
                if "tasks" not in self._warned_feeds:
                    self.query_one("#activity_log", Log).write_line(
                        "[BLOCKER] Task feed offline. Receipt: cached detail view only."
                    )
                    self._warned_feeds.add("tasks")

            # Decisions (ConPort)
            try:
                resp = await client.get(
                    "http://localhost:8005/api/adhd/decisions/recent", timeout=1.0
                )
                if resp.status_code == 200:
                    decisions = resp.json().get("today", [])
                    table = self.query_one("#task_table", DataTable)
                    for d in decisions[:10]:
                        table.add_row(
                            d.get("id", "")[:8],
                            "Decision",
                            d.get("description", ""),
                            "Logged",
                        )
            except Exception:
                if "decisions" not in self._warned_feeds:
                    self.query_one("#activity_log", Log).write_line(
                        "[EDGE] Decision feed quiet. NEXT: verify ConPort health if this persists."
                    )
                    self._warned_feeds.add("decisions")

            # Health
            health_table = self.query_one("#health_table", DataTable)
            health_table.clear()
            services = [
                ("ADHD Engine", "http://localhost:8001/health"),
                ("Serena", "http://localhost:8003/health"),
                ("ConPort", "http://localhost:8005/health"),
            ]
            for name, url in services:
                try:
                    r = await client.get(url, timeout=0.5)
                    status = "✓" if r.status_code == 200 else "✗"
                    lat = f"{r.elapsed.microseconds / 1000:.1f}"
                    health_table.add_row(name, status, lat, "v1")
                except Exception:
                    health_table.add_row(name, "✗", "-", "-")


if __name__ == "__main__":
    app = DetailApp()
    app.run()
