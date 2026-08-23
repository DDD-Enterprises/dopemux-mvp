---
id: HIGH_RISK_HANDOFF_RULES
title: High Risk Handoff Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Rules for handling high-risk branches during PR handoff.
---
# High Risk Handoff Rules

Superseded by [`operator-contract.md`](./operator-contract.md) §8 (High-risk handoff).

The `HIGH_RISK_HANDOFF_REQUIRED` decision and `HIGH` risk-hint vocabulary
previously documented here have been replaced by `risk_lane: L3_RED` (§4).
The fixed `recommended_next_step: MERGE_SPECIALIST_HIGH_RISK_AWARE_FLOW`
token (and its siblings `MERGE_SPECIALIST_NORMAL_FLOW`,
`MERGE_SPECIALIST_DRAFT_FLOW`, `NO_HANDOFF_BLOCKED`) is retired —
`pr-merge-specialist` derives handling from `risk_lane`, `governing_posture`,
and `pr_steward` in the V2 handoff bundle (§9), not from a PRPS-dictated
flow enum. Creation posture, warning preservation, and PR-body integration
notes for high-risk branches are defined in §8.

This stub is kept only so existing links into this filename keep resolving.
