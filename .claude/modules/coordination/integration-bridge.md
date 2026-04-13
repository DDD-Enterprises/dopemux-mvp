# Integration Bridge Module

**Module Version**: 2.0.0 (Simplified Architecture)
**Authority**: Event Coordination and Async Communication
**Modes**: Both PLAN and ACT
**Service**: `/services/mcp-integration-bridge/` at PORT_BASE+16
**Decision Reference**: #132 (Simplified architecture)

## Purpose

The Integration Bridge provides **event-driven coordination** between:
- ConPort (task & decision storage)
- SuperClaude (PRD parsing via `/dx:prd-parse`)
- Python ADHD Engine (cognitive optimization)
- React Ink Dashboard (visualization)

It is **NOT** a Two-Plane coordinator - that architecture was simplified. It's now just async event routing.

## Authority Boundaries

**Integration Bridge ONLY Authority:**
- Async event routing between services
- Redis Streams queue management
- Event bus coordination (pub/sub)
- Multi-instance event isolation
- MetaMCP role-based tool filtering enforcement

**Integration Bridge NEVER:**
- Stores task data (ConPort authority)
- Parses PRDs (SuperClaude authority)
- Calculates ADHD metrics (Python ADHD Engine authority)
- Provides LSP operations (Serena authority)
- Stores decisions (ConPort authority)

## Event Coordination Patterns

### Simplified Event Flow
```bash
# PRD to Task Creation Flow
1. User runs: /dx:prd-parse "requirements.md"
2. SuperClaude + Zen planner → JSON task hierarchy
3. Human reviews and approves
4. Python validator → adds ADHD metadata
5. ConPort batch import → progress_entry + custom_data + links
6. Integration Bridge → publishes "tasks_imported" event
7. Dashboard → updates UI with new tasks
8. ADHD Engine → analyzes tasks and calculates recommendations

# Implementation Flow
1. User runs: /dx:implement
2. ADHD Engine → queries ConPort for optimal task
3. Python session manager → starts 25min timer
4. Integration Bridge → publishes "session_started" event
5. Dashboard → shows timer + current task
6. Auto-save every 5min → ConPort update_progress
7. Integration Bridge → publishes "progress_updated" event
8. Dashboard → updates progress bar
```

### Redis Streams Architecture
```python
# Event Bus Implementation
import redis
from datetime import datetime

class EventBus:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def publish(self, stream: str, event: dict):
        """Publish event to Redis Stream"""
        await self.redis.xadd(
            stream,
            {
                "event_type": event["type"],
                "timestamp": datetime.utcnow().isoformat(),
                "data": json.dumps(event["data"])
            }
        )

    async def subscribe(self, stream: str, consumer_group: str):
        """Subscribe to Redis Stream with consumer group"""
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(stream, consumer_group, id='0')
        except redis.ResponseError:
            pass  # Group already exists

        # Read events
        while True:
            events = await self.redis.xreadgroup(
                consumer_group,
                consumer_name=f"consumer-{uuid.uuid4()}",
                streams={stream: '>'},
                count=10,
                block=1000
            )
            for stream_name, messages in events:
                for msg_id, msg_data in messages:
                    yield msg_id, msg_data

# Usage
bus = EventBus("redis://localhost:6379")

# Publish task creation
await bus.publish("dopemux:events", {
    "type": "tasks_imported",
    "data": {"task_count": 15, "sprint_id": "S-2025.10"}
})

# Subscribe to events
async for msg_id, msg_data in bus.subscribe("dopemux:events", "dashboard"):
    handle_event(msg_data)
```

### Event Types

| Event Type | Publisher | Subscribers | Purpose |
|-----------|-----------|------------|---------|
| `tasks_imported` | ConPort | Dashboard, ADHD Engine | New tasks available |
| `session_started` | ADHD Engine | Dashboard, ConPort | 25min session begins |
| `session_paused` | ADHD Engine | Dashboard, ConPort | Break time |
| `progress_updated` | ConPort | Dashboard | Task progress changed |
| `decision_logged` | ConPort | All services | New architectural decision |
| `adhd_state_changed` | ADHD Engine | Dashboard | Energy/attention updated |
| `break_reminder` | ADHD Engine | Dashboard, User | Time for break |

## REST API Endpoints

### Integration Bridge HTTP API
```bash
# Base URL: http://localhost:3016 (or PORT_BASE+16)

# Health check
GET /health
# Returns: {"status": "healthy", "redis": "connected", "subscribers": 3}

# Publish event (for external services)
POST /events
Content-Type: application/json
{
  "stream": "dopemux:events",
  "event": {
    "type": "tasks_imported",
    "data": {"task_count": 15}
  }
}

# Subscribe to events (SSE - Server-Sent Events)
GET /events/stream?consumer_group=dashboard
# Returns: text/event-stream with real-time events

# Get event history
GET /events/history?stream=dopemux:events&count=100
# Returns: Last 100 events from stream

# Authority enforcement check
POST /check-authority
Content-Type: application/json
{
  "operation": "update_task_status",
  "requester": "serena"
}
# Returns: {"allowed": false, "authority": "conport", "reason": "Only ConPort can update task status"}
```

## MetaMCP Role-Based Tool Filtering

The Integration Bridge enforces **tool-level boundaries** via MetaMCP configuration:

```yaml
# MetaMCP Role Configuration (enforced by Integration Bridge)
roles:
  dopemux-quickfix:
    tools:
      - mcp__conport__get_active_context
      - mcp__conport__update_progress
      - mcp__serena__goto_definition
      - mcp__serena__find_references
      # Only 8 tools - ADHD cognitive load optimization

  dopemux-act:
    tools:
      # Implementation tools (10 tools)
      - mcp__serena__*  # All Serena navigation
      - mcp__conport__log_progress
      - mcp__conport__update_progress
      - mcp__context7__get_library_docs

  dopemux-plan:
    tools:
      # Planning tools (9 tools)
      - mcp__zen__planner
      - mcp__zen__consensus
      - mcp__conport__log_decision
      - mcp__conport__link_conport_items
```

## Multi-Instance Isolation

```python
# Instance-specific event streams
INSTANCE_NAME = os.getenv("DOPEMUX_INSTANCE", "default")

# Each instance gets its own Redis Stream
EVENT_STREAM = f"dopemux:{INSTANCE_NAME}:events"

# No cross-instance event leakage
# "default" instance events don't affect "primary" instance
```

## ADHD Optimizations

- ✅ **Event filtering** - Dashboard only shows relevant events (reduce noise)
- ✅ **Event batching** - Group related events to prevent update spam
- ✅ **Rate limiting** - Max 10 events/sec to prevent overwhelming users
- ✅ **Visual indicators** - Color-coded event types in dashboard
- ✅ **Silent mode** - Suppress non-critical events during focus sessions

## Production Features

- **Event persistence** - Redis Streams keep 7 days of event history
- **Consumer groups** - Multiple subscribers without duplicate processing
- **Acknowledgment** - Ensure events are processed exactly once
- **Dead-letter queue** - Failed events moved to DLQ for manual review
- **Monitoring** - Prometheus metrics for event throughput and latency

---

**See Also:**
- `.claude/modules/coordination/authority-matrix.md` - Authority boundaries reference
- `.claude/modules/shared/event-patterns.md` - Event design patterns
