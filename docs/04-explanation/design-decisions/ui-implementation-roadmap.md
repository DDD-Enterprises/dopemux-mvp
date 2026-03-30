---
id: UI-IMPLEMENTATION-ROADMAP
title: Ui Implementation Roadmap
type: explanation
owner: '@hu3mann'
last_review: '2025-10-17'
next_review: '2026-01-15'
author: '@hu3mann'
date: '2026-02-05'
prelude: Ui Implementation Roadmap (explanation) for dopemux documentation and developer
  workflows.
---
# Dopemux UI Implementation Roadmap

**Status**: Implementation plan based on Decision #15 (libtmux + Textual architecture)
**Foundation**: Builds on existing `scripts/ui/metamcp_status.py`
**Timeline**: 4 phases, ~2-3 weeks

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Dopemux UI Stack                         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 5: User Interface                                        │
│  ├─ Textual Dashboard (optional `dopemux tui`)                  │
│  ├─ Rich CLI Output (primary interface)                         │
│  └─ tmux Status Bar (always-on visual feedback)                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Plugin System                                         │
│  ├─ DopemuxPlugin (base class)                                  │
│  ├─ Hook Registry (event callbacks)                             │
│  └─ Plugin Manager (load/unload/lifecycle)                      │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Application Logic                                     │
│  ├─ DopemuxSession (lifecycle, layouts, templates)              │
│  ├─ DopemuxTheme (ADHD color schemes)                           │
│  └─ DopemuxNavigator (fuzzy search, switching)                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Event Bus                                             │
│  ├─ Session Events (created, destroyed, switched)               │
│  ├─ Pane Events (output, resize, focus)                         │
│  └─ ADHD Events (break_reminder, energy_change, focus_shift)    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: tmux Control                                          │
│  ├─ DopemuxCore (libtmux.Server wrapper)                        │
│  └─ libtmux ORM (Server→Session→Window→Pane)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: libtmux Foundation (Week 1, Days 1-3)

**Goal**: Refactor existing UI code to use libtmux instead of subprocess calls

### Task 1.1: Create DopemuxCore (4h)

**File**: `src/dopemux/core/dopemux_core.py`

```python
"""DopemuxCore - Central coordinator for tmux control and event management."""

import libtmux
from typing import Optional, Dict, List, Callable
from collections import defaultdict
from pathlib import Path
import asyncio

class DopemuxCore:
    """Core dopemux controller with libtmux integration and event bus."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.server = libtmux.Server()
        self.config_dir = config_dir or Path.home() / ".config/dopemux"
        self.hooks: Dict[str, List[Callable]] = defaultdict(list)
        self.plugins: List['DopemuxPlugin'] = []

    def get_or_create_session(self, name: str) -> libtmux.Session:
        """Get existing session or create new one."""
        try:
            return self.server.sessions.get(session_name=name)
        except Exception:
            return self.server.new_session(name)

    def emit(self, event: str, *args, **kwargs):
        """Emit event to all registered hooks."""
        for callback in self.hooks[event]:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Hook error for {event}: {e}")

    def on(self, event: str, callback: Callable):
        """Register event hook."""
        self.hooks[event].append(callback)

    def load_plugin(self, plugin_class):
        """Load and initialize a plugin."""
        plugin = plugin_class(self)
        self.plugins.append(plugin)
        self.emit("plugin_loaded", plugin)
```

### Task 1.2: Create DopemuxSession (4h)

**File**: `src/dopemux/core/dopemux_session.py`

