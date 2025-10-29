# Tmux Dashboard Implementation Sprint Plan

**Sprint Duration:** 2 weeks
**Start Date:** 2025-10-28
**End Date:** 2025-11-11
**Sprint Goal:** Advanced features - sparklines, interactivity, drill-downs

---

## 📋 SPRINT OVERVIEW

### What We're Building
1. Enhanced sparklines with real historical data
2. Interactive keyboard navigation between panels
3. Data drill-down popup views
4. Real-time WebSocket streaming (optional)
5. Advanced panel layouts with presets

### Why Now
- Core dashboard is complete and working
- Users need richer visualizations
- Keyboard navigation is critical for power users
- Drill-down enables self-service debugging

### Success Criteria
- [ ] All sparklines show real Prometheus data
- [ ] Can navigate entire dashboard with keyboard only
- [ ] At least 3 drill-down views working
- [ ] Performance still < 100ms, < 5% CPU
- [ ] Zero crashes in 1-hour stress test

---

## 🗓️ WEEK 1: VISUALIZATION & NAVIGATION

### Day 1-2: Enhanced Sparklines (Mon-Tue)
**Goal:** Replace placeholder sparklines with real historical data

**Tasks:**
```python
# 1. Create SparklineGenerator class
class SparklineGenerator:
    def __init__(self, prometheus_url: str):
        self.prom = PrometheusClient(prometheus_url)
    
    def generate(self, metric: str, hours: int = 24, width: int = 20) -> str:
        """Generate sparkline from time-series data"""
        data = self.prom.query_range(metric, hours)
        return self._render_sparkline(data, width)

# 2. Fetch historical data from Prometheus
async def fetch_cognitive_load_history(hours: int = 24) -> List[float]:
    query = 'adhd_cognitive_load{load_category="optimal"}'
    result = await prom.query_range(query, f"{hours}h")
    return [float(v) for _, v in result]

# 3. Add to TrendsPanel widget
class TrendsPanel(Static):
    async def update_sparklines(self):
        generator = SparklineGenerator("http://localhost:9090")
        
        self.cognitive_sparkline = generator.generate(
            "adhd_cognitive_load", hours=2
        )
        self.velocity_sparkline = generator.generate(
            "adhd_task_velocity_per_day", hours=168  # 7 days
        )
```

**Acceptance Criteria:**
- [ ] Cognitive load sparkline shows last 2 hours
- [ ] Task velocity shows last 7 days
- [ ] Context switches show last 24 hours
- [ ] Auto-updates every 30 seconds
- [ ] Handles missing data gracefully

---

### Day 3-4: Interactive Keyboard Navigation (Wed-Thu)
**Goal:** Full keyboard control of dashboard

**Tasks:**
```python
# 1. Add panel focusing
class DopemuxDashboard(App):
    focused_panel = reactive("adhd")
    
    BINDINGS = [
        ("1", "focus_panel('adhd')", "ADHD State"),
        ("2", "focus_panel('productivity')", "Productivity"),
        ("3", "focus_panel('services')", "Services"),
        ("4", "focus_panel('trends')", "Trends"),
        ("tab", "next_panel", "Next Panel"),
        ("shift+tab", "prev_panel", "Previous Panel"),
        ("enter", "expand_panel", "Expand"),
        ("escape", "collapse_panel", "Collapse"),
    ]
    
    def action_focus_panel(self, panel_id: str):
        """Focus specific panel"""
        self.focused_panel = panel_id
        panel = self.query_one(f"#{panel_id}")
        panel.add_class("focused")
    
    def action_next_panel(self):
        """Focus next panel"""
        panels = ["adhd", "productivity", "services", "trends"]
        idx = panels.index(self.focused_panel)
        next_idx = (idx + 1) % len(panels)
        self.action_focus_panel(panels[next_idx])

# 2. Add visual focus indicator
# In CSS:
.focused {
    border: thick $accent;
    background: $surface-lighten-1;
}

# 3. Add scroll support
class ServicesWidget(Static):
    can_focus = True
    
    def on_key(self, event: events.Key) -> None:
        if event.key == "up":
            self.scroll_up()
        elif event.key == "down":
            self.scroll_down()
```

**Acceptance Criteria:**
- [ ] Number keys (1-4) focus panels
- [ ] Tab/Shift+Tab cycles through panels
- [ ] Arrow keys scroll within focused panel
- [ ] Visual indicator shows focused panel
- [ ] Enter expands focused panel

---

### Day 5: Data Drill-Down Views (Fri)
**Goal:** Popup detail views for deeper inspection

**Tasks:**
```python
# 1. Create TaskDetailScreen
class TaskDetailScreen(Screen):
    """Detailed task view"""
    
    def __init__(self, task_data: Dict):
        super().__init__()
        self.task_data = task_data
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Panel(self._render_task_info(), title="Task Details"),
            Panel(self._render_complexity(), title="Complexity Analysis"),
            Panel(self._render_history(), title="History"),
        )
        yield Footer()
    
    def _render_task_info(self) -> Table:
        table = Table()
        table.add_row("Name", self.task_data["name"])
        table.add_row("Status", self.task_data["status"])
        table.add_row("Complexity", f"{self.task_data['complexity']:.2f}")
        return table

# 2. Add binding to open popup
class ProductivityPanel(Static):
    BINDINGS = [("d", "show_detail", "Detail View")]
    
    def action_show_detail(self):
        """Show task detail popup"""
        task_data = self.get_selected_task()
        self.app.push_screen(TaskDetailScreen(task_data))

# 3. Create ServiceLogsScreen
class ServiceLogsScreen(Screen):
    """Service logs viewer"""
    
    async def on_mount(self):
        logs = await fetch_service_logs(self.service_name, lines=100)
        self.query_one(LogView).update(logs)
```

