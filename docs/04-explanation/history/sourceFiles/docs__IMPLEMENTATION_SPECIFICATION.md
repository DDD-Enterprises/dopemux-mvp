# 🛠️ Dopemux Implementation Specification

## Executive Summary

Complete technical specification for implementing the Dopemux ADHD-optimized MCP orchestration system. This document provides the blueprint for all code, configurations, and integrations required.

## Project Structure

```
dopemux-mvp/
├── docker/
│   ├── docker-compose.yml              # Master orchestration
│   ├── infrastructure/
│   │   ├── postgres/
│   │   │   ├── Dockerfile
│   │   │   ├── init.sql               # Schema initialization
│   │   │   └── indexes.sql            # Performance indexes
│   │   ├── redis/
│   │   │   ├── Dockerfile
│   │   │   └── redis.conf
│   │   └── milvus/
│   │       ├── Dockerfile
│   │       └── milvus.yaml
│   ├── mcp-servers/
│   │   ├── conport/
│   │   ├── openmemory/
│   │   ├── zen/
│   │   ├── mas-sequential-thinking/
│   │   ├── claude-context/
│   │   ├── task-master/
│   │   ├── leantime/
│   │   ├── desktop-commander/
│   │   ├── github/
│   │   ├── context7/
│   │   ├── morphllm-fast-apply/
│   │   └── exa/
│   ├── orchestrator/
│   │   ├── Dockerfile
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── role_manager.py
│   │   │   ├── token_manager.py
│   │   │   └── workflow_engine.py
│   │   └── config/
│   │       ├── roles.yaml
│   │       └── workflows.yaml
│   └── services/
│       ├── calendar-sync/
│       ├── notification-service/
│       └── time-awareness/
├── src/
│   └── dopemux/
│       ├── adhd/
│       │   ├── __init__.py
│       │   ├── context_manager.py
│       │   ├── time_awareness.py
│       │   ├── notifications.py
│       │   └── task_decomposer.py
│       ├── terminal/
│       │   ├── __init__.py
│       │   ├── tmux_controller.py
│       │   ├── dashboard.py
│       │   └── beautification.py
│       ├── calendar/
│       │   ├── __init__.py
│       │   ├── ical_sync.py
│       │   └── time_blocks.py
│       ├── orchestration/
│       │   ├── __init__.py
│       │   ├── session_manager.py
│       │   ├── role_manager.py
│       │   ├── workflow_engine.py
│       │   └── context_predictor.py
│       ├── telemetry/
│       │   ├── __init__.py
│       │   ├── collector.py
│       │   └── analyzer.py
│       └── config/
│           └── manager.py              # UPDATE existing
├── config/
│   ├── dopemux.yaml                   # Main configuration
│   ├── adhd.yaml                      # ADHD-specific settings
│   └── life-domains.yaml              # Domain configurations
├── scripts/
│   ├── install-mcp-servers.sh         # UPDATE existing
│   └── setup-docker.sh                # NEW
├── .env.example                        # Environment template
└── .tmux.conf.dopemux                  # Tmux configuration
```

## Core Implementation Modules

### 1. ADHD Context Manager

**File**: `src/dopemux/adhd/context_manager.py`

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class ContextBookmark:
    """Snapshot of context at interruption point"""
    timestamp: datetime
    file_path: Optional[str]
    line_number: Optional[int]
    active_thought: str
    next_action: str
    breadcrumbs: List[str]
    role: str
    tools_loaded: List[str]

