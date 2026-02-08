---
id: DASHBOARD_DAY10_IMPLEMENTATION_READY
title: Dashboard_Day10_Implementation_Ready
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dashboard_Day10_Implementation_Ready (explanation) for dopemux documentation
  and developer workflows.
---
# Dashboard Day 10 - Implementation Ready! 🚀
# Drill-Downs, Interactions & Hardening

**Date:** 2025-10-29
**Status:** ✅ READY TO IMPLEMENT
**Research:** Complete (29KB deep dive)
**Estimated Time:** 10-12 hours

---

## 🎯 QUICK START - WHAT TO BUILD

### Overview
Build 5 drill-down screens, context menus, search, and production hardening on top of Day 9's sparklines and keyboard navigation.

### What Already Exists ✅
- ✅ SparklineGenerator (Day 9)
- ✅ Keyboard navigation (Day 9)
- ✅ MetricsManager with WebSocket (Day 8)
- ✅ Base dashboard architecture (Days 1-7)

### What We're Adding (Day 10)
1. **Drill-Down Screens** (~400 lines)
2. **Context Menu System** (~200 lines)
3. **Search System** (~150 lines)
4. **Error Boundaries** (~100 lines)
5. **Crash Recovery** (~100 lines)
6. **Tests** (~300 lines)

**Total New Code:** ~1,250 lines
**Time:** 10-12 hours

---

## 📋 TASK 1: DRILL-DOWN SCREENS (4-5 hours)

### 1.1 Base DrillDownScreen Class

**File:** `dopemux_dashboard.py` (add to existing file)

```python
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable
from textual.containers import Container, Vertical, Horizontal
from typing import Dict, Any, Optional
import httpx

class DrillDownScreen(Screen):
    """Base class for all drill-down screens"""

    CSS = """
    DrillDownScreen {
        background: $surface;
    }

    DrillDownScreen Container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    DrillDownScreen .loading {
        content-align: center middle;
        color: $accent;
    }

    DrillDownScreen .error {
        content-align: center middle;
        color: $error;
        border: thick $error;
    }
    """

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(self, title: str):
        super().__init__()
        self.screen_title = title
        self.data = None
        self.loading = True

    def compose(self) -> ComposeResult:
        """Compose screen layout"""
        yield Header()
        yield Container(
            Static("Loading...", id="content", classes="loading"),
            id="main-container"
        )
        yield Footer()

    async def on_mount(self):
        """Load data when screen appears"""
        await self.load_data()

    async def load_data(self):
        """Override in subclasses"""
        try:
            self.show_loading()
            self.data = await self.fetch_data()
            self.render_content()
        except Exception as e:
            self.show_error(e)

    async def fetch_data(self) -> Dict[str, Any]:
        """Override in subclasses - fetch from API"""
        raise NotImplementedError

    def render_content(self):
        """Override in subclasses - render data to UI"""
        raise NotImplementedError

    def show_loading(self):
        """Show loading state"""
        content = self.query_one("#content")
        content.update("⏳ Loading...")
        content.add_class("loading")

    def show_error(self, error: Exception):
        """Show error state"""
        content = self.query_one("#content")
        content.update(
            Panel(
                f"[red]Error:[/red]\n\n{str(error)}\n\n"
                f"Press [cyan]r[/cyan] to retry or [cyan]Esc[/cyan] to go back",
                title="⚠️  Error",
                border_style="red"
            )
        )
        content.remove_class("loading")
        content.add_class("error")

    async def action_refresh(self):
        """Refresh data"""
        await self.load_data()
```

---

### 1.2 TaskDetailScreen

**Purpose:** Show detailed task view with history, context, and decisions.

```python
class TaskDetailScreen(DrillDownScreen):
    """Detailed task view"""

    CSS = """
    TaskDetailScreen {
        layout: grid;
        grid-size: 2 3;
        grid-gutter: 1 2;
    }

    #task-info { column-span: 2; }
    #task-history { row-span: 2; }
    """

    def __init__(self, task_id: str):
        super().__init__(title=f"Task: {task_id}")
        self.task_id = task_id

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch task data from ADHD Engine"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://localhost:8000/tasks/{self.task_id}",
                timeout=5.0
            )
            resp.raise_for_status()
            return resp.json()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(id="task-info"),
            DataTable(id="task-history"),
            Static(id="task-context"),
            Static(id="task-decisions"),
            Static(id="task-stats"),
            id="task-detail-grid"
        )
        yield Footer()

    def render_content(self):
        """Render task details"""
        # Task info panel
        info_panel = Panel(
            f"[cyan]ID:[/cyan] {self.data['id']}\n"
            f"[cyan]Title:[/cyan] {self.data['title']}\n"
            f"[cyan]Status:[/cyan] {self.data['status']}\n"
            f"[cyan]Priority:[/cyan] {self.data['priority']}\n"
            f"[cyan]Created:[/cyan] {self.data['created_at']}\n"
            f"[cyan]Updated:[/cyan] {self.data['updated_at']}",
            title="📋 Task Details",
            border_style="cyan"
        )
        self.query_one("#task-info").update(info_panel)

        # History table
        table = self.query_one("#task-history")
        table.add_columns("Time", "Event", "Details")
        for event in self.data.get("history", []):
            table.add_row(
                event["timestamp"],
                event["type"],
                event["details"]
            )

        # Context panel
        context = self.data.get("context", {})
        context_panel = Panel(
            f"[cyan]Session:[/cyan] {context.get('session_id', 'N/A')}\n"
            f"[cyan]Energy:[/cyan] {context.get('energy_level', 'N/A')}\n"
            f"[cyan]Focus:[/cyan] {context.get('focus_score', 'N/A')}",
            title="🎯 Context",
            border_style="yellow"
        )
        self.query_one("#task-context").update(context_panel)

        # Decisions panel
        decisions = self.data.get("decisions", [])
        decisions_text = "\n".join([
            f"• {d['timestamp']}: {d['decision']}"
            for d in decisions[:5]
        ])
        decisions_panel = Panel(
            decisions_text or "No decisions recorded",
            title="🧠 Decisions",
            border_style="magenta"
        )
        self.query_one("#task-decisions").update(decisions_panel)

        # Stats panel
        stats = self.data.get("stats", {})
        stats_panel = Panel(
            f"[cyan]Time spent:[/cyan] {stats.get('time_spent', '0')}min\n"
            f"[cyan]Interruptions:[/cyan] {stats.get('interruptions', 0)}\n"
            f"[cyan]Context switches:[/cyan] {stats.get('context_switches', 0)}",
            title="📊 Stats",
            border_style="green"
        )
        self.query_one("#task-stats").update(stats_panel)
```

