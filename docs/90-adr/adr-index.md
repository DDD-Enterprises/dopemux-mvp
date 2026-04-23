---
id: adr-index
title: "ADR Index"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Canonical index for the PM-plane ADR authority set and related architecture decisions.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to:
    - adr-pm-plane-authority-boundaries
    - adr-dopecon-bridge-narrowing-to-adapter-only-role
    - adr-leantime-json-rpc-plus-plugin-integration-strategy
    - adr-conport-as-decision-progress-and-context-authority
    - adr-dope-memory-as-chronicle-memory-authority
    - adr-task-orchestrator-as-workflow-authority
    - adr-memory-trinity-authority-and-interaction-model
    - adr-serena-as-technical-context-plane
    - adr-dope-context-as-search-and-retrieval-plane
    - adr-001-workflow-centric-ia-and-handoff-packet-model
    - adr-002-pm-mode-authority-split-and-bounded-leantime-write-scope
---

# ADR Index

| Filename | Title | Status | One-line purpose | Related ADRs |
|---|---|---|---|---|
| [adr-pm-plane-authority-boundaries.md](adr-pm-plane-authority-boundaries.md) | ADR: PM Plane Authority Boundaries | Proposed | Freeze canonical PM-plane authority boundaries across PM, workflow, context, memory, retrieval, and adapter systems. | dopecon-bridge, Leantime, ConPort, dope-memory, Task Orchestrator, Memory Trinity, Serena, dope-context |
| [adr-dopecon-bridge-narrowing-to-adapter-only-role.md](adr-dopecon-bridge-narrowing-to-adapter-only-role.md) | ADR: dopecon-bridge narrowing to adapter-only role | Proposed | Narrow dopecon-bridge to adapter, router, and translator duties over canonical PM-plane backends. | PM Plane Authority Boundaries, Leantime, ConPort, Task Orchestrator |
| [adr-leantime-json-rpc-plus-plugin-integration-strategy.md](adr-leantime-json-rpc-plus-plugin-integration-strategy.md) | ADR: Leantime JSON-RPC plus plugin integration strategy | Proposed | Standardize Leantime JSON-RPC as the primary operational seam, with plugins reserved for bounded augmentation. | PM Plane Authority Boundaries, Task Orchestrator, ConPort, dope-memory, dopecon-bridge |
| [adr-conport-as-decision-progress-and-context-authority.md](adr-conport-as-decision-progress-and-context-authority.md) | ADR: ConPort as decision, progress, and context authority | Proposed | Make ConPort the sole canonical source for decisions, progress, and durable structured project context. | PM Plane Authority Boundaries, dopecon-bridge, dope-memory, Memory Trinity, Serena, dope-context |
| [adr-dope-memory-as-chronicle-memory-authority.md](adr-dope-memory-as-chronicle-memory-authority.md) | ADR: dope-memory as chronicle memory authority | Proposed | Establish dope-memory as the canonical chronicle memory layer while excluding PM, workflow, and decision authority. | PM Plane Authority Boundaries, ConPort, Task Orchestrator, Memory Trinity, Serena, dope-context |
| [adr-task-orchestrator-as-workflow-authority.md](adr-task-orchestrator-as-workflow-authority.md) | ADR: Task Orchestrator as workflow authority | Proposed | Delegate workflow legality, blockers, next-action, and progression semantics to Task Orchestrator. | PM Plane Authority Boundaries, dopecon-bridge, Leantime, ConPort |
| [adr-memory-trinity-authority-and-interaction-model.md](adr-memory-trinity-authority-and-interaction-model.md) | ADR: Memory Trinity authority and interaction model | Proposed | Define ConPort, dope-memory, and dope-context as distinct canonical planes with no silent authority escalation. | PM Plane Authority Boundaries, ConPort, dope-memory, dope-context, Serena |
| [adr-serena-as-technical-context-plane.md](adr-serena-as-technical-context-plane.md) | ADR: Serena as technical context plane | Proposed | Bound Serena to technical/code context authority without promoting it into PM, workflow, decision, or chronicle truth. | PM Plane Authority Boundaries, ConPort, dope-memory, dope-context, Memory Trinity |
| [adr-dope-context-as-search-and-retrieval-plane.md](adr-dope-context-as-search-and-retrieval-plane.md) | ADR: dope-context as search and retrieval plane | Proposed | Bound dope-context to retrieval and provenance-aware search rather than canonical PM, workflow, context, or chronicle truth. | PM Plane Authority Boundaries, ConPort, dope-memory, Serena, Memory Trinity |
| [adr-001-workflow-centric-ia-and-handoff-packet-model.md](adr-001-workflow-centric-ia-and-handoff-packet-model.md) | ADR-001: Workflow-Centric IA and Handoff Packet Authority Model | Proposed | Replace v1.0 service-centric 7-tab IA with dual-mode PM/Implementer operator shell and establish PKT/PKB envelopes as authored provenance, not new authority. | PM Plane Authority Boundaries, ConPort, dope-memory, Task Orchestrator, Leantime |
| [adr-002-pm-mode-authority-split-and-bounded-leantime-write-scope.md](adr-002-pm-mode-authority-split-and-bounded-leantime-write-scope.md) | ADR-002: PM-Mode Authority Split and Bounded Leantime Write Scope | Proposed | Split PM-mode write dispatch by canonical authority (not by pane) and bound Leantime writes to passive metadata, forbidding workflow mutations. | ADR-001, PM Plane Authority Boundaries, Leantime, Task Orchestrator, ConPort, dope-memory, dopecon-bridge |

## Notes

- These ADRs are intended to be read together as the PM-plane authority spine.
- Surface normalization, write adjudication, and runtime hardening work should resolve back to these ADRs rather than inventing parallel authority models.
