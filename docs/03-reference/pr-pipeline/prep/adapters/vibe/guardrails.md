---
id: GUARDRAILS
title: Guardrails
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Guardrails (explanation) for dopemux documentation and developer workflows.
---
# Vibe Adapter Guardrails for PR-Prep-Specialist

Superseded by [`operator-contract.md`](../../operator-contract.md) §3 (Hard
boundaries) and §5 (Conditional workflow).

This file previously enumerated a `PACKAGE_ONLY → DRAFT_FIRST →
SUPERVISED_FINAL` posture progression, a fixed six-checkpoint sequence with
mandatory `BRANCH_STATE.json`/`PR_HANDOFF_BUNDLE.json`-style artifacts per
checkpoint, and violation files named after that ceremony. That posture
model and fixed artifact ceremony are retired.

The current guardrails are the operator contract's hard boundaries (§3: no
merge, no force push, no history rewrite, no branch deletion, no
credential/permission/signer changes, no invented audit/test/CI/proof
state without explicit operator authority) and its conditional S0-S8
workflow (§5). Default PR creation posture is `DRAFT_ONLY` (§S4); there is
no `SUPERVISED_FINAL` state that grants independent non-draft or
merge-ready PR creation.

Vibe-specific plan-mode text-only staging and operator-review-before-proceed
conventions may remain as invocation style, but they defer their decision
vocabulary and consequences to `operator-contract.md` — they do not define
a competing guardrail model.

This stub is kept only so existing links into this filename keep resolving.