**Acceptance Criteria:**
- [ ] Shows task details (ID, title, status, priority)
- [ ] Shows event history in sortable table
- [ ] Shows context (session, energy, focus)
- [ ] Shows decisions made during task
- [ ] Shows stats (time, interruptions, switches)
- [ ] Handles missing data gracefully
- [ ] Refresh button works
- [ ] Escape key returns to main dashboard

---

### 1.3 ServiceLogsScreen

**Purpose:** Real-time log streaming for a specific service.

```python
class ServiceLogsScreen(DrillDownScreen):
    """Real-time service logs viewer"""

    CSS = """
    ServiceLogsScreen {
        layout: vertical;
    }

    #logs-container {
        height: 100%;
        overflow-y: scroll;
        background: $panel;
        padding: 1;
    }

    .log-line {
        width: 100%;
    }

    .log-error { color: $error; }
    .log-warn { color: $warning; }
    .log-info { color: $text; }
    .log-debug { color: $text-muted; }
    """

    BINDINGS = [
        ("escape", "pop_screen", "Back"),
        ("s", "toggle_scroll", "Auto-scroll"),
        ("c", "clear_logs", "Clear"),
        ("slash", "search_logs", "Search"),
    ]

    def __init__(self, service_name: str):
        super().__init__(title=f"Logs: {service_name}")
        self.service_name = service_name
        self.log_buffer = []
        self.auto_scroll = True
        self.max_lines = 1000

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch initial logs"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://localhost:8000/services/{self.service_name}/logs",
                params={"lines": 100},
                timeout=5.0
            )
            resp.raise_for_status()
            return resp.json()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Static(
                f"Service: {self.service_name} | "
                f"Auto-scroll: {'ON' if self.auto_scroll else 'OFF'} | "
                f"Lines: {len(self.log_buffer)}/{self.max_lines}",
                id="log-header"
            ),
            Container(id="logs-container"),
            id="logs-layout"
        )
        yield Footer()

    def render_content(self):
        """Render initial logs"""
        logs = self.data.get("logs", [])
        for log in logs:
            self.add_log_line(log)

        # Start real-time streaming
        asyncio.create_task(self.stream_logs())

    async def stream_logs(self):
        """Stream logs in real-time"""
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "GET",
                    f"http://localhost:8000/services/{self.service_name}/logs/stream",
                    timeout=None
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            self.add_log_line({"message": line, "level": "info"})
        except Exception as e:
            self.add_log_line({
                "message": f"Stream error: {str(e)}",
                "level": "error"
            })

    def add_log_line(self, log: Dict[str, str]):
        """Add log line to UI"""
        # Add to buffer
        self.log_buffer.append(log)

        # Trim old lines
        if len(self.log_buffer) > self.max_lines:
            self.log_buffer.pop(0)
            # Remove from UI
            container = self.query_one("#logs-container")
            if container.children:
                container.children[0].remove()

        # Colorize based on level
        level = log.get("level", "info").lower()
        message = log.get("message", "")
        timestamp = log.get("timestamp", "")

        log_class = f"log-{level}"
        formatted = f"[dim]{timestamp}[/dim] {message}"

        # Add to UI
        container = self.query_one("#logs-container")
        container.mount(Static(formatted, classes=["log-line", log_class]))

        # Auto-scroll to bottom
        if self.auto_scroll:
            container.scroll_end(animate=False)

        # Update header
        self.update_header()

    def update_header(self):
        """Update log header"""
        self.query_one("#log-header").update(
            f"Service: {self.service_name} | "
            f"Auto-scroll: {'ON' if self.auto_scroll else 'OFF'} | "
            f"Lines: {len(self.log_buffer)}/{self.max_lines}"
        )

    def action_toggle_scroll(self):
        """Toggle auto-scroll"""
        self.auto_scroll = not self.auto_scroll
        self.update_header()

    def action_clear_logs(self):
        """Clear log buffer and UI"""
        self.log_buffer = []
        container = self.query_one("#logs-container")
        container.remove_children()
        self.update_header()

    def action_search_logs(self):
        """Open search modal"""
        # TODO: Implement search modal
        self.notify("Search not yet implemented")
```

