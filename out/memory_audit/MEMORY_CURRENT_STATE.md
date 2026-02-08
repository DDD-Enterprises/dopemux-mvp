# MEMORY_CURRENT_STATE

## 1) Canonical Working Memory (Dope-Memory SQLite)

### Storage Location and Lifecycle
- Canonical store is per-workspace SQLite `chronicle.db` under `DOPE_MEMORY_DATA_DIR/<workspace_id>/`, created by `ChronicleStore` on demand. (services/working-memory-assistant/eventbus_consumer.py:L283-L291)
- Schema is initialized from `chronicle/schema.sql` on store creation. (services/working-memory-assistant/chronicle/store.py:L52-L57)
- Raw event TTL cleanup job is available (`cleanup_expired_raw_events`) and can be run periodically by retention worker. (services/working-memory-assistant/chronicle/store.py:L124-L138)

### Schema (Exact)
- `raw_activity_events` columns: `id`, `workspace_id`, `instance_id`, `session_id`, `ts_utc`, `event_type`, `source`, `payload_json`, `redaction_level`, `ttl_days`, `created_at_utc`; indexes on `(workspace_id, instance_id, ts_utc DESC)` and `(event_type, ts_utc DESC)`. (services/working-memory-assistant/chronicle/schema.sql:L5-L27)
- `work_log_entries` columns include categorical fields (`category`, `entry_type`, `workflow_phase`), narrative fields (`summary`, `details_json`, `reasoning`), outcome/importance, tags and links JSON fields, parent linkage, created/updated timestamps; indexes include workspace/time, category/type, phase, and importance ordering. (services/working-memory-assistant/chronicle/schema.sql:L29-L83)
- `issue_links` columns: `id`, `workspace_id`, `instance_id`, `issue_entry_id`, `resolution_entry_id`, `confidence`, `evidence_window_min`, `created_at_utc`; foreign keys to `work_log_entries`; indexes on issue and resolution ids. (services/working-memory-assistant/chronicle/schema.sql:L85-L107)
- `reflection_cards` columns include reflection window, trajectory, top decisions/blockers/progress/next suggestions as JSON text, plus promotion candidates and timestamps. (services/working-memory-assistant/chronicle/schema.sql:L109-L132)
- `trajectory_state` columns include `current_stream`, `current_goal_json`, `last_steps_json`, and `(workspace_id, instance_id)` primary key. (services/working-memory-assistant/chronicle/schema.sql:L134-L146)
- `schema_migrations` table tracks applied schema version. (services/working-memory-assistant/chronicle/schema.sql:L149-L155)

### Search/Ranking Behavior
- `search_work_log` applies filters and deterministic ordering: `ORDER BY importance_score DESC, ts_utc DESC, id ASC`, with cursor semantics tied to the same ordering keys. (services/working-memory-assistant/chronicle/store.py:L231-L248)
- Query matching is SQL `LIKE` on `summary`; tags filtering is JSON-string `LIKE` overlap heuristic. (services/working-memory-assistant/chronicle/store.py:L270-L280)
- Reflection window retrieval also uses deterministic ordering with same sort tuple. (services/working-memory-assistant/chronicle/store.py:L617-L618)

## 2) Event-Driven Ingestion and Materialization

### Ingestion Contract
- Consumer subscribes to input stream `activity.events.v1`, consumer group `dope-memory-ingestor`; output stream is `memory.derived.v1`. (services/working-memory-assistant/eventbus_consumer.py:L35-L37)
- Processing pipeline per message: parse envelope -> redact payload -> write raw event -> promotion attempt -> write curated entry -> publish derived event. (services/working-memory-assistant/eventbus_consumer.py:L357-L368)
- Raw ingestion is always attempted for parsed events via `insert_raw_event`. (services/working-memory-assistant/eventbus_consumer.py:L398-L408)
- Promotion is deterministic and driven by fixed event allowlist/handlers in `PromotionEngine`. (services/working-memory-assistant/promotion/promotion.py:L13-L24)

### Materialized Event Shapes
- Derived event envelope fields: `id`, `ts`, `workspace_id`, `instance_id`, `type`, `source`, `data` serialized JSON. (services/working-memory-assistant/eventbus_consumer.py:L505-L513)
- Published derived types include `worklog.created`, `memory.pulse`, and `reflection.created`. (services/working-memory-assistant/eventbus_consumer.py:L445-L447)

