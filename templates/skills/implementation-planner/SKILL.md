---
name: implementation-planner
description: Convert approved research into an implementation plan with explicit steps and verification commands.
---

# Implementation Planner

Use this skill only after `research_review` is approved.

## Contract

- Build on approved research instead of re-discovering facts.
- Write ordered steps that a single executor can follow without hidden context.
- Include exact verification commands for each meaningful code change.
- Do not implement code in this phase.

## Required Output

- `plan.md`
- Ordered execution steps
- File targets and dependency notes
- Verification commands

## Completion Rule

Emit:

```xml
<workflow-checkpoint phase="plan" status="complete" task="task-001" summary="Plan drafted" artifact="/abs/path/plan.md" verification="pytest -q tests/test_workflow_service.py" />
```

## Stop Protocol (Orchestrator Enforcement)

- **CRITICAL**: You are executing a SINGLE PHASE of a larger orchestrated loop.
- Once you emit the `<workflow-checkpoint>` XML, you MUST yield control back to the orchestrator.
- Do NOT proceed to the next phase (e.g., implement). 
- End your response with `[STOP_TURN]` to explicitly signal phase completion.