**Acceptance Criteria:**
- [ ] Shows last 100 logs on open
- [ ] Streams new logs in real-time
- [ ] Color-codes by log level (error/warn/info/debug)
- [ ] Auto-scrolls to bottom (toggle with 's')
- [ ] Clears logs with 'c'
- [ ] Limits to 1000 lines (trims oldest)
- [ ] Shows service name and line count in header

---

### 1.4 PatternAnalysisScreen

**Purpose:** 7-day trend analysis with correlations and insights.

```python
import numpy as np
from sparkline_generator import SparklineGenerator

class PatternAnalysisScreen(DrillDownScreen):
    """7-day pattern analysis with correlations"""

    def __init__(self):
        super().__init__(title="Pattern Analysis")
        self.sparkline_gen = SparklineGenerator()

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch 7 days of metrics"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "http://localhost:8000/analytics/patterns",
                params={"days": 7},
                timeout=10.0
            )
            resp.raise_for_status()
            return resp.json()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(id="sparklines"),
            Static(id="correlations"),
            Static(id="insights"),
            id="pattern-container"
        )
        yield Footer()

    def render_content(self):
        """Render patterns and insights"""
        # Sparklines for multiple metrics
        sparklines = self.render_sparklines()
        self.query_one("#sparklines").update(sparklines)

        # Correlation matrix
        correlations = self.render_correlations()
        self.query_one("#correlations").update(correlations)

        # AI-generated insights
        insights = self.render_insights()
        self.query_one("#insights").update(insights)

    def render_sparklines(self) -> Panel:
        """Render sparklines for all metrics"""
        metrics = self.data.get("metrics", {})

        lines = []
        for metric_name, values in metrics.items():
            sparkline = self.sparkline_gen.generate(
                [(i, v) for i, v in enumerate(values)],
                width=60
            )
            colored = self.sparkline_gen.colorize(
                sparkline,
                [(i, v) for i, v in enumerate(values)],
                metric_type=metric_name
            )
            lines.append(f"[cyan]{metric_name:20}[/cyan] {colored}")

        return Panel(
            "\n".join(lines),
            title="📊 7-Day Trends",
            border_style="cyan"
        )

    def render_correlations(self) -> Panel:
        """Render correlation matrix"""
        metrics = list(self.data.get("metrics", {}).keys())
        matrix = self.calculate_correlation_matrix()

        # Create table
        table = Table(title="Correlation Matrix")
        table.add_column("Metric", style="cyan")
        for metric in metrics:
            table.add_column(metric[:10], justify="right")

        for i, metric_a in enumerate(metrics):
            row = [metric_a[:20]]
            for j, metric_b in enumerate(metrics):
                corr = matrix[i][j]
                # Color-code correlation strength
                if corr > 0.7:
                    color = "green"
                elif corr < -0.7:
                    color = "red"
                else:
                    color = "yellow"
                row.append(f"[{color}]{corr:.2f}[/{color}]")
            table.add_row(*row)

        return Panel(table, border_style="magenta")

    def calculate_correlation_matrix(self) -> np.ndarray:
        """Calculate Pearson correlation"""
        metrics = self.data.get("metrics", {})
        metric_names = list(metrics.keys())
        n = len(metric_names)
        matrix = np.zeros((n, n))

        for i, metric_a in enumerate(metric_names):
            for j, metric_b in enumerate(metric_names):
                if i == j:
                    matrix[i][j] = 1.0
                else:
                    values_a = np.array(metrics[metric_a])
                    values_b = np.array(metrics[metric_b])
                    matrix[i][j] = np.corrcoef(values_a, values_b)[0, 1]

        return matrix

    def render_insights(self) -> Panel:
        """Render AI-generated insights"""
        insights = self.generate_insights()

        lines = []
        for insight in insights:
            icon = insight["icon"]
            text = insight["text"]
            lines.append(f"{icon} {text}")

        return Panel(
            "\n\n".join(lines) or "No significant patterns detected",
            title="💡 Insights",
            border_style="yellow"
        )

    def generate_insights(self) -> List[Dict[str, str]]:
        """Generate insights from patterns"""
        insights = []
        metrics = self.data.get("metrics", {})
        matrix = self.calculate_correlation_matrix()
        metric_names = list(metrics.keys())

        # High correlation detection
        for i, metric_a in enumerate(metric_names):
            for j, metric_b in enumerate(metric_names):
                if i < j and matrix[i][j] > 0.7:
                    insights.append({
                        "icon": "⚠️",
                        "text": f"High correlation between {metric_a} and {metric_b} ({matrix[i][j]:.2f}). "
                                f"Consider addressing {metric_a} to improve {metric_b}."
                    })

        # Declining trend detection
        for metric, values in metrics.items():
            if self.is_declining_trend(values):
                insights.append({
                    "icon": "📉",
                    "text": f"{metric} has been declining over 7 days. "
                            f"Review recent changes and energy patterns."
                })

        # Rising trend detection
        for metric, values in metrics.items():
            if self.is_rising_trend(values):
                insights.append({
                    "icon": "📈",
                    "text": f"{metric} has been improving! "
                            f"Continue current strategies."
                })

        return insights

    def is_declining_trend(self, values: List[float]) -> bool:
        """Detect declining trend using linear regression"""
        if len(values) < 3:
            return False

        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return slope < -0.1  # Negative slope

    def is_rising_trend(self, values: List[float]) -> bool:
        """Detect rising trend"""
        if len(values) < 3:
            return False

        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return slope > 0.1  # Positive slope
```

