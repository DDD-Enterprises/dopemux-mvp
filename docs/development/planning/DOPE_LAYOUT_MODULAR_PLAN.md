# Dope Layout v2: Modular PM + Implementation Design

**Date**: 2025-10-28
**Status**: Planning Complete (Zen Analysis with Very High Confidence)
**Scope**: New `--layout dope` with dynamic mode switching, Textual + Rich hybrid, ADHD-optimized transient messages

---

## Executive Summary

Create `--layout dope` with **dynamic mode switching** between PM and Implementation contexts using **Textual + Rich hybrid** architecture. Features gorgeous interactive PM mode with epic/task hierarchy, ADHD-optimized transient messages, and Serena untracked work integration.

**Key Innovation**: Single layout that adapts monitor pane content via hotkey toggle between PM planning and implementation coding contexts.

---

## Visual Layout Comparison

### Implementation Mode (Default - Code Focus)
```
+------------------ monitor:adhd ------------------+-- monitor:system -------+
| Energy: MED  Session: 23m  Health: 95/100       | Docker: 12/12 running   |
| Focus: PEAK  Switches: 3/15m                    | MCP: 8/8 healthy        |
|                                                  | LiteLLM: $0.23/hr 1.2s  |
| UNTRACKED WORK DETECTED:                         | Logs: [streaming...]    |
| - 24 files in task-orchestrator/ (4d old)       |                         |
| - No matching task found                         |                         |
| [P] Plan work  [C] Commit  [D] Dismiss          |                         |
+------------------------- orchestrator -----------+---- sandbox ------------+
| Happy orchestrator instance                      | Quick experiments       |
+--------------------------------- agent:primary -----------------------------+
| Specialized agent (cc/codex/copilot)                                       |
+-------------------------------- metrics:bar --------------------------------+
| MED 23m | 3sw | 24* | 2uw | 2! | 85% | $0.23 | 8/8 | 12/12                |
+----------------------------------------------------------------------------+

Press [M] to toggle to PM mode
```

### PM Mode (Planning Focus)
```
+-------------- monitor:pm-hierarchy --------------+-- monitor:task-detail --+
| Q1 2025 Sprint (65% complete)                   | Code monitor panes      |
| +- Epic: Dope Layout [65%]                      | Status: IN PROGRESS     |
| |  +- [DONE] Design metrics bar (2h)            | Assigned: Me            |
| |  +- [ACTIVE] Code panes (4h, 2.5h spent)      | Estimated: 4h           |
| |  +- [TODO] Integration testing (2h)           | Spent: 2.5h (63%)      |
| +- Epic: ADHD Engine v2 [30%]                   | Started: 2h ago         |
| |  +- [ACTIVE] Context switch detection (8h)    |                         |
| +- Epic: Serena Integration [10%]               | Sprint Progress:        |
|    +- [TODO] Untracked work UI (6h)             | - 65% complete          |
|                                                  | - 2 overdue tasks       |
| [Arrow keys to navigate] [Enter for details]    | - Today's focus: THIS   |
+------------------------- orchestrator -----------+---- sandbox ------------+
| Happy orchestrator instance                      | Quick experiments       |
+--------------------------------- agent:primary -----------------------------+
| Specialized agent (cc/codex/copilot)                                       |
+-------------------------------- metrics:bar --------------------------------+
| Sprint 65% | Today: Code panes | Overdue 2 | Active 3 | Est 40h | Spent 26h |
+----------------------------------------------------------------------------+

Press [M] to toggle to Implementation mode
```

---

## Architecture: Textual + Rich Hybrid

### Why Textual?
1. **Interactive PM mode**: Tree widget for epic/task hierarchy with arrow key navigation
2. **Keyboard handling**: M=mode toggle, P=plan, C=commit, D=dismiss, arrows, Enter
3. **Modal overlays**: Transient ADHD messages with priority system (critical/warning/info)
4. **Embeds Rich**: Can use Rich renderables for gorgeous metrics/panels in Textual containers

### Why Not Pure Rich?
- Rich is display-only (no keyboard input handling, no interactive widgets)
- Cannot build navigable tree widget or modal dialogs
- Perfect for metrics bar and static displays, insufficient for PM mode

### Hybrid Approach Benefits
- **Textual app**: Main event loop, keyboard bindings, modals, interactive Tree widget
- **Rich components**: Embedded in Textual for metrics bar and static panel displays
- **Best of both worlds**: Textual's interactivity + Rich's beautiful rendering

---

## Modular File Structure

