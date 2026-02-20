---
id: PROMPT_C_EVENTS
title: Prompt C Events
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-20'
last_review: '2026-02-20'
next_review: '2026-05-21'
prelude: Prompt C Events (explanation) for dopemux documentation and developer workflows.
---
# Prompt C (v2): Events (emitters + consumers + envelope fields)

**Outputs:** `EVENT_EMITTERS.json`, `EVENT_CONSUMERS.json`, `EVENT_ENVELOPE_FIELDS.json`

---

## TASK

Produce THREE JSON files: `EVENT_EMITTERS.json`, `EVENT_CONSUMERS.json`, `EVENT_ENVELOPE_FIELDS.json`.

## TARGET

`/Users/hue/code/dopemux-mvp` WORKING TREE.

## EVENT_EMITTERS.json

- Find code locations where an "event" is constructed/emitted/published/enqueued/logged as an event.
- Capture event name strings/constants when present.
- Emit items:
  - `domain=code_event_emitter`
  - `kind=event_emitter`
  - `name=<event name if literal else symbol>`
  - `symbol=<emitter function>`
  - `strings` include any event name strings and stream names.

## EVENT_CONSUMERS.json

- Find code locations where events are ingested/consumed/processed/subscribed.
- Emit items:
  - `domain=code_event_consumer`
  - `kind=event_consumer`
  - `name=<event name if literal else symbol>`
  - `symbol=<consumer function>`
  - `strings` include any event name strings and filters.

## EVENT_ENVELOPE_FIELDS.json

- Find definitions of event envelope fields (e.g., event_id, ts, producer, stream, payload, schema_version).
- Emit items:
  - `domain=code_model` (or `code_db` if stored schema)
  - `kind=model`
  - `name="event_envelope_fields"`
  - `strings` should be the field names extracted literally.

## RULES

- Exact string extraction only (no guessing event names).
- Universal schema, deterministic sorting.
