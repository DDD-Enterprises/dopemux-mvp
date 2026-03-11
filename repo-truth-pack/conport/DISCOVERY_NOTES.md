# ConPort Phase 1 Discovery Notes

## 1. Repo Identity Snapshot

- **Repository**: `/Users/hue/code/dopemux-mvp` (local)
- **Target Component**: ConPort MCP Server (Knowledge Graph & Context Management)
- **Target Path**: `docker/mcp-servers-source/conport/`
- **Analysis Timestamp**: 2026-03-09T21:04:19Z

## 2. Analyzed Ref

- **Commit**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
- **Branch**: `codex/main-drain-20260306`

## 3. Default Branch

- The analyzed branch is `codex/main-drain-20260306`. The repository default branch is UNKNOWN from local inspection alone (not verified via remote).

## 4. High-Confidence Active Module(s)

### 4.1 `enhanced_server.py` — PRIMARY ACTIVE SERVER (2149 lines)

- **Evidence**: `start_with_info.sh` line 11: `MCP_SERVER_PORT=3004 python enhanced_server.py &`
- **Class**: `EnhancedConPortServer`
- **Role**: HTTP API server (aiohttp) on port 3004 with real PostgreSQL + Redis persistence
- **Transport**: HTTP REST API + JSON-RPC via `/mcp` endpoint
- **Features**:
  - Full PostgreSQL persistence (asyncpg)
  - Redis caching (aioredis)
  - Worktree multi-instance support via `instance_detector.py`
  - DopeconBridge event publishing via `integration_bridge_client.py`
  - Unified cross-workspace queries via `unified_queries.py`
  - Prometheus monitoring via `shared_monitoring.py`
  - Token truncation (9000 token budget per response)
  - Auto-save loop (30-second interval for context preservation)
  - Error handling framework integration (optional import from `dopemux.error_handling`)

### 4.2 `server.py` — ACTIVE MCP SURFACE (FastMCP SSE/stdio, 178 lines)

- **Evidence**: `start_with_info.sh` line 15: `MCP_SERVER_PORT=3005 python server.py sse &`
- **FastMCP name**: `"conport"` (line 12)
- **Role**: Thin MCP protocol client wrapping the enhanced_server HTTP API
- **Transport**: SSE on port 3005 (via uvicorn) OR stdio (default)
- **Pattern**: All tools delegate to `CONPORT_URL` (default `http://localhost:3004`) — this is a pure proxy layer over the enhanced_server HTTP API
- **13 registered `@mcp.tool()` functions**: `get_progress`, `update_progress`, `get_decisions`, `log_decision`, `get_recent_activity`, `get_active_work`, `workspace_summary`, `fork_instance`, `promote`, `promote_all`, `get_context`, `update_context`, `log_progress`

### 4.3 `conport_mcp_stdio.py` — ACTIVE STDIO-ONLY ADMIN CLIENT (175 lines)

- **FastMCP name**: `"conport-admin"` (line 13)
- **Role**: Stdio-only MCP client, near-identical to `server.py` but named differently
- **Evidence**: Referenced in `.claude/claude_config.json.bak` as `conport-admin` with stdio transport
- **13 registered `@mcp.tool()` functions**: Same tool set as `server.py`
- **Difference from server.py**: `log_decision` payload uses `"summary": f"[{topic}] {decision}"` (line 71) vs server.py which uses `"topic": topic` directly

### 4.4 `info_server.py` — ACTIVE SERVICE DISCOVERY SIDECAR (62 lines)

- **Evidence**: `start_with_info.sh` line 7: `python info_server.py &`
- **Port**: 4004 (INFO_PORT = PORT + 1000)
- **Endpoints**: `/health`, `/info` (ADR-208 auto-config)

### 4.5 `unified_queries.py` — ACTIVE QUERY LAYER (361 lines)

- **Evidence**: Imported and used by `enhanced_server.py` line 201: `from unified_queries import UnifiedQueryAPI`
- **Class**: `UnifiedQueryAPI`
- **Dependencies**: asyncpg, redis.asyncio
- **Features**: Cross-workspace full-text search, relationship graph traversal (recursive CTE), workspace summary aggregation
- **Schema reference**: Uses `ag_catalog` schema (line 63, 205)

### 4.6 `instance_detector.py` — ACTIVE UTILITY (197 lines)

