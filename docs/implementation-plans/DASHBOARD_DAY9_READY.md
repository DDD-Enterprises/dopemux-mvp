---
id: DASHBOARD_DAY9_READY
title: Dashboard_Day9_Ready
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Dashboard Day 9 - Implementation Ready! 🚀

**Date:** 2025-10-29
**Status:** ✅ READY TO IMPLEMENT
**Deep Research:** Complete (1,275 lines)
**Estimated Time:** 6-8 hours

---

## 📋 EXECUTIVE SUMMARY

### Current Status
✅ **Day 8 COMPLETE:**
- WebSocket streaming infrastructure (StreamingClient, MetricsManager)
- Reactive widget updates (ADHDStateWidget)
- Connection fallback (WebSocket → HTTP polling)
- Comprehensive testing framework
- Production-ready error handling

✅ **Existing Components:**
- `sparkline_generator.py` - Already implemented! (302 lines)
- `prometheus_client.py` - Prometheus integration exists
- Dashboard base architecture complete
- Multiple widgets (ADHD, Productivity, Services, Trends)

### What We're Building Next (Day 9)
1. **Enhanced Sparklines** - Integrate real Prometheus data → widgets
2. **Keyboard Navigation** - Full dashboard control (no mouse needed)
3. **Testing & Polish** - Integration tests, performance profiling

---

## ✅ WHAT ALREADY EXISTS (No Need to Build!)

### 1. SparklineGenerator ✅
**File:** `sparkline_generator.py` (302 lines)

**Features:**
- ✅ Unicode sparkline rendering (8 block levels)
- ✅ Downsampling (averaging buckets)
- ✅ Upsampling (linear interpolation)
- ✅ ADHD-optimized coloring (cognitive load, velocity, switches)
- ✅ Trend detection (up/down/stable)
- ✅ Stats generation (min/max/avg/current)

**Usage:**
```python
from sparkline_generator import SparklineGenerator

gen = SparklineGenerator()
data = [(now(), 10), (now(), 20), (now(), 30)]
sparkline = gen.generate(data, width=20)
# Returns: "▁▁▃▃▅▅▆▆██"

# With color
colored = gen.colorize(sparkline, data, metric_type="cognitive_load")
# Returns: "[green]▁▁▃▃▅▅▆▆██[/green]"
```

### 2. PrometheusClient ✅
**File:** `prometheus_client.py`

**Features:**
- ✅ Query execution (`query()`, `query_range()`)
- ✅ Caching layer
- ✅ Error handling

**Usage:**
```python
from prometheus_client import PrometheusClient

client = PrometheusClient(PrometheusConfig(url="http://localhost:9090"))
result = await client.query('adhd_cognitive_load')
# Returns: [(timestamp, value), ...]
```

### 3. MetricsManager ✅ (Day 8)
**File:** `dopemux_dashboard.py`

**Features:**
- ✅ WebSocket + HTTP fallback
- ✅ Auto-reconnection
- ✅ Reactive widget updates
- ✅ Connection status tracking

---

## 🎯 WHAT WE NEED TO BUILD (Day 9)

### Task 1: PrometheusSparklineIntegration (2-3 hours)

**Goal:** Wire Prometheus → SparklineGenerator → TrendsWidget

