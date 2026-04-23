---
id: adr-002
title: ADR-002 - PM-Mode Authority Split and Bounded Leantime Write Scope
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-23'
last_review: '2026-04-23'
next_review: '2026-05-23'
prelude: Architecture Decision Record for PM-mode action dispatch and Leantime write scope boundaries.
---

# ADR-002: PM-Mode Authority Split and Bounded Leantime Write Scope

**Status**: Proposed  
**Date**: 2026-04-23  
**Owners**: @hu3mann  
**Depends on**: ADR-001  
**Blocks**: build step 8 of §9.4a (PM-mode write dispatch)

## Context

PM mode must support feature design, research packets, ideas/epics/stories, task breakdown, workflow queue/blockers/approvals, Leantime metadata visibility, ConPort decisions/progress/context, and dope-memory historical receipts. Left unscoped, a PM-mode "edit task" action is ambiguous: does it write title (metadata) or status (workflow)? Left unscoped, `leantime` becomes a convenient write sink for every field visible in a Leantime pane, including status — which is owned by `task-orchestrator`. This would silently route workflow-significant mutations through a metadata service.

`PM_PLANE.md` and `system-boundaries.md` already enumerate split authorities; this ADR ratifies the PM-mode dispatch table and the Leantime write bound.

## Decision

1. **PM-mode action dispatch is split by authority**, not by pane:

   | Intent | Canonical Service | Confirm Label |
   |---|---|---|
   | metadata write | `leantime` | `WRITE -> leantime : <field>` |
   | workflow write (status, queue order, blockers, approvals) | `task-orchestrator` | `WRITE -> task-orchestrator : <action>` |
   | decision / progress write | `conport` | `WRITE -> conport : <action>` |
   | history receipt | `dope-memory` | `WRITE -> dope-memory : <action>` |

2. **A pane displaying a field does not imply that pane's backing service owns that field.** The confirm modal's target service name is canonical; the pane layout is not.

3. **Leantime write scope is bounded to passive metadata only.** Allowed fields:
   - title
   - description / notes
   - assignee
   - labels / tags
   - due date / dates
   - estimate
   - linked identifiers / references

4. **Leantime writes are forbidden for workflow-significant mutations**:
   - status transitions
   - queue reordering
   - blocker resolution
   - approval-state mutation

   These route to `task-orchestrator` regardless of which pane the operator invokes them from.

5. **`[a] approve` is role-gated** and operates only on `task-orchestrator`-controlled workflow objects. Approvals never route through `leantime`.

6. **Bridge and proxy services never own canonical state.** `dopecon-bridge` actions require `shift-Y` and render the adapter confirm label `ADAPTER -> dopecon-bridge : <action>`. `dopetask` is execution-only and does not own task or packet state.

## Consequences

**Accepted**:
- PM-mode input handling must disambiguate intent before dispatch, not after. The confirm modal text is the contract surface.
- A Leantime pane showing `status: in_progress` is read-only for that field from the Leantime authority; editing status from that pane dispatches to `task-orchestrator` and the confirm label reflects it.
- Integration tests must assert that no forbidden Leantime mutation ever lands on the `leantime` service, regardless of invocation path.

**Rejected alternatives**:
- *Route all PM-mode writes through a dopemux dispatcher that fans out silently*: rejected — hides the authority boundary the confirm modal is designed to expose.
- *Allow Leantime status writes as a convenience and reconcile later*: rejected — makes `leantime` and `task-orchestrator` race on the same field, violates single-writer invariant.
- *Let `dopecon-bridge` carry canonical state during outages*: rejected — bridges are adapters; §3.2 mechanism 3 requires visual segregation precisely to prevent this drift.

**Citations**: SPEC.md §3.1, §3.2, §3.4, §3.5, §5.4; `PM_PLANE.md`; `system-boundaries.md`; locked clarifications 9–12.

## Implementation Notes

- Step 8 (authority labeling) depends on this decision being binding. All confirm modals must validate their target service at runtime.
- The input handler must include a dispatch table mapping action intent → canonical service. This table is the implementation of this ADR.
- Role-gating for `[a] approve` does not block this ADR but depends on U4 (role model) being resolved.
- Supporting-view panes may show read-only status fields from `task-orchestrator` even when the backing pane implementation is `leantime`-centric. The `SRC:` tag must be accurate.
