# ConPort MCP Server Surface Inventory

**Date:** 2026-03-12
**Status:** Hardened
**Canonical Authority:** see `docs/90-adr/adr-conport-as-decision-progress-and-context-authority.md`

## Overview
This document specifies the MCP tool surface exposed by the ConPort MCP server (`server.py` and `conport_mcp_stdio.py`). All tools here act as thin, un-opinionated proxies to the underlying ConPort PM-plane REST API running on port 3004.

## Callable-Surface Inventory
The following 13 tools are currently exposed:

### Progress
| MCP Tool | Expected Arguments | Underlying REST API | Description |
|---|---|---|---|
| `get_progress` | `workspace_id` (str), `status` (opt str), `limit` (int) | `GET /api/progress` | Get progress entries for a workspace. |
| `log_progress` | `workspace_id` (str), `description` (str), `status` (str), `priority` (str), `linked_decision_id` (opt str) | `POST /api/progress` | Log a new progress item. |
| `update_progress`| `progress_id` (str), `updates` (dict) | `PUT /api/progress/{progress_id}` | Update existing progress fields. |

### Decisions
| MCP Tool | Expected Arguments | Underlying REST API | Description |
|---|---|---|---|
| `get_decisions` | `workspace_id` (opt str), `limit` (int) | `GET /api/decisions` | Get recent durable decisions. |
| `log_decision` | `workspace_id` (str), `topic` (str), `decision` (str), `rationale` (str), `tags` (opt list) | `POST /api/decisions` | Log an architectural/technical decision. |

### Context & Activity
| MCP Tool | Expected Arguments | Underlying REST API | Description |
|---|---|---|---|
| `get_context` | `workspace_id` (str) | `GET /api/context/{workspace_id}` | Get active workspace context. |
| `update_context`| `workspace_id` (str), `context_data` (dict) | `POST /api/context/{workspace_id}` | Update active workspace context. |
| `get_recent_activity` | `workspace_id` (str), `hours` (int) | `GET /api/recent-activity/{workspace_id}` | Get recent graph events. |
| `get_active_work` | `workspace_id` (str) | `GET /api/active-work/{workspace_id}` | Get active work items for context. |
| `workspace_summary` | `user_id` (str) | `GET /api/workspace-summary` | Aggregated user summary. |

### Instance Management (Multi-Instance Worktrees)
| MCP Tool | Expected Arguments | Underlying REST API | Description |
|---|---|---|---|
| `fork_instance` | `workspace_id` (str), `source_instance` (opt), `target_instance` (opt) | `POST /api/instance/fork` | Fork progress entries to a new instance. |
| `promote` | `progress_id` (str) | `POST /api/progress/promote` | Promote a progress entry to shared memory. |
| `promote_all` | `workspace_id` (str) | `POST /api/progress/promote_all` | Promote all PLANNED/IN_PROGRESS. |

## Equivalence and PM-Plane REST Integration
All MCP tools here enforce a 1:1 functional equivalence to the PM-plane REST API (`http://localhost:3004`). 

The REST API is the **preferred integration surface** for any service/agent acting as a part of the PM plane (e.g., `dopecon-bridge`). The MCP MCP server remains as a developer ergonomics and fast-iteration surface for direct conversational consumption but **does not bypass** the canonical REST endpoints.

## Alignment & Drift Check (TP5)
As of 2026-03-12 (TP5 hardening), the local MCP surfaces in this folder have been validated to contain no operational drift from the canonical REST API structure. They purely pass-through inputs without silently mutating authority bounds.