**New Class:**
```python
class PrometheusSparklineIntegration:
    """
    Bridges Prometheus metrics to sparkline visualization.

    Responsibilities:
    - Fetch time-series data from Prometheus
    - Transform to sparkline-compatible format
    - Cache results (30s TTL)
    - Handle errors gracefully
    """

    def __init__(self, prometheus_client: PrometheusClient):
        self.prom = prometheus_client
        self.sparkline_gen = SparklineGenerator()
        self.cache: Dict[str, Tuple[float, str]] = {}
        self.ttl = 30  # seconds

    async def get_sparkline(
        self,
        metric: str,
        hours: int = 24,
        width: int = 20,
        metric_type: str = "auto"
    ) -> str:
        """
        Get colored sparkline for metric.

        Examples:
        >>> integration = PrometheusSparklineIntegration(prom_client)
        >>> sparkline = await integration.get_sparkline(
        ...     "adhd_cognitive_load", hours=2, metric_type="cognitive_load"
        ... )
        >>> print(sparkline)
        "[green]▁▃▄▆▇▆▅▄▃▂[/green] ▼ -8%"
        """
        # Check cache
        cache_key = f"{metric}:{hours}:{width}:{metric_type}"
        if cache_key in self.cache:
            timestamp, cached_sparkline = self.cache[cache_key]
            if time.time() - timestamp < self.ttl:
                return cached_sparkline  # Cache hit!

        try:
            # Fetch from Prometheus
            end = datetime.now()
            start = end - timedelta(hours=hours)

            data = await self.prom.query_range(
                metric,
                start=start.isoformat(),
                end=end.isoformat(),
                step="5m"  # 5-minute resolution
            )

            if not data:
                return "─" * width  # No data

            # Generate sparkline
            sparkline = self.sparkline_gen.generate(data, width=width)

            # Add color
            colored = self.sparkline_gen.colorize(sparkline, data, metric_type)

            # Add trend indicator
            stats = self.sparkline_gen.generate_with_stats(data, width)
            trend_arrow = {"up": "▲", "down": "▼", "stable": "─", "unknown": "?"}[stats['trend']]

            # Calculate percentage change
            if len(data) >= 2:
                values = [v for _, v in data]
                change = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
                percentage = f"{change:+.0f}%"
            else:
                percentage = "N/A"

            result = f"{colored} {trend_arrow} {percentage}"

            # Cache result
            self.cache[cache_key] = (time.time(), result)

            return result

        except Exception as e:
            logger.warning(f"Sparkline generation failed for {metric}: {e}")
            return f"[dim]{'─' * width} ✖[/dim]"  # Error indicator
```

**Integration into TrendsWidget:**
```python
class TrendsWidget(Static):
    """Trends panel with real Prometheus sparklines"""

    def __init__(self, prom_integration: PrometheusSparklineIntegration, **kwargs):
        super().__init__(**kwargs)
        self.prom_sparklines = prom_integration
        self.sparklines: Dict[str, str] = {}

    async def on_mount(self):
        """Start sparkline updates"""
        self.set_interval(30, self.update_sparklines)  # Refresh every 30s
        await self.update_sparklines()  # Initial load

    async def update_sparklines(self):
        """Fetch all sparklines from Prometheus"""
        try:
            # Cognitive load (2 hours)
            self.sparklines["cognitive_load"] = await self.prom_sparklines.get_sparkline(
                "adhd_cognitive_load",
                hours=2,
                width=20,
                metric_type="cognitive_load"
            )

            # Task velocity (7 days = 168 hours)
            self.sparklines["velocity"] = await self.prom_sparklines.get_sparkline(
                "adhd_task_velocity_per_day",
                hours=168,
                width=20,
                metric_type="velocity"
            )

            # Context switches (24 hours)
            self.sparklines["context_switches"] = await self.prom_sparklines.get_sparkline(
                "adhd_context_switches_total",
                hours=24,
                width=20,
                metric_type="switches"
            )

            # Energy level (24 hours)
            self.sparklines["energy"] = await self.prom_sparklines.get_sparkline(
                "adhd_energy_level",
                hours=24,
                width=20,
                metric_type="auto"
            )

            self.refresh()  # Trigger re-render

        except Exception as e:
            logger.error(f"Sparkline update failed: {e}")

    def render(self) -> RenderableType:
        """Render trends with sparklines"""
        table = Table.grid(padding=(0, 2))
        table.add_column(justify="left", style="bold dim")
        table.add_column(justify="right")

        table.add_row(
            "Cognitive Load (2h)",
            self.sparklines.get("cognitive_load", "─" * 20)
        )
        table.add_row(
            "Task Velocity (7d)",
            self.sparklines.get("velocity", "─" * 20)
        )
        table.add_row(
            "Context Switches (24h)",
            self.sparklines.get("context_switches", "─" * 20)
        )
        table.add_row(
            "Energy Level (24h)",
            self.sparklines.get("energy", "─" * 20)
        )

        return Panel(table, title="📈 Trends", border_style="blue")
```