- **Evidence**: Imported by `enhanced_server.py` line 44
- **Class**: `SimpleInstanceDetector`
- **Env vars**: `DOPEMUX_INSTANCE_ID`, `DOPEMUX_WORKSPACE_ID`
- **Data isolation rules**: IN_PROGRESS/PLANNED → isolated; COMPLETED/BLOCKED/CANCELLED → shared

### 4.7 `integration_bridge_client.py` — ACTIVE EVENT PUBLISHER (163 lines)

- **Evidence**: Imported by `enhanced_server.py` line 51
- **Class**: `DopeconBridgeClient`
- **Target**: DopeconBridge at `DOPECON_BRIDGE_URL` (default `http://dope-decision-graph-bridge:3016`)
- **Event types**: `decision_logged`, `progress_updated`

## 5. Deprecated/Legacy Module(s)

### 5.1 `direct_server.py` — DEPRECATED/PROTOTYPE (271 lines)

- **Evidence**: Not referenced in `start_with_info.sh`, Dockerfile, or compose files
- **Class**: `DirectConPortServer`
- **Returns mock data** (e.g., line 79: `# For now, return mock data`; line 129: `# Mock decision data for now`)
- **Assessment**: Early prototype, superseded by `enhanced_server.py`

### 5.2 `simple_metrics_server.py` — AUXILIARY/UNUSED (48 lines)

- **Evidence**: Not referenced in `start_with_info.sh` or Dockerfile
- **Assessment**: Standalone metrics server. Monitoring is now integrated into `enhanced_server.py` via middleware.

### 5.3 `schema.sql.bak` — BACKUP

- **Evidence**: Content identical to `schema.sql` header; backup file

## 6. Runtime Entrypoints Discovered

| Entrypoint | File | Triggered By | Port | Transport |
|---|---|---|---|---|
| **Enhanced HTTP Server** | `enhanced_server.py` | `start_with_info.sh` line 11 | 3004 | HTTP REST + JSON-RPC |
| **MCP SSE Server** | `server.py sse` | `start_with_info.sh` line 15 | 3005 | SSE (via uvicorn) |
| **Info Sidecar** | `info_server.py` | `start_with_info.sh` line 7 | 4004 | HTTP |
| **MCP stdio** | `server.py` (default) | Manual / direct invocation | N/A | stdio |
| **Admin stdio** | `conport_mcp_stdio.py` | Claude config (backup) | N/A | stdio |
| **Docker CMD** | `start_with_info.sh` | `Dockerfile` line 39 | 3004,3005,4004 | All above |

## 7. Callable/Tool/API Registration Locations

### 7.1 FastMCP Surface A: `server.py` (name: `"conport"`)

| Tool Name | Line | Parameters | Delegates To |
|---|---|---|---|
| `get_progress` | 36 | workspace_id, status?, limit=20 | GET /api/progress |
| `update_progress` | 47 | progress_id, updates | PUT /api/progress/{id} |
| `get_decisions` | 55 | workspace_id?, limit=10 | GET /api/decisions |
| `log_decision` | 66 | workspace_id, topic, decision, rationale, tags? | POST /api/decisions |
| `get_recent_activity` | 81 | workspace_id, hours=24 | GET /api/recent-activity/{id} |
| `get_active_work` | 90 | workspace_id | GET /api/active-work/{id} |
| `workspace_summary` | 99 | user_id | GET /api/workspace-summary |
| `fork_instance` | 108 | workspace_id, source_instance?, target_instance? | POST /api/instance/fork |
| `promote` | 119 | progress_id | POST /api/progress/promote |
| `promote_all` | 126 | workspace_id | POST /api/progress/promote_all |
| `get_context` | 133 | workspace_id | GET /api/context/{id} |
| `update_context` | 142 | workspace_id, context_data | POST /api/context/{id} |
| `log_progress` | 150 | workspace_id, description, status="PLANNED", priority="medium", linked_decision_id? | POST /api/progress |

### 7.2 FastMCP Surface B: `conport_mcp_stdio.py` (name: `"conport-admin"`)

- Same 13 tools as server.py with one difference:
  - `log_decision` payload field uses `"summary": f"[{topic}] {decision}"` instead of `"topic": topic`

### 7.3 JSON-RPC Tool Surface: `enhanced_server.py` `/mcp` endpoint

