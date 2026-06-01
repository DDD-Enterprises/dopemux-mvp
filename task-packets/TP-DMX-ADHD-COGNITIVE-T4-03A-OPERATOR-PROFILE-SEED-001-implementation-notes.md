---
id: TP-DMX-ADHD-COGNITIVE-T4-03A-OPERATOR-PROFILE-SEED-001-implementation-notes
title: Tp Dmx Adhd Cognitive T4 03A Operator Profile Seed 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Tp Dmx Adhd Cognitive T4 03A Operator Profile Seed 001 Implementation Notes
  (explanation) for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T4-03A Operator Profile Seed Implementation Notes

## Authority

- Active Task Packet: `TP-DMX-ADHD-COGNITIVE-T4-03A-OPERATOR-PROFILE-SEED-001`
- Parent dependency: `TP-DMX-ADHD-COGNITIVE-T4-00-OPERATOR-IDENTITY-001`
- Runtime authority: `services/adhd_engine/core/engine.py`
- Profile schema authority: `services/adhd_engine/core/models.py`
- Existing persistence shape: `services/adhd_engine/api/routes.py` uses `json.dumps(asdict(profile), default=str)` for `adhd:profile:<user_id>`.

## Change

- `_load_user_profiles()` now normalizes Redis text keys and values so decoded-string and raw-byte Redis clients both work.
- Startup now seeds a default `ADHDProfile` for the resolved stable operator id when no operator profile was loaded.
- Existing operator profiles are preserved and are not overwritten.
- Seeded operator profiles are persisted under `adhd:profile:<operator_user_id>` using the existing profile JSON shape.

## TDD Evidence

- RED: `python -m pytest tests/unit/test_adhd_operator_profile_seed.py`
  - Exit 1 before implementation.
  - Empty Redis startup left `engine.user_profiles["operator-local-001"]` missing.
  - Byte Redis keys raised a loader error and left existing byte-key profiles unloaded.
- GREEN: `python -m pytest tests/unit/test_adhd_operator_profile_seed.py`
  - Exit 0 after implementation.
  - `3 passed in 1.40s`.

## Validation

- PASS: `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T4-03A-OPERATOR-PROFILE-SEED-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- PASS: `python -m pytest tests/unit/test_adhd_operator_profile_seed.py tests/unit/test_adhd_operator_identity.py tests/unit/test_adhd_engine_settings_contract.py tests/unit/test_adhd_engine_task_orchestrator_url.py`
  - `15 passed in 1.54s`.
- PASS: `python -m py_compile services/adhd_engine/core/engine.py`
- PASS: `git diff --check`
- PASS: `python -m pre_commit run --files services/adhd_engine/core/engine.py tests/unit/test_adhd_operator_profile_seed.py task-packets/TP-DMX-ADHD-COGNITIVE-T4-03A-OPERATOR-PROFILE-SEED-001.json task-packets/TP-DMX-ADHD-COGNITIVE-T4-03A-OPERATOR-PROFILE-SEED-001-implementation-notes.md`

## Residual Risk

- Live Redis/container startup was not exercised in this slice.
- This does not close native hook ingestion or activity-loop gaps; it only proves the active profile load path seeds the operator profile.
- This branch is intentionally stacked on `codex/adhd-operator-identity-001`.