```
scripts/neon_dashboard/
├── core/
│   ├── __init__.py
│   ├── app.py                    # Main Textual app (400 lines)
│   │                             # - Event loop and keyboard bindings
│   │                             # - Mode toggle logic (M key)
│   │                             # - Pane rendering coordination
│   ├── pane_manager.py           # Dynamic pane swapping (200 lines)
│   │                             # - State machine for PM/Implementation
│   │                             # - Pane lifecycle management
│   └── state.py                  # Global state (150 lines)
│                                 # - Current mode, active task, message queue
│
├── collectors/
│   ├── __init__.py
│   ├── base_collector.py         # Abstract base (150 lines)
│   │                             # - Async HTTP with 2s timeout
│   │                             # - Graceful fallback on error
│   │                             # - TTL caching per data source
│   ├── pm_collector.py           # PM data sources (300 lines)
│   │                             # - Leantime epics/tasks/sprints
│   │                             # - ConPort progress tracking
│   │                             # - Sprint metadata
│   └── impl_collector.py         # Implementation data (350 lines)
│                                 # - ADHD Engine state
│                                 # - Serena untracked work detection
│                                 # - Activity Capture context switches
│                                 # - Git, Docker, MCP, LiteLLM health
│
├── panes/
│   ├── __init__.py
│   ├── pm_hierarchy.py           # Textual Tree widget (350 lines)
│   │                             # - Epic/task/subtask hierarchy
│   │                             # - Arrow key navigation
│   │                             # - Status icons (DONE/ACTIVE/TODO/BLOCKED)
│   ├── task_detail.py            # Task details panel (200 lines)
│   │                             # - Selected task info
│   │                             # - Time tracking, estimates
│   │                             # - Description, files, actions
│   ├── adhd_monitor.py           # ADHD + untracked work (400 lines)
│   │                             # - Energy, session, health, focus
│   │                             # - Serena untracked work display
│   │                             # - Context switch warnings
│   └── system_monitor.py         # Infrastructure health (250 lines)
│                                 # - Docker, MCP, LiteLLM status
│                                 # - Log streaming
│
├── components/
│   ├── __init__.py
│   ├── metrics_bar.py            # Rich Text metrics (300 lines)
│   │                             # - Context-aware content
│   │                             # - Implementation: energy, switches, etc
│   │                             # - PM: sprint progress, tasks, time
│   └── transient_messages.py     # Modal overlays (400 lines)
│                                 # - Priority queue system
│                                 # - Critical/warning/info levels
│                                 # - Serena integration
│                                 # - Activity Capture integration
│                                 # - Task drift detection
│
└── config/
    ├── __init__.py
    └── settings.py               # User preferences (150 lines)
                                  # - Enable/disable message categories
                                  # - Thresholds (untracked age, breaks)
                                  # - Default mode (PM vs Implementation)

Total: ~2,300 lines
```

---

## Transient Message System

### Priority Levels

**CRITICAL** (red border, blocks work until dismissed):
- Untracked work > 7 days old
- Task drift detected (working on files unrelated to active task)
- Must respond to continue working

**WARNING** (yellow border, dismissible):
- Untracked work 1-7 days old
- Context switch detected (changed files/directories)
- Can dismiss with 'D' key

**INFO** (blue border, auto-dismiss after 10 seconds):
- Break reminders (after 25m, 45m, 90m sessions)
- Progress updates (task completion, sprint milestones)
- Fades automatically

### Example Overlay: Untracked Work

```
+-------------------------------------------------------+
|  CRITICAL: UNTRACKED WORK DETECTED                    |
|                                                       |
|  24 uncommitted files in task-orchestrator/           |
|  Age: 4 days                                          |
|  Confidence: 0.8 (HIGH - from Serena detection)       |
|  No matching task found in Leantime or ConPort        |
|                                                       |
|  [P] Plan this work  [C] Commit now  [D] Dismiss      |
+-------------------------------------------------------+
```

### Example Overlay: Context Switch

```
+-------------------------------------------------------+
|  WARNING: CONTEXT SWITCH DETECTED                     |
|                                                       |
|  You switched from 'Dope Layout' to 'Serena Integ'   |
|  Last activity on Dope Layout: 23 minutes ago         |
|  New files touched: services/serena/                  |
|                                                       |
|  [U] Update active task  [K] Keep current  [D] Dismiss|
+-------------------------------------------------------+
```

### Example Overlay: Task Drift

```
+-------------------------------------------------------+
|  CRITICAL: TASK DRIFT DETECTED                        |
|                                                       |
|  Active task: "Frontend UI improvements"              |
|  Working on: task-orchestrator/ (backend)             |
|                                                       |
|  Files modified:                                      |
|  - services/task-orchestrator/intelligence/           |
|  - services/task-orchestrator/observability/          |
|                                                       |
|  [S] Switch task  [R] Related work  [D] Dismiss       |
+-------------------------------------------------------+
```

---

## Integration with Serena Untracked Work Detection

### Detection Flow

```
1. Serena runs detection (localhost:3010/detect-untracked)
   Detects: 24 uncommitted files, 4 days old, no matching task

2. impl_collector.py fetches detection every 15 seconds
   Returns: {files: 24, age_days: 4, confidence: 0.8, task_match: null}

3. transient_messages.py evaluates priority:
   Age 4 days = WARNING priority (yellow border, dismissible)
   If age was >7 days = CRITICAL (red, blocks)

4. Modal overlay appears over current panes

5. User presses 'P' (plan this work):
   a. Layout switches to PM mode
   b. Task creation dialog opens
   c. Pre-fills from Serena analysis:
      - Title: "Untracked work in task-orchestrator/"
      - Description: "24 files modified 4 days ago"
      - Epic: (user selects)
      - Estimate: (user provides)
      - Files: [list of uncommitted files]

6. User fills remaining fields, saves task

7. Task created in both Leantime and ConPort

8. Transient message dismissed

9. User can stay in PM mode or toggle back to Implementation
```

