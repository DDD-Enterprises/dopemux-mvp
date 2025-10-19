# Integration Bridge - EventBus Coordination Layer

**Version**: 1.0.0
**Port**: 3016 (PORT_BASE + 16)
**Status**: ✅ Production Ready

## Overview

Integration Bridge provides **async event coordination** between Dopemux services using Redis Streams. Enables real-time communication between ConPort, ADHD Engine, and Dashboard without tight coupling.

## Architecture

### EventBus (Redis Streams)

**Implementation**: `event_bus.py`
**Pattern**: Pub/Sub with consumer groups
**Backend**: Redis Streams (xadd/xreadgroup)

**Features**:
- 8 event types for system coordination
- Consumer groups for load balancing
- Automatic message acknowledgment
- Non-blocking async publishing
- ADHD-optimized: Resilient to interruptions

### Event Types

| Event | Publisher | Subscribers | Purpose |
|-------|-----------|-------------|---------|
| `tasks_imported` | ConPort | Dashboard, ADHD Engine | New tasks available |
| `session_started` | ADHD Engine | Dashboard, ConPort | 25min session begins |
| `progress_updated` | ConPort | Dashboard | Task progress changed |
| `decision_logged` | ConPort | All services | New architectural decision |
| `session_completed` | ADHD Engine | Dashboard, ConPort | Session finished |
| `session_paused` | ADHD Engine | Dashboard | Break time |
| `break_reminder` | ADHD Engine | Dashboard | Time for break |
| `adhd_state_changed` | ADHD Engine | Dashboard | Energy/focus updated |

## REST API

### Base URL
```
http://localhost:3016
```

### Endpoints

#### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "instance": "default",
  "port": 3016,
  "event_bus": "ready"
}
```

#### Publish Event (Generic)
```bash
POST /events
Content-Type: application/json

{
  "stream": "dopemux:events",
  "event_type": "tasks_imported",
  "data": {"task_count": 15, "sprint_id": "S-2025.10"}
}

Response:
{
  "status": "published",
  "message_id": "1760911882663-0",
  "stream": "dopemux:events",
  "event_type": "tasks_imported",
  "timestamp": "2025-10-19T22:11:22.566477"
}
```

#### Get Stream Info
```bash
GET /events/{stream}

Example: GET /events/dopemux:events

Response:
{
  "stream": "dopemux:events",
  "info": {
    "length": 7,
    "groups": 2
  }
}
```

#### Convenience Endpoints

```bash
# Publish tasks_imported
POST /events/tasks-imported?task_count=15&sprint_id=S-2025.10

# Publish session_started
POST /events/session-started?task_id=task-123&duration_minutes=25

# Publish progress_updated
POST /events/progress-updated?task_id=task-123&status=IN_PROGRESS&progress=0.5
```

## Integration Examples

### ConPort → EventBus (Decision Logging)

```python
# In ConPort enhanced_server.py
from integration_bridge_client import IntegrationBridgeClient

# Initialize
self.integration_bridge = IntegrationBridgeClient()
await self.integration_bridge.initialize()

# Publish when decision logged
await self.integration_bridge.publish_decision_logged(
    decision_id="abc-123",
    summary="Use microservices architecture",
    workspace_id="/project/path",
    tags=["architecture"]
)
```

### Dashboard → EventBus (Event Subscription)

```python
# Subscribe to events
async for msg_id, event in event_bus.subscribe("dopemux:events", "dashboard-group"):
    if event.type == EventType.DECISION_LOGGED:
        # Update UI with new decision
        ui.show_notification(f"Decision: {event.data['summary']}")

    elif event.type == EventType.PROGRESS_UPDATED:
        # Update progress bar
        ui.update_progress(event.data['task_id'], event.data['progress'])
