---
id: MEMORY_PLANE
title: Memory Plane
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-02'
last_review: '2026-04-02'
next_review: '2026-07-01'
prelude: Memory Plane (reference) for dopemux documentation and developer workflows.
---
# MEMORY_PLANE.md

This document defines the memory layer of the dopemux system as observed from repo truth.

Memory is not a single system.
Memory authority is split.
Canonical boundaries are partially unresolved.

Do not unify this layer unless runtime evidence proves it.

---

## 1. Purpose

This file exists to:

- prevent collapsing multiple memory systems into one
- distinguish memory from PM and retrieval
- clarify what is canonical vs derived vs mirrored
- enforce correct usage of memory surfaces

If you treat memory as a single system, you will introduce drift.

---

## 2. Memory Surfaces

The repo contains multiple memory-related systems.

### 2.1 dope-memory

- Role: durable chronicle
- Type: append-only evidence store
- Function:
  - store historical events
  - preserve receipts
  - enable auditability

Characteristics:
- chronological
- persistent
- write-heavy
- not optimized for reasoning queries

---

### 2.2 ConPort

- Role: structured memory and knowledge graph
- Type: semantic + relational memory
- Function:
  - store decisions
  - represent relationships
  - support reasoning queries

Characteristics:
- queryable
- structured
- graph-oriented
- used by reasoning and planning systems

---

### 2.3 dope-context

- Role: retrieval system
- Type: index/search layer
- Function:
  - index code and documentation
  - enable lookup and recall

Characteristics:
- derived from source material
- not authoritative
- optimized for search, not truth

---

### 2.4 working-memory-assistant

- Role: operational memory surface
- Function:
  - interacts with memory systems
  - supports workflows and short-term state

Canonical authority:
- UNKNOWN

This system overlaps with other memory surfaces.
Its exact ownership boundaries are not resolved in repo truth.

---

## 3. Authority Model

Memory authority is split across systems.

No single system defines all memory truth.

### Canonical distinctions

- dope-memory:
  - canonical for **chronological evidence**
  - not canonical for workflow or PM state

- ConPort:
  - canonical for **structured decisions and relationships**
  - not canonical for raw event history

- dope-context:
  - canonical for **retrieval indexing only**
  - never canonical for truth itself

- working-memory-assistant:
  - authority is UNKNOWN

---

## 4. Memory vs PM

Memory participates in PM but does not own PM.

Observed interaction model:

- PM systems produce state changes
- those changes may be:
  - mirrored into dope-memory (receipts)
  - represented in ConPort (decisions/relations)

Implications:

- memory reflects PM activity
- memory does not define PM truth
- memory cannot be used as the source of PM authority

Agents do not derive PM state from memory alone.

---

## 5. Memory vs Retrieval

Retrieval is not memory authority.

- dope-context:
  - provides access to information
  - does not define truth

- retrieval outputs must always be traced back to:
  - source system
  - canonical writer

Do not:
- treat retrieved content as authoritative
- assume indexed content is current or canonical

---

## 6. Interaction Model

Memory systems interact but remain distinct.

Typical flow:

1. system action occurs (PM, workflow, or runtime event)
2. event may be written to:
   - dope-memory (chronicle)
   - ConPort (structured representation)
3. dope-context indexes relevant artifacts for retrieval

This is not guaranteed to be consistent across all systems.

Duplication and drift are possible.

---

## 7. Known Ambiguities

The repo does not resolve:

- exact boundary between dope-memory and ConPort responsibilities
- whether working-memory-assistant owns a canonical slice
- how memory synchronization is enforced across systems
- lifecycle rules for memory vs workflow state

These must remain `UNKNOWN` unless proven in runtime code.

---

## 8. Known Failure Modes

If this model is ignored, the system will drift.

Common failures:

- treating dope-memory as PM authority
- treating ConPort as a full memory replacement
- treating retrieval results as truth
- duplicating writes across systems without coordination
- creating conflicting representations of the same event

These failures produce systems that appear coherent but diverge over time.

---

## 9. Working Rules

When interacting with memory:

- identify which memory system is being used
- verify whether it is canonical for the data type
- trace data back to its source system
- distinguish:
  - chronicle (dope-memory)
  - structure (ConPort)
  - retrieval (dope-context)
