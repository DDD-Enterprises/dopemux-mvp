---
id: adr-task-orchestrator-as-workflow-authority
title: "ADR: Task Orchestrator as workflow authority"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-05-27'
next_review: '2026-08-25'
prelude: Delegate workflow legality, blockers, next-action, and progression policy to Task Orchestrator.
status: accepted
ratified_date: '2026-05-27'
graph_metadata:
  node_type: ADR
  impact: high
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-dopecon-bridge-narrowing-to-adapter-only-role
    - adr-leantime-json-rpc-plus-plugin-integration-strategy
    - adr-conport-as-decision-progress-and-context-authority
    - adr-task-orchestrator-claude-surface-integration
---

# ADR: Task Orchestrator as workflow authority

**Status:** Accepted (ratified 2026-05-27)
**Date:** 2026-03-11 (ratified 2026-05-27)
**Owners:** Dopemux Workflow Plane / PM Plane / Integration Layer
**Decision Type:** Authority Boundary / Workflow Architecture
**Scope:** Task Orchestrator, Leantime, dopecon-bridge, ConPort, dope-memory, PM-plane consumers

## Context

The Dopemux stack currently separates operational PM storage, durable context, memory, and coordination across multiple systems:

- Leantime
- Task Orchestrator
- ConPort
- dope-memory
- dopecon-bridge
- supporting retrieval/context systems

Recent truth-pack extraction established several important facts:

1. **Leantime is strong as an operational PM system of record**, but weak as a workflow engine
2. **dopecon-bridge currently overlaps with workflow behavior in unsafe ways**
3. **ConPort is for decisions/progress/context, not workflow progression**
4. **dope-memory stores chronicle memory, not workflow truth**

Leantime’s workflow semantics are especially important here. The extracted pack showed:

- unrestricted or weakly constrained task status transitions
- no meaningful workflow state machine
- no authoritative blocker logic
- no strong dependency enforcement
- no reliable next-action authority

This means Leantime is suitable for storing PM entity state, but not for governing workflow policy.

At the same time, `dopecon-bridge` currently performs some workflow-adjacent behavior:

- local task status updates
- local next-action-like behavior
- PRD-to-task creation flows
- event publication tied to task changes

This creates split-brain risk if `dopecon-bridge` is allowed to continue acting like a local workflow engine.

The architecture therefore needs one explicit workflow authority.

## Decision

**Task Orchestrator is the canonical workflow authority for the Dopemux PM plane.**

This means Task Orchestrator is authoritative for:

- workflow rules
- blockers and unblocking logic
- next-action computation
- state progression policy
- workflow gating
- execution sequencing
- handoff semantics
- rule-based workflow interpretation across work items

Task Orchestrator is not the canonical store for PM entities themselves.

## What Task Orchestrator is authoritative for

### 1. Workflow progression policy

Task Orchestrator defines:

- what transitions are allowed
- what transitions are blocked
- when work can advance
- what preconditions or gates must be satisfied
- what the next actionable work item is

### 2. Blocker logic

Task Orchestrator is authoritative for:

- blocked/unblocked interpretation
- dependency-aware workflow constraints
- gating rules tied to dependencies or execution sequencing
- workflow-level readiness

### 3. Next-action logic

Task Orchestrator is the only system that should be treated as authoritative for:

- priority queue / next task selection
- workflow-aware advancement
- ordering informed by blockers, dependencies, and state policy

### 4. Handoff and execution semantics

Task Orchestrator is authoritative for:

- execution handoffs
- stage/phase progression
- workflow-oriented coordination rules
- gating semantics across actor or subsystem handoff points

## What Task Orchestrator is not authoritative for

Task Orchestrator is not authoritative for:

- PM entity storage
- ticket/project/sprint canonical records
- structured durable decisions/progress/context
- chronological work-log memory
- semantic retrieval
- technical/code context

Those remain the responsibility of other systems.

## Relationship to Leantime

Leantime remains the canonical PM operational system of record.

That means Leantime is authoritative for:

- projects
- tickets/tasks as PM entities
- sprints
- milestones
- PM-local operational records

But Leantime is **not** authoritative for:

- workflow rules
- blocker interpretation
- next-action logic
- execution gating

Therefore:

- Leantime status fields are PM-facing operational state
- Task Orchestrator governs workflow meaning and workflow legality
- any Leantime integration must defer to Task Orchestrator where workflow interpretation matters

Leantime may display state, but Task Orchestrator defines workflow policy.

## Relationship to dopecon-bridge

`dopecon-bridge` must not act as workflow authority.

This means `dopecon-bridge` must not be canonical for:

- next-action computation
- blocker interpretation
- workflow progression
- local task state as workflow truth

Its role is adapter/routing/translation, not workflow governance.

If `dopecon-bridge` exposes endpoints like next-action or task mutation, those behaviors must resolve back to Task Orchestrator and/or the canonical PM entity store, not local bridge shadow state.

## Relationship to ConPort

ConPort remains canonical for:

- decisions
- progress
- structured durable context

Task Orchestrator may consume ConPort context when making workflow decisions, but ConPort does not become workflow authority by containing decision/progress context.

This preserves the separation between:

- **contextual truth**
- **workflow law**

## Relationship to dope-memory

dope-memory remains the canonical chronicle memory authority.

Task Orchestrator may emit workflow events that become chronicle entries, but dope-memory is not workflow authority.

This preserves the distinction between:

- **workflow policy**
- **memory of workflow events**

## PM-plane implications

The normalized PM-plane layer must treat Task Orchestrator as the authority behind tools such as:

- `pm_get_priority_queue`
- `pm_get_blockers`
- `pm_get_next_action`
- `pm_can_advance_work_item`
- `pm_transition_work_item`
- `pm_get_workflow_state`
- `pm_get_handoff_requirements`

Leantime-backed PM-plane calls may still provide operational task/project data, but any call that involves workflow legality, ordering, gating, or progression must route through Task Orchestrator.

## Leantime status vs workflow status rule

A PM entity may have a status in Leantime, but that must not be assumed to mean the workflow engine agrees with its progression.

Therefore:

- Leantime status alone does not establish workflow legality
- Task Orchestrator interpretation may override or constrain workflow progression even if Leantime permits arbitrary status changes
- integrations must not equate editable status fields with workflow authority

This is a key rule for preventing workflow drift.

## Adapter policy rule

Adapters and bridges must not invent workflow authority.

Specifically:

- `dopecon-bridge` must not compute authoritative next-action from local shadow state
- no adapter may become canonical for blockers or transition legality
- adapters may proxy workflow calls, but must not replace Task Orchestrator logic

## Rationale

This decision is necessary because workflow authority is the easiest responsibility to accidentally duplicate.

Leantime has PM entity truth but weak workflow discipline.
dopecon-bridge has coordination value but unsafe local workflow-adjacent behavior.
ConPort has contextual truth but not execution-law semantics.
dope-memory has chronicle truth but not transition authority.

Task Orchestrator is the only subsystem that cleanly fits workflow governance.

If workflow authority is not centralized there, the likely result is:

- Leantime status drift
- bridge-local next-action drift
- inconsistent blocker semantics
- duplicate transition logic
- impossible-to-debug agent behavior

This ADR prevents that by making workflow a first-class, explicitly owned concern.

## Rejected alternatives

### 1. Leantime as workflow authority

Rejected because extracted evidence shows weak or nonexistent workflow enforcement and unconstrained transitions.

### 2. Shared workflow authority between Leantime and Task Orchestrator

Rejected because that would create interpretation conflicts with no clean arbitration mechanism.

### 3. dopecon-bridge as workflow coordinator

Rejected because the bridge already demonstrates unsafe local authority creep and shadow-state drift.

### 4. ConPort-informed workflow without a dedicated workflow authority

Rejected because context does not equal execution law.

## Consequences

### Positive

- one canonical home for workflow semantics
- simpler PM-plane tool routing
- lower split-brain risk
- clearer distinction between PM storage and workflow policy
- better agent behavior consistency

### Negative

- integrations must explicitly respect workflow-vs-PM storage separation
- some existing bridge/local behaviors must be removed or rewritten
- Leantime status changes may need policy wrapping to keep PM and workflow state aligned

## Required follow-up work

1. ensure `dopecon-bridge` next-action behavior is removed or delegated
2. define PM-plane workflow tools backed by Task Orchestrator
3. align Leantime task/status mutations with Task Orchestrator policy
4. ensure workflow events are emitted clearly for ConPort and dope-memory consumers
5. document how PM-facing status and workflow-facing legality interact
6. prevent adapter-local task shadows from becoming workflow decision inputs

## Success criteria

This ADR is implemented successfully when:

- Task Orchestrator is the only workflow authority
- no other subsystem computes canonical next-action independently
- no adapter owns blocker logic
- Leantime remains PM SoR without becoming workflow law
- PM-plane workflow tools resolve to Task Orchestrator
- workflow events can be consumed by ConPort and dope-memory without ambiguity about where workflow authority lives

## Final decision

**Adopt Task Orchestrator as the canonical workflow authority for the Dopemux PM plane, with all workflow legality, blockers, next-action, and progression semantics delegated to it.**
