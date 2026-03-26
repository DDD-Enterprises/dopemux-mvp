# ConPort FastMCP Surface Inventory

**Date:** 2026-03-12
**Sources:**
- `docker/mcp-servers-source/conport/server.py` (SSE transport, port 3005)
- `docker/mcp-servers-source/conport/conport_mcp_stdio.py` (stdio transport)
**Transport:** SSE (port 3005) and stdio

## Total FastMCP tools: 13

All tools delegate to REST `/api/*` endpoints internally.

| Tool | Params | Description |
|------|--------|-------------|
| `get_context` | `workspace_id: str` | Get active context for a workspace, including instance-specific data. |
| `update_context` | `workspace_id: str, context_data: dict` | Update active context for a workspace. |
| `log_decision` | `workspace_id: str, topic: str, decision: str, rationale: str, tags: Optional[List[str]] = None` | Log an architectural or technical decision. Wrapper transforms `(topic, decision)` → REST `summary`. |
| `get_decisions` | `workspace_id: Optional[str] = None, limit: int = 10` | Get recent decisions (optionally filter by workspace). |
| `log_progress` | `workspace_id: str, description: str, status: str = "IN_PROGRESS", priority: str = "medium", linked_decision_id: Optional[str] = None` | Log a new progress item or task. |
| `get_progress` | `workspace_id: str, status: Optional[str] = None, limit: int = 20` | Get progress entries for a workspace, optionally filtered by status. |
| `update_progress` | `progress_id: str, updates: dict` | Update an existing progress entry. |
| `get_recent_activity` | `workspace_id: str, hours: int = 24` | Get recent activity to rebuild context. |
| `get_active_work` | `workspace_id: str` | Get currently active work items to maintain focus. |
| `workspace_summary` | `user_id: str` | Get an aggregated summary across all workspaces for a user. |
| `fork_instance` | `workspace_id: str, source_instance: Optional[str] = None, target_instance: Optional[str] = None` | Fork PLANNED/IN_PROGRESS progress from shared/source into target instance. **Dark/admin.** |
| `promote` | `progress_id: str` | Promote a progress entry to shared (clear instance_id). **Dark/admin.** |
| `promote_all` | `workspace_id: str` | Promote all instance-local PLANNED/IN_PROGRESS entries in current instance to shared. **Dark/admin.** |

## Missing from FastMCP (drift gaps)

| Logical Operation | REST Endpoint | Status |
|---|---|---|
| `search_content` | `GET /api/search/{workspace_id}` | Not exposed — no `@mcp.tool()` wrapper in server.py or conport_mcp_stdio.py |
| `save/get/delete custom_data` | `/api/custom_data` | Not exposed — REST-only |
| `unified_search` | `GET /api/unified-search` | Phase 2, not wrapped |
| `workspace_relationships` | `GET /api/workspace-relationships` | Phase 2, not wrapped |

## Discoverable tools at startup
All 13 tools are registered via `@mcp.tool()` and visible in `tools/list` response.
