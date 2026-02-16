---
id: TMUX_DASHBOARD_DESIGN
title: Tmux_Dashboard_Design
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Tmux_Dashboard_Design (reference) for dopemux documentation and developer
  workflows.
---
# Tmux Dashboard Design - Dopemux Metrics Display

**Comprehensive design for maximum information density with ADHD-optimized presentation**

Generated: 2025-10-28
Research-backed design combining best practices from btop, k9s, lazygit, and dashboard design psychology

---

## 🎯 EXECUTIVE SUMMARY

Based on extensive research and analysis of your metrics inventory, here's the optimal approach:

**Framework:** Python + Rich/Textual (primary) + tmux native status bar (secondary)
**Layout:** Multi-pane dashboard with progressive disclosure
**Update Strategy:** Tiered refresh rates (1s/5s/30s/60s)
**Visual Style:** High-density grid with color-coded sparklines and gauges
**Interaction:** Keyboard-driven navigation with tmux popups for drill-down

---

## 📊 RECOMMENDED ARCHITECTURE

### Three-Tier Display System

```
┌─────────────────────────────────────────────────────────────────┐
│ TIER 1: tmux status bar (always visible)                        │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2: Dedicated pane (Textual dashboard - toggleable)         │
├─────────────────────────────────────────────────────────────────┤
│ TIER 3: tmux popups (detailed views - on-demand)                │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Approach?

1. **tmux status bar** - Zero CPU when not focused, always visible, perfect for critical state
2. **Textual dashboard pane** - Rich visuals, real-time updates, ADHD-optimized layout
3. **tmux popups** - Drill-down without losing context, keyboard-driven

---

## 🎨 TIER 1: TMUX STATUS BAR DESIGN

### Layout (fits in standard terminal width)

```bash
# Left side (session context)
[dopemux-mvp:main 📊] 2h15m ⚡= 👁️● 🧠65%

# Right side (critical metrics)
Flow:🌊 ☕15m | 8/10(80%) | 128K/200K(64%) Sonnet
```

### Component Breakdown

**Left Status (`status-left`):**
```bash
#[fg=cyan,bold]#{pane_current_path}#[default]:#[fg=green]#{pane_current_command} \
#(curl -s localhost:8005/api/adhd/connection/status | jq -r '.icon') \
#(curl -s localhost:8001/api/v1/state | jq -r '.session_time') \
#(curl -s localhost:8001/api/v1/state | jq -r '.energy_icon + .energy_state') \
#(curl -s localhost:8001/api/v1/state | jq -r '.attention_icon + .attention_state') \
#(curl -s localhost:8001/api/v1/state | jq -r '"🧠" + (.cognitive_load * 100 | floor | tostring) + "%"')
```

**Right Status (`status-right`):**
```bash
#(curl -s localhost:8001/api/v1/flow | jq -r 'if .in_flow then "Flow:🌊" else "" end') \
#(curl -s localhost:8001/api/v1/breaks | jq -r 'if .warning then "☕" + .time_until else "" end') | \
#(curl -s localhost:8001/api/v1/tasks | jq -r '.completed + "/" + .total + "(" + (.rate * 100 | floor | tostring) + "%)"') | \
#(curl -s localhost:9090/api/v1/query?query=claude_token_usage | jq -r '.tokens + "/" + .limit + "(" + (.pct | floor | tostring) + "%)")' \
#(curl -s localhost:9090/api/v1/query?query=claude_model | jq -r '.model')
```

### Color Scheme

```bash
# In .tmux.conf
set -g status-style 'bg=#1e1e2e fg=#cdd6f4'  # Catppuccin Mocha base

# Critical thresholds
if-shell '[ $COGNITIVE_LOAD -gt 85 ]' 'set -g status-style bg=#f38ba8'  # Red
if-shell '[ $COGNITIVE_LOAD -gt 70 ]' 'set -g status-style bg=#f9e2af'  # Yellow
if-shell '[ $ENERGY_LEVEL == "depleted" ]' 'set -g status-style bg=#f38ba8'  # Red
```

### Performance Optimization

```bash
# Cache status data in tmpfs
CACHE_DIR="/dev/shm/dopemux-status"
CACHE_TTL=5  # seconds

