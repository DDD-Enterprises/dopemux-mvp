# 04 Audit, History, and Chronicle

## Implemented audit/history systems

### Role transition audit trail
- A dedicated persisted audit table exists: `role_transitions` with `item_id`, `from_role`, `to_role`, trigger, summary, and timestamp. (current/src/main/resources/db/migration/V1__Current_Initial_Schema.sql:64, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/database/schema/RoleTransitionsTable.kt:7)
- Transition records are intended to be written during transition apply in `RoleTransitionHandler.applyTransition`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:295, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:345)
- Transition history is queryable at repository level (`findByItemId`, `findByTimeRange`, `findSince`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/RoleTransitionRepository.kt:9)
- Exposed read surface in tools is limited: `get_context` session-resume reads recent transitions via `findSince`. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetContextTool.kt:223)

### Notes as operational narrative artifacts
- Notes are persisted per item/key and surfaced in context/gate responses; they function as phase artifacts and explanatory record, not immutable event log. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/model/Note.kt:8, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetContextTool.kt:131)
- Notes are mutable via upsert (same `(itemId,key)` updates in place). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/SQLiteNoteRepository.kt:43, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/infrastructure/repository/SQLiteNoteRepository.kt:51)

## Canonical vs supporting record judgment
- `role_transitions` is the closest canonical operational history for workflow transitions.
- Notes are supporting artifacts (required for gates and context) but not canonical transition chronology.
- Repository-level transition history capability is broader than tool-level exposure (full query by item/time exists in repository, but MCP tools expose only `findSince` through `get_context`). (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/domain/repository/RoleTransitionRepository.kt:9, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/tools/workflow/GetContextTool.kt:223)

## Reliability caveat in audit recording
- `RoleTransitionHandler.applyTransition` does not check or propagate failure from `roleTransitionRepository.create(transition)`; it always returns success if item update succeeded. This can produce role changes without guaranteed audit persistence. (current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:342, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:354, current/src/main/kotlin/io/github/jpicklyk/mcptask/current/application/service/RoleTransitionHandler.kt:356)

## Absent/no evidence found
- No separate `chronicle`, immutable event stream, or timeline subsystem beyond `role_transitions` + mutable notes in current module.
  - Negative evidence: event/chronicle terms and event-table patterns scan to zero in current runtime and migrations (excluding `role_transitions`). (pm-workflow-pack/99-evidence-index.md)
