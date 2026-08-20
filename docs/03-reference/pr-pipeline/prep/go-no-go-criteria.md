---
id: GO_NO_GO_CRITERIA
title: Go/No-Go Criteria
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Criteria for determining the operational posture of pr-prep-specialist.
---
# Go/No-Go Criteria

Superseded by [`operator-contract.md`](./operator-contract.md) §6 (Prep states) and §5 (S6 - Independent audit when required).

The `GO_SUPERVISED_FINAL_CREATION` / `GO_DRAFT_FIRST` / `GO_PACKAGE_ONLY` /
`NO_GO_LIMIT_TO_ARTIFACTS_ONLY` / `ROLLBACK_TO_HUMAN_PREP` decision bands
previously documented here — each keyed to quality-band aggregates like
`TRUSTWORTHY`, `READY_FOR_DOWNSTREAM_USE`, `HIGHLY_USEFUL` — have been
replaced by the eight prep states (`PREP_BLOCKED` through
`PREP_READY_FOR_OPERATOR_DECISION`) and the S6 audit-verdict gate
(`PASS`/`PASS_WITH_RISKS`/`FAIL`/`NEEDS_SUPERVISOR`/`SKIPPED`) in the
canonical contract. There is no autonomous "supervised final creation"
state — PR creation defaults to `DRAFT_ONLY` (§S4) and any escalation to
non-draft creation requires explicit operator/Task Packet authorization.

This stub is kept only so existing links into this filename keep resolving.
