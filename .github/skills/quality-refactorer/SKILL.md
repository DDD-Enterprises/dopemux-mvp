---
name: quality-refactorer
description: Harden a completed implementation with bounded cleanup, verification reruns, and final task-quality notes.
---

# Quality Refactorer

Use this skill after implementation is complete and before the manager closes the task.

## Contract

- Keep refactors bounded to clarity, maintainability, and risk reduction.
- Do not widen scope or change behavior without evidence and verification.
- Re-run declared verification commands after refactor work.
- Capture any residual risk so the manager can decide whether the task is truly done.

## Required Output

- `refactor.md`
- Refactor summary
- Re-run verification results
- Residual risks or follow-up notes

## Completion Rule

Emit:

```xml
<workflow-checkpoint phase="refactor" status="complete" task="task-001" summary="Refactor and verification complete" artifact="/abs/path/refactor.md" verification="pytest -q;;ruff check src" />
```
