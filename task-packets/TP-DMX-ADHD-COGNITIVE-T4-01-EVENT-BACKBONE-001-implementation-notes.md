---
title: T4-01 Event Backbone Implementation Notes
status: draft
id: TP-DMX-ADHD-COGNITIVE-T4-01-EVENT-BACKBONE-001-implementation-notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: T4-01 Event Backbone Implementation Notes (explanation) for dopemux documentation
  and developer workflows.
---
# T4-01 Event Backbone Implementation Notes

## Scope

Observed runtime defects:

- `WorkspaceEventEmitter` and `DesktopActivityMonitor`/`CalendarIntegration` imported a nonexistent top-level `event_bus` module and attempted to call a `publish()` API while startup passes `ADHDEventEmitter`.
- `services.adhd_engine.api.routes` imported top-level `event_emitter`, so package imports left `EVENT_EMISSION_AVAILABLE = False`.
- `emit_claude_tool()` emits `claude_tool_completed`, but `ADHDEventListener` only handled `claude_tool_started`.
- `ADHDEventListener._surface_finding()` called `event_bus.publish(...)`, but `ADHDEventEmitter` did not expose a publish-compatible bridge.

## Implementation

- Kept `ADHDEventEmitter` as the canonical ADHD event transport.
- Added `ADHDEventEmitter.publish(stream, event)` as a compatibility bridge for prebuilt `Event` objects while preserving `emit(event_type, data, source)` as the primary producer API.
- Routed workspace and external activity producers through `event_bus.emit(...)`.
- Switched route hook imports to package-relative `..event_emitter`.
- Added `claude_tool_completed` listener mapping to the existing Claude tool handler.

## TDD Evidence

RED:

```text
python -m pytest tests/unit/test_adhd_event_backbone.py
6 failed
```

GREEN:

```text
python -m pytest tests/unit/test_adhd_event_backbone.py
6 passed
```

## Deferred / Out Of Scope

- No live Redis, Desktop Commander, Calendar, or FastAPI startup integration run was performed in this implementation slice.
- No privacy payload narrowing was attempted beyond preserving the existing structured payloads; broader content minimization remains separate remediation work.
