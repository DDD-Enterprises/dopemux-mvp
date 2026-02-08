# GAPS_AND_RECOMMENDATIONS

## Requirement 1: Multi-layer Memory
- Current state: multiple layers exist but are fragmented across separate stores/services (dope-memory SQLite canonical, optional Postgres mirror, ConPort Milvus+Postgres graph, legacy `.dopemux/context.db`). (services/working-memory-assistant/chronicle/schema.sql:L5-L20)
- Current state: dope-memory worker treats SQLite as canonical and mirror as replication target, with raw mirror sync disabled. (services/working-memory-assistant/postgres_mirror_sync.py:L284-L291)
- Current state: ConPort memory server independently manages vector collections and relational graph truth. (src/conport/memory_server.py:L73-L83)
- MISSING: single retrieval/materialization contract spanning deterministic chronicle + graph/vector layers. (services/working-memory-assistant/chronicle/store.py:L21-L29)
- Smallest addition:
  - New file: `src/dopemux/memory/layered_memory_router.py`.
  - Interface: `LayeredMemoryRouter.retrieve(query, lane, scope, top_k) -> LayeredMemoryResult`.
  - Behavior: call deterministic layer first (chronicle), then optional semantic layer (ConPort/dope-context), return merged ranked bundle with provenance IDs.

## Requirement 2: Opt-in Injection Per Lane
- Current state: role/persona catalog exists with role keys, attention states, and enabled server sets. (src/dopemux/roles/catalog.py:L57-L77)
- Current state: role activation exports environment role metadata but no injection policy object is applied at LLM call sites. (src/dopemux/roles/catalog.py:L298-L313)
- Current state: primary LLM injection appends raw `request.context` whenever provided, without lane gating. (services/claude_brain/brain_manager.py:L456-L460)
- MISSING: lane-scoped, opt-in injection policy checks at prompt assembly points. (services/claude_brain/brain_manager.py:L447-L460)
- Smallest addition:
  - New file: `src/dopemux/memory/lane_injection_policy.py`.
  - Interface: `LaneInjectionPolicy.should_inject(lane, source_kind) -> bool` and `LaneInjectionPolicy.max_tokens(lane, source_kind) -> int`.
  - Integrations: enforce in `services/claude_brain/brain_manager.py` and dope-context generator call paths.

## Requirement 3: Event-driven Ingestion and Materialization
- Current state: event-driven ingestion exists in dope-memory (`activity.events.v1` -> chronicle writes -> `memory.derived.v1`). (services/working-memory-assistant/eventbus_consumer.py:L35-L37)
- Current state: dopecon-bridge has active Redis stream publish/subscribe APIs and DDG ingestion worker on `dopemux:events`. (services/dopecon-bridge/main.py:L1819-L1842)
- Current state: stream landscape is fragmented (`dopemux:events`, `activity.events.v1`, `memory.derived.v1`, `conport:events`) without one canonical memory-ingest contract. (services/serena/eventbus_consumer.py:L98-L103)
- MISSING: shared event schema/versioning for memory ingestion and cross-service memory materialization events. (services/dopecon-bridge/event_bus.py:L25-L35)
- Smallest addition:
  - New file: `src/dopemux/events/memory_events.py`.
  - Interface: typed envelopes for `memory.ingest.v1`, `memory.materialized.v1`, `memory.injected.v1` with required fields (`workspace_id`, `instance_id`, `lane`, `source_ids`, `reason_codes`).
  - New file: `config/routing/memory_event_routes.yaml` to map streams and consumer groups.

## Requirement 4: Deterministic-first Retrieval
- Current state: dope-memory search and reflection flows are deterministic and ordered by explicit sort keys. (services/working-memory-assistant/chronicle/store.py:L313-L315)
- Current state: ConPort memory retrieval is vector-similarity based. (src/conport/memory_server.py:L211-L218)
- MISSING: global retrieval policy that enforces deterministic pass before semantic/vector pass for injection use-cases. (services/working-memory-assistant/dope_memory_main.py:L161-L173)
- Smallest addition:
  - New file: `src/dopemux/memory/retrieval_plan.py`.
  - Interface: `build_retrieval_plan(query, lane) -> [DeterministicStep, OptionalSemanticStep]`.
  - Integration: `LayeredMemoryRouter` executes this plan and annotates output with `plan_path`.

## Requirement 5: Audit Log of What Was Injected and Why
- Current state: dope-memory schema has no table capturing LLM injection records. (services/working-memory-assistant/chronicle/schema.sql:L149-L152)
- Current state: current LLM assembly functions return/send messages but do not persist injection provenance. (services/claude_brain/brain_manager.py:L447-L461)
- MISSING: append-only injection audit table and writer API. (services/working-memory-assistant/chronicle/schema.sql:L149-L152)
- Smallest addition:
  - Schema change file: `services/working-memory-assistant/chronicle/schema_v1_1_memory_injection_audit.sql`.
  - New table: `memory_injection_audit(id, ts_utc, workspace_id, instance_id, lane, model, source_entry_ids_json, injected_payload_hash, injected_chars, reason_codes_json, decision_trace_json)`.
  - New module: `services/working-memory-assistant/audit/injection_audit_writer.py` with `log_injection(...)` called by LLM injection sites.

## Minimal Implementation Sequence
- Step 1: Add typed memory event contracts (`src/dopemux/events/memory_events.py`) and route map (`config/routing/memory_event_routes.yaml`) to remove stream/schema ambiguity. (services/dopecon-bridge/main.py:L1814-L1820)
- Step 2: Add lane injection policy module and enforce in `brain_manager` before appending `request.context`. (services/claude_brain/brain_manager.py:L456-L460)
- Step 3: Add layered retrieval router and deterministic-first plan modules, with chronicle-first then optional semantic fallback. (services/working-memory-assistant/chronicle/store.py:L216-L248)
- Step 4: Add injection audit schema + writer and emit `memory.injected.v1` event after each injected LLM call. (services/working-memory-assistant/eventbus_consumer.py:L493-L515)
- Step 5: Wire role catalog lane mapping into injection policy so lane behavior is opt-in and explicit. (src/dopemux/roles/catalog.py:L57-L67)

## Explicit Missing Items Summary
- MISSING: unified layered retrieval interface. (services/working-memory-assistant/chronicle/store.py:L21-L29)
- MISSING: lane-level opt-in injection policy. (services/claude_brain/brain_manager.py:L456-L460)
- MISSING: shared memory event schema/versioning. (services/dopecon-bridge/event_bus.py:L25-L35)
- MISSING: deterministic-first retrieval planner shared across services. (services/working-memory-assistant/dope_memory_main.py:L161-L173)
- MISSING: injection audit persistence and emitted audit event. (services/working-memory-assistant/chronicle/schema.sql:L149-L152)
