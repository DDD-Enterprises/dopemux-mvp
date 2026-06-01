---
id: TP-DMX-ADHD-COGNITIVE-T4-06-BASELINE-CALIBRATION-001-implementation-notes
title: Tp Dmx Adhd Cognitive T4 06 Baseline Calibration 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Tp Dmx Adhd Cognitive T4 06 Baseline Calibration 001 Implementation Notes
  (explanation) for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T4-06-BASELINE-CALIBRATION-001 Implementation Notes

## Scope

- Added in-memory per-user activity baseline samples to `services/adhd_engine/core/engine.py`.
- Baseline samples are derived only from bounded numeric activity metrics already accepted by `record_activity_update`.
- Added explicit `calibrating`/`ready` baseline status via `get_activity_baseline_status`.
- Routed energy and attention assessment through deterministic per-user percentile thresholds once the baseline is ready.
- Preserved bootstrap assessment behavior while fewer than five samples exist.

## RED Evidence

- `python -m pytest tests/unit/test_adhd_baseline_calibration.py`
- Result before implementation: `4 failed in 1.97s`
- Failure modes:
  - missing `get_activity_baseline_status`
  - high-switch user still classified as `AttentionState.SCATTERED` by static thresholds

## GREEN Evidence

- `python -m pytest tests/unit/test_adhd_baseline_calibration.py`
- Result after implementation: `4 passed in 1.76s`
- Focused regression:
  - `python -m pytest tests/unit/test_adhd_baseline_calibration.py tests/unit/test_adhd_real_assessment.py`
  - Result: `8 passed in 1.74s`

## Final Validation

- `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T4-06-BASELINE-CALIBRATION-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`: PASS
- `python -m pytest tests/unit/test_adhd_baseline_calibration.py tests/unit/test_adhd_privacy_guard.py tests/unit/test_adhd_real_assessment.py tests/unit/test_adhd_activity_loop.py tests/unit/test_adhd_operator_profile_seed.py tests/unit/test_adhd_operator_identity.py tests/unit/test_adhd_engine_settings_contract.py tests/unit/test_adhd_engine_task_orchestrator_url.py services/adhd_engine/tests/test_activity_tracker.py services/adhd_engine/tests/test_api.py`: PASS, `57 passed in 0.71s`
- `python -m py_compile services/adhd_engine/core/engine.py`: PASS
- `git diff --check`: PASS
- `pre-commit run --files services/adhd_engine/core/engine.py tests/unit/test_adhd_baseline_calibration.py task-packets/TP-DMX-ADHD-COGNITIVE-T4-06-BASELINE-CALIBRATION-001.json task-packets/TP-DMX-ADHD-COGNITIVE-T4-06-BASELINE-CALIBRATION-001-implementation-notes.md`: PASS

## Residual Risk

- Baselines are process-local in-memory state only; no persistent calibration store is claimed in this slice.
- Bootstrap thresholds remain in use while `sample_count < 5`; readiness remains explicit as `calibrating`.
- Live Redis, EventBus, provider, dashboard, shell-hook, and persistent runtime paths were not exercised by this packet.
