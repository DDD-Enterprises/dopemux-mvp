---
id: TP-DMX-ADHD-COGNITIVE-T4-00-OPERATOR-IDENTITY-001-implementation-notes
title: Tp Dmx Adhd Cognitive T4 00 Operator Identity 001 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: Tp Dmx Adhd Cognitive T4 00 Operator Identity 001 Implementation Notes (explanation)
  for dopemux documentation and developer workflows.
---
# TP-DMX-ADHD-COGNITIVE-T4-00-OPERATOR-IDENTITY-001 Implementation Notes

## Scope

Implemented the T4-00 operator identity gate only.

In scope:
- Add content-free operator identity resolver.
- Persist a random UUID at `~/.dopemux/operator_id` with `0600` permissions.
- Allow explicit content-free environment override without writing the persisted file.
- Thread the resolved operator id through active ADHD engine domain component startup, event listener startup, MCP cognitive-state default, and `/api/v1/state` default.

Out of scope:
- Profile seeding (`T4-03a`).
- Activity input-loop closure (`T4-03b`).
- Event API reconciliation (`T4-01`).
- Assessment algorithm changes (`T4-04`).

## Analysis Performed

Observed runtime authority:
- `services/adhd_engine/main.py` imports `services.adhd_engine.core.engine.ADHDAccommodationEngine`.
- `services/adhd_engine/core/engine.py` used `settings.workspace_id` for `AttentionCalibrator`, `SocialBatteryMonitor`, and `event_listener.start`.
- `services/adhd_engine/api/routes.py` defaulted local `/state` to `"default"`.
- `services/adhd_engine/main.py` defaulted MCP `get_cognitive_state` and lifespan event listener startup to `"default"`.

Challenge notes:
- Do not hash workspace, machine id, hostname, username, repo path, or prompt/file content; those would create fingerprinting or content leakage risk.
- Do not seed `engine.user_profiles` in this slice; the loaded DAG has separate T4-03a profile seeding.
- Do not edit the legacy sibling `services/adhd_engine/engine.py`; the active app path imports `core.engine`.

## Validation Evidence

RED:
- `python -m pytest tests/unit/test_adhd_operator_identity.py`
- Result: `6 failed`.
- Expected failures: missing `services.adhd_engine.operator_identity`, missing `settings.operator_id_path`, missing resolver imports/threading in `core.engine` and `api.routes`.

GREEN:
- `python -m pytest tests/unit/test_adhd_operator_identity.py`
- Result: `6 passed in 1.47s`.

Targeted regression:
- `python -m pytest tests/unit/test_adhd_operator_identity.py tests/unit/test_adhd_engine_settings_contract.py tests/unit/test_adhd_engine_task_orchestrator_url.py`
- Result: `12 passed in 1.42s`.

Packet schema:
- `python -m jsonschema -i task-packets/TP-DMX-ADHD-COGNITIVE-T4-00-OPERATOR-IDENTITY-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- Result: exit code 0. The jsonschema CLI emitted only its deprecation warning.

Diff hygiene:
- `git diff --check`
- Result: exit code 0.

## Remaining Risk

- Existing operator identity files with invalid/path-like content now fail closed at resolver time.
- `/api/v1/state` now resolves the operator id by default, but state dictionaries will still return fallback energy/attention until T4-03a/T4-03b/T4-04 land.
- Runtime integration with a live ADHD engine process was not exercised in this slice.
