# PM Plane Output Boundaries

## Objective
Establish the strict separation between **PM metadata writes** and **workflow-significant writes** to ensure Dopemux systems maintain distinct authority boundaries.

## Authority Boundaries

1. **Leantime** is the canonical PM record/reflection authority. It manages projects, goals, tasks, and sprint planning. It is **not** the workflow-law authority.
2. **Task Orchestrator** is the canonical workflow authority. It adjudicates workflow-significant changes such as task state transitions, phase changes, and blocker clearance.
3. **ConPort / Dope-Memory** handle chronicle logging and task progress context.

## Write Classification Policy

All payloads entering the PM plane must be classified.

### Direct PM Metadata Writes (Allowed)
These updates are allowed to proceed through the generic PM update path (`pm_update_work_item`). They represent record updates and reflection states, such as:
- `title`, `headline`
- `description`, `details`
- `assignee`, `assigned_to`, `owner`
- `due_date`, `start_date`, `end_date`
- `labels`, `tags`
- `notes`, `comments`
- `priority`, `estimate`, `story_points`
- `reflection_metadata`

### Workflow-Significant Writes (Forbidden directly)
Any state change that alters workflow legality must be rejected from generic PM update paths. These include:
- `status`, `state`, `phase`, `stage`
- `transition`
- `blocked`, `blocker`
- `promote`, `demote`, `next_action`
- Any mutation that affects next-action computation.

**Important**: Mixed payloads containing both PM metadata and workflow-significant fields will **fail closed**. We do not silently split mixed payloads to avoid shadow-state drift.

## Routing Rules

The PM-plane tools must adhere to the following routing API:

1. **`pm_update_work_item`**
   - **Type**: Metadata-only direct path.
   - **Behavior**: May reflect directly to Leantime. Rejects payloads containing workflow-significant fields.

2. **`pm_transition_work_item`**
   - **Type**: Task Orchestrator sanctioned transition path.
   - **Behavior**: This is the only valid path for workflow law. Task Orchestrator executes the transition. Leantime mirrors the outcome only.

3. **`pm_log_progress`**
   - **Type**: ConPort/dope-memory logging path.
   - **Behavior**: Writes chronicle updates without altering workflow law.

## Reflection Semantics

Task Orchestrator records explicit `LeantimeReflection` on operations involving Leantime integration. The states represent:

- **`succeeded`**: The operation applied successfully to the canonical backend and was successfully mirrored to Leantime.
- **`failed`**: The operation failed at the canonical backend.
- **`degraded`**: The operation succeeded at the canonical backend (e.g., a workflow transition was successful in Task Orchestrator), but the mirroring to Leantime failed (e.g., due to an API outage).

**Clarifications**:
- Canonical workflow success **can coexist** with degraded reflection.
- `degraded` is not clean success but **does not** affect workflow legality.
- Direct Leantime workflow-significant drift (originating from Leantime UI) is treated as **reconciliation-only**, and does not bypass Task Orchestrator workflow law.

## Rejection and Reconciliation Cases

1. **Direct PM update contains workflow-significant fields**: Rejected. Fails closed with an explicit error asking to use `pm_transition_work_item`.
2. **Direct Leantime workflow-significant write**: Rejected or marked as reconciliation-only. It must never become a lawful transition surface by accident.
3. **Canonical transition succeeds but reflection fails**: The API will return a `degraded` reflection state.
4. **Required workflow data unavailable**: Fail closed.

## Concrete Examples

### Allowed
`pm_update_work_item` with metadata only.
```json
{
  "title": "Fix the parser bug",
  "assignee": "jules",
  "due_date": "2026-03-15"
}
```

### Rejected
`pm_update_work_item` with mixed data.
```json
{
  "title": "Fix the parser bug",
  "status": "in_progress"
}
```

### Sanctioned
`pm_transition_work_item` mapping to an authorized Task Orchestrator operation.
```json
{
  "work_item_id": "task_123",
  "transition": "start_work"
}
```

### Degraded
Transition succeeds canonically in Task Orchestrator, but Leantime reflection fails.
```json
{
  "success": true,
  "operation_type": "transition",
  "canonical_backend": "task_orchestrator",
  "reflection_state": "degraded",
  "reconciliation_state": "pending_reconciliation",
  "message": "transition succeeded canonically, Leantime reflection degraded"
}
```
