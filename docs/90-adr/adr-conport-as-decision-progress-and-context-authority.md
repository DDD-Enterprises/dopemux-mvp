---
id: adr-conport-as-decision-progress-and-context-authority
title: "ADR: ConPort as decision, progress, and context authority"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-09'
prelude: ConPort is the canonical source for decisions, progress, and durable structured project context across the PM plane.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-dopecon-bridge-narrowing-to-adapter-only-role
    - adr-dope-memory-as-chronicle-memory-authority
    - adr-memory-trinity-authority-and-interaction-model
    - adr-serena-as-technical-context-plane
    - adr-dope-context-as-search-and-retrieval-plane
---

# ADR: ConPort as decision, progress, and context authority

**Status:** Proposed
**Date:** 2026-03-11
**Owners:** Dopemux Memory Plane / PM Plane / Context Plane
**Decision Type:** Authority Boundary / Context Architecture
**Scope:** ConPort, dopecon-bridge, dope-memory, conport-kg, PM-plane consumers

## Context

The current Dopemux stack contains multiple systems that touch decision-like, progress-like, and contextual records:

- ConPort
- dopecon-bridge
- dope-memory
- conport-kg
- Serena and other consumers that may read or write contextual metadata

Truth-pack extraction shows that **ConPort is the intended canonical store** for decisions, progress, and structured durable project context. It exposes multiple callable surfaces, including FastMCP, JSON-RPC, and REST, and persists to PostgreSQL with Redis as cache. It also emits decision and progress events.

At the same time, the extraction also showed important problems:

- ConPort authority is currently **more conventional than enforced**
- surface drift exists across FastMCP, JSON-RPC, and REST
- some tools are dark or inconsistently exposed
- invariant claims in docs do not fully match implementation reality
- `dopecon-bridge` has local DDG tables that overlap with ConPort concepts
- `dope-memory` stores memory *about* decisions and progress, but should not be the decision authority
- `conport-kg` is architecturally relevant but not runtime-ready enough to be canonical

Without a formal decision, the system risks letting “context” and “decision” semantics leak across multiple stores.

## Decision

**ConPort is the canonical authority for decisions, progress, and structured durable project context.**

This means:

- decisions are canonical in ConPort
- progress records are canonical in ConPort
- structured durable project context is canonical in ConPort
- other systems may reference, mirror, index, summarize, or project this data
- other systems must not become competing canonical stores for the same concepts

## What ConPort is authoritative for

ConPort is authoritative for:

1. **Decision records**
   - decision identity
   - decision metadata
   - decision status/history where supported
   - structured decision payloads

2. **Progress records**
   - project/work progress entries
   - structured progress updates
   - progress-linked context

3. **Structured durable project context**
   - project-level durable notes/context
   - structured contextual records intended for reuse across systems
   - contextual artifacts that are not merely transient chronicle events

4. **Stable contextual references**
   - IDs and cross-links used by other systems to reference durable context

## What ConPort is not authoritative for

ConPort is not authoritative for:

- PM entity lifecycle
- task/ticket/sprint canonical state
- workflow rules
- blocker semantics
- next-action logic
- chronological work-log authority
- semantic retrieval authority
- technical/code context authority

Those belong elsewhere in the architecture.

## Consequences for adjacent systems

### dopecon-bridge

`dopecon-bridge` must not be a canonical store for DDG decisions or progress.

Its local DDG tables must be treated as one of the following only:

- temporary adapter-local projection
- non-canonical shadow state pending removal
- cache
- transitional migration artifact

They must not remain ambiguous.

If `dopecon-bridge` needs decision/progress information, it should:

- proxy to ConPort
- cache with explicit non-canonical semantics
- or request ConPort-backed data through a standardized callable surface

It must not continue as an equal authority.

### dope-memory

`dope-memory` may store:

- chronicle entries about decisions
- work-log references to decision IDs
- reflections derived from decision events
- recap/trajectory context involving decisions

But it is not authoritative for the decisions themselves.

This means:

- decision identity and canonical structured meaning remain in ConPort
- dope-memory stores memory *about* decision events, not the canonical decision object

### conport-kg

`conport-kg` must not be treated as canonical for decisions or durable context until remediation is complete.

Until then, AGE graph nodes and graph-derived structures must be treated as:

- derived graph projection
- query helper
- non-canonical graph representation

If and when conport-kg becomes runtime-real, its role should still default to **graph projection/query over canonical ConPort records**, not independent decision authority.

### Serena and other consumers

Serena and other context consumers may:

- read ConPort records
- enrich work with ConPort references
- attach metadata or derived context in clearly bounded namespaces

They must not silently redefine canonical decision/progress semantics outside ConPort.

## Callable surface policy

ConPort currently exposes multiple callable surfaces. That is acceptable temporarily, but the architecture will treat this as **one authority with one logical contract**, not multiple competing truths.

### Required rule

The PM plane must choose and standardize on **one preferred callable surface and one payload convention** for ConPort-backed operations.

Until that standardization is complete:

- all integrations must treat surface differences as adapter concerns
- no downstream service may reinterpret surface drift as permission to invent its own canonical records

### Immediate policy

For now, ConPort remains canonical **despite** callable surface drift.  
But hardening and standardization are required follow-up work.

## Normalization rule

When ConPort data is consumed elsewhere:

- the canonical record stays in ConPort
- projections/summaries/search indexes are allowed
- derived copies must carry provenance and non-canonical semantics
- mutation of canonical decision/progress records must resolve back to ConPort

This is especially important for:

- dopecon-bridge
- dope-memory
- future graph projections
- retrieval/indexing systems
- dashboard/summary layers

## Relationship to PM plane

The PM plane should use ConPort for:

- `pm_get_decision_context`
- structured progress retrieval
- durable contextual enrichment
- context references attached to projects/tasks/sprints where needed

The PM plane should **not** use other systems as the canonical source for those concepts.

That means:

- Leantime remains PM SoR
- Task Orchestrator remains workflow authority
- ConPort remains decision/progress/context authority
- dope-memory remains chronicle authority

This ADR is one piece of that larger authority spine.

## Rationale

This decision is necessary because the current stack already contains overlap pressure:

- ConPort is supposed to be canonical
- dopecon-bridge stores DDG-shaped data
- dope-memory stores chronicle events referencing decisions
- conport-kg models graph representations of context and decision-like objects

Without a formal boundary, each layer can slowly grow its own “decision” model until reconciliation becomes impossible.

ConPort is the best place to anchor canonical decision/progress/context truth because:

- it is already designed for that role
- other systems naturally consume rather than originate that class of truth
- it fits the PM-plane need for structured durable context
- it separates decision/context authority from PM entity authority and workflow authority

## Rejected alternatives

### 1. Let dopecon-bridge remain a co-authority for decisions/progress

Rejected because it already shows drift and is being narrowed to adapter-only.

### 2. Let dope-memory act as generalized context authority

Rejected because dope-memory is strongest as chronicle memory, not as canonical structured decision authority.

### 3. Promote conport-kg to immediate canonical graph authority

Rejected because it is not runtime-ready and would create another authority collision.

### 4. Keep ConPort as “intended” canonical without a formal decision

Rejected because that is how systems drift into accidental plural authorities.

## Consequences

### Positive

- one clear home for decisions/progress/context
- cleaner PM-plane composition
- simpler adapter behavior
- less split-brain risk
- better memory-boundary discipline
- clearer future graph projection model

### Negative

- ConPort now needs hardening work to deserve its authority status operationally
- drift across callable surfaces must be normalized
- some existing shadow tables and ambiguous behaviors must be deprecated

## Required follow-up work

1. choose and standardize one preferred ConPort callable surface
2. align tool names, payload shapes, and defaults across exposed surfaces
3. expose or retire dark methods intentionally
4. document and enforce authority invariants
5. de-authorize or remove DDG shadow tables in dopecon-bridge
6. ensure dope-memory stores only decision-linked memory, not canonical decision truth
7. keep conport-kg non-canonical until remediation and later decision

## Success criteria

This ADR is implemented successfully when:

- ConPort is the only canonical source for decisions/progress/context
- no downstream system treats local DDG/decision/progress shadows as canonical
- PM-plane tools resolve those concepts back to ConPort
- graph and memory systems carry provenance and non-canonical semantics where appropriate
- ConPort surface drift is treated as an adapter concern, not an authority ambiguity

## Final decision

**Adopt ConPort as the canonical authority for decisions, progress, and structured durable project context across the Dopemux PM plane.**
