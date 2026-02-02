---
id: DASHBOARD_DAY4_DEEP_RESEARCH
title: Dashboard_Day4_Deep_Research
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Dashboard Day 4: Data Drill-Downs & Modal Views - Deep Research Plan 🔍

**Created:** 2025-10-29
**Phase:** Advanced Features - Interactive Drill-Down System
**Estimated Time:** 6-8 hours
**Status:** 🎯 Ready to implement

---

## 🎯 MISSION

Transform dashboard from **information display** to **interactive investigation tool** with contextual drill-downs, modal popups, and deep data exploration.

**Vision:** Press a key → see complete context → make informed decisions → close and return

---

## 📚 RESEARCH: DRILL-DOWN UI PATTERNS

### 1. Modal/Popup Design Patterns

#### Best-in-Class Examples

**k9s (Kubernetes):**
```
Flow: View pod list → Press 'l' → Modal with logs → Press 'Esc' to close
- Full-screen takeover with border
- Clear title and keybindings shown
- Scrollable content
- Easy exit (Esc or q)
```

**lazydocker:**
```
Flow: See container → Press Enter → Detailed stats modal
- Tabbed interface (Stats | Logs | Config)
- Real-time updates in modal
- Filter/search within modal
- Breadcrumb navigation
```

**htop:**
```
Flow: Select process → Press 'F9' → Action menu modal
- Compact centered popup
- List of actions with shortcuts
- Instant feedback
- No confirmation for safe actions
```

#### ADHD-Optimized Modal Design Principles

1. **Instant Context Recognition**
   - Clear title: "Task #42 Details" not just "Details"
   - Visual distinction from main view (different border/color)
   - Show breadcrumb: "ADHD Panel → Task Details"

2. **Progressive Disclosure**
   - Most important info at top
   - Collapsible sections for deep details
   - Visual hierarchy (color-coded sections)

3. **Zero Friction Exit**
   - Multiple exit keys: Esc, q, Ctrl+C
   - Always show "[Esc] Close" in footer
   - Auto-close on selection (if appropriate)

4. **Maintain Context**
   - Don't lose place in parent view
   - Show "preview" without full drill-down (optional)
   - Breadcrumb trail for nested drills

---

## 🎨 DESIGN: DRILL-DOWN ARCHITECTURE

### Modal System Components

```python
class ModalView(Screen):
    """Base class for all drill-down modals"""

    CSS = """
    ModalView {
        align: center middle;
    }

    #modal-container {
        width: 80%;
        height: 80%;
        background: $surface0;
        border: thick $blue;
        border-title-align: center;
    }

    #modal-content {
        height: 1fr;
        overflow-y: auto;
    }

    #modal-footer {
        dock: bottom;
        height: 3;
        background: $surface1;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Quit"),
        ("?", "help", "Help"),
    ]

    def action_dismiss(self):
        """Close modal and return to main view"""
        self.app.pop_screen()
```

### Specific Drill-Down Views

#### 1. Task Detail View (`TaskDetailModal`)

**Trigger:** Press `Enter` on task in Productivity panel

**Data Sources:**
- `/api/adhd/tasks/{task_id}` - Task details
- `/api/adhd/task-history/{task_id}` - Status changes
- `/api/context/patterns` - Related patterns
- Prometheus: `adhd_task_duration`, `adhd_context_switches`

**Layout:**
```
╭─────────────────── Task #42: "Implement drill-downs" ───────────────────────╮
│                                                                              │
│ 📊 OVERVIEW                                                                  │
│ Status: in_progress  Priority: high  Created: 2h ago  Due: Today 5pm        │
│ Tags: [coding] [deep-work] [backend]                                        │
│                                                                              │
│ 🎯 CONTEXT                                                                   │
│ Parent: Feature #12 "Interactive Dashboard"                                 │
│ Blocked by: None                                                             │
│ Blocking: Task #43, Task #44                                                 │
│                                                                              │
│ 📈 METRICS                                                                   │
│ Time worked: 1h 23m  Estimated: 3h  Remaining: ~1h 37m                      │
│ Focus sessions: 2  Context switches: 4 (low)                                │
│ Cognitive load: ▃▄▅▆▅▄▃ (trend: decreasing ✓)                               │
│                                                                              │
│ 🧠 ADHD INSIGHTS                                                             │
│ • Currently in optimal flow (energy: high, focus: stable)                   │
│ • Good momentum - avoid breaks until natural stopping point                 │
│ • Similar tasks completed 30% faster in afternoon                           │
│                                                                              │
│ 📝 HISTORY                                                                   │
│ 14:32  Status changed: todo → in_progress                                   │
│ 14:35  Note added: "Starting with modal base class"                         │
│ 15:12  Context switch detected (Slack notification)                         │
│ 15:14  Resumed focus                                                         │
│                                                                              │
│ ⚡ ACTIONS                                                                   │
│ [c] Complete task  [b] Block task  [p] Change priority                      │
│ [n] Add note      [t] Add time    [d] Delete task                           │
│                                                                              │
╰────────────────────────── [Esc] Close  [?] Help ────────────────────────────╯
```

