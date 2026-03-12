---
id: ADR_197_P0_STAGE1_STAGE2_IMPLEMENTATION_PR_PLAN_2026_02_06
title: Adr 197 P0 Stage1 Stage2 Implementation Pr Plan 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Decision-complete PR plan to implement ADR-197 Stage-1 and Stage-2 workflow runtime without breaking existing APIs, CLI, or config contracts.
---
# ADR-197 P0 Execution Plan: Stage-1/Stage-2 Workflow Runtime

## Objective
Implement the missing ADR-197 Stage-1 (`Idea`) and Stage-2 (`Epic`) runtime surfaces end-to-end, with no breaking changes, and with explicit compatibility defaults.

## Current Truth Baseline (2026-02-06)

- `docs/90-adr/ADR-197-task-epic-workflow-system.md` defines `workflow_ideas` and `workflow_epics` categories and promotion flow.
- Runtime gap is confirmed in active code paths: there are no Stage-1/Stage-2 workflow endpoints in `services/task-orchestrator/app/main.py`.
- `services/task-orchestrator/conport_mcp_client.py` supports reading custom data (`get_custom_data`) but has no typed Stage-1/Stage-2 workflow operations.
- `src/dopemux/cli.py` currently has no `workflow` command group for idea/epic lifecycle.

## Locked Constraints

1. No breaking changes to existing public APIs/CLI/config.
1. Additive-only contract changes.
1. Stage-1/Stage-2 implementation must persist to ConPort custom data categories:
- `workflow_ideas`
- `workflow_epics`
1. Promotion (`idea -> epic`) must be idempotent and audit-friendly.
1. Degraded-mode behavior is required when ConPort or Leantime is unavailable.

## Additive Public Interface Plan

### Task-Orchestrator API (new endpoints)

Add to `services/task-orchestrator/app/main.py` under `/api/workflow`:

1. `POST /api/workflow/ideas`
- Creates idea in `workflow_ideas`.
- Response: `201` with `idea_id`, `status`, `created_at`.

1. `GET /api/workflow/ideas`
- Lists ideas with optional filters: `status`, `tag`, `limit`.
- Response: `200` list ordered by `created_at DESC`.

1. `PATCH /api/workflow/ideas/{idea_id}`
- Partial update of `title`, `description`, `status`, `tags`.
- Response: `200` updated record.

1. `POST /api/workflow/ideas/{idea_id}/promote`
- Promotes idea to epic (one-way).
- Creates epic in `workflow_epics`.
- Marks idea with `promoted_to_epic_id` and `status=promoted`.
- Optional Leantime project create flag: `sync_to_leantime: bool = true`.
- Response: `201` with `epic_id`, `idea_id`, `leantime_project_id|null`.

1. `POST /api/workflow/epics`
- Direct epic creation for pre-approved initiatives.
- Response: `201` with `epic_id`.

1. `GET /api/workflow/epics`
- Lists epics with optional filters: `status`, `priority`, `tag`, `limit`.
- Response: `200` list ordered by `created_at DESC`.

1. `PATCH /api/workflow/epics/{epic_id}`
- Partial update of scope fields and status.
- Response: `200` updated epic.

### CLI (new additive group)

Add to `src/dopemux/cli.py`:

1. `dopemux workflow ideas add --title --description [--tag ...] [--source]`
1. `dopemux workflow ideas list [--status] [--tag] [--limit]`
1. `dopemux workflow ideas update <idea_id> [--title] [--description] [--status] [--tag ...]`
1. `dopemux workflow ideas promote <idea_id> [--sync-leantime/--no-sync-leantime]`
1. `dopemux workflow epics add --title --description --business-value [--priority]`
1. `dopemux workflow epics list [--status] [--priority] [--limit]`
1. `dopemux workflow epics update <epic_id> [--status] [--priority] [--add-criteria ...]`

All commands are additive and do not alter existing command behavior.

### Config and Environment (additive)

New optional env vars (existing behavior unchanged if absent):

- `DOPMUX_WORKFLOW_ENABLE=true|false` (default `true`)
- `DOPMUX_WORKFLOW_DEFAULT_IDEA_LIMIT=50` (default `50`)
- `DOPMUX_WORKFLOW_DEFAULT_EPIC_LIMIT=50` (default `50`)
- `DOPMUX_WORKFLOW_PROMOTION_SYNC_LEANTIME=true|false` (default `true`)

## Data Contracts

### WorkflowIdea (custom_data value schema)

```json
{
  "id": "idea_<uuid>",
  "title": "string",
  "description": "string",
  "source": "user-request|brainstorm|bug-report|other",
  "creator": "string",
  "tags": ["string"],
  "status": "new|under-review|approved|rejected|promoted",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "promoted_to_epic_id": "epic_<uuid>|null"
}
```

### WorkflowEpic (custom_data value schema)

