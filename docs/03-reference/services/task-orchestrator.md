---
id: task-orchestrator
title: Task Orchestrator
type: reference
owner: '@hu3mann'
last_review: '2026-04-01'
next_review: '2026-06-30'
author: '@codex'
date: '2026-04-01'
prelude: Active Task Orchestrator runtime reference grounded in the current FastAPI service, PM-plane routers, config defaults, and observed persistence boundaries.
---
# Task Orchestrator

## Runtime role

`task-orchestrator` is the intended workflow authority for the PM plane.

The active runtime entrypoint in this checkout is:

- `services/task-orchestrator/app/main.py`

That FastAPI app currently combines:

- idea and epic workflow lifecycle endpoints
- project-scoped workflow read surfaces
- normalized PM write helpers
- coordination, health, info, and metrics surfaces

## Active HTTP surfaces

### Workflow entity lifecycle

- `POST /api/workflow/ideas`
- `GET /api/workflow/ideas`
- `PATCH /api/workflow/ideas/{idea_id}`
- `POST /api/workflow/ideas/{idea_id}/promote`
- `POST /api/workflow/epics`
- `GET /api/workflow/epics`
- `PATCH /api/workflow/epics/{epic_id}`

### Project workflow reads and transition surface

- `GET /api/projects/{project_id}/workflow/queue`
- `GET /api/projects/{project_id}/workflow/blockers`
- `GET /api/projects/{project_id}/workflow/state`
- `POST /api/projects/{project_id}/workflow/transition`

### Normalized PM write helpers

- `POST /api/pm/work-items/{task_id}/update`
- `POST /api/pm/work-items/{task_id}/transition`
- `POST /api/pm/work-items/{task_id}/progress`

### Coordination and service discovery

- `POST /api/coordination/operations`
- `GET /api/coordination/health`
- `GET /api/coordination/metrics`
- `POST /api/coordination/events`
- `GET /api/coordination/conflicts`
- `POST /api/coordination/conflicts/{conflict_id}/resolve`
- `GET /api/coordination/status`
- `POST /api/coordination/test`
- `GET /health`
- `GET /info`
- `GET /metrics`

## Runtime defaults

- Config module: `services/task-orchestrator/task_orchestrator/config.py`
- Default port: `PORT_BASE + 14`
- With default `PORT_BASE=3000`, the observed default resolves to `3014`
- The `/info` route also reports `3014` as the default fallback port when `PORT` is unset

## Persistence boundary

Workflow entity persistence is currently routed through:

- `services/task-orchestrator/app/services/workflow_store.py`

Observed storage categories:

- `workflow_ideas`
- `workflow_epics`
- `workflow_audit`

Observed persistence substrate:

- `WorkflowStore` reads and writes those records through DopeconBridge `custom_data`

This is runtime fact, not intended authority expansion. It means current workflow authority depends on a bridge-mediated persistence path that remains remediation debt.

## Current fail-closed and degraded behaviors

- Project-scoped workflow transition currently returns an explicit unavailable receipt rather than executing a canonical transition path
- Tests verify that direct status mutation is blocked and that audit persistence failure aborts promotion
- PM write helpers record canonical and mirror outcomes into coordinator metrics when the coordinator is initialized

## Known drift to keep explicit

- Architectural target: Task Orchestrator is the workflow authority
- Runtime drift: primary workflow persistence still depends on dopecon-bridge `custom_data`
- Runtime drift: `/api/projects/{project_id}/workflow/transition` is present but not yet bound to canonical transition execution
- Runtime drift: adjacent PM read envelopes elsewhere in the repo still contain stale backend labels; do not infer authority from those envelopes alone

## Evidence companions

- `docs/planes/pm/_evidence/task-orchestrator-runtime-truth/executive-summary.md`
- `docs/planes/pm/_evidence/task-orchestrator-runtime-truth/architecture-and-intended-uses.md`
- `docs/planes/pm/_evidence/task-orchestrator-runtime-truth/transport-and-runbook.md`
- `docs/05-audit-reports/supervisor-pm-mcp-server-matrix-2026-03-27.md`
- `docs/05-audit-reports/supervisor-pm-evidence-packet-2026-03-27.md`
- `docs/05-audit-reports/supervisor-memory-pm-authority-reconciliation-2026-03-27.md`
- `docs/05-audit-reports/supervisor-pm-memory-authority-enforcement-packet-2026-04-01.md`
