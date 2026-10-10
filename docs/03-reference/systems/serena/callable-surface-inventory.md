---
id: serena-callable-surface-inventory
title: Serena Callable Surface Inventory
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-20'
last_review: '2026-03-20'
next_review: '2026-06-18'
prelude: Inventory and classification of repo-proven Serena callable surfaces, with active-runtime status called out explicitly.
---
# Serena Callable Surface Inventory

For the current merged deployment/local capability view, see [capability-manifest.md](./capability-manifest.md).

## Active runtime surfaces

| surface | transport | status | classification | notes |
|---|---|---|---|---|
| `GET /health` | HTTP | repo-proven live | `safe_read_only` | Served by `info_server.py`; smoke-checked locally. |
| `GET /info` | HTTP | repo-proven live | `safe_read_only` | Returns metadata including advertised SSE endpoint. |
| `/sse` | MCP-over-SSE proxy | wired by runtime, not end-to-end smoke-checked in this packet | `safe_read_only` | Exposed by wrapper via `mcp-proxy` around upstream Serena. |

## Local non-deployed candidate surfaces

The following are present in `services/serena/` but not sanctioned for PM-plane dependency because active deployment proof is absent:

- local MCP tools registered by `services/serena/mcp_server.py`
- local HTTP endpoints in `services/serena/http_server.py`
- local ConPort-writing integrations

Classification for PM-plane consumption:

- local read surfaces: `never_expose_directly` until deployment proof exists
- local write-capable producer surfaces: `never_expose_directly`

## Sanctioned PM-plane contract

Allowed now:

- `pm_get_technical_context`

Blocked pending live runtime proof:

- `pm_get_implementation_context`
- `pm_get_code_impact_context`
- `pm_get_technical_risks`
