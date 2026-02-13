---
id: DOPEMUX_CONTINUATION_PRIMER
title: Dopemux Continuation Primer
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Dopemux Continuation Primer (explanation) for dopemux documentation and developer
  workflows.
---
# Dopemux Continuation Primer

This primer is a deterministic restart rail for Dopemux work in a fresh thread.

## Start Sequence

1. Read repository governance:
   - `.claude/PROJECT_INSTRUCTIONS.md`
   - `.claude/PRIMER.md`
2. Read active packet and lock scope.
3. Verify branch, clean tree, and required directories.
4. Confirm refusal semantics (`exit 2`).

## Working Rules

- Evidence-first: claims must map to files or command output.
- Deterministic: avoid nondeterministic artifacts or behavior.
- Minimal diffs: change only what packet scope requires.
- Test-backed: add or run tests for every enforced invariant.
- Artifact-backed: write machine-readable packet outputs under `out/`.

## Default Command Rails

- `git status --porcelain`
- `git rev-parse --abbrev-ref HEAD`
- `pytest -q`

## Refusal Triggers

Refuse (exit 2) when:
- branch isolation is wrong
- worktree is dirty pre-activation
- packet requirements are missing or contradictory
- requested changes exceed packet scope
- determinism cannot be guaranteed

## Completion Contract

A packet is complete only when:
- required files exist with deterministic content
- tests pass
- required artifacts are written
- commit message matches packet text
- verification commands are executed and shown
