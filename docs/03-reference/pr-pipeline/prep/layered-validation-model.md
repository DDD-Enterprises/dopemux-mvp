---
id: LAYERED_VALIDATION_MODEL
title: Layered Validation Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Layered Validation Model (explanation) for dopemux documentation and developer
  workflows.
---
# Layered Validation Model

Superseded by [`operator-contract.md`](./operator-contract.md) §5
(S2 - Obligations and risk; S3 - Deterministic pre-push gate) and §6
(Prep states).

This file previously defined a two-layer gate (deterministic local checks,
then a conditional consensus gate triggered by a `HIGH_RISK_ESCALATE` flag)
producing one of six final decision states: `CLEAN_CREATE_READY`,
`DRAFT_RECOMMENDED`, `BLOCKED_MISSING_DOCS`, `BLOCKED_MISSING_CHANGELOG`,
`BLOCKED_VERIFICATION_GAP`, `BLOCKED_ADJACENT_WORK_AMBIGUITY`,
`HIGH_RISK_HANDOFF_REQUIRED`. That state machine, its consensus-gate
trigger, and its risk-hint escalation flag are retired. The canonical
contract's deterministic pre-push gate (§5 S3) and eight prep states (§6)
supersede it; risk is expressed via `L0-L3` risk lanes (§4), not a
`HIGH_RISK_ESCALATE` flag.

This stub is kept only so existing links into this filename keep resolving.
