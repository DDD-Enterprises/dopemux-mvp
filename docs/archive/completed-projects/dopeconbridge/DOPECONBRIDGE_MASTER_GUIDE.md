---
id: DOPECONBRIDGE_MASTER_GUIDE
title: Dopeconbridge_Master_Guide
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# DopeconBridge Master Guide

**Version:** 2.0
**Date:** 2025-11-13
**Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Service Integration](#service-integration)
5. [Client Usage](#client-usage)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Overview

**DopeconBridge** (formerly Integration Bridge / MCP Integration Bridge) is the **single authoritative gateway** for all cross-plane communication in Dopemux.

### Core Principles

1. **Single Choke Point**: All PM ↔ Cognitive plane communication flows through DopeconBridge
2. **No Direct ConPort Access**: Services MUST NOT access ConPort DB/HTTP directly
3. **Event-Driven**: All state changes publish events to the event bus
4. **Knowledge Graph Authority**: All KG operations go through `/kg/*` endpoints
5. **Decision Graph Integration**: All DDG operations use `/ddg/*` endpoints

### Two-Plane Model

```
┌─────────────────────────────────────────────────────────────┐
│                        PM PLANE                              │
│  • Leantime (tasks, projects)                               │
│  • Task-Master (goals, milestones)                          │
│  • Task-Orchestrator (workflow execution)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │   DopeconBridge     │
         │   (Port 3016)       │
         │                     │
         │  • Event Bus        │
         │  • KG Authority     │
         │  • Decision Graph   │
         │  • Cross-Plane      │
         │    Routing          │
         └─────────┬───────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    COGNITIVE PLANE                           │
│  • Serena (intelligent coding)                              │
│  • ConPort (context + knowledge graph)                      │
│  • ADHD Engine (attention + focus)                          │
│  • DopeBrainz (learning patterns)                           │
│  • Voice Commands (natural interaction)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Core Components

#### 1. **Event Bus** (`/events`)
- Redis Streams-backed event distribution
- Event deduplication (10-minute window)
- Stream management and history
- Subscription/notification system

#### 2. **Cross-Plane Router** (`/route/*`)
- `/route/pm` - Cognitive → PM operations
- `/route/cognitive` - PM → Cognitive operations
- Correlation ID tracking
- Request/response validation

#### 3. **Knowledge Graph Authority** (`/kg/*`)
- `/kg/custom_data` - Custom workspace data
- `/kg/workspace/*` - Workspace queries
- `/kg/search` - Semantic search
- Direct ConPort MCP integration

#### 4. **Decision Graph** (`/ddg/*`)
- `/ddg/decisions/recent` - Recent decisions
- `/ddg/decisions/search` - Decision search
- `/ddg/decisions/related` - Related decisions
- `/ddg/text/related` - Semantic text similarity

#### 5. **Pattern Detection** (`/patterns/*`)
- ADHD state patterns
- Context switch frequency
- Decision churn detection
- Task abandonment tracking
- Knowledge gap identification

#### 6. **Monitoring** (`/health`, `/metrics`)
- Health checks with dependencies
- Prometheus metrics export
- Performance tracking
- Error rate monitoring

---

## Quick Start

### 1. Install DopeconBridge Client

```bash
# From repo root
pip install -e services/shared/dopecon_bridge_client
```

### 2. Set Environment Variables

```bash
export DOPECONBRIDGE_URL="http://localhost:3016"
export DOPECONBRIDGE_TOKEN="your-secret-token"  # Optional
export DOPECONBRIDGE_SOURCE_PLANE="cognitive_plane"  # or "pm_plane"
```

### 3. Start DopeconBridge

```bash
cd services/dopecon-bridge
python3 main.py
```

### 4. Use in Your Service

```python
from services.shared.dopecon_bridge_client import DopeconBridgeClient

# Auto-configures from environment
bridge = DopeconBridgeClient.from_env()

# Publish event
bridge.publish_event(
    event_type="task.created",
    data={"task_id": "123", "title": "Fix bug"},
    source="my-service"
)

# Route to PM plane
response = bridge.route_pm(
    operation="leantime.create_task",
    data={"project_id": 1, "title": "New task"},
    requester="task-orchestrator"
)

# Save custom data to KG
bridge.save_custom_data(
    workspace_id="my-workspace",
    category="session_state",
    key="current_focus",
    value={"task": "bug-fix", "file": "main.py"}
)
```

---

## Service Integration

### Services Migrated to DopeconBridge

✅ **Complete**
- ADHD Engine
- Task Orchestrator
- Serena v2
- Voice Commands
- Workspace Watcher
- Orchestrator TUI
- DopeBrainz
- Activity Capture
- Break Suggester
- DDG (Dope Decision Graph)
- Energy Trends
- Interruption Shield
- Monitoring Dashboard
- Working Memory Assistant

⚠️ **Experimental** (bridge-compatible but not production-critical)
- ML Risk Assessment
- Genetic Agent
- Claude Context
- Dopemux GPT Researcher

### Migration Pattern

Every service follows this pattern:

1. **Add bridge adapter** (`bridge_adapter.py`)
2. **Update config** (read `DOPECONBRIDGE_*` env vars)
3. **Replace direct ConPort calls** with bridge adapter methods
4. **Add tests** with mocked bridge client
5. **Update docs** to reference DopeconBridge

---

## Client Usage

### DopeconBridgeClient API

```python
from services.shared.dopecon_bridge_client import (
    DopeconBridgeClient,
    DopeconBridgeConfig,
    DopeconBridgeError,
)

# Manual configuration
config = DopeconBridgeConfig(
    base_url="http://localhost:3016",
    token="secret",
    timeout=10.0,
    source_plane="cognitive_plane"
)
bridge = DopeconBridgeClient(config=config)

# Or from environment
bridge = DopeconBridgeClient.from_env()
```

### Event Bus Operations

```python
# Publish event
response = bridge.publish_event(
    event_type="adhd.focus_changed",
    data={"state": "focused", "duration_ms": 3600000},
    stream="dopemux:events",
    source="adhd-engine"
)

# Get stream info
info = bridge.get_stream_info("dopemux:events")

# Get event history
history = bridge.get_event_history("dopemux:events", count=50)
```

### Cross-Plane Routing

```python
# Route to PM plane
pm_response = bridge.route_pm(
    operation="leantime.create_task",
    data={"project_id": 1, "title": "Task"},
    requester="cognitive-service"
)

# Route to Cognitive plane
cog_response = bridge.route_cognitive(
    operation="serena.analyze_code",
    data={"file_path": "/path/to/file.py"},
    requester="pm-service"
)
```

### Knowledge Graph Operations

```python
# Save custom data
bridge.save_custom_data(
    workspace_id="workspace-123",
    category="user_preferences",
    key="theme",
    value={"mode": "dark", "accent": "blue"}
)

# Get custom data
data = bridge.get_custom_data(
    workspace_id="workspace-123",
    category="user_preferences",
    key="theme",  # Optional: omit to get all keys in category
    limit=10
)

# Workspace search
results = bridge.search_workspace(
    workspace_id="workspace-123",
    query="authentication bug",
    limit=20
)
```

### Decision Graph Operations

```python
# Recent decisions
decisions = bridge.recent_decisions(
    workspace_id="workspace-123",
    limit=20
)

# Search decisions
results = bridge.search_decisions(
    query="refactor authentication",
    workspace_id="workspace-123"
)

# Related decisions
related = bridge.related_decisions(
    decision_id="decision-456",
    k=10
)

# Related text (semantic search)
similar = bridge.related_text(
    query="How do we handle auth tokens?",
    workspace_id="workspace-123",
    k=10
)
```

### Leantime Operations

```python
# Create project
project = bridge.create_leantime_project(
    name="New Project",
    description="Project description",
    client_id=1
)

# Create task
task = bridge.create_leantime_task(
    project_id=project["id"],
    title="Implement feature",
    description="Feature details",
    milestone_id=5
)

# Get projects
projects = bridge.get_leantime_projects()

# Get tasks
tasks = bridge.get_leantime_tasks(project_id=1)
```

### DopeBrainz Operations

```python
# Log learning event
bridge.log_brainz_learning(
    workspace_id="workspace-123",
    pattern_type="code_pattern",
    data={
        "language": "python",
        "pattern": "decorator_usage",
        "confidence": 0.85
    }
)

# Get learning patterns
patterns = bridge.get_brainz_patterns(
    workspace_id="workspace-123",
    pattern_type="code_pattern",
    limit=50
)
```

### Async Client

```python
from services.shared.dopecon_bridge_client import AsyncDopeconBridgeClient

async def example():
    bridge = AsyncDopeconBridgeClient.from_env()

    # All methods are async
    response = await bridge.publish_event(
        event_type="test.event",
        data={"key": "value"}
    )

    decisions = await bridge.recent_decisions(limit=10)

    await bridge.close()

# Or use as context manager
async def example_ctx():
    async with AsyncDopeconBridgeClient.from_env() as bridge:
        response = await bridge.publish_event(...)
```

---

## Configuration

### Environment Variables

#### DopeconBridge Server

```bash
# Server binding
DOPECONBRIDGE_HOST="0.0.0.0"
DOPECONBRIDGE_PORT="3016"

# Security
DOPECONBRIDGE_TOKEN="your-secret-token"
DOPECONBRIDGE_ALLOWED_ORIGINS="http://localhost:3000,http://localhost:8080"

# Redis (for event bus)
REDIS_URL="redis://localhost:6379/0"

# ConPort integration
CONPORT_URL="http://localhost:3010"
CONPORT_WORKSPACE_ID="/workspace/path"

# Leantime integration
LEANTIME_URL="http://localhost:8080"
LEANTIME_API_KEY="leantime-api-key"

# DopeBrainz integration
DOPEBRAINZ_URL="http://localhost:3020"

# Monitoring
ENABLE_METRICS="true"
LOG_LEVEL="INFO"
```

#### Client Configuration

```bash
# Required
DOPECONBRIDGE_URL="http://localhost:3016"

# Optional
DOPECONBRIDGE_TOKEN="your-secret-token"
DOPECONBRIDGE_SOURCE_PLANE="cognitive_plane"  # or "pm_plane"
DOPECONBRIDGE_TIMEOUT="10.0"
```

### Docker Compose

```yaml
services:
  dopecon-bridge:
    build: ./services/dopecon-bridge
    ports:
      - "3016:3016"
    environment:
      - DOPECONBRIDGE_HOST=0.0.0.0
      - DOPECONBRIDGE_PORT=3016
      - REDIS_URL=redis://redis:6379/0
      - CONPORT_URL=http://conport:3010
      - LEANTIME_URL=http://leantime:8080
      - DOPEBRAINZ_URL=http://dopebrainz:3020
    depends_on:
      - redis
      - conport
    networks:
      - dopemux

  your-service:
    build: ./services/your-service
    environment:
      - DOPECONBRIDGE_URL=http://dopecon-bridge:3016
      - DOPECONBRIDGE_SOURCE_PLANE=cognitive_plane
    depends_on:
      - dopecon-bridge
    networks:
      - dopemux
```

---

## Testing

### Unit Tests

```bash
# Test shared client
python3 -m pytest tests/shared/test_dopecon_bridge_client.py -v

# Test DopeconBridge server
cd services/dopecon-bridge
python3 -m pytest tests/ -v
```

### Integration Tests

```bash
# End-to-end tests
cd services/dopecon-bridge
python3 -m pytest tests/integration/test_phase2_e2e.py -v
python3 -m pytest tests/integration/test_phase3_e2e.py -v
```

### Validation Script

```bash
# Comprehensive validation
./verify_dopecon_bridge.sh
```

### Manual Testing

```bash
# Start bridge
cd services/dopecon-bridge
python3 main.py

# In another terminal, test API
./test_api.sh

# Or use manual smoke test
python3 manual_smoke_test.py
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

**Symptom:** `DopeconBridgeError: Connection refused`

**Solutions:**
- Verify DopeconBridge is running: `curl http://localhost:3016/health`
- Check `DOPECONBRIDGE_URL` environment variable
- Ensure no firewall blocking port 3016

#### 2. Authentication Failed

**Symptom:** `DopeconBridgeError: 401 Unauthorized`

**Solutions:**
- Set `DOPECONBRIDGE_TOKEN` in client environment
- Verify token matches bridge server configuration
- Check token is not expired

#### 3. Event Not Publishing

**Symptom:** Events not appearing in stream

**Solutions:**
- Check Redis connection: `redis-cli PING`
- Verify `REDIS_URL` configuration
- Check event deduplication (10-minute window)
- Review bridge logs for errors

#### 4. ConPort Integration Failing

**Symptom:** `DopeconBridgeError: ConPort unavailable`

**Solutions:**
- Verify ConPort is running: `curl http://localhost:3010/health`
- Check `CONPORT_URL` environment variable
- Ensure ConPort workspace ID is valid
- Review ConPort logs

#### 5. Cross-Plane Routing Failed

**Symptom:** Route operations timeout or fail

**Solutions:**
- Check target service is running
- Verify operation name is correct
- Review bridge logs for routing errors
- Check correlation ID in logs for tracing

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL="DEBUG"
export DOPECONBRIDGE_DEBUG="true"
python3 -m services.dopecon_bridge.main
```

### Health Checks

```bash
# Basic health
curl http://localhost:3016/health

# Detailed health with dependencies
curl http://localhost:3016/health?detailed=true

# Metrics
curl http://localhost:3016/metrics
```

### Logs

```bash
# Real-time logs
tail -f /var/log/dopemux/dopecon-bridge.log

# Error logs only
grep ERROR /var/log/dopemux/dopecon-bridge.log

# Specific correlation ID
grep "correlation_id=abc-123" /var/log/dopemux/dopecon-bridge.log
```

---

## Best Practices

### 1. Always Use the Bridge

❌ **Don't:**
```python
# Direct ConPort access
import sqlite3
conn = sqlite3.connect("context_portal/context.db")
```

✅ **Do:**
```python
# Use DopeconBridge
from services.shared.dopecon_bridge_client import DopeconBridgeClient
bridge = DopeconBridgeClient.from_env()
bridge.save_custom_data(...)
```

### 2. Publish Events for State Changes

❌ **Don't:**
```python
# Silent state change
self.current_state = "focused"
```

✅ **Do:**
```python
# Publish event
self.current_state = "focused"
bridge.publish_event(
    event_type="adhd.state_changed",
    data={"state": "focused", "timestamp": time.time()}
)
```

### 3. Use Correlation IDs

```python
# Generate correlation ID
import uuid
correlation_id = str(uuid.uuid4())

# Use in cross-plane calls
response = bridge.route_pm(
    operation="leantime.create_task",
    data={"task": {...}, "correlation_id": correlation_id},
    requester="my-service"
)

# Log for tracing
logger.info(f"Task created with correlation_id={correlation_id}")
```

### 4. Handle Errors Gracefully

```python
from services.shared.dopecon_bridge_client import DopeconBridgeError

try:
    response = bridge.publish_event(...)
except DopeconBridgeError as e:
    logger.error(f"Bridge error: {e}")
    # Fallback logic
except Exception as e:
    logger.exception("Unexpected error")
```

### 5. Use Async Client for High Throughput

```python
# For services handling many requests
async with AsyncDopeconBridgeClient.from_env() as bridge:
    tasks = [
        bridge.publish_event(...),
        bridge.save_custom_data(...),
        bridge.route_pm(...)
    ]
    results = await asyncio.gather(*tasks)
```

---

## Migration Checklist

When migrating a service to DopeconBridge:

- [ ] Install `dopecon_bridge_client` package
- [ ] Add `DOPECONBRIDGE_*` environment variables
- [ ] Create `bridge_adapter.py` for service-specific logic
- [ ] Replace all direct ConPort/Redis/HTTP calls
- [ ] Update service configuration
- [ ] Add unit tests with mocked bridge client
- [ ] Update service documentation
- [ ] Update Docker Compose integration
- [ ] Test end-to-end with running bridge
- [ ] Add service to bridge monitoring dashboard
- [ ] Document bridge usage in service README

---

## Resources

### Documentation
- [DopeconBridge Service Catalog](./DOPECONBRIDGE_SERVICE_CATALOG.md)
- [DopeconBridge Quick Start](./DOPECONBRIDGE_QUICK_START.md)
- [Phase 9 Config Update](./DOPECONBRIDGE_PHASE9_CONFIG_UPDATE.md)
- [Zen Integration Plan](./DOPECONBRIDGE_ZEN_INTEGRATION_PLAN.md)

### Code Examples
- Shared Client: `services/shared/dopecon_bridge_client/`
- ADHD Engine Adapter: `services/adhd_engine/bridge_integration.py`
- Task Orchestrator Adapter: `services/task-orchestrator/adapters/bridge_adapter.py`
- Serena Adapter: `services/serena/v2/bridge_adapter.py`

### Scripts
- Validation: `./verify_dopecon_bridge.sh`
- Quick Start: `./scripts/day1_quick_start.sh`
- Renaming Tool: `./scripts/rename_to_dopecon_bridge.py`

### Support
- GitHub Issues: [dopemux-mvp/issues](https://github.com/dopemux/dopemux-mvp/issues)
- Documentation: `docs/dopecon-bridge/`
- Slack: `#dopecon-bridge` channel

---

**Last Updated:** 2025-11-13
**Maintained By:** Dopemux Core Team
**License:** MIT
