# Executive Summary

## Repository
| Field                | Value                                                                 |
| -------------------- | --------------------------------------------------------------------- |
| **Name**             | task-orchestrator                                                     |
| **URL**              | https://github.com/jpicklyk/task-orchestrator                         |
| **Ref**              | `99023a9740e3ea310c31c5e80991670aa010fb2f` (HEAD-at-time-of-analysis) |
| **Version**          | 2.2.0                                                                 |
| **License**          | MIT                                                                   |
| **Primary Language** | Kotlin 2.2.0                                                          |
| **Runtime**          | JVM 21                                                                |
| **Transport**        | MCP (stdio, HTTP/SSE via Ktor CIO)                                    |
| **Persistence**      | SQLite (Exposed ORM, Flyway migrations)                               |

## What It Is

An MCP server that provides AI coding assistants with a **persistent work-item graph** for hierarchical task management. Items flow through `queue → work → review → terminal` with server-enforced dependency gates, optional note-schema gates, and audit-trail transitions. The server blocks progression until prerequisites are satisfied, independent of prompt discipline.

## What It Does (from code, 13 MCP tools)

| Category     | Tools                                                                                  | Purpose                                                                                                                 |
| ------------ | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Item CRUD    | `manage_items`, `query_items`                                                          | Create/update/delete/search/overview WorkItems with hierarchy (max depth 3)                                             |
| Notes        | `manage_notes`, `query_notes`                                                          | Upsert/delete/query keyed text Notes attached to WorkItems                                                              |
| Dependencies | `manage_dependencies`, `query_dependencies`                                            | Directed BLOCKS/IS_BLOCKED_BY/RELATES_TO edges with pattern shortcuts (linear, fan-out, fan-in) and BFS graph traversal |
| Workflow     | `advance_item`, `get_next_status`, `get_next_item`, `get_blocked_items`, `get_context` | Trigger-based transitions, gate enforcement, cascade detection, priority-ranked recommendations                         |
| Compound     | `create_work_tree`, `complete_tree`                                                    | Atomic batch creation (items+deps+notes) and batch completion with topological ordering                                 |

## Key Architecture Decisions (code-verified)

1. **Single unified entity**: Everything is a `WorkItem`. No separate Project/Feature/Task types. Hierarchy via `parentId` + computed `depth` (0–3).
2. **Roles, not statuses**: 5 fixed roles (QUEUE, WORK, REVIEW, BLOCKED, TERMINAL). `statusLabel` is a display-only annotation.
3. **Trigger-based transitions**: Named triggers (`start`, `complete`, `block`, `hold`, `resume`, `cancel`) map deterministically to target roles via `RoleTransitionHandler` (3-phase: resolve → validate → apply).
4. **Dependency gating**: Forward transitions check all incoming BLOCKS/IS_BLOCKED_BY edges against `unblockAt` thresholds. BLOCKED transitions always pass.
5. **Note schema gates**: Optional YAML config (`.taskorchestrator/config.yaml`) defines per-tag note requirements. Required notes must exist before `advance_item` allows progression.
6. **Cascade detection**: Completion of all siblings auto-advances parent to TERMINAL. Starting a child auto-advances QUEUE parent to WORK. Unblock detection reports newly-unblocked downstream items.
7. **Clean Architecture**: Domain → Application → Infrastructure → Interface. Domain has zero outward dependencies.

## Integration Decision Matrix

| Use Case            | Verdict | Evidence                                                                                |
| ------------------- | ------- | --------------------------------------------------------------------------------------- |
| MCP routing         | ✅ Ready | 13 tools with stable names, `ToolAnnotations` with read/write/destructive hints         |
| Workflow extraction | ✅ Ready | Complete state machine in `RoleTransitionHandler`, deterministic transition table       |
| Data model mapping  | ✅ Ready | 4 SQLite tables, 2 Flyway migrations, full schema in code                               |
| Contract gates      | ✅ Ready | JSON Schema per tool via `parameterSchema`, response envelope (`{success, data/error}`) |
| Operational runbook | ✅ Ready | Docker images, 6 env vars, volume mounts, graceful shutdown                             |
| Plugin ecosystem    | ✅ Ready | Claude Code plugin with 7 skills + 3 hooks + output style                               |
