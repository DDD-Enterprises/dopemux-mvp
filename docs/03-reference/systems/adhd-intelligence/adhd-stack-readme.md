---
id: ADHD_STACK_README
title: Adhd_Stack_Readme
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# ADHD Intelligence Stack - Complete Guide

**Status**: Production Ready
**Version**: 1.0.0
**Date**: 2025-10-24

## Overview

Complete ADHD intelligence infrastructure providing automatic activity tracking, energy/attention monitoring, break reminders, and productivity insights for neurodivergent developers.

**Zero manual tracking - everything happens automatically!**

---

## Features

### Automatic Activity Tracking
- **Workspace switch detection** - Monitors active app every 5 seconds
- **Session tracking** - Automatic start/end when switching apps
- **Git commit tracking** - Post-commit hook logs completed work
- **File activity detection** - Identifies active coding vs idle time
- **Interruption counting** - Tracks context switches

### ADHD Support
- **Energy/attention assessment** - Real-time cognitive state monitoring
- **Break reminders** - Visual + voice notifications at 25+ minutes
- **Hyperfocus protection** - Urgent alerts at 60+ minutes
- **Smart task recommendations** - "Should I work on this now?"
- **Daily reports** - Track progress and patterns

### Real-Time Statusline
```
dopemux-mvp main | 📚🧠🔬📊🔎🖥️🎯 | 🧠 ⚡= 👁️● | 215K/1000K | Sonnet
```
- 7 MCP server health indicators
- ADHD Engine status
- Energy level (⚡↑/=/↓)
- Attention state (👁️●/🌀/💥)

---

## Architecture

```
[USER ACTIVITY]
     |
     |-- App Switching ----> Workspace Watcher (5s polling)
     |-- File Saves -------> File Activity Checker
     |-- Git Commits ------> Post-commit hook
     |
     v
Redis Streams (dopemux:events)
     |
     v
Activity Capture (Docker port 8096)
     |-- Consumes events
     |-- Tracks sessions
     |-- Aggregates 5-min windows
     |
     v
ADHD Engine (background port 8095)
     |-- 6/6 monitors active
     |-- Assesses energy/attention
     |-- Stores profiles in Redis
     |
     |-- ADHD Notifier (polls every 60s)
     |   |-- Break reminders
     |   |-- Hyperfocus alerts
     |   |-- Voice notifications
     |   v
     Desktop Notifications + TTS
     |
     |-- Dashboard (optional port 8097)
     |   |-- Web UI
     |   |-- REST API
     |   |-- Task recommendations
     |
     v
Statusline: 📚🧠🔬📊🔎🖥️🎯 | 🧠 ⚡= 👁️●
```

---

## Services

### 1. Activity Capture (Docker, port 8096)
**Purpose**: Event consumer and session aggregator
**Location**: `services/activity-capture/`
**Deployment**: Docker container

**Features**:
- Redis Streams consumer
- Session start/end detection
- 5-minute aggregation windows
- ADHD Engine HTTP client

**Endpoints**:
- `GET /health` - Service health
- `GET /metrics` - Activity metrics

### 2. ADHD Engine (Background, port 8095)
**Purpose**: Energy/attention assessment and monitoring
**Location**: `services/adhd_engine/`
**Deployment**: Background Python process

**Features**:
- 6 background monitors (energy, attention, cognitive load, breaks, hyperfocus, context)
- User profile persistence (Redis)
- Activity API for logging
- ML predictions (optional)

**Endpoints**:
- `GET /health` - Engine health
- `GET /api/v1/energy-level/{user_id}` - Current energy
- `GET /api/v1/attention-state/{user_id}` - Current attention
- `POST /api/v1/user-profile` - Create/update profile
- `PUT /api/v1/activity/{user_id}` - Log activity
- `POST /api/v1/assess-task` - Task suitability assessment

### 3. Workspace Watcher (Background)
**Purpose**: Automatic workspace switch detection
**Location**: `services/workspace-watcher/`
**Deployment**: Background Python process

**Features**:
- Polls active app every 5 seconds (macOS: osascript, Linux: wmctrl)
- Maps app to workspace path (configurable)
- File modification detection
- Event emission to Redis

**Configuration**: `config.json` - App to workspace mappings

### 4. ADHD Notifier (Background)
**Purpose**: Break reminders and hyperfocus alerts
**Location**: `services/adhd-notifier/`
**Deployment**: Background Python process

**Features**:
- Desktop notifications (visual)
- Voice notifications (macOS TTS)
- Break detection (25+ min)
- Hyperfocus detection (60+ min)
- Anti-spam protection

### 5. ADHD Dashboard (Optional, port 8097)
**Purpose**: Web UI for ADHD metrics visualization
**Location**: `services/adhd-dashboard/`
**Deployment**: Manual start (on-demand)

**Features**:
- Real-time metrics display
- Session history
- ADHD state visualization
- Smart task recommendations
- REST API

**Endpoints**:
- `GET /` - HTML dashboard
- `GET /api/metrics` - Activity metrics
- `GET /api/adhd-state` - ADHD state
- `GET /api/sessions/today` - Today's sessions
- `GET /api/analytics/summary` - Complete summary

---

## Installation & Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Redis (via Docker)
- Git

### Quick Start

```bash
# 1. Start all services
./scripts/start-all.sh

# 2. Install git hooks (one-time)
./scripts/install-git-hooks.sh

# 3. (Optional) Start dashboard
cd services/adhd-dashboard
python backend.py &

# 4. Verify statusline shows ADHD state
# Your prompt should show: 🧠 ⚡= 👁️●
```

---

## Usage

### Automatic Tracking (Zero Manual Work)

