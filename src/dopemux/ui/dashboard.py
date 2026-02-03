# src/dopemux/ui/dashboard.py
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Sparkline
from textual.reactive import reactive
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
import httpx
import asyncio

class ADHDStatePanel(Static):
    """Top panel - critical state (Tier 1)"""

    energy = reactive("medium")
    attention = reactive("focused")
    cognitive_load = reactive(0.65)
    in_flow = reactive(False)
    break_in = reactive(15)
    is_connected = reactive(True)

    def compose(self) -> ComposeResult:
        yield Static(id="adhd-state")

    async def on_mount(self) -> None:
        self.set_interval(1.0, self.update_state)

    async def update_state(self) -> None:
        async with httpx.AsyncClient() as client:
            try:
                # ADHD Engine at 8001
                resp = await client.get("http://localhost:8001/api/v1/state?user_id=default", timeout=0.5)
                if resp.status_code == 200:
                    data = resp.json()
                    self.energy = data.get("energy_level", "medium")
                    self.attention = data.get("attention_state", "focused")
                    self.cognitive_load = data.get("cognitive_load", 0.5)
                    self.in_flow = data.get("flow_state", {}).get("active", False)
                    # Use a default if break warning structure is missing
                    self.break_in = data.get("break_warning", {}).get("minutes_until", 99)
                    self.is_connected = True
                else:
                    self.is_connected = False
            except Exception:
                self.is_connected = False


    def render(self) -> Panel:
        if not self.is_connected:
            return Panel(
                Text("⚠️  ADHD Engine Disconnected", style="bold red", justify="center"),
                title="ADHD STATE",
                border_style="$red"
            )

        # Create rich panel with current state
        energy_icon = {"high": "⚡↑", "medium": "⚡=", "low": "⚡↓"}.get(self.energy, "⚡")
        attention_icon = {"focused": "👁️●", "scattered": "👁️🌀"}.get(self.attention, "👁️")
        load_bar = self._make_gauge(self.cognitive_load)
        flow_status = "🌊 Active" if self.in_flow else ""
        break_warning = f"☕ in {self.break_in}m" if self.break_in < 20 else ""

        table = Table.grid(padding=1)
        table.add_column(style="bold $green")
        table.add_column(style="bold $mauve")
        table.add_column(style="bold $yellow")

        table.add_row(
            f"{energy_icon} {self.energy.title()}",
            f"{attention_icon} {self.attention.title()}",
            f"🧠 {load_bar} {int(self.cognitive_load * 100)}%"
        )
        table.add_row(flow_status, break_warning, "")

        return Panel(table, title="ADHD STATE", border_style="$green")

    def _make_gauge(self, value: float) -> str:
        """Create ASCII gauge"""
        filled = int(value * 10)
        return f"[{'|' * filled}{'·' * (10 - filled)}]"

class ProductivityPanel(Static):
    """Tasks and velocity metrics (Tier 2)"""

    tasks_completed = reactive(8)
    tasks_total = reactive(10)
    decisions_today = reactive(23)
    velocity = reactive([3, 4, 5, 5, 6, 7, 6, 5, 4])  # sparkline data

    async def on_mount(self) -> None:
        self.set_interval(30.0, self.update_metrics)

    async def update_metrics(self) -> None:
        async with httpx.AsyncClient() as client:
            try:
                # ADHD Engine tasks API at 8001
                tasks_resp = await client.get("http://localhost:8001/api/v1/tasks")
                if tasks_resp.status_code == 200:
                    tasks_data = tasks_resp.json()
                    self.tasks_completed = tasks_data.get("completed", 0)
                    self.tasks_total = tasks_data.get("total", 0)
                
                # ConPort decisions API at 8005
                decisions_resp = await client.get("http://localhost:8005/api/adhd/decisions/recent")
                if decisions_resp.status_code == 200:
                    decisions_data = decisions_resp.json()
                    self.decisions_today = len(decisions_data.get("today", []))
            except Exception:
                pass


    def render(self) -> Panel:
        completion_rate = self.tasks_completed / self.tasks_total if self.tasks_total > 0 else 0
        bar = "█" * int(completion_rate * 10) + "░" * (10 - int(completion_rate * 10))

        sparkline = "".join(["▁▂▃▄▅▆▇█"[min(v, 7)] for v in self.velocity])

        table = Table.grid(padding=1)
        table.add_column()
        table.add_column()

        table.add_row(
            f"Tasks: {self.tasks_completed}/{self.tasks_total} ({int(completion_rate * 100)}%) {bar}",
            f"Decisions: {self.decisions_today} (↑5 today)"
        )
        table.add_row(
            f"Velocity: {sparkline} 7.2/day",
            f"Completion Rate: {int(completion_rate * 100)}% (target: 85%)"
        )

        return Panel(table, title="PRODUCTIVITY", border_style="blue")