# Status script with caching
#!/bin/bash
cache_file="$CACHE_DIR/adhd_state"
if [[ -f "$cache_file" ]] && [[ $(($(date +%s) - $(stat -f %m "$cache_file"))) -lt $CACHE_TTL ]]; then
    cat "$cache_file"
else
    curl -s localhost:8001/api/v1/state | tee "$cache_file"
fi
```

---

## 🎨 TIER 2: TEXTUAL DASHBOARD DESIGN

### Full-Screen Layout (Textual App)

```
╔══════════════════════════════════════════════════════════════════╗
║  ADHD STATE (Tier 1 - Critical)                        [2h 15m] ║
╠══════════════════════════════════════════════════════════════════╣
║ Energy: ⚡= Medium │ Attention: 👁️● Focused │ Cognitive: [||||····] 65%  ║
║ Flow: 🌊 Active 23m │ Break: ☕ in 15m │ Switches: 4 today         ║
╠══════════════════════════════════════════════════════════════════╣
║  PRODUCTIVITY (Tier 2 - High Value)                             ║
╠══════════════════════════════════════════════════════════════════╣
║ Tasks: 8/10 (80%) ████████░░ │ Decisions: 23 (↑5 today)         ║
║ Velocity: ▃▄▅▅▆▇▆▅▄ 7.2/day │ Completion Rate: 85% (target)    ║
╠══════════════════════════════════════════════════════════════════╣
║  SERVICES (Tier 2)                                              ║
╠═══════════╦══════════════╦═══════════╦══════════════╦═══════════╣
║ ConPort   ║ ADHD Engine  ║ Serena    ║ MCP Bridge   ║ Redis     ║
║ 📊 15ms   ║ ✓ 8ms        ║ ✓ 120ms   ║ ✓ 45 calls   ║ 94% hit   ║
║ 23 dec    ║ Load: 0.65   ║ 12 boosts ║ 0 errors     ║ 2.1MB     ║
╠═══════════╩══════════════╩═══════════╩══════════════╩═══════════╣
║  PATTERNS & INSIGHTS (Tier 2)                                   ║
╠══════════════════════════════════════════════════════════════════╣
║ Top Patterns: git_status(12) context_switch(8) high_complexity(5)║
║ Abandoned: 3 stale, 1 likely, 0 definite                        ║
║ Break Adherence: 4/5 taken (80%) - Good job! 🎉                 ║
╠══════════════════════════════════════════════════════════════════╣
║  TRENDS (Tier 3 - sparklines)                                   ║
╠══════════════════════════════════════════════════════════════════╣
║ Cognitive Load:  ▁▂▃▅▆▇█▇▆▅▃▂▁ (last 2h)                        ║
║ Task Velocity:   ▃▄▅▅▆▇▆▅▄▃▂▁ (last 7d)                         ║
║ Context Switches: ▂▁▂▃▅▃▂▁▂▁▁▁ (last 24h)                       ║
╠══════════════════════════════════════════════════════════════════╣
║  HOTKEYS: [t]asks [s]ervices [p]atterns [d]etail [q]uit         ║
╚══════════════════════════════════════════════════════════════════╝
```

### Textual Implementation

```python
# scripts/dopemux_dashboard.py
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

    def compose(self) -> ComposeResult:
        yield Static(id="adhd-state")

    async def on_mount(self) -> None:
        self.set_interval(1.0, self.update_state)

    async def update_state(self) -> None:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8001/api/v1/state")
            data = resp.json()

            self.energy = data["energy_level"]
            self.attention = data["attention_state"]
            self.cognitive_load = data["cognitive_load"]
            self.in_flow = data["flow_state"]["active"]
            self.break_in = data["break_warning"]["minutes_until"]

    def render(self) -> Panel:
        # Create rich panel with current state
        energy_icon = {"high": "⚡↑", "medium": "⚡=", "low": "⚡↓"}[self.energy]
        attention_icon = {"focused": "👁️●", "scattered": "👁️🌀"}[self.attention]
        load_bar = self._make_gauge(self.cognitive_load)
        flow_status = "🌊 Active" if self.in_flow else ""
        break_warning = f"☕ in {self.break_in}m" if self.break_in < 20 else ""

        table = Table.grid(padding=1)
        table.add_column(style="bold cyan")
        table.add_column(style="bold magenta")
        table.add_column(style="bold yellow")

        table.add_row(
            f"{energy_icon} {self.energy.title()}",
            f"{attention_icon} {self.attention.title()}",
            f"🧠 {load_bar} {int(self.cognitive_load * 100)}%"
        )
        table.add_row(flow_status, break_warning, "")

        return Panel(table, title="ADHD STATE", border_style="green")

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
            tasks_resp = await client.get("http://localhost:8001/api/v1/tasks")
            decisions_resp = await client.get("http://localhost:8005/api/adhd/decisions/recent")

            tasks_data = tasks_resp.json()
            decisions_data = decisions_resp.json()

            self.tasks_completed = tasks_data["completed"]
            self.tasks_total = tasks_data["total"]
            self.decisions_today = len(decisions_data["today"])

    def render(self) -> Panel:
        completion_rate = self.tasks_completed / self.tasks_total
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
                    data = resp.json()

                    status = "✓" if data["status"] == "healthy" else "✗"
                    latency = f"{data['latency_ms']}ms"
                    metrics = data.get("metrics", "")

                    table.add_row(name, status, latency, metrics)
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
            normalized = [int((v / max(data)) * 7) for v in data]
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
    Screen {
        background: $surface;
    }

    #adhd-state {
        height: 6;
        border: solid green;
    }

    #productivity {
        height: 6;
        border: solid blue;
    }

    #services {
        height: 8;
        border: solid cyan;
    }

    #trends {
        height: 6;
        border: solid yellow;
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
        subprocess.run([
            "tmux", "display-popup",
            "-E", "-w", "80%", "-h", "80%",
            "python", "dashboard_detail.py"
        ])