**Just work normally!**
1. Switch to Claude Code/VS Code → Session starts
2. Code for 10 minutes → Activity logged
3. Receive notification → "Time for a Break" (25 min)
4. Switch to Chrome → Session ends
5. Statusline updates → Shows current energy/attention

### Manual Commands

**Generate daily report**:
```bash
cd services/adhd-notifier
python daily_reporter.py
```

**Check metrics**:
```bash
curl http://localhost:8096/metrics | jq '.'
curl http://localhost:8095/health | jq '.'
```

**View dashboard**:
```bash
open http://localhost:8097
```

**Get task recommendation**:
```bash
curl http://localhost:8097/api/analytics/summary | jq '.adhd_state.energy'
```

---

## Configuration

### Environment Variables

**Activity Capture** (Docker):
```bash
REDIS_URL=redis://dopemux-redis-events:6379
ADHD_ENGINE_URL=http://host.docker.internal:8095
ADHD_USER_ID=hue
AGGREGATION_WINDOW_SECONDS=300
ALLOWED_ORIGINS=http://localhost:8097
```

**ADHD Engine** (Background):
```bash
API_PORT=8095
REDIS_URL=redis://localhost:6379
```

**Workspace Watcher**:
Edit `services/workspace-watcher/config.json` for app mappings

**Dashboard** (Optional auth):
```bash
DASHBOARD_API_KEY=your-secret-key  # Enable auth
```

---

## Monitoring & Logs

### Service Logs
```bash
# Workspace Watcher
tail -f /tmp/workspace_watcher.log

# Activity Capture
docker logs -f dopemux-activity-capture

# ADHD Engine
tail -f /tmp/adhd_engine.log

# ADHD Notifier
tail -f /tmp/adhd_notifier.log

# Dashboard
tail -f /tmp/adhd_dashboard.log
```

### Health Checks
```bash
curl http://localhost:8096/health  # Activity Capture
curl http://localhost:8095/health  # ADHD Engine
curl http://localhost:8097/health  # Dashboard
```

---

## Statusline Indicators

### MCP Servers (7 total)
- 📚 Context7 (3002) - Documentation
- 🧠 Zen (3003) - Multi-model reasoning
- 🔬 Serena (3006) - Code intelligence
- 📊 DDG-MCP (3016) - Decision graph
- 🔎 Dope-Context (6333) - Semantic search
- 🖥️ Desktop-Commander (3012) - Context switching
- 🎯 Activity Capture (8096) - Activity tracking

### ADHD State
- 🧠 ADHD Engine (active/sleeping)
- ⚡↑/=/↓ Energy (high/medium/low)
- 👁️● Attention (focused)
- 👁️🌀 Attention (scattered)
- 👁️💥 Attention (overwhelmed)

---

## ADHD Benefits

### Zero Cognitive Overhead
- No manual time tracking
- No manual task logging
- Automatic session boundaries
- Passive monitoring

### Real-Time Awareness
- Statusline shows current ADHD state
- Know your energy before starting tasks
- See attention state to choose work
- Break warnings when needed

### Burnout Prevention
- 25-minute break reminders
- 60-minute hyperfocus alerts
- Voice notifications (harder to ignore)
- Automatic session limits

### Pattern Recognition
- Daily reports show trends
- Identify peak productivity times
- Track break compliance
- Optimize work schedule

---

## Troubleshooting

### Statusline shows 💤 (ADHD Engine sleeping)
```bash
# Check if ADHD Engine is running
lsof -i :8095

# Restart ADHD Engine
cd services/adhd_engine
API_PORT=8095 REDIS_URL=redis://localhost:6379 python main.py &
```

### No workspace switches detected
```bash
# Check Workspace Watcher
tail -f /tmp/workspace_watcher.log

# Verify app mappings
cat services/workspace-watcher/config.json
```

### Activity Capture not processing events
```bash
# Check Activity Capture logs
docker logs dopemux-activity-capture --tail 50

# Verify Redis connection
docker exec dopemux-redis-events redis-cli ping
```

---

## Development

### Adding New App Mappings
Edit `services/workspace-watcher/config.json`:
```json
{
  "app_mappings": {
    "Your IDE": "/path/to/your/workspace",
    "Your Terminal": "/path/to/your/workspace"
  }
}
```

### Testing Event Flow
```bash
# Emit test events
python scripts/test-workspace-events.py

# Watch Activity Capture process them
docker logs -f dopemux-activity-capture
```

### Generating Reports
```bash
cd services/adhd-notifier
python daily_reporter.py > ~/adhd-report-$(date +%Y-%m-%d).txt
```

---

## Architecture Decisions

### Why Docker for Activity Capture?
- Clean deployment
- Network isolation
- Auto-restart on failure
- No Python environment conflicts

### Why Background Process for ADHD Engine?
- Simpler than Docker (no dependency issues)
- Direct localhost access
- Easier debugging
- Works perfectly as-is

### Why Polling vs Event-Driven?
- Cross-platform compatibility
- Simpler implementation
- 5-second latency acceptable for ADHD use case
- Future: Could migrate to FSEvents/inotify

### Why ConPort Stub vs Full Integration?
- Zero dependencies (works standalone)
- ADHD Engine fully functional without PostgreSQL
- Future: Integrate for ML pattern learning

---

## Future Enhancements

### Phase 6: Performance (Planned)
- Batched statusline endpoint (100ms → 30ms)
- Redis caching (reduce API calls)
- Optimize file checker

### Phase 7: Intelligence (Planned)
- Full ConPort integration
- ML pattern learning
- Predictive features (forecast energy drops)
- Multi-user support

---

## Credits

Built with Claude Code in one epic session:
- 28 commits
- ~7,000 lines
- 5 microservices
- All 4 phases complete

**ADHD-optimized development for neurodivergent developers!**
