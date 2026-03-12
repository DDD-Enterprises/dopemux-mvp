# ConPort — Integration Notes

**Analyzed Ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**For**: Dopemux Integration Planning

---

## 1. Integration Surfaces

### 1.1 Recommended Integration Path

For Dopemux services integrating with ConPort:

| Use Case | Surface | Endpoint | Notes |
|---|---|---|---|
| AI agent (Claude/Gemini) tool calls | FastMCP (SSE) | `http://localhost:3005/mcp` | 13 tools via MCP protocol |
| Service-to-service API calls | HTTP REST | `http://localhost:3004/api/*` | 22 routes, JSON |
| Programmatic MCP tool invocation | JSON-RPC | `POST http://localhost:3004/mcp` | 12 tools (3 undiscoverable) |
| Health monitoring | HTTP | `GET http://localhost:3004/health` | Returns db+redis status |
| Service discovery | HTTP | `GET http://localhost:4004/info` | ADR-208 compatible |

### 1.2 Client Adapter Pattern

Existing client adapters in the repo:

| Service | File | Pattern |
|---|---|---|
| GPT Researcher | `services/dopemux-gpt-researcher/research_api/adapters/conport_adapter.py` | HTTP client |
| Task Router | `services/task-router/router_api.py` | References `CONPORT_URL` |
| Monitoring Dashboard | `services/monitoring-dashboard/server.py` | Health check |
| Genetic Agent | `services/genetic_agent/shared/mcp/memory_adapter.py` | Memory adapter |
| ADHD Engine | `services/adhd_engine/domains/attention/context_preserver.py` | Context integration |
| ADHD Engine | `services/adhd_engine/domains/task_enablement/working_memory_support.py` | Progress integration |

---

## 2. Data Contract for Integrators

### 2.1 Decision Object

