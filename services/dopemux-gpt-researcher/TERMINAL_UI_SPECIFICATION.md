# GPT-Researcher Terminal UI Specification

**Date**: September 28, 2025
**Status**: Brainstormed & Planned
**Priority**: Next Implementation Phase

## Executive Summary

Following successful completion of discrete ConPort and Context7 integrations, the next logical step is creating an ADHD-optimized terminal UI for real-time research monitoring. This document outlines 5 comprehensive approaches evaluated during our brainstorm session.

`★ ADHD-First Design Principles`
- **Progressive Disclosure**: Show essential info first, details on demand
- **Visual Clarity**: Color-coded status, clear typography, minimal cognitive load
- **Attention Management**: Gentle animations, break reminders, focus modes
- **Context Preservation**: Session persistence, resumable interfaces

## Option Analysis

### Option 1: Python Rich Dashboard ⭐ **RECOMMENDED**
**Technology Stack**: Python `rich` + `textual` libraries
**Integration**: Direct backend integration via WebSocket

**Architecture**:
```
┌─────────────────────────────────────────────────┐
│  Terminal Dashboard (Rich/Textual)             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Progress    │ │ Current     │ │ Attention   ││
│  │ Panel       │ │ Question    │ │ Monitor     ││
│  └─────────────┘ └─────────────┘ └─────────────┘│
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │ Sources     │ │ Session     │ │ Break       ││
│  │ Explorer    │ │ Info        │ │ Timer       ││
│  └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│          FastAPI + WebSocket Backend           │
└─────────────────────────────────────────────────┘
```

**ADHD Optimizations**:
- **Color Coding**: Green (active), Yellow (waiting), Red (blocked), Blue (completed)
- **Progressive Disclosure**: Expandable/collapsible sections for sources and details
- **Gentle Animations**: Smooth progress bars, pulsing for active tasks
- **Break Management**: Visual countdown with sound alerts every 25 minutes
- **Focus Mode**: Hide non-essential panels during deep research
- **Quick Keys**: Single-key shortcuts for common actions

**Implementation Files**:
```
backend/ui/
├── terminal_dashboard.py       # Main dashboard application
├── components/
│   ├── progress_panel.py      # Research progress visualization
│   ├── question_panel.py      # Current question display
│   ├── sources_panel.py       # Source tree explorer
│   ├── attention_tracker.py   # ADHD metrics & break timer
│   └── session_panel.py       # Session persistence info
├── layouts/
│   ├── default_layout.py      # Standard dashboard layout
│   └── focus_layout.py        # Minimal focus mode layout
└── utils/
    ├── websocket_client.py    # API connectivity
    └── adhd_helpers.py        # ADHD-specific utilities
```

**Advantages**:
- ✅ Direct Python integration - no language barriers
- ✅ Rich library is mature and battle-tested
- ✅ Reuses existing WebSocket infrastructure
- ✅ Lower complexity than React alternatives
- ✅ Can evolve to hybrid approach later

**Disadvantages**:
- ❌ Python TUI ecosystem smaller than Node.js
- ❌ Less advanced than React Ink for complex layouts

### Option 2: React Ink TUI Client
**Technology Stack**: React + Ink + TypeScript
**Integration**: Standalone Node.js client via REST/WebSocket

**Architecture**:
```
┌─────────────────────────────────────────────────┐
│         React Ink Application                   │
│  <ResearchDashboard>                           │
│    <TaskProgress />                            │
│    <QuestionList />                            │
│    <SourceExplorer />                          │
│    <AttentionMonitor />                        │
│  </ResearchDashboard>                         │
└─────────────────────────────────────────────────┘
                    │ HTTP/WS
                    ▼
┌─────────────────────────────────────────────────┐
│          Python FastAPI Backend                │
└─────────────────────────────────────────────────┘
```

**ADHD Features**:
- **Component-Based**: Familiar React patterns for UI developers
- **State Management**: Zustand for predictable state updates
- **Keyboard Navigation**: Arrow keys, Tab, Enter for accessibility
- **Responsive Layout**: Flexbox-based panels that adapt to terminal size
- **Hot Reloading**: Rapid iteration during development

