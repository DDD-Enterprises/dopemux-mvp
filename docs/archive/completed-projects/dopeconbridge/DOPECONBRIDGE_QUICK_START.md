---
id: DOPECONBRIDGE_QUICK_START
title: Dopeconbridge_Quick_Start
type: explanation
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# DopeconBridge Quick Start Guide
**Last Updated**: 2025-11-13
**Status**: ✅ Production Ready

---

## What is DopeconBridge?

**DopeconBridge** is the central integration gateway for all Dopemux services. It's the **single point of coordination** between:

- **PM Plane** (Leantime, Task-Master, Taskmaster) - Task/project management
- **Cognitive Plane** (ADHD Engine, Serena, GPT-Researcher) - Context/reasoning
- **Knowledge Graph** (ConPort, Decision Graph) - Persistent memory
- **Event Bus** (Redis Streams) - Real-time communication

**Key Principle**: No service should access ConPort DB or Redis directly - everything goes through DopeconBridge.

---

## Why DopeconBridge?

### Before DopeconBridge ❌
- Services hit ConPort database directly (SQLite, Postgres)
- Ad-hoc HTTP calls to ConPort API
- Direct Redis stream manipulation
- Inconsistent authentication
- Cross-plane chaos

### After DopeconBridge ✅
- Single integration point
- Consistent API (REST + events)
- Centralized auth & rate limiting
- Cross-plane routing enforced
- Observability & monitoring

---

## 5-Minute Setup

### 1. Check If DopeconBridge Is Running

```bash
# Quick health check
curl http://localhost:3016/health

# Or use the CLI
dopemux bridge status
```

Expected response:
```json
{"status": "healthy", "timestamp": "2025-11-13T14:00:00Z"}
```

### 2. Start DopeconBridge (If Not Running)

```bash
# Start with docker-compose
docker-compose -f docker-compose.master.yml up -d dopecon-bridge

# Or via Makefile
make bridge-up

# Check logs
docker logs -f dopecon-bridge
```

### 3. Set Environment Variables

Add to your `.env` file:

```bash
# DopeconBridge URL (default: http://localhost:3016)
DOPECON_BRIDGE_URL=http://localhost:3016

# Optional authentication token
DOPECON_BRIDGE_TOKEN=

# Source plane identifier
DOPECON_BRIDGE_SOURCE_PLANE=cognitive_plane  # or pm_plane

# Workspace identification
WORKSPACE_ID=/path/to/your/workspace
```

### 4. Test Basic Operations

```bash
# Publish a test event
dopemux bridge event test.hello '{"message": "Hello DopeconBridge!"}'

# Query recent decisions
dopemux bridge decisions --limit 5

# Check bridge statistics
dopemux bridge stats
```

---

## CLI Commands Reference

```bash
# Status & Health
dopemux bridge status              # Check if bridge is running
dopemux bridge stats                # Usage statistics

# Events
dopemux bridge event <type> <json> # Publish event
  Example: dopemux bridge event test.event '{"key": "value"}'

# Decisions
dopemux bridge decisions           # Recent decisions (default 10)
dopemux bridge decisions --limit 20 --search "auth"

# Cross-Plane Routing
dopemux bridge route pm leantime.create_task '{"title": "Fix bug"}'
dopemux bridge route cognitive context.update '{"focus": "Testing"}'

# Custom Data
dopemux bridge data save <category> --key <k> --value '{...}'
dopemux bridge data get <category> [--key <k>]
```

---

## Using in Python Services

### Quick Example

```python
from services.shared.dopecon_bridge_client import (
    DopeconBridgeClient,
    DopeconBridgeConfig,
)

# Auto-configure from environment
config = DopeconBridgeConfig.from_env()
bridge = DopeconBridgeClient(config=config)

# Publish event
bridge.publish_event(
    event_type="task.created",
    data={"task_id": 123, "title": "Implement feature"},
)

# Query decisions
decisions = bridge.recent_decisions(workspace_id="/my/workspace")

# Save custom data
bridge.save_custom_data(
    workspace_id="/my/workspace",
    category="adhd_state",
    key="current",
    value={"focus": 8, "energy": 7},
)
```

See [`DOPECONBRIDGE_COMPLETE_INTEGRATION.md`](./DOPECONBRIDGE_COMPLETE_INTEGRATION.md) for full documentation.

---

## Troubleshooting

### Bridge Won't Start

```bash
# Check Docker container
docker ps -a | grep dopecon-bridge

# View logs
docker logs dopecon-bridge

# Restart
make bridge-restart
```

### Can't Connect

```bash
# Test connectivity
curl http://localhost:3016/health

# Check environment
echo $DOPECON_BRIDGE_URL
```

### Events Not Publishing

```bash
# Test event
dopemux bridge event test.ping '{"test": true}'

# Check logs
docker logs -f dopecon-bridge
```

---

## Next Steps

1. **Full Documentation**: [`DOPECONBRIDGE_COMPLETE_INTEGRATION.md`](./DOPECONBRIDGE_COMPLETE_INTEGRATION.md)
2. **Migration Guide**: See "Migration Checklist" in complete docs
3. **API Reference**: `services/dopecon-bridge/README.md`
4. **Examples**: Check migrated services (ADHD Engine, Serena, Task-Orchestrator)

---

**Status**: ✅ Production Ready
**Version**: 1.0.0
**Last Updated**: 2025-11-13