| Tool Name (JSON-RPC) | Line | Dispatch Target |
|---|---|---|
| `conport_get_context` | 1737 | `_get_context_tool` → `_get_context` |
| `conport_update_context` | 1738 | `_update_context_tool` → `_update_context` |
| `conport_log_decision` | 1739 | `_log_decision` |
| `conport_get_decisions` | 1740 | `_get_decisions_tool` → `_get_decisions` |
| `conport_log_progress` | 1741 | `_log_progress` |
| `conport_get_progress` | 1742 | `_get_progress_tool` → `_get_progress` |
| `conport_update_progress` | 1743 | `_update_progress_tool` → `_update_progress` |
| `conport_get_recent_activity` | 1744 | `_get_recent_activity_tool` → `_get_recent_activity` |
| `conport_get_active_work` | 1745 | `_get_active_work_tool` → `_get_active_work` |
| `conport_fork_instance` | 1747 | `_fork_instance` |
| `conport_promote` | 1748 | `_promote_progress` |
| `conport_promote_all` | 1749 | `_promote_all` |

- **Discovery aliases** (line 1693): `tools/list`, `list_tools`, `mcp.listTools`, `tools.list`, `listTools`
- **Tool invocation methods** (line 1698): `tools/call`, `tool/call`, or any method starting with `conport_`

### 7.4 HTTP REST Surface: `enhanced_server.py` `setup_routes()`

| Method | Route | Handler |
|---|---|---|
| GET | `/health` | `health_check` |
| GET | `/metrics` | `metrics_handler` (if monitoring available) |
| GET | `/api/context/{workspace_id}` | `get_context` |
| POST | `/api/context/{workspace_id}` | `update_context` |
| POST | `/api/decisions` | `log_decision` |
| GET | `/api/decisions` | `get_decisions` |
| POST | `/api/progress` | `log_progress` |
| GET | `/api/progress` | `get_progress` |
| PUT | `/api/progress/{progress_id}` | `update_progress` |
| GET | `/api/recent-activity/{workspace_id}` | `get_recent_activity` |
| GET | `/api/active-work/{workspace_id}` | `get_active_work` |
| GET | `/api/search/{workspace_id}` | `search_content` |
| GET | `/api/unified-search` | `unified_search` |
| GET | `/api/workspace-relationships` | `workspace_relationships` |
| GET | `/api/workspace-summary` | `workspace_summary` |
| POST | `/api/custom_data` | `save_custom_data` |
| GET | `/api/custom_data` | `get_custom_data` |
| DELETE | `/api/custom_data` | `delete_custom_data` |
| POST | `/mcp` | `mcp_endpoint` (JSON-RPC) |
| POST | `/api/instance/fork` | `fork_instance` |
| POST | `/api/progress/promote` | `promote_progress` |
| POST | `/api/progress/promote_all` | `promote_all` |

## 8. DTO/Parser/Validator Locations

- **No formal DTO classes** in enhanced_server.py; data is passed as `Dict[str, Any]` throughout
- **Dataclasses** in `unified_queries.py`:
  - `UnifiedSearchResult` (line 24): decision_id, workspace_id, summary, rationale, created_at, relevance_score, user_id, tags
  - `WorkspaceSummary` (line 36): workspace_id, name, total_decisions, recent_decisions_7d, total_progress, in_progress_count, last_activity
- **Token truncation** (response size control):
  - `_estimate_tokens()` (line 725): Conservative 1 token ≈ 4 chars
  - `_truncate_decisions()` (line 731): 9000 token max budget
  - `_truncate_progress()` (line 761): 9000 token max budget
- **JSON-RPC tool schemas**: `_get_tool_schemas()` at line 1787 returns 9 tool definitions with `inputSchema` objects
- **SQL schema constraints** provide validation:
  - `progress_entries.status` CHECK: `('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'BLOCKED', 'CANCELLED')`
  - `progress_entries.priority` CHECK: `('low', 'medium', 'high', 'urgent')`
  - `progress_entries.percentage` CHECK: `0-100`
  - `entity_relationships.strength` CHECK: `0.0-1.0`
  - `decisions.confidence_level` default: `'medium'`
  - `decisions.decision_type` default: `'implementation'`

## 9. Workflow/State/Gating Locations

### 9.1 Instance Isolation (Worktree Multi-Instance)

- **File**: `instance_detector.py`
- **Logic**: `is_isolated_status()` (line 146) — IN_PROGRESS and PLANNED are instance-isolated; COMPLETED, BLOCKED, CANCELLED are shared
- **Used by**: `enhanced_server.py` `_update_progress()` (line 1228-1237) — status transitions trigger instance_id changes
- **Env vars**: `DOPEMUX_INSTANCE_ID`, `DOPEMUX_WORKSPACE_ID`

