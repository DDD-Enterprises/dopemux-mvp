---
id: SEMANTIC_SEARCH_REFERENCE_INVENTORY_2026_02_07
title: Semantic Search Reference Inventory 2026 02 07
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-07'
last_review: '2026-02-07'
next_review: '2026-02-21'
status: draft
prelude: Active tracked-file inventory of semantic-search references with P1 migration risks and owner-targeted closure actions.
---
# Semantic Search Reference Inventory (2026-02-07)

## Scope

Inventory source is tracked files under:

1. `src/`
1. `services/`
1. `tests/`
1. `docs/` (excluding `docs/archive/**`, `docs/05-audit-reports/**`, `docs/06-research/**`)

Artifacts and generator:

1. `reports/strict_closure/semantic_search_reference_inventory_2026-02-07.json`
1. `scripts/docs_audit/extract_semantic_search_reference_inventory.py`

## Summary

Current active-reference counts:

1. files with semantic-search refs: `38`
1. code files: `20`
1. test files: `8`
1. doc files: `10`
1. bridge legacy route refs (`/conport/semantic_search`): `5`
1. legacy endpoint refs (`/api/semantic-search`): `11` (compat fallback + tests)
1. current endpoint refs (`/api/adhd/semantic-search`): `16`
1. `semantic_search_conport` tool refs: `22`

## P1 Findings Promoted To Master Fix Scope

### 1) Session-manager bridge route drift (closed in this wave)

`session-manager` clients call `/conport/semantic_search` on dopecon-bridge.
This compatibility route is now explicitly implemented in active bridge runtime.

Primary paths:

1. `services/session-manager/src/conport_client.py`
1. `services/session-manager/src/conport_http_client.py`
1. `services/dopecon-bridge/main.py`
1. `services/dopecon-bridge/dopecon_bridge/conport_semantic_proxy.py`
1. `tests/unit/test_dopecon_bridge_semantic_proxy.py`

Required closure:

1. Keep route-level integration test coverage (HTTP-level) to guard startup wiring.
1. Continue planned migration away from bridge legacy route when downstream callers are updated.

### 2) Deprecated ConPort tool callers still active (partially closed)

Runtime callers now prefer the non-legacy semantic tool where available, but
legacy alias support is still present for compatibility.

Primary paths:

1. `services/task-orchestrator/conport_mcp_client.py`
1. `services/task-orchestrator/app/adapters/conport_adapter.py`
1. `services/working-memory-assistant/conport_client.py`
1. `tests/unit/test_task_orchestrator_conport_semantic_resolution.py`
1. `tests/unit/test_wma_conport_semantic_resolution.py`

Required closure:

1. Remove/rename remaining legacy-named method and adapter references (`semantic_search_conport`) after downstream contract migration is complete.
1. Keep no-breaking behavior while migration is in flight.

### 3) Active docs still describe old/default semantic-search behavior

Several active docs still describe semantic search as a primary ConPort runtime path without clear compatibility labeling.

Owner bucket:

1. Docs + ConPort/Bridge/Serena owners

Required closure:

1. Mark each active reference as `Implemented (compat shim)` vs `Planned` vs `Migrated`.
1. Ensure docs align with runtime fallback behavior and migration state.

## Notes

1. Legacy endpoint refs in active code are currently isolated to the explicit compatibility fallback in `src/dopemux/tools/conport_client.py` and its tests.
1. This inventory is evidence capture; implementation closure is tracked in the master miss matrix.
