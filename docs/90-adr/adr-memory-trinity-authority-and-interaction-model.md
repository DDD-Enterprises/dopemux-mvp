---
id: adr-memory-trinity-authority-and-interaction-model
title: "ADR: Memory Trinity authority and interaction model"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-11'
prelude: Defines ConPort, dope-memory, and dope-context as distinct canonical memory planes to prevent cross-plane authority escalation.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-conport-as-decision-progress-and-context-authority
    - adr-dope-memory-as-chronicle-memory-authority
    - adr-serena-as-technical-context-plane
    - adr-dope-context-as-search-and-retrieval-plane
---

# ADR: Memory Trinity authority and interaction model

**Status:** Proposed
**Date:** 2026-03-11
**Owners:** Dopemux Memory Plane / Context Plane / PM Plane
**Decision Type:** Architecture / Authority Boundary / Cross-Plane Interaction
**Scope:** ConPort, dope-memory, dope-context, adapters, bridges, PM-plane consumers

## Context

Dopemux’s memory architecture has been evolving across multiple systems that all touch “memory,” “context,” “history,” and “retrieval,” but they do not serve the same role.

Recent evidence from repository truth packs and supervisor memory docs points to a stable conceptual split across three core planes:

- **ConPort / DopeQuery** for structured durable decisions, progress, and project context
- **dope-memory** for temporal chronicle memory, replay, recap, reflection, and trajectory
- **dope-context** for semantic retrieval over indexed code/docs/artifacts

The same docs also make an important architectural rule explicit:

- cross-plane systems may reference, project, index, or summarize another plane’s data
- but they must **not silently overwrite or redefine another plane’s canonical object class**

This matters because the surrounding stack already shows pressure toward overlap:

- adapters like `dopecon-bridge` can drift into shadow authority
- memory products can be mistaken for canonical context
- graph/query systems can be mistaken for canonical stores
- retrieval systems can be mistaken for durable knowledge authorities

Without a formal Memory Trinity ADR, the architecture risks turning “memory” into a vague blob that every subsystem claims to own.

## Decision

Dopemux adopts a **Memory Trinity** model with three distinct canonical planes:

### 1. ConPort / DopeQuery

Canonical authority for:

- structured durable project context
- decisions
- progress records
- durable contextual objects intended for reuse across systems

### 2. dope-memory

Canonical authority for:

- chronological work-log / chronicle memory
- recap/replay/reconstruction over work chronology
- reflections derived from chronicle entries
- trajectory state derived from chronicle entries
- durable temporal narrative of work

### 3. dope-context

Canonical authority for:

- semantic retrieval
- ranking/search over indexed code/docs/artifacts
- retrieval-oriented context assembly from indexed corpora

These three planes are complementary, not interchangeable.

## Canonical object classes

### ConPort canonical object classes

ConPort is canonical for:

- decision objects
- progress objects
- structured durable project-context objects
- stable contextual references and linked metadata where supported

ConPort is not canonical for:

- chronicle memory
- semantic retrieval index truth
- PM operational entities
- workflow state

### dope-memory canonical object classes

dope-memory is canonical for:

- chronicle entries
- work-log event memory
- recap/replay memory products
- reflection memory products
- trajectory memory products
- chronicle-level provenance and supersession chains

dope-memory is not canonical for:

- decisions themselves
- progress records themselves
- structured durable project context objects
- semantic retrieval indexes
- PM entities
- workflow legality

### dope-context canonical object classes

dope-context is canonical for:

- retrieval indexes
- semantic chunks/embeddings/search artifacts
- ranking/retrieval outputs over indexed corpora

dope-context is not canonical for:

- decision truth
- progress truth
- chronicle truth
- PM entity truth
- workflow truth

## Shared invariant

### No silent authority escalation

No adapter, cache, proxy, bridge, mirror, search index, summary layer, or graph projection may silently escalate into authority over another plane’s canonical object class.

This means:

- a projection is not a source of truth
- an index is not a source of truth
- a summary is not a source of truth
- a mirrored copy is not a source of truth
- a graph representation is not a source of truth unless explicitly promoted by separate decision

This invariant applies especially to:

- `dopecon-bridge`
- `conport-kg`
- shadow DDG stores
- any future PM-plane read model
- any future dashboard/summary service

## Cross-plane interaction rules

### Rule 1. ConPort → dope-memory

When a canonical decision or progress event occurs in ConPort, dope-memory may ingest an event-derived chronicle entry that references the canonical ConPort ID.

Allowed:

- chronicle entry referencing `decision_id`
- reflection about the decision’s effect on work
- replay timeline showing when decision-related work happened

Not allowed:

- dope-memory redefining the canonical decision object

### Rule 2. dope-memory → dope-context

Curated or redacted chronicle-derived material may be indexed into dope-context for semantic retrieval, provided provenance is preserved.

Allowed:

- indexing summaries, excerpts, or retrieval-safe chronicle artifacts
- storing provenance pointers back to dope-memory

Not allowed:

- dope-context becoming canonical chronicle memory

### Rule 3. ConPort → dope-context

ConPort context and decision/progress artifacts may be indexed into dope-context for retrieval if needed, with provenance retained.

Allowed:

- semantic indexing of canonical context
- retrieval-friendly chunking

