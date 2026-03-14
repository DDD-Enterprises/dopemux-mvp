# ConPort JSON-RPC Surface Inventory

**Date:** 2026-03-12
**Source:** `docker/mcp-servers-source/conport/enhanced_server.py`
- `mcp_endpoint()` handler (line ~1681)
- `_dispatch_tool()` dispatch map (lines 1736–1750)
- `_get_tool_schemas()` discovery list (lines 1787–1917)
**Endpoint:** `POST /mcp` on port 3004

## Total JSON-RPC methods: 13

Methods dispatch to the REST backend via `_dispatch_tool()`.

| Method | Input Schema Keys | Discoverable via tools/list |
|--------|-------------------|----------------------------|
| `conport_get_context` | workspace_id (req) | ✅ Yes |
| `conport_update_context` | workspace_id (req), + context fields | ✅ Yes |
| `conport_log_decision` | workspace_id (req), summary (req), rationale (req), topic (opt), alternatives (opt), tags (opt), confidence_level (opt), decision_type (opt) | ✅ Yes |
| `conport_get_decisions` | workspace_id (opt), limit (default 10) | ✅ Yes |
| `conport_log_progress` | workspace_id (req), description (req), status (opt, default "IN_PROGRESS"), percentage (opt), priority (opt, default "medium"), estimated_hours (opt), actual_hours (opt), linked_decision_id (opt) | ✅ Yes |
| `conport_get_progress` | workspace_id (req), status (opt), limit (default 20) | ✅ Yes |
| `conport_update_progress` | progress_id (req), status (opt), percentage (opt), description (opt), priority (opt), actual_hours (opt) | ✅ Yes |
| `conport_get_recent_activity` | workspace_id (req), hours (default 24) | ✅ Yes |
| `conport_get_active_work` | workspace_id (req) | ✅ Yes |
| `conport_search_content` | workspace_id (req), q (req), type (opt) | ❌ **NOT discoverable** — in dispatch map but absent from `_get_tool_schemas()` |
| `conport_fork_instance` | workspace_id (req), source_instance (opt), target_instance (opt) | ✅ Yes (dark/admin) |
| `conport_promote` | progress_id (req) | ✅ Yes (dark/admin) |
| `conport_promote_all` | workspace_id (req) | ✅ Yes (dark/admin) |

## Missing from JSON-RPC (drift gaps)

| Logical Operation | FastMCP Tool | REST Endpoint | Gap Type |
|---|---|---|---|
| `workspace_summary` | `workspace_summary` | `GET /api/workspace-summary` | **Not in dispatch map** — method `conport_workspace_summary` is absent from `_dispatch_tool()` (lines 1736-1750) and absent from `_get_tool_schemas()` (lines 1787-1917) |
| `save/get/delete custom_data` | — | `/api/custom_data` | Not exposed — REST-only |
| `unified_search` | — | `GET /api/unified-search` | Phase 2, not wrapped |
| `workspace_relationships` | — | `GET /api/workspace-relationships` | Phase 2, not wrapped |

## Discoverable vs actual capability gap

`tools/list` on JSON-RPC returns 12 discoverable methods (excluding `conport_search_content`).
Actual callable methods include `conport_search_content` — but only if caller knows the method name.
This is the classic "undiscoverable dark method" pattern.
