---
id: POST_PILOT_GO_NO_GO_CRITERIA
title: Post Pilot Go No Go Criteria
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Post Pilot Go No Go Criteria (explanation) for dopemux documentation and
  developer workflows.
---
# Post-Pilot Go/No-Go Criteria

Superseded by [`operator-contract.md`](./operator-contract.md).

This file previously defined `GO_PACKAGE_ONLY`, `GO_DRAFT_FIRST`,
`GO_SUPERVISED_FINAL_CREATION`, `NO_GO_LIMIT_TO_ARTIFACTS_ONLY`, and
`ROLLBACK_TO_HUMAN_PREP` as current, reachable governance outcomes of a
historical TP-PRPS-007/008 pilot evaluation, gated on quality bands such as
`TRUSTWORTHY`, `HIGH_SIGNAL`, and `HIGHLY_USEFUL`. Those bands are
evaluation-quality metrics for that historical pilot, not PR risk or
creation authority, and the `GO_*` / `NO_GO_*` / `ROLLBACK_*` outcomes are
retired as current governing states.

Current PR-creation posture has exactly one default (`DRAFT_ONLY`) and one
escalation path (explicit operator/Task Packet authorization), defined in
`operator-contract.md` §S4. Current PR risk uses the `L0-L3` risk lanes
(§4), not a pilot-readiness quality-band matrix. There is no current
`GO_SUPERVISED_FINAL_CREATION` state that grants independent non-draft or
merge-ready PR creation.

This stub is kept only so existing links into this filename keep resolving.
