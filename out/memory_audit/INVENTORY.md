# INVENTORY

## Scope
- Runtime implementation artifacts audited for event bus, memory/context persistence, and prompt/context injection surfaces are concentrated in `src/dopemux/`, `services/dopecon-bridge/`, `services/working-memory-assistant/`, `services/adhd_engine/`, `services/serena/`, `services/dope-context/`, `src/conport/`, and `services/registry.yaml`. (services/registry.yaml:L1-L20)

## Repo Map (Relevant Tree)
- `src/dopemux/event_bus.py` - core abstract event bus + in-memory and Redis adapters. (src/dopemux/event_bus.py:L68-L80)
- `src/dopemux/events/types.py` - typed Dopemux event models and enums. (src/dopemux/events/types.py:L23-L31)
- `services/dopecon-bridge/event_bus.py` - production Redis Streams event bus with dedup/rate-limit/metrics. (services/dopecon-bridge/event_bus.py:L70-L80)
- `services/dopecon-bridge/main.py` - service startup, EventBus wiring, publish/subscribe/event history endpoints, and DDG ingestion subscriber. (services/dopecon-bridge/main.py:L1713-L1731)
- `services/dopecon-bridge/integrations/adhd_engine.py` - ADHD integration event producer. (services/dopecon-bridge/integrations/adhd_engine.py:L101-L111)
- `services/dopecon-bridge/integrations/dope_context.py` - Dope-Context integration event producer. (services/dopecon-bridge/integrations/dope_context.py:L25-L37)
- `services/dopecon-bridge/dopecon_bridge/event_bus.py` - secondary/minimal route-level EventBus wrapper. (services/dopecon-bridge/dopecon_bridge/event_bus.py:L69-L80)
- `services/dopecon-bridge/dopecon_bridge/routes.py` - minimal publish/stream/history routes using the secondary EventBus. (services/dopecon-bridge/dopecon_bridge/routes.py:L149-L196)
- `services/working-memory-assistant/chronicle/schema.sql` - canonical SQLite memory schema. (services/working-memory-assistant/chronicle/schema.sql:L5-L20)
- `services/working-memory-assistant/chronicle/store.py` - persistence/read APIs, deterministic search ordering, reflection/trajectory helpers. (services/working-memory-assistant/chronicle/store.py:L216-L248)
- `services/working-memory-assistant/eventbus_consumer.py` - event-driven ingestion and materialization pipeline. (services/working-memory-assistant/eventbus_consumer.py:L210-L218)
- `services/working-memory-assistant/promotion/promotion.py` - deterministic promotion policy. (services/working-memory-assistant/promotion/promotion.py:L78-L83)
- `services/working-memory-assistant/promotion/redactor.py` - redaction and payload safety controls. (services/working-memory-assistant/promotion/redactor.py:L102-L107)
- `services/working-memory-assistant/reflection/reflection.py` - deterministic reflection materialization (no LLM). (services/working-memory-assistant/reflection/reflection.py:L1-L11)
- `services/working-memory-assistant/trajectory/manager.py` - trajectory state + deterministic boost logic. (services/working-memory-assistant/trajectory/manager.py:L94-L107)
- `services/working-memory-assistant/dope_memory_main.py` - memory HTTP/MCP entrypoint and background worker lifecycle. (services/working-memory-assistant/dope_memory_main.py:L767-L805)
- `services/working-memory-assistant/chronicle/postgres_mirror.sql` - Postgres mirror schema and search indexes. (services/working-memory-assistant/chronicle/postgres_mirror.sql:L35-L90)
- `services/working-memory-assistant/postgres_mirror_sync.py` - SQLite->Postgres mirror worker. (services/working-memory-assistant/postgres_mirror_sync.py:L35-L43)
- `services/claude_brain/brain_manager.py` - LLM request assembly and completion call. (services/claude_brain/brain_manager.py:L375-L392)
- `services/dope-context/src/context/openai_generator.py` - OpenAI context-generation prompt assembly and call. (services/dope-context/src/context/openai_generator.py:L131-L148)
- `services/dope-context/src/context/claude_generator.py` - Claude context-generation prompt assembly and call. (services/dope-context/src/context/claude_generator.py:L249-L258)
- `services/dope-context/src/context/grok_generator.py` - Grok/OpenRouter context-generation prompt assembly and call. (services/dope-context/src/context/grok_generator.py:L95-L121)
- `src/dopemux/adhd/context_manager.py` - legacy/local SQLite context snapshots. (src/dopemux/adhd/context_manager.py:L189-L203)
- `src/conport/memory_server.py` - ConPort memory graph server (Milvus+Postgres). (src/conport/memory_server.py:L5-L9)
- `src/dopemux/roles/catalog.py` - role/persona catalog (lane-adjacent). (src/dopemux/roles/catalog.py:L57-L67)
- `src/dopemux/cli.py` - role activation CLI wiring. (src/dopemux/cli.py:L97-L103)
- `services/adhd_engine/event_emitter.py` - ADHD Engine Redis producer. (services/adhd_engine/event_emitter.py:L53-L59)
- `services/adhd_engine/event_listener.py` - ADHD Engine Redis consumer and dispatch router. (services/adhd_engine/event_listener.py:L37-L46)
- `services/task-orchestrator/app/services/enhanced_orchestrator.py` - task-orchestrator EventBus consumer. (services/task-orchestrator/app/services/enhanced_orchestrator.py:L1296-L1308)
- `services/activity-capture/event_subscriber.py` - activity-capture Redis consumer. (services/activity-capture/event_subscriber.py:L17-L23)
- `services/workspace-watcher/event_emitter.py` - workspace-watcher event producer. (services/workspace-watcher/event_emitter.py:L30-L35)
- `services/serena/eventbus_consumer.py` - Serena stream consumer (`conport:events`). (services/serena/eventbus_consumer.py:L96-L103)