**Acceptance Criteria:**
- [ ] Shows sparklines for 5+ metrics (7-day trends)
- [ ] Shows correlation matrix (Pearson coefficients)
- [ ] Color-codes correlations (green=high, red=negative, yellow=weak)
- [ ] Generates 3+ AI insights automatically
- [ ] Detects declining trends and suggests actions
- [ ] Detects rising trends and confirms strategies
- [ ] Handles missing data gracefully

---

### 1.5 TimelineScreen

**Purpose:** Visual timeline of session events and state changes.

```python
class TimelineScreen(DrillDownScreen):
    """Session event timeline"""

    def __init__(self, session_id: Optional[str] = None):
        super().__init__(title="Session Timeline")
        self.session_id = session_id or "current"

    async def fetch_data(self) -> Dict[str, Any]:
        """Fetch session timeline"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://localhost:8000/sessions/{self.session_id}/timeline",
                timeout=5.0
            )
            resp.raise_for_status()
            return resp.json()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static(id="timeline-header"),
            DataTable(id="timeline-events"),
            id="timeline-container"
        )
        yield Footer()

    def render_content(self):
        """Render timeline"""
        # Header with session info
        session = self.data.get("session", {})
        header = Panel(
            f"[cyan]Session ID:[/cyan] {session.get('id', 'N/A')}\n"
            f"[cyan]Started:[/cyan] {session.get('started_at', 'N/A')}\n"
            f"[cyan]Duration:[/cyan] {session.get('duration', 'N/A')}min\n"
            f"[cyan]Total Events:[/cyan] {len(self.data.get('events', []))}",
            title="📅 Session Info",
            border_style="cyan"
        )
        self.query_one("#timeline-header").update(header)

        # Timeline table
        table = self.query_one("#timeline-events")
        table.add_columns("Time", "Event", "Details", "State")

        events = self.data.get("events", [])
        for event in events:
            # Color-code event type
            event_type = event.get("type", "")
            if event_type == "state_change":
                icon = "🔄"
            elif event_type == "task_completed":
                icon = "✅"
            elif event_type == "interruption":
                icon = "⚠️"
            elif event_type == "break":
                icon = "☕"
            else:
                icon = "•"

            table.add_row(
                event.get("timestamp", ""),
                f"{icon} {event_type}",
                event.get("details", ""),
                event.get("state", "")
            )
```

**Acceptance Criteria:**
- [ ] Shows session info (ID, start time, duration, event count)
- [ ] Shows all events in chronological order
- [ ] Color-codes events by type (state change, task, interruption, break)
- [ ] Shows event details and state changes
- [ ] Sortable by timestamp
- [ ] Handles long sessions (>100 events) with pagination

---

## 📋 TASK 2: CONTEXT MENU SYSTEM (2-3 hours)

### 2.1 ContextMenu Base Class

```python
from textual.widgets import ListView, ListItem, Label

class ContextMenu(Screen):
    """Popup context menu"""

    CSS = """
    ContextMenu {
        align: center middle;
    }

    #menu-container {
        width: 40;
        height: auto;
        max-height: 20;
        background: $panel;
        border: thick $accent;
        padding: 0;
    }

    ContextMenu ListView {
        width: 100%;
        height: auto;
    }

    ContextMenu ListItem {
        padding: 0 1;
    }

    ContextMenu ListItem:hover {
        background: $accent;
    }
    """

    BINDINGS = [
        ("escape", "close_menu", "Close"),
        ("enter", "activate_item", "Select"),
    ]

    def __init__(self, items: List['MenuItem'], position: Optional[Tuple[int, int]] = None):
        super().__init__()
        self.items = items
        self.position = position

    def compose(self) -> ComposeResult:
        list_view = ListView(
            *[ListItem(Label(item.render())) for item in self.items],
            id="menu-list"
        )
        yield Container(list_view, id="menu-container")

    async def on_list_view_selected(self, event: ListView.Selected):
        """Handle item selection"""
        index = event.list_view.index
        if index is not None and index < len(self.items):
            await self.items[index].callback()
        await self.app.pop_screen()

    def action_close_menu(self):
        """Close menu"""
        self.app.pop_screen()

    async def action_activate_item(self):
        """Activate selected item"""
        list_view = self.query_one("#menu-list", ListView)
        index = list_view.index
        if index is not None:
            await self.items[index].callback()
        await self.app.pop_screen()


class MenuItem:
    """Context menu item"""

    def __init__(self, label: str, callback: Callable,
                 shortcut: Optional[str] = None, icon: str = "•"):
        self.label = label
        self.callback = callback
        self.shortcut = shortcut
        self.icon = icon

    def render(self) -> str:
        """Render menu item"""
        shortcut_text = f" ({self.shortcut})" if self.shortcut else ""
        return f"{self.icon} {self.label}{shortcut_text}"
```

---

### 2.2 Add Context Menus to Panels

