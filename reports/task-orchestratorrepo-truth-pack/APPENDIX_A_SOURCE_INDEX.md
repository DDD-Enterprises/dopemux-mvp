# APPENDIX A — SOURCE INDEX

## Repository
- **URL**: https://github.com/jpicklyk/task-orchestrator
- **Ref**: `99023a9740e3ea310c31c5e80991670aa010fb2f` (HEAD-at-time-of-analysis)
- **Branch**: `main`
- **Version**: 2.2.0 (from `version.properties`)
- **Tags**: v2.2.0, v2.1.0, v2.0.3, v2.0.2, v2.0.1, v1.1.0-beta-01, v1.0.1, v1.0.0

## Module Structure

| Module       | Status     | Description                            |
| ------------ | ---------- | -------------------------------------- |
| `:current`   | **Active** | v3 MCP Task Orchestrator               |
| `:clockwork` | Deprecated | v2 (archived, not built by default CI) |

## Source File Index (`:current` module)

### Entry Point
| File             | Lines | Purpose                                                         |
| ---------------- | ----- | --------------------------------------------------------------- |
| `CurrentMain.kt` | 63    | JVM main(), creates `CurrentMcpServer`, installs shutdown hooks |

### MCP Interface Layer (`interfaces/mcp/`)
| File                  | Lines | Purpose                                                                                 |
| --------------------- | ----- | --------------------------------------------------------------------------------------- |
| `CurrentMcpServer.kt` | 224   | **Authoritative tool registration (L89-108)**, transport dispatch (stdio/HTTP), DB init |
| `McpToolAdapter.kt`   | 137   | Bridges `ToolDefinition` → MCP SDK `Server.addTool()`, boolean preprocessing            |

### Tool Framework (`application/tools/`)
| File                      | Lines | Purpose                                                                                                |
| ------------------------- | ----- | ------------------------------------------------------------------------------------------------------ |
| `ToolDefinition.kt`       | 125   | Interface: name, description, parameterSchema, execute, validateParams, userSummary                    |
| `BaseToolDefinition.kt`   | 385   | Abstract base: param extractors (requireString, optionalBoolean, extractUUID, etc.), response envelope |
| `ToolExecutionContext.kt` | —     | Access to repositories + NoteSchemaService                                                             |
| `ErrorCodes.kt`           | —     | Error code constants                                                                                   |
| `ResponseUtil.kt`         | —     | Response envelope helpers                                                                              |

### Tool Implementations (13 tools)

| #   | Tool Name (code)      | File                                   | Lines | Category              | Operations                                         |
| --- | --------------------- | -------------------------------------- | ----- | --------------------- | -------------------------------------------------- |
| 1   | `manage_items`        | `items/ManageItemsTool.kt`             | 704   | ITEM_MANAGEMENT       | create, update, delete                             |
| 2   | `query_items`         | `items/QueryItemsTool.kt`              | 512   | ITEM_MANAGEMENT       | get, search, overview                              |
| 3   | `manage_notes`        | `notes/ManageNotesTool.kt`             | 347   | NOTE_MANAGEMENT       | upsert, delete                                     |
| 4   | `query_notes`         | `notes/QueryNotesTool.kt`              | 188   | NOTE_MANAGEMENT       | get, list                                          |
| 5   | `manage_dependencies` | `dependency/ManageDependenciesTool.kt` | 508   | DEPENDENCY_MANAGEMENT | create, delete (patterns: linear, fan-out, fan-in) |
| 6   | `query_dependencies`  | `dependency/QueryDependenciesTool.kt`  | 344   | DEPENDENCY_MANAGEMENT | query (BFS graph traversal, topo sort)             |
| 7   | `advance_item`        | `workflow/AdvanceItemTool.kt`          | 449   | WORKFLOW              | Trigger-based transitions with gates + cascades    |
| 8   | `get_next_status`     | `workflow/GetNextStatusTool.kt`        | 154   | WORKFLOW              | Read-only progression recommendation               |
| 9   | `get_next_item`       | `workflow/GetNextItemTool.kt`          | 227   | WORKFLOW              | Priority-ranked next actionable item               |
| 10  | `get_blocked_items`   | `workflow/GetBlockedItemsTool.kt`      | 312   | WORKFLOW              | All items blocked by deps or explicit block        |
| 11  | `get_context`         | `workflow/GetContextTool.kt`           | 425   | WORKFLOW              | Item gate check, session resume, health check      |
| 12  | `complete_tree`       | `compound/CompleteTreeTool.kt`         | 489   | WORKFLOW              | Batch complete/cancel in topological order         |
| 13  | `create_work_tree`    | `compound/CreateWorkTreeTool.kt`       | 471   | ITEM_MANAGEMENT       | Atomic tree creation (items + deps + notes)        |

