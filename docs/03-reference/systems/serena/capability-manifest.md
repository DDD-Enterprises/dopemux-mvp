---
id: serena-capability-manifest
title: Serena Capability Manifest
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-31'
last_review: '2026-03-31'
next_review: '2026-06-29'
prelude: Current repo-truth manifest for Serena deployment status, callable surfaces, local implementation capabilities, and validation state.
---
# Serena Capability Manifest

## Authority

Current authority for Serena runtime/deployment status is:

- `docker/compose.core.yml`
- `docker/mcp-servers-source/serena/`
- `services/serena/`
- [deployment-alignment-and-sanctioned-contract.md](./deployment-alignment-and-sanctioned-contract.md)
- [runtime-candidate-inventory.md](./runtime-candidate-inventory.md)

## Runtime surfaces

| surface | status | transport | backing path | notes |
|---|---|---|---|---|
| Dockerized Serena wrapper | deployed runtime candidate | HTTP info server + MCP-over-SSE proxy | `docker/mcp-servers-source/serena/` | Repo-proven deployed path. PM-plane must treat this as the active Serena runtime until deployment proof changes. |
| Local Serena implementation tree | implementation candidate | local MCP stdio server + local FastAPI HTTP server | `services/serena/` | Richer local feature surface, not repo-proven deployed. |

## Sanctioned PM-plane contract

Allowed:

- `pm_get_technical_context`

Blocked pending live runtime proof:

- `pm_get_implementation_context`
- `pm_get_code_impact_context`
- `pm_get_technical_risks`

## Local implementation candidate

### MCP server

- Path: `services/serena/mcp_server.py`
- Transport: MCP over stdio
- Registered local tools: `33`
- LSP engine: `EnhancedLSPWrapper`
- LSP language targets: Python, TypeScript, Rust
- Tier 3 mode: database-backed with explicit fallback metadata
- Runtime surface classification: `implementation_candidate`

Tool groups:

- Phase 1 files: `read_file`, `list_dir`
- Phase 2A: `get_workspace_status`
- Phase 2B: `find_symbol`, `goto_definition`, `get_context`, `find_references`
- Phase 2C: `analyze_complexity`, `filter_by_focus`, `suggest_next_step`, `get_reading_order`
- Enhanced navigation: `find_similar_code`, `predict_navigation_from_git`, `find_test_file`, `get_unified_complexity`
- Phase 2D: `find_relationships`, `get_navigation_patterns`, `update_focus_mode`
- Feature 1 detection/actions/config/metrics: remaining registered tools

### HTTP server

- Path: `services/serena/http_server.py`
- Transport: FastAPI
- Repo-proven local endpoints:
  - `GET /`
  - `GET /health`
  - `GET /api/metrics`
  - `GET /api/detections/summary`
  - `GET /api/patterns/top`
  - `GET /api/patterns/{pattern_id}`
- Status: local diagnostics/operator surface only, not sanctioned PM-plane dependency

### Dependencies

- PostgreSQL: required for local intelligence persistence and Tier 3 history/profile paths
- Redis: optional but expected for navigation cache acceleration
- Language servers:
  - `pylsp`
  - `typescript-language-server`
  - `rust-analyzer`
- Tree-sitter and ADHD helper components: local optional enhancements with graceful degradation

## Current local behavior

- `find_symbol`, `goto_definition`, and `find_references` route through `EnhancedLSPWrapper` when available and return explicit degraded metadata when they fall back.
- `find_relationships` uses PostgreSQL graph data through `SerenaGraphOperations` when available and falls back explicitly to regex scanning when graph data is unavailable or empty.
- `get_navigation_patterns` reads persisted history from `navigation_patterns` when available and returns `history_unavailable` with explicit provenance when it cannot.
- `update_focus_mode` maps Serena focus state onto `learning_profiles` persistence fields and reloads persisted mode on database initialization when a stored profile exists.

## Validation state

Validation run on `2026-03-31` against the local implementation candidate:

- `python -m py_compile services/serena/mcp_server.py services/serena/multi_workspace_wrapper.py services/serena/test_http_server.py services/serena/intelligence/test_database.py services/serena/intelligence/complete_system_integration_test.py`
  - passed
- `UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=services/serena uv run pytest services/serena --collect-only -q`
  - passed
- `UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=services/serena uv run pytest services/serena -q`
  - exited `0`
  - collection count earlier in the same packet: `49`
  - database-gated tests skipped when local Postgres test initialization failed: `14`
  - implied non-skipped passing tests: `35`

## Phase 3 backlog after stabilization

First wave:

- interruption-aware resume packets from navigation history plus working-memory state
- cross-workspace graph fusion instead of per-workspace aggregation only
- provenance-scored navigation responses
- next-safe-chunk recommendations from complexity and fatigue signals

Second wave:

- predictive navigation/task suggestions
- team/shared cognitive views
- advanced analytics and pattern reporting
