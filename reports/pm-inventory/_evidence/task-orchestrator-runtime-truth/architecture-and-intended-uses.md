---
id: task_orchestrator_runtime_truth_architecture
title: Task Orchestrator Runtime Truth Architecture and Intended Uses
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Runtime-truth architecture summary for Task Orchestrator as evidenced in the current repository and PM authority bundle outputs.
---
# Task Orchestrator - Architecture and Intended Uses

## Scope

This packet is repo-inspection truth, not a generated `repo-truth-pack/` export. It is backed by:

- `docs/planes/pm/_evidence/PM-AUTH-01.outputs/10_services_task-orchestrator_app_api_project_workflow.py.nl.txt`
- `docs/planes/pm/_evidence/PM-AUTH-01.outputs/11_services_task-orchestrator_app_services_workflow_store.py.nl.txt`
- `docs/planes/pm/_evidence/PM-AUTH-01.outputs/12_services_task-orchestrator_app_services_workflow_service.py.nl.txt`
- `docs/planes/pm/_evidence/PM-AUTH-01.outputs/14_services_task-orchestrator_app_models_workflow.py.nl.txt`
- `docs/planes/pm/_evidence/PM-AUTH-01.outputs/15_services_task-orchestrator_app_main.py.nl.txt`
- `docs/planes/pm/_evidence/PM-AUTH-01.outputs/17_services_task-orchestrator_app_api_pm_tools.py.nl.txt`

## Architecture

- The active runtime is the FastAPI service in `services/task-orchestrator/app/main.py`.
- That runtime includes two PM-facing route groups:
  - project-scoped workflow routes under `/api/projects/{project_id}/workflow`
  - PM write routes under `/api/pm`
- The workflow service layer enforces business rules such as blocked direct status mutation, stale-version rejection, and audit persistence requirements.
- The persistence layer is `WorkflowStore`, which currently reads and writes workflow records through dopecon-bridge custom-data APIs.

## Intended use

- Canonical workflow authority for:
  - workflow legality
  - blockers
  - next action
  - workflow-significant transitions
  - Stage-1 / Stage-2 idea-to-epic progression
- Not intended to be the canonical PM entity store.
- Not intended to be the durable decision/progress/context authority.

## Important runtime fact

- The current project-scoped transition route exists but still returns an explicit unavailable receipt with the reason `project-scoped workflow transition is not yet backed by a canonical runtime binding`.
- This means the authority claim is directionally correct, but the project workflow transition HTTP surface is not yet fully bound to the canonical transition path.
