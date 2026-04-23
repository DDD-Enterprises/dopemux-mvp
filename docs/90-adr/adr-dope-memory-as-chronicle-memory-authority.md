---
id: adr-dope-memory-as-chronicle-memory-authority
title: "ADR: dope-memory as chronicle memory authority"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-09'
prelude: Make dope-memory the canonical chronicle-memory layer while excluding it from PM, workflow, and canonical decision authority.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-conport-as-decision-progress-and-context-authority
    - adr-task-orchestrator-as-workflow-authority
    - adr-memory-trinity-authority-and-interaction-model
    - adr-serena-as-technical-context-plane
    - adr-dope-context-as-search-and-retrieval-plane
---

# ADR: dope-memory as chronicle memory authority

**Status:** Proposed
**Date:** 2026-03-11
**Owners:** Dopemux Memory Plane / PM Plane / Context Plane
**Decision Type:** Authority Boundary / Memory Architecture
**Scope:** dope-memory, working-memory-assistant subtree, ConPort, Leantime, Task Orchestrator, PM-plane consumers

## Context

The `services/working-memory-assistant` subtree contains **two distinct personalities**:

1. **dope-memory**
   - active, deployed runtime
   - FastAPI service
   - Docker/compose/registry presence
   - canonical SQLite chronicle
   - active callable tools over HTTP
   - optional Redis Streams intake
   - optional Postgres mirror

2. **WMA / working-memory-assistant prototype**
   - co-located but not the deployed reality
   - partially implemented snapshot/recovery system
   - not the authoritative active runtime of the subtree

Truth-pack extraction showed that the active deployed service is **dope-memory**, not the WMA prototype.

The active dope-memory runtime implements:

- canonical ledger resolution
- append-only chronicle semantics
- deterministic IDs
- provenance and supersession/correction semantics
- recap/replay/reflection/trajectory surfaces
- direct HTTP tool surface
- optional eventbus intake
- optional one-way Postgres mirror

This makes dope-memory a strong candidate for one specific role:

> **durable chronological work-memory authority**

At the same time, the extraction also showed what it is **not**:

- not PM operational truth
- not workflow authority
- not canonical decision/progress authority
- not Leantime replacement
- not Task Orchestrator replacement

Without a formal authority decision, there is a risk that dope-memory gets misused as a generalized context or PM state store simply because it is durable and well-structured.

## Decision

**dope-memory is the canonical authority for chronological work-log / chronicle memory in the Dopemux architecture.**

This means dope-memory is authoritative for:

- chronological work entries
- durable work-log chronology
- recap/replay/reconstruction over work chronology
- reflections derived from chronicle data
- trajectory state derived from chronicle data
- supersession/correction chains within chronicle memory
- durable memory of work events and linked references

dope-memory is **not** authoritative for:

- PM entity lifecycle
- task/ticket canonical state
- workflow state or transition policy
- canonical decisions
- canonical progress records
- strategic PM entity authority
- semantic retrieval authority
- technical/code context authority

## What dope-memory is authoritative for

### 1. Chronicle entries

This includes:

- append-only work-log entries
- linked event records that form a temporal narrative
- entries representing what happened, when, and in what sequence
- durable event-linked records with provenance

### 2. Chronicle-derived memory products

This includes:

- recap outputs
- replay/reconstruction surfaces
- reflections
- trajectory summaries and state
- issue/task linkage as memory references
- superseded/corrected memory chains

### 3. Canonical chronicle ledger rules

This includes:

- canonical ledger path resolution
- deterministic chronicle write identity rules
- append-only write discipline
- fail-closed write path behavior
- correction and supersession semantics
- provenance preservation inside chronicle memory

## What dope-memory is not authoritative for

### 1. PM operational entities

Canonical authority remains elsewhere for:

- projects
- tickets/tasks
- sprints
- milestones
- PM-facing operational records

These are not owned by dope-memory.

### 2. Workflow semantics

Canonical authority remains elsewhere for:

- blockers
- state progression
- next-action
- workflow gates
- execution sequencing

dope-memory may record workflow-related events, but does not own workflow rules.

### 3. Canonical decisions and progress

dope-memory may record decision-linked events and references, but canonical decisions/progress remain outside dope-memory.

A dope-memory record can say:

- a decision was logged
- a decision affected work
- a decision is linked to this chronicle entry

But dope-memory is not the canonical source of the decision itself.

### 4. Technical/code context

dope-memory is not the canonical system for code intelligence or technical environment context.

## Relationship to adjacent authorities

### Leantime

Leantime remains the canonical PM operational system of record.

dope-memory may ingest or receive work events that reference Leantime entities, but it does not own Leantime task/project truth.

### Task Orchestrator

Task Orchestrator remains the workflow authority.

dope-memory may store chronicle entries about workflow transitions, blockers, and execution events, but it does not govern or compute workflow policy.

### ConPort

ConPort remains the canonical authority for:

- decisions
- progress
- structured durable project context

dope-memory may reference ConPort decisions or progress records, but it does not replace them.

### dope-context

dope-context remains the search/retrieval plane.

dope-memory may expose memory retrieval within chronicle space, but it is not the semantic retrieval authority for code/docs corpora.

### Serena

Serena remains the technical/code context layer.

dope-memory may contain chronicle references to technical work, but not canonical technical context.

## Decision-linked memory rule

dope-memory may store **memory about decisions**, but not **canonical decision records**.

Allowed:

- decision-linked work-log entries
- references to ConPort decision IDs
- reflections referencing decisions
- timeline reconstruction involving decisions

Not allowed:

- becoming the primary structured decision store
- redefining canonical decision fields
- acting as a decision-truth replacement for ConPort

