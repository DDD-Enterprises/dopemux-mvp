# ConPort — Executive Summary

**Component**: ConPort (Knowledge Graph & Context Management)
**Path**: `docker/mcp-servers-source/conport/`
**Analyzed Ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Branch**: `codex/main-drain-20260306`

---

## What ConPort Is

ConPort is an ADHD-optimized context preservation and decision tracking server that stores structured project knowledge in PostgreSQL with Redis caching. It exposes three callable surfaces: a FastMCP proxy (13 tools via SSE/stdio), a JSON-RPC endpoint (12 tools via HTTP), and a REST API (22 routes).

## Architecture

Three co-located processes in one Docker container:

| Process | Port | Role |
|---|---|---|
| `enhanced_server.py` | 3004 | Canonical data server (aiohttp, PostgreSQL + Redis) |
| `server.py` (SSE mode) | 3005 | FastMCP protocol proxy → delegates to :3004 |
| `info_server.py` | 4004 | Service discovery sidecar (ADR-208) |

## Data Model

**PostgreSQL** (7 base tables + 6 migration-added tables):
- Core: `workspace_contexts`, `decisions`, `progress_entries`, `session_snapshots`, `custom_data`, `entity_relationships`, `search_cache`
- Migration-added: `decision_relationships`, `adhd_metrics`, `review_reminders`, `decision_patterns`, `users`, `workspaces`, `user_workspace_access`

**Redis**: Read cache (60s–1800s TTL) with write-through invalidation. Not durable.

## Key Capabilities

1. **Decision tracking**: Append-only via API (no update/delete routes for decisions)
2. **Progress management**: Full CRUD with status lifecycle (PLANNED → IN_PROGRESS → COMPLETED)
3. **Worktree isolation**: IN_PROGRESS/PLANNED scoped to instances; COMPLETED/BLOCKED shared
4. **Fork/Promote**: Copy progress between worktree instances and shared state
5. **Cross-workspace search**: Full-text search across workspaces via unified query layer
6. **Event publishing**: Decision/progress changes published to DopeconBridge
7. **Token budgeting**: Responses truncated to 9000 tokens for LLM context windows

## Critical Findings

### ⚠️ Invariant Violations (Docs vs Code)

| Invariant | Docs Claim | Code Reality |
|---|---|---|
| INV-MEM-002 | ConPort is sole authority | No exclusivity enforcement |
| INV-MEM-003 | Append-only ledger | Progress and context are mutable; custom_data supports DELETE |
| INV-MEM-004 | Supervisor promotes to truth | "Promotion" = clear instance_id for worktree sharing only |

### ⚠️ Tool Surface Gaps

- 3 JSON-RPC tools are dispatchable but NOT discoverable via `tools/list`
- `workspace_summary` exists in FastMCP but NOT in JSON-RPC dispatch
- `log_progress` default status differs: `"PLANNED"` (FastMCP) vs `"IN_PROGRESS"` (JSON-RPC/HTTP)
- `log_decision` payload differs between `server.py` (sends `topic`) and `conport_mcp_stdio.py` (sends `summary`)

### ⚠️ Other Drift

- Docs claim SQLite; code uses PostgreSQL exclusively
- Build context `docker/mcp-servers/conport` doesn't exist at analyzed ref
- `unified_queries.py` references `ag_catalog` schema that may not exist
- `session_snapshots` and `entity_relationships` tables have no write API
- ~10% test coverage (only instance detector and token truncation tested)
- Migrations 005 and 006 are missing (gap in sequence)

## Integration Guidance

- **AI agents**: Use FastMCP SSE at `http://localhost:3005/mcp`
- **Backend services**: Use HTTP REST at `http://localhost:3004/api/*`
- **Monitoring**: Health at `:3004/health`, metrics at `:3004/metrics`
- **Event consumers**: Subscribe to DopeconBridge for `decision_logged` / `progress_updated`
- **No authentication**: All endpoints are unauthenticated

## Artifact Inventory

| File | Description |
|---|---|
| `REPO_IDENTITY.md` | Component identification, dependencies, file manifest |
| `TOOL_MANIFEST.json` | All 3 callable surfaces with full tool/route inventory |
| `ARCHITECTURE_AND_INTENDED_USES.md` | System architecture, authority model, intended uses |
| `DATA_MODEL.md` | All 13 tables, views, triggers, migrations, Redis cache patterns |
| `WORKFLOW_AND_GATES.md` | Status lifecycle, isolation rules, fork/promote, event gates |
| `TRANSPORT_AND_RUNBOOK.md` | All 6 transports, startup, health, env vars, troubleshooting |
| `DRIFT_REPORT.md` | INV-MEM violations, tool count gaps, config drift, test gaps |
| `INTEGRATION_NOTES.md` | Client patterns, data contracts, event formats, risks |
| `CONTRACT_SCHEMAS/` | JSON Schema Draft 2020-12 for all tool/route contracts |
| `APPENDIX_A_SOURCE_INDEX.md` | Phase 1 source file inventory |
| `DISCOVERY_NOTES.md` | Phase 1 detailed findings |
| `COMMAND_LOG.md` | Phase 1 command audit trail |
| `SEARCH_PATTERNS.txt` | Phase 1 search patterns used |
| `INSPECTED_FILES.txt` | Phase 1 inspected file list |
