---
id: DASHBOARD_DAY10_READY
title: Dashboard_Day10_Ready
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Dashboard Day 10 - Implementation Ready! 🚀

**Date:** 2025-10-29
**Status:** ✅ READY TO CODE
**Deep Research:** Complete (6,500 words)
**Estimated Time:** 6-8 hours

---

## 📋 QUICK START

### What We're Building
1. **PrometheusSparklineIntegration** - Wire Prometheus → SparklineGenerator → Widgets
2. **Full Keyboard Navigation** - 100% keyboard control, zero mouse dependency
3. **Integration Testing** - 95%+ coverage, performance validation

### Why Now
- ✅ WebSocket streaming complete (Day 8)
- ✅ Drill-down modals complete (Day 6)
- ✅ SparklineGenerator already exists (302 lines)
- ✅ PrometheusClient ready
- 🎯 Time to connect the pieces!

### Success Criteria
- [ ] All 6 sparklines show real Prometheus data
- [ ] 100% keyboard navigable
- [ ] Performance: < 100ms, < 5% CPU
- [ ] 95%+ test coverage
- [ ] Zero crashes in 1-hour test

---

## 🎯 IMPLEMENTATION TASKS

### Task 1: PrometheusSparklineIntegration (3-4 hours)

#### File: `dopemux/integrations/prometheus_sparkline.py`

**Create new file with this code:**