```json
{
  "id": "epic_<uuid>",
  "title": "string",
  "description": "string",
  "business_value": "string",
  "acceptance_criteria": ["string"],
  "priority": "critical|high|medium|low",
  "status": "planned|in-planning|ready|in-progress|done",
  "created_from_idea_id": "idea_<uuid>|null",
  "leantime_project_id": "int|null",
  "tags": ["string"],
  "adhd_metadata": {
    "estimated_complexity": 0.0,
    "required_energy_level": "low|medium|high",
    "can_work_parallel": true
  },
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

## Implementation PR Breakdown (Decision-Complete)

## PR-1: Workflow Domain + Storage Adapter

### Scope
- Add typed models and validation.
- Add typed ConPort custom-data write/update wrappers.

### Files
- `services/task-orchestrator/app/models/workflow.py` (new)
- `services/task-orchestrator/app/services/workflow_store.py` (new)
- `services/task-orchestrator/conport_mcp_client.py` (add `log_custom_data`, `upsert_custom_data`, helper parsing)

### Acceptance
- Schema validation rejects invalid status/priority/energy values.
- Store APIs round-trip ideas and epics via ConPort custom data.

## PR-2: Workflow Service (Business Logic)

### Scope
- Add `WorkflowService` implementing create/list/update/promote behavior.
- Add idempotent promotion guard.

### Files
- `services/task-orchestrator/app/services/workflow_service.py` (new)
- `services/task-orchestrator/app/services/__init__.py` (if needed for exports)

### Logic Rules
- Promotion is one-way.
- Re-promoting already-promoted idea returns existing epic id.
- `updated_at` always changes on mutation.

### Acceptance
- Duplicate promote calls produce same `epic_id` and no duplicate epic records.

## PR-3: API Endpoints

### Scope
- Expose additive `/api/workflow/*` endpoints.
- Add request/response models and strict error mapping.

### Files
- `services/task-orchestrator/app/main.py`

### Error Contract
- `400` validation error
- `404` missing idea/epic
- `409` incompatible state transitions
- `503` upstream unavailable (ConPort/Leantime)

### Acceptance
- OpenAPI includes all new endpoints.
- Existing coordination endpoints unchanged.

## PR-4: Optional Leantime Promotion Sync

### Scope
- On promote, optionally create Leantime project and backfill `leantime_project_id`.
- Degrade gracefully when Leantime unavailable.

### Files
- `services/task-orchestrator/app/adapters/bridge_adapter.py`
- `services/task-orchestrator/app/services/workflow_service.py`

### Defaults
- `sync_to_leantime=true` by default.
- If unavailable, epic creation succeeds with `leantime_project_id=null` and warning metadata.

### Acceptance
- Promotion never loses ConPort record due to Leantime outage.

## PR-5: CLI Integration

### Scope
- Add `workflow` command group and subcommands.
- Add concise ADHD-friendly output formatting.

### Files
- `src/dopemux/cli.py`
- `tests/unit/test_cli_workflow_commands.py` (new)

### Acceptance
- Commands support non-interactive usage and return non-zero on failures.

## PR-6: Tests, Docs, and Certification

### Scope
- Unit + integration coverage for Stage-1/Stage-2.
- Docs for how-to + reference + architecture deltas.

### Files
- `tests/unit/test_task_orchestrator_workflow_models.py` (new)
- `tests/unit/test_task_orchestrator_workflow_service.py` (new)
- `tests/integration/test_workflow_idea_epic_flow.py` (new)
- `docs/02-how-to/workflow-idea-to-epic.md` (new)
- `docs/03-reference/workflow-schema.md` (new)
- `docs/04-explanation/architecture/architecture-3.0-implementation.md` (update)

### Acceptance
- End-to-end: create idea -> promote to epic -> list epic.
- Degraded path: Leantime unavailable still yields epic record in ConPort.

## Required Test Scenarios

1. Schema validation for both models.
1. Idea creation/list/update happy path.
1. Idea promotion idempotency and state transitions.
1. Promotion failure recovery when Leantime sync fails.
1. Epic list/filter behavior.
1. CLI regression for existing command groups.
1. Backward compatibility: no existing API route/CLI option breakage.

## Rollout and Guardrails

1. Ship behind `DOPMUX_WORKFLOW_ENABLE` (default `true`).
1. Log structured events for idea/epic create/promote/update.
1. Add metric counters:
- `workflow_ideas_created_total`
- `workflow_epics_created_total`
- `workflow_promotions_total`
- `workflow_promotion_failures_total`
1. Add warning log when Leantime sync skipped or fails.

## Exit Criteria

1. Stage-1 and Stage-2 runtime endpoints live and tested.
1. CLI supports idea/epic lifecycle commands.
1. Idempotent promotion implemented and verified.
1. No regressions in existing task-orchestrator API/CLI contracts.
1. Docs updated to mark Stage-1/Stage-2 as `Implemented` where applicable.

## Assumptions and Defaults

1. ConPort custom_data remains the persistence authority for Stage-1/Stage-2.
1. Leantime remains status authority for synced epic lifecycle fields.
1. Promotion remains one-way (idea never auto-demotes from epic).
1. Existing ADR-197 Stage-3/Stage-4 logic remains unchanged in this P0 scope.