### 9.2 Promotion (Instance → Shared)

- **promote_progress**: `enhanced_server.py` line 1039 — sets `instance_id = NULL` on a single progress entry
- **promote_all**: `enhanced_server.py` line 1087 — bulk promote all PLANNED/IN_PROGRESS entries for current instance
- **MCP surface**: `promote` and `promote_all` tools in server.py (lines 119, 126)

### 9.3 Fork (Shared → Instance)

- **fork_instance**: `enhanced_server.py` line 974 — copies PLANNED/IN_PROGRESS from shared (or source instance) to target instance
- **Auto-fork**: `enhanced_server.py` line 911 — auto-forks from shared when `get_progress` returns empty and `DOPEMUX_AUTO_FORK_PROGRESS` is `'1'` (default enabled, line 146)

### 9.4 Auto-Save Loop (ADHD Context Preservation)

- **File**: `enhanced_server.py` line 1497
- **Interval**: 30 seconds (`self.auto_save_interval`)
- **Action**: Touches `updated_at` on recently active workspace_contexts

### 9.5 Auto-Complete Trigger (SQL)

- **File**: `schema.sql` line 184
- **Trigger**: `auto_complete_progress_trigger` — when percentage reaches 100, auto-sets status to COMPLETED

## 10. Persistence/Storage Locations

### 10.1 PostgreSQL (Primary Durable Store)

- **Connection**: `DATABASE_URL` env var, default `postgresql://dopemux_age:...@dopemux-postgres-age:5432/dopemux_knowledge_graph`
- **Pool**: asyncpg, min=5, max=20 (configurable via `DB_POOL_MIN`, `DB_POOL_MAX`)
- **Schema file**: `schema.sql` (applied on startup via `_ensure_schema()`)
- **Tables** (from schema.sql):
  1. `workspace_contexts` — active context per workspace (+ optional instance_id via migration 007)
  2. `decisions` — architectural/technical decisions with rationale, tags, type
  3. `progress_entries` — task tracking with status, percentage, priority, linked_decision_id
  4. `session_snapshots` — ADHD session metrics (focus, interruptions, quality)
  5. `custom_data` — generic KV store (workspace_id, category, key → JSONB value)
  6. `entity_relationships` — knowledge graph edges (source_type/id → target_type/id, relationship_type, strength)
  7. `search_cache` — full-text search result cache (1hr TTL)
- **Views**:
  1. `recent_activity` — UNION of decisions + progress_entries
  2. `active_work` — IN_PROGRESS/PLANNED progress with linked decision context
- **Triggers**:
  1. `update_modified_column()` — auto-update `updated_at`
  2. `auto_complete_progress()` — auto-transition to COMPLETED at 100%
- **Extensions**: `uuid-ossp`, `pg_trgm`
- **Full-text search**: GIN index on `decisions(summary || rationale)` with `to_tsvector('english', ...)`

### 10.2 Migration Tables (from migrations/)

| Migration | Tables/Columns Added |
|---|---|
| 001 | 14 new columns on `decisions` (impact_score, reversibility, etc.) + `decision_relationships`, `adhd_metrics`, `review_reminders` |
| 002 | `decision_patterns` table (pattern recognition) |
| 003 | `user_id` column to multiple tables (multi-tenancy) |
| 004 | Cross-workspace query indexes |
| 007 | `instance_id` column on `progress_entries` and `created_by_instance` on `decisions` |

### 10.3 Redis (Cache Layer)

- **Connection**: `REDIS_URL` env var, default `redis://redis-primary:6379`
- **Cache keys** (all with TTL):
  - `context:{workspace_id}:{instance_id}` → 300s (5 min)
  - `query:context:{workspace_id}:{instance_id}` → 180s (3 min)
  - `decisions:{workspace_id}:{limit}` → 300s
  - `query:decisions:{workspace_id}:{limit}` → 180s
  - `progress:{workspace_id}:{status}:{limit}` → 300s
  - `recent_activity:{workspace_id}:{hours}` → 180s
  - `active_work:{workspace_id}` → 180s
  - `search:{query_hash}` → 300s
  - `custom_data:{workspace_id}:{category}:{key}` → (invalidated on write)