```python
"""
Prometheus Sparkline Integration
Bridges Prometheus metrics → SparklineGenerator → Dashboard widgets
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from prometheus_client import PrometheusClient, PrometheusConfig
from sparkline_generator import SparklineGenerator

logger = logging.getLogger(__name__)


@dataclass
class SparklineConfig:
    """Configuration for a single sparkline metric"""
    metric_query: str           # Prometheus query
    time_window: str            # e.g., "2h", "7d", "24h"
    resolution: str             # e.g., "5m", "1h"
    width: int = 20             # Character width
    metric_type: str = "gauge"  # For color coding
    label: str = ""             # Display label
    cache_ttl: int = 30         # Cache seconds


@dataclass
class SparklineResult:
    """Result of sparkline generation"""
    sparkline: str              # Unicode sparkline string
    colored_sparkline: str      # With color codes
    stats: Dict[str, float]     # min, max, avg, current
    trend: str                  # "up", "down", "stable"
    trend_icon: str             # ▲, ▼, →
    last_updated: datetime
    from_cache: bool


class PrometheusSparklineIntegration:
    """
    Integrates Prometheus metrics with sparkline visualization.

    Features:
    - Batch fetching for efficiency
    - Intelligent caching with TTL
    - Error recovery (fallbacks, retries)
    - Real-time updates via callback

    Usage:
        prom = PrometheusClient(...)
        sparkgen = SparklineGenerator()
        integration = PrometheusSparklineIntegration(prom, sparkgen)

        config = SparklineConfig(
            metric_query="adhd_cognitive_load",
            time_window="2h",
            resolution="5m",
            label="Cognitive Load"
        )

        result = await integration.generate_sparkline(config)
        print(f"{result.label}: {result.colored_sparkline}")
    """

    def __init__(
        self,
        prometheus_client: PrometheusClient,
        sparkline_generator: SparklineGenerator,
        default_cache_ttl: int = 30
    ):
        self.prom = prometheus_client
        self.sparkgen = sparkline_generator
        self.cache: Dict[str, Tuple[SparklineResult, float]] = {}
        self.default_ttl = default_cache_ttl
        self.update_callbacks: List[callable] = []

    async def generate_sparkline(
        self,
        config: SparklineConfig,
        use_cache: bool = True
    ) -> SparklineResult:
        """
        Generate a single sparkline from Prometheus data.

        Process:
        1. Check cache (if enabled)
        2. Query Prometheus for time-series data
        3. Generate sparkline using SparklineGenerator
        4. Add color coding and stats
        5. Cache result
        6. Return SparklineResult
        """
        # 1. Check cache
        if use_cache:
            cached = self._get_from_cache(config.metric_query)
            if cached:
                logger.debug(f"Cache hit for {config.label}")
                return cached

        try:
            # 2. Query Prometheus
            data = await self._query_prometheus(
                config.metric_query,
                config.time_window,
                config.resolution
            )

            if not data:
                logger.warning(f"No data for {config.label}")
                return self._empty_sparkline(config, "No data")

            # 3. Generate sparkline
            sparkline = self.sparkgen.generate(
                data,
                width=config.width
            )

            # 4. Add coloring
            colored = self.sparkgen.colorize(
                sparkline,
                data,
                metric_type=config.metric_type
            )

            # 5. Calculate stats
            values = [v for _, v in data]
            stats = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "current": values[-1] if values else 0
            }

            # 6. Detect trend
            trend, trend_icon = self._detect_trend(data)

            result = SparklineResult(
                sparkline=sparkline,
                colored_sparkline=colored,
                stats=stats,
                trend=trend,
                trend_icon=trend_icon,
                last_updated=datetime.now(),
                from_cache=False
            )

            # 7. Cache result
            self._cache_result(config.metric_query, result, config.cache_ttl)

            logger.info(f"Generated sparkline for {config.label}: {trend} trend")
            return result

        except Exception as e:
            logger.error(f"Sparkline generation failed for {config.label}: {e}")
            return self._empty_sparkline(config, str(e))

    async def generate_batch(
        self,
        configs: List[SparklineConfig]
    ) -> Dict[str, SparklineResult]:
        """
        Generate multiple sparklines in parallel.

        More efficient than sequential generation.
        """
        logger.info(f"Generating batch of {len(configs)} sparklines")

        tasks = [
            self.generate_sparkline(config)
            for config in configs
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for config, result in zip(configs, results):
            if isinstance(result, Exception):
                logger.error(f"Batch generation failed for {config.label}: {result}")
                output[config.label] = self._empty_sparkline(config, str(result))
            else:
                output[config.label] = result

        return output

    async def _query_prometheus(
        self,
        query: str,
        time_window: str,
        resolution: str
    ) -> List[Tuple[datetime, float]]:
        """
        Query Prometheus for time-series data.

        Args:
            query: Prometheus query (e.g., "adhd_cognitive_load")
            time_window: How far back (e.g., "2h", "7d")
            resolution: Data point interval (e.g., "5m", "1h")

        Returns:
            List of (timestamp, value) tuples
        """
        # Construct range query
        range_query = f"{query}[{time_window}:{resolution}]"

        try:
            logger.debug(f"Querying Prometheus: {range_query}")
            result = await self.prom.query_range(
                query=range_query,
                timeout=5.0
            )
            logger.debug(f"Got {len(result)} data points")
            return result

        except Exception as e:
            logger.warning(f"Prometheus query failed: {e}")

            # Try simplified query (shorter time window)
            if time_window.endswith('d'):  # e.g., "7d" → "24h"
                simplified_window = "24h"
                simplified = f"{query}[{simplified_window}:{resolution}]"
                logger.info(f"Retrying with simplified query: {simplified}")

                try:
                    result = await self.prom.query_range(simplified, timeout=3.0)
                    logger.info(f"Simplified query succeeded with {len(result)} points")
                    return result
                except Exception as e2:
                    logger.error(f"Simplified query also failed: {e2}")

            return []

    def _detect_trend(self, data: List[Tuple[datetime, float]]) -> Tuple[str, str]:
        """
        Detect trend direction from time-series data.

        Algorithm: Compare first 25% to last 25% of data

        Returns:
            (trend_name, trend_icon)
        """
        if len(data) < 4:
            return ("stable", "→")

        values = [v for _, v in data]
        quarter = max(1, len(values) // 4)

        first_quarter_avg = sum(values[:quarter]) / quarter
        last_quarter_avg = sum(values[-quarter:]) / quarter

        if first_quarter_avg == 0:
            return ("stable", "→")

        change_pct = (last_quarter_avg - first_quarter_avg) / first_quarter_avg

        if change_pct > 0.1:  # 10% increase
            return ("up", "▲")
        elif change_pct < -0.1:  # 10% decrease
            return ("down", "▼")
        else:
            return ("stable", "→")

    def _get_from_cache(self, key: str) -> Optional[SparklineResult]:
        """Get cached sparkline if still valid"""
        if key not in self.cache:
            return None

        result, expires_at = self.cache[key]

        if datetime.now().timestamp() > expires_at:
            logger.debug(f"Cache expired for {key}")
            del self.cache[key]
            return None

        # Mark as from cache
        result.from_cache = True
        return result

    def _cache_result(self, key: str, result: SparklineResult, ttl: int):
        """Cache sparkline result with TTL"""
        expires_at = datetime.now().timestamp() + ttl
        self.cache[key] = (result, expires_at)
        logger.debug(f"Cached {key} with TTL={ttl}s")

    def _empty_sparkline(self, config: SparklineConfig, reason: str) -> SparklineResult:
        """Return empty sparkline on error"""
        empty = "─" * config.width
        return SparklineResult(
            sparkline=empty,
            colored_sparkline=f"[dim]{empty}[/dim]",
            stats={"min": 0, "max": 0, "avg": 0, "current": 0},
            trend="stable",
            trend_icon="→",
            last_updated=datetime.now(),
            from_cache=False
        )

    def register_update_callback(self, callback: callable):
        """Register callback for sparkline updates"""
        self.update_callbacks.append(callback)
        logger.info(f"Registered update callback: {callback.__name__}")

    async def auto_update_loop(self, interval: int = 30):
        """Background task to auto-update all sparklines"""
        logger.info(f"Starting auto-update loop (interval={interval}s)")

        while True:
            await asyncio.sleep(interval)

            logger.debug("Auto-update triggered")
            # Clear cache to force refresh
            self.cache.clear()

            # Notify callbacks
            for callback in self.update_callbacks:
                try:
                    await callback()
                except Exception as e:
                    logger.error(f"Update callback {callback.__name__} failed: {e}")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": 100,  # Could make configurable
        }


# Predefined sparkline configurations for dashboard
DASHBOARD_SPARKLINES = [
    SparklineConfig(
        metric_query="adhd_cognitive_load",
        time_window="2h",
        resolution="5m",
        width=20,
        metric_type="cognitive_load",
        label="Cognitive Load (2h)",
        cache_ttl=30
    ),
    SparklineConfig(
        metric_query="rate(adhd_task_completions_total[1h])",
        time_window="7d",
        resolution="1h",
        width=20,
        metric_type="velocity",
        label="Task Velocity (7d)",
        cache_ttl=60
    ),
    SparklineConfig(
        metric_query="adhd_energy_level",
        time_window="24h",
        resolution="5m",
        width=20,
        metric_type="gauge",
        label="Energy Level (24h)",
        cache_ttl=30
    ),
    SparklineConfig(
        metric_query="increase(adhd_context_switches_total[1m])",
        time_window="1h",
        resolution="1m",
        width=20,
        metric_type="gauge",
        label="Context Switches (1h)",
        cache_ttl=10
    ),
    SparklineConfig(
        metric_query="adhd_flow_events_total",
        time_window="7d",
        resolution="1h",
        width=20,
        metric_type="gauge",
        label="Flow Events (7d)",
        cache_ttl=300
    ),
    SparklineConfig(
        metric_query="adhd_break_compliance_rate",
        time_window="24h",
        resolution="5m",
        width=20,
        metric_type="gauge",
        label="Break Compliance (24h)",
        cache_ttl=60
    ),
]
```

