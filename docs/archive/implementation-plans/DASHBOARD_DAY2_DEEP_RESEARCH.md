---
id: DASHBOARD_DAY2_DEEP_RESEARCH
title: Dashboard_Day2_Deep_Research
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Dashboard_Day2_Deep_Research (explanation) for dopemux documentation and
  developer workflows.
---
# Dashboard Day 2: Deep Research & Planning 🔬

**Created:** 2025-10-29
**Phase:** Advanced Features - Sparklines & Interactive Navigation
**Approach:** Zen Research → Deep Analysis → Surgical Implementation

---

## 🎯 EXECUTIVE SUMMARY

### What We're Building (Day 2 Focus)
**Primary Goal:** Enhanced sparklines with real historical Prometheus data
**Secondary Goal:** Interactive keyboard navigation foundation

### Why This Matters
- Current dashboard shows static/placeholder data
- Users need **trend visualization** to understand patterns
- Cognitive load over time reveals ADHD state patterns
- Task velocity trends show productivity cycles
- Context switches reveal distraction patterns

### Success Criteria
- [ ] Sparklines render real Prometheus time-series data
- [ ] At least 3 metrics show historical trends (2hr, 24hr, 7day)
- [ ] Auto-refresh every 30 seconds
- [ ] Handles missing data gracefully (gaps, no data, Prometheus down)
- [ ] Performance: < 100ms render, < 5% CPU
- [ ] Visual: Clear at-a-glance trend direction

---

## 📚 DEEP RESEARCH: SPARKLINES

### What Are Sparklines?
> "Intense, simple, word-sized graphics" - Edward Tufte

**Design Principles:**
1. **High data density** - Maximum information in minimal space
1. **Contextual** - Embedded inline with text
1. **Trend focus** - Show direction, not exact values
1. **No decoration** - No axes, labels, or legends
1. **Fast perception** - Understand in < 1 second

### Examples in Production Systems
```
btop:     CPU  [▁▂▃▅▇██▇▅▃▂▁]  85%
k9s:      Pods [▂▃▅▆▇██▇▅▃▂▁]  12/15
lazygit:  Commits ▁▁▂▃▅▇█▇▅▃▂ (last 30 days)
```

### Best Practices for ADHD Users
1. **Use color** - Green (↑), Red (↓), Yellow (≈)
1. **Show recent on right** - Time flows left → right
1. **Consistent scale** - Same metric = same visual range
1. **Smooth interpolation** - No jarring jumps
1. **Context markers** - Highlight anomalies

---

## 🏗️ TECHNICAL ARCHITECTURE

### Data Flow
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Prometheus  │─────▶│  Sparkline  │─────▶│  Dashboard  │
│   Metrics   │      │  Generator  │      │    Panel    │
│  (PromQL)   │      │  (Python)   │      │  (Textual)  │
└─────────────┘      └─────────────┘      └─────────────┘
     ▲                     ▲                     ▲
     │                     │                     │
  Historical          Rendering              Display
   Queries             Logic                 Updates
