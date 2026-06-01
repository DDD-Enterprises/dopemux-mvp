---
id: TP-DMX-ADHD-COGNITIVE-T4-03B-ACTIVITY-LOOP-001-implementation-notes
title: Tp Dmx Adhd Cognitive T4 03B Activity Loop 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Tp Dmx Adhd Cognitive T4 03B Activity Loop 001 Implementation Notes (explanation)
  for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T4-03B Activity Loop Implementation Notes

## Authority

- Active Task Packet: `TP-DMX-ADHD-COGNITIVE-T4-03B-ACTIVITY-LOOP-001`
- Parent dependency: `TP-DMX-ADHD-COGNITIVE-T4-03A-OPERATOR-PROFILE-SEED-001`
- Runtime authority: `services/adhd_engine/core/engine.py`
- Listener authority: `services/adhd_engine/event_listener.py`
- `/activity` route authority: `services/adhd_engine/api/routes.py`

## Change

- Added `ADHDAccommodationEngine.record_activity_update()` to sanitize bounded activity metrics, refresh energy and attention assessments, and write `current_energy_levels` and `current_attention_states`.
- Made immediate activity updates take precedence over `ActivityTracker` reads during reassessment.
- Injected the active engine into `ADHDEventListener`.
- Added listener handling for `native_hook_activity` and `activity_updated` events.
- Changed `/activity` to process every update, write current state, and best-effort emit a content-free `activity_updated` event.
- Removed the stale early cache-hit return from `/activity` so state-changing calls are not skipped.

## TDD Evidence

- RED: `python -m pytest tests/unit/test_adhd_activity_loop.py`
  - Exit 1 before implementation.
  - Missing `record_activity_update`, missing listener `adhd_engine` injection, and missing route `ADHDEventEmitter` import.
- RED: `python -m pytest tests/unit/test_adhd_activity_loop.py`
  - Exit 1 after adding immediate-update precedence regression.
  - `_get_recent_activity()` returned stale `ActivityTracker` data instead of the just-recorded update.
- RED: `python -m pytest tests/unit/test_adhd_activity_loop.py`
  - Exit 1 after adding cache-bypass regression.
  - `/activity` returned a cached response and skipped the update path.
- GREEN: `python -m pytest tests/unit/test_adhd_activity_loop.py`
  - Exit 0 after implementation.
  - `5 passed in 1.65s`.

## Validation

- PASS: `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T4-03B-ACTIVITY-LOOP-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- PASS: `python -m pytest tests/unit/test_adhd_activity_loop.py tests/unit/test_adhd_operator_profile_seed.py tests/unit/test_adhd_operator_identity.py tests/unit/test_adhd_engine_settings_contract.py tests/unit/test_adhd_engine_task_orchestrator_url.py`
  - `20 passed in 1.48s`.
- PASS: `python -m py_compile services/adhd_engine/core/engine.py services/adhd_engine/event_listener.py services/adhd_engine/api/routes.py`
- PASS: `git diff --check`
- PASS: `python -m pre_commit run --files services/adhd_engine/core/engine.py services/adhd_engine/event_listener.py services/adhd_engine/api/routes.py tests/unit/test_adhd_activity_loop.py task-packets/TP-DMX-ADHD-COGNITIVE-T4-03B-ACTIVITY-LOOP-001.json task-packets/TP-DMX-ADHD-COGNITIVE-T4-03B-ACTIVITY-LOOP-001-implementation-notes.md`

## Residual Risk

- Live Redis stream consumption was not exercised in this slice.
- Native hook producer code lives in the parallel T4-02a branch; full producer-to-consumer validation remains pending until dependency branches are merged together.
- The attention indicator mapping from activity metrics is intentionally minimal; richer weak-signal fusion remains the next T4 item.