class ADHDContextManager:
    """Manages context preservation and restoration"""

    def __init__(self, conport_client, openmemory_client):
        self.conport = conport_client
        self.openmemory = openmemory_client
        self.current_bookmark = None
        self.context_trail = []

    async def detect_context_switch(self) -> bool:
        """Detect if user is switching contexts"""
        indicators = {
            'file_change': self._check_file_pattern_change(),
            'time_gap': self._check_time_gap(),
            'tool_switch': self._check_tool_usage_change(),
            'directory_change': self._check_directory_change()
        }

        score = sum(1 for v in indicators.values() if v)
        return score >= 2

    async def create_bookmark(self) -> ContextBookmark:
        """Create a bookmark of current context"""
        bookmark = ContextBookmark(
            timestamp=datetime.now(),
            file_path=self.get_current_file(),
            line_number=self.get_current_line(),
            active_thought=await self._capture_active_thought(),
            next_action=await self._predict_next_action(),
            breadcrumbs=self.context_trail[-10:],
            role=self.current_role,
            tools_loaded=self.get_loaded_tools()
        )

        # Save to ConPort
        await self.conport.update_active_context({
            'bookmark': bookmark.to_dict()
        })

        return bookmark

    async def restore_from_bookmark(self, bookmark: ContextBookmark):
        """Restore context from bookmark"""
        # Load the role and tools
        await self.load_role(bookmark.role)

        # Open the file if applicable
        if bookmark.file_path:
            await self.open_file(bookmark.file_path, bookmark.line_number)

        # Restore breadcrumbs
        self.context_trail = bookmark.breadcrumbs

        # Display context summary
        await self.display_context_summary(bookmark)

    async def handle_interruption(self):
        """Grace period for handling interruptions"""
        print("🔖 Detecting interruption... saving context")

        bookmark = await self.create_bookmark()

        # Give visual feedback
        await self.show_bookmark_saved(bookmark)

        # Store for quick recovery
        await self.openmemory.store(
            key='last_interruption',
            value=bookmark.to_dict()
        )

        return bookmark

    def add_breadcrumb(self, crumb: str):
        """Add to context trail"""
        self.context_trail.append({
            'timestamp': datetime.now(),
            'description': crumb,
            'type': self._classify_breadcrumb(crumb)
        })

        # Keep trail manageable
        if len(self.context_trail) > 50:
            self.context_trail = self.context_trail[-50:]
```

### 2. Time Awareness System

**File**: `src/dopemux/adhd/time_awareness.py`

```python
from datetime import datetime, timedelta
import asyncio
from typing import Optional

class GentleTimeAwareness:
    """Non-anxious time tracking for ADHD"""

    def __init__(self, notification_service, calendar_service):
        self.notifications = notification_service
        self.calendar = calendar_service
        self.session_start = None
        self.last_break = None
        self.focus_blocks = []

    async def start_session(self):
        """Initialize time tracking for session"""
        self.session_start = datetime.now()
        self.last_break = datetime.now()

        # Start background monitoring
        asyncio.create_task(self._monitor_time())

    async def _monitor_time(self):
        """Background time monitoring"""
        while True:
            await asyncio.sleep(60)  # Check every minute

            elapsed = self.get_elapsed_time()

            # Gentle reminders based on elapsed time
            if elapsed.total_seconds() > 1500:  # 25 minutes
                await self.suggest_break()
            elif elapsed.total_seconds() > 5400:  # 90 minutes
                await self.suggest_longer_break()
            elif elapsed.total_seconds() > 14400:  # 4 hours
                await self.suggest_session_end()

    def get_elapsed_time(self) -> timedelta:
        """Get time since last break"""
        return datetime.now() - self.last_break

    def format_friendly_time(self, td: timedelta) -> str:
        """Format time in ADHD-friendly way"""
        total_minutes = int(td.total_seconds() / 60)

        if total_minutes < 5:
            return "just started"
        elif total_minutes < 15:
            return "about 10 minutes"
        elif total_minutes < 25:
            return "about 20 minutes"
        elif total_minutes < 35:
            return "about half an hour"
        elif total_minutes < 50:
            return "about 45 minutes"
        elif total_minutes < 70:
            return "about an hour"
        elif total_minutes < 110:
            return "about an hour and a half"
        elif total_minutes < 150:
            return "about 2 hours"
        else:
            hours = total_minutes // 60
            return f"about {hours} hours"

    async def get_time_context(self) -> dict:
        """Get current time awareness context"""
        elapsed = self.get_elapsed_time()

        # Check calendar for upcoming events
        next_event = await self.calendar.get_next_event()
        time_until_event = None
        if next_event:
            time_until_event = next_event.start - datetime.now()

        return {
            'elapsed': self.format_friendly_time(elapsed),
            'elapsed_raw': elapsed,
            'pace': self._calculate_pace(),
            'energy': self._estimate_energy_level(),
            'suggestion': self._get_time_suggestion(elapsed),
            'next_event': next_event,
            'time_until_event': self.format_friendly_time(time_until_event) if time_until_event else None,
            'visual': self._create_progress_bar(elapsed)
        }

    def _calculate_pace(self) -> str:
        """Calculate work pace"""
        # Based on task completion vs estimates
        return "good pace"  # Placeholder

    def _estimate_energy_level(self) -> str:
        """Estimate current energy level"""
        elapsed = self.get_elapsed_time()
        hour = datetime.now().hour

        if elapsed.total_seconds() < 1800:  # < 30 min
            return "fresh"
        elif elapsed.total_seconds() < 5400:  # < 90 min
            return "focused"
        elif elapsed.total_seconds() < 10800:  # < 3 hours
            return "steady"
        else:
            return "low"

    def _create_progress_bar(self, elapsed: timedelta) -> str:
        """Create visual progress indicator"""
        minutes = int(elapsed.total_seconds() / 60)

        # 25-minute chunks
        full_chunks = minutes // 25
        partial = (minutes % 25) / 25

        bar = "🟩" * full_chunks
        if partial > 0.75:
            bar += "🟨"
        elif partial > 0.5:
            bar += "🟧"
        elif partial > 0.25:
            bar += "🟥"
        else:
            bar += "⬜"

        # Add remaining empty chunks (up to 4 total for 100 min)
        remaining = 4 - full_chunks - (1 if partial > 0 else 0)
        bar += "⬜" * max(0, remaining)

        return f"[{bar}]"

    async def suggest_break(self):
        """Gentle break suggestion"""
        await self.notifications.notify(
            message="Good progress! Time for a quick break?",
            style='gentle_reminder',
            actions=['Take 5 min break', 'Continue for 5 more', 'Snooze']
        )

    async def prevent_deadline_doom(self):
        """Detect and prevent last-minute panic"""
        upcoming_deadlines = await self.calendar.get_deadlines(days=2)

        for deadline in upcoming_deadlines:
            time_remaining = deadline.due - datetime.now()
            estimated_time = deadline.estimated_hours * 3600

            if time_remaining.total_seconds() < estimated_time * 1.5:
                # Not enough time with buffer
                await self.trigger_gentle_intervention(deadline)
                await self.suggest_scope_reduction(deadline)
