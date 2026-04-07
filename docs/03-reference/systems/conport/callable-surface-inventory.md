---
id: conport-callable-surface-inventory
title: ConPort Callable Surface Inventory
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Inventory of active ConPort REST, JSON-RPC, and FastMCP callable surfaces used by the PM plane.
---
# ConPort Callable Surface Inventory

This inventory captures the active callable surfaces in the ConPort runtime under [`docker/mcp-servers-source/conport/`](../../../docker/mcp-servers-source/conport/).

## Surface inventory

| surface | transport | entrypoint | primary files | scope | notes |
|---|---|---|---|---|---|
| REST `/api/*` | HTTP | `enhanced_server.py` on port `3004` | `enhanced_server.py` | Decisions, progress, context, search, custom data, activity, admin progress-instance operations | Preferred backend integration surface for the PM plane. |
| JSON-RPC `/mcp` | HTTP JSON-RPC | `enhanced_server.py` on port `3004` | `enhanced_server.py` | `tools/list`, `tools/call`, direct `conport_*` method dispatch | Compatibility surface with known discovery/payload drift. |
| FastMCP SSE | HTTP SSE | `server.py sse` on port `3005` | `server.py` | Agent-facing tool wrapper over REST operations | Wrapper surface; not the canonical backend contract. |
| FastMCP stdio | stdio | `conport_mcp_stdio.py` | `conport_mcp_stdio.py` | Admin/tool wrapper over REST operations | Operational wrapper aligned to the same logical contract as the SSE wrapper. |

## Active REST operations

- `/api/context/{workspace_id}`
- `/api/decisions`
- `/api/progress`
- `/api/progress/{progress_id}`
- `/api/recent-activity/{workspace_id}`
- `/api/active-work/{workspace_id}`
- `/api/search/{workspace_id}`
- `/api/workspace-summary`
- `/api/custom_data`
- `/api/instance/fork`
- `/api/progress/promote`
- `/api/progress/promote_all`

## FastMCP tool families

The FastMCP wrappers currently expose tool families for:

- context get/update
- decisions get/log
- progress get/log/update
- recent activity
- active work
- workspace summary
- fork/promote/promote_all

## Surface posture summary

- REST is the broadest and most explicit contract.
- FastMCP surfaces are wrappers over REST and should stay aligned to REST semantics.
- JSON-RPC remains useful for compatibility, but it is not sufficiently aligned to serve as the PM plane's preferred integration contract today.
