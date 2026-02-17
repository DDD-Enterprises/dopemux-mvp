# Dopemux Memory Surface Audit

## Scope + Method
- [VERIFIED] This inventory is built from in-repo code/spec evidence with line citations, plus service registry reconciliation.
- [VERIFIED] Service registry defines core memory-related services: `dope-query` (ConPort runtime), `dope-memory`, `redis`, `qdrant`, `dopecon-bridge`, and ADHD services. (source: `services/registry.yaml:44-76`, `services/registry.yaml:89-117`, `services/registry.yaml:134-158`, `services/registry.yaml:246-268`)

## 1) Inventory: Existing Memory/Context Systems

### 1.1 Dope-Memory (working-memory-assistant)
- [VERIFIED] SQLite canonical schema exists with raw events, curated work logs, reflection cards, issue links, and trajectory state tables. (source: `services/working-memory-assistant/chronicle/schema.sql:5-155`)
- [VERIFIED] Deterministic search ordering and cursor pagination are implemented as `(importance_score DESC, ts_utc DESC, id ASC)` with scope-aware cursors. (source: `services/working-memory-assistant/chronicle/store.py:216-321`, `services/working-memory-assistant/mcp/server.py:88-120`, `services/working-memory-assistant/mcp/server.py:174-220`)
- [VERIFIED] MCP tool surface includes `memory_search`, `memory_store`, `memory_recap`, `memory_mark_issue`, `memory_link_resolution`, `memory_replay_session` and enforces Top-K bounds. (source: `services/working-memory-assistant/mcp/server.py:48-57`, `services/working-memory-assistant/mcp/server.py:132-157`, `services/working-memory-assistant/mcp/server.py:520-541`)
- [VERIFIED] Redaction is enforced before persistence with denylist paths, sensitive keys, regex secret detectors, and payload size caps. (source: `services/working-memory-assistant/promotion/redactor.py:16-99`, `services/working-memory-assistant/promotion/redactor.py:102-179`)
- [VERIFIED] Promotion engine is deterministic and rule-based for specific event types (no LLM in Phase 1). (source: `services/working-memory-assistant/promotion/promotion.py:13-35`, `services/working-memory-assistant/promotion/promotion.py:78-117`)
- [VERIFIED] HTTP entrypoint (`dope_memory_main.py`) exposes `/health` and `/tools/*` endpoints, with optional EventBus consumer, retention job, and Postgres mirror sync. (source: `services/working-memory-assistant/dope_memory_main.py:49-53`, `services/working-memory-assistant/dope_memory_main.py:705-716`, `services/working-memory-assistant/dope_memory_main.py:752-809`, `services/working-memory-assistant/dope_memory_main.py:872-1090`)

### 1.2 Event-Driven Ingestion (Dope-Memory consumer)
- [VERIFIED] Consumer subscribes to `activity.events.v1`, writes raw events, promotes curated entries, and publishes derived events on `memory.derived.v1`. (source: `services/working-memory-assistant/eventbus_consumer.py:35-39`, `services/working-memory-assistant/eventbus_consumer.py:214-218`, `services/working-memory-assistant/eventbus_consumer.py:395-457`, `services/working-memory-assistant/eventbus_consumer.py:493-516`)
- [VERIFIED] Phase-2 behavior includes pulse emission, idle/session-end reflection triggers, and optional DopeContext indexing (`worklog_index`). (source: `services/working-memory-assistant/eventbus_consumer.py:523-613`, `services/working-memory-assistant/eventbus_consumer.py:617-687`, `services/working-memory-assistant/eventbus_consumer.py:714-753`)

### 1.3 ConPort / DopeQuery / Bridge surfaces
- [VERIFIED] Registry defines `dope-query` as ConPort runtime (“knowledge graph and context management MCP server”). (source: `services/registry.yaml:90-101`)
- [VERIFIED] Dopecon-bridge includes a ConPort client + HTTP middleware that hydrates request state from `X-Context-Token` and persists context deltas after request completion. (source: `services/dopecon-bridge/main.py:507-575`, `services/dopecon-bridge/main.py:621-665`, `services/dopecon-bridge/main.py:1432-1433`)
- [VERIFIED] Task-orchestrator adapter reads ADHD state from ConPort active context (`energy`, `attention`, `mode`). (source: `services/task-orchestrator/app/adapters/conport_adapter.py:1125-1162`)