```

### 3. Terminal Notification System

**File**: `src/dopemux/terminal/notifications.py`

```python
import subprocess
import asyncio
from typing import Optional, List

class TerminalNotificationSystem:
    """Beautiful terminal and macOS notifications"""

    def __init__(self):
        self.tmux = self._detect_tmux()
        self.terminal_app = self._detect_terminal_app()

    async def notify(self, message: str, style: str, **kwargs):
        """Multi-layer notification strategy"""

        if style == 'time_awareness':
            await self._update_tmux_status(message)

        elif style == 'gentle_reminder':
            await self._show_corner_notification(message)

        elif style == 'deadline_approaching':
            await self._escalating_notification(message)

        elif style == 'achievement':
            await self._celebration_notification(message)

        elif style == 'context_switch':
            await self._floating_window_notification(message)

    async def _update_tmux_status(self, message: str):
        """Update tmux status bar"""
        if not self.tmux:
            return

        # Right side of status bar
        cmd = f"tmux set-option -g status-right '{message}'"
        subprocess.run(cmd, shell=True)

    async def _show_corner_notification(self, message: str):
        """Subtle corner notification"""
        # macOS notification center
        subprocess.run([
            'osascript', '-e',
            f'display notification "{message}" with title "Dopemux" sound name "Submarine"'
        ])

        # Also update terminal title
        print(f"\033]0;Dopemux: {message}\007", end='')

    async def _escalating_notification(self, message: str):
        """Gradually increasing visibility"""
        # Stage 1: Status bar
        await self._update_tmux_status(f"⏰ {message}")
        await asyncio.sleep(5)

        # Stage 2: Terminal badge
        if self.terminal_app == 'iTerm2':
            subprocess.run(['osascript', '-e',
                'tell application "iTerm" to set badge of current session to "!"'])

        # Stage 3: System notification
        await asyncio.sleep(10)
        subprocess.run(['terminal-notifier',
            '-title', 'Dopemux Deadline',
            '-message', message,
            '-sound', 'default'])

    async def _celebration_notification(self, message: str):
        """Dopamine reward notification"""
        # Confetti in terminal (using special chars)
        confetti = "🎉 🎊 ✨ 🎈 🎆"
        print(f"\n{confetti} {message} {confetti}\n")

        # Play celebration sound
        subprocess.run(['afplay', '/System/Library/Sounds/Glass.aiff'])

        # macOS notification
        subprocess.run(['osascript', '-e',
            f'display notification "🎉 {message}" with title "Achievement!" sound name "Glass"'])

    async def _floating_window_notification(self, message: str):
        """Floating terminal window"""
        if self.tmux:
            # Create floating pane
            subprocess.run([
                'tmux', 'display-popup', '-E',
                f'echo "{message}"; read -n 1'
            ])
        else:
            # Fall back to regular notification
            await self._show_corner_notification(message)

    def create_adhd_dashboard(self) -> str:
        """Generate terminal dashboard"""
        dashboard = """
╔════════════════════ Dopemux Dashboard ════════════════════╗
║ Role: {role} │ Context: {context} │ Focus: {focus_time}   ║
╠════════════════════════════════════════════════════════════╣
║ 📍 Current Task                                            ║
║ ├─ {task_title}                                           ║
║ ├─ Progress: {progress_bar} {progress_percent}%           ║
║ └─ Next: {next_steps}                                     ║
╠════════════════════════════════════════════════════════════╣
║ ⏰ Time Awareness                                          ║
║ ├─ Session: {session_time}                                ║
║ ├─ Next break: {break_time}                               ║
║ └─ Today: {today_summary}                                 ║
╠════════════════════════════════════════════════════════════╣
║ 📅 Upcoming (from iCal)                                    ║
║ ├─ {event1}                                               ║
║ ├─ {event2}                                               ║
║ └─ {event3}                                               ║
╠════════════════════════════════════════════════════════════╣
║ 🎯 Quick Actions                                           ║
║ [f]ocus [s]catter [c]heckpoint [b]reak [?]help            ║
╚════════════════════════════════════════════════════════════╝
        """
        return dashboard
