---
id: runbook-bootstrap
title: DevOps AutoPR Bootstrap Runbook
type: how-to
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Bootstrap runbook for starting a governance-bound optimized development workflow packet.
---
# DevOps AutoPR Bootstrap Runbook

## Steps

1. Run repo identity checks: `pwd`, `git remote -v`, `git status --short`, `git branch --show-current`, and `test -f .dopetaskroot`.
2. Confirm the strict task-packet schema at `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`.
3. Read `AGENTS.md`, active task packet, and relevant repo governance docs before editing.
4. Create or switch to a scoped branch/worktree before modifications.
5. Validate the task packet JSON before implementing the first file edit.
6. Keep edits inside `commit.allowlist`; stop if additional files are needed.
7. Run the smallest relevant validation after each meaningful slice.
8. Run embedded audit when required and write the auditor report into proof.

## Stop Conditions

Stop if repo identity, branch identity, schema path, auditor invocation, or scope boundary is unclear. Record `UNKNOWN` rather than filling gaps with inference.
