---
id: pm-plane-write-adjudication-model
title: PM Plane Write Adjudication Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-26'
next_review: '2026-06-10'
prelude: Canonical PM-plane write model for adjudicating mutations across Leantime, Task Orchestrator, ConPort, dope-memory, and adapter layers.
---
# PM Plane Write Adjudication Model

This document defines how PM-plane writes are adjudicated so runtime implementations can enforce the authority split frozen by the ADR set in [`docs/90-adr/adr-index.md`](../../90-adr/adr-index.md).

## Canonical authority spine

- **Leantime** is the PM-facing record authority for projects, work items, sprints, milestones, and PM metadata.
- **Task Orchestrator** is the workflow authority for legality, blockers, next-action, sequencing, and progression policy.
- **ConPort** is the authority for decisions, progress, and durable contextual attachments.
- **dope-memory** is the chronicle-memory authority for timeline/event truth.
- **dopecon-bridge** is never a canonical writer. It may only proxy or normalize writes under explicit policy.

## Mutation classes in scope

The PM plane recognizes these canonical mutation classes:

1. `create_work_item`
2. `update_pm_metadata`
3. `transition_workflow_state`
4. `block_unblock_work_item`
5. `attach_decision`
6. `log_progress`
7. `emit_chronicle_event`
8. `mirror_workflow_outcome_into_leantime`
9. `attach_technical_context`
10. `attach_retrieval_search_metadata`

These ten classes are the minimum write surface for PM-plane implementations. New write classes must be mapped into this model before they are exposed.

## Core adjudication rules

### Rule 1. Workflow-significant mutations require Task Orchestrator adjudication

Any mutation that changes workflow legality, blockers, readiness, ordering, next-action, or progression semantics must be adjudicated by Task Orchestrator before any reflection into Leantime or any adapter-visible success response.

This includes:

- `transition_workflow_state`
- `block_unblock_work_item`
- `mirror_workflow_outcome_into_leantime`
- any PM mutation that carries status or transition semantics, even if initiated through a Leantime-backed surface

### Rule 2. Decision and progress mutations resolve to ConPort

Any mutation whose primary purpose is to create, update, or durably attach decision/progress/context semantics must resolve to ConPort.

This includes:

- `attach_decision`
- `log_progress`
- `attach_technical_context` when the attachment must become durable PM-plane context
- `attach_retrieval_search_metadata` when the attachment must become durable PM-plane context

### Rule 3. Chronicle mutations resolve to dope-memory

Any mutation whose primary purpose is to append or correct the work chronicle must resolve to dope-memory.

This includes:

- `emit_chronicle_event`
- chronicle reflections or replay-safe corrections that stay within dope-memory's object class

### Rule 4. Adapter and proxy layers may not silently escalate authority

Adapter layers may translate, validate, or normalize writes, but they may not:

- become the canonical writer for a mutation class
- invent local truth when an upstream canonical backend is unavailable
- hide failed canonical writes behind "best effort" local persistence
- mirror state into a canonical-looking local store without explicit non-canonical labeling

### Rule 5. Mirror writes are secondary, not primary

Mirror writes are permitted only after the canonical writer has accepted the mutation. Mirrors must preserve:

- canonical IDs
- provenance
- whether the mirror is read-only, cache-like, or reflective

### Rule 6. Reconciliation is class-specific and fail-closed

When canonical and mirrored state diverge:

- workflow-significant truth is resolved by Task Orchestrator
- PM record truth is resolved by Leantime
- durable decision/progress/context truth is resolved by ConPort
- chronicle truth is resolved by dope-memory

Adapters must fail closed rather than present local shadow state as authoritative.

## Canonical write path

Every PM-plane write should follow this sequence:

1. Classify the requested mutation.
2. Resolve the canonical writer for that mutation class.
3. Run any required pre-check against the canonical precheck authority.
4. Execute the canonical write.
5. Reflect to approved mirrors only after the canonical write succeeds.
6. Return a response that includes canonical IDs and provenance.
7. Trigger reconciliation only according to the owning authority's rules.

## Runtime constraint: current Task Orchestrator surface gap

The active runtime now exposes project-scoped queue, blocker, and workflow-state envelopes through Task Orchestrator-backed PM-plane reads, but the project-scoped transition route is still not bound to a canonical runtime transition engine.

Current implementation behavior:

- `pm_get_priority_queue`, `pm_get_blockers`, and `pm_get_workflow_state` route to Task Orchestrator and fail closed when the workflow authority is unavailable
- workflow-significant bridge routes must fail closed instead of substituting bridge-local state
- Leantime status mutation paths must not be treated as workflow adjudication
- `pm_transition_work_item` may exist as a canonical helper, but any runtime path that lacks an authoritative Task Orchestrator transition binding must return an explicit unavailable result rather than claim transition success

## Boundary clarifications

### Leantime writes that are allowed directly

Leantime may directly own:

- creation of PM work items
- updates to PM metadata that do not carry workflow legality
- reflection of already-adjudicated workflow outcomes into PM-facing record fields

### Leantime writes that are not self-authorizing

Leantime may not self-authorize:

- status transitions as workflow law
- blocker state as workflow truth
- next-action or readiness decisions

### Serena and dope-context attachments

Serena and dope-context remain supporting planes. If their outputs need to become durable PM-plane context, the attachment is written to ConPort with provenance pointing back to the technical or retrieval source.

### Bridge-local data stores

Any surviving local bridge table is transitional and non-canonical. Bridge-local persistence must never be used to justify bypassing the adjudication rules above.

## Implementation expectations

- PM-plane write tools must map one-to-one onto the mutation classes in this model.
- Policy-wrapped adapters must reject writes that target the wrong authority.
- All write-capable bridge surfaces must document their canonical backend and forbidden direct paths.
- Reconciliation behavior must be explicit in code and docs, not inferred from retries or local caches.

## Related ADRs

- [`docs/90-adr/adr-pm-plane-authority-boundaries.md`](../../90-adr/adr-pm-plane-authority-boundaries.md)
- [`docs/90-adr/adr-task-orchestrator-as-workflow-authority.md`](../../90-adr/adr-task-orchestrator-as-workflow-authority.md)
- [`docs/90-adr/adr-conport-as-decision-progress-and-context-authority.md`](../../90-adr/adr-conport-as-decision-progress-and-context-authority.md)
- [`docs/90-adr/adr-dope-memory-as-chronicle-memory-authority.md`](../../90-adr/adr-dope-memory-as-chronicle-memory-authority.md)
- [`docs/90-adr/adr-dopecon-bridge-narrowing-to-adapter-only-role.md`](../../90-adr/adr-dopecon-bridge-narrowing-to-adapter-only-role.md)
