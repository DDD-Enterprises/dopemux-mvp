# ConPort — Drift Report

**Analyzed Ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Source**: `docker/mcp-servers-source/conport/`

---

## 1. Critical Discrepancies

### 1.1 INV-MEM-002: Authority Invariant — NOT ENFORCED

| Aspect | Docs Say | Code Does |
|---|---|---|
| **Claim** | "If a decision or progress is not in ConPort, it didn't formally happen" | ConPort stores decisions/progress in PostgreSQL. No mechanism prevents other services from creating authoritative records elsewhere. |
| **Enforcement** | Implied: ConPort is the sole authority | No exclusivity enforcement. No referential integrity checks at API boundaries. Last-write-wins semantics. |
| **Evidence** | `.claude/GEMINI.md`, workspace instructions | No validation code in `enhanced_server.py` |

**Severity**: HIGH — The invariant is aspirational, not implemented.

### 1.2 INV-MEM-003: Append-Only Ledger — NOT IMPLEMENTED

| Aspect | Docs Say | Code Does |
|---|---|---|
| **Claim** | "All events written to append-only chronicle ledger" | `progress_entries` and `workspace_contexts` are fully mutable. `custom_data` supports DELETE. |
| **Append-only in practice** | All data should be immutable | Only `decisions` table is effectively append-only (no UPDATE/DELETE API routes). But the SQL schema allows updates (triggers exist). |
| **Evidence** | `.claude/GEMINI.md` | `update_progress` (line 1210), `delete_custom_data` (line 1646) |

**Severity**: HIGH — Fundamental architectural claim is false.

### 1.3 INV-MEM-004: Promotion = Supervisor Truth — DIFFERENT MEANING

| Aspect | Docs Say | Code Does |
|---|---|---|
| **Claim** | "Supervisor promotes summaries to truth; promoted content must cite source event IDs" | "Promotion" sets `instance_id = NULL` on progress entries, making them visible across worktrees. |
| **Provenance** | Source event IDs required | No provenance tracking. No event ID citation. No supervisor concept. |
| **Evidence** | `.claude/GEMINI.md` | `_promote_progress` (line 1039): `UPDATE progress_entries SET instance_id = NULL` |

**Severity**: HIGH — Same word, completely different meaning.

### 1.4 SQLite Claims vs PostgreSQL Reality

| Aspect | Docs Say | Code Does |
|---|---|---|
| **Claim** | Various docs reference SQLite as ConPort's storage | PostgreSQL + Redis exclusively |
| **Evidence** | Workspace instructions, some config docs | Zero SQLite imports in any ConPort source file |

**Severity**: MEDIUM — Documentation is stale/wrong.

---

## 2. Tool Count Discrepancies

### 2.1 FastMCP Surface

| Source | Count | Tools |
|---|---|---|
| `server.py` `@mcp.tool()` decorators | 13 | All listed in TOOL_MANIFEST.json |
| `conport_mcp_stdio.py` `@mcp.tool()` decorators | 13 | Same set (with `log_decision` payload difference) |

**Status**: ✅ Consistent

### 2.2 JSON-RPC Surface

| Source | Count | Notes |
|---|---|---|
| `dispatch_map` (line 1736-1750) | 12 | All 12 dispatchable |
| `_get_tool_schemas()` (line 1787-1917) | 9 | Only 9 advertised |
| **Gap** | 3 | `conport_fork_instance`, `conport_promote`, `conport_promote_all` are callable but NOT in schema |

**Status**: ⚠️ 3 tools are "dark" — dispatchable but not discoverable via `tools/list`

### 2.3 HTTP Surface

| Source | Count |
|---|---|
| `setup_routes()` (lines 235-280) | 22 routes |
| `/mcp` route (JSON-RPC) | 1 (counted in both HTTP and JSON-RPC) |

**Status**: ✅ Consistent with Phase 1 finding

### 2.4 FastMCP vs JSON-RPC Tool Name Mapping

| FastMCP Tool | JSON-RPC Tool | Notes |
|---|---|---|
| `get_context` | `conport_get_context` | Different names, same backend |
| `update_context` | `conport_update_context` | |
| `log_decision` | `conport_log_decision` | FastMCP uses `topic`; JSON-RPC uses `summary` |
| `get_decisions` | `conport_get_decisions` | |
| `log_progress` | `conport_log_progress` | FastMCP default status="PLANNED"; JSON-RPC default="IN_PROGRESS" |
| `get_progress` | `conport_get_progress` | |
| `update_progress` | `conport_update_progress` | FastMCP passes `updates` dict; JSON-RPC passes flat args |
| `get_recent_activity` | `conport_get_recent_activity` | |
| `get_active_work` | `conport_get_active_work` | |
| `workspace_summary` | — | No JSON-RPC equivalent in dispatch_map |
| `fork_instance` | `conport_fork_instance` | JSON-RPC: undiscoverable |
| `promote` | `conport_promote` | JSON-RPC: undiscoverable |
| `promote_all` | `conport_promote_all` | JSON-RPC: undiscoverable |

