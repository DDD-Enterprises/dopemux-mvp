# 99 Evidence Index

## A) Primary code/schema/runtime citations

### Core entity/state model
- WorkItem model and validation: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/WorkItem.kt:7-75`
- Role enum/progression/threshold checks: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Role.kt:8-33`
- Note model: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Note.kt:13-34`
- Dependency model + unblock threshold semantics: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Dependency.kt:13-47`
- RoleTransition model: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/RoleTransition.kt:10-23`
- Note schema entry model: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/NoteSchemaEntry.kt:34-40`

### Persistence schema
- Migration tables and constraints: `current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:5-77`
- WorkItems table mapping: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/WorkItemsTable.kt:6-33`
- Notes table mapping: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/NotesTable.kt:7-21`
- Dependencies table mapping: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/DependenciesTable.kt:7-21`
- RoleTransitions table mapping: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/RoleTransitionsTable.kt:7-22`
- V2 migration field changes: `current/src/main/resources/db/migration/V2__Work_Item_Field_Updates.sql:5-53`

### Repository ownership
- WorkItem repository interface: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/WorkItemRepository.kt:9-98`
- Note repository interface: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/NoteRepository.kt:6-14`
- Dependency repository interface: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/DependencyRepository.kt:10-31`
- RoleTransition repository interface: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/RoleTransitionRepository.kt:7-13`
- Repository provider bindings: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/DefaultRepositoryProvider.kt:20-32`

### Transition legality/gates
- RoleTransitionHandler lifecycle and legality: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:57-119`, `...:121-184`, `...:199-274`, `...:306-371`
- Advance tool legality path and note-gate checks: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:157-193`, `...:195-258`, `...:261-361`
- Complete-tree legality path and gate checks: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/compound/CompleteTreeTool.kt:255-304`, `...:405-421`
- Cascade/unblock detection: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/CascadeDetector.kt:71-124`, `...:137-162`, `...:179-241`

### Direct mutation bypass evidence
- ManageItems direct role assignment/update path: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:250-257`, `...:395-411`, `...:491-499`, `...:502-516`
- Workflow guide stating no direct role assignment (documented intent): `current/docs/workflow-guide.md:39`

### Dependency/blocker/next-action computation
- GetNextStatus recommendation and progression position: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextStatusTool.kt:75-141`
- GetNextItem candidate/filter/sort logic: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:86-114`, `...:183-225`
- GetBlockedItems blocked derivation: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetBlockedItemsTool.kt:109-197`, `...:243-266`
- QueryItems overview role counts (derived progress): `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/QueryItemsTool.kt:396-417`, `...:435-448`, `...:506-509`

### Notes/schema participation
- Schema service source/path/env selector: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/config/YamlNoteSchemaService.kt:13-16`, `...:40-46`, `...:86-89`
- NoteSchemaService schema-free behavior: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/NoteSchemaService.kt:11-13`, `...:35-37`
- ManageNotes write path: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/notes/ManageNotesTool.kt:128-216`, `...:222-331`
- Note upsert mutation behavior (update-in-place): `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/SQLiteNoteRepository.kt:43-57`

### Audit/history
- RoleTransition repository implementation: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/SQLiteRoleTransitionRepository.kt:27-121`
- Transition read exposure via get_context: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetContextTool.kt:222-260`
- Audit write caveat (create result ignored): `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:354-362`

### Integration seams and runtime selectors
- Tool context wiring: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/ToolExecutionContext.kt:23-45`
- Server setup + tool registration + transport select: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:76-120`
- MCP adapter addTool bridge: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/McpToolAdapter.kt:46-83`
- Env-config selectors: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseConfig.kt:14-22`, `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/CurrentMcpServer.kt:165`
- Schema manager variant selection: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/DatabaseManager.kt:105-109`, `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/management/SchemaManagerFactory.kt:17-22`
- Direct DB writes in work-tree service: `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/service/SQLiteWorkTreeService.kt:41-63`, `...:84-92`, `...:105-121`

### Runtime variants / split-brain evidence
- Gradle includes both modules: `settings.gradle.kts:7-11`
- Clockwork deprecated but runnable docs: `clockwork/DEPRECATED.md:3-4`, `clockwork/DEPRECATED.md:41-59`
- Docker runtime targets v2 and current: `Dockerfile:82-92`
- Compose includes v2 and v3 services: `docker-compose.yml:2-6`, `docker-compose.yml:36-40`, `docker-compose.yml:68-72`
- Clockwork legacy main and DB default: `clockwork/src/main/kotlin/Main.kt:60-68`, `clockwork/src/main/kotlin/Main.kt:84`

### Plugin/hook seams
- Plugin manifest: `claude-plugins/task-orchestrator/.claude-plugin/plugin.json:2-7`
- Hook registration map: `claude-plugins/task-orchestrator/hooks/hooks-config.json:3-50`
- Hook-injected workflow usage guidance: `claude-plugins/task-orchestrator/hooks/session-start.mjs:8-18`, `claude-plugins/task-orchestrator/hooks/subagent-start.mjs:12-17`

## B) Negative-evidence searches (explicit)

### Scope
- `current/src/main/kotlin`
- `current/src/main/resources`
- `current/src/main/resources/db/migration`
- `current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools`

### Commands and results
1. Decision model symbols
- Command:
  - `rg -n "data class Decision|class Decision|enum class Decision|decision_id|decisions table" current/src/main/kotlin current/src/main/resources | wc -l`
- Result: `0`

2. Event streaming / webhook symbols
- Command:
  - `rg -n "webhook|kafka|rabbitmq|pubsub|sns|sqs|nats|event bus|emitEvent|publish\(" current/src/main/kotlin current/src/main/resources | wc -l`
- Result: `0`

3. Non-MCP REST route/controller symbols
- Command:
  - `rg -n "@GetMapping|@PostMapping|routing\s*\{|Route\(" current/src/main/kotlin current/src/main/resources | wc -l`
- Result: `0`

4. Import/export tool symbols
- Command:
  - `rg -n "export_|import_|backup|restore|csv|jsonl" current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools | wc -l`
- Result: `0`

5. Dedicated role-transition MCP tool classes
- Command:
  - `rg -n "class .*RoleTransition|name\s*=\s*\"query_role|name\s*=\s*\"list_role" current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools | wc -l`
- Result: `0`

6. Decision tables in current migrations
- Command:
  - `rg -n "CREATE TABLE .*decision|decision_id|decisions" current/src/main/resources/db/migration | wc -l`
- Result: `0`

7. Event/audit/history tables beyond role_transitions
- Command:
  - `rg -n "CREATE TABLE .*event|CREATE TABLE .*audit|CREATE TABLE .*history|chronicle" current/src/main/resources/db/migration | wc -l`
- Result: `0`

8. CLI framework/subcommand parser symbols in current
- Command:
  - `rg -n "picocli|kotlinx\.cli|commons-cli|subcommand|commandLine" current/src/main/kotlin | wc -l`
- Result: `0`

9. Main entrypoints in current
- Command:
  - `rg -n "fun main\(" current/src/main/kotlin | wc -l`
- Result: `1`

### Supplemental search evidence
- No `addPrompt`/`addResource` implementations found in current MCP interface package (capabilities declared, tool registration present):
  - Search command used: `rg -n "addPrompt|addResource|...|addTool" current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp`
  - Positive lines include `addTool` only; no `addPrompt`/`addResource` hits. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/interfaces/mcp/McpToolAdapter.kt:46)
