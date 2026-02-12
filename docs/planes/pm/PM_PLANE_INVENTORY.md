---
id: PM_PLANE_INVENTORY
title: Pm Plane Inventory
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-11'
next_review: '2026-05-12'
prelude: Pm Plane Inventory (explanation) for dopemux documentation and developer
  workflows.
---
# PM Plane Inventory (Phase 0)

Status: DRAFT (evidence-first)

## Scope
Phase 0 only. Inventory and reality check. No design.

## Evidence bundle pointers
- Evidence outputs folder:
  - docs/planes/pm/_evidence/PM-INV-00.outputs/
- Command list:
  - docs/planes/pm/_evidence/PM-INV-00.commands.txt

## Observed components (Verified)
Fill this section only with evidence references.

| Component | Location | Purpose (Observed) | Entry points | Storage | Task model | States | Integrations | Tests | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| task-orchestrator | services/task-orchestrator/ | TBD | TBD | TBD | TBD | TBD | TBD | TBD | path:line |
| taskmaster | services/taskmaster/ | TBD | TBD | TBD | TBD | TBD | TBD | TBD | path:line |
| dopemux CLI | src/dopemux/cli.py | TBD | CLI | TBD | TBD | TBD | TBD | TBD | path:line |
| event bus | src/dopemux/event_bus.py (or equivalent) | TBD | API | TBD | N/A | N/A | producers/consumers | TBD | path:line |
| leantime installer | installers/leantime/ | TBD | scripts | TBD | TBD | TBD | sync/bridge | TBD | path:line |

## Task lifecycle inventory (Verified)
Document task lifecycle and status transitions for each task system.

| System | Canonical task object name | Status/state representation | Transition function(s) | Idempotency strategy | Evidence |
|---|---|---|---|---|---|
| task-orchestrator | TBD | TBD | TBD | TBD | path:line |
| taskmaster | TBD | TBD | TBD | TBD | path:line |

## Event producers/consumers (Verified)
List PM-relevant event types and streams.

| Producer | Consumer | Stream/topic | Event types | Payload shape | Determinism risks | Evidence |
|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | path:line |

## Cross-plane wiring (Verified)
Document explicit integration touchpoints (only if evidenced).

| PM component | Memory/Chronicle | DopeQuery/ConPort | ADHD Engine | Notes | Evidence |
|---|---|---|---|---|---|
| task-orchestrator | TBD | TBD | TBD | TBD | path:line |
| taskmaster | TBD | TBD | TBD | TBD | path:line |

## Unknown or Missing (Phase 0)
Everything here must include what evidence is missing and how to get it.

| Question | Why it matters | How to resolve (exact file/command) |
|---|---|---|
| What is the PM canonical status source (Leantime vs internal)? | prevents drift | inspect docs/90-adr/* + installers/leantime + task-orchestrator sync code |
| Are decisions linked to tasks in a canonical store? | traceability | search for conport/dopequery references in task services |
| Does event bus persist PM events? | determinism | inspect event bus adapter implementation |