---

## Dynamic Pane Manager

### State Machine

```python
class PaneManager:
    """Manages dynamic pane swapping between PM and Implementation modes"""

    def __init__(self):
        self.mode = 'implementation'  # Current mode
        self.left_pane = None          # Left monitor pane
        self.right_pane = None         # Right monitor pane
        self.metrics_bar = None        # Bottom metrics bar
        self.transient_queue = PriorityQueue()  # Message queue

    def toggle_mode(self):
        """Press 'M' to switch contexts"""
        if self.mode == 'implementation':
            # Switch to PM mode
            self.mode = 'pm'
            self.left_pane = PMHierarchyPane()    # Textual Tree widget
            self.right_pane = TaskDetailPane()     # Textual Panel
            self.metrics_bar.set_mode('pm')        # Update metrics content
        else:
            # Switch to Implementation mode
            self.mode = 'implementation'
            self.left_pane = ADHDMonitorPane()     # Rich embedded in Textual
            self.right_pane = SystemMonitorPane()  # Rich embedded in Textual
            self.metrics_bar.set_mode('implementation')

        self.render_all()

    def show_transient(self, message):
        """Display modal overlay, hijack focus until dismissed"""
        self.transient_queue.put(message)
        modal = TransientModal(message)
        self.app.push_screen(modal)  # Textual modal system
```

### Hotkey Bindings

**Global (both modes):**
- `M` - Toggle between PM and Implementation mode
- `?` - Show help overlay with all hotkeys
- `Q` - Quit (with confirmation)

**Implementation Mode:**
- `P` - Plan untracked work (if Serena detected any)
- `C` - Quick commit (if uncommitted files exist)
- `D` - Dismiss current transient message

**PM Mode:**
- `↑↓` Arrow keys - Navigate epic/task tree
- `←→` Arrow keys - Expand/collapse tree nodes
- `Enter` - Select task for details in right pane
- `N` - Create new task
- `E` - Edit selected task
- `Space` - Toggle task status (TODO → IN_PROGRESS → DONE)
- `Del` - Delete selected task (with confirmation)

---

## PM Mode: Epic/Task Hierarchy

### Textual Tree Widget Implementation

```python
# pm_hierarchy.py
from textual.widgets import Tree
from textual.app import ComposeResult

class PMHierarchyPane(Container):
    """Left pane in PM mode - epic/task tree"""

    def compose(self) -> ComposeResult:
        yield Tree("Q1 2025 Sprint", id="pm-tree")

    def build_tree(self, epics):
        """Build Textual Tree from Leantime data"""
        tree = self.query_one("#pm-tree", Tree)
        tree.clear()

        for epic in epics:
            # Epic node with completion percentage
            epic_node = tree.root.add(
                f"[cyan]Epic: {epic['name']}[/cyan] [{epic['completion']}%]",
                data=epic
            )

            for task in epic['tasks']:
                # Task node with status icon
                status_icon = self.get_status_icon(task['status'])
                task_node = epic_node.add(
                    f"{status_icon} {task['name']} ({task['estimate']}h)",
                    data=task
                )

                # Subtasks (3-level limit)
                for subtask in task.get('subtasks', []):
                    subtask_icon = self.get_status_icon(subtask['status'])
                    task_node.add(
                        f"{subtask_icon} {subtask['name']}",
                        data=subtask
                    )

        tree.root.expand()

    def get_status_icon(self, status):
        """Visual status indicators"""
        return {
            'DONE': '[green]✓[/green]',
            'IN_PROGRESS': '[yellow]▶[/yellow]',
            'TODO': '[dim]○[/dim]',
            'BLOCKED': '[red]✗[/red]',
        }[status]

    def on_tree_node_selected(self, event):
        """When user selects task, update detail pane"""
        selected_data = event.node.data
        self.app.update_task_detail(selected_data)
```

### Task Detail Pane

```
When user selects task in tree, right pane shows:

+---------------------- Task Details ------------------------+
| Code monitor panes                                         |
| Status: IN PROGRESS                                        |
| Assigned: Me                                               |
| Epic: Dope Layout                                          |
|                                                            |
| Time Tracking:                                             |
| Estimated: 4h                                              |
| Spent: 2.5h (63% of estimate)                             |
| Remaining: 1.5h                                            |
| Started: 2 hours ago                                       |
|                                                            |
| Description:                                               |
| Implement Rich-based monitor panes for ADHD and system    |
| health monitoring. Integrate with data collection layer   |
| and ensure graceful degradation on service timeouts.      |
|                                                            |
| Files Touched (from git tracking):                         |
| - scripts/neon_dashboard/adhd_monitor.py                   |
| - scripts/neon_dashboard/system_monitor.py                 |
| - scripts/neon_dashboard/collectors/impl_collector.py      |
|                                                            |
| Actions:                                                   |
| [E] Edit  [C] Change status  [A] Add time  [N] Add note   |
+------------------------------------------------------------+
```