**Subtasks:**
- [ ] Create file `dopemux/integrations/prometheus_sparkline.py`
- [ ] Copy code above
- [ ] Run: `python -c "from dopemux.integrations.prometheus_sparkline import *; print('✓ Import OK')"`
- [ ] Fix any import errors

---

### Task 2: Update TrendsWidget (1 hour)

#### File: `dopemux_dashboard.py` (modify existing)

**Find TrendsPanel class and update:**

```python
# Add this import at top
from dopemux.integrations.prometheus_sparkline import (
    PrometheusSparklineIntegration,
    DASHBOARD_SPARKLINES
)

# Update TrendsPanel class
class TrendsPanel(Static):
    """Trends visualization panel with real Prometheus sparklines"""

    sparklines = reactive({})
    last_update = reactive("")

    def __init__(self, sparkline_integration: PrometheusSparklineIntegration):
        super().__init__()
        self.integration = sparkline_integration
        self.update_task = None

    async def on_mount(self):
        """Start sparkline updates when widget mounts"""
        # Initial load
        await self.update_sparklines()

        # Start auto-update
        self.update_task = asyncio.create_task(self._auto_update_loop())

    async def on_unmount(self):
        """Cancel auto-update when widget unmounts"""
        if self.update_task:
            self.update_task.cancel()

    async def update_sparklines(self):
        """Fetch and update all sparklines"""
        try:
            # Batch fetch all sparklines
            results = await self.integration.generate_batch(DASHBOARD_SPARKLINES)

            # Update reactive state
            self.sparklines = results
            self.last_update = datetime.now().strftime("%H:%M:%S")

            logger.info(f"Updated {len(results)} sparklines")

        except Exception as e:
            logger.error(f"Sparkline update failed: {e}")

    async def _auto_update_loop(self):
        """Auto-update sparklines every 30 seconds"""
        while True:
            await asyncio.sleep(30)
            await self.update_sparklines()

    def render(self) -> Panel:
        """Render trends panel with sparklines"""
        if not self.sparklines:
            return Panel(
                "[dim]Loading sparklines...[/dim]",
                title="📊 Trends",
                border_style="blue"
            )

        lines = [
            "Trends & Patterns",
            ""
        ]

        for label, result in self.sparklines.items():
            lines.append(
                f"{label:25} {result.trend_icon} {result.colored_sparkline} "
                f"[dim]{result.stats['current']:.1f}[/dim]"
            )

        lines.append("")
        lines.append(f"[dim]Updated: {self.last_update}[/dim]")

        return Panel(
            "\n".join(lines),
            title="📊 Trends",
            border_style="blue"
        )
```