```python
class DopemuxDashboard(App):
    """Add context menu support to dashboard"""

    BINDINGS = [
        # ... existing bindings ...
        ("colon", "show_context_menu", "Menu"),
    ]

    async def action_show_context_menu(self):
        """Show context menu for focused panel"""
        focused = self.focused

        if focused == self.query_one("#adhd-state", ADHDStateWidget):
            items = self.get_adhd_context_menu()
        elif focused == self.query_one("#productivity", ProductivityWidget):
            items = self.get_productivity_context_menu()
        elif focused == self.query_one("#services", ServicesWidget):
            items = self.get_services_context_menu()
        else:
            items = self.get_global_context_menu()

        menu = ContextMenu(items)
        await self.push_screen(menu)

    def get_adhd_context_menu(self) -> List[MenuItem]:
        """Context menu for ADHD panel"""
        return [
            MenuItem("View Details", self.action_view_adhd_details, "d", "📊"),
            MenuItem("Refresh Data", self.action_refresh, "r", "🔄"),
            MenuItem("Export to JSON", self.action_export_adhd_json, "", "💾"),
            MenuItem("Toggle Notifications", self.action_toggle_notifications, "n", "🔔"),
        ]

    def get_productivity_context_menu(self) -> List[MenuItem]:
        """Context menu for productivity panel"""
        return [
            MenuItem("View Task Details", self.action_view_task_details, "t", "📋"),
            MenuItem("View Timeline", self.action_view_timeline, "", "📅"),
            MenuItem("Refresh Data", self.action_refresh, "r", "🔄"),
            MenuItem("Export to CSV", self.action_export_productivity_csv, "", "💾"),
        ]

    def get_services_context_menu(self) -> List[MenuItem]:
        """Context menu for services panel"""
        return [
            MenuItem("View Logs", self.action_view_service_logs, "l", "📜"),
            MenuItem("Restart Service", self.action_restart_service, "", "🔄"),
            MenuItem("View Metrics", self.action_view_service_metrics, "", "📊"),
            MenuItem("Refresh Status", self.action_refresh, "r", "🔄"),
        ]

    def get_global_context_menu(self) -> List[MenuItem]:
        """Global context menu"""
        return [
            MenuItem("Search", self.action_search, "/", "🔍"),
            MenuItem("Settings", self.action_settings, "", "⚙️"),
            MenuItem("Help", self.action_help, "?", "❓"),
            MenuItem("Quit", self.action_quit, "q", "🚪"),
        ]

    async def action_view_adhd_details(self):
        """Open ADHD state detail screen"""
        screen = StateDetailScreen()
        await self.push_screen(screen)

    async def action_view_task_details(self):
        """Open task detail screen"""
        # Get selected task (implement task selection first)
        task_id = "current"  # TODO: Get from selection
        screen = TaskDetailScreen(task_id)
        await self.push_screen(screen)

    async def action_view_service_logs(self):
        """Open service logs screen"""
        # Get selected service
        service = "adhd-engine"  # TODO: Get from selection
        screen = ServiceLogsScreen(service)
        await self.push_screen(screen)

    async def action_view_timeline(self):
        """Open timeline screen"""
        screen = TimelineScreen()
        await self.push_screen(screen)
```

**Acceptance Criteria:**
- [ ] Context menu appears on `:` key
- [ ] Different menus for different panels
- [ ] Keyboard navigation (up/down/enter/esc)
- [ ] Mouse click support
- [ ] Icons and shortcuts shown
- [ ] All actions functional

---

## 📋 TASK 3: SEARCH SYSTEM (2-3 hours)

### 3.1 SearchManager

```python
from collections import defaultdict
import re

class SearchManager:
    """Full-text search across dashboard data"""

    def __init__(self):
        self.index = defaultdict(set)  # {keyword: {item_ids}}
        self.items = {}  # {item_id: data}

    def index_item(self, item_id: str, data: Dict[str, Any],
                   searchable_fields: List[str]):
        """Add item to search index"""
        self.items[item_id] = data

        # Extract and tokenize searchable text
        text_parts = []
        for field in searchable_fields:
            value = data.get(field, "")
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, (list, tuple)):
                text_parts.extend(str(v) for v in value)

        text = " ".join(text_parts).lower()
        keywords = self._tokenize(text)

        # Add to index
        for keyword in keywords:
            self.index[keyword].add(item_id)

    def search(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search and return ranked results"""
        if not query or len(query) < 2:
            return []

        keywords = self._tokenize(query.lower())
        if not keywords:
            return []

        # Find matching items
        matching_items = set()
        for keyword in keywords:
            # Exact match
            if keyword in self.index:
                matching_items.update(self.index[keyword])

            # Partial match (prefix)
            for indexed_keyword in self.index:
                if indexed_keyword.startswith(keyword):
                    matching_items.update(self.index[indexed_keyword])

        # Rank by relevance
        ranked = sorted(
            matching_items,
            key=lambda item_id: self._calculate_score(item_id, keywords),
            reverse=True
        )

        # Return top results
        return [self.items[item_id] for item_id in ranked[:max_results]]

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into searchable keywords"""
        # Split on whitespace and punctuation
        tokens = re.findall(r'\w+', text.lower())
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to'}
        return [t for t in tokens if t not in stop_words and len(t) > 1]

    def _calculate_score(self, item_id: str, keywords: List[str]) -> float:
        """Calculate relevance score for ranking"""
        data = self.items[item_id]
        text = str(data).lower()

        score = 0.0
        for keyword in keywords:
            # Exact word matches (higher weight)
            score += text.count(f" {keyword} ") * 2.0
            # Partial matches
            score += text.count(keyword) * 1.0

        return score

    def clear(self):
        """Clear all indexed data"""
        self.index.clear()
        self.items.clear()
```