---

## Metrics Bar: Context-Aware Content

### Implementation Mode Metrics
```
Energy: MED 23m | Switches: 3 | Uncommitted: 24 | Untracked: 2 | Overdue: 2 | Progress: 85% | Cost: $0.23 | MCP: 8/8 | Docker: 12/12
```

**Data Sources:**
- ADHD Engine: Energy level, session time
- Activity Capture: Context switches
- Git: Uncommitted file count
- Serena: Untracked work count
- Leantime: Overdue task count
- ConPort: Progress percentage
- LiteLLM: Cost per hour
- MCP: Server health count
- Docker: Container health count

### PM Mode Metrics
```
Sprint: 65% | Today: Code panes | Overdue: 2 | Active: 3 | Blocked: 0 | Completed: 8 | Est: 40h | Spent: 26h | Remaining: 14h
```

**Data Sources:**
- Leantime: Sprint progress, today's focus task, overdue/active/blocked/completed counts
- ConPort: Time estimates and spent time tracking

### Responsive Width Handling

**Terminal Width >= 160 chars:** Show all metrics
**Terminal Width 120-159 chars:** Hide Docker and MCP (least critical)
**Terminal Width < 120 chars:** Hide Docker, MCP, and expand abbreviations

---

## Data Collectors

### PM Collector (pm_collector.py)

```python
class PMCollector(BaseCollector):
    """Collects project management data from Leantime and ConPort"""

    async def fetch_leantime_epics(self):
        """Fetch epic/task hierarchy from Leantime API"""
        url = "http://localhost:3007/epics"
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    return await resp.json()
        except (asyncio.TimeoutError, aiohttp.ClientError):
            return {'epics': [], 'error': 'Leantime offline'}

    async def fetch_sprint_metadata(self):
        """Current sprint progress, dates, goals"""
        url = "http://localhost:3007/sprint/current"
        # ... similar timeout/fallback pattern

    async def fetch_conport_progress(self):
        """Task completion rates from ConPort"""
        url = "http://localhost:3009/progress/summary"
        # ... similar timeout/fallback pattern

    async def fetch_all(self):
        """Fetch all PM data concurrently"""
        results = await asyncio.gather(
            self.fetch_leantime_epics(),
            self.fetch_sprint_metadata(),
            self.fetch_conport_progress(),
            return_exceptions=True
        )
        return {
            'epics': results[0],
            'sprint': results[1],
            'progress': results[2],
        }
```

### Implementation Collector (impl_collector.py)

```python
class ImplCollector(BaseCollector):
    """Collects ADHD monitoring and system health data"""

    async def fetch_adhd_engine(self):
        """Energy, session, health, focus state"""
        url = "http://localhost:3008/adhd-state"
        # ... with 2s timeout and fallback

    async def fetch_serena_untracked(self):
        """Untracked work detection from Serena"""
        url = "http://localhost:3010/detect-untracked"
        # Returns: {file_count, age_days, confidence, files_list}

    async def fetch_activity_capture(self):
        """Context switches from desktop monitoring"""
        url = "http://localhost:3006/recent"
        # Returns: {switches_15m, screenshot_active}

    async def fetch_git_status(self):
        """Git status via CLI"""
        proc = await asyncio.create_subprocess_exec(
            'git', 'status', '--porcelain',
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return {'uncommitted': len(stdout.decode().strip().split('\n'))}

    async def fetch_docker_status(self):
        """Docker Compose container health"""
        proc = await asyncio.create_subprocess_exec(
            'docker-compose', 'ps', '--format', 'json',
            stdout=asyncio.subprocess.PIPE
        )
        # ... parse and count healthy containers

    # Similar methods for MCP, LiteLLM

    async def fetch_all(self):
        """Fetch all implementation data concurrently"""
        results = await asyncio.gather(
            self.fetch_adhd_engine(),
            self.fetch_serena_untracked(),
            self.fetch_activity_capture(),
            self.fetch_git_status(),
            self.fetch_docker_status(),
            self.fetch_mcp_health(),
            self.fetch_litellm_health(),
            return_exceptions=True
        )
        return {
            'adhd': results[0],
            'serena': results[1],
            'activity': results[2],
            'git': results[3],
            'docker': results[4],
            'mcp': results[5],
            'litellm': results[6],
        }
```

---

## CLI Integration

### Modify src/dopemux/tmux/cli.py

Add new layout function:

```python
def _setup_dope_layout(controller, session, base_pane, start_dir, config, dual_agent):
    """
    Dope layout with dynamic pane swapping.

    Structure:
    - Top band (35%): 2 monitor panes (split 60/40)
    - Middle band (45%): orchestrator (70%) + sandbox (30%)
    - Agent band (15%): agent:primary (+ optional secondary)
    - Metrics bar (5%): 1-2 line status bar
    """

    # Split base pane into 3 horizontal bands + metrics bar
    agent_band = controller.backend.split_window(
        target=base_pane.pane_id, percent=15, vertical=True
    )

    middle_band = controller.backend.split_window(
        target=base_pane.pane_id, percent=45, vertical=True
    )

    top_band = base_pane.pane_id  # Remaining 35% + 5% metrics

    # Split top band: monitors (35%) + metrics bar (5%)
    metrics_bar_id = controller.backend.split_window(
        target=top_band, percent=12, vertical=True  # 5/40 = 12.5%
    )

    monitors_id = top_band

    # Split monitors into left (60%) and right (40%)
    right_monitor_id = controller.backend.split_window(
        target=monitors_id, percent=40, vertical=False
    )
    left_monitor_id = monitors_id

    # Split middle band: orchestrator (70%) + sandbox (30%)
    sandbox_id = controller.backend.split_window(
        target=middle_band, percent=30, vertical=False
    )
    orchestrator_id = middle_band

    # Agent pane (with optional secondary agent)
    agent_primary_id = agent_band
    agent_secondary_id = None
    if dual_agent:
        agent_secondary_id = controller.backend.split_window(
            target=agent_primary_id, percent=50, vertical=False
        )

    # Set pane titles and colors per NEON_THEME
    pane_titles = [
        (left_monitor_id, "monitor:adhd"),       # or monitor:pm-hierarchy
        (right_monitor_id, "monitor:system"),    # or monitor:task-detail
        (orchestrator_id, "orchestrator:control"),
        (sandbox_id, "sandbox:shell"),
        (agent_primary_id, "agent:primary"),
        (metrics_bar_id, "metrics:bar"),
    ]

    if agent_secondary_id:
        pane_titles.append((agent_secondary_id, "agent:secondary"))

    # Apply theme colors
    for pane_id, title in pane_titles:
        tmux_utils.set_pane_title(pane_id, title)
        style = NEON_THEME["pane"].get(title, NEON_THEME["pane"]["default"])
        tmux_utils.set_pane_style(pane_id, style)

    # Auto-start Textual app in monitor panes
    # This single app manages both panes and handles mode toggling
    monitor_cmd = "python3 scripts/neon_dashboard/core/app.py"
    controller.send_keys(left_monitor_id, monitor_cmd, enter=True)

    # Metrics bar auto-start
    metrics_cmd = "python3 scripts/neon_dashboard/components/metrics_bar.py"
    controller.send_keys(metrics_bar_id, metrics_cmd, enter=True)

    # Environment variables for orchestrator
    orchestrator_prefix = (
        f"export DOPEMUX_DEFAULT_LITELLM=1; "
        f"export DOPEMUX_TMUX_SESSION={session}; "
        f"export DOPEMUX_AGENT_ROLE=orchestrator; "
        f"export DOPEMUX_SANDBOX_PANE={sandbox_id}; "
        f"export DOPEMUX_AGENT_PANE={agent_primary_id}; "
    )

    # Happy banner in orchestrator pane
    controller.send_keys(orchestrator_id, orchestrator_prefix, enter=False)
    # ... existing Happy integration code

    return DopeLayout(
        monitors=[left_monitor_id, right_monitor_id],
        orchestrator=orchestrator_id,
        sandbox=sandbox_id,
        agent=agent_primary_id,
        secondary_agent=agent_secondary_id,
        metrics_bar=metrics_bar_id,
    )

# Add to layout registry
LAYOUT_FUNCTIONS = {
    'orchestrator': _setup_orchestrator_layout,
    'dope': _setup_dope_layout,  # NEW
    # ... existing layouts
}
```

---

## Configuration

### dopemux.toml

```toml
[tmux]
default_layout = "dope"  # Set dope as default (or keep "orchestrator")

[dope_layout]
default_mode = "implementation"  # Start in implementation mode
metrics_bar_enabled = true       # Show metrics bar
transient_messages_enabled = true  # Enable ADHD messages

[transient_messages]
# Enable/disable by category
untracked_work = true
context_switches = true
task_drift = true
break_reminders = false  # User can disable if annoying

# Thresholds for priority levels
untracked_critical_days = 7   # >7 days = CRITICAL
untracked_warning_days = 1    # 1-7 days = WARNING
break_reminder_minutes = [25, 45, 90]  # Break prompts

[pm_mode]
leantime_url = "http://localhost:3007"
conport_url = "http://localhost:3009"
auto_switch = false  # Smart context detection (opt-in, not yet implemented)

[services]
# Service URLs (with defaults)
adhd_engine_url = "http://localhost:3008"
activity_capture_url = "http://localhost:3006"
serena_url = "http://localhost:3010"
litellm_url = "http://localhost:4000"
```

---

## Dependencies

### Python Packages (requirements.txt)

```
# UI Frameworks
textual>=0.50.0        # Interactive TUI framework with widgets
rich>=13.7.0           # Beautiful text rendering (embedded in Textual)

# Async HTTP
aiohttp>=3.9.0         # Async HTTP client for data collection
asyncio                # stdlib, async I/O primitives
```

### Services (graceful degradation if offline)

