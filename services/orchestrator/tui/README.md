# Dopemux Orchestrator TUI

**Fully Interactive Multi-AI Coordination Interface**

## Features ✨

- **Multi-Instance Development**: Coordinate Claude, Gemini, and Grok in a single pane
- **Full Keyboard Interaction**: Command input, AI targeting, pane navigation
- **Visual Progress Tracking**: Real-time progress bars, task counters, break timers
- **ADHD-Optimized**: Color-coded status, energy level display, 25-min break reminders
- **Energy-Adaptive**: Integrates with ADHD Engine for cognitive load management

## Installation

```bash
cd /Users/hue/code/dopemux-mvp/services/orchestrator
pip install textual textual-dev
```

## Quick Start

```bash
# Launch the TUI
python -m tui.main

# Or from project root
python services/orchestrator/tui/main.py
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `@claude <cmd>` | Send command to Claude |
| `@gemini <cmd>` | Send command to Gemini |
| `@grok <cmd>` | Send command to Grok |
| `@all <cmd>` | Send to all AIs (parallel) |
| `Ctrl+1/2/3` | Focus specific pane |
| `Ctrl+R` | Refresh energy level |
| `?` | Show help |
| `q` | Quit (with confirmation) |

## UI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Dopemux Orchestrator TUI  │  Energy: 🟢 HIGH  │  Session: 18min │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│             │             │             │             │         │
│   Claude    │   Gemini    │    Grok     │  Progress   │ Status  │
│   Output    │   Output    │   Output    │   Tracker   │  Info   │
│             │             │             │             │         │
│ [Scrolling  │ [Scrolling  │ [Scrolling  │ ████░░░░░░  │ Tasks:  │
│  AI resp]   │  AI resp]   │  AI resp]   │ 40% (2/5)   │ 2 done  │
│             │             │             │             │ 1 active│
│             │             │             │ Break in:   │ 2 todo  │
│             │             │             │ 7 minutes   │         │
├─────────────┴─────────────┴─────────────┴─────────────┴─────────┤
│ Command: @claude analyze auth.py for security issues             │
│ [@claude @gemini @grok | Tab=switch | Ctrl+Enter=send | ?=help] │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture

### Layer 3: Interactive TUI (Textual Framework)
- `AIOutputPane`: Scrollable AI output with status indicators
- `ProgressTrackerPane`: Visual progress bars and break timers
- `StatusInfoPane`: Energy level, session duration, shortcuts
- `CommandInput`: Enhanced input with @mentions and history

### Layer 2: Command Router (TODO: Day 3)
- Route commands to `claude`, `gemini-cli`, `grok-cli`
- Parallel execution support for `@all` commands
- Response aggregation and display

### Layer 1: Tmux Control (✅ COMPLETE)
- `TmuxLayoutManager`: Energy-adaptive 2/3/4 pane layouts
- libtmux orchestration
- ConPort session persistence

## ADHD Optimizations

1. **Visual Progress Indicators**
   - Per-AI progress bars
   - Overall session progress
   - Task completion with ✅ animations
   - Time-based progress (e.g., "45% of 25min")

2. **Cognitive Load Reduction**
   - Max 4 panes (prevents overwhelm)
   - Color-coded status (green=ready, yellow=busy, red=error)
   - Whitespace for visual breathing room
   - Progressive disclosure (hide details by default)

3. **Energy Adaptation**
   - Query ADHD Engine every 5 minutes
   - Visual energy indicator (🔴/🟡/🟢)
   - Auto-adjust pane count when energy drops (TODO)

4. **Interrupt Recovery**
   - Auto-save state every 30 seconds (TODO: Day 6)
   - Quick restore on restart
   - Command history preserved per AI

## Implementation Status

### ✅ Completed (Days 1-2)
- [x] Day 1: TmuxLayoutManager with energy-adaptive layouts (17/17 tests passing)
- [x] Day 2.1: Textual framework installation
- [x] Day 2.2: Main TUI app shell with 4-pane layout
- [x] Day 2.3: Keyboard navigation and shortcuts
- [x] Day 2.4: Basic validation testing

### 🚧 In Progress
- [ ] Day 3: Command routing to actual AI CLIs
- [ ] Day 4: Progress tracking integration with ConPort

### 📋 Planned
- [ ] Days 5-7: Multi-AI orchestration, session persistence
- [ ] Days 8-10: Polish, ADHD features, integration testing

## Development

### Run in Dev Mode (with live reload)
```bash
textual run --dev services/orchestrator/tui/main.py
```

### Test Specific Features
```python
# Test AI pane output
from tui.main import AIOutputPane
pane = AIOutputPane("Claude")
pane.add_output("Test message")
```

### Debug Console
```bash
# Enable Textual devtools
textual console
# In another terminal
textual run services/orchestrator/tui/main.py
```

## Next Steps (Day 3)

1. **Command Routing Implementation**
   - Detect available AI CLIs (`claude`, `gemini-cli`, `grok-cli`)
   - Route commands via subprocess
   - Capture and display output in real-time
   - Handle errors gracefully

2. **CLI Integration**
   ```python
   async def execute_command(self, ai: str, command: str):
       cli_map = {
           "claude": ["claude", "code", "execute"],
           "gemini": ["gemini-cli", "--interactive"],
           "grok": ["grok-cli"]
       }
       # Run subprocess and stream output to pane
   ```

3. **Testing**
   - Unit tests for command parsing
   - Integration tests with mock AI responses
   - Performance testing (< 100ms UI updates)

## Troubleshooting

**TUI doesn't launch**:
```bash
# Check Textual installation
pip show textual

# Verify imports work
python -c "from textual.app import App; print('OK')"
```

**Import errors for TmuxLayoutManager**:
```bash
# Ensure parent directory is in Python path
export PYTHONPATH="/Users/hue/code/dopemux-mvp/services:$PYTHONPATH"
```

**Keyboard shortcuts not working**:
- Ensure terminal supports ANSI codes
- Try different terminal (iTerm2, Alacritty recommended)
- Check Textual logs: `textual console`

## Resources

- [Textual Documentation](https://textual.textualize.io/)
- [Textual Widget Guide](https://textual.textualize.io/widget_gallery/)
- [ADHD-Friendly UI Principles](../../docs/03-reference/adhd-theme-design-principles.md)
- [IP-005 Implementation Plan](../../docs/implementation-plans/05-ORCHESTRATOR-TUI.md)

## License

Part of Dopemux MVP - ADHD-Optimized Development Platform
