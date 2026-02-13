---
id: THREAD_PRIMER_TASKX
title: Thread Primer Taskx
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Thread Primer Taskx (explanation) for dopemux documentation and developer
  workflows.
---
# TaskX Thread Primer

This file allows deterministic restart of development in a fresh chat.

Before proceeding in any new thread:

1. Read:
   - docs/STATELESS_OPERATOR_MODE_PROMPT.md
   - docs/EXECUTIVE_INVARIANTS_1PAGER.md
2. Confirm:
   - Current branch
   - Working tree clean
   - Active packet ID
3. Confirm refusal semantics (exit code 2)

System summary:

TaskX is a deterministic CLI implementing:

Planes:
- Lifecycle (compile/run/evidence/gate/commit/finish)
- Project stabilization (shell + upgrade)
- Assisted routing (taskx route)
- Assisted PR flow (taskx pr open)
- LLM contract autogen (taskx docs refresh-llm)

All features:
- Deterministic
- Idempotent
- Refusal-driven
- Artifact-writing under out/*
- Test-covered

If scope is ambiguous -> refuse.
If branch isolation violated -> refuse.
If determinism at risk -> refuse.

Proceed only in deterministic assisted mode.