```python
"""DopemuxSession - Session lifecycle and layout management."""

import libtmux
from typing import Optional, Dict, List
from datetime import datetime

class DopemuxSession:
    """Manages individual dopemux session with two-plane awareness."""

    def __init__(self, core: 'DopemuxCore', name: str):
        self.core = core
        self.name = name
        self.session = core.get_or_create_session(name)
        self.created_at = datetime.now()
        self.mode = "ACT"  # PLAN or ACT

    def create_two_plane_layout(self, mode: str = "PLAN"):
        """Create layout optimized for PLAN or ACT mode."""
        self.mode = mode

        if mode == "PLAN":
            return self._create_plan_layout()
        else:
            return self._create_act_layout()

    def _create_plan_layout(self):
        """PM Plane layout: Leantime + Task-Master + ConPort."""
        # Main window: Leantime dashboard
        main = self.session.windows[0]
        main.rename_window("pm-dashboard")

        # Split for Task-Master
        task_pane = main.split_window(vertical=True, percentage=40)
        task_pane.send_keys("dopemux task status", enter=True)

        # Split for ConPort queries
        conport_pane = task_pane.split_window(vertical=False, percentage=50)
        conport_pane.send_keys("# ConPort decision browser", enter=False)

        self.core.emit("session_created", self, mode="PLAN")

    def _create_act_layout(self):
        """Cognitive Plane layout: Editor + Tests + Serena + Logs."""
        main = self.session.windows[0]
        main.rename_window("code")

        # Editor pane (main)
        # Test runner pane (right, 30%)
        test_pane = main.split_window(vertical=True, percentage=30)
        test_pane.send_keys("pytest --watch", enter=True)

        # Logs pane (bottom of tests)
        log_pane = test_pane.split_window(vertical=False, percentage=50)
        log_pane.send_keys("tail -f logs/dopemux.log", enter=True)

        self.core.emit("session_created", self, mode="ACT")
```

### Task 1.3: Migrate metamcp_status.py (3h)

**File**: Update `scripts/ui/metamcp_status.py` to use DopemuxCore

```python
# BEFORE: subprocess calls
result = subprocess.run([
    'python', str(self.project_root / 'metamcp_simple_query.py'),
    'get_status'
], capture_output=True, text=True, timeout=3)

# AFTER: libtmux ORM
from dopemux.core import DopemuxCore

class MetaMCPStatusBar:
    def __init__(self):
        self.dopemux = DopemuxCore()
        self.current_session = self._detect_current_session()

    def _detect_current_session(self) -> Optional[libtmux.Session]:
        """Detect which tmux session we're running in."""
        tmux_var = os.getenv("TMUX")
        if tmux_var:
            # Parse session from TMUX variable
            session_name = self.dopemux.server.attached_session
            return session_name
        return None

    def get_session_info(self) -> Dict:
        """Get session info from libtmux instead of subprocess."""
        if not self.current_session:
            return self._get_fallback_status()

        return {
            'session_name': self.current_session.name,
            'windows': len(self.current_session.windows),
            'panes': sum(len(w.panes) for w in self.current_session.windows),
            'created_at': self.current_session.get('@created_at'),
            'mode': self.current_session.get('@dopemux_mode', 'ACT')
        }
```

### Task 1.4: Implement ADHD Theme System (5h)

**File**: `src/dopemux/themes/theme_manager.py`