**Required for full functionality:**
- ADHD Engine: `localhost:3008` (energy, session, health, focus)
- Activity Capture: `localhost:3006` (context switches, screenshots)
- Serena: `localhost:3010` (untracked work detection)
- Leantime: `localhost:3007` (epics, tasks, sprints)
- ConPort: `localhost:3009` (progress tracking, time logs)
- LiteLLM: `localhost:4000` (cost tracking, latency)

**CLI tools:**
- Git CLI (`git status`, `git diff`)
- Docker Compose CLI (`docker-compose ps`)

**Graceful Fallback:**
- If service offline: Show "N/A" or "Offline" with gray text
- If CLI command fails: Show "Unknown" or cached last value
- Layout remains usable even if all services are down

---

## Implementation Phases

### Phase 1: Core Infrastructure (400 lines, ~2 days)

**Files:**
- `core/app.py` - Main Textual application
- `core/pane_manager.py` - Dynamic pane swapping
- `core/state.py` - Global state management

**Tasks:**
1. Create Textual app skeleton with basic layout
2. Implement PaneManager with mode toggle logic
3. Set up global state for mode, active task, message queue
4. Add keyboard bindings: M (mode toggle), Q (quit), ? (help)
5. Test basic mode switching between dummy panes

**Acceptance Criteria:**
- Press M to toggle between two simple text panes
- App renders without errors
- Keyboard bindings work

---

### Phase 2: Data Collection (500 lines, ~2 days)

**Files:**
- `collectors/base_collector.py` - Abstract base with timeout/fallback
- `collectors/pm_collector.py` - Leantime, ConPort integration
- `collectors/impl_collector.py` - ADHD, Serena, system health

**Tasks:**
1. Implement BaseCollector with async HTTP, 2s timeout, fallback values
2. Create PMCollector with Leantime epic/task/sprint fetching
3. Create ImplCollector with ADHD, Serena, Activity Capture, Git, Docker, MCP, LiteLLM
4. Add TTL caching per data source (5s-30s)
5. Test each collector independently with mock/offline services

**Acceptance Criteria:**
- All collectors return data or fallback gracefully
- 2s timeout enforced on all HTTP calls
- No hanging on offline services

---

### Phase 3: Panes (800 lines, ~3 days)

**Files:**
- `panes/pm_hierarchy.py` - Textual Tree widget for epics/tasks
- `panes/task_detail.py` - Task details panel
- `panes/adhd_monitor.py` - ADHD state + untracked work display
- `panes/system_monitor.py` - Infrastructure health + logs

**Tasks:**
1. Build PM hierarchy pane with Textual Tree widget
   - Epic/task/subtask 3-level tree
   - Status icons (DONE, IN_PROGRESS, TODO, BLOCKED)
   - Arrow key navigation
2. Build task detail pane with selected task info
   - Time tracking, estimates, progress
   - Description, files, action buttons
3. Build ADHD monitor pane with Rich panels
   - Energy, session, health, focus display
   - Serena untracked work section
   - Context switch warnings
4. Build system monitor pane with Rich panels
   - Docker, MCP, LiteLLM status
   - Log streaming (tail -f style)
5. Integrate panes with PaneManager for mode switching

**Acceptance Criteria:**
- PM mode shows navigable tree of epics/tasks
- Selecting task in tree updates detail pane
- ADHD monitor displays real data from collectors
- System monitor shows infrastructure health
- Mode toggle swaps panes correctly

---

### Phase 4: Components (700 lines, ~2 days)

**Files:**
- `components/metrics_bar.py` - Rich Text metrics bar
- `components/transient_messages.py` - Modal overlay system

**Tasks:**
1. Implement metrics bar with Rich Text
   - Context-aware content (PM vs Implementation)
   - Responsive width handling (hide Docker/MCP first)
   - Real-time updates every 5 seconds
2. Implement transient message system
   - Priority queue (critical > warning > info)
   - Modal overlays with Textual Screen system
   - Serena untracked work integration
   - Activity Capture context switch integration
   - Task drift detection (work vs active task mismatch)
3. Add hotkey actions for transients
   - P: Plan untracked work (switch to PM mode, create task)
   - C: Quick commit (git commit with auto-message)
   - D: Dismiss message
4. Test message priority and dismissal

**Acceptance Criteria:**
- Metrics bar shows correct content per mode
- Transient messages appear as modals
- Priority levels work (critical blocks, warning dismissible, info auto-dismiss)
- Pressing P in untracked work message switches to PM mode
- User can dismiss messages with D

---

### Phase 5: Integration & Testing (300 lines, ~2 days)

**Files:**
- `src/dopemux/tmux/cli.py` - Add _setup_dope_layout function
- `config/settings.py` - Configuration loading from dopemux.toml

**Tasks:**
1. Modify cli.py to add dope layout
   - Create pane structure (monitors, orchestrator, sandbox, agent, metrics bar)
   - Auto-start Textual app in monitor panes
   - Auto-start metrics bar
   - Apply NEON_THEME colors
2. Implement configuration loading
   - Read dopemux.toml
   - Apply transient message settings
   - Set default mode