**⚠️ Key discrepancy**: `workspace_summary` is a FastMCP tool (delegates to `/api/workspace-summary`) but has NO JSON-RPC dispatch entry. It is accessible only via FastMCP or HTTP REST.

**⚠️ Default status drift**: `log_progress` defaults to `"PLANNED"` in `server.py` (line 150) but `"IN_PROGRESS"` in `enhanced_server.py` `_log_progress` (line 1150). Since FastMCP passes the default through, the effective default is `"PLANNED"` via MCP and `"IN_PROGRESS"` via JSON-RPC/HTTP.

---

## 3. Build Context Discrepancy

| Compose File | Build Context | Exists? |
|---|---|---|
| `compose.yml` line 232 | `./docker/mcp-servers/conport` | ❌ Not at analyzed ref |
| `docker-compose.smoke.yml` line 81 | `./docker/mcp-servers/conport` | ❌ Not at analyzed ref |
| Actual source | `./docker/mcp-servers-source/conport` | ✅ Exists |

**Assessment**: Likely a build-time copy/symlink step creates `docker/mcp-servers/` from `docker/mcp-servers-source/`. Not present in git tree.

---

## 4. Schema vs Code Discrepancies

### 4.1 `ag_catalog` Schema Reference

`unified_queries.py` (line 63, 108, 198, 275, 288, 341) references `ag_catalog` schema for table queries. However:
- No Apache AGE graph DDL found in ConPort code
- `entity_relationships` uses relational SQL, not Cypher
- The `ag_catalog` schema prefix may cause query failures if AGE extension is not installed

**Severity**: MEDIUM — Potential runtime failure depending on PostgreSQL configuration.

### 4.2 Missing Migrations 005, 006

Migration numbering jumps from 004 to 007. Migrations 005 and 006 are absent.

**Severity**: LOW — No functional impact, but gap suggests removed/abandoned migrations.

### 4.3 `session_snapshots` Table — No API Surface

The `session_snapshots` table exists in schema but no API endpoint reads from or writes to it.

**Severity**: LOW — Dead table.

### 4.4 `entity_relationships` — No Write API

The `entity_relationships` table exists in schema but no HTTP or JSON-RPC endpoint creates relationships. `unified_queries.py` reads from it for graph traversal.

**Severity**: MEDIUM — Table is read-only from ConPort's perspective. Data must be inserted externally.

---

## 5. Configuration Drift

### 5.1 `info_server.py` SSE URL

`info_server.py` line 38 advertises SSE URL as `http://localhost:{PORT}/sse` (port 3004). But the SSE server runs on port 3005 via `server.py`. The `/info` endpoint returns incorrect SSE connection info.

**Severity**: MEDIUM — Service discovery will return wrong SSE URL.

### 5.2 Dockerfile EXPOSE

`Dockerfile` line 32 exposes ports `3004 4004` but NOT `3005`. The SSE server on 3005 is started by `start_with_info.sh` but not declared in EXPOSE.

**Severity**: LOW — EXPOSE is documentation-only; compose port mapping handles actual exposure.

---

## 6. Test Coverage Gaps

| Component | Tests? | Coverage |
|---|---|---|
| Instance detector | ✅ | 16 unit tests |
| Worktree routing | ✅ | Integration tests (mocked) |
| Token truncation | ✅ | Unit tests |
| Worktree validation | ✅ | Edge case tests |
| HTTP REST handlers | ❌ | No tests |
| JSON-RPC dispatch | ❌ | No tests |
| PostgreSQL operations | ❌ | No tests |
| Redis caching | ❌ | No tests |
| Promotion logic | ❌ | No tests |
| Fork logic | ❌ | No tests |
| Unified queries | ❌ | No tests |
| Search | ❌ | No tests |
| Auto-save loop | ❌ | No tests |
| Event publishing | ❌ | No tests |
| Schema ensure | ❌ | No tests |

**Overall**: ~10% of functional surface area has test coverage.
