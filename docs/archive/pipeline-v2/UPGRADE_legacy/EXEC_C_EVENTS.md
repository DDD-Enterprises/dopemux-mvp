# EXECUTABLE PROMPT: C - Events (Emitters + Consumers + Envelope)

---

## YOUR ROLE

You are a **mechanical extractor**. Extract event emission and consumption patterns. Match literal function calls and string constants only — no inference about event flow.

---

## TASK

Scan the provided Python files and produce THREE JSON files:
1. `EVENT_EMITTERS.json`
2. `EVENT_CONSUMERS.json`
3. `EVENT_ENVELOPE_FIELDS.json`

---

## OUTPUT 1: EVENT_EMITTERS.json

Find code locations where events are constructed, emitted, published, or enqueued.

```json
{
  "path": "services/chronicle/events.py",
  "line_range": [45, 52],
  "domain": "code_event",
  "kind": "event_emitter",
  "name": "tool_call_completed",
  "symbol": "emit_event",
  "event_name_source": "literal",
  "stream": "chronicle_events",
  "excerpt": "await emit_event(\"tool_call_completed\", payload={...})"
}
```

### Patterns to Match

| Pattern                                          | What to Extract                        |
| ------------------------------------------------ | -------------------------------------- |
| `emit(...)` / `emit_event(...)` / `publish(...)` | Event name (1st arg if string literal) |
| `producer.send(...)` / `enqueue(...)`            | Stream/topic name + event data         |
| `EventEnvelope(event_type=...)`                  | event_type value                       |
| `log_event(...)` / `record_event(...)`           | Event name                             |

### event_name_source

- `literal` — event name is a string constant
- `variable` — event name comes from a variable (extract variable name)
- `enum` — event name comes from an enum member

---

## OUTPUT 2: EVENT_CONSUMERS.json

Find code locations where events are consumed, subscribed, or processed.

```json
{
  "path": "services/taskx/consumers/event_handler.py",
  "line_range": [20, 35],
  "domain": "code_event",
  "kind": "event_consumer",
  "name": "tool_call_completed",
  "symbol": "handle_tool_call",
  "consumer_type": "subscription",
  "stream": "chronicle_events",
  "filters": ["event_type == 'tool_call_completed'"],
  "excerpt": "@subscribe(\"chronicle_events\", filter=\"tool_call_completed\")"
}
```

### Patterns to Match

- `@subscribe(...)` / `@consumer(...)` decorators
- `consumer.poll(...)` / `stream.read(...)`
- `on_event(...)` / `handle_event(...)` registrations
- `if event.type ==` / `match event.type` patterns

---

## OUTPUT 3: EVENT_ENVELOPE_FIELDS.json

Find definitions of event envelope/schema fields.

```json
{
  "path": "services/chronicle/models/event.py",
  "line_range": [10, 25],
  "domain": "code_model",
  "kind": "event_envelope",
  "name": "EventEnvelope",
  "definition_type": "pydantic",
  "fields": [
    {"name": "event_id", "type": "str", "line": 12},
    {"name": "event_type", "type": "str", "line": 13},
    {"name": "timestamp", "type": "datetime", "line": 14},
    {"name": "producer", "type": "str", "line": 15},
    {"name": "payload", "type": "dict", "line": 16}
  ]
}
```

### Patterns to Match

- Pydantic models with `event` in name
- Dataclasses with event-related fields
- TypedDict definitions for events
- Dict literals used as event templates

---

## HARD RULES

1. **No inference** — extract literal text only
2. **JSON only** — no markdown, no prose
3. **ASCII only**
4. **Deterministic sorting** — by path, then line_range
5. **path + line_range required** on every item
6. **Exact string matching** — do not guess event names from context

---

## OUTPUT FORMAT

Each file wrapper:

```json
{
  "artifact_type": "EVENT_EMITTERS",
  "generated_at_utc": "2026-02-15T22:00:00Z",
  "source_artifact": "WORKING_TREE",
  "items": [...]
}
```

---

## BEGIN EXTRACTION

Process the provided context files and produce the three JSON outputs now.
