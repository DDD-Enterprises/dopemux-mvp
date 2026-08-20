---
id: HANDOFF_CONTRACT
title: Handoff Contract
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Handoff Contract for pr-prep-specialist to pr-merge-specialist handoff.
---
# Handoff Contract

Superseded by [`operator-contract.md`](./operator-contract.md) §9 (Handoff V2)
and [`handoff-to-prms-contract.md`](./handoff-to-prms-contract.md).

This file previously documented a third, competing handoff schema (a
`risk_hint: LOW|MEDIUM|HIGH|CRITICAL` field and a
`MERGE_SPECIALIST_NORMAL_FLOW|MERGE_SPECIALIST_DRAFT_FLOW|MERGE_SPECIALIST_HIGH_RISK_AWARE_FLOW|NO_HANDOFF_BLOCKED`
next-step enum) alongside the one in `handoff-to-prms-contract.md`. Both are
superseded by the single `schema_version: "2.0.0"` handoff bundle in the
canonical contract, which uses `risk_lane: L0|L1|L2|L3` in place of
`risk_hint`.

This stub is kept only so existing links into this filename keep resolving.
