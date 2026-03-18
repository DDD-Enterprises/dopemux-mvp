---
id: EDIT_VERIFY_GATE_SIGNOFF_MODEL
title: Edit Verify Gate Signoff Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Edit Verify Gate Signoff Model (explanation) for dopemux documentation and
  developer workflows.
---
# Edit-Verify-Gate-Signoff Model

## Overview

The end-to-end model for code editing in the flight deck is a 4-stage pipeline.
Every edit traverses all 4 stages. No stage can be skipped.

## 4-Stage Pipeline

```
┌─────────┐    ┌────────┐    ┌──────┐    ┌──────────────────┐
│  EDIT   │───►│ VERIFY │───►│ GATE │───►│ SIGNOFF or DEFER │
└─────────┘    └────────┘    └──────┘    └──────────────────┘
```

### Stage 1: EDIT
- `PatchEngine.plan_patch()` constructs patch with provenance
- `PatchEngine.classify_patch()` assigns patch class
- `PatchEngine.apply_patch()` executes conditional apply
- Output: `PatchApplicationTrace` with outcome

### Stage 2: VERIFY
- `FusionEngine.run_verification()` determines required checks from patch class
- Checks run against actual or simulated CI
- Output: `{status: PASSED|FAILED, checks: [...], passed: bool}`

### Stage 3: GATE
- `FusionEngine.recompute_gate()` integrates verify result + posture
- Gate decisions: `APPROVED`, `PENDING_SIGNOFF`, `DEFER`
- Output: `{decision, signoff_required, defer_required, reason}`

### Stage 4: SIGNOFF or DEFER
- If `signoff_required`: `SignoffPacket` emitted → operator reviews
- If `defer_required`: `DeferPacket` emitted → blocker captured
- If `APPROVED`: cycle completes cleanly
- Output: `FusionTrace` with all stage outcomes

## Pipeline Invariants

1. **No skip gate**: Every patch traverses EDIT → VERIFY → GATE → SIGNOFF/DEFER.
2. **Fail-closed**: Any unhandled exception in any stage produces a DEFER packet.
3. **Mutual exclusion**: `SignoffPacket` and `DeferPacket` are never both non-None simultaneously.
4. **Provenance chain**: All stages share the same `patch_id` and `trace_id`.
5. **Recompute required**: Gate always re-evaluates posture after verification; cached posture is not trusted.

## Gate Recompute Triggers

The gate recomputes posture after:
- Verification PASSED
- Verification FAILED
- Apply outcome is BLOCKED or FAILED
- Apply outcome is STAGED (awaiting signoff)
- Internal error (→ DEFER)
