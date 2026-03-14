# 01 Entity and Persistence Model

## Implemented behavior (repo-local)

### Core workflow entities owned by this repo
- `WorkItem` is the primary workflow object with hierarchical linkage (`parentId`), workflow role (`role`), optional `statusLabel`, rollback role (`previousRole`), priority, complexity, verification flag, depth, metadata/tags, timestamps, and optimistic-lock version. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/WorkItem.kt:7)
- `Role` is a fixed enum (`QUEUE`, `WORK`, `REVIEW`, `BLOCKED`, `TERMINAL`) with progression ordering and threshold comparison logic for dependency gates. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Role.kt:8, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Role.kt:19, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Role.kt:26)
- `Note` is a keyed, role-scoped artifact attached to a `WorkItem`, unique by `(itemId,key)`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Note.kt:13, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Note.kt:11)
- `Dependency` is a directed edge between `WorkItem`s with type and optional `unblockAt` threshold. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Dependency.kt:13)
- `RoleTransition` is the transition audit record for role changes (`fromRole`, `toRole`, trigger, summary, timestamp). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/RoleTransition.kt:10)
- `NoteSchemaEntry` is config-derived gating metadata (not DB persisted) used at transition/gate time. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/NoteSchemaEntry.kt:34)

### Persisted state and schema
- Persisted tables: `work_items`, `notes`, `dependencies`, `role_transitions` (migration and Exposed schema align). (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:5, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:34, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:49, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:64, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/WorkItemsTable.kt:6, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/NotesTable.kt:7, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/DependenciesTable.kt:7, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/RoleTransitionsTable.kt:7)
- Role and dependency-type constraints are DB-enforced via `CHECK` constraints in migrations. (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:11, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:53)
- `notes` and `dependencies` are referentially tied to `work_items` with cascade delete. (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:36, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:51, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:52)
- `work_items` persistence includes optimistic locking (`version`) and role-change timestamp (`role_changed_at`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/WorkItemsTable.kt:22, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/WorkItemsTable.kt:23)

### Relationships
- Hierarchy is self-referential on `work_items.parent_id -> work_items.id`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/WorkItemsTable.kt:26)
- Notes are per-item artifacts with unique key per item. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/NotesTable.kt:16, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/NotesTable.kt:17)
- Dependencies are directional links across items with uniqueness on `(from_item_id,to_item_id,type)`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/DependenciesTable.kt:15, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/DependenciesTable.kt:17)
- Role transitions are many-to-one history entries per item. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/RoleTransitionsTable.kt:18)

### Writers/readers by repository and tool layer
- Repository interfaces define read/write ownership over each entity type (`WorkItemRepository`, `NoteRepository`, `DependencyRepository`, `RoleTransitionRepository`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/WorkItemRepository.kt:9, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/NoteRepository.kt:6, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/DependencyRepository.kt:10, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/RoleTransitionRepository.kt:7)
- Registered MCP write tools: `manage_items`, `manage_notes`, `manage_dependencies`, `advance_item`, `complete_tree`, `create_work_tree`; read tools include `query_*`, `get_*`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:89, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:99, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:104)
- Tool context exposes repository/service access paths used by all tools. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/ToolExecutionContext.kt:29, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/ToolExecutionContext.kt:38, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/ToolExecutionContext.kt:44)

## Documented intent (secondary)
- API docs describe a unified WorkItem graph with notes, dependencies, and role-based workflow. (current/docs/api-reference.md:5)

## Inferred capability (explicitly inferred)
- Because all 13 tools are MCP-registered and transport-selectable (`stdio`/`http`), this repo is intended to be the operational PM state authority for clients that use those tools. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:89, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:115)
