# ConPort — Architecture and Intended Uses

**Analyzed Ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Source**: `docker/mcp-servers-source/conport/`

---

## 1. System Architecture

### 1.1 Three-Process Docker Architecture

ConPort runs as three co-located processes inside a single Docker container, orchestrated by `start_with_info.sh`:

```
start_with_info.sh (bash, PID 1 via CMD)
├── info_server.py       → :4004 (FastAPI, service discovery, ADR-208)
├── enhanced_server.py   → :3004 (aiohttp, REST + JSON-RPC, PostgreSQL + Redis)
└── server.py sse        → :3005 (FastMCP SSE via uvicorn, proxy to :3004)
```

**Source**: `start_with_info.sh` lines 7, 11, 15

### 1.2 Server Roles

| Server | Port | Framework | Role | Persistence |
|---|---|---|---|---|
| `enhanced_server.py` | 3004 | aiohttp | **Canonical data server**. All reads/writes go through PostgreSQL + Redis. | PostgreSQL (durable), Redis (cache) |
| `server.py` | 3005 | FastMCP/uvicorn | **MCP protocol proxy**. Translates MCP tool calls to HTTP requests against :3004. | None (stateless proxy) |
| `info_server.py` | 4004 | FastAPI/uvicorn | **Service discovery sidecar**. Exposes `/health` and `/info` for ADR-208 auto-config. | None (stateless) |

### 1.3 Dependency Graph

```
server.py (MCP SSE :3005)     ──HTTP──▸  enhanced_server.py (REST :3004)
conport_mcp_stdio.py (stdio)  ──HTTP──▸  enhanced_server.py (REST :3004)
enhanced_server.py             ──asyncpg──▸  PostgreSQL (:5432)
enhanced_server.py             ──redis──▸    Redis (:6379)
enhanced_server.py             ──HTTP──▸     DopeconBridge (:3016) [optional]
enhanced_server.py             ──import──▸   unified_queries.py
enhanced_server.py             ──import──▸   instance_detector.py
enhanced_server.py             ──import──▸   integration_bridge_client.py
enhanced_server.py             ──import──▸   shared_monitoring.py
enhanced_server.py             ──optional──▸ dopemux.error_handling
```

**Source**: `enhanced_server.py` lines 43-64, 112-116, 192-210

### 1.4 Compose Dependencies

From `compose.yml` lines 226-260:
- **depends_on**: `postgres`, `redis-primary`, `mcp-qdrant`, `dopecon-bridge`
- **Ports exposed**: 3004, 3005, 4004
- **Build context**: `./docker/mcp-servers/conport` (⚠️ does not exist at analyzed ref; see DRIFT_REPORT.md)

---

## 2. Data Architecture

### 2.1 PostgreSQL (Primary Durable Store)

**Connection**: `DATABASE_URL` env var
**Default**: `postgresql://dopemux_age:...@dopemux-postgres-age:5432/dopemux_knowledge_graph`
**Driver**: asyncpg with connection pool (min=5, max=20, configurable)

**Source**: `enhanced_server.py` lines 112-115, 159-171

#### Base Schema (7 tables from `schema.sql`)

1. `workspace_contexts` — Active context per workspace/instance
2. `decisions` — Architectural/technical decisions with rationale
3. `progress_entries` — Task tracking with status lifecycle
4. `session_snapshots` — ADHD session metrics
5. `custom_data` — Generic KV store (workspace+category+key → JSONB)
6. `entity_relationships` — Knowledge graph edges (relational, NOT Apache AGE Cypher)
7. `search_cache` — Full-text search result cache (1hr TTL)

#### Migration-Added Tables (3 tables from migrations 001-002)

8. `decision_relationships` — Decision genealogy (supersedes, validates, etc.)
9. `adhd_metrics` — Time-series ADHD metrics (energy, focus, attention)
10. `review_reminders` — Scheduled decision review reminders

#### Migration-Added Tables (3 tables from migration 003)

11. `users` — User management (id, email, display_name, settings)
12. `workspaces` — Workspace metadata (id, owner, name, path)
13. `user_workspace_access` — RBAC (user × workspace × role)

### 2.2 Redis (Cache Layer)

**Connection**: `REDIS_URL` env var, default `redis://redis-primary:6379`
**Purpose**: Read caching with explicit TTLs and write-through invalidation

All cache keys are workspace-scoped or workspace+instance-scoped. No Redis persistence is relied upon — PostgreSQL is the single durable store.

**Source**: `enhanced_server.py` lines 116, 182-189

### 2.3 No SQLite

**Code evidence**: Zero SQLite imports or `.db` file references in any ConPort source file. Despite documentation elsewhere claiming SQLite usage, the code exclusively uses PostgreSQL + Redis.

---

## 3. Multi-Tenancy Model

### 3.1 Workspace Isolation

Every data entity is scoped by `workspace_id` (VARCHAR 255). This is the primary isolation boundary.