---

### 3.2 SearchScreen

```python
class SearchScreen(Screen):
    """Full-screen search interface"""

    CSS = """
    SearchScreen {
        layout: vertical;
    }

    #search-input {
        dock: top;
        height: 3;
        margin: 1 2;
    }

    #search-results {
        height: 100%;
        margin: 0 2 1 2;
    }

    .no-results {
        content-align: center middle;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("escape", "close_search", "Close"),
    ]

    def __init__(self, search_manager: SearchManager):
        super().__init__()
        self.search_manager = search_manager
        self.results = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(
            placeholder="Search tasks, services, patterns, logs...",
            id="search-input"
        )
        yield DataTable(id="search-results")
        yield Footer()

    async def on_mount(self):
        """Focus search input on mount"""
        self.query_one("#search-input", Input).focus()

        # Setup results table
        table = self.query_one("#search-results", DataTable)
        table.add_columns("Type", "Title", "Details", "Score")

    async def on_input_changed(self, event: Input.Changed):
        """Live search as user types"""
        query = event.value

        if len(query) < 2:
            self.clear_results()
            return

        # Debounce search (wait 300ms)
        await asyncio.sleep(0.3)

        # Check if query changed while waiting
        if self.query_one("#search-input", Input).value != query:
            return

        # Perform search
        self.results = self.search_manager.search(query)
        self.render_results()

    def render_results(self):
        """Render search results"""
        table = self.query_one("#search-results", DataTable)
        table.clear()

        if not self.results:
            table.update("[dim]No results found[/dim]")
            return

        for result in self.results[:50]:  # Limit to 50 results
            table.add_row(
                result.get("type", "unknown"),
                result.get("title", ""),
                result.get("details", "")[:50],  # Truncate
                f"{result.get('score', 0):.1f}"
            )

    def clear_results(self):
        """Clear results table"""
        table = self.query_one("#search-results", DataTable)
        table.clear()

    async def on_data_table_row_selected(self, event: DataTable.RowSelected):
        """Open drill-down for selected result"""
        if event.row_index >= len(self.results):
            return

        result = self.results[event.row_index]
        screen = self.create_drill_down(result)

        if screen:
            await self.app.push_screen(screen)

    def create_drill_down(self, result: Dict) -> Optional[DrillDownScreen]:
        """Create appropriate drill-down screen"""
        result_type = result.get("type")

        if result_type == "task":
            return TaskDetailScreen(result.get("id"))
        elif result_type == "service":
            return ServiceLogsScreen(result.get("name"))
        elif result_type == "pattern":
            return PatternAnalysisScreen()
        else:
            return None

    def action_close_search(self):
        """Close search screen"""
        self.app.pop_screen()
```

---

### 3.3 Integrate Search with Dashboard

```python
class DopemuxDashboard(App):
    """Add search to dashboard"""

    def __init__(self):
        super().__init__()
        self.search_manager = SearchManager()

    BINDINGS = [
        # ... existing bindings ...
        ("slash", "search", "Search"),
        ("ctrl+f", "search", "Search"),
    ]

    async def on_mount(self):
        """Initialize and index data for search"""
        await super().on_mount()

        # Index initial data
        await self.index_all_data()

        # Re-index every 60 seconds
        self.set_interval(60, self.index_all_data)

    async def index_all_data(self):
        """Index all searchable data"""
        # Index tasks
        tasks = await self.fetch_tasks()
        for task in tasks:
            self.search_manager.index_item(
                f"task_{task['id']}",
                {"type": "task", **task},
                ["title", "description", "status"]
            )

        # Index services
        services = await self.fetch_services()
        for service in services:
            self.search_manager.index_item(
                f"service_{service['name']}",
                {"type": "service", **service},
                ["name", "status", "description"]
            )

        # Index patterns (if available)
        patterns = await self.fetch_patterns()
        for pattern in patterns:
            self.search_manager.index_item(
                f"pattern_{pattern['id']}",
                {"type": "pattern", **pattern},
                ["name", "description"]
            )

    async def action_search(self):
        """Open search screen"""
        screen = SearchScreen(self.search_manager)
        await self.push_screen(screen)
```

**Acceptance Criteria:**
- [ ] Search opens with `/` or `Ctrl+F`
- [ ] Live search updates as user types (debounced 300ms)
- [ ] Searches across tasks, services, patterns, logs
- [ ] Results ranked by relevance
- [ ] Click result to open drill-down
- [ ] Handles 1000+ indexed items efficiently
- [ ] Case-insensitive search
- [ ] Partial word matching

---

## 📋 TASK 4: PRODUCTION HARDENING (2-3 hours)

### 4.1 Error Boundaries

