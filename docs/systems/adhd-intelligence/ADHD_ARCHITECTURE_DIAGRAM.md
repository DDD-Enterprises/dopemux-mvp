---
id: ADHD_ARCHITECTURE_DIAGRAM
title: Adhd_Architecture_Diagram
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# ADHD Intelligence Stack - Complete Architecture

**Date**: 2025-10-25
**Version**: 1.0 (Production)
**Services**: 6 microservices, 7 MCP servers

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER ACTIVITY                                 │
│  - Switches apps (Claude Code ↔ Chrome ↔ Terminal)                 │
│  - Saves files (auth.py, config.ts)                                 │
│  - Makes commits (git commit -m "...")                              │
└─────────────────────────────────────────────────────────────────────┘
           │           │              │
           │           │              │
      ┌────┘           │              └─────┐
      │                │                    │
      v                v                    v
┌──────────┐    ┌──────────┐      ┌──────────────┐
│Workspace │    │   File   │      │  Git Hook    │
│ Watcher  │    │ Activity │      │post-commit   │
│(5s poll) │    │ Checker  │      │              │
└──────────┘    └──────────┘      └──────────────┘
      │                │                    │
      │                │                    │
      └────────┬───────┴────────────────────┘
               │
               v
    ┌─────────────────────────┐
    │   Redis Streams         │
    │   (dopemux:events)      │
    │                         │
    │  Events:                │
    │  - workspace.switched   │
    │  - code.committed       │
    │  - code.complexity.high │
    └─────────────────────────┘
               │
        ┌──────┴──────────┐
        │                 │
        v                 v
┌──────────────┐   ┌──────────────┐
│  Activity    │   │   F-NEW-8    │
│  Capture     │   │Break Suggester│
│(Docker 8096) │   │(background)  │
└──────────────┘   └──────────────┘
        │                 │
        │  Sessions,      │  Intelligent
        │  Interruptions  │  Correlation
        │                 │
        └─────┬───────────┘
              │
              v
    ┌─────────────────┐
    │  ADHD Engine    │
    │(background 8095)│
    │                 │
    │ 6/6 Monitors:   │
    │ - Energy        │
    │ - Attention     │
    │ - Cognitive Load│
    │ - Break Timing  │
    │ - Hyperfocus    │
    │ - Context Switch│
    └─────────────────┘
              │
        ┌─────┴──────┐
        │            │
        v            v
┌──────────────┐  ┌─────────────┐
│ADHD Notifier │  │  Dashboard  │
│(background)  │  │(port 8097)  │
│              │  │             │
│Receives:     │  │Web UI:      │
│- Time checks │  │- Metrics    │
│- F-NEW-8     │  │- Charts     │
│  suggestions │  │- Tasks      │
│              │  │             │
│Delivers:     │  └─────────────┘
│- Desktop     │
│  notifications│
│- Voice TTS   │
└──────────────┘
        │
        v
┌─────────────────┐
│   Statusline    │
│📚🧠🔬📊🔎🖥️🎯│
│🧠 ⚡= 👁️●    │
└─────────────────┘
```

---

## Service Details

### 1. Workspace Watcher (Background)
**Purpose**: Automatic app/workspace monitoring
**Technology**: Python, osascript (macOS), wmctrl (Linux)
**Polling**: Every 5 seconds
**Detects**:
- Active application changes
- Workspace switches
- File modifications (last 30s)

**Events Emitted**:
- workspace.switched

### 2. Activity Capture (Docker, port 8096)
**Purpose**: Event consumer & session aggregator
**Technology**: FastAPI, Redis Streams, aiohttp
**Consumes**:
- workspace.switched
- code.committed

**Functions**:
- Track session start/end
- Count interruptions
- Aggregate 5-minute windows
- Log activities to ADHD Engine

**Endpoints**:
- GET /health
- GET /metrics

### 3. ADHD Engine (Background, port 8095)
**Purpose**: Energy/attention assessment
**Technology**: FastAPI, Redis, ConPort stub
**Features**:
- 6 background monitors
- User profile persistence
- Activity logging API
- State assessment

**Endpoints**:
- GET /health
- GET /api/v1/statusline/{user_id} (batched)
- GET /api/v1/energy-level/{user_id}
- GET /api/v1/attention-state/{user_id}
- POST /api/v1/user-profile
- PUT /api/v1/activity/{user_id}
- POST /api/v1/assess-task

### 4. F-NEW-8 Break Suggester (Background)
**Purpose**: Intelligent break detection via event correlation
**Technology**: Python, Redis Streams, asyncio
**Monitors**:
- code.complexity.high (from Serena)
- cognitive.state.change (from ADHD Engine)
- session duration (from Activity Capture)

**Logic**:
- Correlates 3+ complexity events in 25-min window
- Checks cognitive decline (low energy, scattered attention)
- Evaluates time thresholds
- Generates priority: CRITICAL/HIGH/MEDIUM

**Events Emitted**:
- break.suggestion

### 5. ADHD Notifier (Background)
**Purpose**: Multi-modal notification delivery
**Technology**: Python, osascript (macOS), notify-send (Linux)
**Sources**:
- Activity Capture metrics (polling 60s)
- F-NEW-8 break suggestions (event subscription)

**Delivers**:
- Desktop notifications
- Voice TTS (macOS `say` command)
- Anti-spam protection (10/15 min intervals)

**Notification Types**:
- Break reminder (25+ min)
- Urgent break (45+ min)
- Hyperfocus alert (60+ min)
- F-NEW-8 intelligent suggestions

### 6. Dashboard (Optional, port 8097)
**Purpose**: Web UI for metrics visualization
**Technology**: FastAPI, HTML/CSS/JavaScript
**Features**:
- Real-time metrics display
- Session history
- ADHD state visualization
- Task recommendations
- Auto-refresh (5s)

**Endpoints**:
- GET / (HTML dashboard)
- GET /api/metrics
- GET /api/adhd-state
- GET /api/sessions/today
- GET /api/analytics/summary

---

## Data Flow

### Session Tracking Flow:
```
1. User switches to Claude Code
   → Workspace Watcher detects (osascript)
   → Emits: workspace.switched
   → Activity Capture receives
   → Starts session tracking