```

### 4. Calendar Integration

**File**: `src/dopemux/calendar/ical_sync.py`

```python
from caldav import DAVClient, Calendar
from icalendar import Event, Todo
from datetime import datetime, timedelta
import asyncio

class ICalIntegration:
    """Seamless iCal/CalDAV integration"""

    def __init__(self, config):
        self.client = DAVClient(
            url=config['caldav_url'],
            username=config['username'],
            password=config['password']
        )
        self.dopemux_calendar = None

    async def initialize(self):
        """Set up Dopemux calendar"""
        principal = self.client.principal()

        # Check if Dopemux calendar exists
        for calendar in principal.calendars():
            if calendar.name == 'Dopemux Tasks':
                self.dopemux_calendar = calendar
                break

        # Create if doesn't exist
        if not self.dopemux_calendar:
            self.dopemux_calendar = principal.make_calendar(
                name='Dopemux Tasks',
                color='#7aa2f7'
            )

    async def sync_tasks_to_calendar(self, tasks):
        """Sync tasks from Task-Master/Leantime to iCal"""
        for task in tasks:
            # Check if event already exists
            existing = await self._find_event_by_task_id(task.id)

            if existing:
                await self._update_event(existing, task)
            else:
                await self._create_event(task)

    async def _create_event(self, task):
        """Create calendar event from task"""
        event = Event()

        # ADHD-friendly title with emoji
        emoji = self._get_task_emoji(task.type)
        event.add('summary', f"{emoji} {task.title}")

        # Time settings
        event.add('dtstart', task.scheduled_start or datetime.now())
        event.add('dtend', task.scheduled_end or
                 (task.scheduled_start + timedelta(minutes=task.estimated_minutes)))

        # Detailed description
        description = f"""
Task ID: {task.id}
Project: {task.project}
Context: {task.context}

Estimated Time: {task.estimated_minutes} minutes
Energy Required: {task.energy_level}
Focus Type: {task.focus_type}

Description:
{task.description}

Checklist:
{self._format_subtasks(task.subtasks)}

---
Managed by Dopemux
        """
        event.add('description', description)

        # Color coding
        if task.priority == 'urgent':
            event.add('color', 'red')
        elif task.energy_level == 'low':
            event.add('color', 'green')
        elif task.focus_type == 'hyperfocus':
            event.add('color', 'purple')
        else:
            event.add('color', 'blue')

        # Add to calendar
        self.dopemux_calendar.add_event(event)

    def _get_task_emoji(self, task_type):
        """Get emoji for task type"""
        emojis = {
            'bug': '🐛',
            'feature': '✨',
            'meeting': '👥',
            'review': '👀',
            'planning': '📝',
            'coding': '💻',
            'break': '☕',
            'exercise': '🏃',
            'personal': '🏠'
        }
        return emojis.get(task_type, '📌')

    async def get_time_blocks(self, days=7):
        """Find available time blocks for deep work"""
        # Get all events for next N days
        events = self.dopemux_calendar.date_search(
            start=datetime.now(),
            end=datetime.now() + timedelta(days=days)
        )

        # Find gaps
        time_blocks = []
        last_end = datetime.now()

        for event in sorted(events, key=lambda e: e.start):
            gap = event.start - last_end

            if gap > timedelta(minutes=30):  # At least 30 min gap
                time_blocks.append({
                    'start': last_end,
                    'end': event.start,
                    'duration': gap,
                    'quality': self._assess_time_quality(last_end)
                })

            last_end = event.end

        return time_blocks

    def _assess_time_quality(self, time):
        """Assess quality of time block for ADHD patterns"""
        hour = time.hour

        if 6 <= hour < 10:
            return 'morning_focus'  # High focus
        elif 10 <= hour < 12:
            return 'late_morning'    # Good focus
        elif 14 <= hour < 17:
            return 'afternoon'       # Variable
        elif 19 <= hour < 22:
            return 'evening'         # Second wind
        else:
            return 'low_energy'      # Not ideal
