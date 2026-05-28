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
- Owns workflow state (task-orchestrator authority — per AGENTS.md §6 + accepted workflow-authority ADR)
- Stores decisions (ConPort authority)
- Parses PRDs (SuperClaude authority)
- Calculates ADHD metrics (Python ADHD Engine authority)
- Provides LSP operations (Serena authority)
- Stores PM entity records (Leantime authority)

## Event Coordination Patterns

### Simplified Event Flow
```bash
# PRD to Work-Item Creation Flow (orchestrator-first)
1. User runs: /dx:prd-parse "requirements.md"
2. SuperClaude + PAL planner → JSON work-item hierarchy
3. Human reviews and approves
4. SuperClaude → mcp__task-orchestrator__create_work_tree (with `type` set on each item)
5. Orchestrator → "item-created" events for each new work-item
6. Integration Bridge → fans out to subscribers
7. Dashboard → updates UI with new work-items
8. ADHD Engine → queries orchestrator for ranked candidates
9. ConPort → optional log_decision if the PRD parsing itself was architectural; link_conport_items to the new items

# Implementation Flow (orchestrator-first)
1. User runs: /dx:next (or /dx:implement)
2. Orchestrator → get_next_item returns ranked candidates with schema + gate status
3. User picks an item → /dx:start <id>
4. Orchestrator → advance_item(trigger="start") + emits "item-started" event
5. Integration Bridge → publishes "item-started" + ADHD Engine starts 25min timer
6. During work → manage_notes(upsert) accumulates implementation-evidence
7. At completion → /dx:complete <id> requires `proof-bundle` note filed first
8. Orchestrator → advance_item(trigger="complete") + emits "item-completed" event
9. Integration Bridge publishes "item-completed" → Dashboard celebrates + ConPort.log_decision if architectural
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

**Workflow events** (canonical source: task-orchestrator MCP per AGENTS.md §6):

| Event Type | Publisher | Subscribers | Purpose |
|-----------|-----------|------------|---------|
| `item-created` | task-orchestrator | Dashboard, ADHD Engine | New work-item available (via manage_items or create_work_tree) |
| `item-started` | task-orchestrator | Dashboard, ADHD Engine, ConPort (for active_context) | Work-item advanced queue → work |
| `item-blocked` | task-orchestrator | Dashboard | Work-item advanced any → blocked (or BLOCKED-BY edge fired) |
| `item-resumed` | task-orchestrator | Dashboard | Blocked work-item resumed to previous role |
| `item-completed` | task-orchestrator | Dashboard, ConPort (for decision linkage), ADHD Engine | Work-item advanced to terminal (gate-passed: proof-bundle filled) |
| `item-cancelled` | task-orchestrator | Dashboard | Work-item terminal via `cancel` (statusLabel="cancelled") |
| `item-reopened` | task-orchestrator | Dashboard | Terminal item reopened to queue |
| `dependency-satisfied` | task-orchestrator | Dashboard, ADHD Engine | BLOCKS edge satisfied (item now eligible to advance) |
| `claim-acquired` | task-orchestrator | Dashboard (operator visibility) | Agent claimed an item via claim_item |
| `claim-released` / `claim-expired` | task-orchestrator | Dashboard, anti-pattern detector | Stale-claim detection feeds Phase 7 retros |

**Session + ADHD events** (canonical source: ADHD Engine):

| Event Type | Publisher | Subscribers | Purpose |
|-----------|-----------|------------|---------|
| `session_started` | ADHD Engine | Dashboard, ConPort (active_context) | 25min session begins |
| `session_paused` | ADHD Engine | Dashboard, ConPort | Break time |
| `adhd_state_changed` | ADHD Engine | Dashboard | Energy/attention updated |
| `break_reminder` | ADHD Engine | Dashboard, User | Time for break |

**Decision events** (canonical source: ConPort):

| Event Type | Publisher | Subscribers | Purpose |
|-----------|-----------|------------|---------|
| `decision_logged` | ConPort | All services | New architectural decision (often linked to an orchestrator work-item via link_conport_items) |

**Deprecated**: `tasks_imported`, `progress_updated` (ConPort progress_entry no longer represents workflow state; replaced by `item-created` and the role-transition events above).

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