```

### Component Design

#### 1. PrometheusClient (Data Layer)
```python
class PrometheusClient:
    """Fetches time-series data from Prometheus"""

    def __init__(self, base_url: str = "http://localhost:9090"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=5.0)

    async def query_range(
        self,
        query: str,
        hours: int = 24,
        step: str = "5m"
    ) -> List[Tuple[datetime, float]]:
        """
        Query Prometheus for time-series data

        Args:
            query: PromQL query (e.g., 'adhd_cognitive_load')
            hours: How far back to fetch
            step: Resolution (1m, 5m, 15m, 1h)

        Returns:
            List of (timestamp, value) tuples
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        params = {
            'query': query,
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'step': step
        }

        response = await self.client.get(
            f"{self.base_url}/api/v1/query_range",
            params=params
        )

        if response.status_code != 200:
            logger.warning(f"Prometheus query failed: {response.text}")
            return []

        data = response.json()
        if data['status'] != 'success':
            return []

        # Parse result
        result = data['data']['result']
        if not result:
            return []

        # Extract values
        values = result[0]['values']  # [[timestamp, value], ...]
        return [(datetime.fromtimestamp(ts), float(val)) for ts, val in values]
```

#### 2. SparklineGenerator (Rendering Layer)
```python
class SparklineGenerator:
    """Converts time-series data into ASCII/Unicode sparklines"""

    # Unicode block characters for smooth rendering
    BLOCKS = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

    def generate(
        self,
        data: List[Tuple[datetime, float]],
        width: int = 20,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None
    ) -> str:
        """
        Generate sparkline from time-series data

        Args:
            data: List of (timestamp, value) tuples
            width: Desired character width
            min_val: Force minimum value (for consistent scale)
            max_val: Force maximum value

        Returns:
            Unicode sparkline string
        """
        if not data:
            return '─' * width  # Empty line if no data

        # Extract values
        values = [v for _, v in data]

        # Resample to desired width
        if len(values) > width:
            # Downsample - take every Nth value
            step = len(values) / width
            values = [values[int(i * step)] for i in range(width)]
        elif len(values) < width:
            # Upsample - interpolate
            values = self._interpolate(values, width)

        # Normalize to 0-7 range
        min_v = min_val if min_val is not None else min(values)
        max_v = max_val if max_val is not None else max(values)

        if max_v == min_v:
            # Flat line
            return self.BLOCKS[4] * width

        normalized = [
            int((v - min_v) / (max_v - min_v) * 7)
            for v in values
        ]

        # Render
        return ''.join(self.BLOCKS[n] for n in normalized)

    def _interpolate(self, values: List[float], target_len: int) -> List[float]:
        """Linear interpolation to expand data"""
        if len(values) == 1:
            return values * target_len

        result = []
        step = (len(values) - 1) / (target_len - 1)

        for i in range(target_len):
            idx = i * step
            idx_low = int(idx)
            idx_high = min(idx_low + 1, len(values) - 1)
            weight = idx - idx_low

            val = values[idx_low] * (1 - weight) + values[idx_high] * weight
            result.append(val)

        return result

    def colorize(self, sparkline: str, values: List[float]) -> str:
        """Add ADHD-optimized color based on trends"""
        if len(values) < 2:
            return sparkline

        # Calculate trend
        recent_avg = sum(values[-3:]) / min(3, len(values))
        older_avg = sum(values[:3]) / min(3, len(values))

        if recent_avg > older_avg * 1.1:
            # Upward trend - green
            return f"[green]{sparkline}[/green]"
        elif recent_avg < older_avg * 0.9:
            # Downward trend - red
            return f"[red]{sparkline}[/red]"
        else:
            # Stable - yellow
            return f"[yellow]{sparkline}[/yellow]"
```

#### 3. Dashboard Integration (UI Layer)
```python
class TrendsPanel(Static):
    """Trends panel with live sparklines"""

    def __init__(self):
        super().__init__()
        self.prom = PrometheusClient()
        self.sparkline_gen = SparklineGenerator()
        self.sparklines = {}

    async def update_sparklines(self):
        """Fetch and render all sparklines"""

        # Cognitive Load (last 2 hours, 5min resolution)
        cognitive_data = await self.prom.query_range(
            'adhd_cognitive_load{load_category="optimal"}',
            hours=2,
            step='5m'
        )
        self.sparklines['cognitive'] = self.sparkline_gen.generate(
            cognitive_data,
            width=24,
            min_val=0,
            max_val=100
        )

        # Task Velocity (last 7 days, 1hr resolution)
        velocity_data = await self.prom.query_range(
            'adhd_task_velocity_per_day',
            hours=168,  # 7 days
            step='1h'
        )
        self.sparklines['velocity'] = self.sparkline_gen.generate(
            velocity_data,
            width=24
        )

        # Context Switches (last 24 hours, 15min resolution)
        switches_data = await self.prom.query_range(
            'adhd_context_switches_total',
            hours=24,
            step='15m'
        )
        self.sparklines['switches'] = self.sparkline_gen.generate(
            switches_data,
            width=24
        )

        # Refresh display
        self.refresh()

    def render(self) -> Panel:
        """Render trends panel with sparklines"""

        content = f"""
