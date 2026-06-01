---
title: T4-02a Native Hooks Events Implementation Notes
status: draft
id: TP-DMX-ADHD-COGNITIVE-T4-02A-NATIVE-HOOKS-EVENTS-001-implementation-notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-31'
last_review: '2026-05-31'
next_review: '2026-08-29'
prelude: T4-02a Native Hooks Events Implementation Notes (explanation) for dopemux
  documentation and developer workflows.
---
# T4-02a Native Hooks Events Implementation Notes

## Scope

Native hook activity now emits best-effort Redis Stream events for:

- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `PostToolUseFailure`

The emitted event intentionally excludes prompt text, tool input, tool response, errors, cwd, paths, and session IDs.

## Event Shape

Each event is written with `xadd` to `dopemux:events` by default:

```json
{
  "event_type": "native_hook_activity",
  "timestamp": "<utc iso timestamp>",
  "source": "dopemux.native_hooks",
  "data": "{\"hook_event_name\":\"PreToolUse\",\"status\":\"attempt\",\"tool_name\":\"Read\"}"
}
```

## TDD Evidence

RED:

```text
python -m pytest tests/test_native_hooks_workflow.py
1 failed, 4 passed
```

GREEN:

```text
python -m pytest tests/test_native_hooks_workflow.py
5 passed
```

## Deferred / Out Of Scope

- No live Redis integration run was performed in this slice.
- No changes were made to Claude settings registration or shell hook scripts.
