---
id: adr-dopecon-bridge-narrowing-to-adapter-only-role
title: "ADR: dopecon-bridge narrowing to adapter-only role"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-09'
prelude: Narrow dopecon-bridge from mixed authority into an adapter, router, and translator over canonical PM-plane backends.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-leantime-json-rpc-plus-plugin-integration-strategy
    - adr-conport-as-decision-progress-and-context-authority
    - adr-task-orchestrator-as-workflow-authority
---

# ADR: dopecon-bridge narrowing to adapter-only role

**Status:** Proposed
**Date:** 2026-03-11
**Owners:** Dopemux PM Plane / Integration Layer / Memory Plane / Workflow Plane
**Decision Type:** Architecture / Service Responsibility Narrowing
**Scope:** `services/dopecon-bridge`

## Context

`dopecon-bridge` currently sits in the middle of several critical systems:

- Leantime
- Task Orchestrator
- ConPort
- event streams
- cross-service client routing

Truth-pack extraction showed that the active runtime of `dopecon-bridge` is smaller than the full subtree and consists of the FastAPI service rooted in `main.py` plus the `dopecon_bridge/` package. Legacy and planned root-level modules such as KG endpoints, orchestrator endpoints, root event bus logic, and pattern-detection layers are not part of the active runtime unless explicitly imported and wired.

The current active runtime exposes multiple HTTP endpoints across auth, events, tasks, DDG, and health surfaces. It also stores local task and DDG-related records in PostgreSQL and uses Redis streams for event routing.

Evidence from the discovery and Phase 2 packs shows that `dopecon-bridge` currently behaves as more than a translator:

- it creates local task records
- it serves next-action-like behavior from local bridge state
- it updates local task status
- it stores DDG-related shadow tables
- it publishes events into shared streams
- it overlaps with Leantime, Task Orchestrator, and ConPort

This creates split-brain risk across the PM plane.

The strongest risks identified are:

- local `tasks` state diverges from Leantime
- task status updates do not propagate cleanly to canonical systems
- next-action behavior competes with Task Orchestrator
- DDG decision/progress concepts overlap with ConPort
- write endpoints are insufficiently protected
- some event writes are unauthenticated
- shared client expectations drift from active runtime reality

The current truth-pack recommendation for `dopecon-bridge` is to narrow it to an adapter role.

## Decision

`dopecon-bridge` will be narrowed to an **adapter/router/translator-only** role.

It will no longer be treated as an authority for:

- PM task state
- next-action computation
- workflow progression
- decision/progress authority
- canonical DDG records
- canonical PM entities of any kind

Instead, `dopecon-bridge` will be responsible only for:

- cross-system routing
- request/response translation
- contract mediation
- event transport/orchestration
- health aggregation
- bounded integration glue between systems

## What dopecon-bridge is allowed to do

`dopecon-bridge` may:

1. translate between external PM-plane calls and subsystem-specific contracts
2. proxy requests to canonical authorities
3. aggregate health/status views from multiple systems
4. route authenticated event traffic into shared messaging infrastructure
5. maintain temporary adapter-local transport state if clearly non-canonical
6. provide normalization logic for subsystem payloads
7. expose PM-plane-friendly endpoints that are backed by canonical systems

## What dopecon-bridge must stop doing

`dopecon-bridge` must not:

1. own canonical task records
2. act as the source of truth for task status
3. compute or serve canonical next-action based on diverged local task state
4. own canonical decisions or progress records
5. maintain de facto shadow authorities that can drift from upstream systems
6. expose unsafe side-effect endpoints directly to agents without policy wrapping
7. publish unauthenticated writes into shared event streams

## Canonical delegations

### Tasks and PM entity lifecycle

Canonical authority: **Leantime**

`dopecon-bridge` may reference, translate, and proxy task-related calls, but task lifecycle truth belongs to Leantime unless and until a different PM entity authority is explicitly adopted.

### Workflow, blockers, and next-action

Canonical authority: **Task Orchestrator**

`dopecon-bridge` must not compute or present local next-action as authoritative. Any next-action or blocker logic must be delegated to Task Orchestrator.

### Decisions, progress, structured durable context

Canonical authority: **ConPort**

`dopecon-bridge` may proxy or translate decision/progress calls, but must not maintain a competing canonical DDG decision/progress store.