╔══ 📈 Trends (Live) ═══════════════════════╗
║                                            ║
║  Cognitive Load (2h)                      ║
║  {self.sparklines.get('cognitive', '─' * 24)}  ║
║  [dim]Low ←─────────────────────→ High[/dim]   ║
║                                            ║
║  Task Velocity (7d)                       ║
║  {self.sparklines.get('velocity', '─' * 24)}   ║
║  [dim]Mon ←───────────────────→ Sun[/dim]      ║
║                                            ║
║  Context Switches (24h)                   ║
║  {self.sparklines.get('switches', '─' * 24)}   ║
║  [dim]00:00 ←─────────────→ 23:59[/dim]       ║
║                                            ║
╚════════════════════════════════════════════╝
        """

        return Panel(content, style="cyan")
```

---

## 🎨 VISUAL DESIGN RESEARCH

### Color Psychology for ADHD
**Research:** Color improves working memory recall by 55-78% (Singh, 2006)

**Our Color Strategy:**
```python
TREND_COLORS = {
    'positive': 'green',      # Dopamine boost - progress!
    'negative': 'red',        # Alert - needs attention
    'stable': 'yellow',       # Neutral - monitor
    'unknown': 'dim white'    # No data
}

COGNITIVE_LOAD_COLORS = {
    (0, 50): 'green',         # Optimal flow zone
    (50, 70): 'yellow',       # Moderate - sustainable
    (70, 85): 'orange',       # High - take break soon
    (85, 100): 'red'          # Critical - break NOW
}
```

### Information Hierarchy
```
Priority 1: Current value (large, bright)
Priority 2: Trend direction (color + sparkline)
Priority 3: Historical context (muted sparkline)
Priority 4: Exact numbers (only on hover/drill-down)
```

### Layout Research
**Finding:** Users scan F-pattern (top-left → top-right → left side)

**Our Layout:**
```
┌────────────────────────────────┐
│ 🧠 65% [▃▅▆▇▇▇▆▅] ↗           │ ← Top: Current + Trend
│ Last 2h: Climbing              │ ← Context
│ [View details: press 'd']      │ ← Action
└────────────────────────────────┘
```

---

## 📊 METRICS TO VISUALIZE (Priority Order)

### Tier 1: Critical ADHD Metrics (Must Have)
1. **Cognitive Load** (2-hour window)
- Query: `adhd_cognitive_load{load_category="optimal"}`
- Update: Every 30s
- Scale: 0-100%
- Color: Green (0-50), Yellow (50-70), Orange (70-85), Red (85-100)

1. **Task Velocity** (7-day window)
- Query: `adhd_task_velocity_per_day`
- Update: Every 5 min
- Scale: Tasks per day
- Color: Green (↑), Red (↓), Yellow (→)

1. **Context Switches** (24-hour window)
- Query: `adhd_context_switches_total`
- Update: Every 1 min
- Scale: Switches per hour
- Color: Green (low), Red (high)

### Tier 2: Flow State Metrics (Should Have)
1. **Flow Duration** (24-hour window)
- Query: `adhd_flow_duration_seconds`
- Update: Every 5 min
- Scale: Minutes in flow
- Color: Green (high), Yellow (low)

1. **Break Adherence** (7-day window)
- Query: `adhd_break_adherence_rate`
- Update: Every 5 min
- Scale: 0-100%
- Color: Green (>80%), Yellow (60-80%), Red (<60%)

### Tier 3: Pattern Metrics (Nice to Have)
1. **Decision Quality** (7-day trend)
- Query: `conport_decision_quality_score`
- Update: Every 5 min

1. **Pattern Matches** (24-hour trend)
- Query: `serena_pattern_matches_total`
- Update: Every 1 min

---

## 🔧 IMPLEMENTATION PLAN

### Phase 1: Foundation (Morning - 2 hours)
**Goal:** Basic sparkline infrastructure working

```python
# Step 1: Create prometheus_client.py (30 min)
- PrometheusClient class
- query_range() method
- Error handling
- Connection pooling

# Step 2: Create sparkline_generator.py (45 min)
- SparklineGenerator class
- generate() method
- _interpolate() helper
- colorize() method

# Step 3: Unit tests (45 min)
- Test empty data
- Test single point
- Test full range
- Test interpolation
- Test colorization
```

### Phase 2: Integration (Afternoon - 2 hours)
**Goal:** Sparklines in dashboard

```python
# Step 1: Update TrendsPanel (60 min)
- Add sparkline rendering
- Add auto-refresh timer
- Handle missing data
- Add loading states

# Step 2: Update main dashboard (30 min)
- Wire up TrendsPanel
- Add refresh interval config
- Test with real Prometheus

# Step 3: Visual polish (30 min)
- Adjust colors
- Fine-tune widths
- Add context labels
- Test readability
```

### Phase 3: Testing & Refinement (Evening - 1 hour)
**Goal:** Production-ready quality

```python
# Step 1: Performance testing (20 min)
- Measure render time
- Check CPU usage
- Test with 24hr data load

# Step 2: Edge case testing (20 min)
- Prometheus down
- No data returned
- Partial data
- Stale data

# Step 3: UX refinement (20 min)
- Adjust update intervals
- Fine-tune colors
- Smooth animations
- User feedback
```

---

## 🎯 ACCEPTANCE CRITERIA

### Functional Requirements
- [ ] Cognitive load sparkline shows last 2 hours
- [ ] Task velocity sparkline shows last 7 days
- [ ] Context switches sparkline shows last 24 hours
- [ ] All sparklines auto-refresh every 30 seconds
- [ ] Handles Prometheus downtime gracefully
- [ ] Shows "No data" state clearly
- [ ] Colors indicate trend direction

### Performance Requirements
- [ ] Sparkline render time < 50ms
- [ ] Total dashboard update < 100ms
- [ ] CPU usage < 5% during updates
- [ ] Memory stable (no leaks over 1 hour)

### UX Requirements
- [ ] Sparklines readable at a glance
- [ ] Trend direction clear (color + shape)
- [ ] No visual jitter during updates
- [ ] Smooth interpolation (no jagged lines)
- [ ] Context labels visible

### Code Quality
- [ ] Unit tests for sparkline generator
- [ ] Error handling for all API calls
- [ ] Logging for debugging
- [ ] Type hints throughout
- [ ] Docstrings on public methods

---

## 🧪 TESTING STRATEGY

### Unit Tests
```python
def test_sparkline_empty_data():
    gen = SparklineGenerator()
    result = gen.generate([])
    assert result == '─' * 20

def test_sparkline_single_point():
    gen = SparklineGenerator()
    result = gen.generate([(now(), 50.0)], width=10)
    assert len(result) == 10
    assert all(c == '▄' for c in result)  # Mid-range block

def test_sparkline_full_range():
    gen = SparklineGenerator()
    data = [(now(), i * 10.0) for i in range(11)]  # 0, 10, 20...100
    result = gen.generate(data, width=11)
    assert result[0] == '▁'  # Min
    assert result[-1] == '█'  # Max
```

### Integration Tests
```python
async def test_dashboard_sparklines_update():
    dashboard = DopemuxDashboard()
    trends = dashboard.query_one(TrendsPanel)

    # Trigger update
    await trends.update_sparklines()

    # Verify sparklines rendered
    assert 'cognitive' in trends.sparklines
    assert len(trends.sparklines['cognitive']) == 24
    assert trends.sparklines['cognitive'] != '─' * 24
```

### Manual Testing Checklist
- [ ] Start dashboard with Prometheus running
- [ ] Verify sparklines appear
- [ ] Wait 30s, verify auto-refresh
- [ ] Stop Prometheus, verify graceful fallback
- [ ] Restart Prometheus, verify recovery
- [ ] Monitor CPU/memory for 5 minutes
- [ ] Check colors match trend direction
- [ ] Verify readability in different terminal themes

---

## 📈 PROMETHEUS QUERIES REFERENCE

### ADHD Engine Metrics
```promql
# Cognitive Load (0-100)
adhd_cognitive_load{load_category="optimal"}

# Task Velocity (tasks/day)
adhd_task_velocity_per_day

# Context Switches (count)
adhd_context_switches_total

# Flow Duration (seconds)
adhd_flow_duration_seconds

# Break Adherence (0-1)
adhd_break_adherence_rate

# Energy Level (enum: high, medium, low, depleted)
adhd_energy_level{level="medium"}
```

### Time Range Examples
```promql
# Last 2 hours, 5-minute resolution
query_range?query=adhd_cognitive_load&start=-2h&end=now&step=5m

# Last 7 days, 1-hour resolution
query_range?query=adhd_task_velocity_per_day&start=-7d&end=now&step=1h

# Last 24 hours, 15-minute resolution
query_range?query=adhd_context_switches_total&start=-24h&end=now&step=15m
```

---

## 🚀 QUICK START COMMANDS

### Run Prometheus (if not running)
```bash
docker start dopemux-prometheus
# or
docker run -d -p 9090:9090 prom/prometheus
```

### Check Prometheus Health
```bash
curl http://localhost:9090/api/v1/status/config | jq '.status'
```

### Test Query
```bash
curl 'http://localhost:9090/api/v1/query_range?query=adhd_cognitive_load&start=2025-10-29T00:00:00Z&end=2025-10-29T02:00:00Z&step=5m' | jq '.data.result[0].values'
```

### Run Dashboard
```bash
cd /Users/hue/code/dopemux-mvp
python3 dopemux_dashboard.py
```

---

## 🎓 RESEARCH REFERENCES

### Academic Papers
1. **"Sparklines: Theory and Practice"** - Edward Tufte, 2006
- Information density in minimal space
- Word-sized graphics principles

1. **"Color Psychology in HCI"** - Singh, 2006
- Color improves recall by 55-78%
- Consistency crucial for pattern recognition

1. **"Visualization for ADHD Users"** - CHADD Research, 2018
- High contrast reduces cognitive load
- Progressive disclosure prevents overwhelm

### Production Systems Analyzed
1. **btop** - Excellent real-time sparklines
1. **k9s** - Color-coded resource trends
1. **lazygit** - Clean historical visualization
1. **htop** - Classic bar chart approach

### Best Practices Extracted
- Keep it simple (< 3 colors per sparkline)
- Update frequently but smoothly (30s interval)
- Show context (last value + trend)
- Handle errors gracefully (show "—" not crash)

---

## 💡 KEY INSIGHTS

### What Makes Good Sparklines
1. **Consistent scale** - Same metric = same visual range
1. **Recent emphasis** - Right side is "now"
1. **Smooth rendering** - Interpolate gaps
1. **Color meaning** - Green/Yellow/Red = Good/Neutral/Bad
1. **Fast updates** - < 100ms render time

### ADHD-Specific Optimizations
1. **High contrast** - Easy to distinguish at a glance
1. **Predictable layout** - Same position every time
1. **Clear trends** - Direction obvious without thinking
1. **No surprises** - Smooth transitions, no jumps
1. **Actionable** - See problem → take action

### Technical Learnings
1. **Prometheus query_range** - More efficient than multiple queries
1. **Unicode blocks** - Better than ASCII for smoothness
1. **Async updates** - Don't block UI on slow API
1. **Caching** - Store last N values for trend calculation
1. **Interpolation** - Linear works fine for most metrics

---

## 📋 NEXT STEPS (After Day 2)

### Day 3: Interactive Navigation
- Keyboard shortcuts (1-4 to focus panels)
- Tab/Shift+Tab navigation
- Enter to expand panel
- Escape to collapse

### Day 4: Drill-Down Views
- Press 'd' on cognitive load → detailed history
- Press 't' on tasks → task list popup
- Press 'l' on service → log viewer

### Week 2: Advanced Features
- Real-time WebSocket streaming
- Custom time range selection
- Export to CSV
- Alert thresholds

---

## ✅ CHECKLIST

### Before Starting
- [ ] Read this entire document
- [ ] Confirm Prometheus is running
- [ ] Check current dashboard works
- [ ] Review existing code structure
- [ ] Estimate 5 hours for Day 2

### During Implementation
- [ ] Follow TDD (test first)
- [ ] Commit after each phase
- [ ] Test on real data
- [ ] Monitor performance
- [ ] Document decisions

### Before Completing
- [ ] All acceptance criteria met
- [ ] Performance benchmarks passed
- [ ] Edge cases handled
- [ ] Code reviewed
- [ ] Documentation updated

---

**Status:** 📖 Ready for Implementation
**Confidence:** HIGH
**Risk Level:** LOW (well-researched, clear path)

**Let's build beautiful sparklines! 🎨📊**
