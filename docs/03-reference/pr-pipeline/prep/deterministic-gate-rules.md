---
id: DETERMINISTIC_GATE_RULES
title: Deterministic Gate Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Deterministic Gate Rules for pr-prep-specialist layered validation.
---
# Deterministic Gate Rules

Folded into [`operator-contract.md`](./operator-contract.md) §5 (S3 -
Deterministic pre-push gate).

The gate categories previously enumerated here — `WORKTREE_CLEANLINESS`,
`PRECOMMIT`, `LINT/TYPECHECK/TARGETED_TESTS`, `TEMPLATE_SUFFICIENCY`,
`DOCS_PRESENCE`, `CHANGELOG_PRESENCE`, `MIGRATION_NOTE_PRESENCE`,
`LINKED_CONTEXT_SUFFICIENCY` — remain valid checks; S3 supersedes the
free-standing `PASS/FAIL/PARTIAL/NOT_RUN` gate taxonomy and blocker-decision
vocabulary this file used to define, folding them into the canonical
pre-push gate and the prep states (§6) in the canonical contract.

This stub is kept only so existing links into this filename keep resolving.
