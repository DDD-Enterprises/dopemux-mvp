---
name: task-breakdown
description: Break a workflow brief into manager-valid task mirrors while respecting Dopemux PM authority boundaries.
---

# Task Breakdown

Use this skill after the brief is accepted and before research starts.

## Contract

- Use Dopemux PM authority when reachable.
- When PM is unavailable, create temporary local task mirrors only. Do not pretend they are canonical.
- Keep tasks independently executable by a single workflow executor.
- Record task ids, required artifacts, and verification expectations up front.

## Required Output

- Ordered task list with ids
- Ownership and authority source
- Required artifacts per task
- Verification commands or verification placeholders

## Completion Rule

Emit:

```xml
<workflow-checkpoint phase="breakdown" status="complete" task="task-001" summary="Task mirror created" artifact="/abs/path/tasks/task-001/task.md" />
```

## Stop Protocol (Orchestrator Enforcement)

- **CRITICAL**: You are executing a SINGLE PHASE of a larger orchestrated loop.
- Once you emit the `<workflow-checkpoint>` XML, you MUST yield control back to the orchestrator.
- Do NOT proceed to the next phase (e.g., research, plan, implement). 
- End your response with `[STOP_TURN]` to explicitly signal phase completion.
