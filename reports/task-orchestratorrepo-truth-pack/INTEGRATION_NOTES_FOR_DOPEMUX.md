# Integration Notes for Dopemux

> Practical guidance for integrating task-orchestrator into dopemux workflows.
> Based on code analysis, not speculation.

## MCP Routing

### Tool Categories for Routing
| Category                | Tools                                                                                                                      | Access Pattern                        |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Read-only               | `query_items`, `query_notes`, `query_dependencies`, `get_next_status`, `get_next_item`, `get_blocked_items`, `get_context` | Safe to call concurrently, idempotent |
| Write (non-destructive) | `manage_items` (create), `manage_notes` (upsert), `manage_dependencies` (create), `advance_item`, `create_work_tree`       | May conflict with concurrent writes   |
| Write (destructive)     | `manage_items` (delete), `manage_notes` (delete), `manage_dependencies` (delete), `complete_tree`                          | Cascading effects, use with caution   |

### Tool Annotations (from code)
All tools declare `ToolAnnotations` with `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`. These can be used for MCP routing decisions.

## Response Envelope

All tools return consistent JSON:
```json
// Success
{ "success": true, "data": { ... } }

// Error
{ "success": false, "error": { "code": "...", "message": "..." } }
```

Error codes from `ErrorCodes.kt`:
- `VALIDATION_ERROR` — bad input
- `RESOURCE_NOT_FOUND` — item/note/dep not found
- `DATABASE_ERROR` — persistence failure
- `INTERNAL_ERROR` — unexpected

## Integration Points

### 1. Session Resume Pattern
```
get_context() → {activeItems, blockedItems, recentTransitions, recommendations}
```
Call at session start to hydrate agent context.

### 2. Workflow Orchestration Pattern
```
create_work_tree() → create hierarchy atomically
advance_item(trigger="start") → move through phases
get_context(itemId=...) → check gate status
manage_notes(operation="upsert") → fill required notes
advance_item(trigger="start") → advance after gates pass
```

### 3. Priority Queue Pattern
```
get_next_item(parentId=..., tags=...) → next actionable item
advance_item(trigger="start") → start work
```

### 4. Completion Pattern
```
complete_tree(itemId=..., trigger="complete") → batch close descendants
```

## Transport Considerations

- **stdio**: Use for local MCP clients (Claude Code, etc.). One process per client.
- **HTTP**: Use for shared/remote access. Bind to `0.0.0.0:3001`. Supports concurrent clients.
- **Data isolation**: Use separate Docker volumes per project/workspace.

## Key Constraints for Integration

1. **Max depth 3**: Hierarchy is 4 levels (0-3). Deeper nesting rejected.
2. **Tags format**: Lowercase alphanumeric + hyphens only. Comma-separated string.
3. **UUID primary keys**: All entity IDs are UUIDs.
4. **Note uniqueness**: `(itemId, key)` is unique. Upserting with same pair updates in-place.
5. **Dependency uniqueness**: `(fromItemId, toItemId, type)` is unique.
6. **Atomic batch create**: `manage_dependencies` create is all-or-nothing. `create_work_tree` is atomic.
7. **Cascade effects**: `advance_item` may trigger parent cascades and unblock notifications.
8. **Schema-free by default**: No config needed for base functionality. All 13 tools work without YAML.
