## Canonical Integration Design

This design is an evidence-backed inference from the merged truth-pack and PM-pack evidence. It intentionally avoids claiming implementation details the packs do not prove.

## 1. Canonical authority model

- `Leantime` is the canonical PM-facing system of record.
- `Task Orchestrator` is the canonical workflow-law, dependency, and next-action engine.
- Durable decision canon beyond PM presentation is `Unresolved` within this two-repo evidence set. The Leantime pack points that responsibility outside the pair toward ConPort.

## 2. Operating rule

All workflow-significant changes should be adjudicated by `Task Orchestrator` before they are reflected into `Leantime`, and that adjudication must use Task Orchestrator’s sanctioned transition paths rather than raw role writes.

Why this is the strongest model:

- Leantime does not enforce legal transitions or blockers.
- Task Orchestrator does enforce legal transitions, blockers, and gated advancement on its transition-path tools.
- Leantime is explicitly the PM record authority for human-facing entities.

Evidence: `reports/leantime-repo-truth-pack/INTEGRATION_NOTES.md`, `reports/leantime-pm-workflow-pack/02-workflow-and-transition-analysis.md`, `reports/task-orchestratorrepo-truth-pack/WORKFLOW_AND_GATES.md`, `reports/task-orchestrator-pm-workflow-pack/02-workflow-legality-and-transition-analysis.md`.

## 3. Canonical ownership by concern

### PM-facing record state

Write canon: `Leantime`

Task Orchestrator may maintain an internal execution graph, but that graph should be treated as workflow-control state, not the public PM record.

### Workflow legality

Write canon: `Task Orchestrator transition tools only`

No direct Leantime status transition should be considered authoritative for legality by itself, and no direct Task Orchestrator role write should be treated as legality-bearing by itself.

### Blockers / dependencies

Write canon: `Task Orchestrator`

Do not overload Leantime `dependingTicketId` or entity relationships to represent blocker law.

### Next-action computation

Read canon: `Task Orchestrator`

Leantime can display the result, but it should not independently compute the canonical next action from PM fields alone.

### Decisions / progress

Use a split model:

- `Leantime` owns PM-visible decisions and PM-visible progress artifacts that it already stores.
- `Task Orchestrator` owns workflow-execution progress for its graph.
- Do not promote Task Orchestrator into the primary decision authority on current evidence.

### Chronicle / history / audit

Use a linked-dual-ledger model:

- `Leantime` remains the PM chronicle for PM entities.
- `Task Orchestrator` remains the workflow audit for triggers, role transitions, and gate outcomes.

## 4. Minimal canonical flow

1. Human or integration intent originates in Leantime or an external client.
2. If the change affects legality, blockers, or next-step readiness, the request is evaluated by Task Orchestrator first.
3. Task Orchestrator accepts or rejects using its own state machine and dependency graph.
4. Accepted outcomes are mirrored into Leantime so the PM-facing record stays current.
5. Leantime remains the visible PM record; Task Orchestrator remains the source for why the workflow move was legal.

This is an inference from the evidence, not a directly implemented flow in either pack.

## 5. Required invariants

- A Leantime status change is not sufficient evidence of workflow legality.
- A Task Orchestrator dependency edge is the only canonical blocker relation.
- A Leantime PM record and a Task Orchestrator work item must remain explicitly linkable; otherwise dual-store drift cannot be audited.
- Direct Leantime edits that bypass Task Orchestrator should be treated as reconciliation events, not quiet truth.
- Direct Task Orchestrator role writes that bypass the transition engine should be forbidden or treated as reconciliation events, not canonical workflow moves.
- A single merged audit stream should not replace the native ledgers; cross-linking is safer than collapsing semantics.

## 6. Why this model is optimal from the evidence

It is the only model that aligns with both packs without forcing either repo to pretend it implements something it does not:

- It keeps Leantime in the role its pack explicitly assigns to it.
- It keeps Task Orchestrator in the role its packs explicitly assign to it.
- It avoids inventing blocker or workflow semantics inside Leantime.
- It avoids inventing PM-record authority inside Task Orchestrator.
- It incorporates the PM-pack warning that the authority split is not self-enforcing unless bypass paths are constrained.

## 7. Explicit unresolved items

- A single canonical authority for durable decisions and rationale is unresolved within these two repos alone.
- A single canonical global chronology across both systems is not evidenced; linked dual ledgers are safer than asserting one.
- The exact cross-system identity mapping mechanism is not specified in the packs; only the need for stable linkage is justified.