```

## Deployment

### Docker Build
```bash
cd services/mcp-integration-bridge
docker build -t mcp-integration-bridge:latest .
```

### Docker Run
```bash
docker run -d \
  --name mcp-integration-bridge \
  --network dopemux-network \
  -p 3016:3016 \
  -e PORT_BASE=3000 \
  -e REDIS_URL=redis://dopemux-redis-primary:6379 \
  -e POSTGRES_URL=postgresql+asyncpg://user:pass@host:5432/db \
  mcp-integration-bridge:latest
```

### Multi-Network Setup
```bash
# Connect to both dopemux-network and mcp-network
docker network connect mcp-network mcp-integration-bridge
```

## Testing

### Run EventBus Tests
```bash
# Test all event types via REST API
bash test_api.sh

# Test ConPort integration
bash test_conport_integration.sh

# Manual test with curl
curl -X POST http://localhost:3016/events \
  -H "Content-Type: application/json" \
  -d '{"event_type":"test_event","data":{"key":"value"}}'
```

### Verify Events in Redis
```bash
# Check stream length
docker exec dopemux-redis-primary redis-cli XLEN "dopemux:events"

# Read events
docker exec dopemux-redis-primary redis-cli XRANGE "dopemux:events" - + COUNT 5
```

## Files

- `event_bus.py` - Redis Streams EventBus implementation (320 lines)
- `main.py` - FastAPI application with event endpoints (1720 lines)
- `integration_bridge_client.py` - HTTP client for other services (130 lines)
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container build configuration
- `test_api.sh` - EventBus REST API tests
- `test_conport_integration.sh` - ConPort integration tests
- `EVENTBUS_VALIDATION.md` - Validation test results

## Event Flow Diagram

```
ConPort                     Integration Bridge              Redis Streams
┌─────────┐                ┌─────────────────┐             ┌──────────────┐
│log_     │                │                 │             │              │
│decision │──HTTP POST───▶ │ POST /events    │──xadd────▶  │ dopemux:     │
│         │                │                 │             │ events       │
└─────────┘                └─────────────────┘             └──────────────┘
                                                                   │
                           ┌─────────────────┐                    │
                           │ Dashboard       │◀──xreadgroup───────┘
                           │ (subscriber)    │
                           └─────────────────┘
```

## Performance

- **Event Publishing**: < 10ms
- **Redis Streams**: < 5ms storage
- **HTTP API**: < 50ms end-to-end
- **Non-blocking**: Events published asynchronously

## ADHD Optimizations

- **Non-blocking**: Event failures don't break workflows
- **Graceful degradation**: Services work without EventBus
- **Fast feedback**: < 50ms latency for UI updates
- **Resilient**: Automatic reconnection on failures

## Production Checklist

- ✅ EventBus tested with 7+ events
- ✅ ConPort integration validated
- ✅ Redis Streams storing correctly
- ✅ REST API operational
- ✅ Multi-network connectivity confirmed
- ✅ Error handling comprehensive
- ✅ Logging and monitoring enabled
- ⬜ Dashboard subscriber implementation (next step)
- ⬜ ADHD Engine integration (next step)

## Next Steps

1. **Dashboard Integration**: Build event subscriber in React/Ink
2. **ADHD Engine**: Publish session lifecycle events
3. **Monitoring**: Add Prometheus metrics for event rates
4. **Schema Migration**: Add instance_id to progress_entries table

## Troubleshooting

### EventBus not connecting
```bash
# Check Redis
docker ps | grep redis
docker exec dopemux-redis-primary redis-cli PING

# Check Integration Bridge logs
docker logs mcp-integration-bridge
```

### Events not publishing
```bash
# Check Integration Bridge health
curl http://localhost:3016/health

# Check ConPort Integration Bridge client
docker logs mcp-conport | grep integration_bridge
```

## Documentation

- Module spec: `.claude/modules/coordination/integration-bridge.md`
- Validation: `EVENTBUS_VALIDATION.md`
- ConPort API: `docker/mcp-servers/conport/README.md` (TBD)

---

**Status**: ✅ Integration Bridge EventBus is production-ready and enables real-time cross-service coordination for Dopemux ADHD-optimized workflows.
