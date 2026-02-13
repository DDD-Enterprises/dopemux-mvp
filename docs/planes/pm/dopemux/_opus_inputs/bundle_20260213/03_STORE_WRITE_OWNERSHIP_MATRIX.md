# 03 Store Write Ownership Matrix

| store | owner writer service | other writers (if any) | interface (API vs direct DB) | evidence | determinism risk note |
|---|---|---|---|---|---|
| ConPort Postgres tables (`workspace_contexts`, `decisions`, `progress_entries`, `custom_data`) | `conport` server (`enhanced_server.py`) | `services/shared/conport_client/adapters/postgresql_adapter.py` (direct DB writes) | API + direct SQL | `docker/mcp-servers/conport/enhanced_server.py:245`, `:581`, `:642`, `:1062`, `:1415`; `services/shared/conport_client/adapters/postgresql_adapter.py:72`, `:175`, `:200`, `:344` | Multi-writer authority surface + bypass path |
| dope-memory chronicle SQLite (`chronicle.sqlite`) | `dope-memory` | UNKNOWN | direct SQLite via `ChronicleStore` | `compose.yml:487-490`; `services/working-memory-assistant/chronicle/store.py:256-314` | Single-service writer appears deterministic; retention deletes raw events by time |
| Redis `redis-events` streams | `dopecon-bridge`, `dope-memory` | potential other producers via `/events` endpoint | stream API (`XADD`/`XREADGROUP`) | `compose.yml:363`, `:481`; `services/dopecon-bridge/event_bus.py:314-317`; `services/working-memory-assistant/eventbus_consumer.py:314-320`, `:516` | Async ordering + open publisher surface |
| Redis `redis-primary` cache/stream | `conport` (cache writes), `adhd-engine` (event stream), likely `task-orchestrator` consumers | UNKNOWN | Redis direct | `compose.yml:243`, `:394`, `:437`; `docker/mcp-servers/conport/enhanced_server.py:616`; `services/adhd_engine/event_emitter.py:135-139` | Split Redis topology can fragment stream visibility |
| Qdrant | `dope-context` indexing pipeline | UNKNOWN (configured in `conport` and `dopecon-bridge`, write use not proven there) | Qdrant client API (`create_collection`, `upsert`) | `services/dope-context/src/pipeline/indexing_pipeline.py:371`, `:434`; `services/dope-context/src/search/dense_search.py:139`, `:270` | Index freshness/cache state affects retrieval determinism |
| Leantime MySQL/Redis | `leantime` | UNKNOWN | app DB/cache | `compose.yml:102-107`, `:127-134`, `:150-197` | Out of core authority contract scope unless explicitly included |

## Evidence excerpts
- `docker/mcp-servers/conport/enhanced_server.py:641-647`
```text
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO decisions
                    (id, workspace_id, summary, rationale, alternatives, tags,
                     confidence_level, decision_type)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, decision_id,
```
- `services/shared/conport_client/adapters/postgresql_adapter.py:172-179`
```text
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ag_catalog.workspace_contexts (workspace_id, session_id, active_context)
                VALUES ($1, $2, $3)
                ON CONFLICT (workspace_id, session_id)
                DO UPDATE SET active_context = $3, updated_at = NOW()
                """,
```
- `services/working-memory-assistant/chronicle/store.py:293-300`
```text
            INSERT OR IGNORE INTO raw_activity_events (
                id, workspace_id, instance_id, session_id,
                ts_utc, event_type, source,
                payload_json, redaction_level, ttl_days, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                final_event_id,
```
- `services/dopecon-bridge/event_bus.py:314-317`
```text
            # Publish to Redis
            msg_id = await self.redis_client.xadd(
                stream,
                event.to_redis_dict()
            )
```
- `services/adhd_engine/event_emitter.py:135-139`
```text
            await self._redis.xadd(
                self.stream_name,
                event.to_redis_dict(),
                maxlen=10000  # Keep reasonable stream length
            )
```
- `services/dope-context/src/search/dense_search.py:139-145`
```text
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "content_vec": VectorParams(
                        size=self.vector_size,
                        distance=Distance.DOT,
```
