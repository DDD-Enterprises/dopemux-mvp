---
id: TP-DMX-ADHD-COGNITIVE-T4-04-REAL-ASSESSMENT-001-implementation-notes
title: Tp Dmx Adhd Cognitive T4 04 Real Assessment 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Tp Dmx Adhd Cognitive T4 04 Real Assessment 001 Implementation Notes
  (explanation) for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T4-04 Real Assessment Implementation Notes

## Authority

- Active Task Packet: `TP-DMX-ADHD-COGNITIVE-T4-04-REAL-ASSESSMENT-001`
- Parent dependency: `TP-DMX-ADHD-COGNITIVE-T4-03B-ACTIVITY-LOOP-001`
- Runtime authority: `services/adhd_engine/core/engine.py`
- Activity evidence authority: `services/adhd_engine/core/activity_tracker.py`
- Existing activity-loop tests: `tests/unit/test_adhd_activity_loop.py`

## Change

- Added bounded recent hook activity samples in `ADHDAccommodationEngine` and derived content-free aggregate metrics from those samples.
- Made recent activity metrics drive attention indicators instead of returning fixed focused defaults.
- Kept raw prompt content out of `recent_activity_updates`; only allowlisted numeric/string counters survive sanitization.
- Added `activity_evidence` to `ActivityTracker.get_recent_activity()` so downstream assessment can distinguish observed activity from fallback/default data.
- Added focused regression coverage for high context switching, repeated hook failures, and ActivityTracker evidence flags.

## TDD Evidence

- RED: `python -m pytest tests/unit/test_adhd_real_assessment.py`
  - Exit 1 before implementation.
  - High context-switch activity returned `AttentionState.FOCUSED` instead of `SCATTERED`.
  - Repeated hook failures left energy at `EnergyLevel.MEDIUM`.
  - `ActivityTracker.get_recent_activity()` did not expose `activity_evidence`.
- GREEN: `python -m pytest tests/unit/test_adhd_real_assessment.py`
  - Exit 0 after implementation.
  - `4 passed in 1.45s`.

## Validation

- PASS: `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T4-04-REAL-ASSESSMENT-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- PASS: `python -m pytest tests/unit/test_adhd_real_assessment.py tests/unit/test_adhd_activity_loop.py tests/unit/test_adhd_operator_profile_seed.py tests/unit/test_adhd_operator_identity.py tests/unit/test_adhd_engine_settings_contract.py tests/unit/test_adhd_engine_task_orchestrator_url.py services/adhd_engine/tests/test_activity_tracker.py`
  - `37 passed in 0.27s`.
- PASS: `python -m py_compile services/adhd_engine/core/engine.py services/adhd_engine/core/activity_tracker.py`
- PASS: `git diff --check`

## Residual Risk

- Live Redis and live event-stream ingestion were not exercised in this slice.
- The weak-signal scoring remains intentionally conservative and bounded; richer privacy-schema hardening remains the separate section 6 guard item.
- This branch is intentionally stacked on `codex/adhd-activity-loop-001`.
