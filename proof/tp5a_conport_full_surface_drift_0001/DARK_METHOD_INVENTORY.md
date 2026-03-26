# ConPort Dark Method Inventory

**Date:** 2026-03-12
**Definition:** Implemented and callable, but not part of the sanctioned PM-plane contract.
This includes methods that are: internal/admin-only, multi-instance management concerns, or reachable
but not documented as general PM-plane operations.

---

## Dark Methods

### 1. fork_instance

| Field | Value |
|-------|-------|
| logical_operation | `fork_instance` |
| REST endpoint | `POST /api/instance/fork` |
| JSON-RPC method | `conport_fork_instance` |
| FastMCP tool | `fork_instance` |
| discoverable | YES — appears on all three surfaces, including `tools/list` |
| PM-plane sanctioned | **NO** |
| reason | Multi-instance worktree concern. Copies PLANNED/IN_PROGRESS progress entries from source_instance to target_instance. This is an internal ConPort operational command, not a PM workflow operation. |
| decision | Retain as internal/admin-only. PM-plane integrations must not call fork_instance as part of normal workflow. |
| auth_required | No (same auth gap as all surfaces) |

### 2. promote

| Field | Value |
|-------|-------|
| logical_operation | `promote_progress` |
| REST endpoint | `POST /api/progress/promote` |
| JSON-RPC method | `conport_promote` |
| FastMCP tool | `promote` |
| discoverable | YES — appears on all three surfaces |
| PM-plane sanctioned | **NO** |
| reason | Instance promotion concern. Clears instance_id from a single progress entry to make it visible across all instances. Internal ConPort lifecycle management. |
| decision | Retain as internal/admin-only. Not for PM-plane workflows. |
| auth_required | No |

### 3. promote_all

| Field | Value |
|-------|-------|
| logical_operation | `promote_all` |
| REST endpoint | `POST /api/progress/promote_all` |
| JSON-RPC method | `conport_promote_all` |
| FastMCP tool | `promote_all` |
| discoverable | YES — appears on all three surfaces |
| PM-plane sanctioned | **NO** |
| reason | Bulk instance promotion. Same concern as promote but batch. |
| decision | Retain as internal/admin-only. Not for PM-plane workflows. |
| auth_required | No |

### 4. search_content on JSON-RPC (undiscoverable)

| Field | Value |
|-------|-------|
| logical_operation | `search_content` |
| REST endpoint | `GET /api/search/{workspace_id}` |
| JSON-RPC method | `conport_search_content` |
| FastMCP tool | MISSING |
| discoverable | **NO on JSON-RPC** — in dispatch map but absent from `_get_tool_schemas()` |
| PM-plane sanctioned | **PARTIALLY** — search is a valid PM operation but the undiscoverable JSON-RPC surface is a dark method pattern |
| reason | `conport_search_content` is callable via JSON-RPC only if the caller knows the exact method name. It does not appear in `tools/list`. |
| decision | Promote to discoverable: add to `_get_tool_schemas()`. Add FastMCP wrapper. Until then, use REST for search. |
| auth_required | No |

---

## Non-dark but infrastructure-only

These are callable on REST but are not PM-plane operations:

| Operation | REST Endpoint | Notes |
|-----------|---------------|-------|
| `health_check` | `GET /health` | Infrastructure health. Not a PM-plane contract operation. |
| `metrics` | `GET /metrics` | Prometheus exporter. Conditional on MONITORING_AVAILABLE. Not a PM-plane contract operation. |

---

## Dark Method Summary

| Name | All surfaces | Discoverable | PM-sanctioned |
|------|-------------|-------------|---------------|
| fork_instance | REST + JSON-RPC + FastMCP | YES | NO |
| promote | REST + JSON-RPC + FastMCP | YES | NO |
| promote_all | REST + JSON-RPC + FastMCP | YES | NO |
| search_content (JSON-RPC) | JSON-RPC only | **NO** | Partially |
