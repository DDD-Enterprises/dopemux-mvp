# INTEGRATION_NOTES.md — dope-context

**Analyzed ref:** `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`

---

## 1. Integration Points

### 1.1 Qdrant (Hard Dependency)

| Property | Value | Evidence |
|----------|-------|----------|
| Connection | `QDRANT_URL` (default: `localhost`), `QDRANT_PORT` (default: `6333`) | server.py:803-804 |
| Compose dependency | `depends_on: mcp-qdrant` | compose.yml |
| Collections | `code_{hash}`, `docs_{hash}` | utils/workspace.py:176-177 |
| Vector dim | 1024 | multi_index_config.yaml:9 |
| Operations | Create/delete collection, upsert/search/delete points, get payloads | dense_search.py |

**Integration note:** Qdrant is the sole vector store. No fallback. If Qdrant is down, all search and indexing tools will fail. Health check should verify Qdrant connectivity.

### 1.2 Voyage AI (Hard Dependency)

| Property | Value | Evidence |
|----------|-------|----------|
| API key | `VOYAGE_API_KEY` or `VOYAGEAI_API_KEY` | server.py:465, 776-792 |
| Embedding model (code) | `voyage-code-3` | server.py:347, 912, 1160 |
| Embedding model (docs) | `voyage-context-3` | server.py:1637 |
| Reranking model | `voyage-rerank-2.5` | voyage_reranker.py |
| Cost tracking | `CostTracker` in embedder and reranker classes | voyage_embedder.py, voyage_reranker.py |

**Integration note:** All search and indexing operations require Voyage AI. If API key is missing, tools return structured error responses. Cost tracking is in-memory only.

### 1.3 OpenAI (Soft Dependency)

| Property | Value | Evidence |
|----------|-------|----------|
| API key | `OPENAI_API_KEY` | server.py:801 |
| Purpose | Context generation for code embeddings | openai_generator.py |
| Fallback | Indexing works without context generation | server.py:816-819 |

**Integration note:** Optional. If missing, code indexing proceeds without LLM-generated context snippets. Quality of embeddings may be lower without context.

### 1.4 dopecon-bridge (Soft Dependency)

| Property | Value | Evidence |
|----------|-------|----------|
| URL | `DOPECON_BRIDGE_URL` (default: `http://localhost:3016`) | server.py:1860 |
| Endpoint | `GET /kg/decisions/search?text={query}&limit={limit}` | server.py:1929 |
| Timeout | 5 seconds | server.py:1931 |
| Gating | Requires `configure_decision_auto_indexing(enabled=True)` | server.py:2022-2026 |

**Integration note:** Decision enrichment in `search_all` requires:
1. dopecon-bridge running at configured URL
2. Decision auto-indexing explicitly enabled via MCP tool
3. `include_decisions=True` in `search_all` call (default)
4. `top_k >= 3` for budget allocation

Fails silently (returns empty array).

### 1.5 ADHD Engine (Soft Dependency)

| Property | Value | Evidence |
|----------|-------|----------|
| Connection | Redis-based (via `adhd_config_service`) | server.py:297-304 |
| Feature flag | `FEATURE_ADHD_ENGINE_DOPE_CONTEXT` (Redis key) | server.py:327 |
| Purpose | Dynamic top_k based on attention state | server.py:313-339 |
| States | scattered→5, focused→15, hyperfocused→40, fallback→requested | server.py:315-321 |

**Integration note:** Feature-flagged. Requires ADHD Engine service running with Redis. Degrades gracefully — uses original `top_k` on failure. No configuration UI.

### 1.6 Serena / Code Graph (Soft Dependency)

| Property | Value | Evidence |
|----------|-------|----------|
| Gating | `enrich_with_graph=True` parameter on `search_code` | server.py:1288-1300 |
| Import | Lazy: `from enrichment.code_graph_enricher import get_code_graph_enricher` | server.py:1290 |
| Max enrich | 5 results (ADHD limit) | server.py:1295 |

**Integration note:** Opt-in via parameter. Lazy-loaded. Import path may have issues (see DRIFT_REPORT D-12). Fails silently.

### 1.7 ConPort Event Bridge (Conditional)

| Property | Value | Evidence |
|----------|-------|----------|
| Import | `from dopecon_bridge_connector import emit_search_completed` | server.py:70 |
| Flag | `CONPORT_INTEGRATION_AVAILABLE` | server.py:71 |
| Purpose | Track search patterns in ConPort-KG | integration_bridge_connector.py |

