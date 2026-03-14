# APPENDICES.md

## Appendix A: Full Tool Name Listing

### v2 (clockwork, default docker-compose deployment target)
Source evidence: `grep -rn "override val name: String"` on clockwork module.

| #   | Tool Name                | Class                      | Category              | Read/Write |
| --- | ------------------------ | -------------------------- | --------------------- | ---------- |
| 1   | `query_container`        | `QueryContainerTool`       | TASK_MANAGEMENT       | Read       |
| 2   | `manage_container`       | `ManageContainerTool`      | TASK_MANAGEMENT       | Write      |
| 3   | `query_sections`         | `QuerySectionsTool`        | SECTION_MANAGEMENT    | Read       |
| 4   | `manage_sections`        | `ManageSectionsTool`       | SECTION_MANAGEMENT    | Write      |
| 5   | `query_templates`        | `QueryTemplatesTool`       | TEMPLATE_MANAGEMENT   | Read       |
| 6   | `manage_template`        | `ManageTemplateTool`       | TEMPLATE_MANAGEMENT   | Write      |
| 7   | `apply_template`         | `ApplyTemplateTool`        | TEMPLATE_MANAGEMENT   | Write      |
| 8   | `query_dependencies`     | `QueryDependenciesTool`    | DEPENDENCY_MANAGEMENT | Read       |
| 9   | `manage_dependencies`    | `ManageDependenciesTool`   | DEPENDENCY_MANAGEMENT | Write      |
| 10  | `get_next_task`          | `GetNextTaskTool`          | TASK_MANAGEMENT       | Read       |
| 11  | `get_blocked_tasks`      | `GetBlockedTasksTool`      | TASK_MANAGEMENT       | Read       |
| 12  | `get_next_status`        | `GetNextStatusTool`        | SYSTEM                | Read       |
| 13  | `request_transition`     | `RequestTransitionTool`    | SYSTEM                | Write      |
| 14  | `query_role_transitions` | `QueryRoleTransitionsTool` | SYSTEM                | Read       |

### v3 (current, requires `--profile current` in docker-compose)
Source evidence: direct grep on `current/` module source files.

| #   | Tool Name             | Class                    | Category | Read/Write |
| --- | --------------------- | ------------------------ | -------- | ---------- |
| 1   | `query_items`         | `QueryItemsTool`         | UNKNOWN  | Read       |
| 2   | `manage_items`        | `ManageItemsTool`        | UNKNOWN  | Write      |
| 3   | `query_notes`         | `QueryNotesTool`         | UNKNOWN  | Read       |
| 4   | `manage_notes`        | `ManageNotesTool`        | UNKNOWN  | Write      |
| 5   | `query_dependencies`  | `QueryDependenciesTool`  | UNKNOWN  | Read       |
| 6   | `manage_dependencies` | `ManageDependenciesTool` | UNKNOWN  | Write      |
| 7   | `get_next_item`       | `GetNextItemTool`        | UNKNOWN  | Read       |
| 8   | `get_blocked_items`   | `GetBlockedItemsTool`    | UNKNOWN  | Read       |
| 9   | `get_next_status`     | `GetNextStatusTool`      | UNKNOWN  | Read       |
| 10  | `advance_item`        | `AdvanceItemTool`        | UNKNOWN  | Write      |
| 11  | `get_context`         | `GetContextTool`         | UNKNOWN  | Read       |
| 12  | `create_work_tree`    | `CreateWorkTreeTool`     | UNKNOWN  | Write      |
| 13  | `complete_tree`       | `CompleteTreeTool`       | UNKNOWN  | Write      |

---

## Appendix B: Enum Value Reference

All values are exact Kotlin enum names as stored in database and returned in API responses.

### TaskStatus
`PENDING`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `DEFERRED`, `BACKLOG`, `IN_REVIEW`, `CHANGES_REQUESTED`, `ON_HOLD`, `TESTING`, `READY_FOR_QA`, `INVESTIGATING`, `BLOCKED`, `DEPLOYED`

Input normalization: hyphens replaced with underscores, then `valueOf()`. Additional aliases: `INPROGRESS→IN_PROGRESS`, `INREVIEW→IN_REVIEW`, `CHANGESREQUESTED→CHANGES_REQUESTED`, `ONHOLD→ON_HOLD`, `READYFORQA→READY_FOR_QA`, `CANCELED→CANCELLED`.

