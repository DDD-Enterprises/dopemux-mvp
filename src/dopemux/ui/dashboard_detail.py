from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, TabbedContent, TabPane, Log
from textual.containers import Container
from rich.table import Table
from rich.text import Text
import httpx
import asyncio
import sys

class DetailApp(App):
    """Detailed view for Dopemux popup."""
    
    CSS = """
    /* Catppuccin Mocha Palette */
    $base: #1e1e2e;
    $mantle: #181825;
    $crust: #11111b;
    $text: #cdd6f4;
    $green: #a6e3a1;
    $blue: #89b4fa;
    $mauve: #cba6f7;
    $red: #f38ba8;
    $peach: #fab387;
    $yellow: #f9e2af;
    $lavender: #b4befe;
    $surface0: #313244;
    $surface1: #45475a;

    Screen {
        background: $base;
        color: $text;
    }
    
    TabbedContent {
        background: $mantle;
        border: solid $surface1;
    }
    
    TabPane {
        background: $mantle;
        padding: 1;
    }
    
    DataTable {
        background: $mantle;
        color: $text;
        border: none;
    }
    
    DataTable > .datatable--header {
        background: $crust;
        color: $lavender;
        text-style: bold;
    }
    
    Log {
        background: $crust;
        color: $text;
        border: solid $surface0;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Close Popup"),
    ]

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
        # Initialize tables
        task_table = self.query_one("#task_table", DataTable)
        task_table.add_columns("ID", "Type", "Summary", "Status")
        
        health_table = self.query_one("#health_table", DataTable)
        health_table.add_columns("Service", "Status", "Latency (ms)", "Version")
        
        # Start data fetch
        self.set_interval(2.0, self.refresh_data)
        await self.refresh_data()

    async def refresh_data(self) -> None:
        async with httpx.AsyncClient() as client:
            # 1. Fetch Tasks (Mock/Real)
            try:
                resp = await client.get("http://localhost:8001/api/v1/tasks", timeout=1.0)
                if resp.status_code == 200:
                    data = resp.json().get("recent_tasks", [])
                    table = self.query_one("#task_table", DataTable)
                    table.clear()
                    for t in data[:20]:
                        table.add_row(t.get("id", "")[:8], "Task", t.get("description", ""), t.get("status", ""))
            except Exception:
                pass

            # 2. Fetch Decisions (ConPort)
            try:
                resp = await client.get("http://localhost:8005/api/adhd/decisions/recent", timeout=1.0)
                if resp.status_code == 200:
                    decisions = resp.json().get("today", [])
                    table = self.query_one("#task_table", DataTable)
                    # Append decisions (this is naive, normally would merge)
                    for d in decisions[:10]:
                        table.add_row(d.get("id", "")[:8], "Decision", d.get("description", ""), "Logged")
            except Exception:
                pass

            # 3. Fetch Health
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
                except:
                    health_table.add_row(name, "✗", "-", "-")

if __name__ == "__main__":
    app = DetailApp()
    app.run()