```

### 5. Session Orchestrator

**File**: `src/dopemux/orchestration/session_manager.py`

```python
class SessionOrchestrator:
    """Automated session lifecycle management"""

    def __init__(self, services):
        self.conport = services['conport']
        self.openmemory = services['openmemory']
        self.metamcp = services['metamcp']
        self.calendar = services['calendar']
        self.notifications = services['notifications']
        self.time_awareness = services['time_awareness']

        self.session_id = None
        self.current_role = None
        self.checkpoints = []

    async def initialize_session(self):
        """Full session initialization"""
        print("🚀 Initializing Dopemux session...")

        # 1. Detect workspace
        workspace = await self._detect_workspace()

        # 2. Check ConPort
        conport_status = await self._initialize_conport(workspace)

        # 3. Load previous context
        previous_context = await self.openmemory.retrieve('last_session')

        # 4. Check calendar
        upcoming = await self.calendar.get_next_event()

        # 5. Analyze and suggest role
        suggested_role = await self._analyze_context_for_role(
            conport_status, previous_context, upcoming
        )

        # 6. Load role tools
        await self.metamcp.switch_role(suggested_role)

        # 7. Start monitoring
        await self._start_background_monitoring()

        # 8. Display status
        await self._display_session_status({
            'workspace': workspace,
            'conport': conport_status,
            'role': suggested_role,
            'tokens': self.metamcp.get_token_count(),
            'next_event': upcoming
        })

        return True

    async def _start_background_monitoring(self):
        """Start all background tasks"""
        tasks = [
            self._checkpoint_monitor(),
            self._calendar_monitor(),
            self._context_switch_monitor(),
            self._deadline_monitor()
        ]

        for task in tasks:
            asyncio.create_task(task)

    async def _checkpoint_monitor(self):
        """Regular checkpointing for ADHD"""
        while True:
            await asyncio.sleep(1500)  # 25 minutes

            await self.create_checkpoint()
            await self.notifications.notify(
                "25-minute checkpoint! Time for a quick break?",
                style='gentle_reminder'
            )

    async def create_checkpoint(self):
        """Save current state"""
        checkpoint = {
            'timestamp': datetime.now(),
            'role': self.current_role,
            'context': await self.conport.get_active_context(),
            'progress': await self.conport.get_progress(limit=5),
            'tokens_used': self.metamcp.get_token_count()
        }

        # Save to multiple places
        await self.conport.update_active_context({
            'last_checkpoint': checkpoint
        })
        await self.openmemory.store(
            f'checkpoint_{self.session_id}_{len(self.checkpoints)}',
            checkpoint
        )

        self.checkpoints.append(checkpoint)

        return checkpoint

    async def _analyze_context_for_role(self, conport, previous, calendar):
        """Intelligently determine starting role"""

        # Check active context
        if conport and conport.get('active_context'):
            active = conport['active_context']
            if 'current_task' in active:
                task_type = active['current_task'].get('type')

                if task_type == 'research':
                    return 'researcher'
                elif task_type == 'implementation':
                    return 'implementer'
                elif task_type == 'review':
                    return 'reviewer'

        # Check calendar
        if calendar and calendar.get('title'):
            if 'standup' in calendar['title'].lower():
                return 'product_manager'
            elif 'review' in calendar['title'].lower():
                return 'reviewer'
            elif 'planning' in calendar['title'].lower():
                return 'architect'

        # Check time of day
        hour = datetime.now().hour
        if 6 <= hour < 10:
            return 'researcher'  # Morning = research/planning
        elif 10 <= hour < 15:
            return 'implementer'  # Midday = coding
        elif 15 <= hour < 18:
            return 'reviewer'  # Afternoon = review
        else:
            return 'documenter'  # Evening = documentation

    async def handle_interrupt(self):
        """Handle interruption gracefully"""
        # Create bookmark
        bookmark = await self.context_manager.create_bookmark()

        # Quick save
        await self.create_checkpoint()

        # Notify
        await self.notifications.notify(
            f"Context saved! Bookmark created at {bookmark.file_path}:{bookmark.line_number}",
            style='context_switch'
        )

        return bookmark