## File Catalog (Purpose, Key Types/Functions, References)

### Event Bus + Coordination
- `src/dopemux/event_bus.py`
  - Purpose: defines `EventBus` abstraction and adapters (`InMemoryAdapter`, `RedisStreamsAdapter`). (src/dopemux/event_bus.py:L68-L82)
  - Key types/functions: `DopemuxEvent.create`, `publish`, `subscribe`, `unsubscribe`. (src/dopemux/event_bus.py:L55-L80)
  - Referenced by: `services/taskmaster/server.py` imports and uses `RedisStreamsAdapter` + `DopemuxEvent`. (services/taskmaster/server.py:L28-L28)
- `src/dopemux/events/types.py`
  - Purpose: typed event schema (`Event` + specialized domain events). (src/dopemux/events/types.py:L23-L31)
  - Key types/functions: `WorktreeEvent`, `ContextEvent`, `ADHDEvent`, `ThemeEvent`, `SessionEvent`. (src/dopemux/events/types.py:L36-L115)
  - Referenced by: `src/dopemux/event_bus.py` imports `Event`/`EventPriority`. (src/dopemux/event_bus.py:L16-L16)
- `services/dopecon-bridge/event_bus.py`
  - Purpose: Redis Streams coordination bus with operational controls. (services/dopecon-bridge/event_bus.py:L70-L80)
  - Key types/functions: `EventType`, `Event`, `EventBus.publish`, `EventBus.subscribe`, `get_stream_info`. (services/dopecon-bridge/event_bus.py:L25-L35)
  - Referenced by: `services/dopecon-bridge/main.py` global `event_bus` and event endpoints. (services/dopecon-bridge/main.py:L79-L79)
- `services/dopecon-bridge/main.py`
  - Purpose: bootstraps coordination service and wires `EventBus` + DDG ingestion. (services/dopecon-bridge/main.py:L1713-L1731)
  - Key types/functions: `start_ddg_ingestion`, `/events`, `/events/stream`, `/events/history`. (services/dopecon-bridge/main.py:L334-L343)
  - Referenced by: runtime entrypoint for dopecon-bridge service registered as coordination layer. (services/registry.yaml:L106-L117)

### Memory + Persistence
- `services/working-memory-assistant/chronicle/schema.sql`
  - Purpose: canonical SQLite schema for raw/curated memory layers. (services/working-memory-assistant/chronicle/schema.sql:L1-L20)
  - Key tables: `raw_activity_events`, `work_log_entries`, `issue_links`, `reflection_cards`, `trajectory_state`. (services/working-memory-assistant/chronicle/schema.sql:L5-L146)
  - Referenced by: `ChronicleStore.initialize_schema`. (services/working-memory-assistant/chronicle/store.py:L52-L57)
- `services/working-memory-assistant/chronicle/store.py`
  - Purpose: CRUD/search/materialization helper for chronicle SQLite. (services/working-memory-assistant/chronicle/store.py:L21-L29)
  - Key functions: `insert_raw_event`, `cleanup_expired_raw_events`, `search_work_log`, `insert_reflection_card`, `upsert_trajectory_state`. (services/working-memory-assistant/chronicle/store.py:L63-L76)
  - Referenced by: `dope_memory_main.py`, `eventbus_consumer.py`, `postgres_mirror_sync.py`. (services/working-memory-assistant/dope_memory_main.py:L39-L39)
- `services/working-memory-assistant/eventbus_consumer.py`
  - Purpose: stream ingestion (`activity.events.v1`) to derived memory outputs (`memory.derived.v1`). (services/working-memory-assistant/eventbus_consumer.py:L4-L10)
  - Key functions: `start`, `_process_message`, `_publish_derived_event`, `_generate_reflection_boundary`, `_index_in_dopecontext`. (services/working-memory-assistant/eventbus_consumer.py:L293-L303)
  - Referenced by: optional startup path in `dope_memory_main.py`. (services/working-memory-assistant/dope_memory_main.py:L767-L779)
