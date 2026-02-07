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
2. `services/`
3. `tests/`
4. `docs/` (excluding `docs/archive/**`, `docs/05-audit-reports/**`, `docs/06-research/**`)

Artifacts and generator:

1. `reports/strict_closure/semantic_search_reference_inventory_2026-02-07.json`
2. `scripts/docs_audit/extract_semantic_search_reference_inventory.py`

## Summary

Current active-reference counts:

1. files with semantic-search refs: `34`
2. code files: `19`
3. test files: `5`
4. doc files: `10`
5. bridge legacy route refs (`/conport/semantic_search`): `5`
6. legacy endpoint refs (`/api/semantic-search`): `5` (compat fallback + tests)
7. current endpoint refs (`/api/adhd/semantic-search`): `10`
8. `semantic_search_conport` tool refs: `17`

## P1 Findings Promoted To Master Fix Scope

### 1) Session-manager bridge route drift (closed in this wave)

`session-manager` clients call `/conport/semantic_search` on dopecon-bridge.
This compatibility route is now explicitly implemented in active bridge runtime.

Primary paths:

1. `services/session-manager/src/conport_client.py`
2. `services/session-manager/src/conport_http_client.py`
3. `services/dopecon-bridge/main.py`
4. `services/dopecon-bridge/dopecon_bridge/conport_semantic_proxy.py`
5. `tests/unit/test_dopecon_bridge_semantic_proxy.py`

Required closure:

1. Keep route-level integration test coverage (HTTP-level) to guard startup wiring.
2. Continue planned migration away from bridge legacy route when downstream callers are updated.

### 2) Deprecated ConPort tool callers still active

Runtime callers still directly invoke `semantic_search_conport` compatibility tool.

Primary paths:

1. `services/task-orchestrator/conport_mcp_client.py`
2. `services/task-orchestrator/app/adapters/conport_adapter.py`
3. `services/working-memory-assistant/conport_client.py`

Required closure:

1. Migrate to final intended retrieval path (`dope-context`/Serena-backed flow) or keep shim with explicit deprecation horizon and owner.
2. Keep no-breaking behavior while migration is in flight.

### 3) Active docs still describe old/default semantic-search behavior

Several active docs still describe semantic search as a primary ConPort runtime path without clear compatibility labeling.

Owner bucket:

1. Docs + ConPort/Bridge/Serena owners

Required closure:

1. Mark each active reference as `Implemented (compat shim)` vs `Planned` vs `Migrated`.
2. Ensure docs align with runtime fallback behavior and migration state.

## Notes

1. Legacy endpoint refs in active code are currently isolated to the explicit compatibility fallback in `src/dopemux/tools/conport_client.py` and its tests.
2. This inventory is evidence capture; implementation closure is tracked in the master miss matrix.
