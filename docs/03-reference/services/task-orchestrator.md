---
id: task-orchestrator
title: Task Orchestrator
type: reference
owner: '@hu3mann'
last_review: '2026-03-11'
next_review: '2026-06-11'
author: '@hu3mann'
date: '2026-02-08'
prelude: Task Orchestrator (reference) for dopemux documentation and developer workflows.
---
# Task Orchestrator

## Runtime Role

`task-orchestrator` provides coordination APIs and ADR-197 workflow runtime for
idea and epic lifecycle management.

Primary runtime module:
- `services/task-orchestrator/app/main.py`

Workflow business logic:
- `services/task-orchestrator/app/services/workflow_service.py`

Persistence adapter:
- `services/task-orchestrator/app/services/workflow_store.py`

## Implemented Workflow Scope (ADR-197)

Implemented now:
- Stage-1 Idea lifecycle: create, list, update.
- Stage-2 Epic lifecycle: create, list, update.
- Idea promotion to epic (idempotent promote endpoint).
- Optional Leantime project sync during promote with degraded fallback.
- ConPort custom-data persistence for ideas and epics.

Not implemented yet in this service runtime:
- Stage-3 task decomposition lifecycle from ADR-197.
- Stage-4 execution loop and automated completion handoff.

## HTTP API Contracts

### Workflow Endpoints

- `POST /api/workflow/ideas`
- `GET /api/workflow/ideas`
- `PATCH /api/workflow/ideas/{idea_id}`
- `POST /api/workflow/ideas/{idea_id}/promote`
- `POST /api/workflow/epics`
- `GET /api/workflow/epics`
- `PATCH /api/workflow/epics/{epic_id}`

### Coordination Endpoints (existing)

- `POST /api/coordination/operations`
- `GET /api/coordination/health`
- `GET /api/coordination/metrics`
- `POST /api/coordination/events`
- `GET /api/coordination/conflicts`
- `POST /api/coordination/conflicts/{conflict_id}/resolve`

### Health and Service Discovery

- `GET /health`
- `GET /info`
- `GET /metrics`

## Workflow Error Mapping

Workflow endpoints use stable error contracts:
- `404` for `WorkflowNotFoundError`
- `409` for `WorkflowConflictError`
- `503` for `WorkflowUnavailableError`
- `400` for validation/value errors
- `500` for unexpected failures

## Persistence Model

Workflow data is stored via DopeconBridge custom-data records:
- Category `workflow_ideas`
- Category `workflow_epics`

Each record stores serialized workflow entities keyed by id:
- idea id format: `idea_<uuidhex>`
- epic id format: `epic_<uuidhex>`

## Environment Flags

Workflow runtime toggles:
- `DOPMUX_WORKFLOW_ENABLE` (default `true`)
- `DOPMUX_WORKFLOW_DEFAULT_IDEA_LIMIT` (default `50`)
- `DOPMUX_WORKFLOW_DEFAULT_EPIC_LIMIT` (default `50`)
- `DOPMUX_WORKFLOW_PROMOTION_SYNC_LEANTIME` (default `true`)

Bridge settings:
- `DOPECON_BRIDGE_URL` (default `http://localhost:3016`)
- `DOPECON_BRIDGE_TOKEN` (optional)
- `DOPECON_BRIDGE_SOURCE_PLANE` (default `cognitive_plane`)

## Compatibility Notes

- Workflow contracts are additive and preserve existing coordination APIs.
- Idea promotion is idempotent: repeated promote returns existing epic.
- Leantime sync failure does not fail promotion; warning is returned in payload.
- Progress synchronization can be submitted via `POST /api/coordination/operations` using operation `update_progress` (best-effort live sync with local ledger fallback in docs tooling).

## Runtime Defaults

- Canonical compose service: `task-orchestrator` in `compose.yml`.
- Default host port: `8000` (override with `TASK_ORCHESTRATOR_PORT`).
- Smoke profile startup: `scripts/smoke_up.sh`.
- Full stack startup: `docker compose -f compose.yml up -d task-orchestrator`.

## Leantime / Task-Orchestrator Follow-up Tickets (2026-03-11)

- `PM-TO-001`: Standardize task-orchestrator health + readiness probe expectations between `/health` and workflow endpoints.
- `PM-TO-002`: Add automated verification that Leantime promotion warnings are surfaced in CLI output and docs examples.
- `PM-TO-003`: Add integration test coverage for idea/epic lifecycle with canonical port `8000` and `TASK_ORCHESTRATOR_PORT` override.
- `PM-TO-004`: Add ops runbook step for rogue non-canonical task-orchestrator container cleanup (`scripts/start.sh` behavior).
- `PM-TO-005`: Roll out PR docgen sync skill family and canonical index reconciliation automation.
- `PM-TO-006`: Validate live `update_progress` ticket sync behavior in task-orchestrator + Leantime environments.
