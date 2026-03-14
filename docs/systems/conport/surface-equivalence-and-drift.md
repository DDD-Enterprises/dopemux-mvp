---
id: conport-surface-equivalence-and-drift
title: ConPort Surface Equivalence And Drift
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Equivalence map and drift matrix across ConPort REST, JSON-RPC, and FastMCP callable surfaces.
---
# ConPort Surface Equivalence And Drift

## Method equivalence map

| logical operation | REST | JSON-RPC `/mcp` | FastMCP SSE / stdio | status |
|---|---|---|---|---|
| get context | `GET /api/context/{workspace_id}` | `conport_get_context` | `get_context` | equivalent |
| update context | `POST /api/context/{workspace_id}` | `conport_update_context` | `update_context` | equivalent |
| get decisions | `GET /api/decisions` | `conport_get_decisions` | `get_decisions` | equivalent |
| log decision | `POST /api/decisions` | `conport_log_decision` | `log_decision` | wrapper drift repaired; REST remains source contract |
| get progress | `GET /api/progress` | `conport_get_progress` | `get_progress` | equivalent |
| log progress | `POST /api/progress` | `conport_log_progress` | `log_progress` | wrapper drift repaired; REST remains source contract |
| update progress | `PUT /api/progress/{progress_id}` | `conport_update_progress` | `update_progress` | equivalent |
| recent activity | `GET /api/recent-activity/{workspace_id}` | `conport_get_recent_activity` | `get_recent_activity` | equivalent |
| active work | `GET /api/active-work/{workspace_id}` | `conport_get_active_work` | `get_active_work` | equivalent |
| search | `GET /api/search/{workspace_id}` | `conport_search_content` | no first-class wrapper | partial parity |
| workspace summary | `GET /api/workspace-summary` | missing from JSON-RPC discovery/dispatch surface | `workspace_summary` | drift |
| custom data | `GET/POST /api/custom_data` | no first-class JSON-RPC parity | no first-class wrapper | REST-only for now |
| fork instance | `POST /api/instance/fork` | `conport_fork_instance` | `fork_instance` | exposed but not sanctioned for PM-plane integration |
| promote | `POST /api/progress/promote` | `conport_promote` | `promote` | exposed but not sanctioned for PM-plane integration |
| promote all | `POST /api/progress/promote_all` | `conport_promote_all` | `promote_all` | exposed but not sanctioned for PM-plane integration |

## Drift matrix

| drift case | affected surfaces | current state | decision |
|---|---|---|---|
| `log_progress` default mismatch | FastMCP SSE, FastMCP stdio vs REST/JSON-RPC | wrappers previously defaulted to `PLANNED`, while REST/JSON-RPC resolve to `IN_PROGRESS` | fixed in wrappers; REST default is canonical |
| `log_decision` payload mismatch | FastMCP SSE vs REST/stdio | SSE wrapper previously sent `topic` without aligned `summary` | fixed in wrappers; wrappers now send both `topic` and `summary` |
| `workspace_summary` missing from JSON-RPC parity | JSON-RPC `/mcp` | REST and FastMCP expose it; JSON-RPC parity remains incomplete | document as compatibility gap; do not choose JSON-RPC as canonical PM surface |
| dark admin methods (`fork`, `promote`, `promote_all`) | REST, JSON-RPC, FastMCP | callable but underdocumented for PM-plane usage | retain as internal/admin-only, not sanctioned PM-plane methods |
| unauthenticated access posture | REST, JSON-RPC, FastMCP | no repo-evidenced auth gate on active ConPort callable surfaces | document as hardening risk; PM-plane adapters must treat it as a boundary concern |
| AGE / `ag_catalog` dependency ambiguity | REST and JSON-RPC implementation | enhanced server initializes graph/query logic against `ag_catalog`, but deployment assumptions remain environment-sensitive | document as operational dependency risk until deployment evidence is tighter |

## Summary

- **Drift cases identified:** 6
- **Wrapper drift fixed in code:** 2
- **Documented compatibility/runtime gaps remaining:** 4
