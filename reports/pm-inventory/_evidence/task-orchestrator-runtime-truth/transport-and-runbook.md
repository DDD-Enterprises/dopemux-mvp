---
id: task_orchestrator_runtime_truth_transport_runbook
title: Task Orchestrator Runtime Truth Transport and Runbook
type: runbook
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
status: active
prelude: Active transport surfaces and default runtime settings for the current Task Orchestrator service.
---
# Task Orchestrator - Transport and Runbook

## Active HTTP runtime

- Framework: FastAPI
- Entrypoint: `services/task-orchestrator/app/main.py`
- Service name default: `task-orchestrator`
- Health path default: `/health`
- Default port: `PORT_BASE + 14`, which resolves to `3014` when `PORT_BASE=3000`

## PM-facing routes

- `/api/projects/{project_id}/workflow/queue`
- `/api/projects/{project_id}/workflow/blockers`
- `/api/projects/{project_id}/workflow/state`
- `/api/projects/{project_id}/workflow/transition`
- `/api/pm/work-items/{task_id}/update`
- `/api/pm/work-items/{task_id}/transition`
- `/api/pm/work-items/{task_id}/progress`

## Key environment defaults

- `PORT` default: `3014`
- `LEANTIME_URL` default: `http://leantime:8080`
- `REDIS_URL` default: `redis://redis:6379`
- `CONPORT_URL` default: `http://conport:8005`

## Operational caveat

- The project workflow transition route is callable but not fully implemented as a canonical transition binding yet.
- Operators should treat it as an explicit unavailable surface until that binding is repaired.