Not allowed:

- dope-context becoming canonical for decision/progress/context truth

### Rule 4. Multi-plane reads are allowed

A user- or agent-facing query may fuse data across planes, but the response must preserve provenance and must not collapse distinct authorities into one implied source of truth.

## Query composition model

The system should follow this query rule:

### Single-plane first

If a request maps clearly to one plane, query that plane directly.

Examples:

- “What was the decision?” → ConPort
- “What happened over time?” → dope-memory
- “Find relevant docs/code/notes” → dope-context

### Multi-plane only when needed

If a request spans chronology, structured decisions, and semantic evidence, a query broker may compose across planes.

Examples:

- “What decision was made, when did it affect work, and where is the supporting code/doc evidence?”

That may require:

- ConPort for decision object
- dope-memory for timeline of effect
- dope-context for supporting artifacts

### Provenance is mandatory

A multi-plane answer must preserve:

- source plane
- canonical IDs
- timestamps / scope
- whether an item is canonical vs derived

## Relation to PM-plane authorities

This ADR does not replace the PM-plane authority ADRs. It complements them.

### Leantime

Leantime remains canonical for operational PM entities. It may provide promotable material into memory/context systems, but it is not part of the Memory Trinity.

### Task Orchestrator

Task Orchestrator remains canonical for workflow authority. It may emit events consumed by dope-memory or ConPort, but it is not a memory plane authority.

### dopecon-bridge

dopecon-bridge is not part of the Memory Trinity. It may route, translate, proxy, or emit events between planes, but it may not silently become canonical for any Trinity object class.

### conport-kg

conport-kg is not currently canonical. If activated later, its default role should be graph projection/query over canonical ConPort context, not independent durable authority.

## Mirror, cache, and projection rules

### ConPort mirrors/projections

Any mirror, cache, or projection of ConPort data must be explicitly labeled non-canonical unless a separate ADR says otherwise.

### dope-memory mirrors/projections

For dope-memory:

- SQLite chronicle is canonical
- Postgres mirror is non-canonical
- Redis Streams are transport only, not authority

### dope-context indexes

Indexes/chunks/embeddings are canonical only as retrieval artifacts, not as source truth for the content they reference.

## Promotion and provenance rules

### Promotion

Promotion between planes is allowed only when the target plane is storing its own canonical object class.

Examples:

- ConPort decision event → dope-memory chronicle entry
- dope-memory curated chronicle → dope-context retrieval chunk

### Provenance

All cross-plane promoted/projected/indexed records must preserve enough provenance to trace back to the canonical source plane.

Minimum expectations:

- source plane
- canonical ID if available
- timestamp or version context
- whether item is canonical, projected, or indexed

## Rationale

This decision is necessary because “memory” is not one thing.

Without explicit separation, the architecture risks:

- decision truth leaking into chronicle stores
- chronicle products being mistaken for structured context
- search indexes being mistaken for durable knowledge authority
- adapters and projections becoming accidental authorities

The Trinity model keeps each plane strong at what it is best at:

- **ConPort** for structured durable context
- **dope-memory** for lived temporal work history
- **dope-context** for semantic retrieval

This also keeps the surrounding PM-plane architecture clean:

- Leantime = PM entity truth
- Task Orchestrator = workflow truth
- Memory Trinity = context, chronicle, retrieval

## Rejected alternatives

### 1. One generalized memory authority

Rejected because temporal chronicle, structured context, and semantic retrieval are materially different problem classes.

### 2. dope-memory as generalized context authority

Rejected because dope-memory is strongest as chronicle memory, not structured decision/progress/context authority.

### 3. dope-context as durable knowledge authority

Rejected because semantic retrieval artifacts are not the same as canonical structured context or chronicle truth.

### 4. ConPort as sole memory system

Rejected because structured context and temporal chronicle are not the same thing, and forcing them together would weaken both.

## Consequences

### Positive

- clear separation of memory concerns
- cleaner authority model
- lower risk of shadow authority growth
- better provenance discipline
- easier design of cross-plane query fusion
- stronger foundation for PM-plane tool design

### Negative

- cross-plane composition requires more explicit routing and provenance handling
- projections and indexes must be explicitly labeled non-canonical
- some existing subsystems may need narrowing or cleanup to comply

## Required follow-up work

1. add the “no silent authority escalation” invariant to the PM-plane authority ADR set
2. ensure adapters like `dopecon-bridge` follow the Trinity rules
3. keep conport-kg non-canonical until separate remediation and decision
4. document provenance requirements for cross-plane reads/writes
5. define PM-plane read tools that compose across Trinity planes safely
6. align runtime reality with documented transport assumptions where drift exists

## Success criteria

This ADR is implemented successfully when:

- ConPort is the only canonical structured context/decision/progress authority
- dope-memory is the only canonical chronicle memory authority
- dope-context is the only canonical semantic retrieval authority
- projections/indexes/mirrors are explicitly non-canonical
- adapters do not silently escalate authority
- multi-plane reads preserve provenance and canonical-source identity

## Final decision

**Adopt the Memory Trinity model in which ConPort is canonical for structured durable context, dope-memory is canonical for chronicle memory, and dope-context is canonical for semantic retrieval, with explicit prohibition on silent authority escalation across planes.**