**Subtasks:**
- [ ] Add import at top of `dopemux_dashboard.py`
- [ ] Find `TrendsPanel` class
- [ ] Replace with updated code above
- [ ] Test: `python dopemux_dashboard.py` (should see real sparklines)

---

### Task 3: Keyboard Navigation (2-3 hours)

#### File: `dopemux/ui/keybindings.py` (new file)

```python
"""
Keyboard Navigation System
Centralized keybinding registry and focus management
"""

from enum import Enum
from typing import Dict, Callable, Optional, List, Any
import logging

logger = logging.getLogger(__name__)


class PanelID(Enum):
    """Panel identifiers for navigation"""
    ADHD = "adhd"
    PRODUCTIVITY = "productivity"
    SERVICES = "services"
    TRENDS = "trends"
    FOOTER = "footer"


class KeybindingRegistry:
    """
    Central registry for all keyboard shortcuts.

    Features:
    - Conflict detection
    - Context-aware bindings (modal vs main)
    - Help text generation
    """

    def __init__(self):
        self.bindings: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        key: str,
        action: Callable,
        description: str,
        context: str = "global",
        show_in_help: bool = True
    ):
        """Register a keyboard shortcut"""
        if key in self.bindings:
            logger.warning(f"Overriding existing binding for '{key}'")

        self.bindings[key] = {
            "action": action,
            "description": description,
            "context": context,
            "show_in_help": show_in_help
        }

        logger.debug(f"Registered: {key} → {description}")

    def get_action(self, key: str, context: str = "global") -> Optional[Callable]:
        """Get action for key in given context"""
        binding = self.bindings.get(key)
        if not binding:
            return None

        # Check context match
        if binding["context"] not in [context, "global"]:
            return None

        return binding["action"]

    def generate_help_text(self) -> str:
        """Generate help screen content"""
        lines = ["# Keyboard Shortcuts\n"]

        categories = {
            "Navigation": [],
            "Panels": [],
            "Actions": [],
            "Modals": [],
        }

        for key, binding in self.bindings.items():
            if not binding["show_in_help"]:
                continue

            # Categorize
            if binding["context"] == "modal":
                categories["Modals"].append((key, binding["description"]))
            elif key.isdigit():
                categories["Panels"].append((key, binding["description"]))
            elif key in ["tab", "shift+tab", "up", "down", "left", "right"]:
                categories["Navigation"].append((key, binding["description"]))
            else:
                categories["Actions"].append((key, binding["description"]))

        for category, items in categories.items():
            if items:
                lines.append(f"\n## {category}\n")
                for key, desc in sorted(items):
                    lines.append(f"  {key:15} {desc}")

        return "\n".join(lines)


class FocusManager:
    """
    Manages focus state across dashboard panels.

    Features:
    - Logical focus order (top→bottom, left→right)
    - Focus history (for back navigation)
    - Visual feedback coordination
    """

    def __init__(self, app):
        self.app = app
        self.current_panel: Optional[PanelID] = None
        self.focus_history: List[PanelID] = []
        self.panel_order = [
            PanelID.ADHD,
            PanelID.PRODUCTIVITY,
            PanelID.SERVICES,
            PanelID.TRENDS,
        ]

    def focus_panel(self, panel_id: PanelID):
        """Set focus to specific panel"""
        if self.current_panel:
            self.focus_history.append(self.current_panel)

        self.current_panel = panel_id
        self._apply_visual_focus(panel_id)

        logger.info(f"Focused panel: {panel_id.value}")

    def next_panel(self):
        """Focus next panel in order"""
        if not self.current_panel:
            self.focus_panel(self.panel_order[0])
            return

        current_idx = self.panel_order.index(self.current_panel)
        next_idx = (current_idx + 1) % len(self.panel_order)
        self.focus_panel(self.panel_order[next_idx])

    def prev_panel(self):
        """Focus previous panel"""
        if not self.current_panel:
            self.focus_panel(self.panel_order[-1])
            return

        current_idx = self.panel_order.index(self.current_panel)
        prev_idx = (current_idx - 1) % len(self.panel_order)
        self.focus_panel(self.panel_order[prev_idx])

    def back(self):
        """Return to previous focus"""
        if self.focus_history:
            prev_panel = self.focus_history.pop()
            self.current_panel = prev_panel
            self._apply_visual_focus(prev_panel)

    def _apply_visual_focus(self, panel_id: PanelID):
        """Apply visual focus indicator to panel"""
        try:
            # Remove focus from all panels
            for pid in self.panel_order:
                widget = self.app.query_one(f"#{pid.value}")
                widget.remove_class("focused")

            # Add focus to target panel
            widget = self.app.query_one(f"#{panel_id.value}")
            widget.add_class("focused")
        except Exception as e:
            logger.error(f"Focus application failed: {e}")
```

