---
id: CLOSED_LOOP_MODEL
title: Closed Loop Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Closed Loop Model (explanation) for dopemux documentation and developer workflows.
---
# Closed-Loop Model

## Overview

The flight deck operates as an 8-stage closed-loop control system. Each cycle refreshes
mission state, selects the next safe tactic, and emits audit artifacts before returning
control to the operator surface.

## 8-Stage Lifecycle

| Stage | Name | Description |
|-------|------|-------------|
| 1 | INTAKE | Receive PR identifier and current mission context |
| 2 | REFRESH | Reload posture, blockers, and artifact TTL state |
| 3 | RECOMPUTE | Derive allowed_actions from current posture + blocker set |
| 4 | SELECT | Apply tactic priority ordering; fail-closed to DEFER |
| 5 | STAGE | Conditionally-implicit actions fire; all others await operator |
| 6 | VERIFY | Verification burden matched to patch class |
| 7 | GATE | Gate recompute after verify; signoff or defer surfaces |
| 8 | EMIT | Write audit trace artifacts; update monitoring health |

## Action Taxonomy

### Always-Implicit (fire automatically, no operator staging required)
- `REFRESH_STATE` — reload mission posture and artifact TTLs
- `SELECT_TACTIC` — compute next safe tactic
- `RECOMPUTE_SUMMARY` — update posture/blockers after any meaningful event

### Conditionally-Implicit (fire automatically only when posture permits)
- `APPLY_FIX` (SAFE_LOCAL_EDIT, SAFE_METADATA_EDIT) — when posture is GO_SUPERVISED_ONLY or GO_FULL_AUTO and `APPLY_FIX` is in allowed_actions
- `REQUEST_REVIEW` — when checks pass and review is the priority action

### Never-Implicit (always require operator staging)
- `MERGE` — requires signoff regardless of posture
- `APPROVE` — requires operator confirmation
- `SIGNOFF_REQUIRED_PATCH` application — always staged, never auto-applied
- `CLOSE` — requires explicit operator instruction

## Loop Termination Conditions

The loop terminates when any of the following are true:
1. `next_tactic == "DEFER"` and defer packet is emitted
2. Signoff packet is pending and awaiting operator
3. An internal error produces a FAILED trace (fail-closed invariant)
4. PR reaches terminal state: `merged`, `closed`
