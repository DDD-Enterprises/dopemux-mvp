# 07 Repo-Local Authority Verdict

## Hard verdict (repo-local)

### What this repo is authoritative for
- It is authoritative for persistence and CRUD of v3 `WorkItem`, `Note`, `Dependency`, and `RoleTransition` records in SQLite (via repositories + migrations). (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:5, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:34, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:49, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:64, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/DefaultRepositoryProvider.kt:20)
- It is authoritative for MCP-exposed PM operations through the 13-tool server surface. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:89, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:220)

### What it appears designed to enforce
- Trigger-based role-transition legality, dependency preconditions, and note-schema gates when callers use transition tools (`advance_item`, `complete_tree`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:67, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:199, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:195, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/compound/CompleteTreeTool.kt:255)
- Dependency graph legality against cycles/duplicates on dependency creation paths. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/SQLiteDependencyRepository.kt:37, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/SQLiteDependencyRepository.kt:42, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/SQLiteDependencyRepository.kt:132)

### What it computes
- Next status recommendation and progression position (`get_next_status`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextStatusTool.kt:31, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextStatusTool.kt:126)
- Next actionable items by role/dependency/priority/complexity (`get_next_item`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:86, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:101, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:107)
- Blocked-item sets and blocker satisfaction details (`get_blocked_items`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetBlockedItemsTool.kt:17, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetBlockedItemsTool.kt:185)
- Context snapshots for item/session/health including stalled-by-note-gate detection (`get_context`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetContextTool.kt:15, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetContextTool.kt:353)

### What it stores
- Current state (`work_items`), supporting artifacts (`notes`), dependency graph (`dependencies`), and transition history (`role_transitions`). (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:5, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:34, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:49, current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:64)

### What it does **not** own (based on repo-local evidence)
- No explicit decision object/table/system; decision persistence is absent. (pm-workflow-pack/99-evidence-index.md)
- No event-stream/webhook bus/export-import subsystem in current module. (pm-workflow-pack/99-evidence-index.md)
- No globally enforced transition legality at DB boundary (only value-domain checks plus path-level enforcement). (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:11, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:491)

### What external integrators must not bypass
- Do not bypass `advance_item` / `complete_tree` for role changes if relying on legality (dependency gates, note gates, trigger legality, transition audit intent).
  - Bypass path exists via `manage_items` role updates. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:169, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/compound/CompleteTreeTool.kt:287, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:491)
- Do not assume single-version authority unless deployment explicitly pins v3 `current`; v2 `clockwork` remains buildable/runnable in repo. (settings.gradle.kts:11, Dockerfile:82, docker-compose.yml:2)
