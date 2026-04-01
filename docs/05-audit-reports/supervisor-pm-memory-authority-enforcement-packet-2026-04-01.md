---
id: supervisor_pm_memory_authority_enforcement_packet_2026_04_01
title: Supervisor PM and Memory Authority Enforcement Packet
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-06-30'
prelude: Implementation-facing supervisor packet that converts the current PM and memory authority drifts into concrete enforcement work items with proof targets.
graph_metadata:
  node_type: DocPage
  impact: high
---
# Supervisor PM and Memory Authority Enforcement Packet

## Authority targets to enforce

- `Leantime` owns PM entities and sprint state
- `Task Orchestrator` owns workflow legality, blockers, next action, and transitions
- `ConPort` owns decisions, progress, and durable project context
- `dope-memory` owns chronicle, replay, reflection, and supersession
- `dope-context` owns retrieval only
- `Serena v2` owns technical context only
- `dopecon-bridge` remains adapter-only

## Enforcement item 1. Remove Task Orchestrator dependence on bridge custom-data persistence

### Current violating path

- `WorkflowStore` reads and writes `workflow_ideas`, `workflow_epics`, and `workflow_audit` via dopecon-bridge custom-data APIs.

### Required replacement path

- move workflow persistence behind a dedicated Task Orchestrator-owned backing store or authoritative service path
- keep bridge usage limited to mediation, routing, or mirroring

### Allowed mirrors

- Leantime reflection after canonical workflow decisions
- ConPort or dope-memory references only where explicitly designed

### Forbidden direct path

- Task Orchestrator canonical workflow state depending on bridge custom-data as primary persistence

### Proof target

- workflow tests still pass
- runtime no longer requires bridge custom-data for primary workflow idea/epic/audit persistence
- bridge remains non-canonical in both docs and runtime wiring

## Enforcement item 2. Repair PM read-envelope authority drift

### Current violating path

- `src/dopemux/pm/reads.py` sets `canonical_backend="orchestrator"` for:
  - `pm_get_project_context`
  - `pm_get_sprint_snapshot`

### Required replacement path

- `pm_get_project_context` must report the correct canonical backend for durable project context
- `pm_get_sprint_snapshot` must report the correct canonical backend for PM sprint state
- provenance, supporting sources, and canonical backend fields must agree

### Forbidden direct path

- mismatched authority labels that force supervisor tools to infer the wrong owner

### Proof target

- targeted tests or assertions cover both envelopes
- no remaining contradiction between `canonical_backend` and provenance/source markers

## Enforcement item 3. Bind project-scoped Task Orchestrator transition route to the canonical transition path

### Current violating path

- `/api/projects/{project_id}/workflow/transition` returns a permanent unavailable receipt

### Required replacement path

- route delegates to the same canonical transition logic that owns workflow-significant state changes
- response includes real legality result, resulting state, and canonical receipt metadata

### Forbidden direct path

- direct Leantime status updates pretending to satisfy workflow transition authority

### Proof target

- integration or route-level tests prove a real transition path
- unavailable receipt disappears except for genuine outage/degraded cases

## Enforcement item 4. Retire or retarget dope-memory stdio transport away from legacy WMA

### Current violating path

- dope-memory stdio adapter still targets legacy WMA `8096`

### Required replacement path

- retarget stdio transport to the canonical dope-memory runtime on `3020`, or retire the adapter if it is not meant to survive

### Forbidden direct path

- any operator or MCP flow silently landing on WMA while claiming to speak to canonical dope-memory

### Proof target

- transport docs and runtime target match
- smoke or route check confirms canonical dope-memory endpoint is the one actually reached

## Priority order

1. Task Orchestrator persistence decoupling
2. PM read-envelope authority repair
3. project workflow transition binding
4. dope-memory stdio retarget or retirement

## Evidence basis

- [supervisor-pm-evidence-packet-2026-03-27.md](/private/tmp/dopemux-pm/evidence-closure/docs/05-audit-reports/supervisor-pm-evidence-packet-2026-03-27.md)
- [supervisor-memory-pm-authority-reconciliation-2026-03-27.md](/private/tmp/dopemux-pm/evidence-closure/docs/05-audit-reports/supervisor-memory-pm-authority-reconciliation-2026-03-27.md)
- `docs/planes/pm/_evidence/task-orchestrator-runtime-truth/`
- `docs/planes/pm/_evidence/leantime-runtime-truth/`
- `docs/planes/pm/_evidence/dopecon-bridge-runtime-truth/`
