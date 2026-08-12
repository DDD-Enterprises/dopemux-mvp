---
id: BRANCH_STATE_SCHEMA
title: Branch State Schema
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Branch State Schema (explanation) for dopemux documentation and developer
  workflows.
---
# Branch State Schema

Superseded by [`operator-contract.md`](./operator-contract.md) §4 (Risk lanes)
and §9 (Handoff V2).

This file previously defined a standalone `BRANCH_STATE.json` schema keyed on
a `risk_hint: LOW|MEDIUM|HIGH|UNKNOWN` enum, as part of the legacy fixed
seven-artifact ceremony. That ceremony and its `risk_hint` field are retired.
Custody, drift, and overlap state are now captured directly in the conditional
S0-S8 workflow (§5) and the `risk_lane: L0|L1|L2|L3` field of the V2 handoff
bundle (§9), not in a separately maintained schema document.

This stub is kept only so existing links into this filename keep resolving.
