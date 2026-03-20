---
id: SIGNOFF_TRIGGER_RULES
title: Signoff Trigger Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Signoff Trigger Rules (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Signoff Trigger Rules

## Exactly When a SignoffPacket Fires

A `SignoffPacket` is emitted when ALL of the following are true:
1. Verification passed (`verification.status == "PASSED"`)
2. Gate decision is `PENDING_SIGNOFF` (not `DEFER` or `APPROVED`)
3. `DeferPacket` would NOT be emitted (mutual exclusion)

## Specific Conditions That Trigger Signoff

| Condition | Trigger Reason |
|-----------|----------------|
| `patch_class == SIGNOFF_REQUIRED_PATCH` | Policy mandates signoff for this class |
| `risk_class in {MEDIUM, HIGH}` AND verify passed | Risk level exceeds auto-apply threshold |
| Apply outcome == `STAGED` | Patch was not auto-applied; needs operator action |
| Posture is `HOLD` or `CAUTION` after apply | Posture gate still active even after verify pass |

## SignoffPacket Contents

| Field | Value |
|-------|-------|
| `packet_id` | UUID4 |
| `patch_id` | From originating PatchPlan |
| `trigger_reason` | Human-readable reason from gate |
| `patch_class` | From PatchPlan.patch_class.value |
| `risk_class` | From PatchPlan.scope.risk_class |
| `verification_outcome` | PASSED (always — defer fires on FAILED) |
| `owner` | "operator" (default) |
| `state` | "PENDING_SIGNOFF" |

## What Happens After Signoff Is Emitted

1. `FusionTrace.signoff_packet` is populated
2. `SIGNOFF_TRIGGER_REPORT.json` artifact is written
3. Loop terminates for this cycle (operator action required)
4. Operator must acknowledge packet before next apply attempt

## Invariant

`SignoffPacket` is NEVER emitted simultaneously with `DeferPacket`.
If both conditions would trigger, `DeferPacket` takes precedence and `SignoffPacket`
is set to None (defer wins on uncertainty).
