---
id: adr-pm-plane-authority-boundaries
title: "ADR: PM Plane Authority Boundaries"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-11'
next_review: '2026-06-09'
prelude: PM-plane authority model for canonical system responsibilities, write boundaries, and integration routing.
status: proposed
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-dopecon-bridge-narrowing-to-adapter-only-role
    - adr-leantime-json-rpc-plus-plugin-integration-strategy
    - adr-conport-as-decision-progress-and-context-authority
    - adr-dope-memory-as-chronicle-memory-authority
    - adr-task-orchestrator-as-workflow-authority
    - adr-memory-trinity-authority-and-interaction-model
    - adr-serena-as-technical-context-plane
    - adr-dope-context-as-search-and-retrieval-plane
---

# ADR: PM Plane Authority Boundaries

**Status:** Proposed
**Date:** 2026-03-11
**Owners:** Dopemux PM Plane / Memory Plane / Workflow Plane
**Decision Type:** Architecture / Authority Boundaries
**Scope:** Leantime, Task Orchestrator, ConPort, dope-memory, dopecon-bridge, dope-context, Serena, conport-kg

## Context

Dopemux is evolving into a multi-system PM plane with overlapping responsibilities across:

- operational PM software
- workflow/orchestration logic
- durable context and decisions
- chronological memory
- semantic retrieval
- technical/code intelligence
- cross-system adapters/bridges

Recent evidence-first truth-pack extraction across the active systems shows that several components currently overlap in ways that create authority ambiguity and split-brain risk.

The biggest confirmed risks are:

- **Leantime** is a strong PM entity store but has weak workflow enforcement
- **Task Orchestrator** is the natural workflow authority
- **ConPort** is the intended authority for decisions/progress/context, but its invariants are not yet fully enforced
- **dope-memory** is a real durable chronicle store, but should not be confused with PM or decision authority
- **dopecon-bridge** currently behaves like a mixed adapter + shadow authority and must be narrowed
- **dope-context** is retrieval/search, not truth
- **Serena** is technical context, not PM truth
- **conport-kg** is architecturally important but not operationally ready enough to be canonical

Without explicit authority boundaries, the PM plane will drift into duplicated writes, contradictory state, and unresolvable reconciliation problems.

## Decision

The PM plane will use the following authority model.

### 1. Leantime is the canonical PM operational system of record

Leantime is authoritative for:

- projects
- goals
- milestones
- work items/tasks
- sprint planning
- user-facing PM state

Leantime is not authoritative for:

- workflow rules
- durable memory
- technical context

### 2. Task Orchestrator is the canonical workflow authority

Task Orchestrator is authoritative for:

- workflow rules
- blockers and unblocking logic
- next-action computation
- state progression policy
- workflow gating
- execution sequencing
- handoff semantics
- rule-based workflow interpretation across work items

Task Orchestrator is not the canonical PM entity store.

### 3. ConPort is the canonical authority for decisions, progress, and structured durable project context

ConPort is authoritative for:

- decisions
- progress records
- structured project context
- durable contextual records intended for reuse across systems

ConPort is not authoritative for:

- PM task lifecycle
- workflow transitions
- chronological work log

This authority is accepted as the target architecture even though runtime invariant enforcement is not yet complete.

### 4. dope-memory is the canonical authority for chronological work chronicle memory

dope-memory is authoritative for:

- chronological work log / chronicle entries
- durable work-log chronology
- recap/replay/reconstruction over chronicle entries
- reflections derived from chronicle entries
- trajectory state derived from chronicle entries
- supersession/correction chains within chronicle memory
- durable memory of work events and linked references

dope-memory is not authoritative for:

- decisions themselves
- PM task lifecycle
- workflow state
- project/ticket canonical truth

### 5. dopecon-bridge is an adapter/router/translator only

dopecon-bridge must be treated as:

- translation layer
- contract mediation layer
- event routing layer
- health aggregation layer
- cross-system client orchestration layer

dopecon-bridge must not be treated as canonical for:

- tasks
- next-action
- decision/progress
- workflow state
- PM entity authority

Its current mixed-authority behavior is architectural debt and must be narrowed.

### 6. dope-context is the canonical search/retrieval plane

dope-context is authoritative for:

- semantic retrieval over code/docs/indexed artifacts
- retrieval/ranking behavior within its search domain

It is not authoritative for:

- PM entities
- workflow
- decisions
- durable memory truth

### 7. Serena is the canonical technical/code context layer

Serena is authoritative for:

- technical/code intelligence
- implementation-facing context
- tool/environment-aware technical retrieval and support

It is not authoritative for:

- PM task truth
- workflow
- decisions
- chronicle memory

### 8. conport-kg is not canonical until remediated

conport-kg is currently treated as:

- architecturally important
- potentially useful graph/context infrastructure
- non-canonical
- blocked pending remediation and runtime validation

It must not be treated as authoritative until runtime, wiring, tests, and authority boundaries are repaired.

## Integration consequences

### PM-plane normalized tools must sit above the subsystem surfaces

Agents should not consume raw subsystem-specific surfaces as their primary PM interface.

Instead, Dopemux should define normalized PM-plane tools such as:

- `pm_get_project_context`
- `pm_get_priority_queue`
- `pm_get_blockers`
- `pm_update_work_item`
- `pm_get_sprint_snapshot`
- `pm_get_decision_context`
- `pm_get_work_chronicle`
- `pm_search_project_knowledge`
- `pm_get_technical_context`

These tools should delegate to the canonical authority for each concern.

### Leantime integration strategy

Leantime should be integrated primarily through:

- **JSON-RPC** as the stable external seam
- optional plugin support for hooks, UI injection, and internal extension seams

Leantime’s MCP path is not yet mature enough to be treated as the primary contract surface.

### dopecon-bridge narrowing requirement

dopecon-bridge must be remediated so that:

- local task shadow state is removed or explicitly non-canonical
- local DDG decision/progress shadow state is removed or explicitly non-canonical
- next-action is delegated to Task Orchestrator
- decision/progress is delegated to ConPort
- unauthenticated writes are removed
- side-effect-heavy write surfaces are policy-wrapped

### Memory promotion boundary

Promotion into durable memory/context must follow these rules:

- Leantime operational entities remain canonical in Leantime
- decisions/progress remain canonical in ConPort
- chronicle/work-log memory remains canonical in dope-memory
- HTML-rich or noisy content must be normalized before promotion
- raw comments, UI state, queue chatter, and transient event noise must not be promoted without normalization

## Rationale

This decision is based on the extracted behavior of the current systems:

- Leantime is broad, stable, and operationally central, but weak as a workflow engine
- Task Orchestrator is the only subsystem that naturally fits workflow governance
- ConPort is the intended durable decision/progress/context system
- dope-memory is a real canonical chronicle system, not just a cache
- dopecon-bridge is valuable as coordination infrastructure but dangerous as a local authority
- dope-context and Serena are clearly supportive context systems, not PM truth stores
- conport-kg is not runtime-ready enough to safely join the authority set

The alternative, allowing multiple systems to co-own tasks, decisions, next-action, and memory semantics, would create:

- split-brain task truth
- duplicated decision records
- contradictory workflow states
- invalid memory promotion
- fragile reconciliation logic
- unsafe agent write behavior

## Rejected alternatives

### 1. Leantime as both PM SoR and workflow authority

Rejected because Leantime’s workflow semantics are too weak and unconstrained.

### 2. dopecon-bridge as PM-plane authority hub

Rejected because it already shows shadow-state drift, weak auth, and split-brain risk.

### 3. dope-memory as generalized context authority

Rejected because dope-memory is specifically strong as chronicle memory, not structured decision/project authority.

### 4. ConPort + conport-kg as a combined immediate canonical context stack

Rejected for now because conport-kg is not operationally ready.

### 5. Multiple equal authorities with reconciliation

Rejected because the current system does not have the invariant enforcement needed to make this safe.

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

### High priority

1. **dopecon-bridge narrowing/remediation**
2. **ConPort surface/invariant hardening**
3. **dope-memory Phase 2 completion**
4. **Serena deployment-alignment**
5. **conport-kg remediation before any authority promotion**

### Medium priority

6. define normalized PM-plane tool contracts
7. add explicit policy wrappers around all side-effectful PM-plane writes
8. define memory-promotion normalization rules for Leantime content

## Success criteria

This ADR is successfully implemented when:

- no subsystem besides Leantime is treated as canonical for PM entities
- no subsystem besides Task Orchestrator is treated as canonical for workflow state/progression
- no subsystem besides ConPort is treated as canonical for decisions/progress/context
- no subsystem besides dope-memory is treated as canonical for chronicle memory
- dopecon-bridge no longer maintains de facto local authority
- PM-plane tools route to the correct canonical backends
- normalization rules exist for promotion into durable memory/context

## Final decision

**Adopt the authority model defined above as the working architecture for the Dopemux PM plane.**