**Implementation:**
```python
class TaskDetailModal(ModalView):
    """Detailed view of a single task"""

    def __init__(self, task_id: int):
        super().__init__()
        self.task_id = task_id

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static(id="modal-header")
            with Vertical(id="modal-content"):
                yield Static(id="overview-section")
                yield Static(id="context-section")
                yield Static(id="metrics-section")
                yield Static(id="insights-section")
                yield Static(id="history-section")
            yield Static(id="modal-footer")

    async def on_mount(self):
        """Fetch task data and render"""
        task_data = await self.fetch_task_details()
        self.render_task(task_data)

    async def fetch_task_details(self) -> Dict:
        """Fetch all task-related data"""
        async with httpx.AsyncClient() as client:
            # Fetch from multiple sources in parallel
            task, history, metrics, insights = await asyncio.gather(
                client.get(f"http://localhost:8006/api/adhd/tasks/{self.task_id}"),
                client.get(f"http://localhost:8006/api/adhd/task-history/{self.task_id}"),
                client.get(f"http://localhost:9090/api/v1/query?query=adhd_task_duration{{task_id=\"{self.task_id}\"}}"),
                client.get(f"http://localhost:8006/api/adhd/insights?task_id={self.task_id}")
            )

            return {
                "task": task.json(),
                "history": history.json(),
                "metrics": metrics.json(),
                "insights": insights.json()
            }

    BINDINGS = [
        *ModalView.BINDINGS,
        ("c", "complete_task", "Complete"),
        ("b", "block_task", "Block"),
        ("p", "change_priority", "Priority"),
        ("n", "add_note", "Note"),
    ]

    def action_complete_task(self):
        """Mark task as complete and close modal"""
        # Call API to update task
        # Show brief confirmation
        # Close modal
        pass
```

#### 2. Service Logs Viewer (`ServiceLogsModal`)

**Trigger:** Press `l` on service in Services panel

**Data Sources:**
- `/api/services/{service_name}/logs?lines=100&tail=true`
- `/api/services/{service_name}/status`
- `/api/services/{service_name}/health`

**Features:**
- Live-updating log tail
- Color-coded by log level (ERROR=red, WARN=yellow, INFO=blue)
- Scroll through history
- Filter by log level
- Search functionality
- Export logs

**Layout:**
```
╭───────────────────── Serena Service Logs (live) ────────────────────────────╮
│ Status: ✓ Running  Uptime: 2h 34m  Requests/s: 45  Errors/s: 0.1           │
│                                                                              │
│ [Filtering: ALL ▾] [Search: ____] [Auto-scroll: ON]                         │
│ ────────────────────────────────────────────────────────────────────────────│
│ 16:15:23 INFO  Starting session intelligence update                         │
│ 16:15:23 DEBUG Fetching patterns from database                              │
│ 16:15:24 INFO  Found 23 active patterns                                     │
│ 16:15:24 WARN  Pattern #15 has low confidence (0.45)                        │
│ 16:15:25 INFO  Session analysis complete (127ms)                            │
│ 16:15:30 ERROR Failed to connect to Redis: Connection timeout               │
│ 16:15:30 WARN  Retrying Redis connection (attempt 1/3)                      │
│ 16:15:31 INFO  Redis connection restored                                    │
│ 16:15:35 INFO  Cognitive load recalculated: 0.65 (medium)                   │
│ ...                                                                          │
│                                                                              │
│ ────────────────────────────────────────────────────────────────────────────│
│ [f] Filter  [/] Search  [↑↓] Scroll  [s] Toggle auto-scroll  [e] Export    │
╰──────────────────────── [Esc] Close  [?] Help ──────────────────────────────╯
```

