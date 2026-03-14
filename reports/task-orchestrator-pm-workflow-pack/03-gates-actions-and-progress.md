# 03 Gates, Actions, and Progress

## Dependency gates
- **Classification:** `authoritative on transition recommendation/advance paths`, `partially authoritative globally`.
- Implemented checks:
  - Transition validation checks unsatisfied incoming blocking deps for forward progressions. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:218, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:252)
  - `unblockAt` threshold defaults to `terminal` when omitted. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Dependency.kt:43)
  - `advance_item` calls dependency validation before apply. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:169)
  - `get_next_status` and `get_next_item` also compute dependency-blocked readiness. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextStatusTool.kt:109, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:101, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:188)
- Partial-authority caveat:
  - Dependency gates are not enforced when role changes are done through `manage_items` direct update (role can move without transition validation). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:491, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:502)

## Blockers
- **Classification:** `authoritative for blocker derivation on read surfaces`, `advisory for external clients that bypass transition path`.
- `get_blocked_items` computes blocked state from explicit `Role.BLOCKED` and dependency unsatisfied state. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetBlockedItemsTool.kt:17, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetBlockedItemsTool.kt:175, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetBlockedItemsTool.kt:188)
- `CascadeDetector.findUnblockedItems` emits downstream unblocked candidates after transitions. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/CascadeDetector.kt:169, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/CascadeDetector.kt:196)

## Note/comment gates
- **Classification:** `authoritative on transition paths using advance/complete-tree`; `partially authoritative globally`.
- Gate source is schema config (`.taskorchestrator/config.yaml`) resolved by item tags. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/config/YamlNoteSchemaService.kt:13, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/config/YamlNoteSchemaService.kt:40)
- `advance_item` enforces:
  - `start` => required notes for current phase; (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:195)
  - `complete` => all required notes across phases. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:228)
- `complete_tree` also gate-checks required notes before completion and skips dependents on gate failure. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/compound/CompleteTreeTool.kt:255, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/compound/CompleteTreeTool.kt:266)
- `manage_notes` validates note structure and item existence, but does not enforce schema-key correctness at write time. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/notes/ManageNotesTool.kt:141, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/notes/ManageNotesTool.kt:155, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Note.kt:26)

## Next-action computation
- **Classification:** `derived/advisory`.
- `get_next_item` computes next actions by: QUEUE candidates -> remove blocked -> sort by priority/complexity -> limit. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:86, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:101, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:107, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextItemTool.kt:114)
- `get_next_status` computes readiness recommendation (`Ready|Blocked|Terminal`) and next role suggestion. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextStatusTool.kt:31, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextStatusTool.kt:122)

## Decisions/progress tracking
- **Classification:** `partially authoritative for role-progress`, `absent for explicit decision records`.
- Implemented progress signals:
  - Role progression position returned by `get_next_status` (`progressionPosition`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetNextStatusTool.kt:126)
  - Child-count by role in `query_items(overview)` as aggregate progress proxy. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/QueryItemsTool.kt:396, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/QueryItemsTool.kt:506)
- No explicit persisted `Decision` entity/table/tool found in current code/migrations.
  - Negative evidence: decision-model symbol count `0` in `current/src/main/kotlin` + `current/src/main/resources`; decision-table count `0` in current migrations. (pm-workflow-pack/99-evidence-index.md)
