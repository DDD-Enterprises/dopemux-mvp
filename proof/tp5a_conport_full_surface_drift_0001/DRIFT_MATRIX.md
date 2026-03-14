# ConPort Drift Matrix

**Date:** 2026-03-12
**Total drift cases identified: 6**

## Drift Cases

### Drift 1: workspace_summary missing from JSON-RPC dispatch

| Field | Value |
|-------|-------|
| logical_operation | `workspace_summary` |
| drift_type | missing_surface |
| affected_surface | JSON-RPC |
| evidence | `_dispatch_tool()` (enhanced_server.py:1736–1750) has no entry for `conport_workspace_summary`. `_get_tool_schemas()` (lines 1787–1917) has no schema for it. REST and FastMCP expose it fully. |
| impact | Agents using JSON-RPC cannot call workspace_summary. Silent failure or method-not-found error. |
| notes | Fix: add `conport_workspace_summary` to both dispatch map and schema list. **Do not choose JSON-RPC as canonical surface until this is closed.** |

### Drift 2: search_content not discoverable on JSON-RPC

| Field | Value |
|-------|-------|
| logical_operation | `search_content` |
| drift_type | discoverability_drift |
| affected_surface | JSON-RPC |
| evidence | `conport_search_content` exists in `_dispatch_tool()` (enhanced_server.py:1738) but is absent from `_get_tool_schemas()` discovery list (lines 1787–1917). `tools/list` does not return it. |
| impact | JSON-RPC clients cannot discover search_content via standard protocol introspection. Must know method name out-of-band. Effectively a dark method on JSON-RPC. |
| notes | Fix: add schema to `_get_tool_schemas()`. Or treat as dark/admin and document explicitly. |

### Drift 3: search_content missing from FastMCP entirely

| Field | Value |
|-------|-------|
| logical_operation | `search_content` |
| drift_type | missing_surface |
| affected_surface | FastMCP |
| evidence | Neither `server.py` nor `conport_mcp_stdio.py` defines a `@mcp.tool()` wrapper for search. REST exposes `GET /api/search/{workspace_id}`. JSON-RPC has it (undiscoverable). |
| impact | Agent-facing FastMCP surface cannot invoke search. Agents must fall back to REST or JSON-RPC by name. |
| notes | Fix: add `@mcp.tool() search_content` wrapper that delegates to `GET /api/search/{workspace_id}`. |

### Drift 4: custom_data REST-only across all wrapper surfaces

| Field | Value |
|-------|-------|
| logical_operation | `save_custom_data`, `get_custom_data`, `delete_custom_data` |
| drift_type | missing_surface |
| affected_surface | JSON-RPC, FastMCP |
| evidence | `POST/GET/DELETE /api/custom_data` exists in REST (setup_routes). No JSON-RPC entry in dispatch map. No FastMCP `@mcp.tool()` wrapper. |
| impact | Agents cannot use generic KV store via MCP. Must call REST directly. |
| notes | Low urgency — custom_data not yet sanctioned as PM-plane operation. Document as REST-only until PM scope is defined. |

### Drift 5: Phase 2 operations (unified_search, workspace_relationships) REST-only

| Field | Value |
|-------|-------|
| logical_operation | `unified_search`, `workspace_relationships` |
| drift_type | missing_surface |
| affected_surface | JSON-RPC, FastMCP |
| evidence | `GET /api/unified-search` and `GET /api/workspace-relationships` exist in REST implementation (enhanced_server.py:2063+). No wrappers on any other surface. |
| impact | Phase 2 features inaccessible to agents using MCP. |
| notes | Expected — Phase 2 features are not yet hardened. Add wrappers post-stabilization. |

### Drift 6: No auth gate on any callable surface

| Field | Value |
|-------|-------|
| logical_operation | all |
| drift_type | security_gap |
| affected_surface | REST, JSON-RPC, FastMCP |
| evidence | `enhanced_server.py`, `server.py`, `conport_mcp_stdio.py` — no authentication/authorization middleware applied to any route handler. ConPort assumes PM-plane boundary enforcement is external. |
| impact | Any caller that can reach ConPort's network surface can read or write all workspaces. |
| notes | Known architectural assumption. PM-plane adapters are responsible for auth boundary. Document as operational hardening gap. Fix requires adding auth middleware at REST handler entry points. |

## Previously-Repaired Drift (Closed)

| Drift | Was | Now | Source |
|-------|-----|-----|--------|
| `log_decision` topic/decision → summary mismatch | FastMCP sent `(topic, decision)` separately; REST expected `summary` field | Repaired: FastMCP wrapper transforms `summary = f"[{topic}] {decision}"` before POST | enhanced_server.py + server.py |
| `log_progress` default status PLANNED vs IN_PROGRESS | Older FastMCP defaulted to `PLANNED`; REST defaulted to `IN_PROGRESS` | Repaired: all surfaces default to `IN_PROGRESS` | enhanced_server.py + server.py |

## Drift Summary

| Category | Count |
|----------|-------|
| missing_surface | 4 |
| discoverability_drift | 1 |
| security_gap | 1 |
| **Total open drift cases** | **6** |
| Closed/repaired | 2 |