**Implementation:**
```python
class ServiceLogsModal(ModalView):
    """Live log viewer for services"""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.auto_scroll = True
        self.filter_level = "ALL"
        self.log_buffer = []

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static(id="log-header")
            yield Static(id="log-controls")
            yield Static(id="log-separator")
            with Container(id="log-content", classes="scrollable"):
                yield DataTable(id="log-table")
            yield Static(id="log-footer")

    async def on_mount(self):
        """Start log streaming"""
        # Fetch initial logs
        logs = await self.fetch_logs(lines=100)
        self.render_logs(logs)

        # Start live tail in background
        asyncio.create_task(self.stream_logs())

    async def stream_logs(self):
        """Stream logs in real-time"""
        # WebSocket or polling approach
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"http://localhost:8006/api/services/{self.service_name}/logs",
                        params={"since": self.last_timestamp, "tail": True}
                    )
                    new_logs = response.json()

                    if new_logs:
                        self.append_logs(new_logs)
                        if self.auto_scroll:
                            self.scroll_to_bottom()

                    await asyncio.sleep(1)  # Poll every second
                except Exception as e:
                    logger.error(f"Log stream error: {e}")
                    await asyncio.sleep(5)

    BINDINGS = [
        *ModalView.BINDINGS,
        ("f", "toggle_filter", "Filter"),
        ("/", "search", "Search"),
        ("s", "toggle_autoscroll", "Auto-scroll"),
        ("e", "export_logs", "Export"),
    ]
```

#### 3. Pattern Detail View (`PatternDetailModal`)

**Trigger:** Press `p` on pattern in ADHD State panel

**Data Sources:**
- `/api/context/patterns/{pattern_id}`
- `/api/context/pattern-occurrences/{pattern_id}`
- `/api/adhd/recommendations?pattern_id={pattern_id}`

**Layout:**
```
╭──────────────── Pattern #7: "Deep Work Morning Block" ──────────────────────╮
│                                                                              │
│ 📊 PATTERN STATISTICS                                                        │
│ Occurrences: 47  Success rate: 89%  Avg duration: 2h 15m                    │
│ Last seen: Today 9am  Confidence: 0.92 (very high)                          │
│ Tags: [morning] [deep-work] [productive]                                    │
│                                                                              │
│ 🎯 PATTERN DEFINITION                                                        │
│ Triggers:                                                                    │
│   • Time: 8:00-10:00 AM                                                      │
│   • Energy level: High                                                       │
│   • No meetings scheduled                                                    │
│   • Coffee consumed in last 30 min                                           │
│                                                                              │
│ Typical behavior:                                                            │
│   • 2-3 hour focused coding session                                          │
│   • Minimal context switches (avg: 2)                                        │
│   • High task completion rate                                                │
│   • Break taken around 10:15 AM                                              │
│                                                                              │
│ 📈 TREND ANALYSIS                                                            │
│ Occurrence by day: Mon ████ Tue ███ Wed █████ Thu ██ Fri ███                │
│ Success rate over time: ▅▆▇▇██▇▆ (improving)                                │
│                                                                              │
│ 🧠 RECOMMENDATIONS                                                           │
│ ✓ Schedule complex tasks during this window                                 │
│ ✓ Block calendar from 8-10 AM daily                                         │
│ ✓ Prepare task list night before                                            │
│ ✗ Avoid meetings or calls in this slot                                      │
│                                                                              │
│ 🔄 RECENT OCCURRENCES                                                        │
│ Today 9:00    ✓ Completed  Duration: 2h 12m  Tasks: 3/3                     │
│ Yesterday     ✓ Completed  Duration: 1h 54m  Tasks: 2/3                     │
│ 2 days ago    ✗ Interrupted  Duration: 45m  (Meeting conflict)              │
│ 3 days ago    ✓ Completed  Duration: 2h 31m  Tasks: 4/4                     │
│                                                                              │
╰────────────────────────── [Esc] Close  [?] Help ────────────────────────────╯
```

#### 4. Metric History Viewer (`MetricHistoryModal`)

**Trigger:** Press `h` on any sparkline

**Shows:** Full historical graph with zoom, annotations, and analysis