- **Cross-workspace caches** (from unified_queries.py):
  - `unified_search:{user_id}:{query}:{workspaces}` → 60s
  - `relationships:{decision_id}:{user_id}:{include_workspaces}:{max_depth}` → 1800s (30 min)
  - `workspace_summary:{user_id}` → 300s
  - `user_workspaces:{user_id}` → 300s
- **Cache invalidation**: Write operations explicitly delete relevant cache keys

### 10.4 No SQLite

- **Code evidence**: No SQLite imports or `.db` file references found in any ConPort source file.
- **Assessment**: Despite docs/instructions mentioning SQLite, code uses PostgreSQL + Redis exclusively.

## 11. Transport Locations

### 11.1 HTTP REST (Primary)

- **File**: `enhanced_server.py`, class `EnhancedConPortServer`
- **Framework**: aiohttp `web.Application`
- **Port**: 3004 (env `MCP_SERVER_PORT`, but overridden to 3004 in `start_with_info.sh`)
- **22 routes** registered in `setup_routes()` (see Section 7.4)
- **Middleware**: Prometheus monitoring middleware

### 11.2 SSE (MCP Protocol)

- **File**: `server.py` line 173-175: `app = mcp.sse_app(); uvicorn.run(app, ...)`
- **Port**: 3005 (from `start_with_info.sh` line 15)
- **Client config**: `.claude.json` → `"type": "sse", "url": "http://localhost:3005/mcp"`
- **Framework**: FastMCP `.sse_app()` served by uvicorn

### 11.3 stdio (MCP Protocol)

- **File**: `server.py` line 177: `mcp.run(transport="stdio")`
- **File**: `conport_mcp_stdio.py` line 169: `await mcp.run_stdio_async()`
- **Usage**: Direct invocation or via Claude Code MCP config

### 11.4 JSON-RPC over HTTP

- **File**: `enhanced_server.py` line 1681-1763
- **Endpoint**: `POST /mcp`
- **Protocol**: JSON-RPC 2.0
- **Method discovery**: `tools/list` and aliases
- **Method invocation**: `tools/call`, `tool/call`, or direct `conport_*` methods

### 11.5 Streamable HTTP

- **Not found** in any ConPort source file.

## 12. Export/Report Locations

- **No export or file-generation surfaces found** in ConPort source code.
- All data is served via HTTP JSON responses.
- Token truncation stats are included in responses when truncation occurs (`truncation_stats` key).

## 13. Architecture/Module Boundary Notes

### 13.1 Three-Process Architecture (Docker)

```
start_with_info.sh
├── info_server.py       → :4004 (FastAPI, service discovery)
├── enhanced_server.py   → :3004 (aiohttp, REST+JSON-RPC, PostgreSQL+Redis)
└── server.py sse        → :3005 (FastMCP SSE, proxies to :3004)
```

### 13.2 Dependency Graph

```
server.py (MCP SSE)  ──HTTP──▸  enhanced_server.py (REST API)
conport_mcp_stdio.py ──HTTP──▸  enhanced_server.py (REST API)
enhanced_server.py   ──asyncpg──▸  PostgreSQL (port 5432)
enhanced_server.py   ──redis──▸    Redis (port 6379)
enhanced_server.py   ──HTTP──▸     DopeconBridge (port 3016)
enhanced_server.py   ──import──▸   unified_queries.py
enhanced_server.py   ──import──▸   instance_detector.py
enhanced_server.py   ──import──▸   integration_bridge_client.py
enhanced_server.py   ──import──▸   shared_monitoring.py (via /app/shared)
enhanced_server.py   ──optional──▸ dopemux.error_handling
```

### 13.3 Registry Entries

- `conport-http`: port 3004, health `/health`, enabled in smoke
- `conport-mcp`: port 3005, health `/health`, NOT enabled in smoke

### 13.4 Compose Dependencies

- **compose.yml**: conport depends on `postgres`, `redis-primary`, `mcp-qdrant`, `dopecon-bridge`
- **Ports exposed**: 3004, 3005, 4004
- **Build context**: `./docker/mcp-servers/conport` (note: `docker/mcp-servers/` directory does NOT exist at analyzed ref — likely a symlink or build-time artifact from `docker/mcp-servers-source/`)

## 14. Intended-Use Notes

### Docs Say

- ConPort is the "Single Source of Truth" (SSoT) per workspace instructions
- Authority Invariant (INV-MEM-002): "If a decision or progress is not in ConPort, it didn't formally happen"
- Append-Only Ledger (INV-MEM-003): All events written to chronicle ledger
- Promotion (INV-MEM-004): Supervisor promotes summaries to truth

