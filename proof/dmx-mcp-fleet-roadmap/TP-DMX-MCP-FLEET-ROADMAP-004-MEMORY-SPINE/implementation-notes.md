# TP-DMX-MCP-FLEET-ROADMAP-004-MEMORY-SPINE Implementation Notes

## Scope

Implemented Lane 4 memory-spine capture repair for promotable source events.

## Changes

- Added `emit_promotable_capture_event` and `try_emit_promotable_capture_event`
  in the capture client.
- The helper only accepts WMA-promotable event types and defaults Redis/event-bus
  fan-out off.
- Native hook `PostToolUseFailure` now emits bounded `error.encountered`
  capture metadata without raw tool input, raw error text, or session ID.
- PM source writers now emit best-effort promotable events only after canonical
  writes succeed:
  - `decision.logged` after ConPort decision writes.
  - `workflow.phase_changed` after task-orchestrator transitions.
  - `task.completed` and `task.blocked` for matching workflow transitions.
- WMA `PromotionEngine.promote` now also accepts its legacy
  `(event_type, payload)` call form while preserving fail-closed provenance
  validation for runtime event envelopes.

## Authority

- ConPort remains the structured decision/progress authority.
- task-orchestrator remains workflow transition authority.
- dope-memory receives chronicle/capture receipts and does not become PM truth.
- Redis streams remain optional transport, not authority.

## Validation

PASS:

- `python -m jsonschema -i task-packets/generated/TP-DMX-MCP-FLEET-ROADMAP-004-MEMORY-SPINE.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `python -m pytest tests/test_native_hooks_workflow.py tests/unit/test_memory_capture_client.py -q`
- `python -m pytest tests/test_pm_api.py -q`
- `python -m pytest services/working-memory-assistant/tests/test_promotion_allowlist.py -q`
- `python -m py_compile src/dopemux/claude/native_hooks.py src/dopemux/memory/capture_client.py src/dopemux/pm/writes.py src/dopemux/pm/api.py services/working-memory-assistant/promotion/promotion.py`
- Review-fix reruns of the focused, PM, WMA allowlist, and py-compile checks.

FAIL:

- Initial extra WMA promotion allowlist run failed because the test file used
  the legacy `(event_type, payload)` call shape while runtime code accepted only
  full event envelopes. A compatibility path was added and the suite passed.
- PR review identified four drift risks: payload-colliding legacy promotion IDs,
  hard-coded CLI capture mode, async transition phase defaults, and missing
  underscore event normalization. These were fixed with focused regression tests.

NOT_RUN:

- Live ConPort, task-orchestrator, Redis, or dope-memory runtime integration.
  The lane validates source-event construction and fail-open capture behavior
  with unit tests only.

## Runtime Boundaries

No Docker services were started. No provider calls were made. No secrets were
printed. Hook failure capture intentionally omits raw hook error text and Claude
session IDs.