```python
"""ADHD-optimized theme system with semantic colors."""

from typing import Dict, Optional
from pathlib import Path
import json

class DopemuxTheme:
    """Theme configuration with ADHD-friendly color schemes."""

    BUILTIN_THEMES = {
        "nord-adhd": {
            "name": "Nord ADHD",
            "description": "Calm blues and greens for focus",
            "colors": {
                "bg": "#2e3440",
                "fg": "#d8dee9",
                "bg_bright": "#3b4252",
                "fg_dim": "#4c566a",

                # Semantic ADHD colors
                "focus": "#88c0d0",          # Calm blue
                "hyperfocus": "#b48ead",     # Purple energy
                "scattered": "#d08770",      # Warm orange
                "break_needed": "#bf616a",   # Gentle red
                "success": "#a3be8c",        # Green completion
                "warning": "#ebcb8b",        # Yellow caution

                # Pane states
                "pane_active": "#88c0d0",
                "pane_inactive": "#4c566a",

                # Two-plane modes
                "mode_plan": "#d08770",      # Orange for planning
                "mode_act": "#a3be8c",       # Green for action
            },
            "tmux_options": {
                "window-style": "fg=#d8dee9,bg=#2e3440",
                "window-active-style": "fg=#eceff4,bg=#2e3440",
                "pane-border-style": "fg=#4c566a",
                "pane-active-border-style": "fg=#88c0d0,bold",
                "status-style": "fg=#d8dee9,bg=#3b4252",
            }
        },

        "dracula-adhd": {
            "name": "Dracula ADHD",
            "description": "High contrast for hyperfocus",
            "colors": {
                "bg": "#282a36",
                "fg": "#f8f8f2",
                "bg_bright": "#44475a",
                "fg_dim": "#6272a4",

                "focus": "#8be9fd",          # Cyan clarity
                "hyperfocus": "#bd93f9",     # Purple intensity
                "scattered": "#ffb86c",      # Orange warning
                "break_needed": "#ff5555",   # Red alert
                "success": "#50fa7b",        # Green win
                "warning": "#f1fa8c",        # Yellow attention

                "pane_active": "#bd93f9",
                "pane_inactive": "#6272a4",

                "mode_plan": "#ffb86c",
                "mode_act": "#50fa7b",
            },
            "tmux_options": {
                "window-style": "fg=#f8f8f2,bg=#282a36",
                "window-active-style": "fg=#ffffff,bg=#282a36",
                "pane-border-style": "fg=#6272a4",
                "pane-active-border-style": "fg=#bd93f9,bold",
                "status-style": "fg=#f8f8f2,bg=#44475a",
            }
        },

        "tokyo-night-adhd": {
            "name": "Tokyo Night ADHD",
            "description": "Gentle dark theme for late night coding",
            "colors": {
                "bg": "#1a1b26",
                "fg": "#c0caf5",
                "bg_bright": "#24283b",
                "fg_dim": "#565f89",

                "focus": "#7aa2f7",
                "hyperfocus": "#bb9af7",
                "scattered": "#ff9e64",
                "break_needed": "#f7768e",
                "success": "#9ece6a",
                "warning": "#e0af68",

                "pane_active": "#7aa2f7",
                "pane_inactive": "#565f89",

                "mode_plan": "#ff9e64",
                "mode_act": "#9ece6a",
            },
            "tmux_options": {
                "window-style": "fg=#c0caf5,bg=#1a1b26",
                "window-active-style": "fg=#ffffff,bg=#1a1b26",
                "pane-border-style": "fg=#565f89",
                "pane-active-border-style": "fg=#7aa2f7,bold",
                "status-style": "fg=#c0caf5,bg=#24283b",
            }
        }
    }

    def __init__(self, theme_name: str = "nord-adhd"):
        self.current_theme = self.BUILTIN_THEMES[theme_name]

    def apply_to_tmux(self, server: libtmux.Server):
        """Apply theme to tmux configuration."""
        options = self.current_theme["tmux_options"]
        for key, value in options.items():
            server.cmd("set", "-g", key, value)

    def get_color(self, role: str) -> str:
        """Get color for semantic role."""
        return self.current_theme["colors"].get(role, "#ffffff")
```

**Deliverables Phase 1**:
- ✅ DopemuxCore with libtmux integration
- ✅ DopemuxSession with two-plane layouts
- ✅ Updated metamcp_status.py using ORM
- ✅ ADHD theme system with 3 presets (Nord, Dracula, Tokyo Night)

## Phase 2: Plugin Architecture (Week 1, Days 4-5)

**Goal**: Enable extensibility through hook-based plugin system

### Task 2.1: DopemuxPlugin Base Class (3h)

**File**: `src/dopemux/plugins/base.py`

```python
"""Base plugin class for dopemux extensibility."""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from dopemux.core import DopemuxCore

class DopemuxPlugin:
    """Base class for all dopemux plugins."""

    # Plugin metadata
    name: str = "base_plugin"
    version: str = "0.1.0"
    description: str = "Base plugin"

    def __init__(self, dopemux: 'DopemuxCore'):
        self.dopemux = dopemux
        self.config = {}
        self.register_hooks()

    def register_hooks(self):
        """Override to register event hooks."""
        pass

    # Lifecycle hooks
    def on_load(self):
        """Called when plugin is loaded."""
        pass

    def on_unload(self):
        """Called when plugin is unloaded."""
        pass

    # Session hooks
    def on_session_created(self, session: 'DopemuxSession', **kwargs):
        """Called when new session is created."""
        pass

    def on_session_destroyed(self, session: 'DopemuxSession'):
        """Called when session is destroyed."""
        pass

    # Pane hooks
    def on_pane_output(self, pane: libtmux.Pane, output: str):
        """Called when pane produces output."""
        pass

    def on_pane_focus(self, pane: libtmux.Pane):
        """Called when pane receives focus."""
        pass

    # ADHD hooks
    def on_break_reminder(self, session: 'DopemuxSession', minutes: int):
        """Called when break reminder is triggered."""
        pass

    def on_energy_change(self, old_level: str, new_level: str):
        """Called when energy level changes."""
        pass
```