```python
class ErrorBoundary(Container):
    """Error boundary wrapper for widgets"""

    def __init__(self, widget: Widget, fallback_text: str = "Error loading widget"):
        super().__init__()
        self.widget = widget
        self.fallback_text = fallback_text
        self.has_error = False

    async def on_mount(self):
        """Mount widget with error handling"""
        try:
            await self.mount(self.widget)
        except Exception as e:
            self.has_error = True
            self.handle_error(e)

    def handle_error(self, error: Exception):
        """Display error fallback"""
        logger.exception(f"Widget error: {error}")

        # TODO: Send to Sentry
        # sentry_sdk.capture_exception(error)

        # Display fallback
        error_widget = Static(
            Panel(
                f"[red]{self.fallback_text}[/red]\n\n"
                f"{str(error)}\n\n"
                f"Press [cyan]r[/cyan] to retry",
                title="⚠️  Error",
                border_style="red"
            )
        )
        self.mount(error_widget)

# Usage in dashboard
class DopemuxDashboard(App):
    def compose(self) -> ComposeResult:
        yield Header()

        # Wrap widgets in error boundaries
        yield ErrorBoundary(
            ADHDStateWidget(id="adhd-state"),
            "Error loading ADHD state"
        )
        yield ErrorBoundary(
            ProductivityWidget(id="productivity"),
            "Error loading productivity"
        )
        yield ErrorBoundary(
            ServicesWidget(id="services"),
            "Error loading services"
        )
        yield ErrorBoundary(
            TrendsWidget(id="trends"),
            "Error loading trends"
        )

        yield Footer()
```

---

### 4.2 Crash Recovery

```python
import json
from pathlib import Path
from datetime import datetime

class StateManager:
    """Persist dashboard state for crash recovery"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        """Load state from disk"""
        if not self.state_file.exists():
            return self.default_state()

        try:
            return json.loads(self.state_file.read_text())
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
            return self.default_state()

    def default_state(self) -> Dict[str, Any]:
        """Default state"""
        return {
            "version": "1.0",
            "last_saved": None,
            "crashed": False,
            "panels": {},
            "settings": {},
        }

    async def save_state(self, state: Dict[str, Any]):
        """Save state to disk (async)"""
        state["last_saved"] = datetime.now().isoformat()
        state["crashed"] = False

        # Save asynchronously to avoid blocking UI
        data = json.dumps(state, indent=2)
        await asyncio.to_thread(self.state_file.write_text, data)

    def mark_crashed(self):
        """Mark state as crashed (for next startup)"""
        self.state["crashed"] = True
        try:
            self.state_file.write_text(json.dumps(self.state, indent=2))
        except:
            pass

# Usage in dashboard
class DopemuxDashboard(App):
    async def on_mount(self):
        # Initialize state manager
        state_file = Path.home() / ".dopemux" / "dashboard_state.json"
        state_file.parent.mkdir(exist_ok=True)

        self.state_manager = StateManager(state_file)

        # Check for previous crash
        if self.state_manager.state.get("crashed"):
            self.notify(
                "Dashboard recovered from previous crash",
                severity="warning",
                timeout=5
            )

            # Optionally restore previous state
            # await self.restore_state()

        # Auto-save every 30 seconds
        self.set_interval(30, self.auto_save)

    async def auto_save(self):
        """Periodic state save"""
        state = {
            "panels": self.get_panel_states(),
            "settings": self.get_settings(),
        }
        await self.state_manager.save_state(state)

    def get_panel_states(self) -> Dict[str, Any]:
        """Get current state of all panels"""
        return {
            "adhd": self.query_one("#adhd-state").get_state(),
            "productivity": self.query_one("#productivity").get_state(),
            "services": self.query_one("#services").get_state(),
            "trends": self.query_one("#trends").get_state(),
        }

    def get_settings(self) -> Dict[str, Any]:
        """Get current settings"""
        return {
            "theme": self.current_theme,
            "notifications_enabled": self.notifications_enabled,
            "auto_refresh": self.auto_refresh_enabled,
        }

    async def on_unmount(self):
        """Save state on clean shutdown"""
        await self.auto_save()
```

**Acceptance Criteria:**
- [ ] State saved every 30 seconds
- [ ] State restored on startup after crash
- [ ] Warning shown if previous crash detected
- [ ] Panel states preserved (scroll position, selection)
- [ ] Settings preserved (theme, notifications)
- [ ] Handles corrupted state file gracefully

---

## 🧪 TASK 5: TESTING (2 hours)

### 5.1 Integration Tests