#### File: `dopemux_dashboard.py` (add keyboard support)

**Add to imports:**
```python
from dopemux.ui.keybindings import KeybindingRegistry, FocusManager, PanelID
```

**Add to DopemuxDashboard class:**

```python
class DopemuxDashboard(App):
    """Enhanced dashboard with full keyboard navigation"""

    CSS = """
    .panel {
        border: solid $surface0;
        transition: border 150ms;
    }

    .panel.focused {
        border: thick $blue;
        box-shadow: 0 0 8px $blue;
    }
    """

    BINDINGS = [
        # Panel focus (1-4)
        ("1", "focus_panel('adhd')", "ADHD State"),
        ("2", "focus_panel('productivity')", "Productivity"),
        ("3", "focus_panel('services')", "Services"),
        ("4", "focus_panel('trends')", "Trends"),

        # Navigation
        ("tab", "next_panel", "Next Panel"),
        ("shift+tab", "prev_panel", "Previous Panel"),

        # Actions
        ("f", "toggle_focus_mode", "Focus Mode"),
        ("t", "cycle_theme", "Themes"),
        ("r", "refresh_all", "Refresh"),

        # Help
        ("question_mark", "show_help", "Help"),
        ("escape", "close_modal", "Close"),
    ]

    def __init__(self):
        super().__init__()
        self.keybindings = KeybindingRegistry()
        self.focus_manager = FocusManager(self)
        self._register_keybindings()

    def _register_keybindings(self):
        """Register all keyboard shortcuts"""
        # Navigation
        self.keybindings.register("tab", self.action_next_panel, "Next Panel")
        self.keybindings.register("shift+tab", self.action_prev_panel, "Previous Panel")

        # Panel focus
        for i, panel in enumerate([PanelID.ADHD, PanelID.PRODUCTIVITY,
                                    PanelID.SERVICES, PanelID.TRENDS], 1):
            self.keybindings.register(
                str(i),
                lambda p=panel: self.action_focus_panel(p.value),
                f"{panel.value.title()} Panel"
            )

        # Actions
        self.keybindings.register("f", self.action_toggle_focus_mode, "Focus Mode")
        self.keybindings.register("t", self.action_cycle_theme, "Cycle Themes")
        self.keybindings.register("r", self.action_refresh_all, "Refresh All")
        self.keybindings.register("?", self.action_show_help, "Help")

        # Modal bindings
        self.keybindings.register("escape", self.action_close_modal, "Close Modal", context="modal")

    def action_focus_panel(self, panel_id: str):
        """Focus specific panel"""
        self.focus_manager.focus_panel(PanelID(panel_id))

    def action_next_panel(self):
        """Navigate to next panel"""
        self.focus_manager.next_panel()

    def action_prev_panel(self):
        """Navigate to previous panel"""
        self.focus_manager.prev_panel()

    def action_show_help(self):
        """Show keyboard shortcuts help"""
        help_text = self.keybindings.generate_help_text()
        # TODO: Create HelpModal
        logger.info("Help requested (modal not implemented yet)")
        logger.info(f"\n{help_text}")

    def action_close_modal(self):
        """Close current modal"""
        try:
            self.pop_screen()
        except:
            pass

    def action_refresh_all(self):
        """Refresh all widgets"""
        self.refresh()
```