### Example Plugin: ADHD Break Reminder

**File**: `src/dopemux/plugins/adhd_breaks.py`

```python
"""ADHD break reminder plugin with gentle notifications."""

from dopemux.plugins.base import DopemuxPlugin
import asyncio
from datetime import datetime, timedelta

class ADHDBreakPlugin(DopemuxPlugin):
    name = "adhd_breaks"
    version = "1.0.0"
    description = "Gentle break reminders for ADHD focus management"

    def __init__(self, dopemux):
        self.break_intervals = [25, 50, 90]  # Pomodoro-style
        self.last_reminder = {}
        super().__init__(dopemux)

    def register_hooks(self):
        self.dopemux.on("session_created", self.start_break_monitor)
        self.dopemux.on("pane_output", self.reset_activity_timer)

    def start_break_monitor(self, session, **kwargs):
        """Start monitoring session for break reminders."""
        asyncio.create_task(self._monitor_session(session))

    async def _monitor_session(self, session):
        """Monitor session and send gentle break reminders."""
        start_time = datetime.now()

        while True:
            await asyncio.sleep(60)  # Check every minute

            elapsed = (datetime.now() - start_time).total_seconds() / 60

            for interval in self.break_intervals:
                if elapsed >= interval and session.name not in self.last_reminder:
                    self._send_break_reminder(session, int(elapsed))
                    self.last_reminder[session.name] = interval
                    break

    def _send_break_reminder(self, session, minutes: int):
        """Send gentle break reminder to session."""
        if minutes >= 90:
            icon = "🔴"
            message = f"You've been focused for {minutes} minutes. Time for a proper break! 🧘"
        elif minutes >= 50:
            icon = "🟡"
            message = f"{minutes} min session. Consider a quick break soon 🚶"
        else:
            icon = "🟢"
            message = f"{minutes} min - great focus! Short break recommended ☕"

        # Send tmux display-message
        session.session.cmd("display-message", f"{icon} {message}")

        # Emit event for other plugins
        self.dopemux.emit("break_reminder", session, minutes=minutes)
```

## Phase 3: Session Templates (Week 2, Days 1-3)

**Goal**: YAML-based session templates for reproducible two-plane workflows

### Task 3.1: Template Format Design

**File**: `~/.config/dopemux/templates/plan-mode.yaml`

```yaml
# PM Plane (PLAN mode) session template
name: "dopemux-plan-{project}"
mode: PLAN
description: "Project management and strategic planning layout"

before_script:
- "source .env"
- "dopemux profile switch planner"

windows:
- name: "pm-dashboard"
    layout: "main-horizontal"
    main_pane_height: 70
    panes:
- focus: true
        commands:
- "# Leantime Dashboard"
- "echo 'Opening Leantime at http://localhost:8080'"
- "open http://localhost:8080 || xdg-open http://localhost:8080"

- commands:
- "# Task-Master CLI"
- "dopemux task list --sprint current"

- name: "decisions"
    layout: "even-vertical"
    panes:
- commands:
- "# ConPort Decision Browser"
- "dopemux conport search --recent 10"

- commands:
- "# Knowledge Graph Query"
- "dopemux conport graph --visualize"

theme: "nord-adhd"
adhd_settings:
  break_reminders: true
  energy_aware: true
  progressive_disclosure: true
```

**File**: `~/.config/dopemux/templates/code-mode.yaml`

```yaml
# Cognitive Plane (ACT mode) session template
name: "dopemux-code-{project}"
mode: ACT
description: "Development and implementation layout"

before_script:
- "source venv/bin/activate"
- "dopemux profile switch developer"

windows:
- name: "editor"
    layout: "main-vertical"
    main_pane_width: 65
    panes:
- focus: true
        commands:
- "vim ."  # Or: code ., nvim ., etc.

- commands:
- "# Test Runner"
- "pytest --watch --failed-first"

- name: "serena-lsp"
    layout: "even-horizontal"
    panes:
- commands:
- "# Serena Code Intelligence"
- "dopemux serena navigate --interactive"

- commands:
- "# Application Logs"
- "tail -f logs/dopemux.log | grep -v DEBUG"

- name: "tools"
    layout: "tiled"
    panes:
- commands: ["git status"]
- commands: ["docker-compose logs -f"]
- commands: ["htop"]

theme: "dracula-adhd"
adhd_settings:
  break_reminders: true
  complexity_scoring: true
  focus_mode: true
```

