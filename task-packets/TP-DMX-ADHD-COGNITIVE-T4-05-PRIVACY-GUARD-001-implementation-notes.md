---
id: TP-DMX-ADHD-COGNITIVE-T4-05-PRIVACY-GUARD-001-implementation-notes
title: Tp Dmx Adhd Cognitive T4 05 Privacy Guard 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Tp Dmx Adhd Cognitive T4 05 Privacy Guard 001 Implementation Notes
  (explanation) for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T4-05 Privacy Guard Implementation Notes

## Authority

- Active Task Packet: `TP-DMX-ADHD-COGNITIVE-T4-05-PRIVACY-GUARD-001`
- Parent dependency: `TP-DMX-ADHD-COGNITIVE-T4-04-REAL-ASSESSMENT-001`
- Runtime route authority: `services/adhd_engine/api/routes.py`
- Runtime engine authority: `services/adhd_engine/core/engine.py`
- Event payload authority: `services/adhd_engine/event_emitter.py`

## Change

- Added a recursive content-bearing hook payload guard for prompt, path, file, code, raw-argument, and arbitrary content fields.
- Made `/save-context` and `/log-intent` reject content-bearing payloads before persistence or event emission.
- Removed prompt summaries and prompt hints from emitted Claude prompt/context events.
- Made `/tasks`, `/tasks/{user_id}`, and `/unfinished-work` fail closed with HTTP 410 instead of exposing task, PM, path, or unfinished-work data.
- Removed the ConPort progress-entry write from cognitive overload handling.
- Updated stale ADHD API task tests to assert the new fail-closed contract.

## TDD Evidence

- RED: `python -m pytest tests/unit/test_adhd_privacy_guard.py`
  - Exit 1 before implementation.
  - `5 failed`: routes accepted prompt/path content, event helpers emitted prompt fields, task/unfinished routes did not fail closed, and cognitive overload wrote ConPort progress.
- GREEN: `python -m pytest tests/unit/test_adhd_privacy_guard.py`
  - Exit 0 after implementation.
  - `5 passed in 1.11s`.
- GREEN: `python -m pytest tests/unit/test_adhd_privacy_guard.py services/adhd_engine/tests/test_api.py`
  - Exit 0 after updating stale task API expectations.
  - `16 passed in 0.23s`.

## Validation

- PASS: `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T4-05-PRIVACY-GUARD-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- PASS: `python -m pytest tests/unit/test_adhd_privacy_guard.py tests/unit/test_adhd_real_assessment.py tests/unit/test_adhd_activity_loop.py tests/unit/test_adhd_operator_profile_seed.py tests/unit/test_adhd_operator_identity.py tests/unit/test_adhd_engine_settings_contract.py tests/unit/test_adhd_engine_task_orchestrator_url.py services/adhd_engine/tests/test_activity_tracker.py services/adhd_engine/tests/test_api.py`
  - `53 passed`.
- PASS: `python -m py_compile services/adhd_engine/core/engine.py services/adhd_engine/api/routes.py services/adhd_engine/event_emitter.py`
- PASS: `git diff --check`

## Residual Risk

- Live Redis, live EventBus, and real hook shell scripts were not exercised in this slice.
- The guard is route/event-path coverage, not a full repository-wide privacy scanner.
- This branch is intentionally stacked on `codex/adhd-real-assessment-001`.