**Acceptance Criteria:**
- [ ] Sparklines show real Prometheus data
- [ ] Auto-refresh every 30 seconds
- [ ] Color-coded by metric type
- [ ] Trend arrows (▲▼─)
- [ ] Percentage change displayed
- [ ] Cache working (30s TTL)
- [ ] Errors handled gracefully

---

### Task 2: Keyboard Navigation & Focus Management (3-4 hours)

**Goal:** Full keyboard control without mouse

**New Class:**
```python
class FocusManager:
    """
    Manages panel focus state and keyboard navigation.

    ADHD Principles:
    - Always clear which panel is focused (high contrast border)
    - Smooth transitions (no jarring jumps)
    - Escape always works (safety net)
    - Visual + optional auditory feedback
    """

    def __init__(self, app: "DopemuxDashboard"):
        self.app = app
        self.focused_panel_id: Optional[str] = "adhd"  # Default focus
        self.panel_order = ["adhd", "productivity", "services", "trends"]
        self.focus_history: List[str] = []

    def focus_panel(self, panel_id: str):
        """
        Focus specific panel with visual feedback.

        Visual Changes:
        1. Previous panel → remove "focused" class
        2. New panel → add "focused" class (triggers CSS)
        3. Scroll into view if needed
        4. Optional sound (macOS only)
        """
        # Unfocus previous
        if self.focused_panel_id:
            prev_panel = self.app.query_one(f"#{self.focused_panel_id}")
            prev_panel.remove_class("focused")

        # Store history
        if self.focused_panel_id != panel_id:
            self.focus_history.append(self.focused_panel_id)

        # Focus new
        self.focused_panel_id = panel_id
        new_panel = self.app.query_one(f"#{panel_id}")
        new_panel.add_class("focused")
        new_panel.scroll_visible()

        # Optional: Auditory feedback (subtle tink sound)
        # self._play_focus_sound()

    def next_panel(self):
        """Tab: cycle to next panel"""
        current_idx = self.panel_order.index(self.focused_panel_id)
        next_idx = (current_idx + 1) % len(self.panel_order)
        self.focus_panel(self.panel_order[next_idx])

    def prev_panel(self):
        """Shift+Tab: cycle to previous panel"""
        current_idx = self.panel_order.index(self.focused_panel_id)
        prev_idx = (current_idx - 1) % len(self.panel_order)
        self.focus_panel(self.panel_order[prev_idx])

    def go_back(self):
        """Backspace: return to previous focus"""
        if self.focus_history:
            prev_panel = self.focus_history.pop()
            self.focus_panel(prev_panel)
```