### Task 3.2: Template Loader Implementation (6h)

**File**: `src/dopemux/templates/loader.py`

```python
"""Session template loader with Jinja2 support."""

import yaml
from jinja2 import Template
from pathlib import Path
from typing import Dict, Optional

class TemplateLoader:
    """Load and process dopemux session templates."""

    def __init__(self, config_dir: Path):
        self.template_dir = config_dir / "templates"
        self.template_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self, name: str, variables: Optional[Dict] = None) -> Dict:
        """Load template with variable substitution."""
        template_path = self.template_dir / f"{name}.yaml"

        if not template_path.exists():
            raise FileNotFoundError(f"Template {name} not found")

        # Read template file
        with open(template_path) as f:
            template_str = f.read()

        # Apply Jinja2 variables
        if variables:
            jinja_template = Template(template_str)
            template_str = jinja_template.render(**variables)

        # Parse YAML
        return yaml.safe_load(template_str)

    def apply_template(self, dopemux_session: 'DopemuxSession', template: Dict):
        """Apply template configuration to session."""
        # Set mode
        dopemux_session.mode = template.get("mode", "ACT")

        # Run before_script
        for command in template.get("before_script", []):
            # Execute in shell
            subprocess.run(command, shell=True)

        # Create windows
        for window_config in template.get("windows", []):
            self._create_window(dopemux_session.session, window_config)

        # Apply theme
        theme_name = template.get("theme", "nord-adhd")
        theme = DopemuxTheme(theme_name)
        theme.apply_to_tmux(dopemux_session.core.server)

        # Set ADHD settings
        adhd_config = template.get("adhd_settings", {})
        for key, value in adhd_config.items():
            dopemux_session.session.set_option(f"@adhd_{key}", str(value))

    def _create_window(self, session: libtmux.Session, config: Dict):
        """Create window from template configuration."""
        name = config["name"]
        layout = config.get("layout", "even-horizontal")

        # Create or get window
        window = session.new_window(window_name=name)

        # Create panes
        panes_config = config.get("panes", [])
        main_pane = window.panes[0]

        for i, pane_config in enumerate(panes_config):
            if i == 0:
                # Use existing main pane
                pane = main_pane
            else:
                # Split to create new pane
                vertical = layout in ["main-vertical", "even-vertical"]
                pane = window.split_window(vertical=vertical)

            # Execute commands
            for command in pane_config.get("commands", []):
                pane.send_keys(command, enter=True)

            # Set focus if specified
            if pane_config.get("focus", False):
                pane.select_pane()

        # Apply layout
        window.select_layout(layout)
```

## Phase 4: Textual Dashboard (Week 2-3)

**Goal**: Optional TUI for real-time session monitoring and F002 multi-session display

### Task 4.1: Basic Textual App (6h)

**File**: `src/dopemux/tui/dashboard.py`