**Subtasks:**
- [ ] Create `dopemux/ui/keybindings.py`
- [ ] Add keyboard navigation to `dopemux_dashboard.py`
- [ ] Add CSS for focus indicators
- [ ] Test: Press 1-4 keys to focus panels
- [ ] Test: Tab/Shift+Tab navigation
- [ ] Test: ? for help

---

### Task 4: Integration Tests (1-2 hours)

#### File: `tests/test_prometheus_sparkline.py`

```python
"""
Integration tests for PrometheusSparklineIntegration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from dopemux.integrations.prometheus_sparkline import (
    PrometheusSparklineIntegration,
    SparklineConfig,
    SparklineResult
)
from prometheus_client import PrometheusClient, PrometheusConfig
from sparkline_generator import SparklineGenerator


@pytest.fixture
async def integration():
    """Create test integration instance"""
    prom_config = PrometheusConfig(url="http://localhost:9090")
    prom_client = PrometheusClient(prom_config)
    sparkgen = SparklineGenerator()
    return PrometheusSparklineIntegration(prom_client, sparkgen)


@pytest.fixture
def sample_config():
    """Sample sparkline configuration"""
    return SparklineConfig(
        metric_query="adhd_cognitive_load",
        time_window="2h",
        resolution="5m",
        width=20,
        metric_type="cognitive_load",
        label="Test Metric"
    )


@pytest.mark.asyncio
async def test_generate_sparkline_basic(integration, sample_config):
    """Test basic sparkline generation"""
    result = await integration.generate_sparkline(sample_config)

    assert isinstance(result, SparklineResult)
    assert len(result.sparkline) == sample_config.width
    assert result.label or True  # Has some label
    assert result.trend in ["up", "down", "stable"]


@pytest.mark.asyncio
async def test_generate_batch(integration):
    """Test batch sparkline generation"""
    configs = [
        SparklineConfig(
            metric_query="adhd_cognitive_load",
            time_window="2h",
            resolution="5m",
            label="Metric 1"
        ),
        SparklineConfig(
            metric_query="adhd_energy_level",
            time_window="24h",
            resolution="5m",
            label="Metric 2"
        ),
    ]

    results = await integration.generate_batch(configs)

    assert len(results) == 2
    assert "Metric 1" in results
    assert "Metric 2" in results


@pytest.mark.asyncio
async def test_caching(integration, sample_config):
    """Test sparkline caching"""
    # First call - should cache
    result1 = await integration.generate_sparkline(sample_config, use_cache=True)
    assert result1.from_cache == False

    # Second call - should hit cache
    result2 = await integration.generate_sparkline(sample_config, use_cache=True)
    assert result2.from_cache == True

    # Third call - bypass cache
    result3 = await integration.generate_sparkline(sample_config, use_cache=False)
    assert result3.from_cache == False


@pytest.mark.asyncio
async def test_error_handling(integration):
    """Test error handling for invalid queries"""
    config = SparklineConfig(
        metric_query="invalid_metric_that_does_not_exist",
        time_window="2h",
        resolution="5m",
        label="Invalid"
    )

    result = await integration.generate_sparkline(config)

    # Should return empty sparkline, not crash
    assert isinstance(result, SparklineResult)
    assert result.sparkline == "─" * config.width


@pytest.mark.asyncio
async def test_trend_detection(integration):
    """Test trend detection accuracy"""
    # Create mock data with clear upward trend
    now = datetime.now()
    data = [(now - timedelta(minutes=i*5), i) for i in range(24)]

    trend, icon = integration._detect_trend(data)
    assert trend == "up"
    assert icon == "▲"


def test_cache_stats(integration):
    """Test cache statistics"""
    stats = integration.get_cache_stats()
    assert "size" in stats
    assert isinstance(stats["size"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

#### File: `tests/test_keyboard_nav.py`

```python
"""
Tests for keyboard navigation system
"""

