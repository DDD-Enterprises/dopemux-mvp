# EVENT_BUS_MAP

## Implementations
- Core Dopemux event bus abstraction exists at `src/dopemux/event_bus.py` with `EventBus` interface and two adapters (`InMemoryAdapter`, `RedisStreamsAdapter`). (src/dopemux/event_bus.py:L68-L82)
- Primary production event bus exists at `services/dopecon-bridge/event_bus.py`, using Redis Streams (`xadd`, `xreadgroup`, `xack`) with dedup/rate-limit/metrics options. (services/dopecon-bridge/event_bus.py:L168-L195)
- Secondary minimal event bus exists at `services/dopecon-bridge/dopecon_bridge/event_bus.py` with route-oriented defaults and direct Redis stream calls. (services/dopecon-bridge/dopecon_bridge/event_bus.py:L69-L87)
- Dopecon-bridge app binds global `event_bus = EventBus(REDIS_URL, REDIS_PASSWORD)` and initializes it at startup. (services/dopecon-bridge/main.py:L1344-L1348)

## Streams Identified
- `dopemux:events` is the primary cross-service stream for coordination events. (services/dopecon-bridge/main.py:L1814-L1820)
- `dopemux:cross-plane` is used for cross-plane route publication. (services/dopecon-bridge/main.py:L2840-L2840)
- `activity.events.v1` is the input stream for dope-memory ingestion. (services/working-memory-assistant/eventbus_consumer.py:L35-L37)
- `memory.derived.v1` is the output stream for materialized memory events. (services/working-memory-assistant/eventbus_consumer.py:L35-L37)
- `conport:events` is consumed by Serena’s decision cache consumer. (services/serena/eventbus_consumer.py:L98-L103)

## Event Type Registries

### Typed Pydantic Events (Core Dopemux)
- Base type is `Event` with fields `type`, `timestamp`, `priority`, `data`, `source`. (src/dopemux/events/types.py:L23-L31)
- Domain wrappers exist for `worktree`, `context`, `adhd`, `theme`, and `session`. (src/dopemux/events/types.py:L36-L115)

### Dopecon-Bridge EventType Enum
- Enum values: `tasks_imported`, `session_started`, `session_paused`, `session_completed`, `progress_updated`, `decision_logged`, `adhd_state_changed`, `break_reminder`. (services/dopecon-bridge/event_bus.py:L25-L35)

### ADHD Engine Local Event Constants
- ADHD event constants include `claude_prompt_received`, `claude_tool_started`, `claude_tool_completed`, `claude_session_stopped`, `file_opened`, `file_saved`, `file_activity`, `progress_logged`, `task_completed`, `context_saved`, `context_switch`. (services/adhd_engine/event_emitter.py:L237-L259)

### Dope-Memory Ingestion/Materialization Event Sets
- High-signal promotable trackers include `decision.logged`, `task.completed`, `task.failed`, `task.blocked`, `error.encountered`, `manual.memory_store`, `workflow.phase_changed`. (services/working-memory-assistant/eventbus_consumer.py:L57-L66)
- Derived events published include `worklog.created`, `memory.pulse`, `reflection.created`. (services/working-memory-assistant/eventbus_consumer.py:L445-L447)

## Producers (Publishers)
- `services/dopecon-bridge/main.py` publishes user-specified events via `/events` endpoint. (services/dopecon-bridge/main.py:L1819-L1842)
- `services/dopecon-bridge/main.py` publishes convenience events (`tasks_imported`, `session_started`, `progress_updated`) to `dopemux:events`. (services/dopecon-bridge/main.py:L1877-L1907)
- `services/dopecon-bridge/integrations/adhd_engine.py` publishes `cognitive.state.changed`, `adhd.overload.detected`, `break.recommended` to `dopemux:events`. (services/dopecon-bridge/integrations/adhd_engine.py:L192-L203)
- `services/dopecon-bridge/integrations/dope_context.py` publishes `search.completed`, `knowledge.gap.detected`, `search.pattern.discovered` to `dopemux:events`. (services/dopecon-bridge/integrations/dope_context.py:L93-L106)
- `services/adhd_engine/event_emitter.py` publishes arbitrary ADHD Engine API events to `dopemux:events` via `xadd`. (services/adhd_engine/event_emitter.py:L75-L76)
- `services/workspace-watcher/event_emitter.py` publishes `workspace.switched` to `dopemux:events`. (services/workspace-watcher/event_emitter.py:L96-L117)
- `services/working-memory-assistant/eventbus_consumer.py` publishes derived memory events to `memory.derived.v1`. (services/working-memory-assistant/eventbus_consumer.py:L493-L515)

## Consumers (Subscribers)
- `services/dopecon-bridge/main.py` starts DDG ingestion subscriber on `dopemux:events` consumer group `ddg-ingest`. (services/dopecon-bridge/main.py:L334-L343)
- `services/dopecon-bridge/main.py` exposes SSE stream subscriber endpoint reading from EventBus subscription. (services/dopecon-bridge/main.py:L1910-L1931)
- `services/adhd_engine/event_listener.py` subscribes to `dopemux:events` as `adhd-engine` and dispatches by `event.type` handler map. (services/adhd_engine/event_listener.py:L142-L150)
- `services/task-orchestrator/app/services/enhanced_orchestrator.py` subscribes to `dopemux:events` as `task-orchestrator` and handles `EventType` branches. (services/task-orchestrator/app/services/enhanced_orchestrator.py:L1303-L1334)
- `services/activity-capture/event_subscriber.py` subscribes to configured stream (documented for `dopemux:events`) and routes selected event types to activity handlers. (services/activity-capture/event_subscriber.py:L21-L23)
- `services/working-memory-assistant/eventbus_consumer.py` subscribes to `activity.events.v1` as `dope-memory-ingestor`. (services/working-memory-assistant/eventbus_consumer.py:L35-L37)
- `services/serena/eventbus_consumer.py` subscribes to `conport:events` with consumer group `serena`. (services/serena/eventbus_consumer.py:L98-L106)

## Bus Fragmentation Observations
- MISSING: no single canonical event-type registry shared across all producers/consumers; at least three incompatible registries exist (`src/dopemux/events/types.py`, `services/dopecon-bridge/event_bus.py`, `services/adhd_engine/event_emitter.py`). (src/dopemux/events/types.py:L23-L31)
- MISSING: no lane/persona field appears in primary event envelope dataclasses (`Event` in dopecon-bridge bus has `type/data/timestamp/source/workspace_path` only). (services/dopecon-bridge/event_bus.py:L37-L45)