### Code Does

- **SSoT**: ConPort stores decisions and progress in PostgreSQL. It IS the durable store for these entities. However, there is no code enforcing exclusivity or preventing other services from writing to the same tables.
- **INV-MEM-002**: No enforcement code found. No validation that decisions exist before referencing them externally.
- **INV-MEM-003**: No append-only ledger implementation found in ConPort code. Records CAN be updated and deleted (e.g., `update_progress`, `delete_custom_data`). The `decisions` table does not support updates through any API endpoint (effectively append-only for decisions), but `progress_entries` and `workspace_contexts` are mutable.
- **INV-MEM-004**: "Promotion" exists but means instance→shared transition (clearing `instance_id`), NOT supervisor-promoted truth validation. No provenance tracking or source event ID citation found.
- **Deduplication**: No deduplication logic found. UUIDs prevent ID collision but content duplicates are allowed.
- **Authority boundaries**: ConPort is the canonical writer for its own tables. No locking or optimistic concurrency. Last-write-wins.

### Tests Verify

- `tests/test_instance_detector.py`: 16 tests covering env var detection, status isolation rules, convenience functions, real-world scenarios
- `tests/test_worktree_routing.py`: Integration tests for worktree routing (mocking enhanced_server)
- `test_token_limit_fix.py`: Tests for token truncation logic
- `test_worktree_validation.py`: Tests for worktree validation scenarios
- **No tests** for: JSON-RPC dispatch, REST API handlers, database operations, Redis caching, promotion logic, fork logic, unified queries, search, auto-save loop, event publishing

### Discrepancies (Docs vs Code)

| Claim | Status |
|---|---|
| ConPort is SSoT | Partially true: it stores decisions/progress durably, but no enforcement mechanism |
| INV-MEM-002 Authority Invariant | NOT IMPLEMENTED in code |
| INV-MEM-003 Append-Only Ledger | NOT IMPLEMENTED; progress and context are mutable |
| INV-MEM-004 Promotion = supervisor truth | NOT IMPLEMENTED; "promotion" means instance→shared only |
| SQLite storage | NOT PRESENT; PostgreSQL + Redis only |

## 15. Missing Evidence

1. **`docker/mcp-servers/conport/` directory** does not exist — compose files reference it for build context. Likely a symlink, copy step, or git submodule not present at this ref.
2. **No requirements.txt or pyproject.toml** inside the conport directory — dependencies are installed inline in Dockerfile: `pip install uv aiohttp asyncpg redis mcp prometheus-client fastapi uvicorn`
3. **No README** inside the conport directory — service description comes from registry and compose files
4. **Migration sequencing** — migrations 005 and 006 are absent (gap between 004 and 007)
5. **AGE graph** — `unified_queries.py` references `ag_catalog` schema and `entity_relationships` table, but no Apache AGE graph DDL (CREATE GRAPH, Cypher queries) found in conport code. The `entity_relationships` table uses relational SQL, not graph queries.
6. **Test coverage** — Only instance detector and worktree routing have unit tests. No tests for core API handlers, persistence, or JSON-RPC dispatch.
7. **No version file** — Version is hardcoded in `info_server.py` as `"1.0.0"` and in compose env as `SERVICE_VERSION`

## 16. Explicit Readiness Judgment

### **READY_FOR_PHASE_2**

**Rationale**: All primary source files have been inspected. The tool registration surfaces (FastMCP, JSON-RPC dispatch, HTTP routes) are fully enumerated. The persistence model (PostgreSQL schema + Redis cache) is documented. The transport layer (HTTP, SSE, stdio, JSON-RPC) is mapped. Active vs deprecated modules are clearly identified. Architecture boundaries and dependency graph are established.

**Caveats for Phase 2**:
- The `docker/mcp-servers/conport/` build context discrepancy must be resolved (symlink or copy artifact)
- The gap between documented invariants (INV-MEM-002/003/004) and actual code behavior should be called out explicitly in any extraction
- The `conport_mcp_stdio.py` vs `server.py` tool surfaces are near-identical but have a subtle difference in `log_decision` payload construction — treat as separate surfaces
- The JSON-RPC tool schemas in `_get_tool_schemas()` only list 9 tools but the dispatch map has 12 entries — the 3 instance management tools (`conport_fork_instance`, `conport_promote`, `conport_promote_all`) are dispatchable but not in the advertised schema
