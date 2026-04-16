"""Dopemux Dashboard Detail View — tmux popup companion.

Opened via the ``d`` keybinding in the main dashboard (tmux display-popup).
"""

from __future__ import annotations

from datetime import datetime, timezone
import sys

import httpx
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Log, TabbedContent, TabPane

from .service_endpoints import refresh_age_label, resolve_dashboard_endpoints
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
        self._last_refresh_at: datetime | None = None

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
        health_table.add_columns("Service", "Status", "Latency (ms)", "Version", "Source", "Updated")

        activity_log = self.query_one("#activity_log", Log)
        activity_log.write_line(VOICE.banner("detail"))
        activity_log.write_line("[LOGGED] Detail cockpit live. Receipt: data refresh every 2s.")
        activity_log.write_line(f"[AFTERCARE] {VOICE.get_aftercare()}")
        endpoints = resolve_dashboard_endpoints()
        activity_log.write_line(
            "[LIVE] Endpoint sources locked: "
            f"ADHD={endpoints['adhd'].source}, "
            f"Bridge={endpoints['bridge'].source}, "
            f"ConPort={endpoints['conport'].source}, "
            f"Serena={endpoints['serena'].source}."
        )

        self.set_interval(2.0, self.refresh_data)
        await self.refresh_data()

    async def refresh_data(self) -> None:
        endpoints = resolve_dashboard_endpoints()
        task_table = self.query_one("#task_table", DataTable)
        task_table.clear()
        async with httpx.AsyncClient() as client:
            # Tasks
            try:
                resp = await client.get(endpoints["adhd"].url("/api/v1/tasks"), timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json().get("recent_tasks", [])
                    for t in data[:20]:
                        task_table.add_row(
                            t.get("id", "")[:8],
                            "Task",
                            t.get("description", ""),
                            t.get("status", ""),
                        )
            except Exception:
                if "tasks" not in self._warned_feeds:
                    self.query_one("#activity_log", Log).write_line(
                        "[BLOCKER] Task feed offline. NEXT: verify the resolved ADHD Engine endpoint or restart the feed."
                    )
                    self._warned_feeds.add("tasks")

            # Decisions (Bridge-backed)
            try:
                resp = await client.get(
                    endpoints["bridge"].url("/ddg/decisions?limit=10"), timeout=1.0
                )
                if resp.status_code == 200:
                    decisions = resp.json().get("items", [])
                    for d in decisions[:10]:
                        task_table.add_row(
                            d.get("id", "")[:8],
                            "Decision",
                            d.get("summary", d.get("description", "")),
                            "Logged",
                        )
            except Exception:
                if "decisions" not in self._warned_feeds:
                    self.query_one("#activity_log", Log).write_line(
                        "[EDGE] Decision feed quiet. NEXT: verify the resolved bridge endpoint and decision store health."
                    )
                    self._warned_feeds.add("decisions")

            # Health
            health_table = self.query_one("#health_table", DataTable)
            health_table.clear()
            services = [
                (endpoints["adhd"], "/health"),
                (endpoints["serena"], "/health"),
                (endpoints["conport"], "/health"),
                (endpoints["bridge"], "/kg/health"),
            ]
            sampled_at = datetime.now(timezone.utc)
            for endpoint, health_path in services:
                try:
                    r = await client.get(endpoint.url(health_path), timeout=0.5)
                    status = "✓" if r.status_code == 200 else "✗"
                    lat = f"{r.elapsed.microseconds / 1000:.1f}"
                    version = "v1"
                    if r.status_code == 200:
                        try:
                            version = str(r.json().get("version", "v1"))
                        except Exception:
                            version = "v1"
                    health_table.add_row(
                        endpoint.name,
                        status,
                        lat,
                        version,
                        endpoint.source,
                        refresh_age_label(sampled_at),
                    )
                except Exception:
                    health_table.add_row(
                        endpoint.name,
                        "✗",
                        "-",
                        "-",
                        endpoint.source,
                        refresh_age_label(sampled_at),
                    )
            self._last_refresh_at = sampled_at


if __name__ == "__main__":
    app = DetailApp()
    app.run()