- **Env var**: `DOPEMUX_WORKSPACE_ID` (read by `instance_detector.py`)
- **Fallback**: Current working directory
- **Source**: `instance_detector.py` lines 80-110

### 3.2 Instance Isolation (Worktree Support)

Within a workspace, data can be further isolated by `instance_id` for git worktree support.

- **Env var**: `DOPEMUX_INSTANCE_ID`
- **Isolation rules** (from `instance_detector.py` line 146):
  - `IN_PROGRESS`, `PLANNED` → **isolated** (instance-specific)
  - `COMPLETED`, `BLOCKED`, `CANCELLED` → **shared** (instance_id = NULL)

**Source**: `instance_detector.py` lines 145-175, `enhanced_server.py` lines 1228-1237

### 3.3 User-Level Multi-Tenancy (Migration 003)

Migration 003 adds `user_id` columns to 5 tables with default `'default'`. Tables `users`, `workspaces`, and `user_workspace_access` implement RBAC.

**Status**: Schema exists but `enhanced_server.py` handlers do NOT filter by `user_id` in most queries. Only `unified_queries.py` uses `user_id` for cross-workspace queries.

---

## 4. Authority Model — Docs vs Code

### 4.1 What Documentation Claims

| Invariant | Claim |
|---|---|
| INV-MEM-002 | "If a decision or progress is not in ConPort, it didn't formally happen" |
| INV-MEM-003 | "All events written to append-only chronicle ledger" |
| INV-MEM-004 | "Supervisor promotes summaries to truth; promoted content must cite source event IDs" |

**Source**: `.claude/GEMINI.md` and workspace instructions

### 4.2 What Code Actually Implements

| Invariant | Actual Implementation | Evidence |
|---|---|---|
| INV-MEM-002 | **NOT ENFORCED**. ConPort stores decisions/progress durably in PostgreSQL, but no mechanism prevents other services from bypassing ConPort or creating authoritative records elsewhere. No referential integrity check exists at the API level. | No validation code found in `enhanced_server.py` |
| INV-MEM-003 | **NOT IMPLEMENTED**. Records are mutable: `update_progress` updates in place, `delete_custom_data` deletes records. `decisions` table has no UPDATE endpoint (effectively append-only for decisions via API), but `workspace_contexts` and `progress_entries` are fully mutable. | `enhanced_server.py` lines 1210-1320 (update_progress), 1646-1679 (delete_custom_data) |
| INV-MEM-004 | **DIFFERENT MEANING**. "Promotion" in code means setting `instance_id = NULL` to make an instance-local progress entry visible to all worktrees. No supervisor validation, no provenance tracking, no source event ID citation. | `enhanced_server.py` lines 1039-1073 (_promote_progress) |

### 4.3 What "Promotion" Actually Means in Code

```
Instance-local entry (instance_id = "feature-auth")
    ↓ promote (API call)
Shared entry (instance_id = NULL, visible to all worktrees)
```

**NOT**: Raw log → supervisor review → validated truth

**Source**: `enhanced_server.py` lines 1039-1073

---

## 5. Intended Uses

### 5.1 Primary Use Case: ADHD-Optimized Context Preservation

ConPort is designed to preserve cognitive context across sessions for neurodivergent developers:

- **Auto-save loop** (30s interval): Touches `updated_at` on recently active contexts
- **Context loading**: `get_context` returns workspace state for session resumption
- **Activity feed**: `get_recent_activity` shows last N hours of decisions+progress
- **Active work view**: `get_active_work` shows prioritized IN_PROGRESS/PLANNED items
- **Token budgeting**: Responses truncated to 9000 tokens to fit LLM context windows

**Source**: `enhanced_server.py` lines 118-119, 1497-1521, 725-787

### 5.2 Decision Tracking

Persistent record of architectural and technical decisions with:
- Summary, rationale, alternatives, tags
- Confidence level, decision type
- Enhanced metadata (migration 001): impact score, reversibility, cognitive load, energy level
- Decision relationships (migration 001): builds_upon, supersedes, conflicts_with, validates

### 5.3 Progress Tracking

Task/progress lifecycle management:
- Status workflow: PLANNED → IN_PROGRESS → COMPLETED (or BLOCKED/CANCELLED)
- Auto-complete trigger: percentage=100 → status=COMPLETED (SQL trigger)
- Priority ordering: urgent > high > medium > low
- Linked decisions: progress entries can reference a decision

### 5.4 Cross-Workspace Queries (F-NEW-7)

Via `unified_queries.py`:
- Cross-workspace full-text search (target: <200ms)
- Relationship graph traversal (recursive CTE, target: <500ms for depth-3)
- Workspace summary aggregation (target: <100ms)

### 5.5 Event Publishing

ConPort publishes events to DopeconBridge when decisions are logged or progress is updated, enabling:
- Dashboard real-time updates
- ADHD Engine reactions
- Cross-service coordination

**Event types**: `decision_logged`, `progress_updated`
**Source**: `integration_bridge_client.py` lines 122-162
