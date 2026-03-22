---
name: code-implementer
description: Execute an approved workflow plan, produce implementation artifacts, and run the declared verification commands.
---

# Code Implementer

Use this skill only after `plan_review` is approved.

## Contract

- Implement only the active task and only the approved plan.
- Explain the next move before edits or command execution.
- Record what changed, what was verified, and what remains risky.
- If verification fails, stop and emit a blocker instead of guessing.

## Required Output

- Code changes limited to the active task scope
- `implementation-notes.md`
- Verification output or failure summary

## Completion Rule

Emit one of:

```xml
<workflow-checkpoint phase="implement" status="complete" task="task-001" summary="Implementation complete" artifact="/abs/path/implementation-notes.md" verification="pytest -q" />
```

```xml
<workflow-checkpoint phase="implement" status="blocked" task="task-001" summary="Implementation blocked by failing verification" artifact="/abs/path/implementation-notes.md" verification="pytest -q" />
```

## Stop Protocol (Orchestrator Enforcement)

- **CRITICAL**: You are executing a SINGLE PHASE of a larger orchestrated loop.
- Once you emit the `<workflow-checkpoint>` XML (whether complete or blocked), you MUST yield control back to the orchestrator.
- Do NOT proceed to the next phase (e.g., refactor, review).
- End your response with `[STOP_TURN]` to explicitly signal phase completion.