- `services/working-memory-assistant/dope_memory_main.py`
  - Purpose: service entrypoint exposing memory tools and background workers. (services/working-memory-assistant/dope_memory_main.py:L3-L12)
  - Key functions: `memory_search`, `memory_store`, `memory_recap`, `memory_generate_reflection`, `memory_trajectory`; lifecycle worker startup. (services/working-memory-assistant/dope_memory_main.py:L907-L929)
  - Referenced by: registry entry as `dope-memory` service. (services/registry.yaml:L146-L159)
- `services/working-memory-assistant/chronicle/postgres_mirror.sql`
  - Purpose: Postgres mirror schema for multi-service access and text search. (services/working-memory-assistant/chronicle/postgres_mirror.sql:L1-L6)
  - Key schema: `dm_work_log_entries`, `summary_tsv` generated column + GIN index. (services/working-memory-assistant/chronicle/postgres_mirror.sql:L35-L90)
  - Referenced by: `PostgresMirrorSync._ensure_schema`. (services/working-memory-assistant/postgres_mirror_sync.py:L90-L111)
- `services/working-memory-assistant/postgres_mirror_sync.py`
  - Purpose: async replication worker from SQLite canonical to Postgres mirror. (services/working-memory-assistant/postgres_mirror_sync.py:L2-L10)
  - Key functions: `_sync_work_log_entries`, `_sync_raw_events`, `_sync_issue_links`. (services/working-memory-assistant/postgres_mirror_sync.py:L199-L205)
  - Referenced by: optional startup path in `dope_memory_main.py`. (services/working-memory-assistant/dope_memory_main.py:L793-L805)

### Prompt/Context Injection Surfaces
- `services/claude_brain/brain_manager.py`
  - Purpose: composes LLM messages and dispatches via LiteLLM. (services/claude_brain/brain_manager.py:L375-L392)
  - Key functions: `_prepare_messages`, `_get_system_prompt`, `_optimize_temperature`, `_optimize_max_tokens`. (services/claude_brain/brain_manager.py:L447-L529)
  - Referenced by: claude-brain service runtime manager module. (services/claude_brain/brain_manager.py:L83-L90)
- `services/dope-context/src/context/openai_generator.py`
  - Purpose: OpenAI-based context generation for code chunks. (services/dope-context/src/context/openai_generator.py:L131-L148)
  - Key functions: `_build_prompt`, `generate_context`, batch generation. (services/dope-context/src/context/openai_generator.py:L218-L241)
  - Referenced by: dope-context context generation pipeline implementation. (services/dope-context/src/context/openai_generator.py:L184-L216)
- `services/dope-context/src/context/claude_generator.py`
  - Purpose: Claude-based context generation with deterministic settings. (services/dope-context/src/context/claude_generator.py:L252-L258)
  - Key functions: `_build_context_prompt`, `generate_context`. (services/dope-context/src/context/claude_generator.py:L167-L215)
  - Referenced by: dope-context context generation pipeline implementation. (services/dope-context/src/context/claude_generator.py:L217-L233)
- `services/dope-context/src/context/grok_generator.py`
  - Purpose: Grok/OpenRouter-based context generation. (services/dope-context/src/context/grok_generator.py:L103-L121)
  - Key functions: prompt construction with input truncation (`chunk_content[:2000]`), OpenRouter call. (services/dope-context/src/context/grok_generator.py:L95-L101)
  - Referenced by: dope-context context generation pipeline implementation. (services/dope-context/src/context/grok_generator.py:L103-L123)

### Other Memory/Context Stores
- `src/dopemux/adhd/context_manager.py`
  - Purpose: local context snapshot manager with SQLite backing. (src/dopemux/adhd/context_manager.py:L79-L89)
  - Key schema: `context_snapshots`, `session_metadata`, `session_tags`. (src/dopemux/adhd/context_manager.py:L194-L233)
  - Referenced by: CLI imports `ContextManager`. (src/dopemux/cli.py:L53-L53)
- `src/conport/memory_server.py`
  - Purpose: ConPort memory graph server with vector + relational layers. (src/conport/memory_server.py:L5-L9)
  - Key types/functions: `MilvusManager`, `PostgreSQLManager`, embedding and semantic search methods. (src/conport/memory_server.py:L73-L83)
  - Referenced by: ConPort runtime module itself as MCP memory surface. (src/conport/memory_server.py:L3-L10)

### Lane/Persona Signals
- `src/dopemux/roles/catalog.py`
  - Purpose: role/persona catalog with required/optional servers and attention state. (src/dopemux/roles/catalog.py:L57-L67)
  - Key types/functions: `RoleSpec`, `ROLE_CATALOG`, `activate_role`. (src/dopemux/roles/catalog.py:L29-L41)
  - Referenced by: CLI role activation import. (src/dopemux/cli.py:L97-L103)
- `src/dopemux/cli.py`
  - Purpose: CLI startup wiring, including role activation hooks. (src/dopemux/cli.py:L3-L7)
  - Key functions: role wiring and profile/attention defaults setup. (src/dopemux/cli.py:L126-L162)
  - Referenced by: Dopemux command entrypoint module. (src/dopemux/cli.py:L1-L4)

