---
id: task_orchestrator_runtime_truth_workflow_gates
title: Task Orchestrator Runtime Truth Workflow and Gates
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Runtime workflow constraints and fail-closed gates enforced by Task Orchestrator service code and tests.
---
# Task Orchestrator - Workflow and Gates

## Enforced gates

Evidence from `services/task-orchestrator/app/services/workflow_service.py` and `services/task-orchestrator/tests/test_workflow.py`:

- direct status mutation is blocked; callers must use transition APIs
- stale version updates are rejected
- conflicting linked-ID overwrite fails closed
- failed workflow transition audit persistence aborts promotion

## Transition gate

- The project-scoped transition route currently emits an explicit unavailable receipt instead of executing a canonical transition.
- This is a fail-closed behavior, not a permissive fallback.

## Idempotency / audit

- ideas and epics support idempotency keys
- transition audit records are required for durable workflow progression
- workflow versioning is part of the conflict gate
