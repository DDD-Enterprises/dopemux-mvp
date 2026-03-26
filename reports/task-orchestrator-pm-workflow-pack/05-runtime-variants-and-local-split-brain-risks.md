# 05 Runtime Variants and Local Split-Brain Risks

## Variant inventory and risk analysis

### 1) Parallel modules in same repo (`current` v3 + `clockwork` v2)
- **Pattern:** parallel implementations included in build graph.
- **Systems/components involved:** Gradle includes both modules; v2 marked deprecated but still buildable/runnable.
- **Why risk:** operators can run different PM legality models from same repo checkout.
- **Evidence:** `:current` and `:clockwork` both included. (settings.gradle.kts:7, settings.gradle.kts:11)
- **Evidence:** clockwork explicitly deprecated but still documented runnable. (clockwork/DEPRECATED.md:3, clockwork/DEPRECATED.md:41)

### 2) Multi-runtime container targets (`runtime-v2` and `runtime-current`)
- **Pattern:** two runtime images defined in one Dockerfile.
- **Systems/components involved:** `runtime-v2` target (clockwork jar) and `runtime-current` target (current jar).
- **Why risk:** deployment tooling can accidentally ship/run v2 instead of v3, creating behavioral divergence.
- **Evidence:** Docker targets for both versions. (Dockerfile:82, Dockerfile:89)

### 3) Compose profiles expose both v2 and v3 services
- **Pattern:** local orchestration includes a v2 service and two v3 services.
- **Systems/components involved:** `mcp-task-orchestrator` (v2), `mcp-task-orchestrator-current`, `...-current-http`.
- **Why risk:** concurrent local services with similar naming can create endpoint/authority confusion.
- **Evidence:** v2 uses `runtime-v2`; v3 uses `runtime-current`; both defined in same compose file. (docker-compose.yml:2, docker-compose.yml:5, docker-compose.yml:36, docker-compose.yml:68)

### 4) Schema management mode variants (Flyway vs Direct)
- **Pattern:** runtime-selected schema manager implementation.
- **Systems/components involved:** `SchemaManagerFactory` chooses `FlywayDatabaseSchemaManager` or `DirectDatabaseSchemaManager` from env/runtime state.
- **Why risk:** different environments may enforce schema via migrations vs direct table-create ordering; behavior can diverge subtly.
- **Evidence:** selection logic uses `USE_FLYWAY` and `jdbcUrl` availability. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseManager.kt:105, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/management/SchemaManagerFactory.kt:17)

### 5) Duplicate internal write paths for same entities
- **Pattern:** repository writes coexist with direct table writes in `SQLiteWorkTreeService`.
- **Systems/components involved:** `SQLiteWorkItemRepository`/`SQLiteNoteRepository`/`SQLiteDependencyRepository` vs `SQLiteWorkTreeService` direct `WorkItemsTable`/`DependenciesTable`/`NotesTable` writes.
- **Why risk:** legality/audit rules enforced in one write path may be bypassed or drift in another path.
- **Evidence:** direct inserts/updates in work-tree service. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/service/SQLiteWorkTreeService.kt:41, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/service/SQLiteWorkTreeService.kt:84, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/service/SQLiteWorkTreeService.kt:105)

### 6) Competing role-change paths
- **Pattern:** validated transition path (`advance_item`/`complete_tree`) coexists with direct role mutation path (`manage_items update`).
- **Systems/components involved:** `RoleTransitionHandler` vs `ManageItemsTool` partial update.
- **Why risk:** split-brain legality: some callers follow trigger legality + gates + blockers, others can mutate role directly.
- **Evidence:** transition path via handler. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:157, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:261)
- **Evidence:** direct role assignment in update path. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:395, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:491)

## Runtime selectors that choose variants
- Transport selector: `MCP_TRANSPORT` chooses `stdio` vs `http`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:115)
- DB mode selector: `USE_FLYWAY` influences schema manager choice. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseConfig.kt:22)
- DB file selector: `DATABASE_PATH` can point different instances at different or same stores. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseConfig.kt:14)