3. End-to-end testing
   - Mode toggle works in tmux session
   - Transient messages appear correctly
   - PM workflow: navigate tree, select task, view details
   - Implementation workflow: view ADHD state, untracked work
4. Performance validation
   - <1% CPU usage
   - <25MB RAM
   - <100ms mode toggle latency
   - 2s timeout on all service calls

**Acceptance Criteria:**
- `dopemux tmux start --layout dope` launches successfully
- All panes render correctly with NEON_THEME colors
- Mode toggle works instantly
- Transient messages integrate with Serena
- Performance targets met

---

## Edge Cases & Error Handling

### Service Offline
- **Behavior**: Show "N/A" or "Offline" in gray text
- **Example**: ADHD Engine offline → Energy: N/A, Session: --
- **Implementation**: Try/except with fallback values in collectors

### Terminal Too Narrow
- **Behavior**: Hide less critical metrics (Docker, MCP first)
- **Example**: Terminal 100 chars → Hide Docker/MCP, show core ADHD data
- **Implementation**: Check terminal width, conditionally render

### Multiple Transient Messages
- **Behavior**: Queue by priority, show one at a time
- **Example**: Untracked work (warning) + break reminder (info) → Show untracked first
- **Implementation**: PriorityQueue in transient_messages.py

### Task Drift False Positive
- **Behavior**: User can mark "related work" to dismiss
- **Example**: Frontend task but editing backend for related feature
- **Implementation**: Add [R] Related work option in modal

### No Tasks in PM Mode
- **Behavior**: Show "No tasks - create one?" prompt
- **Example**: Empty Leantime, new sprint
- **Implementation**: Check if epic list empty, show placeholder

### Rapid Mode Toggling
- **Behavior**: Debounce to prevent flicker
- **Example**: User accidentally presses M multiple times
- **Implementation**: 500ms debounce on mode toggle

### Long Task Names
- **Behavior**: Truncate with ellipsis in tree
- **Example**: "Implement comprehensive multi-tenant authentication..." → "Implement comprehensive mu..."
- **Implementation**: Max 40 chars, add "..." if longer

### Deep Task Nesting
- **Behavior**: Limit to 3 levels (epic → task → subtask)
- **Example**: Subtasks cannot have children
- **Implementation**: Enforce in tree builder

---

## Performance Targets

### Resource Usage
- **CPU**: <1% average (async I/O, no blocking operations)
- **RAM**: <25MB (Textual overhead vs Rich-only 20MB baseline)
- **Network**: 2s timeout on all HTTP calls (no hanging)
- **Disk**: Minimal (no file writes except logs)

### Responsiveness
- **Mode Toggle**: <100ms latency (instant feel)
- **Pane Refresh**: 5-30s intervals per data source (staggered)
- **Startup Time**: <2s from command to full render
- **Keyboard Input**: <50ms response (Textual event loop)

### Validation Commands
```bash
# CPU usage
top -p $(pgrep -f "neon_dashboard") -bn1 | grep python

# RAM usage
ps aux | grep neon_dashboard | awk '{print $6}'

# Mode toggle latency
time echo "M" | tmux send-keys -t dope:monitor:adhd

# Network timeout test
# (Stop ADHD Engine service, verify 2s timeout not hanging)
```

---

## Success Criteria

### Functional Requirements
- [ ] Mode toggle with 'M' key works instantly
- [ ] PM mode shows epic/task hierarchy from Leantime
- [ ] Transient messages appear for untracked work, context switches, task drift
- [ ] Metrics bar adapts to current mode (PM vs Implementation)
- [ ] User can create task from untracked work detection
- [ ] Hotkeys work: P (plan), C (commit), D (dismiss), arrows, Enter
- [ ] Graceful degradation when services offline

### Performance Requirements
- [ ] <1% CPU usage during normal operation
- [ ] <25MB RAM footprint
- [ ] <2s startup time for Textual app
- [ ] <100ms mode toggle latency
- [ ] 2s timeout enforced on all service calls
- [ ] No hanging or freezing on offline services

### ADHD Optimization Requirements
- [ ] Progressive disclosure (metrics bar → panes → details)
- [ ] Clear visual hierarchy (PM vs Implementation separation)
- [ ] Transient messages reduce decision fatigue
- [ ] Gorgeous UI reduces cognitive load
- [ ] Serena integration surfaces untracked work automatically
- [ ] Context switch warnings help maintain focus
- [ ] Task drift alerts prevent unintentional scope creep

---

## Testing Strategy

### Unit Testing
```bash
# Test data collectors independently
cd scripts/neon_dashboard
python3 -m pytest tests/test_collectors.py

# Test pane rendering
python3 -m pytest tests/test_panes.py

# Test transient message priority
python3 -m pytest tests/test_transients.py
```

### Integration Testing
```bash
# Launch dope layout
dopemux tmux start --layout dope

# Verify pane structure
dopemux tmux list  # Should show monitors, orchestrator, sandbox, agent, metrics

# Test mode toggle
# Press M in monitor pane
# Verify pane content changes from ADHD → PM hierarchy

# Test transient messages
# Stop a service to trigger "offline" message
# Check modal appears with correct priority

# Test PM workflow
# Navigate tree with arrows
# Select task with Enter
# Verify detail pane updates
```