**Integration into DopemuxDashboard:**
```python
class DopemuxDashboard(App):
    """Enhanced with keyboard navigation"""

    CSS = """
    /* Focus indicators */
    .panel {
        border: solid gray;
        transition: border 150ms ease-in-out;
    }

    .panel.focused {
        border: thick $accent;  /* Blue in Mocha theme */
        box-shadow: 0 0 8px $accent;
    }

    .panel:hover {
        border: solid white;
    }
    """

    BINDINGS = [
        # Panel Navigation
        ("1", "focus_panel('adhd')", "ADHD State"),
        ("2", "focus_panel('productivity')", "Productivity"),
        ("3", "focus_panel('services')", "Services"),
        ("4", "focus_panel('trends')", "Trends"),
        ("tab", "next_panel", "Next Panel"),
        ("shift+tab", "prev_panel", "Previous Panel"),

        # Panel Actions
        ("enter", "expand_focused_panel", "Expand/Details"),
        ("space", "refresh_focused_panel", "Refresh"),
        ("escape", "collapse_all", "Close Modals"),

        # Detail Views (context-sensitive)
        ("d", "show_detail", "Details"),
        ("l", "show_logs", "Logs"),
        ("p", "show_patterns", "Patterns"),
        ("h", "show_history", "History"),

        # Quick Actions
        ("f", "toggle_focus_mode", "Focus Mode"),
        ("b", "start_break_timer", "Break Timer"),
        ("t", "cycle_theme", "Cycle Theme"),
        ("n", "toggle_notifications", "Notifications"),

        # Vim-style Navigation
        ("j", "scroll_down", "Scroll Down"),
        ("k", "scroll_up", "Scroll Up"),
        ("g", "scroll_home", "Top"),
        ("G", "scroll_end", "Bottom"),

        # Help & Control
        ("?", "show_help", "Show Help"),
        ("r", "force_refresh", "Refresh All"),
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.focus_manager = FocusManager(self)
        # ... existing code ...

    # Panel Navigation Actions
    def action_focus_panel(self, panel_id: str):
        """Focus specific panel (1-4 keys)"""
        self.focus_manager.focus_panel(panel_id)

    def action_next_panel(self):
        """Focus next panel (Tab)"""
        self.focus_manager.next_panel()

    def action_prev_panel(self):
        """Focus previous panel (Shift+Tab)"""
        self.focus_manager.prev_panel()

    # Panel Actions
    def action_expand_focused_panel(self):
        """Expand currently focused panel (Enter)"""
        panel_id = self.focus_manager.focused_panel_id
        # Show detail modal based on panel type
        if panel_id == "adhd":
            self.action_show_detail()
        elif panel_id == "productivity":
            self.action_show_detail()
        elif panel_id == "services":
            self.action_show_logs()
        elif panel_id == "trends":
            self.action_show_history()

    def action_refresh_focused_panel(self):
        """Refresh currently focused panel (Space)"""
        panel_id = self.focus_manager.focused_panel_id
        panel = self.query_one(f"#{panel_id}")
        if hasattr(panel, 'refresh_data'):
            panel.refresh_data()

    # Help Modal
    def action_show_help(self):
        """Show keyboard shortcuts help (?)"""
        self.push_screen(KeyboardHelpScreen())
```

**Help Modal:**
```python
class KeyboardHelpScreen(Screen):
    """Full-screen help with all keyboard shortcuts"""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self._render_help(), id="help-content"),
            id="help-modal"
        )

    def _render_help(self) -> RenderableType:
        """Render help table"""
        table = Table(title="⌨️  Keyboard Shortcuts", box=box.ROUNDED)
        table.add_column("Key", style="cyan bold")
        table.add_column("Action", style="white")
        table.add_column("Category", style="dim")

        # Panel Navigation
        table.add_row("1-4", "Focus panel (ADHD/Productivity/Services/Trends)", "Navigation")
        table.add_row("Tab", "Next panel", "Navigation")
        table.add_row("Shift+Tab", "Previous panel", "Navigation")

        # Panel Actions
        table.add_row("Enter", "Expand/show details", "Actions")
        table.add_row("Space", "Refresh panel", "Actions")
        table.add_row("Escape", "Close modals", "Actions")

        # Detail Views
        table.add_row("d", "Show details", "Views")
        table.add_row("l", "Show logs", "Views")
        table.add_row("p", "Show patterns", "Views")
        table.add_row("h", "Show history", "Views")

        # Quick Actions
        table.add_row("f", "Toggle focus mode", "Quick")
        table.add_row("b", "Start break timer", "Quick")
        table.add_row("t", "Cycle theme", "Quick")
        table.add_row("n", "Toggle notifications", "Quick")

        # Vim Navigation
        table.add_row("j/k", "Scroll down/up", "Scroll")
        table.add_row("g/G", "Jump to top/bottom", "Scroll")

        # Control
        table.add_row("?", "Show this help", "Help")
        table.add_row("r", "Refresh all panels", "Control")
        table.add_row("q", "Quit dashboard", "Control")

        return Panel(table, border_style="blue")

    def action_dismiss(self):
        """Close help modal"""
        self.app.pop_screen()
```

