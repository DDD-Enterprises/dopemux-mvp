# ConPort REST Surface Inventory

**Date:** 2026-03-12
**Source:** `docker/mcp-servers-source/conport/enhanced_server.py` (setup_routes, lines 235–280)
**Port:** 3004

## Total REST operations: 21

### Core PM Operations (9)

| Method | Path | Required Params | Notes |
|--------|------|----------------|-------|
| GET | `/api/context/{workspace_id}` | workspace_id (path) | Returns active_context, focus_state, session fields |
| POST | `/api/context/{workspace_id}` | workspace_id (path) | Accepts active_context, focus_state, session_milestone |
| POST | `/api/decisions` | workspace_id, summary, rationale (body) | tags, alternatives, confidence_level optional |
| GET | `/api/decisions` | — | Query: workspace_id (opt), limit (default 10) |
| POST | `/api/progress` | workspace_id, description (body) | status default "IN_PROGRESS", priority default "medium" |
| GET | `/api/progress` | workspace_id (query, req) | Query: status (opt), limit (default 20) |
| PUT | `/api/progress/{progress_id}` | progress_id (path) | Partial update: status, percentage, description, priority |
| GET | `/api/recent-activity/{workspace_id}` | workspace_id (path) | Query: hours (default 24) |
| GET | `/api/active-work/{workspace_id}` | workspace_id (path) | Returns in-progress work items |

### Search and Discovery (4)

| Method | Path | Required Params | Notes |
|--------|------|----------------|-------|
| GET | `/api/search/{workspace_id}` | workspace_id (path), q (query) | type: decisions/progress/all; FTS + Redis cache |
| GET | `/api/workspace-summary` | user_id (query) | Aggregated across all workspaces (Phase 2) |
| GET | `/api/unified-search` | — | Cross-workspace search (Phase 2, REST-only) |
| GET | `/api/workspace-relationships` | — | Workspace relationship graph (Phase 2, REST-only) |

### Custom Data (3)

| Method | Path | Required Params | Notes |
|--------|------|----------------|-------|
| POST | `/api/custom_data` | workspace_id, category, key, value (body) | Generic KV store |
| GET | `/api/custom_data` | workspace_id (query) | Filter by category, key; REST-only |
| DELETE | `/api/custom_data` | workspace_id (query) | Scoped delete; REST-only |

### Instance Operations / Dark Methods (3)

| Method | Path | Required Params | Notes |
|--------|------|----------------|-------|
| POST | `/api/instance/fork` | workspace_id (body) | Copies PLANNED/IN_PROGRESS across instances |
| POST | `/api/progress/promote` | progress_id (body) | Sets instance_id = NULL |
| POST | `/api/progress/promote_all` | workspace_id (body) | Clears instance_id for all PLANNED/IN_PROGRESS |

### System Endpoints (2)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | `{status, ...metrics}` |
| GET | `/metrics` | Prometheus text/plain; conditional on MONITORING_AVAILABLE |

## Authority note
REST is the canonical backend. FastMCP and JSON-RPC wrappers delegate to these endpoints.