### Performance Testing
```bash
# Monitor CPU usage over 5 minutes
top -p $(pgrep -f "neon_dashboard") -d 1 -bn 300 > cpu_test.log

# Monitor RAM usage
watch -n 1 'ps aux | grep neon_dashboard | awk "{print \$6}"'

# Test mode toggle latency
for i in {1..100}; do
  time echo "M" | tmux send-keys -t dope:monitor:adhd
done | grep real | awk '{print $2}' | sort -n | tail -1

# Test service timeout
# Stop all services, verify app still responsive with 2s fallback
```

---

## Future Enhancements (Out of Scope)

### Smart Context Detection
- Auto-switch to PM mode during morning planning hours (9-10am)
- Auto-switch to Implementation mode when many uncommitted files
- Machine learning model to predict optimal mode based on patterns

### Voice Commands
- "Switch to PM mode" voice command
- "Plan this work" for untracked files
- "Show task details for X"

### Mobile Dashboard
- Web-based dashboard showing same metrics
- Mobile notifications for critical transient messages
- Remote mode toggle from phone

### Advanced Analytics
- Task completion velocity trends
- ADHD energy pattern analysis
- Context switch heat maps
- Sprint burndown visualizations

### Integration with Other Tools
- GitHub Issues sync with Leantime tasks
- Slack notifications for critical messages
- Google Calendar integration for time tracking

---

## Questions Resolved

1. **New layout vs modify orchestrator?**
   - ✓ New `--layout dope` (orchestrator unchanged)

2. **Metrics bar always-on?**
   - ✓ Yes, with context-aware content (PM vs Implementation)

3. **Hide Docker/MCP first if needed?**
   - ✓ Yes, responsive width handling

4. **Refresh rates 5-30s OK?**
   - ✓ Yes, staggered intervals per data source type

5. **Textual vs Rich?**
   - ✓ Hybrid: Textual for interactivity + Rich for beauty

6. **Transient message triggers?**
   - ✓ Untracked work, context switches, task drift (user selected)

7. **PM vs Implementation mode?**
   - ✓ Dynamic pane swapping with 'M' toggle (user selected)

8. **Use gorgeous UI libraries?**
   - ✓ Yes, Textual + Rich hybrid for maximum beauty and interactivity

9. **Incorporate Serena untracked work?**
   - ✓ Yes, integrated into transient message system with "Plan this work" action

10. **Optimize for PM use?**
    - ✓ Yes, dedicated PM mode with epic/task hierarchy and task details

---

## Architecture Decisions

### Why Textual + Rich Hybrid?
- **Textual**: Only option for interactive PM mode (Tree widget, keyboard, modals)
- **Rich**: Still best for metrics bar and static displays
- **Hybrid**: Textual can embed Rich renderables, best of both worlds

### Why Not Pure Rich?
- Rich is display-only (no keyboard input, no interactivity)
- Cannot build navigable tree widget or modal dialogs
- Insufficient for PM mode requirements

### Why Separate PM and Implementation Collectors?
- **Data Model Difference**: PM is hierarchical (epics → tasks), Implementation is flat metrics
- **Refresh Rates**: PM data changes slowly (30s), Implementation changes rapidly (5s)
- **Service Dependencies**: PM needs Leantime/ConPort, Implementation needs ADHD/Serena
- **Modularity**: Clear separation of concerns, easier to maintain

### Why Priority Queue for Transient Messages?
- **ADHD Optimization**: Critical messages must not be ignored
- **User Control**: Warning/info can be dismissed when user is focused
- **Prevents Spam**: Queue ensures one message at a time
- **Flexibility**: User can disable categories in config

---

## References

### Related Documentation
- `NEON_LAYOUT_ZEN_PLAN.md` - Original Zen planning (7-pane Balanced Hybrid design)
- `MONITORING-DOCS-INDEX.md` - Existing monitoring infrastructure
- `ORCHESTRATOR-INTEGRATION-COMPLETE.md` - Orchestrator layout patterns
- `src/dopemux/tmux/cli.py` - Existing layout implementations

### Zen Analysis Summary
- **Steps Completed**: 7 steps (3 initial + 4 deep analysis)
- **Confidence**: Very High
- **Key Findings**:
  - Textual superior to Rich for interactive PM mode
  - Hybrid approach solves all requirements
  - Modular architecture with separate collectors
  - Priority system for transient ADHD messages
  - Dynamic pane swapping via state machine

### External Resources
- Textual Documentation: https://textual.textualize.io/
- Rich Documentation: https://rich.readthedocs.io/
- Serena Untracked Work API: `localhost:3010/detect-untracked`
- Leantime API: `localhost:3007/api/v1/`

---

**Plan Status**: ✓ Complete and ready for implementation
**Total Lines**: ~2,300 across 15 files
**Estimated Time**: ~11 days (5 phases)
**Confidence**: Very High (Zen validated)