### Redaction/Safety
- Redactor drops sensitive keys, regex-redacts secret patterns, hashes denylisted file paths, and enforces a 64KB payload cap. (services/working-memory-assistant/promotion/redactor.py:L37-L60)
- Redaction is fail-closed, returning minimal safe payload on error. (services/working-memory-assistant/promotion/redactor.py:L120-L126)

## 3) Reflection and Trajectory Layers
- Reflection generation is deterministic/rule-based with explicit claim of no LLM calls. (services/working-memory-assistant/reflection/reflection.py:L1-L11)
- Reflection selection logic produces top decisions/blockers and next suggestions via stable sorting passes. (services/working-memory-assistant/reflection/reflection.py:L189-L223)
- Trajectory state is updated and persisted per `(workspace_id, instance_id)` and includes conservative boost factor capped at `0.5`. (services/working-memory-assistant/trajectory/manager.py:L23-L29)
- Memory search re-ranks base results with trajectory boost before top-k truncation. (services/working-memory-assistant/dope_memory_main.py:L175-L199)

## 4) Postgres Mirror Layer
- Mirror schema includes `dm_raw_activity_events`, `dm_work_log_entries`, `dm_reflection_cards`, `dm_issue_links`, and migration table. (services/working-memory-assistant/chronicle/postgres_mirror.sql:L10-L147)
- Mirror adds search indexes unavailable in canonical SQLite, including `GIN(tags)`, `GIN(linked_files)`, and `summary_tsv` generated `tsvector` + `GIN` index. (services/working-memory-assistant/chronicle/postgres_mirror.sql:L77-L90)
- Mirror sync worker treats SQLite as source of truth and periodically upserts work logs and issue links. (services/working-memory-assistant/postgres_mirror_sync.py:L37-L43)
- Raw event sync is currently disabled (`return 0`) in `_sync_raw_events`. (services/working-memory-assistant/postgres_mirror_sync.py:L284-L291)

## 5) Other Memory/Context Systems in Repo

### ConPort Context Hydration Cache (Dopecon-Bridge)
- Middleware hydrates `request.state.context` via ConPort token and persists request deltas back on response completion. (services/dopecon-bridge/main.py:L628-L661)
- Fallback context cache is stored in Redis key `context_fallback:{context_token}` with 1-hour TTL. (services/dopecon-bridge/main.py:L577-L610)

### Local ADHD Context Manager (Legacy/Parallel)
- Separate SQLite database `.dopemux/context.db` stores `context_snapshots`, `session_metadata`, and `session_tags`. (src/dopemux/adhd/context_manager.py:L94-L101)
- This store is independent of dope-memory chronicle schema. (src/dopemux/adhd/context_manager.py:L189-L233)

### ConPort Memory Server (Graph + Vectors)
- ConPort memory server is defined as unified graph memory with Milvus vectors and PostgreSQL truth layer. (src/conport/memory_server.py:L5-L9)
- Milvus collections include `decisions/messages/files/tasks/agents/threads/runs` and similarity search across selected collections. (src/conport/memory_server.py:L104-L115)

## 6) Deterministic vs Non-Deterministic Retrieval
- Deterministic-first retrieval exists in dope-memory (`search_work_log` ordering and deterministic promotion/reflection). (services/working-memory-assistant/chronicle/store.py:L313-L315)
- Non-deterministic/vector retrieval exists in ConPort memory (vector similarity via Milvus distance ranking). (src/conport/memory_server.py:L211-L218)

## 7) Current-State Gaps (Observed in Code)
- MISSING: unified multi-layer memory facade that combines chronicle SQLite + mirror + ConPort vector layers behind one retrieval contract. (services/working-memory-assistant/chronicle/store.py:L21-L29)
- MISSING: lane/persona selector in memory schema or ingestion envelope (no `lane` column in raw/curated tables). (services/working-memory-assistant/chronicle/schema.sql:L5-L20)
- MISSING: canonical audit table recording per-response injected context slices and rationale. (services/working-memory-assistant/chronicle/schema.sql:L149-L152)

