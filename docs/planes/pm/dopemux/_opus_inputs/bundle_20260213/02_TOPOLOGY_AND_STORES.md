# 02 Topology And Stores

## Store topology summary

| store | instance(s) | connected services (evidence-backed) | notes |
|---|---|---|---|
| Postgres (AGE) | `postgres` (`dopemux-postgres-age`) \| `conport`, `dopecon-bridge`, `dope-memory` | authority DB for ConPort-style records + graph extension |
| Redis Events | `redis-events` \| `dopecon-bridge`, `dope-memory` \| stream/event transport (`dopemux:events`, `activity.events.v1`, `memory.derived.v1`) |
| Redis Primary | `redis-primary` \| `conport`, `task-orchestrator`, `adhd-engine` | caching + some stream/event writing in ADHD engine |
| Qdrant | `mcp-qdrant` \| `dope-context` (writes/index), `conport` + `dopecon-bridge` configured with URL | vector store; deterministic behavior affected by index/cache freshness |
| SQLite Chronicle | `./.dopemux:/data` with `chronicle.sqlite` \| `dope-memory` | temporal memory chronicle store |
| MySQL + Redis (Leantime) | `mysql_leantime`, `redis_leantime` \| `leantime` | PM app persistence, not core authority for ConPort/dope-memory |

## Topology notes relevant to contract
- Two Redis backends are active (`redis-events` and `redis-primary`) with overlapping event usage (`dopemux:events` appears in multiple producers).
- `conport` is wired to `redis-primary`, while `dopecon-bridge` and `dope-memory` are wired to `redis-events`.
- `dope-memory` explicitly mounts local filesystem storage for `chronicle.sqlite`.

## Evidence excerpts
- `compose.yml:73-99`
```text
  redis-events:
    image: redis:7-alpine
    container_name: redis-events
    restart: unless-stopped
    networks:
- dopemux-network

    ports:
- "6379:6379"

  # Redis Primary (for caching)
  redis-primary:
    image: redis:7-alpine
    container_name: redis-primary
```
- `compose.yml:235-244`
```text
    environment:
- MCP_SERVER_PORT=3004
- DOPECON_BRIDGE_URL=http://dope-decision-graph-bridge:3016
- DATABASE_URL=postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph
- POSTGRES_URL=postgresql+asyncpg://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph
- AGE_HOST=dopemux-postgres-age
- AGE_PORT=5432
- AGE_PASSWORD=${AGE_PASSWORD:-dopemux_age_dev_password}
- REDIS_URL=redis://redis-primary:6379
- QDRANT_URL=http://mcp-qdrant:6333
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
- `compose.yml:473-490`
```text
    environment:
- WMA_SECRET_KEY=${WMA_SECRET_KEY:-dev-only-change-me}
- WMA_ENCRYPTION_KEY=${WMA_ENCRYPTION_KEY:-dev-only-change-me}
- POSTGRES_HOST=postgres
- POSTGRES_PORT=5432
- POSTGRES_DB=dopemux_knowledge_graph
- POSTGRES_USER=dopemux_age
- POSTGRES_PASSWORD=${AGE_PASSWORD:-dopemux_age_dev_password}
- REDIS_URL=redis://redis-events:6379
- ENABLE_EVENTBUS=true
- ENABLE_MIRROR_SYNC=${ENABLE_MIRROR_SYNC:-false}
- MIRROR_SCHEMA_RESET=${MIRROR_SCHEMA_RESET:-false}
- DOPE_MEMORY_WORKSPACE_ID=${DOPE_MEMORY_WORKSPACE_ID:-default}
- POSTGRES_URL=postgresql://dopemux_age:${AGE_PASSWORD:-dopemux_age_dev_password}@postgres:5432/dopemux_knowledge_graph
- DOPEMUX_CAPTURE_LEDGER_PATH=/data/chronicle.sqlite
- DOPEMUX_SQLITE_JOURNAL_MODE=DELETE
    volumes:
- ./.dopemux:/data
```
- `services/dope-context/src/search/dense_search.py:236-273`
```text
    async def insert_points_batch(
        self,
        points: List[Tuple[List[float], List[float], List[float], Dict, Optional[str]]],
    ) -> List[str]:
        """
        Insert multiple points in batch.

        Args:
            points: List of (content_vec, title_vec, breadcrumb_vec, payload, point_id)
        """
        await self.client.upsert(
            collection_name=self.collection_name,
            points=point_structs,
        )

        logger.info(f"Inserted {len(point_structs)} points in batch")
```
