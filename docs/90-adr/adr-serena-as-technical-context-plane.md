---
id: adr-serena-as-technical-context-plane
title: "ADR: Serena as technical context plane"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-09'
prelude: Bound Serena to technical and code-context authority without promoting it into PM, workflow, decision, or chronicle truth.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-conport-as-decision-progress-and-context-authority
    - adr-dope-memory-as-chronicle-memory-authority
    - adr-dope-context-as-search-and-retrieval-plane
    - adr-memory-trinity-authority-and-interaction-model
---

# ADR: Serena as technical context plane

**Status:** Proposed
**Date:** 2026-03-11
**Owners:** Dopemux Technical Context Plane / PM Plane / Integration Layer
**Decision Type:** Authority Boundary / Technical Context Architecture
**Scope:** Serena, ConPort, dope-memory, dope-context, Leantime, Task Orchestrator, PM-plane consumers

## Context

The Dopemux stack includes multiple systems that provide context, but not all context is the same.

Recent truth-pack extraction shows that Serena's strongest role is not PM authority, workflow authority, or durable decision authority. Its strongest role is as a technical/code-intelligence layer that helps operators and agents understand implementation state, code structure, tooling context, and environment-relevant technical information.

At the same time, Serena has important limitations and risks:

- its deployment/runtime reality drifts from the intended Dopemux-local implementation
- the Docker/runtime path appears to diverge from the local `services/serena` surface
- it may write progress or custom data into ConPort, which creates risk if semantics are not tightly bounded
- it is not an authoritative system for PM entities, workflow, or chronicle memory

Without an explicit authority boundary, Serena could be overused as if technical context were the same thing as PM truth or durable project context.

## Decision

**Serena is the technical/code context plane for the Dopemux architecture.**

This means Serena is authoritative for:

- technical/code intelligence
- implementation-facing context
- code-aware support and retrieval
- environment/tooling-aware technical assistance
- technical analysis and technical context assembly within its actual runtime scope

Serena is not authoritative for:

- PM operational entities
- workflow state or rules
- canonical decisions/progress/context
- chronicle/work-log memory
- semantic retrieval authority over all indexed corpora

## What Serena is authoritative for

Serena is authoritative for:

1. **Technical/code context**
   - code-structure-aware context
   - implementation-local technical details
   - tool/environment-aware technical reasoning support

2. **Code-intelligence support**
   - code navigation and code-oriented context assembly
   - developer-facing technical assistance
   - technical state interpretation where implemented

3. **Technical enrichment**
   - bounded technical metadata attached to work where appropriate
   - derived technical support signals that do not override canonical PM or context records

## What Serena is not authoritative for

Serena is not authoritative for:

- projects, tasks, sprints, milestones, or PM lifecycle
- blockers, next-action, workflow legality, or transition policy
- canonical decision records
- canonical progress records
- canonical durable project context
- canonical chronicle memory
- canonical semantic index truth outside its own implemented scope

## Relationship to ConPort

ConPort remains the canonical authority for:

- decisions
- progress
- structured durable project context

Serena may read from ConPort and may enrich workflows with technical context, but it must not redefine canonical decision/progress semantics.

If Serena writes progress-like or custom metadata into ConPort, that behavior must be:

- bounded
- documented
- non-conflicting with ConPort’s canonical object classes
- treated as an allowed producer into ConPort, not a competing authority

## Relationship to dope-memory

dope-memory remains the canonical chronicle memory authority.

Serena may emit or inform technical events that later appear in chronicle memory, but it does not own memory truth.

This preserves the split:

- **Serena** = technical context about implementation
- **dope-memory** = memory of what happened over time

## Relationship to dope-context

dope-context remains the canonical search/retrieval plane.

Serena may consume or benefit from retrieval support, but it is not the general semantic retrieval authority for all indexed corpora.

This preserves the split:

- **Serena** = technical/code context plane
- **dope-context** = semantic retrieval plane

## Relationship to Leantime

Leantime remains the canonical PM operational system of record.

Serena may support implementation-aware understanding of PM-linked work, but it does not own PM truth.

## Relationship to Task Orchestrator

Task Orchestrator remains the workflow authority.

Serena may assist with technical interpretation relevant to execution, but it does not define workflow legality, blockers, next-action, or progression policy.

## Runtime alignment rule

Serena must not be treated as a stable architectural authority until its **intended implementation** and **deployed runtime** are aligned.

This means:

- architecture decisions should reference the actual runtime surface, not aspirational local code alone
- deployment drift must be fixed before Serena is relied on as a stable PM-plane dependency
- tool counts, callable surfaces, and write behaviors must be taken from the active runtime, not from whichever code path is more flattering

## PM-plane implications

The PM plane may use Serena for tools such as:

- `pm_get_technical_context`
- `pm_get_implementation_context`
- `pm_get_code_impact_context`
- `pm_get_technical_risks` (only if grounded in implemented technical context surfaces)

The PM plane must not use Serena as the authority for:

- PM task truth
- workflow truth
- decisions/progress truth
- chronicle truth

## Rationale

This decision is necessary because “context” is too broad a word, and systems that provide useful technical context often get promoted into roles they did not earn.

Serena's real value is technical/code intelligence, not PM authority.

Keeping Serena in the technical context plane:

- preserves clean separation from PM truth
- avoids conflict with ConPort and dope-memory
- prevents technical enrichment from becoming accidental authority
- gives the PM plane a clean place to get implementation-aware support

## Rejected alternatives

### 1. Serena as PM-plane authority
Rejected because Serena does not own PM entities, workflow, or canonical context.

### 2. Serena as decision/progress authority
Rejected because that role belongs to ConPort.

### 3. Serena as chronicle memory authority
Rejected because that role belongs to dope-memory.

### 4. Serena as generalized search plane
Rejected because dope-context is the proper semantic retrieval authority.

## Consequences

### Positive

- cleaner separation of technical context from PM and memory authority
- clearer PM-plane routing
- reduced risk of context overlap
- better architectural discipline around implementation-aware assistance

### Negative

- deployment/runtime drift must be fixed before Serena can be treated as dependable
- some existing assumptions about Serena surfaces may need correction

## Required follow-up work

1. align Serena deployment/runtime with intended Dopemux-local implementation
2. document the actual active callable surface
3. bound and document any Serena → ConPort writes
4. ensure PM-plane tools treat Serena as technical context only
5. avoid using Serena as a substitute for workflow, PM, or context authorities

## Success criteria

This ADR is implemented successfully when:

- Serena is used only as the technical/code context plane
- Serena is not treated as PM, workflow, decision, or chronicle authority
- deployment/runtime matches intended implementation
- any writes into ConPort are bounded and non-conflicting
- PM-plane tools call Serena only for technical context use cases

## Final decision

**Adopt Serena as the technical/code context plane in the Dopemux architecture, with explicit exclusion from PM, workflow, decision, and chronicle authority.**