### 1.4 Dope-Context surfaces
- [VERIFIED] `dope-context` MCP server exposes semantic search/indexing tools and includes ADHD dynamic top-k behavior. (source: `services/dope-context/src/mcp/server.py:1-10`, `services/dope-context/src/mcp/server.py:124-180`)
- [VERIFIED] Context generators exist for Claude and OpenAI APIs with caching/cost tracking; used for contextual retrieval/indexing workflows. (source: `services/dope-context/src/context/claude_generator.py:102-111`, `services/dope-context/src/context/claude_generator.py:217-257`, `services/dope-context/src/context/openai_generator.py:47-57`, `services/dope-context/src/context/openai_generator.py:92-173`)
- [VERIFIED] Hybrid search uses BM25 + dense vectors with RRF fusion and deterministic weighted ranking flow. (source: `services/dope-context/src/search/hybrid_search.py:55-84`, `services/dope-context/src/search/hybrid_search.py:183-194`, `services/dope-context/src/search/hybrid_search.py:214-329`)

### 1.5 Architecture specs (Dope-Memory v1)
- [VERIFIED] Spec positions Dope-Memory as temporal/working memory, with no duplication of DopeQuery/DopeContext, strict redaction, Top-3 ADHD boundaries, and deterministic output requirements. (source: `docs/spec/dope-memory/v1/00_overview.md:26-48`, `docs/spec/dope-memory/v1/00_overview.md:49-90`)
- [VERIFIED] Spec defines event stream contracts (`activity.events.v1`, `memory.derived.v1`) and deterministic ranking/pagination semantics. (source: `docs/spec/dope-memory/v1/01_architecture.md:50-107`)
- [VERIFIED] Spec defines Postgres mirror (`dm_*`) and FTS/GIN surfaces. (source: `docs/spec/dope-memory/v1/03_data_model_postgres.md:20-105`)

## 2) Context Injection Today (Current State)
- [VERIFIED] Injection is currently decentralized, not a single global lane injector:
  - Request-level ConPort hydration via `X-Context-Token` middleware in dopecon-bridge. (source: `services/dopecon-bridge/main.py:628-665`)
  - Retrieval-based context assembly in dope-context search/context-generation paths. (source: `services/dope-context/src/mcp/server.py:1500-1533`, `services/dope-context/src/context/claude_generator.py:167-215`)
  - Recap/search APIs in Dope-Memory with explicit `workspace_id/instance_id/session_id` scoping and `top_k` controls. (source: `services/working-memory-assistant/mcp/server.py:132-248`, `services/working-memory-assistant/mcp/server.py:312-443`)
- [INFERRED] There is no single repository-wide “lane registry” that centrally enforces opt-in injection policy per lane today; enforcement appears service-local.

## 3) Lane-Like Constructs Already Present
- [VERIFIED] Profile model mandates ConPort in all profiles and treats it as memory authority. (source: `src/dopemux/profile_models.py:143-199`)
- [VERIFIED] Profile config already models shared-vs-local memory stores (shared ConPort + local context/Serena DBs). (source: `config/profiles/python-ml.yaml:42-57`)
- [VERIFIED] Router modes in dope_brainz router (`default`, `background`, `think`, `webSearch`) are explicit traffic lanes for model routing. (source: `src/dopemux/dope_brainz_router.py:111-137`)
- [VERIFIED] Dope-Memory already has structural lanes at data level via `category`, `entry_type`, `workflow_phase`, and `tags`. (source: `services/working-memory-assistant/chronicle/schema.sql:38-70`)

## 4) Event Catalog (Producer/Consumer map)

### 4.1 Core event types and envelopes
- [VERIFIED] Shared event model includes `type`, `timestamp`, `priority`, `data`, `source`; typed events include `ContextEvent`, `ADHDEvent`, `SessionEvent`. (source: `src/dopemux/events/types.py:23-115`)
- [VERIFIED] Dopecon-bridge EventBus event types include `decision_logged`, `progress_updated`, `session_started`, etc. (source: `services/dopecon-bridge/event_bus.py:25-35`)

