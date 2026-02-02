---
id: 04_event_taxonomy
title: 04_Event_Taxonomy
type: explanation
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Dope-Memory v1 — Event Taxonomy

## Streams
- activity.events.v1 (input)
- memory.derived.v1 (output)

## Required Event Envelope (all producers)
All events must include:
- id (uuid)
- ts (utc iso)
- workspace_id
- instance_id
- session_id (optional)
- type (event_type)
- source
- data (object)

Example:
```json
{
  "id": "uuid",
  "ts": "2026-02-02T10:00:00Z",
  "workspace_id": "ws_uuid_or_string",
  "instance_id": "A",
  "session_id": "session_uuid_or_null",
  "type": "decision.logged",
  "source": "dopequery",
  "data": {...}
}
```

## Phase 1 Promoted (Curated) Event Types
These events are eligible for promotion into work_log_entries:

1) decision.logged
- data: {decision_id, title, choice, rationale, affected_files?, tags?}

2) task.completed
3) task.failed
4) task.blocked
- data: {task_id, title, outcome, duration_seconds?, error?, service?, tags?}

5) error.encountered
- data: {error_kind, message, stack?, file?, test?, ci_job?, tags?}

6) workflow.phase_changed
- data: {from_phase, to_phase, reason?}

7) manual.memory_store
- data: {category, entry_type, summary, details?, tags?, links?}

## Phase 1 Raw-Only Event Types
Stored in raw_activity_events only; not promoted in Phase 1:
- file.created / file.modified / file.deleted / file.renamed
- git.commit / git.push / git.branch_created / git.branch_switched / git.merge
- tool.invoked (unless it is manual.memory_store)
- test.started / test.completed (unless error.encountered)
- build.started / build.completed (unless failure)
- context.retrieved (analytics only)
- memory.pressure (analytics only)

## Derived Output Events (published by Dope-Memory)
1) worklog.created
- data: {entry_id, category, entry_type, importance_score, summary}

2) worklog.updated
- data: {entry_id, updated_fields}

3) memory.pulse (Phase 2)
- data: {trajectory, constraints[], suggested_next[], source_entry_ids[]}

4) reflection.created (Phase 2)
- data: {reflection_id, window_start, window_end, trajectory}

5) edge.proposed (Phase 3)
- data: {edge_type, from_id, to_id, confidence, evidence_ids[], window_start, window_end}

## Deterministic Promotion Contract
Promotion eligibility depends solely on:
- event_type
- presence of minimum required fields
- passing redaction gate
No probabilistic behavior in Phase 1 promotion.