**Layout:**
```
╭─────────────── Cognitive Load History (Last 7 Days) ────────────────────────╮
│                                                                              │
│ [Zoom: 7d ▾] [Granularity: 1h ▾]                                            │
│                                                                              │
│ 1.0 │                    ╭──╮                                                │
│     │          ╭────╮   ╭╯  ╰╮     ╭╮                                        │
│ 0.8 │     ╭───╯    ╰──╯      ╰───╯ ╰╮    Current: 0.65                      │
│     │    ╭╯                           ╰╮                                     │
│ 0.6 │───╯─────────────────────────────╰──────────                           │
│     │                                                                        │
│ 0.4 │                                         Avg: 0.71                      │
│     │                                                                        │
│ 0.2 │                                         Min: 0.42                      │
│     │                                         Max: 0.95                      │
│ 0.0 │─────┬─────┬─────┬─────┬─────┬─────┬─────                              │
│     Mon   Tue   Wed   Thu   Fri   Sat   Sun                                 │
│                                                                              │
│ 📊 ANNOTATIONS                                                               │
│ Wed 2pm: Peak load (0.95) - Meeting marathon                                │
│ Thu 9am: Optimal zone (0.65) - Deep work session                            │
│ Fri 4pm: Low load (0.42) - End of week fatigue                              │
│                                                                              │
│ 🎯 INSIGHTS                                                                  │
│ • Best performance: Tue-Thu mornings (8-11 AM)                              │
│ • Decline pattern: Friday afternoons                                        │
│ • Suggestion: Schedule deep work Tue/Wed/Thu AM                             │
│                                                                              │
╰───────── [z] Zoom  [←→] Pan  [a] Add note  [e] Export ──────────────────────╯
```

---

## 🏗️ IMPLEMENTATION PLAN

### Phase 1: Modal Infrastructure (2 hours)

**Step 1:** Create base `ModalView` class
```python
# File: dopemux_dashboard.py (add class)

class ModalView(Screen):
    """Base class for all drill-down modals"""

    CSS = """
    ModalView {
        align: center middle;
    }

    #modal-container {
        width: 80%;
        height: 80%;
        background: $surface0;
        border: thick $blue;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Quit"),
    ]

    def action_dismiss(self):
        self.app.pop_screen()
```

**Step 2:** Test modal system with simple example
```python
class TestModal(ModalView):
    """Simple test modal"""

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static("Test Modal - Press Esc to close")

# In main app, add keybinding to test
BINDINGS = [
    ...
    ("t", "test_modal", "Test Modal"),
]

def action_test_modal(self):
    self.push_screen(TestModal())
```

**Acceptance Criteria:**
- [ ] Modal centers on screen
- [ ] Clear visual distinction from main view
- [ ] Esc closes modal and returns to main view
- [ ] No flickering or layout issues

### Phase 2: Task Detail Modal (2 hours)

**Step 1:** Implement `TaskDetailModal` structure
```python
class TaskDetailModal(ModalView):
    def __init__(self, task_id: int):
        super().__init__()
        self.task_id = task_id

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static(f"Task #{self.task_id} Details", id="header")
            yield Static("Loading...", id="content")
```

**Step 2:** Add data fetching
```python
async def on_mount(self):
    task_data = await self.fetch_task_details()
    self.render_task_content(task_data)

async def fetch_task_details(self):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8006/api/adhd/tasks/{self.task_id}"
        )
        return response.json()
```

**Step 3:** Wire up from main dashboard
```python
# In ProductivityPanel
BINDINGS = [
    ("enter", "show_task_detail", "Task Details"),
]

def action_show_task_detail(self):
    # Get currently selected/focused task ID
    task_id = self.get_selected_task_id()
    if task_id:
        self.app.push_screen(TaskDetailModal(task_id))
```

**Acceptance Criteria:**
- [ ] Pressing Enter on task opens modal
- [ ] Shows all task metadata
- [ ] Displays metrics and history
- [ ] ADHD insights section populated
- [ ] Can close and return to task list

### Phase 3: Service Logs Modal (2-3 hours)

**Step 1:** Basic log viewer structure
```python
class ServiceLogsModal(ModalView):
    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Static(id="log-header")
            yield DataTable(id="log-table")
            yield Static(id="log-footer")
```

**Step 2:** Add log fetching and rendering
```python
async def on_mount(self):
    logs = await self.fetch_logs(lines=100)
    self.render_logs(logs)

def render_logs(self, logs):
    table = self.query_one("#log-table", DataTable)
    table.add_columns("Time", "Level", "Message")

    for log in logs:
        # Color-code by level
        level_style = self.get_level_style(log['level'])
        table.add_row(
            log['timestamp'],
            Text(log['level'], style=level_style),
            log['message']
        )
```

**Step 3:** Add live streaming (optional for v1)
```python
async def stream_logs(self):
    """Poll for new logs every second"""
    while not self.is_closed:
        new_logs = await self.fetch_logs(since=self.last_timestamp)
        if new_logs:
            self.append_logs(new_logs)
        await asyncio.sleep(1)
```