```

### 6. MetaMCP Orchestrator

**File**: `docker/orchestrator/src/main.py`

```python
from fastapi import FastAPI, WebSocket
from typing import Dict, List, Optional
import asyncio
import yaml

class MetaMCPOrchestrator:
    """Central gateway for MCP server orchestration"""

    def __init__(self, config_path: str):
        self.app = FastAPI()
        self.config = self._load_config(config_path)
        self.active_servers = {}
        self.token_budget = 10000
        self.current_role = None
        self.websockets = {}

        self._setup_routes()

    def _load_config(self, path: str) -> dict:
        """Load role and server configurations"""
        with open(f"{path}/roles.yaml") as f:
            roles = yaml.safe_load(f)
        with open(f"{path}/workflows.yaml") as f:
            workflows = yaml.safe_load(f)

        return {
            'roles': roles,
            'workflows': workflows
        }

    async def switch_role(self, new_role: str):
        """Switch to a new role with tool loading"""
        print(f"🔄 Switching from {self.current_role} to {new_role}")

        # Unload current tools
        if self.current_role:
            await self._unload_role(self.current_role)

        # Load new role tools
        role_config = self.config['roles'][new_role]

        for server_name, tools in role_config['servers'].items():
            await self._load_server(server_name, tools)

        self.current_role = new_role

        # Update token count
        self._update_token_count()

        return {
            'role': new_role,
            'servers_loaded': list(self.active_servers.keys()),
            'token_count': self.get_token_count()
        }

    async def _load_server(self, server_name: str, tools: List[str]):
        """Load specific tools from a server"""
        if server_name in self.active_servers:
            # Already loaded, just update tools
            self.active_servers[server_name]['tools'] = tools
        else:
            # Connect to server
            ws = await self._connect_to_server(server_name)
            self.active_servers[server_name] = {
                'websocket': ws,
                'tools': tools,
                'token_cost': self._estimate_tool_tokens(tools)
            }

    async def _connect_to_server(self, server_name: str):
        """Establish WebSocket connection to MCP server"""
        url = f"ws://{server_name}:8080/mcp"
        ws = await websocket.connect(url)
        self.websockets[server_name] = ws
        return ws

    def get_token_count(self) -> int:
        """Calculate current token usage"""
        total = 0
        for server in self.active_servers.values():
            total += server['token_cost']
        return total

    def _estimate_tool_tokens(self, tools: List[str]) -> int:
        """Estimate token cost for tools"""
        # Tool token estimates
        estimates = {
            'sequentialthinking': 900,
            'search_code': 800,
            'edit_file': 1000,
            'codereview': 1200,
            'get_docs': 700,
            # ... more estimates
        }

        return sum(estimates.get(tool, 500) for tool in tools)

    async def handle_request(self, request: dict):
        """Route request to appropriate server"""
        tool = request['tool']

        # Find which server handles this tool
        for server_name, server_info in self.active_servers.items():
            if tool in server_info['tools']:
                # Forward to server
                ws = server_info['websocket']
                await ws.send_json(request)
                response = await ws.receive_json()
                return response

        return {"error": f"Tool {tool} not available in current role"}

    @app.websocket("/orchestrator")
    async def websocket_endpoint(self, websocket: WebSocket):
        """Main WebSocket endpoint for Claude"""
        await websocket.accept()

        while True:
            try:
                data = await websocket.receive_json()

                if data['type'] == 'switch_role':
                    result = await self.switch_role(data['role'])
                    await websocket.send_json(result)

                elif data['type'] == 'request':
                    result = await self.handle_request(data)
                    await websocket.send_json(result)

                elif data['type'] == 'status':
                    await websocket.send_json({
                        'role': self.current_role,
                        'servers': list(self.active_servers.keys()),
                        'tokens': self.get_token_count()
                    })

            except Exception as e:
                await websocket.send_json({"error": str(e)})
