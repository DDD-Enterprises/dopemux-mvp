---
id: DEFER_TRIGGER_RULES
title: Defer Trigger Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Defer Trigger Rules (explanation) for dopemux documentation and developer
  workflows.
---
# Defer Trigger Rules

## Exactly When a DeferPacket Fires

A `DeferPacket` is emitted when ANY of the following are true:

| Condition | Defer Reason |
|-----------|-------------|
| Verification failed (`verification.status == "FAILED"`) | `VERIFICATION_FAILED` |
| `patch_class == DISALLOWED_PATCH` | `POLICY_BLOCK` |
| Gate decision is `DEFER` and `defer_required == True` | `INSUFFICIENT_EVIDENCE` |
| Apply outcome is `BLOCKED` or `FAILED` | `INSUFFICIENT_EVIDENCE` |
| Internal exception in any pipeline stage | `INTERNAL_ERROR` |

## Defer Reason Taxonomy

| Reason | Meaning |
|--------|---------|
| `VERIFICATION_FAILED` | Required checks did not pass |
| `INSUFFICIENT_EVIDENCE` | Apply blocked or gate forced defer without enough evidence |
| `POLICY_BLOCK` | Patch class is DISALLOWED or invariant broken |
| `INTERNAL_ERROR` | Unhandled exception caught by fail-closed wrapper |

## DeferPacket Contents

| Field | Value |
|-------|-------|
| `packet_id` | UUID4 |
| `patch_id` | From originating PatchPlan (or "unknown" on early error) |
| `defer_reason` | One of the taxonomy values above |
| `blockers` | List of active blockers at time of defer |
| `created_at` | Unix timestamp |

## What Happens After Defer Is Emitted

1. `FusionTrace.defer_packet` is populated
2. `DEFER_TRIGGER_REPORT.json` artifact is written
3. Loop terminates for this cycle
4. Blocker list is preserved for next cycle's REFRESH

## Precedence Rule

When both SignoffPacket and DeferPacket conditions are met simultaneously:
- `DeferPacket` takes precedence
- `SignoffPacket` is set to None
- Rationale: defer is the more conservative outcome; fail-closed wins

## Invariant

A `DeferPacket` with `defer_reason == INTERNAL_ERROR` is ALWAYS emitted
when an unhandled exception propagates to the `FusionEngine.fuse()` method,
regardless of patch state or posture.