### FeatureStatus
`PLANNING`, `IN_DEVELOPMENT`, `COMPLETED`, `ARCHIVED`, `DRAFT`, `ON_HOLD`, `TESTING`, `VALIDATING`, `PENDING_REVIEW`, `BLOCKED`, `DEPLOYED`

### ProjectStatus
`PLANNING`, `IN_DEVELOPMENT`, `COMPLETED`, `ARCHIVED`, `ON_HOLD`, `DEPLOYED`, `CANCELLED`

### Priority
`HIGH`, `MEDIUM`, `LOW`

### DependencyType
`BLOCKS`, `IS_BLOCKED_BY`, `RELATES_TO`

### ContentFormat
`PLAIN_TEXT`, `MARKDOWN`, `JSON`, `CODE`

### EntityType
`PROJECT`, `FEATURE`, `TASK`, `TEMPLATE`, `SECTION`

---

## Appendix C: Database Tables

Source evidence: Exposed ORM table definition files.

| Table              | PK                    | Notable Columns                                                                                                         |
| ------------------ | --------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `tasks`            | `id` (UUID)           | project_id, feature_id, title, status, priority, complexity, version, lock_status, requires_verification, search_vector |
| `sections`         | `id` (UUID)           | entity_type, entity_id, ordinal (unique per entity), tags (comma-sep TEXT)                                              |
| `dependencies`     | `id` (UUID)           | from_task_id, to_task_id, type, unblock_at; unique_(from, to, type)                                                     |
| `projects`         | `id` (UUID, inferred) | name, status, description, summary, version                                                                             |
| `features`         | `id` (UUID, inferred) | project_id, name, status, priority, requires_verification, version                                                      |
| `templates`        | `id` (UUID, inferred) | name, target_entity_type, is_built_in, is_protected, is_enabled                                                         |
| `entity_tags`      | composite             | Normalized tags table for projects/features/tasks                                                                       |
| `task_locks`       | UNKNOWN               | Referenced by locking system                                                                                            |
| `role_transitions` | UNKNOWN               | Referenced by request_transition/query_role_transitions                                                                 |
| `work_sessions`    | UNKNOWN               | Referenced by session management                                                                                        |

---

## Appendix D: Error Code Reference

Source: `ErrorCodes.kt` (clockwork) and `ErrorCodes.kt` (current)

| Code                 | HTTP Analogue | Meaning                     |
| -------------------- | ------------- | --------------------------- |
| `VALIDATION_ERROR`   | 400           | Invalid request parameters  |
| `RESOURCE_NOT_FOUND` | 404           | Entity not found            |
| `DATABASE_ERROR`     | 500           | Persistence layer failure   |
| `INTERNAL_ERROR`     | 500           | Unexpected server error     |
| `DUPLICATE_RESOURCE` | 409           | Unique constraint violation |

---

## Appendix E: Files NOT Inspected (Extraction Gaps)

These files were identified but not read during extraction. They represent known unknowns:

1. `clockwork/.../template/ManageTemplateTool.kt` — Full schema
2. `clockwork/.../template/ApplyTemplateTool.kt` — Full schema
3. `clockwork/.../dependency/QueryDependenciesTool.kt` — Full schema
4. `clockwork/.../dependency/ManageDependenciesTool.kt` — Full schema
5. `clockwork/.../task/GetNextTaskTool.kt` — Full schema
6. `clockwork/.../task/GetBlockedTasksTool.kt` — Full schema
7. `clockwork/.../status/GetNextStatusTool.kt` — Full schema
8. `clockwork/.../status/RequestTransitionTool.kt` — Full schema
9. `clockwork/.../status/QueryRoleTransitionsTool.kt` — Full schema
10. `clockwork/.../infrastructure/database/schema/FeaturesTable.kt`
11. `clockwork/.../infrastructure/database/schema/ProjectsTable.kt`
12. `clockwork/.../infrastructure/database/schema/TemplatesTable.kt`
13. `clockwork/.../infrastructure/database/migration/` — All migration files
14. `clockwork/.../domain/service/StatusValidator.kt` — Exact validation logic
15. `clockwork/.../domain/service/VerificationGateService.kt`
16. `clockwork/.../domain/service/CascadeServiceImpl.kt`
17. `current/src/main/kotlin/.../interfaces/mcp/CurrentMcpServer.kt` — v3 registration details
18. All `current/` domain model files
19. All `current/` tool implementation files (schemas UNKNOWN)