```

### 7. Docker Compose Configuration

**File**: `docker/docker-compose.yml`

```yaml
version: '3.8'

networks:
  dopemux-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

volumes:
  postgres_data:
  redis_data:
  milvus_data:
  conport_data:
  openmemory_data:
  leantime_data:
  grafana_data:

services:
  # === INFRASTRUCTURE LAYER ===
  postgres:
    build: ./infrastructure/postgres
    container_name: dopemux-postgres
    environment:
      POSTGRES_DB: dopemux
      POSTGRES_USER: dopemux
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/postgres/init.sql:/docker-entrypoint-initdb.d/01-init.sql
    networks:
      - dopemux-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dopemux"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    build: ./infrastructure/redis
    container_name: dopemux-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - dopemux-net
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]

  # === MCP SERVERS ===
  conport:
    build: ./mcp-servers/conport
    container_name: dopemux-conport
    environment:
      DATABASE_URL: postgresql://dopemux:${POSTGRES_PASSWORD}@postgres:5432/dopemux
      AUTO_DETECT_WORKSPACE: "true"
      WORKSPACE_SEARCH_START: /workspace
    volumes:
      - ${PWD}:/workspace:ro
      - conport_data:/data
    networks:
      - dopemux-net
    depends_on:
      postgres:
        condition: service_healthy

  openmemory:
    build: ./mcp-servers/openmemory
    container_name: dopemux-openmemory
    environment:
      DATABASE_URL: postgresql://dopemux:${POSTGRES_PASSWORD}@postgres:5432/dopemux
      REDIS_URL: redis://default:${REDIS_PASSWORD}@redis:6379
    networks:
      - dopemux-net
    depends_on:
      - postgres
      - redis

  zen:
    build: ./mcp-servers/zen
    container_name: dopemux-zen
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      ZEN_DISABLED_TOOLS: "chat,explain,translate,summarize"
    networks:
      - dopemux-net

  mas-sequential-thinking:
    build:
      context: ${MAS_PATH:-/Users/hue/code/mcp-server-mas-sequential-thinking}
      dockerfile: Dockerfile
    container_name: dopemux-mas-sequential
    environment:
      LLM_PROVIDER: ${LLM_PROVIDER:-deepseek}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    networks:
      - dopemux-net

  # === ORCHESTRATOR ===
  orchestrator:
    build: ./orchestrator
    container_name: dopemux-orchestrator
    ports:
      - "8000:8000"
    environment:
      CONFIG_PATH: /config
      MAX_TOKENS: 10000
      DEFAULT_ROLE: researcher
    volumes:
      - ./orchestrator/config:/config:ro
    networks:
      - dopemux-net
    depends_on:
      - conport
      - openmemory
      - zen

  # === MONITORING ===
  grafana:
    image: grafana/grafana:latest
    container_name: dopemux-grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_INSTALL_PLUGINS: redis-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    networks:
      - dopemux-net
```

## CLI Enhancement

**File**: `src/dopemux/cli.py` (additions)

```python
# New commands to add to existing CLI

@click.group()
def adhd():
    """ADHD support commands"""
    pass

@adhd.command()
def focus():
    """Enter deep focus mode"""
    orchestrator = get_orchestrator()
    orchestrator.switch_role('implementer')
    notifications.notify("Entering focus mode", style='focus')
    calendar.block_time(duration=120)

@adhd.command()
def scatter():
    """Switch to exploration mode"""
    orchestrator = get_orchestrator()
    orchestrator.switch_role('researcher')
    notifications.notify("Exploration mode", style='scatter')

@adhd.command()
def checkpoint():
    """Save current context"""
    session = get_session_orchestrator()
    checkpoint = session.create_checkpoint()
    print(f"✅ Checkpoint saved: {checkpoint['timestamp']}")

@adhd.command()
def time():
    """Show time awareness"""
    time_awareness = get_time_awareness()
    context = time_awareness.get_time_context()
    print(f"⏰ {context['visual']} {context['elapsed']}")
    print(f"   Energy: {context['energy']}")
    print(f"   {context['suggestion']}")