### 4.2 Streams and endpoints
- [VERIFIED] Dopecon-bridge publishes/subscribes via Redis Streams, consumer groups, ack/retry semantics; stream defaults include `dopemux:events` and `dopemux:cross-plane` usage in routes. (source: `services/dopecon-bridge/event_bus.py:70-80`, `services/dopecon-bridge/event_bus.py:239-317`, `services/dopecon-bridge/main.py:1812-1953`, `services/dopecon-bridge/main.py:2826-2937`)
- [VERIFIED] Dope-Memory consumer ingests `activity.events.v1`, emits `memory.derived.v1`, and emits `worklog.created`, `memory.pulse`, `reflection.created`. (source: `services/working-memory-assistant/eventbus_consumer.py:35-39`, `services/working-memory-assistant/eventbus_consumer.py:444-457`, `services/working-memory-assistant/eventbus_consumer.py:599-677`)
- [VERIFIED] Conport bridge schemas define dotted event names (`decision.logged`, `decision.updated`, `progress.updated`). (source: `docker/mcp-servers/conport-bridge/event_schemas.py:7-36`)

### 4.3 Startup wiring
- [VERIFIED] Dopecon-bridge startup initializes DB/cache/MCP/ConPort/EventBus and launches background DDG ingestion from `dopemux:events`. (source: `services/dopecon-bridge/main.py:1713-1733`, `services/dopecon-bridge/main.py:334-431`)

## 5) Storage + Search Surfaces
- [VERIFIED] Redis is used for event streaming/caching; qdrant is registered as vector DB; Postgres is used by bridge and spec’d as mirror for Dope-Memory. (source: `services/registry.yaml:44-76`, `services/registry.yaml:66-87`, `services/dopecon-bridge/main.py:116-119`, `docs/spec/dope-memory/v1/03_data_model_postgres.md:15-17`)
- [VERIFIED] Dope-Memory canonical persists in SQLite (`chronicle.db`) with WAL mode and schema initialization. (source: `services/working-memory-assistant/chronicle/store.py:34-57`)
- [VERIFIED] Deterministic retrieval contract and Top-3 boundary are specified and implemented in both spec and server code. (source: `docs/spec/dope-memory/v1/06_retrieval_ranking.md:35-48`, `docs/spec/dope-memory/v1/07_mcp_contracts.md:14-39`, `services/working-memory-assistant/mcp/server.py:156-157`)

## 6) Registry Reconciliation: Memory-Related Services Missed by Registry
- [VERIFIED] Service directories include additional memory/context-adjacent modules not currently listed in `services/registry.yaml` entries shown above, including `dope-context`, `working-memory-assistant`, `claude_brain`, `intelligence`, `session-intelligence`, and `conport`. (source: `services/registry.yaml:20-293`, `_audit_out/_sources/services_dir_listing.txt:9-37`)
- [VERIFIED] `dope-context` directory exists (`services/dope-context`), but no `name: dope-context` entry appears in registry grep hits. (source: `_audit_out/_sources/services_dir_listing.txt:12`, `services/registry.yaml:44-293`)
- [INFERRED] Registry and service-directory drift is present for memory integration planning and should be normalized before lane-level rollout.

## 7) VERIFIED vs INFERRED vs UNKNOWN Summary
- VERIFIED: Event streams, promotion/redaction pipeline, deterministic ranking/pagination, ConPort middleware hydration, Dope-Memory/DopeContext active code paths.
- INFERRED: No centralized lane registry yet; lane behavior currently distributed across service-local contracts.
- UNKNOWN:
  - Whether unregistered memory-adjacent services (`claude_brain`, `intelligence`, `session-intelligence`) are production-active or experimental.
  - Whether `wma_core.py` prototype paths are intentionally deprecated in favor of `dope_memory_main.py` + `eventbus_consumer.py`. (source: `services/working-memory-assistant/wma_core.py:1-7`)
