---
id: ADR-PM-002-pm-event-taxonomy
title: Adr Pm 002 Pm Event Taxonomy
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Adr Pm 002 Pm Event Taxonomy (adr) for dopemux documentation and developer
  workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# Context

Current PM-related event surfaces are fragmented:

- Task-orchestrator coordinator uses internal event types like `task_created`, `task_updated`, and `task_completed`.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L22-L29`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_event_coordinator.py.txt:L191-L194`.
- Taskmaster adapter emits namespaced events such as `taskmaster.task.created` and `taskmaster.task.status_updated`.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L82-L90`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L131-L140`.
- Event bus transport can continue with local fan-out fallback while disconnected, which risks silent coordination drift unless callers get explicit degraded results.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_src_dopemux_event_bus.py.txt:L141-L156`.

# Decision

PM plane adopts a canonical `pm.*` event taxonomy and envelope:

- `pm.task.created`
- `pm.task.updated`
- `pm.task.status_changed`
- `pm.task.blocked`
- `pm.task.completed`
- `pm.decision.linked`
- `pm.sync.leantime.requested|succeeded|failed`

Envelope invariants:

1. `event_id` is a content-address hash over canonical payload fields.
1. `ts_utc` is the authoritative event timestamp field.
1. `idempotency_key` is required for transition-producing events.
1. `source` is required and normalized to producing component.
1. Consumers are replay-safe and ignore duplicate `event_id`.

# Consequences

- Positive:
- Cross-service coordination semantics become explicit and auditable.
- Retries become safe by construction.
- Failure handling can return precise degraded statuses.
- Tradeoffs:
- Existing producers need mapping/adaptation into `pm.*` names.
- Additional normalization logic is required for timestamp and hashing fields.

# Alternatives Considered

1. Keep existing event names per component.
- Rejected: creates translation ambiguity and weak replay guarantees.

1. Use transport-level IDs only (no content hash).
- Rejected: weak idempotency across retries/replays from different producers.

1. Use only status snapshots and no transition events.
- Rejected: loses audit trail and causal ordering.

# Acceptance Tests

1. PM architecture doc includes canonical `pm.*` event list and required envelope fields.
1. Event idempotency rules are specified at producer and consumer boundaries.
1. Failure-mode section states explicit behavior for EventBus unavailability.
1. All event-taxonomy claims in docs are backed by evidence citations or marked UNKNOWN.