class ServicesGrid(Static):
    """Service health matrix (Tier 2)"""

    def compose(self) -> ComposeResult:
        yield DataTable(id="services")

    async def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Service", "Status", "Latency", "Metrics")

        self.set_interval(30.0, self.update_services)
        await self.update_services()

    async def update_services(self) -> None:
        table = self.query_one(DataTable)
        table.clear()

        # Fetch all service health
        services = [
            ("ConPort", "http://localhost:8005/health"),
            ("ADHD Engine", "http://localhost:8001/health"),
            ("Serena", "http://localhost:8003/health"),
            ("MCP Bridge", "http://localhost:8002/health"),
        ]

        async with httpx.AsyncClient() as client:
            for name, url in services:
                try:
                    resp = await client.get(url, timeout=2.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        status = "✓" if data.get("status") == "healthy" else "✗"
                        latency = f"{data.get('latency_ms', 0)}ms"
                        metrics = str(data.get("metrics", ""))
                        table.add_row(name, status, latency, metrics)
                    else:
                        table.add_row(name, "✗", "error", str(resp.status_code))
                except Exception as e:
                    table.add_row(name, "✗", "timeout", str(e)[:20])

class TrendsPanel(Static):
    """Sparkline trends (Tier 3)"""

    cognitive_history = reactive([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3])
    velocity_history = reactive([3, 4, 5, 5, 6, 7, 6, 5, 4, 3, 2, 1])
    switches_history = reactive([2, 1, 2, 3, 5, 3, 2, 1, 2, 1, 1, 1])

    def render(self) -> Panel:
        def sparkline(data):
            chars = "▁▂▃▄▅▆▇█"
            normalized = [int((v / (max(data) or 1)) * 7) for v in data]
            return "".join([chars[min(i, 7)] for i in normalized])

        table = Table.grid(padding=1)
        table.add_column(style="dim")
        table.add_column()
        table.add_column(style="dim")

        table.add_row("Cognitive Load:", sparkline(self.cognitive_history), "(last 2h)")
        table.add_row("Task Velocity:", sparkline(self.velocity_history), "(last 7d)")
        table.add_row("Context Switches:", sparkline(self.switches_history), "(last 24h)")

        return Panel(table, title="TRENDS", border_style="yellow")

class DopemuxDashboard(App):
    """Main Textual dashboard app"""

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
    $overlay0: #6c7086;

    Screen {
        background: $base;
        color: $text;
    }

    #adhd-state {
        height: 6;
        border: solid $green;
        background: $mantle;
    }

    #productivity {
        height: 6;
        border: solid $blue;
        background: $mantle;
    }

    #services {
        height: 8;
        border: solid $mauve;
        background: $mantle;
    }

    #trends {
        height: 6;
        border: solid $peach;
        background: $mantle;
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
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_tasks", "Tasks"),
        ("s", "toggle_services", "Services"),
        ("p", "toggle_patterns", "Patterns"),
        ("d", "show_detail", "Detail"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield ADHDStatePanel(id="adhd-state")
        yield ProductivityPanel(id="productivity")
        yield ServicesGrid(id="services")
        yield TrendsPanel(id="trends")
        yield Footer()

    def action_show_detail(self) -> None:
        """Open tmux popup with detailed view"""
        import subprocess
        import sys
        from pathlib import Path
        
        # Locate the detail script relative to this file
        current_dir = Path(__file__).parent.resolve()
        detail_script = current_dir / "dashboard_detail.py"
        
        if not detail_script.exists():
            return

        # Use tmux display-popup to show the detail view
        cmd = [
            "tmux", "display-popup",
            "-E",          # Close popup on exit
            "-w", "95%",   # Width
            "-h", "90%",   # Height
            "-T", "Dopemux Details", # Title
            f"{sys.executable} {detail_script}"
        ]
        
        try:
            subprocess.run(cmd, check=False)
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

if __name__ == "__main__":
    app = DopemuxDashboard()
    app.run()