**Implementation Structure**:
```
services/dopemux-gpt-researcher/tui/
├── package.json                    # Node.js dependencies
├── src/
│   ├── App.tsx                    # Main application
│   ├── components/
│   │   ├── ResearchDashboard.tsx  # Container component
│   │   ├── TaskProgress.tsx       # Progress visualization
│   │   ├── QuestionList.tsx       # Research questions
│   │   ├── SourceExplorer.tsx     # Source tree
│   │   └── AttentionMonitor.tsx   # ADHD metrics
│   ├── stores/
│   │   └── researchStore.ts       # Zustand state
│   ├── hooks/
│   │   ├── useWebSocket.ts        # WebSocket connection
│   │   └── useADHDTimer.ts        # Break management
│   └── utils/
│       └── apiClient.ts           # HTTP client
└── bin/
    └── gptr-ui                    # Executable script
```

**Advantages**:
- ✅ Excellent developer experience for React developers
- ✅ Advanced layout capabilities with Yoga/Flexbox
- ✅ Rich ecosystem of TUI components
- ✅ Hot reloading for rapid development

**Disadvantages**:
- ❌ Additional Node.js dependency
- ❌ More complex deployment (2 runtime environments)
- ❌ Higher memory usage than Python alternatives

### Option 3: Browser-based Real-time Dashboard
**Technology Stack**: HTML/CSS/JS + WebSocket
**Integration**: Static files served by FastAPI

**Features**:
- **Real-time Updates**: WebSocket connection for live data
- **Responsive Design**: Works on desktop and mobile
- **ADHD-Optimized UI**: Dark mode, large text, clear indicators
- **Notification System**: Browser notifications for breaks

**Implementation**:
```
backend/static/
├── dashboard.html              # Main dashboard page
├── css/
│   ├── dashboard.css          # ADHD-friendly styling
│   └── dark-theme.css         # Dark mode theme
├── js/
│   ├── dashboard.js           # Main application logic
│   ├── websocket-client.js    # WebSocket handling
│   └── adhd-helpers.js        # Break timers, notifications
└── assets/
    ├── sounds/                # Gentle notification sounds
    └── icons/                 # Status indicators
```

**Advantages**:
- ✅ Cross-platform compatibility
- ✅ Rich CSS styling capabilities
- ✅ Browser notification API
- ✅ Easy to share and demo

**Disadvantages**:
- ❌ Not truly "terminal" UI
- ❌ Requires browser to be open
- ❌ Less integrated feel

### Option 4: Lightweight CLI Progress Viewer
**Technology Stack**: Python Click + Rich
**Integration**: HTTP polling to existing API

**Usage**:
```bash
# Watch specific research task
gptr-watch c887880a-5b49-4118-80ce-cf1a045fd4e8

# Watch latest task
gptr-watch --latest

# Minimal mode (just progress bar)
gptr-watch --minimal <task-id>
```

**Features**:
- **Single Purpose**: Focus only on progress monitoring
- **Minimal Resource Usage**: Lightweight HTTP polling
- **Clear Status**: Simple progress bar and ETA
- **ADHD-Friendly**: No visual overwhelm

**Implementation**:
```
backend/cli/
├── watcher.py                  # Main CLI application
├── formatters.py              # Output formatting
└── api_client.py              # HTTP client for API
```

**Advantages**:
- ✅ Extremely lightweight
- ✅ Single-purpose tool (no cognitive overwhelm)
- ✅ Works with existing API
- ✅ Easy to integrate into scripts

**Disadvantages**:
- ❌ Limited functionality
- ❌ No real-time updates (polling only)

### Option 5: Hybrid Multi-Tool Approach
**Strategy**: Combine multiple tools for different use cases

**Tool Suite**:
1. **Rich startup messages** - Beautiful API server initialization
2. **Click CLI commands** - `gptr create`, `gptr status`, `gptr cancel`
3. **Simple progress viewer** - Lightweight monitoring
4. **Full dashboard** - When detailed monitoring needed

**Implementation Strategy**:
```
Phase 1: Basic CLI Tools (Week 1)
  ├── Rich startup messages
  ├── Click command suite
  └── Simple progress viewer

Phase 2: Dashboard (Week 2-3)
  ├── Python Rich dashboard
  └── Integration with CLI tools

Phase 3: Advanced Features (Week 4+)
  ├── React Ink alternative
  └── Browser dashboard option
```

## Recommended Implementation Path

### Phase 1: Python Rich Dashboard (Immediate)
**Rationale**:
- Direct integration with existing Python backend
- Rich library provides excellent ADHD-friendly features
- Lower complexity than React alternatives
- Can evolve incrementally

