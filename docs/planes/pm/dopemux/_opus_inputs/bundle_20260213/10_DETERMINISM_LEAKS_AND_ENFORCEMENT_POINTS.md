# 10 Determinism Leaks And Enforcement Points

Only evidence-backed leaks are listed.

| leak | evidence | impact | enforcement point |
|---|---|---|---|
| Unauthenticated event publish surface | `services/dopecon-bridge/dopecon_bridge/routes.py:149-165` (no `Depends(get_current_user)` on `/events`) | any caller can publish arbitrary event/source into shared stream | require auth dependency on `events_router.post` + signature validation for emitters |
| ConPort write routes without explicit auth checks in runtime file | `docker/mcp-servers/conport/enhanced_server.py:245-272` + auth search yielded no matches | authority records can be mutated without in-handler auth gate | enforce API-key/JWT middleware for all write routes |
| Authority DB multi-writer bypass | `docker/mcp-servers/conport/enhanced_server.py` writes + `services/shared/conport_client/adapters/postgresql_adapter.py` direct inserts/upserts | contract drift and non-audited writes | block direct DB writes outside authority service; enforce write-only through authenticated API |
| Split Redis topology for overlapping event namespace | `compose.yml:363` (`dopecon-bridge` -> `redis-events`) vs `compose.yml:437` (`adhd-engine` -> `redis-primary`) + ADHD publishes `dopemux:events` | observers can see divergent event histories | unify event stream backend or strictly namespace streams by Redis instance |
| Dynamic search cardinality by ADHD state | `services/dope-context/src/mcp/server.py:155-176` | same query may return different result count/order | add deterministic mode flag forcing fixed `top_k` |
| Reranker failure fallback changes ordering path | `services/dope-context/src/mcp/server.py:917-925`, `:958-963` | non-repeatable ranking under transient rerank errors | require explicit `ranking_mode` in contract + telemetry assertion when fallback used |
| Cache-path-dependent retrieval behavior | BM25 snapshot load/fallback in `services/dope-context/src/mcp/server.py:810-833` | output depends on local snapshot existence/state | enforce snapshot version pin + stale-index detector |
| Time-based retention deletes raw evidence | `services/working-memory-assistant/chronicle/store.py:317-328` + scheduled job `dope_memory_main.py:887-899` | replay/audit nondeterminism over time | contract retention window + archive-before-delete path |
| Retry without idempotency key on progress writes | `services/task-orchestrator/app/adapters/conport_adapter.py:584-609` + server generates new UUID on create `enhanced_server.py:1047` | duplicate progress entries on retry ambiguity | add idempotency key field and dedupe constraint on authority service |
| Stream trimming in ADHD emitter | `services/adhd_engine/event_emitter.py:135-139` (`maxlen=10000`) | silent loss of older events | move trim policy to explicit retention worker with audit log |

## Evidence excerpts
- `services/dopecon-bridge/dopecon_bridge/routes.py:149-162`
```text
@events_router.post("")
async def publish_event(request: PublishEventRequest):
    """Publish event to Redis Stream for cross-service coordination."""
    try:
        from .event_bus import EventBus, Event

        event_bus = EventBus()
        await event_bus.initialize()

        event = Event(
            type=request.event_type,
            data=request.data,
            source=request.source or settings.service_name
        )
```
- `services/dopecon-bridge/dopecon_bridge/routes.py:327-333`
```text
@tasks_router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    request: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
```
- `compose.yml:356-363`
```text
    environment:
      - PORT_BASE=3000
      - POSTGRES_URL=postgresql+asyncpg://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph
      - AGE_HOST=dopemux-postgres-age
      - AGE_PORT=5432
      - AGE_PASSWORD=${AGE_PASSWORD:-dopemux_age_dev_password}
      - QDRANT_URL=http://mcp-qdrant:6333
      - REDIS_URL=redis://redis-events:6379
```
- `compose.yml:433-439`
```text
    environment:
      - API_PORT=8095
      - HOST=0.0.0.0
      - ADHD_ENGINE_API_KEY=${ADHD_ENGINE_API_KEY:-dev-key-123}
      - REDIS_URL=redis://redis-primary:6379
      - CONPORT_URL=http://conport:3004
      - DOPECON_BRIDGE_URL=http://dopecon-bridge:3016
```
- `services/task-orchestrator/app/adapters/conport_adapter.py:584-607`
```text
        max_retries = 3

        for attempt in range(max_retries):
            try:
                url = f"{self.conport_url}/api/progress/log"
                params = {"workspace_id": self.workspace_id}
                async with self.http_session.post(url, params=params, json=progress_data) as response:
                    if response.status == 200:
                        result = await response.json()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"ConPort connection failed (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
```