```python
"""Textual TUI dashboard for dopemux monitoring."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Static, Log
from textual.containers import Container, Horizontal
from textual import events
import libtmux
import asyncio

class DopemuxDashboard(App):
    """Interactive TUI dashboard for dopemux sessions."""

    CSS = """
    #session-tree {
        width: 30%;
        dock: left;
        border: solid #88c0d0;
    }

    #pane-viewer {
        width: 70%;
        border: solid #a3be8c;
    }

    .session-focused {
        background: #2e3440;
        color: #88c0d0;
        text-style: bold;
    }

    .session-scattered {
        background: #2e3440;
        color: #d08770;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("s", "switch_session", "Switch Session"),
        ("n", "new_session", "New Session"),
    ]

    def __init__(self, dopemux_core: 'DopemuxCore'):
        super().__init__()
        self.dopemux = dopemux_core
        self.server = dopemux_core.server
        self.selected_session = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield Tree("Sessions", id="session-tree")
            yield Log(id="pane-viewer", highlight=True, markup=True)
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize dashboard on mount."""
        self.refresh_sessions()
        self.monitor_task = asyncio.create_task(self.monitor_tmux())

    def refresh_sessions(self):
        """Refresh session tree."""
        tree = self.query_one("#session-tree", Tree)
        tree.clear()

        for session in self.server.sessions:
            # Get ADHD state
            attention_state = session.get("@adhd_attention_state", "focused")

            # Style based on state
            if attention_state == "focused":
                style_class = "session-focused"
            else:
                style_class = "session-scattered"

            # Add session node
            session_node = tree.root.add(
                f"📂 {session.name} ({len(session.windows)} windows)",
                data={"type": "session", "obj": session}
            )
            session_node.add_class(style_class)

            # Add windows
            for window in session.windows:
                window_node = session_node.add(
                    f"🪟 {window.name} ({len(window.panes)} panes)",
                    data={"type": "window", "obj": window}
                )

                # Add panes
                for pane in window.panes:
                    pane_node = window_node.add(
                        f"⬛ Pane {pane.index}",
                        data={"type": "pane", "obj": pane}
                    )

    async def monitor_tmux(self):
        """Monitor tmux state changes in real-time."""
        while True:
            await asyncio.sleep(2)
            self.refresh_sessions()

    def action_refresh(self):
        """Refresh dashboard."""
        self.refresh_sessions()

    def action_switch_session(self):
        """Switch to selected session."""
        # Implementation for session switching
        pass

    def action_new_session(self):
        """Create new session from template."""
        # Implementation for session creation
        pass
```

### Task 4.2: F002 Multi-Session Display (4h)

Add to dashboard to show all active sessions across worktrees:

```python
class F002MultiSessionWidget(Static):
    """Display all active dopemux sessions (F002 spec)."""

    def compose(self) -> ComposeResult:
        yield Static("[bold]Active Sessions[/bold]")
        yield Static(id="session-list")

    async def on_mount(self):
        """Load session data from ConPort."""
        # Query ConPort for all active sessions
        sessions = await self.get_active_sessions()
        self.display_sessions(sessions)

    async def get_active_sessions(self):
        """Query ConPort for session data."""
        # Implementation using ConPort MCP
        return []

    def display_sessions(self, sessions):
        """Display session summary."""
        session_list = self.query_one("#session-list", Static)

        output = []
        for session in sessions:
            status_icon = "🟢" if session["status"] == "active" else "⏸️"
            output.append(
                f"{status_icon} {session['session_id']}: "
                f"{session['worktree_path']} ({session['branch']})"
            )

        session_list.update("\n".join(output))
```

## Success Criteria

**Phase 1 Complete When**:
- ✅ All tmux operations use libtmux instead of subprocess
- ✅ Three ADHD themes (Nord, Dracula, Tokyo Night) available and working
- ✅ DopemuxCore event bus functional
- ✅ metamcp_status.py using libtmux ORM

**Phase 2 Complete When**:
- ✅ Plugin system loads and executes plugins
- ✅ At least 2 example plugins working (ADHD breaks, git status)
- ✅ Hook system triggers events correctly

**Phase 3 Complete When**:
- ✅ Template loader parses and applies YAML configs
- ✅ Default templates for PLAN and ACT modes working
- ✅ Jinja2 variable substitution functional
- ✅ Sessions created from templates match specification

**Phase 4 Complete When**:
- ✅ Textual dashboard displays all sessions
- ✅ Real-time updates working (<2s refresh)
- ✅ F002 multi-session view integrated
- ✅ Navigation between sessions functional

## Next Steps

**Immediate (Today)**:
1. Create directory structure: `src/dopemux/{core,themes,plugins,templates,tui}/`
1. Implement DopemuxCore (Task 1.1)
1. Start migrating metamcp_status.py (Task 1.2)

**Tomorrow**:
1. Complete DopemuxSession with two-plane layouts
1. Implement theme system
1. Test end-to-end with existing scripts

**Week 1 Goal**: Phase 1 + Phase 2 complete (libtmux foundation + plugin system)

---

★ Insight ─────────────────────────────────────
The research validates dopemux's unique positioning:
combining mature Python tmux libraries with ADHD
optimizations creates a terminal productivity tool
that doesn't exist elsewhere. Key differentiators:
(1) Two-plane architecture (PM + Cognitive) via
templates; (2) ADHD-first design (energy-aware
layouts, break reminders, progressive disclosure);
(3) Plugin system for extensibility; (4) F002
multi-session support for parallel development.
─────────────────────────────────────────────────