### Chronicle / temporal memory

Canonical authority: **dope-memory**

`dopecon-bridge` may emit events that contribute to memory, but it does not own chronicle memory.

## Required service changes

### 1. Remove or de-authorize local task authority

The local `tasks` table must be treated as one of the following:

- removed entirely
- explicit transient staging state
- explicit non-canonical shadow state with bounded lifetime

It must not be treated as canonical task truth.

### 2. Remove or de-authorize local DDG storage

`ddg_decisions`, `ddg_progress`, and related shadow tables must be:

- removed
- converted to non-canonical cache/projection
- or replaced by direct proxying to ConPort

They must not remain ambiguous.

### 3. Delegate next-action to Task Orchestrator

Any endpoint or behavior that provides next-action or task-prioritization semantics must use Task Orchestrator as the source of truth.

### 4. Delegate decision/progress to ConPort

Any endpoint or behavior that surfaces decisions or progress must route through ConPort rather than local shadow records.

### 5. Lock down write safety

All side-effectful writes must be:

- authenticated
- policy-wrapped
- scoped to explicit canonical backends
- idempotent where required

Unauthenticated shared event writes must be removed.

### 6. Quarantine legacy/planned surfaces

Legacy or excluded modules must remain excluded from active runtime truth unless explicitly reactivated through a separate decision.

## Endpoint policy implications

### Safe direct exposure

Only clearly read-only, well-bounded, non-authoritative adapter endpoints may be exposed directly.

### Policy-wrapped only

These classes of endpoints must be policy-wrapped:

- PRD/task creation flows
- task status updates
- cross-system side-effect orchestration
- event publication
- decision/progress mutation

### Never expose directly

Endpoints that mutate shadow-local state without canonical propagation must not be exposed directly to agents.

## Rationale

The current active runtime of `dopecon-bridge` provides real value as a coordination layer, but it becomes dangerous when it drifts into local authority.

This narrowing decision is necessary because:

- Leantime already exists as PM SoR
- Task Orchestrator already exists as workflow authority
- ConPort already exists as decision/progress/context authority
- dopecon-bridge has proven overlap with all three
- the current auth and write-safety posture is not good enough to justify local authority
- adapter logic is useful, but shadow authority is harmful

Narrowing `dopecon-bridge` preserves the useful parts of the service while removing the parts most likely to create long-term reconciliation pain.

## Rejected alternatives

### 1. Keep dopecon-bridge as mixed authority

Rejected because current evidence shows high overlap, split-brain risk, and weak write safety.

### 2. Promote dopecon-bridge to PM-plane hub authority

Rejected because this would duplicate existing canonical systems and worsen drift.

### 3. Let dopecon-bridge remain a task shadow store

Rejected because local task truth without canonical reconciliation is unstable and misleading.

### 4. Let dopecon-bridge retain local DDG authority

Rejected because ConPort is the proper location for decisions/progress/context authority.

## Consequences

### Positive

- cleaner authority boundaries
- less split-brain risk
- simpler PM-plane reasoning
- safer agent exposure model
- clearer routing responsibilities

### Negative

- some current convenience behavior must be rewritten or delegated
- bridge-local tables may need migration, deprecation, or deletion
- some endpoints may need to be removed or re-scoped
- short-term implementation effort increases

## Required follow-up work

1. create a narrowing/remediation packet for `dopecon-bridge`
2. classify all active endpoints as:
   - safe read-only
   - policy-wrapped
   - never expose directly
3. remove or de-authorize local task/DDG tables
4. rewire next-action to Task Orchestrator
5. rewire decision/progress to ConPort
6. authenticate and constrain event publication
7. align shared client surfaces with real active runtime
8. document active vs legacy runtime boundaries permanently

## Success criteria

This ADR is implemented successfully when:

- `dopecon-bridge` no longer acts as canonical for tasks
- `dopecon-bridge` no longer acts as canonical for decisions/progress
- next-action is sourced from Task Orchestrator
- decision/progress is sourced from ConPort
- unsafe unauthenticated writes are eliminated
- adapter endpoints reflect canonical backend behavior
- local shadow state is removed or clearly labeled non-canonical

## Final decision

**Adopt an adapter-only target architecture for `dopecon-bridge` and remove its mixed-authority role over time.**