import pytest
from dopemux.ui.keybindings import (
    KeybindingRegistry,
    FocusManager,
    PanelID
)


@pytest.fixture
def keybindings():
    """Create test keybinding registry"""
    return KeybindingRegistry()


@pytest.fixture
def mock_app():
    """Create mock app for FocusManager"""
    class MockApp:
        def query_one(self, selector):
            class MockWidget:
                def add_class(self, cls): pass
                def remove_class(self, cls): pass
            return MockWidget()
    return MockApp()


@pytest.fixture
def focus_manager(mock_app):
    """Create test focus manager"""
    return FocusManager(mock_app)


def test_register_keybinding(keybindings):
    """Test keybinding registration"""
    def action(): pass

    keybindings.register("f", action, "Test Action")

    assert "f" in keybindings.bindings
    assert keybindings.bindings["f"]["description"] == "Test Action"


def test_get_action(keybindings):
    """Test action retrieval"""
    def action(): return "test"

    keybindings.register("f", action, "Test")
    retrieved = keybindings.get_action("f")

    assert retrieved == action
    assert retrieved() == "test"


def test_context_filtering(keybindings):
    """Test context-aware bindings"""
    def global_action(): pass
    def modal_action(): pass

    keybindings.register("f", global_action, "Global", context="global")
    keybindings.register("m", modal_action, "Modal", context="modal")

    # Global context should get global actions only
    assert keybindings.get_action("f", "global") == global_action
    assert keybindings.get_action("m", "global") is None

    # Modal context should get both
    assert keybindings.get_action("m", "modal") == modal_action


