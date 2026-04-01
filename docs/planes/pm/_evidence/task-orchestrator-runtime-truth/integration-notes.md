---
id: task_orchestrator_runtime_truth_integration_notes
title: Task Orchestrator Runtime Truth Integration Notes
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Current Task Orchestrator integration boundaries with Leantime, dopecon-bridge, ConPort, and PM-plane helpers.
---
# Task Orchestrator - Integration Notes

## Leantime

- Epics can carry `leantime_project_id` and `leantime_reflection`.
- Promotion paths can sync to Leantime and record degraded reflection state when the upstream bridge or Leantime path fails.
- PM write rules treat Leantime as mirror only for workflow-significant transitions.

## dopecon-bridge

- `WorkflowService` owns a bridge client for PM routing.
- `WorkflowStore` uses dopecon-bridge custom-data APIs as its present persistence substrate.
- This is the main runtime authority leak documented in the supervisor packet.

## ConPort / PM-plane helpers

- The project workflow routes import and delegate to `dopemux.pm.reads`.
- The PM write routes import and delegate to `src.dopemux.pm.writes`.
- This means Task Orchestrator currently sits partly above and partly beside the normalized PM-plane helper layer.

## Memory

- PM write helpers mirror progress to dope-memory chronicle and mirror workflow outcomes to Leantime, but the Task Orchestrator packet itself does not evidence dope-memory as a workflow store.
