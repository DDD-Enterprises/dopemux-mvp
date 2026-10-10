---
id: task_orchestrator_runtime_truth_data_model
title: Task Orchestrator Runtime Truth Data Model
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Current Task Orchestrator workflow data model, request envelopes, and persistence categories as observed in the repository.
---
# Task Orchestrator - Data Model

## Core persisted models

Source: `services/task-orchestrator/app/models/workflow.py`

- `WorkflowIdea`
  - persisted as Stage-1 workflow idea
  - IDs must start with `idea_`
  - status domain: `new`, `under-review`, `approved`, `rejected`, `promoted`
- `WorkflowEpic`
  - persisted as Stage-2 workflow epic
  - IDs must start with `epic_`
  - status domain: `planned`, `in-planning`, `ready`, `in-progress`, `done`
- `TransitionAuditRecord`
  - immutable transition audit shape with `from_state`, `to_state`, versions, idempotency key, and linked ID snapshot
- `LeantimeReflection`
  - reconciliation metadata for Leantime mirroring

## Request / response envelopes

- `TransitionWorkflowRequest`
- `PriorityQueueResult`
- `BlockersResult`
- `WorkflowStateResult`
- `TransitionResult`

These are the project-scoped workflow HTTP envelopes used by `/api/projects/{project_id}/workflow/*`.

## Persistence categories

Source: `services/task-orchestrator/app/services/workflow_store.py`

- `workflow_ideas`
- `workflow_epics`
- `workflow_audit`

These categories are currently stored through dopecon-bridge custom-data calls, which means the workflow runtime does not yet have a cleanly isolated authoritative backing store.

## PM write contract dependency

The PM write routes mounted under `/api/pm` delegate to `src/dopemux/pm/writes.py`, which applies canonical-authority rules for:

- metadata updates -> `Leantime`
- workflow transitions -> `Task Orchestrator`
- progress logging -> `ConPort`
