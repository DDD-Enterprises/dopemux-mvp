---
id: FINAL_PREP_DECISION_MODEL
title: Final Prep Decision Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-11'
last_review: '2026-08-11'
next_review: '2026-11-09'
prelude: Final Prep Decision Model for pr-prep-specialist validation.
---
# Final Prep Decision Model

Superseded by [`operator-contract.md`](./operator-contract.md) §6 (Prep
states).

This file previously defined `CREATE_READY`, `DRAFT_RECOMMENDED`, and a
family of `BLOCKED_*` / `HIGH_RISK_HANDOFF_REQUIRED` codes as the current
governing synthesis of the prep decision, written to `FINAL_PREP_DECISION.json`.
Those states are retired.

The current prep state is exactly one of the eight states in
`operator-contract.md` §6 (`PREP_BLOCKED`, `PREP_NEEDS_IMPLEMENTER`,
`PREP_NEEDS_SUPERVISOR`, `PREP_COMPLETE_AWAITING_AUDIT`,
`PREP_COMPLETE_AWAITING_PROOF`, `PREP_COMPLETE_AWAITING_CI`,
`PREP_COMPLETE_AWAITING_STEWARD`, `PREP_READY_FOR_OPERATOR_DECISION`),
derived from the conditional S0-S8 workflow (§5) and reported in the V2
handoff bundle (§9), not from a bespoke `FINAL_PREP_DECISION.json` synthesis
document. `PREP_READY_FOR_OPERATOR_DECISION` never implies merge authority.

This stub is kept only so existing links into this filename keep resolving.