**Integration note:** Conditional import. If `dopecon_bridge_connector` module is not available, flag is `False` and no events are emitted. The module itself uses Redis event bus.

---

## 2. Integration Patterns

### 2.1 Multi-Workspace Pattern
All tools support `workspace_path` (single) and `workspace_paths` (batch). The response shape changes:
- Single workspace: direct result
- Multiple workspaces: `{workspace_count, results: [{workspace, ...}]}`

**For integrators:** Always handle both shapes. Check for `workspace_count` key to detect multi-workspace responses.

### 2.2 Error Response Pattern
All search tools return structured error dicts instead of raising exceptions:
```json
{
  "error": "Description of what went wrong",
  "help": "What to do about it",
  "query": "original query",
  "workspace": "/path/to/workspace",
  "collection": "code_abc123"
}
```

**For integrators:** Check for `error` key in response items.

### 2.3 Trinity Boundary Contract
`search_all` includes `trinity_boundaries` metadata in every response:
```json
{
  "marker": "search-memory-authority-boundary-v1",
  "decision_authority": "memory_plane",
  "code_docs_authority": "search_plane"
}
```

**For integrators:** The `marker` value is a versioned contract identifier. Use it to validate boundary enforcement.

### 2.4 Token Budget Contract
All search responses are truncated to fit within MCP token limits:
- Default budget: 9000 tokens (10K limit with 10% headroom)
- Per-item truncation: 2000 characters
- Budget is reduced for unified search: 4000 (or 3200 with decisions)

**For integrators:** Response sizes are predictable. Do not rely on getting all `top_k` results — budget truncation may drop items.

---

## 3. MCP Client Configuration

### stdio Configuration (claude.json)
```json
{
  "mcpServers": {
    "dope-context": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "/path/to/services/dope-context",
      "env": {
        "VOYAGE_API_KEY": "...",
        "QDRANT_URL": "localhost",
        "QDRANT_PORT": "6333"
      }
    }
  }
}
```

### SSE Configuration (claude.json)
```json
{
  "mcpServers": {
    "dope-context": {
      "type": "sse",
      "url": "http://localhost:3010/mcp"
    }
  }
}
```

### Docker Wrapper Configuration
```json
{
  "mcpServers": {
    "dope-context": {
      "command": "scripts/mcp-wrappers/dope-context-wrapper.sh"
    }
  }
}
```

**⚠ Note:** Wrapper has known path mismatch (see DRIFT_REPORT D-05).

---

## 4. Recommended Integration Sequence

### Initial Setup
1. Start Qdrant (port 6333)
2. Start dope-context (port 3010)
3. Verify: `curl http://localhost:3010/health` → `{"status": "ok"}`
4. Bootstrap: `POST /autoindex/bootstrap` with workspace path
5. Verify: `GET /autoindex/status`

### Ongoing Operation
1. MCP tools handle workspace detection automatically
2. Start autonomous indexing for zero-touch updates
3. Use `search_code` for code queries, `docs_search` for documentation
4. Use `search_all` for unified cross-plane results
5. Monitor via `get_search_metrics` and `get_autonomous_status`

### Optional Enhancements
1. Enable decision enrichment: `configure_decision_auto_indexing(enabled=True)`
2. Enable ADHD top_k: Set `FEATURE_ADHD_ENGINE_DOPE_CONTEXT` in Redis
3. Enable graph enrichment: Pass `enrich_with_graph=True` to `search_code`
4. Enable ConPort events: Ensure `dopecon_bridge_connector` module is importable

---

## 5. Compose Integration

### Network
- Network: `dopemux-network` (shared with other Dopemux services)
- Container name: `mcp-dope-context`

### Required Co-Services
- `mcp-qdrant` (hard dependency)

### Optional Co-Services
- `dopecon-bridge` (for decision enrichment)
- `adhd-engine` (for dynamic top_k)
- Redis (for ADHD Engine and ConPort event bus)

### Volume Requirements
- Host source code must be mounted at `/workspaces` in container
- `HOST_CODE_PARENT_DIR` env var must point to the parent of project directories
- `HOST_PROJECT_RELATIVE_PATH` sets `DOPEMUX_WORKSPACE_ROOT`