```python
# tests/integration/test_day10_drilldowns.py

import pytest
from dopemux_dashboard import (
    TaskDetailScreen,
    ServiceLogsScreen,
    PatternAnalysisScreen,
    TimelineScreen,
)

@pytest.mark.asyncio
async def test_task_detail_screen_loads():
    """Test task detail screen loads data"""
    screen = TaskDetailScreen(task_id="test-task-1")

    # Mock API response
    with patch_api_response({
        "id": "test-task-1",
        "title": "Test Task",
        "status": "completed",
        "history": [{"timestamp": "2025-10-29T10:00:00", "type": "created"}]
    }):
        await screen.on_mount()

    assert screen.data is not None
    assert screen.data["id"] == "test-task-1"
    assert len(screen.data["history"]) > 0

@pytest.mark.asyncio
async def test_service_logs_stream():
    """Test service logs streaming"""
    screen = ServiceLogsScreen(service_name="adhd-engine")

    # Start streaming
    with patch_streaming_logs([
        {"message": "Log line 1", "level": "info"},
        {"message": "Log line 2", "level": "warn"},
    ]):
        await screen.on_mount()
        await asyncio.sleep(0.5)  # Wait for streaming

    assert len(screen.log_buffer) >= 2
    assert screen.log_buffer[0]["message"] == "Log line 1"

@pytest.mark.asyncio
async def test_pattern_analysis_correlations():
    """Test pattern analysis correlation calculation"""
    screen = PatternAnalysisScreen()

    # Mock data
    screen.data = {
        "metrics": {
            "metric_a": [1, 2, 3, 4, 5],
            "metric_b": [2, 4, 6, 8, 10],  # Perfect correlation
        }
    }

    matrix = screen.calculate_correlation_matrix()

    # metric_b is perfectly correlated with metric_a
    assert matrix[0][1] > 0.99  # Near perfect correlation

@pytest.mark.asyncio
async def test_search_indexes_data():
    """Test search manager indexes data"""
    from dopemux_dashboard import SearchManager

    manager = SearchManager()

    # Index some items
    manager.index_item("task-1", {
        "type": "task",
        "title": "Fix bug in dashboard",
        "description": "The sparklines are broken"
    }, ["title", "description"])

    # Search
    results = manager.search("sparklines")

    assert len(results) == 1
    assert results[0]["type"] == "task"

@pytest.mark.asyncio
async def test_context_menu_appears():
    """Test context menu appears on trigger"""
    from dopemux_dashboard import DopemuxDashboard, ContextMenu

    app = DopemuxDashboard()

    async with app.run_test() as pilot:
        # Trigger context menu
        await pilot.press("colon")

        # Check menu appeared
        assert app.screen_stack[-1].__class__ == ContextMenu
```

---

### 5.2 Performance Tests

```python
# tests/performance/test_day10_performance.py

import pytest
import time

@pytest.mark.performance
async def test_drill_down_latency():
    """Test drill-down screens load in <500ms"""
    screen = TaskDetailScreen(task_id="test-task")

    start = time.time()
    await screen.on_mount()
    duration = time.time() - start

    assert duration < 0.5, f"Drill-down took {duration:.2f}s (>500ms)"

@pytest.mark.performance
async def test_search_performance():
    """Test search completes in <100ms for 1000 items"""
    manager = SearchManager()

    # Index 1000 items
    for i in range(1000):
        manager.index_item(f"item-{i}", {
            "type": "task",
            "title": f"Task {i}",
            "description": f"Description {i}"
        }, ["title", "description"])

    # Search
    start = time.time()
    results = manager.search("task")
    duration = time.time() - start

    assert duration < 0.1, f"Search took {duration:.3f}s (>100ms)"
    assert len(results) > 0

@pytest.mark.performance
async def test_log_streaming_performance():
    """Test log streaming handles 100 logs/sec"""
    screen = ServiceLogsScreen(service_name="test")

    # Add 100 logs rapidly
    start = time.time()
    for i in range(100):
        screen.add_log_line({
            "message": f"Log line {i}",
            "level": "info",
            "timestamp": f"2025-10-29T10:00:{i:02d}"
        })
    duration = time.time() - start

    assert duration < 1.0, f"Streaming took {duration:.2f}s (>1s)"
    assert len(screen.log_buffer) == 100
```

---

## ✅ FINAL CHECKLIST

### Before You Start
- [ ] Read Day 10 Zen Research document
- [ ] Check services (Prometheus, ADHD Engine running)
- [ ] Create feature branch: `git checkout -b feature/day10-drilldowns`
- [ ] Open implementation files

### Task 1: Drill-Downs (4-5 hrs)
- [ ] Create `DrillDownScreen` base class
- [ ] Implement `TaskDetailScreen`
- [ ] Implement `ServiceLogsScreen`
- [ ] Implement `PatternAnalysisScreen`
- [ ] Implement `TimelineScreen`
- [ ] Add lazy loading and caching
- [ ] Test all drill-downs with real data

### Task 2: Context Menus (2-3 hrs)
- [ ] Create `ContextMenu` system
- [ ] Add context menus to all panels
- [ ] Test keyboard navigation
- [ ] Test all menu actions

### Task 3: Search (2-3 hrs)
- [ ] Implement `SearchManager`
- [ ] Implement `SearchScreen`
- [ ] Index initial data
- [ ] Test search with 1000+ items
- [ ] Test drill-downs from search results

### Task 4: Hardening (2-3 hrs)
- [ ] Add error boundaries to all widgets
- [ ] Implement crash recovery
- [ ] Add state persistence
- [ ] Test recovery after simulated crash

### Task 5: Testing (2 hrs)
- [ ] Write integration tests (10+)
- [ ] Write performance tests (5+)
- [ ] Run 24-hour stress test
- [ ] Profile performance

### After Implementation
- [ ] All tests passing
- [ ] Performance targets met
- [ ] Documentation updated
- [ ] Demo video recorded
- [ ] Commit and push
- [ ] Ready to merge! 🎉

---

## 🎯 SUCCESS METRICS

- ✅ 5+ drill-down screens functional
- ✅ Context menus on all panels
- ✅ Full-text search working
- ✅ Zero crashes in 24-hour test
- ✅ p99 latency <100ms
- ✅ Search results in <100ms
- ✅ State recovery working

---

**Status:** ✅ READY TO IMPLEMENT
**Next:** Start coding!
**Confidence:** 🔥🔥🔥🔥🔥

---

*Created: 2025-10-29*
*Version: 1.0*
*Estimated Time: 10-12 hours*