This preserves a clean split:

- **ConPort** = what the decision is
- **dope-memory** = how the decision appeared in lived work chronology

## Task/workflow-linked memory rule

dope-memory may store **memory about tasks and workflow events**, but not **canonical task/workflow state**.

Allowed:

- task-started/task-blocked/task-failed/task-completed chronicle entries
- recap of task history
- trajectory summaries over work evolution
- references to task IDs from canonical PM/workflow systems

Not allowed:

- canonical task state ownership
- workflow transition authority
- next-action authority
- blocker authority

This preserves a clean split:

- **Leantime** = PM task entity truth
- **Task Orchestrator** = workflow state/rules
- **dope-memory** = memory of what happened around that work

## Mirror and transport rules

When other systems mirror packet lifecycle into dope-memory chronicle space, dope-memory remains authoritative only for the chronicle receipt, not the packet's canonical workflow or PM state.

For Dopemux TUI packet pin mirrors, the chronicle receipt model is:

- append-only receipt stream
- field name `pinned_at`
- `pinned_at: <timestamp>` means pinned at that time
- `pinned_at: null` means an explicit unpin receipt
- the effective pin state is resolved from the latest receipt for the packet id

This preserves chronicle truthfulness:

- no prior receipt is mutated
- pin and unpin are both historical events
- downstream readers can reconstruct pin history without inventing mutable state inside dope-memory

### SQLite chronicle

The local SQLite chronicle is canonical.

It is the authoritative durable store for dope-memory’s chronicle layer.

### Postgres mirror

The Postgres mirror is **non-canonical**.

It may be used for:

- replication
- reporting
- analysis
- operational convenience
- integration support

It must not be treated as the canonical chronicle authority.

### Redis Streams / eventbus

Redis Streams are **transport/intake only**.

Event intake does not create authority by itself.

An event entering through Redis becomes authoritative in dope-memory only when it is written into the canonical chronicle according to dope-memory’s write rules.

## WMA prototype exclusion rule

The WMA prototype inside the same subtree is **not part of the active dope-memory authority model** unless future deployment/runtime proof explicitly changes that fact.

This means:

- WMA-specific snapshot/recovery behavior must not contaminate dope-memory authority conclusions
- WMA-specific PostgreSQL assumptions must not be treated as active dope-memory truth
- any future activation of WMA requires a separate architectural decision

## Integration implications for the PM plane

The PM plane may use dope-memory for:

- `pm_get_work_chronicle`
- timeline/replay views
- recap of recent work
- work reflections
- trajectory/history context
- chronicle-linked issue/task references

The PM plane must not use dope-memory as the authority for:

- task lifecycle
- PM state truth
- workflow transitions
- decisions/progress truth

This means PM-plane tools should treat dope-memory as a **memory backend**, not an operational backend.

## Write policy implications

### Safe write category

Safe or mostly safe writes are those that append or correct chronicle memory within dope-memory’s authority boundary.

### Policy-wrapped category

Writes that ingest external events or perform cross-system linking should be policy-wrapped where needed.

### Never-authoritative category

Writes that would attempt to redefine:

- canonical decisions
- canonical task state
- workflow state
- PM entity truth

must not be routed into dope-memory as if it owned those concepts.

## Rationale

This decision is necessary because dope-memory is strong enough to be mistaken for a generalized truth store.

That would be a mistake.

Its actual strength is:

- temporal structure
- append-only chronology
- durable chronicle
- replay/recap/reflection value
- provenance-aware work memory

Those are exactly the traits you want in a chronicle memory system.

But they do not make it the right home for:

- PM entities
- workflow rules
- decisions/progress truth

By formalizing this boundary now, the architecture avoids “durable store gravity,” where any durable subsystem gradually accretes responsibility just because it exists.

## Rejected alternatives

### 1. Use dope-memory as generalized durable context authority

Rejected because structured durable context belongs in ConPort, not chronicle memory.

### 2. Let dope-memory co-own decisions

Rejected because this would create conflict with ConPort and blur the line between decision truth and decision-linked memory.

### 3. Let dope-memory co-own task/workflow state

Rejected because Leantime and Task Orchestrator already occupy those roles more appropriately.

### 4. Treat WMA prototype as co-equal active runtime

Rejected because current deployment/runtime evidence does not support that.

## Consequences

### Positive

- clean temporal-memory authority
- strong separation from PM and workflow authority
- clear boundaries with ConPort
- easier memory-promotion discipline
- reduced risk of chronicle becoming a catch-all truth store

### Negative

- some tempting cross-domain uses of dope-memory must be explicitly refused
- integration code must preserve reference links to external authorities rather than absorbing their truth

## Required follow-up work

1. finish dope-memory Phase 2 contract extraction
2. document canonical write surfaces vs derived/query surfaces
3. document mirror semantics explicitly in runtime/config docs
4. ensure PM-plane tools treat dope-memory as memory backend only
5. keep WMA prototype in excluded/appendix status unless activated later
6. link chronicle entries to canonical ConPort/Leantime/Task Orchestrator IDs where appropriate

## Success criteria

This ADR is implemented successfully when:

- dope-memory is the only canonical chronicle memory authority
- no one treats Postgres mirror as canonical
- no one treats eventbus intake as authority by itself
- dope-memory stores decision-linked memory but not canonical decisions
- dope-memory stores task/workflow-linked memory but not canonical task/workflow state
- WMA prototype remains excluded from active authority assumptions
- PM-plane tools use dope-memory only for chronicle/memory functions

## Final decision

**Adopt dope-memory as the canonical chronicle memory authority for the Dopemux architecture, with strict exclusion from PM entity, workflow, and canonical decision authority.**
