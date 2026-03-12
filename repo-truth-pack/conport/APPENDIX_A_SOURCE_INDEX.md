# ConPort Phase 1 — Appendix A: Source Index

**Analyzed Ref**: `fe48c0a874ac25ed179b9ddb091252a6dbe9b5c2`
**Branch**: `codex/main-drain-20260306`
**Generated**: 2026-03-09

---

## Root Docs

| File | Lines | Role |
|---|---|---|
| `.claude.json` | (key: `dopemux-conport`) | MCP client config (SSE on :3005/mcp) |
| `compose.yml` | 232-260 | Docker service definition for conport |
| `docker-compose.smoke.yml` | 80-100 | Smoke stack conport definition |
| `docker-compose.mcp-test.yml` | (references) | MCP test stack reference |
| `services/registry.yaml` | 87-115 | Registry entries: conport-http (3004), conport-mcp (3005) |

## docs/

| File | Role |
|---|---|
| `.claude/llms.md` | Mentions conport as "Decision tracking and architecture memory" |
| `.claude/MULTI_LANGUAGE_SUPPORT.md` | References conport Python patterns |
| `.claude/claude_config.json.bak_*` | Backup MCP configs with conport and conport-admin |

## Source (docker/mcp-servers-source/conport/)

### Active Server Files

| File | Lines | Role | Active? |
|---|---|---|---|
| `enhanced_server.py` | 2149 | Primary HTTP+JSON-RPC server (PostgreSQL+Redis) | ✅ Active |
| `server.py` | 178 | FastMCP SSE/stdio thin client (proxies to :3004) | ✅ Active |
| `conport_mcp_stdio.py` | 175 | FastMCP stdio-only admin client | ✅ Active |
| `info_server.py` | 62 | Service discovery sidecar (FastAPI, port 4004) | ✅ Active |
| `start_with_info.sh` | 19 | Multi-process entrypoint (runs all 3 above) | ✅ Active |

### Support Modules

| File | Lines | Role | Active? |
|---|---|---|---|
| `unified_queries.py` | 361 | Cross-workspace query layer (asyncpg+redis) | ✅ Active |
| `instance_detector.py` | 197 | Worktree instance detection (env vars) | ✅ Active |
| `integration_bridge_client.py` | 163 | DopeconBridge event publisher | ✅ Active |
| `shared_monitoring.py` | 359 | Prometheus monitoring base class | ✅ Active |
| `shared_monitoring_init.py` | 5 | Monitoring package __init__.py | ✅ Active |

### Deprecated/Auxiliary Files

| File | Lines | Role | Active? |
|---|---|---|---|
| `direct_server.py` | 271 | Prototype HTTP server (mock data) | ❌ Deprecated |
| `simple_metrics_server.py` | 48 | Standalone metrics server | ❌ Superseded |
| `schema.sql.bak` | ~291 | Backup of schema.sql | ❌ Backup |

### Schema & Migrations

| File | Lines | Role |
|---|---|---|
| `schema.sql` | 291 | Base PostgreSQL schema (7 tables, 2 views, 3 triggers) |
| `migrations/001_enhanced_decision_model.sql` | ~200 | Phase 1: Enhanced decision metadata + 3 new tables |
| `migrations/002_decision_patterns_table.sql` | ~80 | Phase 2: Decision patterns table |
| `migrations/003_multi_tenancy_foundation.sql` | ~150 | Phase 3: user_id multi-tenancy columns |
| `migrations/004_unified_query_indexes.sql` | ~100 | Phase 4: Cross-workspace search indexes |
| `migrations/007_worktree_support_simple.sql` | ~50 | Migration 7: instance_id for worktree isolation |
| `migrations/007_rollback.sql` | ~20 | Rollback for migration 7 |
| `migrations/README.md` | ~120 | Migration 7 documentation |
| `migrations/run_migration_001.py` | ~50 | Python runner for migration 001 |
| `migrations/run_migration_002.py` | ~50 | Python runner for migration 002 |
| `migrations/test_migration_007.sh` | ~30 | Test script for migration 007 |

## Tests

| File | Lines | Role | Coverage |
|---|---|---|---|
| `tests/test_instance_detector.py` | ~180 | Unit tests for SimpleInstanceDetector | 16 tests, env vars, status rules, scenarios |
| `tests/test_worktree_routing.py` | ~200 | Integration tests for worktree routing | Mocked enhanced_server |
| `test_token_limit_fix.py` | ~100 | Token truncation logic tests | _estimate_tokens, _truncate_decisions |
| `test_worktree_validation.py` | ~100 | Worktree validation scenarios | Validation edge cases |

## Build/Runtime

| File | Lines | Role |
|---|---|---|
| `Dockerfile` | 40 | Container build: python:3.11-slim, pip install deps |
| `start_with_info.sh` | 19 | Entrypoint: 3 processes (info, enhanced, server sse) |

## Release/Tag Sources

- No release tags found specific to conport. Versioned only via `info_server.py` hardcoded `"1.0.0"`.

## External References (services/ and compose/)

| File | Role |
|---|---|
| `services/registry.yaml` | Port registry (3004, 3005) |
| `services/dopemux-gpt-researcher/research_api/adapters/conport_adapter.py` | ConPort client adapter |
| `services/task-router/router_api.py` | References CONPORT_URL |
| `services/monitoring-dashboard/server.py` | References conport health |
| `services/genetic_agent/shared/mcp/memory_adapter.py` | ConPort memory adapter |
| `services/adhd_engine/domains/attention/context_preserver.py` | ConPort context integration |
| `services/adhd_engine/domains/task_enablement/working_memory_support.py` | ConPort progress integration |
| `compose/legacy/conport-kg-docker-compose.yml` | Legacy KG compose |
