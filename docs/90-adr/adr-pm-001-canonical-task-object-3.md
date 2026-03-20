---
id: ADR-PM-001-canonical-task-object
title: Adr Pm 001 Canonical Task Object
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Adr Pm 001 Canonical Task Object (adr) for dopemux documentation and developer
  workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# Context

PM task state is currently spread across multiple surfaces with incompatible status dialects and field sets.

- Task-orchestrator has `TaskStatus` with `pending/in_progress/completed/blocked` plus ADHD-only states (`needs_break`, `context_switch`, `paused`).
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_task-orchestrator_task_orchestrator_models.py.txt:L13-L22`.
- Taskmaster bridge writes `TODO` status into progress metadata and emits status events, but does not implement robust in-place update semantics.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L57-L79`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_bridge_adapter.py.txt:L129-L131`.
- Taskmaster runtime is wrapper-centric (`server.py` + adapter + console entrypoint) and does not expose a separate domain model module.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/12_taskmaster_find_files.txt:L3-L10`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_services_taskmaster_src_dopemux_taskmaster.egg-info_entry_points.txt.txt:L1-L2`; `docs/planes/pm/_evidence/PM-ARCH-03.outputs/99_missing_expected_files.txt:L1-L3`.

Without one canonical object, idempotent transitions and deterministic reconciliation cannot be enforced.

# Decision

PM plane adopts one canonical task object as the only authority for lifecycle state. Every producer maps into this object before any lifecycle transition is accepted.

Invariants:

1. `task_id` is immutable and globally stable for the task lifecycle.
1. `status` uses only canonical enum: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `CANCELED`.
1. Every transition request includes an idempotency key; duplicate keys are no-op replays.
1. `updated_at_utc` and `version` are monotonic; stale writes are refused.
1. Link fields to ConPort/Chronicle/Leantime/Taskmaster are references only, never alternate truth stores.

# Consequences

- Positive:
- Deterministic lifecycle behavior across task-orchestrator, taskmaster, and CLI surfaces.
- Explicit source and provenance tracking for auditability.
- Simpler failure handling via one transition contract.
- Tradeoffs:
- Existing status dialects require explicit mapping logic.
- Producer adapters must supply idempotency inputs.
- Some existing advisory states become overlays, not lifecycle states.

# Alternatives Considered

1. Keep current multi-surface status dialects.
- Rejected: preserves drift and non-deterministic reconciliation.

1. Use task-orchestrator `OrchestrationTask` as canonical without reduction.
- Rejected: includes ADHD/session fields that are not universally valid lifecycle authority.

1. Use dopecon-bridge `TaskRecord` as canonical PM model.
- Rejected: integration service model is useful but not currently the PM-plane-wide contract.
  Evidence: `docs/planes/pm/_evidence/PM-ARCH-03.outputs/nl_top10_services_dopecon-bridge_dopecon_bridge_models.py.txt:L46-L65`.

# Acceptance Tests

1. Architecture docs define canonical field list, lifecycle enum, and idempotency invariants with citations.
1. A mapping table exists from observed status dialects to canonical enum.
1. No section claims taskmaster has `models.py` or standalone domain model without evidence.
1. Open UNKNOWNs are listed with explicit evidence-needed statements.