if __name__ == "__main__":
    app = DopemuxDashboard()
    app.run()
```

---

## 🎨 TIER 3: TMUX POPUP DETAILS

### Detail Views (On-Demand)

```bash
# Bind keys in .tmux.conf
bind-key M-d display-popup -E -w 80% -h 80% "python ~/.dopemux/dashboard_detail.py"
bind-key M-t display-popup -E -w 60% -h 40% "python ~/.dopemux/tasks_detail.py"
bind-key M-s display-popup -E -w 60% -h 40% "python ~/.dopemux/services_detail.py"
```

### Example: Task Detail Popup

```python
# tasks_detail.py
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import httpx

console = Console()

async def show_tasks():
    async with httpx.AsyncClient() as client:
        resp = await client.get("http://localhost:8001/api/v1/tasks/detailed")
        tasks = resp.json()

    table = Table(title="Task Details", show_header=True, header_style="bold magenta")
    table.add_column("Task", style="cyan", width=40)
    table.add_column("Status", justify="center")
    table.add_column("Complexity", justify="right")
    table.add_column("Duration", justify="right")

    for task in tasks:
        status_icon = "✓" if task["completed"] else "⧗"
        complexity_bar = "█" * int(task["complexity"] * 5)

        table.add_row(
            task["name"][:40],
            status_icon,
            complexity_bar,
            task["duration"]
        )

    console.print(Panel(table, border_style="green"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(show_tasks())
```

---

## 🎨 COLOR PSYCHOLOGY & ADHD OPTIMIZATION

### Color Scheme (Catppuccin Mocha)

```python
COLORS = {
    # Base colors
    "base": "#1e1e2e",
    "surface": "#313244",
    "text": "#cdd6f4",
    "subtext": "#bac2de",

    # Semantic colors (ADHD-optimized)
    "success": "#a6e3a1",    # Green - completed, optimal
    "warning": "#f9e2af",    # Yellow - approaching threshold
    "error": "#f38ba8",      # Red - critical, take action
    "info": "#89b4fa",       # Blue - neutral info

    # Cognitive load gradient
    "load_low": "#89dceb",    # Cyan - underutilized
    "load_optimal": "#a6e3a1", # Green - sweet spot (0.6-0.7)
    "load_high": "#f9e2af",   # Yellow - getting heavy
    "load_critical": "#f38ba8", # Red - overwhelm

    # Energy states
    "energy_high": "#f5c2e7",  # Pink - hyperfocus
    "energy_medium": "#89b4fa", # Blue - baseline
    "energy_low": "#fab387",   # Peach - depleting

    # Attention states
    "attention_focused": "#a6e3a1",    # Green - on task
    "attention_scattered": "#f9e2af",  # Yellow - fragmenting
    "attention_overwhelmed": "#f38ba8", # Red - overload
}
```

### Visual Hierarchy Rules

1. **Size**: Critical > High Value > Detail
   - Critical metrics: Bold, larger font
   - High value: Normal font
   - Detail: Smaller, dimmed

2. **Color**: Actionable > Informational > Background
   - Red: TAKE ACTION NOW
   - Yellow: ATTENTION NEEDED SOON
   - Green: ALL GOOD / COMPLETED
   - Blue: INFORMATIONAL
   - Gray: DISABLED / INACTIVE

3. **Position**: Top-left > Top-right > Bottom
   - Top-left: Primary focus (ADHD state)
   - Top-right: Secondary context (time, model)
   - Center: Working data
   - Bottom: References, hotkeys

4. **Animation**: None for critical, subtle for updates
   - No blinking or flashing (ADHD trigger)
   - Smooth color transitions (0.3s fade)
   - Sparklines for trends (not live-updating)

---

## 🎨 PROGRESSIVE DISCLOSURE DESIGN

### 3-Level Information Architecture

```
Level 1 (Always Visible - Status Bar)
├─ Energy state
├─ Attention state
├─ Cognitive load
├─ Break warning
├─ Flow state
└─ Token usage

Level 2 (Toggleable - Dashboard Pane)
├─ Level 1 (expanded)
├─ Task metrics
├─ Service health
├─ Pattern insights
└─ Trends (sparklines)

Level 3 (On-Demand - Popups)
├─ Detailed task list
├─ Service logs
├─ Pattern analysis
├─ Historical graphs
└─ Configuration
```

### Interaction Flow

```
User working → Glance at status bar (1s)
              ├─ All good? → Keep working
              └─ Issue? → Check dashboard (5s)
                          ├─ Understand? → Adjust behavior
                          └─ Need more? → Open popup (detailed analysis)
```

### Cognitive Load Limits

- **Status bar**: Max 8 items (Miller's Law: 7±2)
- **Dashboard**: Max 5 sections visible at once
- **Each section**: Max 3-5 data points
- **Popups**: Unlimited (user chose to drill down)

---

## ⚡ PERFORMANCE OPTIMIZATION

### Update Frequencies (Based on Metric Type)

```python
UPDATE_INTERVALS = {
    # Real-time (1 second)
    "energy_level": 1,
    "attention_state": 1,
    "cognitive_load": 1,
    "flow_state": 1,

    # Fast (5 seconds)
    "break_timer": 5,
    "session_time": 5,
    "token_usage": 5,

    # Medium (30 seconds)
    "tasks": 30,
    "decisions": 30,
    "context_switches": 30,
    "cache_stats": 30,

    # Slow (60 seconds)
    "patterns": 60,
    "trends": 60,
    "service_health": 60,
    "database_stats": 60,
}
```

### Caching Strategy

```python
# Multi-tier cache
class MetricsCache:
    def __init__(self):
        self.memory = {}  # In-memory (instant)
        self.redis = redis.Redis()  # Shared cache (fast)
        self.tmpfs = Path("/dev/shm/dopemux")  # Disk cache (backup)

    async def get(self, key: str, fetcher: callable, ttl: int):
        # Check memory cache
        if key in self.memory and not self._is_stale(key, ttl):
            return self.memory[key]

        # Check Redis
        cached = await self.redis.get(f"metrics:{key}")
        if cached:
            self.memory[key] = json.loads(cached)
            return self.memory[key]

        # Fetch fresh data
        data = await fetcher()

        # Store in all caches
        self.memory[key] = data
        await self.redis.setex(f"metrics:{key}", ttl, json.dumps(data))

        return data
```

### Resource Limits

```python
# Prevent dashboard from affecting work
RESOURCE_LIMITS = {
    "max_cpu_percent": 5,     # Max 5% CPU usage
    "max_memory_mb": 100,      # Max 100MB RAM
    "max_update_time_ms": 100, # Updates must complete in 100ms
}

# Throttle updates if system under load
async def adaptive_update_rate():
    system_load = psutil.cpu_percent()

    if system_load > 80:
        return 60  # Update every 60s when busy
    elif system_load > 50:
        return 30  # Every 30s when medium
    else:
        return 5   # Every 5s when idle
```

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Foundation (Week 1)
- [ ] Set up tmux status bar with basic metrics
- [ ] Create API endpoints for all metrics
- [ ] Implement caching layer
- [ ] Test performance (must be <100ms, <5% CPU)

### Phase 2: Textual Dashboard (Week 2)
- [ ] Build ADHD state panel
- [ ] Build productivity panel
- [ ] Build services grid
- [ ] Add sparkline trends
- [ ] Implement keyboard navigation

### Phase 3: Popups & Detail Views (Week 3)
- [ ] Create task detail popup
- [ ] Create service logs popup
- [ ] Create pattern analysis popup
- [ ] Add configuration UI

### Phase 4: Polish & Optimization (Week 4)
- [ ] Fine-tune color scheme
- [ ] Optimize update frequencies
- [ ] Add accessibility features
- [ ] User testing with ADHD users
- [ ] Documentation

---

## 📦 DEPENDENCIES

```bash
# Python packages
pip install \
    textual \          # TUI framework
    rich \             # Terminal formatting
    httpx \            # Async HTTP client
    redis \            # Caching
    prometheus-client \ # Metrics scraping
    psutil             # System monitoring

# System packages
brew install tmux jq curl
```

---

## 📚 REFERENCES

### Research Sources
- Dashboard Design Patterns (arXiv.org)
- ADHD-Friendly UI Design (UXPin, Baeldung)
- Terminal Dashboard Best Practices (awesome-tmux, btop)
- Color Psychology in Dashboards (Devfinity)

### Inspirations
- **btop**: High-density system monitoring
- **k9s**: Kubernetes dashboard (clean info hierarchy)
- **lazygit**: Intuitive TUI navigation
- **Grafana**: Visualization patterns

### Code Examples
- Textual Documentation: https://textual.textualize.io
- Rich Examples: https://github.com/Textualize/rich
- tmux-powerline: https://github.com/erikw/tmux-powerline

---

## 🎯 SUCCESS METRICS

### Quantitative
- [ ] Status bar update latency < 100ms
- [ ] Dashboard CPU usage < 5%
- [ ] Dashboard memory < 100MB
- [ ] All metrics accessible within 3 clicks/keystrokes

### Qualitative (ADHD User Testing)
- [ ] "I can glance and know my state instantly" (visibility)
- [ ] "It doesn't distract me from work" (non-intrusive)
- [ ] "I actually use it to take breaks" (actionable)
- [ ] "The colors make sense intuitively" (clarity)
- [ ] "I don't feel overwhelmed" (information density)

---

**Next Step:** Start with Phase 1 (tmux status bar) - it's the highest ROI with lowest risk!