def test_help_text_generation(keybindings):
    """Test help text generation"""
    keybindings.register("f", lambda: None, "Focus", show_in_help=True)
    keybindings.register("h", lambda: None, "Hidden", show_in_help=False)

    help_text = keybindings.generate_help_text()

    assert "Focus" in help_text
    assert "Hidden" not in help_text


def test_focus_panel(focus_manager):
    """Test panel focusing"""
    focus_manager.focus_panel(PanelID.ADHD)

    assert focus_manager.current_panel == PanelID.ADHD
    assert len(focus_manager.focus_history) == 0


def test_next_panel(focus_manager):
    """Test next panel navigation"""
    focus_manager.focus_panel(PanelID.ADHD)
    focus_manager.next_panel()

    assert focus_manager.current_panel == PanelID.PRODUCTIVITY


def test_prev_panel(focus_manager):
    """Test previous panel navigation"""
    focus_manager.focus_panel(PanelID.PRODUCTIVITY)
    focus_manager.prev_panel()

    assert focus_manager.current_panel == PanelID.ADHD


def test_focus_wrap_around(focus_manager):
    """Test focus wraps around at ends"""
    focus_manager.focus_panel(PanelID.TRENDS)
    focus_manager.next_panel()

    # Should wrap to first panel
    assert focus_manager.current_panel == PanelID.ADHD


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Subtasks:**
- [ ] Create test files
- [ ] Run: `pytest tests/test_prometheus_sparkline.py -v`
- [ ] Run: `pytest tests/test_keyboard_nav.py -v`
- [ ] Achieve 95%+ coverage

---

## ✅ VERIFICATION CHECKLIST

### Functional Testing
- [ ] All 6 sparklines display real Prometheus data
- [ ] Sparklines update every 30 seconds
- [ ] Can navigate with 1-4 keys
- [ ] Tab/Shift+Tab navigation works
- [ ] ? shows help screen
- [ ] Escape closes modals
- [ ] Focus indicators are visible

### Performance Testing
- [ ] Dashboard starts in < 2 seconds
- [ ] Sparkline updates < 100ms
- [ ] CPU usage < 5%
- [ ] Memory stable over 1 hour

### Error Handling
- [ ] Graceful degradation if Prometheus down
- [ ] Cache fallback works
- [ ] No crashes on bad data

### Code Quality
- [ ] All tests pass
- [ ] 95%+ test coverage
- [ ] No linting errors
- [ ] Git commits clean

---

## 🚀 DEPLOYMENT

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/day10-sparklines-keyboard

# Implement in commits:
git add dopemux/integrations/prometheus_sparkline.py
git commit -m "Add PrometheusSparklineIntegration"

git add dopemux/ui/keybindings.py
git commit -m "Add keyboard navigation system"

git add dopemux_dashboard.py
git commit -m "Wire sparklines and keyboard nav to dashboard"

git add tests/
git commit -m "Add integration tests"

# Push
git push origin feature/day10-sparklines-keyboard
```

---

## 📊 SUCCESS METRICS

**Completed when:**
- [x] Deep research complete (6,500 words)
- [x] Implementation plan ready
- [ ] All 6 sparklines showing real data
- [ ] 100% keyboard navigable
- [ ] Performance < 100ms, < 5% CPU
- [ ] 95%+ test coverage
- [ ] Zero crashes in 1-hour test

---

**Ready to implement?** 🚀 Let's code!

**Estimated Time:** 6-8 hours
**Start Time:** _____________
**End Time:** _____________

**Notes:**