**Acceptance Criteria:**
- [ ] Number keys (1-4) focus panels
- [ ] Tab/Shift+Tab cycle through panels
- [ ] Visual focus indicators (blue border + shadow)
- [ ] Enter expands focused panel
- [ ] ? shows help modal with all shortcuts
- [ ] Escape closes modals
- [ ] Vim navigation (j/k/g/G) works
- [ ] All shortcuts work without mouse

---

### Task 3: Testing & Polish (1-2 hours)

**Integration Tests:**
```python
# tests/integration/test_day9_features.py

import pytest
from textual.pilot import Pilot
from dopemux_dashboard import DopemuxDashboard

@pytest.mark.asyncio
async def test_sparklines_show_real_data():
    """Verify sparklines display Prometheus data"""
    app = DopemuxDashboard()

    async with app.run_test() as pilot:
        await pilot.pause(2)  # Wait for initial data load

        trends_widget = app.query_one("#trends")
        assert "▁" in trends_widget.sparklines.get("cognitive_load", "")
        assert "▼" in trends_widget.sparklines.get("velocity", "") or \
               "▲" in trends_widget.sparklines.get("velocity", "") or \
               "─" in trends_widget.sparklines.get("velocity", "")

@pytest.mark.asyncio
async def test_keyboard_navigation_full_cycle():
    """Test complete keyboard navigation workflow"""
    app = DopemuxDashboard()

    async with app.run_test() as pilot:
        # Start at ADHD panel (default)
        assert app.focus_manager.focused_panel_id == "adhd"

        # Tab through all panels
        await pilot.press("tab")
        assert app.focus_manager.focused_panel_id == "productivity"

        await pilot.press("tab")
        assert app.focus_manager.focused_panel_id == "services"

        await pilot.press("tab")
        assert app.focus_manager.focused_panel_id == "trends"

        # Tab wraps to first
        await pilot.press("tab")
        assert app.focus_manager.focused_panel_id == "adhd"

        # Shift+Tab goes backward
        await pilot.press("shift+tab")
        assert app.focus_manager.focused_panel_id == "trends"

        # Number keys jump directly
        await pilot.press("1")
        assert app.focus_manager.focused_panel_id == "adhd"

        await pilot.press("3")
        assert app.focus_manager.focused_panel_id == "services"

@pytest.mark.asyncio
async def test_help_modal_shows_and_closes():
    """Test help modal (? key)"""
    app = DopemuxDashboard()

    async with app.run_test() as pilot:
        # Press ? to open help
        await pilot.press("?")
        assert len(app.screen_stack) == 2  # Main + Help

        # Press Escape to close
        await pilot.press("escape")
        assert len(app.screen_stack) == 1  # Main only

@pytest.mark.asyncio
async def test_sparkline_cache_working():
    """Verify sparkline caching reduces Prometheus calls"""
    app = DopemuxDashboard()

    async with app.run_test() as pilot:
        trends = app.query_one("#trends")
        integration = trends.prom_sparklines

        # First call - cache miss
        sparkline1 = await integration.get_sparkline("test_metric", hours=24)
        call_count_1 = len(integration.prom.call_log)  # Mock tracking

        # Second call - cache hit (within 30s)
        sparkline2 = await integration.get_sparkline("test_metric", hours=24)
        call_count_2 = len(integration.prom.call_log)

        # Should be same sparkline, no new Prometheus call
        assert sparkline1 == sparkline2
        assert call_count_1 == call_count_2  # No new call
```

**Performance Test:**
```python
# tests/performance/test_day9_performance.py

import pytest
import time

@pytest.mark.performance
async def test_sparkline_generation_latency():
    """Sparkline generation < 50ms"""
    integration = PrometheusSparklineIntegration(mock_prom_client)

    # Warmup
    await integration.get_sparkline("test_metric")

    # Measure 10 runs
    times = []
    for _ in range(10):
        start = time.perf_counter()
        await integration.get_sparkline("test_metric")
        times.append((time.perf_counter() - start) * 1000)

    avg = sum(times) / len(times)
    assert avg < 50, f"Avg {avg:.2f}ms exceeds 50ms target"

@pytest.mark.performance
async def test_keyboard_action_latency():
    """Keyboard actions < 50ms"""
    app = DopemuxDashboard()

    async with app.run_test() as pilot:
        # Measure Tab key latency
        times = []
        for _ in range(20):
            start = time.perf_counter()
            await pilot.press("tab")
            times.append((time.perf_counter() - start) * 1000)

        avg = sum(times) / len(times)
        assert avg < 50, f"Avg {avg:.2f}ms exceeds 50ms target"
```

