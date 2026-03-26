---
id: adr-dope-context-as-search-and-retrieval-plane
title: "ADR: dope-context as search and retrieval plane"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-09'
prelude: Bound dope-context to semantic retrieval and provenance-aware search rather than canonical PM, workflow, context, or chronicle truth.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-conport-as-decision-progress-and-context-authority
    - adr-dope-memory-as-chronicle-memory-authority
    - adr-serena-as-technical-context-plane
    - adr-memory-trinity-authority-and-interaction-model
---

# ADR: dope-context as search and retrieval plane

**Status:** Proposed
**Date:** 2026-03-11
**Owners:** Dopemux Retrieval Plane / Context Plane / PM Plane
**Decision Type:** Authority Boundary / Retrieval Architecture
**Scope:** dope-context, ConPort, dope-memory, Serena, PM-plane consumers

## Context

Dopemux includes several systems that deal with context, but only one is intended to be the semantic retrieval/search plane.

Recent truth-pack extraction and memory-plane docs indicate that **dope-context** is the subsystem designed for:

- semantic retrieval
- ranking/search over indexed artifacts
- retrieval-oriented context assembly from code/docs and other indexed corpora

It is explicitly not the canonical authority for:

- decisions/progress/context truth
- chronicle memory
- PM operational entities
- workflow rules

This matters because search systems often drift into quasi-authoritative roles when consumers stop distinguishing between:

- indexed representation
- retrieved evidence
- canonical source truth

Without an explicit ADR, dope-context could be misused as if semantic retrieval artifacts were the same thing as canonical project context.

## Decision

**dope-context is the search and retrieval plane for the Dopemux architecture.**

This means dope-context is authoritative for:

- semantic retrieval indexes
- ranking and retrieval behavior over indexed corpora
- retrieval-oriented context assembly within its implemented scope
- search-plane outputs derived from indexed artifacts

It is not authoritative for:

- canonical decisions/progress/context
- chronicle/work-log truth
- PM entity truth
- workflow truth
- technical/code context authority outside retrieval semantics

## What dope-context is authoritative for

dope-context is authoritative for:

1. **Retrieval indexes**
   - semantic chunks
   - vector/index artifacts
   - retrieval-oriented representations of code/docs/artifacts

2. **Retrieval behavior**
   - ranking
   - recall
   - retrieval filtering within implemented boundaries
   - evidence selection from indexed corpora

3. **Search-plane outputs**
   - retrieval results
   - ranked evidence sets
   - search-derived context assembly

## What dope-context is not authoritative for

dope-context is not authoritative for:

- canonical decision objects
- canonical progress records
- canonical structured project context
- canonical chronicle entries
- canonical PM entities
- canonical workflow legality or next-action
- canonical technical/code truth beyond retrieval support

## Relationship to ConPort

ConPort remains the canonical authority for:

- decisions
- progress
- structured durable project context

dope-context may index ConPort-derived material and make it retrievable, but it must not redefine canonical ConPort truth.

This preserves the split:

- **ConPort** = what the durable context is
- **dope-context** = how relevant contextual evidence is retrieved

## Relationship to dope-memory

dope-memory remains the canonical chronicle memory authority.

dope-context may index curated or redacted chronicle-derived material with provenance, but it must not become canonical for chronicle truth.

This preserves the split:

- **dope-memory** = what happened over time
- **dope-context** = how chronicle-derived evidence is found

## Relationship to Serena

Serena remains the technical/code context plane.

dope-context may support Serena with retrieval over indexed artifacts, but Serena is still the technical context layer and dope-context is still the search/retrieval layer.

This preserves the split:

- **Serena** = technical/code context assistance
- **dope-context** = retrieval/search substrate

## Relationship to Leantime and Task Orchestrator

Leantime remains PM operational authority and Task Orchestrator remains workflow authority.

dope-context may index relevant PM or workflow-related artifacts where allowed, but it does not become authoritative for PM or workflow semantics by making them searchable.

## Provenance rule

All dope-context retrieval outputs must preserve or expose enough provenance to identify the canonical source plane or system where possible.

Minimum expectations include:

- source system or source plane
- canonical ID or source reference where available
- whether the result is indexed/projection material rather than canonical source truth

This prevents retrieval outputs from being mistaken for primary records.

## PM-plane implications

The PM plane may use dope-context for tools such as:

- `pm_search_project_knowledge`
- `pm_search_code_and_docs`
- `pm_find_supporting_evidence`
- `pm_retrieve_related_artifacts`

The PM plane must not use dope-context as the authority for:

- PM task/project state
- workflow legality
- decision/progress truth
- chronicle truth

## Hard dependency and runtime reality rule

Where implemented, dope-context’s retrieval/search role depends on its actual runtime indexing stack.

Architecture and PM-plane integration must therefore be based on:

- implemented indexes
- real runtime dependencies
- actual supported corpora
- actual supported retrieval behavior

and not on aspirational configs or unused declared index types.

## Rationale

This decision is necessary because retrieval systems are incredibly useful and therefore constantly at risk of being treated like truth stores.

That is the wrong mental model.

dope-context is strongest when it is allowed to be:

- retrieval-focused
- ranking-focused
- provenance-aware
- authority-boundary aware

It becomes dangerous when retrieved evidence is confused with canonical durable truth.

Formalizing dope-context as the search/retrieval plane:

- protects ConPort and dope-memory from search-plane authority creep
- gives the PM plane a clean retrieval backend
- clarifies how evidence should be fused without flattening source authority

## Rejected alternatives

### 1. dope-context as durable context authority
Rejected because durable structured context belongs to ConPort.

### 2. dope-context as chronicle authority
Rejected because chronicle memory belongs to dope-memory.

### 3. dope-context as PM/workflow authority
Rejected because PM/workflow truth belongs elsewhere.

### 4. retrieval results treated as canonical truth
Rejected because indexed retrieval artifacts are representations, not source authority.

## Consequences

### Positive

- clear separation between retrieval and source truth
- cleaner PM-plane read composition
- reduced authority confusion
- stronger provenance discipline

### Negative

- integrations must preserve provenance and avoid flattening retrieved results into source truth
- configs/docs that overstate implemented retrieval scope need cleanup

## Required follow-up work

1. align configs/docs with implemented dope-context reality
2. document supported corpora/indexes clearly
3. ensure PM-plane tools treat dope-context as retrieval only
4. preserve provenance in all retrieval outputs
5. keep decision/context/chronicle truth in their canonical planes

## Success criteria

This ADR is implemented successfully when:

- dope-context is used only as the search/retrieval plane
- retrieval outputs preserve provenance
- no consumer treats indexed artifacts as canonical source truth
- PM-plane read composition uses dope-context as supporting evidence, not authority replacement

## Final decision

**Adopt dope-context as the search and retrieval plane in the Dopemux architecture, with explicit exclusion from canonical PM, workflow, decision, progress, and chronicle authority.**