@click.group()
def cal():
    """Calendar integration"""
    pass

@cal.command()
def sync():
    """Sync with iCal"""
    calendar = get_calendar_service()
    result = calendar.sync()
    print(f"📅 Synced {result['events']} events, {result['tasks']} tasks")

@cal.command()
def today():
    """Show today's schedule"""
    calendar = get_calendar_service()
    events = calendar.get_today()
    for event in events:
        print(f"{event['time']} - {event['title']}")
```

## Configuration Files

**File**: `config/dopemux.yaml`

```yaml
# Main Dopemux configuration

adhd:
  checkpoint_interval: 25m
  break_duration: 5m
  hyperfocus_max: 4h
  notification_style: gentle
  time_display: relative
  context_preservation: true

orchestration:
  max_tokens: 10000
  default_role: researcher
  auto_transitions: true
  role_switching: dynamic

calendar:
  provider: ical
  url: ${CALDAV_URL}
  sync_interval: 5m
  bidirectional: true

notifications:
  terminal: true
  macos: true
  sound: gentle
  visual_style: minimal

telemetry:
  enabled: true
  anonymous: true
  metrics:
    - token_usage
    - role_transitions
    - task_completion
    - focus_duration
```

## Environment Variables Template

**File**: `.env.example`

```bash
# === API Keys ===
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
GROQ_API_KEY=gsk_...
EXA_API_KEY=...
GITHUB_TOKEN=ghp_...
MEM0_API_KEY=...

# === Database ===
POSTGRES_PASSWORD=secure_password
REDIS_PASSWORD=secure_password

# === Calendar ===
CALDAV_URL=https://caldav.icloud.com/
CALDAV_USERNAME=your_apple_id@icloud.com
CALDAV_PASSWORD=app_specific_password

# === Paths ===
MAS_PATH=/Users/hue/code/mcp-server-mas-sequential-thinking
WORKSPACE_PATH=/Users/hue/code/dopemux-mvp

# === Monitoring ===
GRAFANA_PASSWORD=admin_password

# === ADHD Settings ===
CHECKPOINT_INTERVAL=25m
BREAK_DURATION=5m
HYPERFOCUS_MAX=4h
NOTIFICATION_STYLE=gentle
TIME_DISPLAY=relative
```

## Implementation Checklist

### Phase 1: Infrastructure (Week 1)
- [ ] Create Docker directory structure
- [ ] Write docker-compose.yml
- [ ] Set up PostgreSQL schema
- [ ] Configure Redis
- [ ] Deploy Milvus
- [ ] Test infrastructure connectivity

### Phase 2: MCP Servers (Week 1-2)
- [ ] Containerize ConPort
- [ ] Containerize OpenMemory
- [ ] Containerize zen-mcp
- [ ] Use existing mas-sequential Dockerfile
- [ ] Containerize remaining servers
- [ ] Test individual server functionality

### Phase 3: Orchestration (Week 2)
- [ ] Build MetaMCP orchestrator
- [ ] Implement role management
- [ ] Create token budget system
- [ ] Test role switching
- [ ] Verify tool loading/unloading

### Phase 4: ADHD Features (Week 3)
- [ ] Implement context manager
- [ ] Create time awareness system
- [ ] Build notification system
- [ ] Design terminal dashboard
- [ ] Add interrupt handling

### Phase 5: Integration (Week 3-4)
- [ ] Calendar sync implementation
- [ ] Task management integration
- [ ] Session orchestrator
- [ ] Workflow engine
- [ ] Context predictor

### Phase 6: Polish (Week 4-5)
- [ ] Performance optimization
- [ ] Error handling
- [ ] Testing suite
- [ ] Documentation
- [ ] User onboarding

## Success Criteria

1. **Performance**
   - Context switch: <5 seconds
   - Token usage: <10k active
   - Response time: <500ms

2. **ADHD Support**
   - Checkpoint success: >95%
   - Context preservation: 100%
   - Break reminders: Every 25min

3. **Integration**
   - Calendar sync: Bidirectional
   - Task sync: Real-time
   - Notification delivery: 100%

4. **User Experience**
   - Setup time: <10 minutes
   - Learning curve: <1 hour
   - Daily active use: >80%

---

*This specification provides the complete blueprint for implementing the Dopemux ADHD-optimized MCP orchestration system.*