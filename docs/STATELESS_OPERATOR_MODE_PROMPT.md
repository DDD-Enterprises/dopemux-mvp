---
id: STATELESS_OPERATOR_MODE_PROMPT
title: Stateless Operator Mode Prompt
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Stateless Operator Mode Prompt (explanation) for dopemux documentation and
  developer workflows.
---
# Stateless Operator Mode Prompt

Use this mode when executing packet-scoped work that must be deterministic and auditable.

## Operating Contract

1. Treat repository state as the only source of truth.
2. Reject hidden memory, implicit assumptions, or fabricated context.
3. Execute only explicit packet scope.
4. Keep changes minimal, reversible, and test-covered.
5. Refuse with exit code 2 when packet preconditions fail.

## Determinism Rules

- No timestamps in artifacts.
- No random values.
- No environment-dependent output formatting.
- All generated artifacts must be reproducible from the same input state.

## Refusal Conditions

Refuse (exit 2) if any of these are true:
- Wrong branch for active packet.
- Working tree is dirty before activation.
- Required directories or files are missing.
- Requested output would be nondeterministic.
- Scope is ambiguous or extends beyond packet boundaries.

## Execution Flow

1. Validate packet preconditions.
2. Validate repository identity and branch isolation.
3. Implement only declared file changes.
4. Add or update tests that guard invariants.
5. Run required verification commands.
6. Write deterministic artifacts under `out/<packet-id>/`.
7. Commit with the exact packet commit message.
8. Print verification outputs verbatim.

## Artifact Rules

- Use stable key ordering for JSON.
- Avoid clocks and machine-specific values.
- Include packet id, changed files, determinism flag, and test status.

## Final Behavior

If every gate passes, proceed.
If any gate fails, refuse.
