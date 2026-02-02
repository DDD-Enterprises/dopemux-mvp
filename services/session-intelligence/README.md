# Session Intelligence Service

**Category**: Cognitive Plane  
**Status**: Production  
**Purpose**: AI-powered session analysis and continuity

## Overview

Session Intelligence provides intelligent session tracking, context preservation, and automatic session recovery for ADHD-optimized workflows.

## Quick Start

```bash
# Start via Docker Compose
docker-compose -f docker-compose.master.yml up -d session-intelligence

# Check status
docker logs session-intelligence
```

## Health Check

```bash
curl http://localhost:8099/health
```

## Configuration

Environment variables:
- `PORT` - Service port (default: 8099)
- `DOPECON_BRIDGE_URL` - DopeconBridge URL (default: http://localhost:3016)
- `SESSION_RETENTION_DAYS` - Session data retention (default: 90)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

## Features

- **Session Tracking** - Automatic session boundary detection
- **Context Preservation** - Save and restore session context
- **Continuity Suggestions** - "Pick up where you left off"
- **Pattern Detection** - Identify workflow patterns
- **ADHD-Optimized** - Handle interrupted/fragmented work sessions

## DopeconBridge Integration

Uses `bridge_adapter.py` to:
- Store session metadata in ConPort
- Query previous session context
- Track decision history across sessions
- Preserve multi-session continuity

## Session Lifecycle

1. **Session Start** - Detect new work session
2. **Context Capture** - Track tasks, decisions, progress
3. **Session Pause** - Handle interruptions/context switches
4. **Session Resume** - Restore context on return
5. **Session End** - Archive session data

## Development

```bash
cd services/session-intelligence
python bridge_adapter.py
```

## Documentation

See ConPort documentation for session data schema.