2. User codes for 10 minutes
   → Activity Capture aggregates
   → Logs to ADHD Engine
   → ADHD Engine updates energy/attention

3. User codes for 25 minutes
   → ADHD Notifier checks Activity Capture metrics
   → Detects 25+ min session
   → Sends notification + voice: "Time for a break"

4. Meanwhile: High complexity detected
   → Serena emits: code.complexity.high
   → F-NEW-8 receives and correlates
   → Evaluates: 3+ events + 25 min + scattered attention
   → Emits: break.suggestion (HIGH priority)
   → ADHD Notifier receives
   → Sends intelligent notification: "High complexity work for 30 min - break recommended"

5. User switches to Chrome
   → Workspace Watcher detects
   → Activity Capture ends session
   → Logs final activity with interruption count

6. Statusline updates
   → Queries ADHD Engine /api/v1/statusline/hue
   → Displays: 🧠 ⚡= 👁️●
```

---

## Event Types

### Published To Redis (dopemux:events):

**workspace.switched** (from Workspace Watcher):
```json
{
  "type": "workspace.switched",
  "data": {
    "from_workspace": "/Users/hue/other-project",
    "to_workspace": "/Users/hue/code/dopemux-mvp",
    "from_app": "Chrome",
    "to_app": "Claude Code",
    "switch_type": "automatic",
    "adhd_context_capture": {
      "file_activity": {
        "has_recent_activity": true,
        "files_modified": 3,
        "seconds_since_last_save": 15
      }
    }
  },
  "source": "workspace-watcher"
}
```

**code.committed** (from Git Hook):
```json
{
  "type": "code.committed",
  "data": {
    "commit_hash": "9abb5a36",
    "files_changed": 4,
    "lines_added": 250,
    "lines_removed": 30,
    "complexity": 0.28,
    "activity_signal": "high_productivity"
  },
  "source": "git-hook"
}
```

**break.suggestion** (from F-NEW-8):
```json
{
  "type": "break.suggestion",
  "data": {
    "priority": "high",
    "message": "High complexity work for 30 min - break recommended",
    "suggested_duration": 5,
    "reason": "Maintain productivity and prevent cognitive fatigue",
    "triggered_by": ["high_complexity", "scattered_attention"]
  },
  "source": "break-suggester"
}
```

---

## Technology Stack

### Languages:
- Python 3.11+ (all services)
- Bash (startup scripts, git hooks, statusline)
- HTML/CSS/JavaScript (dashboard)

### Frameworks:
- FastAPI (Activity Capture, ADHD Engine, Dashboard)
- asyncio (async/await throughout)

### Infrastructure:
- Docker (Activity Capture)
- Redis (event streams, state persistence)
- PostgreSQL AGE (ConPort, future)
- Qdrant (semantic search)

### External Tools:
- osascript (macOS app detection, notifications, TTS)
- wmctrl/xdotool (Linux app detection)
- notify-send (Linux notifications)

---

## Deployment Architecture

### Docker Containers (15 total):
- Activity Capture
- 12 MCP Servers
- PostgreSQL
- Redis
- Qdrant

### Background Processes (4 total):
- ADHD Engine
- Workspace Watcher
- ADHD Notifier
- F-NEW-8 Break Suggester

### Optional Services:
- Dashboard (manual start)

---

## Network Topology

```
localhost:3002  - Context7 MCP
localhost:3003  - Zen MCP
localhost:3006  - Serena MCP
localhost:3012  - Desktop-Commander MCP
localhost:3014  - Task Orchestrator
localhost:3016  - DopeconBridge
localhost:5455  - PostgreSQL AGE
localhost:6333  - Qdrant
localhost:6379  - Redis
localhost:8095  - ADHD Engine
localhost:8096  - Activity Capture
localhost:8097  - Dashboard (optional)
```

---

## State Management

### Redis (3 databases):
- DB 0: MCP server cache
- DB 1: Activity Capture cache (future)
- DB 6: ADHD Engine state
  - Keys: `adhd:profile:{user_id}`
  - Data: User profiles (JSON)
  - TTL: No expiration (persistent)

### In-Memory:
- Activity Capture: Current session state
- ADHD Engine: Current energy/attention/accommodations
- Workspace Watcher: Current app/workspace
- F-NEW-8: Cognitive load window (25-min sliding)

---

## Integration Points

### Workspace Watcher → Activity Capture:
- Protocol: Redis Streams
- Event: workspace.switched
- Frequency: On app change (5s polling)

### Activity Capture → ADHD Engine:
- Protocol: HTTP REST
- Endpoint: PUT /api/v1/activity/{user_id}
- Frequency: Every 5 min OR session end

### F-NEW-8 → ADHD Notifier:
- Protocol: Redis Streams
- Event: break.suggestion
- Frequency: When correlation triggers

### Statusline → ADHD Engine:
- Protocol: HTTP REST
- Endpoint: GET /api/v1/statusline/{user_id}
- Frequency: Every keystroke (with 0.4s timeout)

---

## Performance Characteristics

### Latency:
- Workspace detection: ~5s max (polling interval)
- Event processing: <100ms (Activity Capture)
- ADHD assessment: <50ms (engine monitors)
- Statusline update: ~154ms total (batched endpoint)
- Break notification: ~60s max (notifier polling)
- F-NEW-8 correlation: <200ms

### Throughput:
- Event processing: 10 events/second (Activity Capture)
- Workspace polling: 12 checks/minute
- ADHD monitoring: 1 check/minute (break), 1/3min (attention), 1/5min (energy)

### Resource Usage:
- Memory: ~500MB total (all services)
- CPU: <5% (all services combined)
- Network: Minimal (localhost only)
- Disk: Logs only (~10MB/day)

---

## ADHD Optimization Features

### Progressive Disclosure:
- Statusline: Essential info only (7 MCP + ADHD state)
- Dashboard: Expandable sections
- Notifications: Dismissible

### Anti-Overwhelm:
- Max result limits (dynamic 5-40 based on attention)
- Anti-spam notifications (10/15 min intervals)
- Gentle language mode
- Celebration of breaks

### Graceful Degradation:
- All services work independently
- Fallbacks if dependencies unavailable
- No blocking failures
- Silent error handling (git hooks, etc.)

---

## Security

### Network:
- All localhost only (no external exposure)
- CORS restricted to whitelisted origins
- Optional API key auth (Dashboard)

### Data:
- No sensitive data stored
- User profiles: ADHD preferences only
- Sessions: Duration/interruptions only
- No code content logged

### Process Isolation:
- Docker container: Activity Capture
- Background processes: Separate user space
- No root privileges required

---

## Monitoring

### Health Checks:
- Activity Capture: GET /health (every 30s)
- ADHD Engine: Port check (statusline, every keystroke)
- Dashboard: GET /health (on access)

### Logs:
- /tmp/workspace_watcher.log
- /tmp/adhd_engine.log
- /tmp/adhd_notifier.log
- /tmp/break_suggester.log
- Docker logs: dopemux-activity-capture

### Metrics:
- Activity Capture: GET /metrics
- Dashboard: GET /api/analytics/summary
- Statusline: Visual indicators

---

## ADHD Benefits - Complete Flow

### Morning:
```
09:00 - Start services (./scripts/start-all.sh)
09:01 - Switch to Claude Code
        → Workspace Watcher detects
        → Session starts automatically
        → Statusline shows: 🧠 ⚡↑ 👁️●
```

### Working:
```
09:30 - Coding for 30 minutes
        → F-NEW-8 detects: 4 complexity events + 30 min
        → Correlates with: Scattered attention
        → Generates: HIGH priority suggestion
        → ADHD Notifier delivers:
          - Desktop: "High complexity work for 30 min"
          - Voice: "Time for a break. You have been focused for 30 minutes"
```

### Break Time:
```
09:35 - Take 5-minute break
        → Switch to browser
        → Session ends
        → Interruption counted
        → Break logged
```

### Back to Work:
```
09:40 - Return to coding
        → New session starts
        → Statusline updates
        → Cycle repeats
```

### End of Day:
```
17:00 - Generate report
        → cd services/adhd-notifier
        → python daily_reporter.py
        → See: 8 sessions, 7 activities, 6 breaks, 1 hyperfocus event
```

---

## The Magic: Zero Manual Tracking

**You just work. The system handles everything.**

No timers. No logging. No tracking.
Just automatic ADHD support in the background.

**That's the power of this architecture!**
