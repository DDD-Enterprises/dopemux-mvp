---
id: TP-RTE-S7-DRIFT-FIX-001
title: Verify S7 Drift Gate — Confirm FAIL on Injected Stale Step
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-06'
status: READY_FOR_REVIEW
prelude: Verify-first / conditional-fix packet for the RTE S7 truth-split gate. Prior docs claimed S7 was an "always-PASS stub." Evidence-gate verification (TP-DMX-EVIDENCE-GATE-VERIFY-001) found the implementation present. This packet proves the gate actually fails under injected stale drift.
---
# Task Packet: TP-RTE-S7-DRIFT-FIX-001 · Development Factory · Verify S7 Drift Gate

════════════════════════════════════════════════════════════

## Objective

Verify that `collect_truth_split()` in `validate_pre_live_gate_v25.py` returns `FAIL` when a runner step is not registered in the declared model map (injected stale drift). If drift → FAIL: close with proof (VERIFY_AND_CLOSE). If drift → PASS: fix only the S7 gate path + tests. If call path or fixture format unclear: stop and return evidence.

────────────────────────────────────────────────────────────

## Why This Packet Exists Now

`TP-DMX-DDF-DOCS-CORRECT-001` reframed S7 from "always-PASS stub, must fix" → "implementation present at HEAD, verify-and-close." This packet is the verify step: exercise the gate against injected drift and confirm FAIL with the correct blocker and classification.

The prior docs claim that caused this:
> "S7 `collect_truth_split` is an always-PASS stub; the gate never rejects stale steps."

Evidence-gate verification found `collect_truth_split` builds rows, classifies, and emits blockers into `all_blockers` — the stub claim was stale. The hardcoded `runner_active=True` / `prompt_resolution_active=True` in the collection loop means `STALE_RUNNER_REGISTRY` and `STALE_PROMPTSET` are unreachable via the loop (dead branches), but `STALE_MODEL_MAP` is fully reachable when a step_id is absent from `model_map_declared_step_keys()`.

────────────────────────────────────────────────────────────

## Outcome

**VERIFY_AND_CLOSE** — drift → FAIL confirmed.

`test_collect_truth_split_fails_for_stale_drift_step` injected a FakeRunner returning `step_id="FAKE_STALE_STEP"` (not in MODEL_MAP_PATH yaml) into phase "A". `collect_truth_split()` returned:

- `payload["status"] == "FAIL"` ✅
- `blockers[0].reason_code == TARGET_TRUTH_SPLIT_MISMATCH` ✅
- `payload["rows"][0]["classification"] == "STALE_MODEL_MAP"` ✅
- `payload["target_phase_mismatch_count"] >= 1` ✅

Full suite: **10 passed / 0 failed** (9 existing + 1 new) in 0.52s.

No runtime code change was required. The S7 gate is correct.

────────────────────────────────────────────────────────────

## Scope

IN (modified + created):

* `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py` — added `test_collect_truth_split_fails_for_stale_drift_step`
* `task-packets/development-factory/TP-RTE-S7-DRIFT-FIX-001.md` (this file)
* `proof/TP-RTE-S7-DRIFT-FIX-001/PROOF.json`
* `proof/TP-RTE-S7-DRIFT-FIX-001/SUMMARY.md`

OUT (not touched):

* `services/repo-truth-extractor/validate_pre_live_gate_v25.py` — implementation correct; no changes
* Runtime code, schemas, `config/`, `.github/workflows/`
* Task-Orchestrator / Dopetask / ConPort / dope-memory / dope-context / dopecon-bridge state
* GitHub state, merge automation
* `queue_drain.py`, `scripts/batch_resolve_and_merge.py`

────────────────────────────────────────────────────────────

## Invariants

* Test-only change. No runtime code, schema, or config touched.
* No service/task/proof-policy/GitHub state changed.
* No secrets printed.
* `queue_drain.py` / `batch_resolve_and_merge.py` not touched, imported, or executed.
* Dead branches (`STALE_RUNNER_REGISTRY`, `STALE_PROMPTSET` via loop) documented as remaining uncertainty, not fixed.

────────────────────────────────────────────────────────────

## What Was Verified

1. **`classify_truth_split_row()`** (line 174): correctly returns `STALE_MODEL_MAP` when `prompt_resolution_active=True` and `model_map_declared=False`.
2. **`collect_truth_split()`** (line 523): correctly appends `Blocker(TARGET_TRUTH_SPLIT_MISMATCH, ...)` for any non-MATCH classification and returns `"status": "FAIL"` when blockers exist.
3. **`model_map_declared_step_keys()`** (line 507): reads MODEL_MAP_PATH yaml; a step_id absent from that file yields `model_map_declared=False`.
4. **Hardcoded flags in loop**: `runner_active=True` and `prompt_resolution_active=True` are hardcoded in `collect_truth_split`'s loop → `STALE_RUNNER_REGISTRY` and `STALE_PROMPTSET` are dead branches via the loop path. Documented as remaining uncertainty. Not fixed (separate concern, no observable correctness impact on the reachable path).

────────────────────────────────────────────────────────────

## Commands Run

```bash
python -m pytest -v services/repo-truth-extractor/tests/test_pre_live_gate_v25.py
# 10 passed in 0.52s
```

────────────────────────────────────────────────────────────

## Acceptance Criteria

* `collect_truth_split()` returns FAIL when injected drift step is absent from model map. ✅
* New test asserts status==FAIL, reason_code==TARGET_TRUTH_SPLIT_MISMATCH, classification==STALE_MODEL_MAP. ✅
* Full 10-test suite green (no regressions). ✅
* No runtime code touched. ✅
* Packet, PROOF.json, SUMMARY.md exist and validate. ✅

────────────────────────────────────────────────────────────

## Rollback

* `git checkout -- services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`
* `rm -rf task-packets/development-factory/TP-RTE-S7-DRIFT-FIX-001.md proof/TP-RTE-S7-DRIFT-FIX-001/`

────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STOP CONDITIONS (preserved — no stop triggered)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Would have stopped if: runtime code / schema / config changes required, call path or fixture format unclear with no convergence after 2 attempts, or evidence conflicted with described correction. None triggered.

## Next Recommended Packet

`TP-DMX-DCP-SEAM-LIFT-001` — wire existing `RedLaneScanner` executable into CI/steward (confirmed present, confirmed unwired per TP-DMX-EVIDENCE-GATE-VERIFY-001).
