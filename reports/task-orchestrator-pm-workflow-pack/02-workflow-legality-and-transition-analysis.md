# 02 Workflow Legality and Transition Analysis

## Implemented behavior

### Transition legality engine exists and is explicit
- `RoleTransitionHandler` implements a 3-phase model: resolve trigger -> validate dependency legality -> apply (persist + transition record intent). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:57, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:199, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:306)
- Trigger legality is constrained to `start|complete|block|hold|resume|cancel`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:67)
- Illegal trigger/role combinations are rejected (examples: start from terminal/blocked, complete from blocked/terminal, resume when not blocked, resume without `previousRole`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:129, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:145, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:164, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:171)
- `advance_item` uses this handler and enforces both dependency validation and note gates before apply. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:169, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:195, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:228, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/AdvanceItemTool.kt:261)
- `complete_tree` also routes role changes through `RoleTransitionHandler` (not raw role assignment). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/compound/CompleteTreeTool.kt:230, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/compound/CompleteTreeTool.kt:272, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/compound/CompleteTreeTool.kt:287)

### State/value constraints are partly enforced at model/DB level
- Role domain is constrained at DB level (`queue/work/review/blocked/terminal`). (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:11)
- Role values are parsed from fixed enum in domain code; unknowns fail conversion and/or default only on row mapping fallbacks. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Role.kt:13, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/SQLiteWorkItemRepository.kt:478)
- Dependency threshold values are validated (`queue/work/review/terminal`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Dependency.kt:31)

## Direct mutation bypasses (critical for legality model)
- `manage_items` update allows direct `role` mutation and persists via repository update without trigger-resolution legality checks. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:395, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:491, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:502)
- `manage_items` create accepts caller-provided role directly (default queue only if omitted). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:181, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:250, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:280)
- This means workflow legality is **not** globally enforced at write boundary; it is enforced only on transition-path tools that call `RoleTransitionHandler`.
  - Evidence of documented intent conflicting with implementation: workflow guide says no direct role assignment, but `manage_items` implements direct role set/update. (current/docs/workflow-guide.md:39, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/items/ManageItemsTool.kt:491)

## Classification
- Transition legality via triggers: **authoritative on transition paths** (`advance_item`, `complete_tree`), **not authoritative globally** due to direct role writes in `manage_items`.
- Role/status/state-change constraints: **partially authoritative** (DB enum/value constraints exist; path-level transition legality can be bypassed).

## Absent/no evidence found
- No global database-level transition state machine (e.g., SQL constraint forcing allowed prior->next role pairs) found in migrations.
  - Search evidence (scope `current/src/main/resources/db/migration`):
    - `rg -n "CREATE TABLE .*decision|decision_id|decisions" current/src/main/resources/db/migration | wc -l` => `0`
    - `rg -n "CREATE TABLE .*event|CREATE TABLE .*audit|CREATE TABLE .*history|chronicle" current/src/main/resources/db/migration | wc -l` => `0`
  - Existing schema evidence shows role value constraints only. (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:11)
