# INTEGRATION NOTES — dope-memory

## 1. Integration-Critical Surfaces

### For Dopemux Orchestration Layer

| Surface | Protocol | Stability | Notes |
|---------|----------|-----------|-------|
| `POST /tools/memory_store` | HTTP REST | Stable | Primary write path for manual captures |
| `POST /tools/memory_search` | HTTP REST | Stable | Primary read path for context retrieval |
| `POST /tools/memory_recap` | HTTP REST | Stable | ADHD-optimized context restoration |
| `POST /tools/memory_correct` | HTTP REST | Stable | Supersession-based correction |
| `GET /health` | HTTP REST | Stable | Health monitoring |
| `activity.events.v1` (Redis) | Redis Streams | Stable | Real-time event ingestion input |
| `memory.derived.v1` (Redis) | Redis Streams | Stable | Post-promotion derived events output |

### For MCP Client Integration

| Method | Current Status | Recommendation |
|--------|---------------|----------------|
| HTTP REST (`/tools/*`) | ✅ Working | Direct integration via HTTP POST |
| SSE (`/mcp`) | ❌ Not implemented | Requires MCP proxy or implementation |
| Stdio JSON-RPC | ⚠️ Targets wrong port | Fix adapter to target port 3020 |

## 2. Integration Approach Recommendations

### Recommended: Direct HTTP Integration

The HTTP REST surface is the most mature and well-tested integration path. All 10 tools are callable via `POST /tools/{tool_name}` with JSON body matching the Pydantic request models.

```python
# Example integration
import httpx

async def memory_search(query: str, workspace_id: str = "default"):
    async with httpx.AsyncClient(base_url="http://localhost:3020") as client:
        response = await client.post("/tools/memory_search", json={
            "query": query,
            "workspace_id": workspace_id,
            "instance_id": "A",
            "top_k": 3,
        })
        return response.json()
```

### If MCP Protocol Compliance Required

Option A: Add MCP proxy (e.g., `mcp-proxy-server`) in front of the HTTP REST API.

Option B: Implement native MCP JSON-RPC endpoints in `dope_memory_main.py`. This would require:
1. Adding `tools/list` and `tools/call` JSON-RPC handlers
2. Adding SSE transport at `/mcp` endpoint
3. Implementing MCP protocol framing

Option C: Fix the existing stdio adapter (`mcp_stdio_adapter.py`) to target port 3020 and expand tool coverage from 3 to 10.

### If Capture Client Integration Required

The `src/dopemux/memory/capture_client.py` module provides a CLI/plugin capture path that writes directly to the same canonical ledger. This is suitable for:
- CLI tool integrations
- Pre-commit hook captures
- Plugin-mode captures (IDE extensions)

The capture client resolves the ledger path using the same `resolve_canonical_ledger()` function, ensuring all write paths converge.

## 3. Workspace/Instance Scoping

All dope-memory operations are scoped by `workspace_id` and `instance_id`. Integrators must:

1. **Always provide `workspace_id`** — defaults to `DOPE_MEMORY_WORKSPACE_ID` env var or `"default"`
2. **Always provide `instance_id`** — defaults to `DOPE_MEMORY_INSTANCE_ID` env var or `"A"`
3. **Optionally provide `session_id`** — for session-scoped queries

Cross-workspace queries are NOT supported within dope-memory. Each workspace has its own canonical ledger.

## 4. Event Integration (Redis Streams)

### Publishing Events to dope-memory

Events published to `activity.events.v1` Redis stream will be automatically consumed if `ENABLE_EVENTBUS=true`.

#### Event Envelope Format

```json
{
  "id": "unique-event-id",
  "event_type": "decision.logged",
  "source": "your-service-name",
  "ts_utc": "2026-03-06T20:22:43Z",
  "workspace_id": "your-workspace-id",
  "instance_id": "A",
  "session_id": "optional-session-id",
  "payload": {
    "decision_id": "d-123",
    "title": "Use Redis for event bus",
    "choice": "Redis Streams",
    "rationale": "Low latency, built-in consumer groups"
  }
}
```

#### Promotable Event Types

Only these event types will be promoted to work_log_entries:
- `decision.logged`
- `task.completed`
- `task.failed`
- `task.blocked`
- `error.encountered`
- `workflow.phase_changed`
- `manual.memory_store`

All other event types are ingested as raw events (7-day TTL) but NOT promoted.

### Consuming Derived Events

After promotion, derived events are published to `memory.derived.v1` Redis stream. Downstream services can subscribe to this stream for post-processing.

## 5. Canonical Ledger Considerations

### Concurrent Access

The canonical ledger uses SQLite in WAL mode (or DELETE mode in Docker). Multiple readers are safe. Multiple writers through the same `ChronicleStore` instance are serialized by SQLite's internal locking.

**Warning:** If multiple processes write to the same SQLite file simultaneously (e.g., capture client + HTTP server), WAL mode is required for safe concurrent access. The Docker compose config overrides to DELETE mode, which serializes all writes.

### Ledger Location

In Docker: `/data/chronicle.sqlite` (via `DOPEMUX_CAPTURE_LEDGER_PATH`)
In development: `{repo_root}/.dopemux/chronicle.sqlite`

Integrators using the capture client outside Docker must ensure they resolve to the same ledger path.

## 6. Error Handling Integration

### HTTP Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success — response is the `data` dict from ToolResponse |
| 400 | Tool error — `{"detail": "error message"}` |
| 503 | Server not initialized (pre-lifespan) |
| 422 | Pydantic validation error (FastAPI automatic) |

### Supersession Errors

When using `memory_correct`, these specific `ValueError` messages indicate corrective action:

| Error Pattern | Meaning | Action |
|--------------|---------|--------|
| `"Cannot supersede non-existent entry"` | Target entry_id is invalid | Verify entry_id |
| `"already superseded. Target the chain head instead: {id}"` | Must target newest version | Use the suggested head ID |
| `"Supersession chain depth limit exceeded"` | Chain has 10 entries | Cannot correct further |
| `"Supersession fork attempt rejected"` | Entry already has a correction | Use existing correction's ID |

## 7. Memory Trinity Coordination

| Operation | dope-memory Role | Coordination With |
|-----------|-----------------|-------------------|
| Event capture | Write to chronicle | DopeContext may index (if ENABLE_DOPECONTEXT_INDEX) |
| Decision storage | Store as work_log_entry | ConPort should be notified for structured truth |
| Context retrieval | Temporal search | DopeContext for semantic search, ConPort for structured queries |
| Reflection promotion | Generate reflection card with `promotion_candidates_json` | Candidates intended for ConPort promotion (not yet wired) |

## 8. Feature Flags for Integration

| Flag | Default | Effect |
|------|---------|--------|
| `ENABLE_EVENTBUS` | `false` | Enables Redis stream consumer |
| `ENABLE_MIRROR_SYNC` | `false` | Enables PostgreSQL mirror |
| `ENABLE_RETENTION_JOB` | `true` | Enables raw event cleanup |
| `ENABLE_DOPECONTEXT_INDEX` | `false` | Cross-indexes to DopeContext (stub) |
