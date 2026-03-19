---
id: LOOP_FUSION_POLICY
title: Loop Fusion Policy
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Loop Fusion Policy (explanation) for dopemux documentation and developer
  workflows.
---
# ━━━◆ Ø ◆━━━

Status: [LOGGED] Flight deck reference

## Loop Fusion Policy

## Fail-Closed Invariant

The loop fusion pipeline is designed to fail closed. This means:
1. Any unhandled exception in any stage produces a `DeferPacket` with `INTERNAL_ERROR`.
2. No patch can reach an APPLIED state if any upstream stage failed.
3. A missing or invalid verification result defaults to `FAILED` (not `PASSED`).

## No-Skip Gate Rule

No patch path can skip the gate recompute after verification:
- Gate always runs after VERIFY completes (pass or fail).
- Gate result always produces either `APPROVED`, `PENDING_SIGNOFF`, or `DEFER`.
- There is no path from VERIFY directly to a terminal state.

## All Transitions Are Traced

Every stage transition in the fusion pipeline is recorded in `FusionTrace.stages`:
```
[
  {stage: "VERIFY",           outcome: "STARTED",       timestamp: ...},
  {stage: "VERIFY",           outcome: "PASSED|FAILED",  timestamp: ...},
  {stage: "GATE",             outcome: "STARTED",        timestamp: ...},
  {stage: "GATE",             outcome: "decision",       timestamp: ...},
  {stage: "SIGNOFF_OR_DEFER", outcome: "STARTED",        timestamp: ...},
  {stage: "SIGNOFF_OR_DEFER", outcome: "outcome",        timestamp: ...},
  {stage: "FINAL_STATE",      outcome: "COMPLETE",       timestamp: ...},
]
```

On error: `{stage: "ERROR", outcome: "INTERNAL_ERROR", timestamp: ...}` is appended.

## Mutual Exclusion Invariant

`SignoffPacket` and `DeferPacket` are never simultaneously non-None in a `FusionTrace`.
If both conditions trigger, `DeferPacket` wins and `SignoffPacket` is set to None.

## Artifact Completeness

Every `fuse()` call writes exactly 5 artifact files (via `emit_fusion_artifacts()`):
1. `LOOP_FUSION_TRACE.json` — full trace with all stages
2. `VERIFICATION_GATE_REPORT.json` — VERIFY + GATE stage outcomes
3. `SIGNOFF_TRIGGER_REPORT.json` — signoff packet or null
4. `DEFER_TRIGGER_REPORT.json` — defer packet or null
5. `POST_EDIT_STATE_RECOMPUTE.json` — final state after gate

If any artifact write fails, the failure is logged but does not block the pipeline.

## Closed-Loop Linkage

The fusion pipeline feeds directly into the closed-loop engine:
1. `ClosedLoopEngine.run_cycle()` selects tactic
2. If tactic is `APPLY_FIX`: `PatchEngine` plans and applies
3. `FusionEngine.fuse()` verifies, gates, and surfaces signoff/defer
4. `ClosedLoopEngine.recompute_summary()` updates state with fusion outcome
5. `emit_trace_artifacts()` writes the cycle-level audit record
