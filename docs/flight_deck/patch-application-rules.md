---
id: PATCH_APPLICATION_RULES
title: Patch Application Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Patch Application Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Patch Application Rules

## Apply Rules by Patch Class

| Patch Class | Apply Condition | Outcome on Allow | Outcome on Block |
|-------------|----------------|------------------|------------------|
| DISALLOWED_PATCH | Never | — | BLOCKED (immediate) |
| SAFE_LOCAL_EDIT | APPLY_FIX in allowed_actions AND posture in GO_* | APPLIED | STAGED |
| SAFE_METADATA_EDIT | APPLY_FIX in allowed_actions AND posture in GO_* | APPLIED | STAGED |
| LOW_RISK_PATCH_PROPOSAL | APPLY_FIX in allowed_actions AND posture in GO_* | APPLIED | STAGED |
| SIGNOFF_REQUIRED_PATCH | Never auto-applied | — | STAGED (always) |

## Posture Requirements

| Posture | Auto-Apply Permitted |
|---------|---------------------|
| HOLD | No |
| CAUTION | No |
| GO_SUPERVISED_ONLY | Yes (for SAFE classes only) |
| GO_FULL_AUTO | Yes (for all non-SIGNOFF classes) |

## Signoff Gate Conditions

A `SignoffPacket` is emitted (blocking apply) when:
1. `patch_class == SIGNOFF_REQUIRED_PATCH` (always)
2. `risk_class in {MEDIUM, HIGH}` AND verification passed AND posture is still gated
3. Gate decision is `PENDING_SIGNOFF` (posture HOLD or CAUTION after apply)

## Outcome Definitions

| Outcome | Meaning |
|---------|---------|
| APPLIED | Patch was applied; verification required next |
| STAGED | Patch is queued; awaiting signoff or posture change |
| BLOCKED | Patch class or policy prevents any application |
| FAILED | Internal error during apply attempt |

## Invariants

1. A DISALLOWED_PATCH NEVER transitions to APPLIED.
2. A SIGNOFF_REQUIRED_PATCH NEVER auto-applies, regardless of posture.
3. All APPLIED patches trigger verification (verification_required = True).
4. All STAGED patches generate a verification_plan_id for future linkage.