### Domain Models (`domain/model/`)
| File                 | Lines | Purpose                                                                 |
| -------------------- | ----- | ----------------------------------------------------------------------- |
| `WorkItem.kt`        | 76    | Core entity: 18 fields, parentId hierarchy, tag validation              |
| `Note.kt`            | 35    | Accountability artifact: (itemId, key) unique, role-scoped              |
| `Dependency.kt`      | 48    | Directed edge: (fromItemId, toItemId, type) unique, unblockAt threshold |
| `RoleTransition.kt`  | 25    | Audit trail: fromRole, toRole, trigger, summary                         |
| `Role.kt`            | 35    | Enum: QUEUE, WORK, REVIEW, BLOCKED, TERMINAL                            |
| `Priority.kt`        | 10    | Enum: HIGH, MEDIUM, LOW                                                 |
| `DependencyType.kt`  | 13    | Enum: BLOCKS, IS_BLOCKED_BY, RELATES_TO                                 |
| `NoteSchemaEntry.kt` | 41    | Schema entry: key, role, required, description, guidance                |

### Domain Repositories (`domain/repository/`)
| File                          | Purpose                                  |
| ----------------------------- | ---------------------------------------- |
| `WorkItemRepository.kt`       | CRUD + hierarchy queries + filters       |
| `NoteRepository.kt`           | CRUD + findByItemId                      |
| `DependencyRepository.kt`     | CRUD + findByToItemId/fromItemId + batch |
| `RoleTransitionRepository.kt` | create + findByItemId                    |
| `Result.kt`                   | Result\<T\> sealed class (Success/Error) |

### Application Services (`application/service/`)
| File                       | Lines | Purpose                                                             |
| -------------------------- | ----- | ------------------------------------------------------------------- |
| `RoleTransitionHandler.kt` | 373   | 3-phase: resolve (pure) → validate (deps) → apply (persist + audit) |
| `NoteSchemaService.kt`     | 38    | Interface: getSchemaForTags, hasReviewPhase + NoOp impl             |
| `CascadeDetector.kt`       | 243   | Parent completion cascades + unblock detection                      |
| `WorkTreeExecutor.kt`      | 41    | Interface + DTOs for atomic tree creation                           |

### Infrastructure — Database
| File                                               | Lines | Purpose                                                                                                         |
| -------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------- |
| `DatabaseConfig.kt`                                | 53    | 6 env vars: DATABASE_PATH, USE_FLYWAY, LOG_LEVEL, AGENT_CONFIG_DIR, DATABASE_MAX_CONNECTIONS, DATABASE_SHOW_SQL |
| `DatabaseManager.kt`                               | 204   | SQLite init, WAL mode, foreign keys, busy_timeout, cycle integrity check                                        |
| `schema/WorkItemsTable.kt`                         | 34    | Exposed ORM table definition                                                                                    |
| `schema/NotesTable.kt`                             | —     | Exposed ORM table                                                                                               |
| `schema/DependenciesTable.kt`                      | —     | Exposed ORM table                                                                                               |
| `schema/RoleTransitionsTable.kt`                   | —     | Exposed ORM table                                                                                               |
| `schema/management/DatabaseSchemaManager.kt`       | —     | Interface                                                                                                       |
| `schema/management/FlywayDatabaseSchemaManager.kt` | —     | Flyway implementation                                                                                           |
| `schema/management/DirectDatabaseSchemaManager.kt` | —     | Direct SQL fallback                                                                                             |
| `schema/management/SchemaManagerFactory.kt`        | —     | Factory: useFlyway toggle                                                                                       |