**Acceptance Criteria:**
- [ ] All integration tests pass
- [ ] All performance tests pass
- [ ] Sparkline latency < 50ms
- [ ] Keyboard latency < 50ms
- [ ] No crashes in 1-hour stress test
- [ ] Documentation updated

---

## 📊 IMPLEMENTATION CHECKLIST

### Hour 1-2: Prometheus Sparkline Integration
- [ ] Create `PrometheusSparklineIntegration` class
- [ ] Add caching logic (30s TTL)
- [ ] Integrate into `TrendsWidget`
- [ ] Test with mock data
- [ ] Test with live Prometheus
- [ ] Verify auto-refresh (30s)

### Hour 3-4: Keyboard Navigation
- [ ] Create `FocusManager` class
- [ ] Add BINDINGS to `DopemuxDashboard`
- [ ] Implement all action methods
- [ ] Add CSS for focus indicators
- [ ] Create `KeyboardHelpScreen`
- [ ] Test all shortcuts manually

### Hour 5-6: Testing & Polish
- [ ] Write integration tests (10 tests)
- [ ] Write performance tests (5 tests)
- [ ] Run full test suite
- [ ] Performance profiling
- [ ] Fix any bugs found
- [ ] Update documentation

---

## 🎯 SUCCESS METRICS

### Functional
- [x] SparklineGenerator exists ✅
- [x] PrometheusClient exists ✅
- [x] MetricsManager exists ✅ (Day 8)
- [ ] PrometheusSparklineIntegration works
- [ ] FocusManager works
- [ ] All keyboard shortcuts work
- [ ] Help modal accessible

### Performance
- [ ] Sparkline generation: <50ms
- [ ] Keyboard actions: <50ms
- [ ] Dashboard update (all sparklines): <200ms
- [ ] CPU usage: <5%
- [ ] Memory usage: <100MB
- [ ] Cache hit rate: >75%

### Quality
- [ ] Unit tests: 95%+ coverage
- [ ] Integration tests: Pass 100%
- [ ] Performance tests: Pass 100%
- [ ] No crashes in 1-hour test
- [ ] Documentation complete

---

## 🚀 READY TO START!

**Everything is planned!**
- ✅ Deep research complete (1,275 lines)
- ✅ Architecture designed
- ✅ Code examples ready
- ✅ Tests planned
- ✅ Success criteria defined

**Existing code we leverage:**
- ✅ SparklineGenerator (302 lines)
- ✅ PrometheusClient
- ✅ MetricsManager (Day 8)
- ✅ Dashboard base architecture

**New code to write:**
- PrometheusSparklineIntegration (~150 lines)
- FocusManager (~100 lines)
- Keyboard shortcuts (~50 lines)
- Help modal (~80 lines)
- Tests (~300 lines)

**Total new code:** ~680 lines
**Estimated time:** 6-8 hours
**Difficulty:** Medium
**Fun factor:** 🔥🔥🔥🔥🔥

---

## 📝 NEXT STEPS

1. **Review this document** (5 minutes)
2. **Start with Task 1** (Prometheus Sparklines) - 2 hours
3. **Move to Task 2** (Keyboard Navigation) - 3 hours
4. **Finish with Task 3** (Testing) - 1-2 hours
5. **Celebrate!** 🎉

**Let's build the most keyboard-friendly, visual ADHD dashboard ever!** 🚀

---

**Document Version:** 1.0
**Date:** 2025-10-29
**Status:** ✅ READY FOR IMPLEMENTATION
**Deep Research:** `DASHBOARD_DAY9_DEEP_RESEARCH.md` (1,275 lines)