**Acceptance Criteria:**
- [ ] Press 'd' on task panel for detail view
- [ ] Press 'l' on service panel for logs
- [ ] Press 'p' on patterns for pattern analysis
- [ ] Escape key closes popups
- [ ] Popups are scrollable

---

## 🗓️ WEEK 2: STREAMING & LAYOUTS

### Day 6-7: Real-Time Streaming (Mon-Tue)
**Goal:** WebSocket updates for instant metrics (optional based on time)

**Tasks:**
```python
# 1. Add WebSocket endpoint to ADHD Engine
# In services/adhd_engine/api/routes.py
@router.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            state = await get_current_state()
            await websocket.send_json(state)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass

# 2. Create WebSocket client in dashboard
class RealtimeMetrics:
    async def subscribe(self, metric: str):
        async with websockets.connect(
            f"ws://localhost:8001/ws/metrics"
        ) as ws:
            async for message in ws:
                yield json.loads(message)

# 3. Update widgets in real-time
class ADHDStateWidget(Static):
    async def on_mount(self):
        # Start WebSocket subscription
        self.run_worker(self.stream_updates())
    
    async def stream_updates(self):
        metrics = RealtimeMetrics()
        async for data in metrics.subscribe("adhd_state"):
            self.energy = data["energy_level"]
            self.attention = data["attention_state"]
            self.refresh()
```

**Acceptance Criteria:**
- [ ] ADHD state updates instantly (< 1s lag)
- [ ] Sparklines animate smoothly
- [ ] Reconnects on connection loss
- [ ] Fallback to polling if WebSocket unavailable

---

### Day 8-9: Advanced Layouts (Wed-Thu)
**Goal:** Layout presets and customization

**Tasks:**
```python
# 1. Define layout presets
LAYOUTS = {
    "compact": {
        "adhd": {"height": 5},
        "productivity": {"height": 4},
        "services": {"height": 6},
        "trends": {"height": 4},
    },
    "standard": {
        "adhd": {"height": 7},
        "productivity": {"height": 6},
        "services": {"height": 8},
        "trends": {"height": 6},
    },
    "detailed": {
        "adhd": {"height": 10},
        "productivity": {"height": 8},
        "services": {"height": 12},
        "trends": {"height": 10},
    },
}

# 2. Add layout switcher
class DopemuxDashboard(App):
    current_layout = reactive("standard")
    
    BINDINGS = [
        ("alt+1", "set_layout('compact')", "Compact"),
        ("alt+2", "set_layout('standard')", "Standard"),
        ("alt+3", "set_layout('detailed')", "Detailed"),
    ]
    
    def action_set_layout(self, layout: str):
        self.current_layout = layout
        self.apply_layout(LAYOUTS[layout])

# 3. Save/load preferences
def save_preferences():
    config = {
        "layout": app.current_layout,
        "theme": app.current_theme,
        "focused_panel": app.focused_panel,
    }
    Path("~/.dopemux/dashboard.json").write_text(
        json.dumps(config)
    )
```

**Acceptance Criteria:**
- [ ] Alt+1/2/3 switch layouts
- [ ] Layout persists across restarts
- [ ] Smooth transition animations
- [ ] All panels resize correctly

---

### Day 10: Testing & Polish (Fri)
**Goal:** Ensure quality and performance

**Tasks:**
```bash
# 1. Performance profiling
python -m cProfile -o dashboard.prof dopemux_dashboard.py
python -m pstats dashboard.prof

# 2. Memory leak testing
while true; do
    ps aux | grep dopemux_dashboard
    sleep 60
done

# 3. Stress testing
# Run dashboard for 1 hour with varying loads
timeout 3600 python dopemux_dashboard.py

# 4. User testing
# Get 3+ people to try it and collect feedback

# 5. Documentation
# Update README with new features
# Record demo video
# Add screenshots
```

**Acceptance Criteria:**
- [ ] No memory leaks over 1 hour
- [ ] CPU < 5% average
- [ ] All features work on fresh install
- [ ] Documentation updated
- [ ] Demo video recorded

---

## 📊 DAILY STANDUP FORMAT

### Questions to Answer:
1. What did I complete yesterday?
2. What am I working on today?
3. Any blockers?

### Track in DASHBOARD_IMPLEMENTATION_TRACKER.md:
```markdown
## Daily Log

### 2025-10-28 (Mon)
- [x] Set up sparkline generator class
- [x] Connected to Prometheus
- [ ] Implemented cognitive load sparkline (blocked: need Prometheus data)
- Next: Fix Prometheus query, test with real data

### 2025-10-29 (Tue)
- [x] Fixed Prometheus query
- [x] All sparklines working
- [x] Added auto-update every 30s
- Next: Start keyboard navigation

### 2025-10-30 (Wed)
...
```

---

## 🚀 QUICK REFERENCE

### Run Dashboard
```bash
python dopemux_dashboard.py
```

### Test Specific Feature
```bash
# Test sparklines only
python -c "from dopemux_dashboard import SparklineGenerator; ..."

# Test keyboard nav
python dopemux_dashboard.py --test-navigation
```

### Commit Messages
```bash
git commit -m "feat(sparklines): add historical data from Prometheus"
git commit -m "feat(navigation): keyboard panel focusing"
git commit -m "feat(popups): task detail drill-down view"
git commit -m "perf: optimize sparkline generation"
git commit -m "fix: handle missing Prometheus data"
```

---

## 🎯 DONE DEFINITION

A feature is DONE when:
- [ ] Code is written and tested
- [ ] Performance < 100ms, < 5% CPU
- [ ] Works on fresh install
- [ ] Documentation updated
- [ ] Committed with clear message
- [ ] No regressions in existing features

---

**Let's ship it! ��**