**Key Components**:
1. **Main Dashboard** (`terminal_dashboard.py`)
   - Multi-panel layout using Rich/Textual
   - WebSocket connection to existing API
   - Keyboard shortcuts for navigation

2. **Progress Visualization** (`progress_panel.py`)
   - Real-time progress bars for each research question
   - Color-coded status indicators
   - Estimated time remaining

3. **Attention Tracker** (`attention_tracker.py`)
   - Break timer with visual countdown
   - Focus session tracking
   - Gentle notification system

4. **Source Explorer** (`sources_panel.py`)
   - Collapsible tree view of discovered sources
   - Quick preview of source content
   - Relevance scoring visualization

### ADHD-Specific Features

#### Visual Design
- **Color Palette**: Consistent color coding across all panels
  - 🟢 Green: Active/successful states
  - 🟡 Yellow: Waiting/in-progress states
  - 🔴 Red: Error/blocked states
  - 🔵 Blue: Completed states
  - ⚪ Gray: Inactive/background elements

#### Interaction Patterns
- **Progressive Disclosure**: Start with essential info, expand on demand
- **Single-Key Actions**: `q` (quit), `r` (refresh), `f` (focus mode), `b` (break)
- **Attention Management**: Automatic focus mode after 15 minutes of activity
- **Context Preservation**: Save dashboard state between sessions

#### Break Management
- **Pomodoro Integration**: 25-minute focus periods with 5-minute breaks
- **Gentle Reminders**: Soft visual/audio cues (no jarring interruptions)
- **Break Activities**: Suggested micro-activities during breaks
- **Hyperfocus Protection**: Warnings after 90+ minutes of continuous work

## Technical Specifications

### Dependencies
```toml
# Additional dependencies for terminal UI
rich = "^13.6.0"
textual = "^0.38.0"
click = "^8.1.7"
asyncclick = "^8.1.3.4"
websocket-client = "^1.6.4"
```

### Configuration
```python
# ADHD-optimized default settings
ADHD_CONFIG = {
    "break_interval_minutes": 25,
    "break_duration_minutes": 5,
    "hyperfocus_warning_minutes": 90,
    "notification_style": "gentle",
    "color_scheme": "high_contrast",
    "animation_speed": "slow",
    "auto_focus_mode": True,
    "sound_notifications": True
}
```

### WebSocket Integration
- Reuse existing WebSocket infrastructure from FastAPI backend
- Real-time updates for progress, status changes, and new sources
- Efficient binary protocol for minimal bandwidth usage

## Success Metrics

### User Experience Goals
- **Time to Information**: Key research status visible within 2 seconds
- **Cognitive Load**: Maximum 3 pieces of information visible at once
- **Interruption Recovery**: Return to previous state within 5 seconds
- **Break Compliance**: 80% adherence to break recommendations

### Technical Goals
- **Latency**: <100ms response to user interactions
- **Memory Usage**: <50MB for dashboard application
- **CPU Usage**: <5% during normal operation
- **Network**: <1KB/s sustained WebSocket traffic

## Future Enhancements

### Advanced ADHD Features
- **Attention Pattern Learning**: Adapt break timing based on user patterns
- **Context Switching Support**: Multiple research task monitoring
- **Distraction Filtering**: Hide low-priority information during focus periods
- **Progress Gamification**: Achievement system for research milestones

### Integration Opportunities
- **Calendar Integration**: Schedule research sessions around meetings
- **Notification Sync**: Coordinate with system notifications
- **Voice Commands**: Hands-free status checking
- **Wearable Integration**: Break reminders on smartwatch

## Implementation Timeline

### Week 1: Foundation
- [ ] Set up basic Rich/Textual dashboard structure
- [ ] Implement WebSocket client connectivity
- [ ] Create core progress visualization
- [ ] Basic ADHD break timer

### Week 2: Enhanced Features
- [ ] Source explorer with tree view
- [ ] Attention tracking and metrics
- [ ] Focus mode implementation
- [ ] Keyboard shortcut system

### Week 3: Polish & Testing
- [ ] ADHD user testing and feedback
- [ ] Performance optimization
- [ ] Documentation and deployment
- [ ] Integration with existing tools

### Week 4+: Advanced Features
- [ ] Multi-task monitoring
- [ ] Advanced break management
- [ ] React Ink alternative (optional)
- [ ] Browser dashboard option

---

**Next Steps**: Implement Phase 1 Python Rich Dashboard with core ADHD optimizations