```json
{
  "id": "uuid-string",
  "workspace_id": "string",
  "summary": "string",
  "rationale": "string",
  "alternatives": ["string"],
  "tags": ["string"],
  "confidence_level": "low|medium|high",
  "decision_type": "implementation|...",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

### 2.2 Progress Object

```json
{
  "id": "uuid-string",
  "workspace_id": "string",
  "description": "string",
  "status": "PLANNED|IN_PROGRESS|COMPLETED|BLOCKED|CANCELLED",
  "percentage": 0-100,
  "linked_decision_id": "uuid-string|null",
  "priority": "low|medium|high|urgent",
  "estimated_hours": "decimal|null",
  "actual_hours": "decimal|null",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "completed_at": "ISO-8601|null"
}
```

### 2.3 Context Object

```json
{
  "workspace_id": "string",
  "instance_id": "string|null",
  "active_context": "string",
  "last_activity": "string",
  "session_time": "string",
  "focus_state": "string",
  "session_milestone": "string|null",
  "updated_at": "ISO-8601"
}
```

---

## 3. Event Integration

### 3.1 Events Published to DopeconBridge

ConPort publishes two event types via HTTP POST to `{DOPECON_BRIDGE_URL}/events`:

**`decision_logged`**:
```json
{
  "stream": "dopemux:events",
  "event_type": "decision_logged",
  "source": "conport",
  "data": {
    "decision_id": "uuid",
    "summary": "string",
    "workspace_id": "string",
    "tags": ["string"],
    "instance_id": "string|null"
  }
}
```

**`progress_updated`**:
```json
{
  "stream": "dopemux:events",
  "event_type": "progress_updated",
  "source": "conport",
  "data": {
    "progress_id": "uuid",
    "status": "string",
    "description": "string",
    "workspace_id": "string",
    "percentage": 0-100,
    "instance_id": "string|null"
  }
}
```

### 3.2 Event Publishing Behavior

- Best-effort delivery (non-blocking)
- 2-second timeout per publish
- Silently drops if bridge unavailable
- Bridge availability checked on startup (5s timeout)

---

## 4. Multi-Tenancy Integration

### 4.1 Workspace Scoping

All API calls should include `workspace_id`. This is the primary isolation boundary.

**For MCP clients**: Pass `workspace_id` as first parameter to most tools.
**For HTTP clients**: Pass `workspace_id` as query parameter or path segment.

### 4.2 Instance Isolation

For worktree-aware integrations:
- Set `DOPEMUX_INSTANCE_ID` env var in the ConPort container
- IN_PROGRESS/PLANNED items are isolated per instance
- COMPLETED/BLOCKED/CANCELLED items are shared

### 4.3 User Isolation (Partial)

Migration 003 adds `user_id` columns but most handlers don't filter by it. Only `unified_queries.py` (cross-workspace search) uses `user_id`.

**Recommendation**: Do NOT rely on user-level isolation until API handlers enforce it.

---

## 5. Integration Risks

### 5.1 No Authentication

All ConPort endpoints are unauthenticated. Any service on the Docker network can read/write all data.

**Recommendation**: Restrict network access via Docker network isolation. Do not expose ConPort ports externally.

### 5.2 No Rate Limiting

No request rate limiting or throttling. A misbehaving service can overwhelm the database connection pool.

**Recommendation**: Set `DB_POOL_MAX` appropriately. Monitor `/metrics` for connection exhaustion.

### 5.3 Token Truncation

List responses are truncated to 9000 tokens. Integrators should check `truncation_stats` in responses and implement pagination if needed.

### 5.4 Cache Staleness

Redis cache TTLs range from 60s to 1800s. Recent writes may not be visible in subsequent reads for up to 5 minutes (context) or 30 minutes (relationships).

Write operations invalidate relevant caches explicitly, but cross-key invalidation is incomplete (e.g., `_log_decision` invalidates `decisions:{workspace_id}` but not all possible `decisions:{workspace_id}:{limit}` variants).

### 5.5 `ag_catalog` Schema Dependency

`unified_queries.py` queries reference `ag_catalog` schema. If Apache AGE extension is not installed, cross-workspace queries will fail. This is a latent defect — the tables exist in `public` schema but queries reference `ag_catalog`.

---

## 6. Recommended Integration Patterns

### 6.1 For AI Agents (Claude, Gemini, etc.)

Use the FastMCP SSE surface at `:3005/mcp`. Configure in `.claude.json` or equivalent:

```json
{
  "conport": {
    "type": "sse",
    "url": "http://localhost:3005/mcp"
  }
}
```

### 6.2 For Backend Services

Use HTTP REST API at `:3004`. Example with aiohttp:

```python
async with aiohttp.ClientSession() as session:
    async with session.post(
        "http://conport:3004/api/decisions",
        json={"workspace_id": "my-project", "summary": "...", "rationale": "..."}
    ) as resp:
        result = await resp.json()
```

### 6.3 For Event-Driven Services

Subscribe to DopeconBridge events (stream `dopemux:events`) for `decision_logged` and `progress_updated` event types.

### 6.4 For Monitoring

- Health: `GET http://conport:3004/health`
- Metrics: `GET http://conport:3004/metrics` (Prometheus format)
- Info: `GET http://conport:4004/info` (service discovery)

---

## 7. Dopemux Memory Architecture Position

ConPort occupies the "structured truth" tier in the Dopemux memory hierarchy:

```
┌─────────────────────────────────────────────────────┐
│                  Memory Architecture                 │
├─────────────────────────────────────────────────────┤
│ DopeContext      │ Semantic archival (vector/Qdrant) │
│ ConPort (HERE)   │ Structured truth (PG decisions)   │
│ ConPort-KG       │ Graph relationships (relational)  │
│ Dope-Memory      │ Temporal chronicle (work logs)    │
└─────────────────────────────────────────────────────┘
```

**ConPort is authoritative for**: Decisions, progress entries, workspace contexts, custom data.
**ConPort is NOT authoritative for**: Semantic search results (DopeContext), temporal work logs (Dope-Memory), vector embeddings (Qdrant).

**Key insight**: Despite docs claiming ConPort is the "single source of truth for everything," its actual authority is limited to its own PostgreSQL tables. No enforcement mechanism prevents other services from creating parallel truth stores.
