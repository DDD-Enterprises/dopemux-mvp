# Proof Summary — TP-RTE-S7-DRIFT-FIX-001

**Packet:** Verify S7 Drift Gate — Confirm FAIL on Injected Stale Step
**Branch:** `claude/hungry-lalande-e617d2`
**Head SHA (before):** `c6ed2ea5181f349b34a2e35c4146bb0c565f1b36`
**Commit SHA:** TBD_AFTER_COMMIT
**Authority input:** `TP-DMX-DDF-DOCS-CORRECT-001` + `TP-DMX-EVIDENCE-GATE-VERIFY-001` (read-only verification, HEAD `8042f9f9f`)
**Outcome:** VERIFY_AND_CLOSE — drift → FAIL confirmed
**Validation:** PASSED · **Status:** READY_FOR_REVIEW

## What Was Verified

The S7 truth-split gate (`collect_truth_split()` in `validate_pre_live_gate_v25.py`) correctly returns `FAIL` when a runner step is absent from the declared model map.

Prior docs claimed this was an "always-PASS stub." That claim was stale. The implementation is present and correct at HEAD.

## Test Added

`test_collect_truth_split_fails_for_stale_drift_step` in `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`:

- Injects `FakeRunner` returning `step_id="FAKE_STALE_STEP"` in phase "A"
- "FAKE_STALE_STEP" is absent from `model_map_declared_step_keys()` → `model_map_declared=False`
- `classify_truth_split_row()` returns `STALE_MODEL_MAP`
- `collect_truth_split()` appends `Blocker(TARGET_TRUTH_SPLIT_MISMATCH, ...)` → `status="FAIL"`

All three assertions pass:
- `payload["status"] == "FAIL"` ✅
- `any(b.reason_code == TARGET_TRUTH_SPLIT_MISMATCH for b in blockers)` ✅
- `payload["rows"][0]["classification"] == "STALE_MODEL_MAP"` ✅
- `payload["target_phase_mismatch_count"] >= 1` ✅

## Test Results

```
10 passed in 0.52s
```

9 pre-existing tests + 1 new. Zero regressions.

## What Was NOT Touched

Runtime code (`validate_pre_live_gate_v25.py`), schemas, `config/`, `.github/workflows/`, Task-Orchestrator/Dopetask/ConPort/dope-memory/dope-context/dopecon-bridge state, GitHub state, merge automation. `queue_drain.py` and `scripts/batch_resolve_and_merge.py` not touched, imported, or executed. No secrets printed.

## Files Changed

- **Modified (1):** `services/repo-truth-extractor/tests/test_pre_live_gate_v25.py`
- **Created (3):** task packet + PROOF.json + SUMMARY.md

## Remaining Uncertainty

- `STALE_RUNNER_REGISTRY` and `STALE_PROMPTSET` branches in `collect_truth_split`'s loop are dead code (hardcoded `runner_active=True`, `prompt_resolution_active=True`). Not tested via loop path, not fixed — separate concern.
- Gate not exercised against a real extraction run — this is static code path verification only.

## Next Packet

`TP-DMX-DCP-SEAM-LIFT-001` — wire existing `RedLaneScanner` executable into CI/steward.