**Acceptance Criteria:**
- [ ] Shows last 100 log lines
- [ ] Color-coded by log level
- [ ] Scrollable content
- [ ] Performance: < 100ms to open
- [ ] (Optional) Live updates every second

### Phase 4: Pattern & Metric Modals (1-2 hours)

**Step 1:** Create `PatternDetailModal`
- Similar structure to TaskDetailModal
- Fetch pattern stats and occurrences
- Show recommendations and trends

**Step 2:** Create `MetricHistoryModal`
- Fetch time-series data from Prometheus
- Render larger graph with annotations
- Add zoom/pan controls (optional for v1)

**Acceptance Criteria:**
- [ ] Pattern modal shows full pattern definition
- [ ] Metric modal shows full historical graph
- [ ] Both have clear, actionable insights

---

## 🧪 TESTING STRATEGY

### Manual Testing Checklist

**Modal System:**
- [ ] All modals open without errors
- [ ] All modals close with Esc, q, Ctrl+C
- [ ] No memory leaks (check after opening/closing 20+ times)
- [ ] Works in different terminal sizes

**Task Detail Modal:**
- [ ] Opens from task list
- [ ] Shows all sections (overview, context, metrics, insights, history)
- [ ] Data loads within 500ms
- [ ] Actions work (mark complete, etc.)
- [ ] Handles missing data gracefully

**Service Logs Modal:**
- [ ] Opens from service list
- [ ] Shows logs with correct colors
- [ ] Scrolling works smoothly
- [ ] Filter works
- [ ] Live updates work (if implemented)

**Performance:**
- [ ] Opening modal: < 200ms
- [ ] Data fetch: < 500ms
- [ ] No UI freezing while fetching
- [ ] Memory usage stable

### Integration Testing

```python
# Test modal navigation flow
async def test_drill_down_flow():
    """Test complete drill-down workflow"""
    app = DopemuxDashboard()

    # Start app
    async with app.run_test() as pilot:
        # Navigate to task
        await pilot.press("2")  # Focus productivity panel
        await pilot.press("down", "down")  # Select task

        # Open modal
        await pilot.press("enter")

        # Verify modal is open
        assert app.screen is TaskDetailModal

        # Close modal
        await pilot.press("escape")

        # Verify back on main view
        assert app.screen is DopemuxDashboard
```

---

## 📈 SUCCESS METRICS

### Functional Goals
- [ ] 4+ drill-down views implemented
- [ ] All modals < 200ms to open
- [ ] Zero crashes in 30-minute test session
- [ ] Works in 80x24 terminal minimum

### UX Goals
- [ ] Clear visual hierarchy in modals
- [ ] Intuitive keyboard shortcuts
- [ ] Helpful error messages
- [ ] Breadcrumb navigation

### Performance Goals
- [ ] Modal render: < 100ms
- [ ] Data fetch: < 500ms
- [ ] Memory: < 50MB total
- [ ] No UI blocking

---

## 🚀 DEPLOYMENT CHECKLIST

Before marking Day 4 complete:

- [ ] All 4 modal types implemented
- [ ] Integration with main dashboard complete
- [ ] Keyboard shortcuts documented
- [ ] Error handling for network failures
- [ ] Graceful degradation if services unavailable
- [ ] User testing with 3+ scenarios
- [ ] Performance profiling completed
- [ ] Documentation updated

---

## 📚 REFERENCE LINKS

**Textual Docs:**
- [Screens & Modals](https://textual.textualize.io/guide/screens/)
- [DataTable Widget](https://textual.textualize.io/widgets/data_table/)
- [Bindings](https://textual.textualize.io/guide/actions/)

**Design Inspiration:**
- k9s: https://github.com/derailed/k9s
- lazydocker: https://github.com/jesseduffield/lazydocker
- htop: https://github.com/htop-dev/htop

**API Endpoints to Use:**
- `GET /api/adhd/tasks/{id}` - Task details
- `GET /api/services/{name}/logs` - Service logs
- `GET /api/context/patterns/{id}` - Pattern details
- `GET /api/v1/query_range` - Prometheus metrics

---

## 🎯 NEXT STEPS (Day 5)

After completing drill-downs:
1. **Advanced Layouts:** Grid system with custom panel sizing
2. **Real-time Streaming:** WebSocket integration for instant updates
3. **Export Functions:** CSV/JSON export of metrics and logs
4. **Keyboard Help:** Press `?` for full command reference
5. **Theme Switcher:** Multiple color schemes

---

**Ready to implement! Let's build an interactive command center! 🚀**