### Infrastructure — Repository
| File                                | Purpose                                    |
| ----------------------------------- | ------------------------------------------ |
| `RepositoryProvider.kt`             | DI interface: all repos + workTreeExecutor |
| `DefaultRepositoryProvider.kt`      | Default wiring                             |
| `SQLiteWorkItemRepository.kt`       | Exposed-based WorkItem persistence         |
| `SQLiteNoteRepository.kt`           | Exposed-based Note persistence             |
| `SQLiteDependencyRepository.kt`     | Exposed-based Dependency persistence       |
| `SQLiteRoleTransitionRepository.kt` | Exposed-based RoleTransition persistence   |

### Infrastructure — Other
| File                               | Purpose                                             |
| ---------------------------------- | --------------------------------------------------- |
| `config/YamlNoteSchemaService.kt`  | Loads `.taskorchestrator/config.yaml` via SnakeYAML |
| `service/SQLiteWorkTreeService.kt` | Atomic tree creation with rollback                  |
| `shutdown/ShutdownCoordinator.kt`  | Graceful shutdown coordination                      |
| `shutdown/SignalHandler.kt`        | OS signal handling (SIGTERM, SIGINT)                |

### Flyway Migrations
| File                              | Purpose                                                     |
| --------------------------------- | ----------------------------------------------------------- |
| `V1__Current_Initial_Schema.sql`  | 4 tables: work_items, notes, dependencies, role_transitions |
| `V2__Work_Item_Field_Updates.sql` | complexity nullable, add requires_verification              |

### Test Files (35 total)
| Category             | Count | Files                                                                                                 |
| -------------------- | ----- | ----------------------------------------------------------------------------------------------------- |
| Service tests        | 4     | CascadeDetectorTest, NoteSchemaServiceTest, RoleTransitionHandlerTest, WorkTreeServiceIntegrationTest |
| Tool tests           | 14    | One per tool + SchemaGatedLifecycleTest + WorkflowIntegrationTest                                     |
| Domain model tests   | 5     | DependencyTest, NoteTest, RoleTest, RoleTransitionTest, WorkItemTest                                  |
| Repository tests     | 7     | One per repo + FilterTest + AncestorCycleTest + GraphTest                                             |
| Infrastructure tests | 2     | YamlNoteSchemaServiceTest, ResultTest                                                                 |
| Adapter tests        | 2     | BaseToolDefinitionTest, ResponseUtilTest                                                              |

### Docs
| File                             | Size    | Purpose                                       |
| -------------------------------- | ------- | --------------------------------------------- |
| `current/docs/api-reference.md`  | 33.9 KB | Full API reference for all 13 tools           |
| `current/docs/workflow-guide.md` | 27.2 KB | Workflow, schemas, gates, dependency patterns |
| `current/docs/quick-start.md`    | 13.7 KB | Setup walkthrough                             |
| `current/docs/Home.md`           | 2.3 KB  | Wiki landing page                             |
| `current/docs/_Sidebar.md`       | 0.4 KB  | Wiki sidebar                                  |

### Build / Config
| File                       | Purpose                                                   |
| -------------------------- | --------------------------------------------------------- |
| `settings.gradle.kts`      | Module includes: :current, :clockwork                     |
| `build.gradle.kts` (root)  | Group, plugins                                            |
| `current/build.gradle.kts` | Dependencies, main class, JVM 21 toolchain, fat JAR       |
| `version.properties`       | 2.2.0                                                     |
| `gradle.properties`        | JVM args, Dokka                                           |
| `Dockerfile`               | Multi-stage: builder (temurin:23) → runtime (corretto:25) |
| `docker-compose.yml`       | 3 services: v2-stdio, v3-stdio, v3-http                   |
| `CHANGELOG.md`             | Release history                                           |
| `CONTRIBUTING.md`          | Dev setup                                                 |
| `CLAUDE.md`                | Claude Code project context                               |
