---
id: LIVE_PILOT_PROTOCOL
title: Live Pilot Protocol
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Live Pilot Protocol for pr-prep-specialist operational testing.
---
# Live Pilot Protocol

Superseded by [`operator-contract.md`](./operator-contract.md) §3
(Hard boundaries) and §5 (S4 - Draft or verify PR metadata).

This file previously documented a historical `TP-PRPS-007` pilot with three
modes (`PACKAGE_ONLY`, `DRAFT_FIRST`, `SUPERVISED_FINAL_CREATION`), the
last of which let the specialist create non-draft PRs once an operator
approved the action in the loop. `SUPERVISED_FINAL_CREATION` as a
current PR-prep capability is retired: the specialist has no non-draft
creation mode of its own to graduate into. Under the V2 contract, PR
creation is always `DRAFT_ONLY` by default, and any non-draft creation or
update requires explicit operator or Task Packet authorization on a
per-action basis, not a pilot-earned capability tier.

This stub is kept only so existing links into this filename keep resolving.
