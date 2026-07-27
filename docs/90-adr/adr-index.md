---
id: adr-index
title: "ADR Index"
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-07-21'
next_review: '2026-08-21'
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
---

# ADR Index

| Filename | Title | Status | One-line purpose | Related ADRs |
|---|---|---|---|---|
| [adr-conport-canonical-record-service-v2.md](adr-conport-canonical-record-service-v2.md) | ADR: ConPort Canonical Record Service v2 | Accepted | Define one normalized ConPort canonical record service with registry-backed project/workspace/instance identity, bounded decision/context/evidence authority, durable outbox events, derived projections, and ADR-gated rollout. | ConPort authority, Memory Trinity, dope-memory, dope-context, Task Orchestrator, MCP integration |
| [adr-pm-plane-authority-boundaries.md](adr-pm-plane-authority-boundaries.md) | ADR: PM Plane Authority Boundaries | Proposed | Freeze canonical PM-plane authority boundaries across PM, workflow, context, memory, retrieval, and adapter systems. | dopecon-bridge, Leantime, ConPort, dope-memory, Task Orchestrator, Memory Trinity, Serena, dope-context |
| [adr-dopecon-bridge-narrowing-to-adapter-only-role.md](adr-dopecon-bridge-narrowing-to-adapter-only-role.md) | ADR: dopecon-bridge narrowing to adapter-only role | Proposed | Narrow dopecon-bridge to adapter, router, and translator duties over canonical PM-plane backends. | PM Plane Authority Boundaries, Leantime, ConPort, Task Orchestrator |
| [adr-leantime-json-rpc-plus-plugin-integration-strategy.md](adr-leantime-json-rpc-plus-plugin-integration-strategy.md) | ADR: Leantime JSON-RPC plus plugin integration strategy | Proposed | Standardize Leantime JSON-RPC as the primary operational seam, with plugins reserved for bounded augmentation. | PM Plane Authority Boundaries, Task Orchestrator, ConPort, dope-memory, dopecon-bridge |
| [adr-conport-as-decision-progress-and-context-authority.md](adr-conport-as-decision-progress-and-context-authority.md) | ADR: ConPort as decision, progress, and context authority | Superseded | Make ConPort the sole canonical source for decisions, progress, and durable structured project context. | PM Plane Authority Boundaries, dopecon-bridge, dope-memory, Memory Trinity, Serena, dope-context |
| [adr-dope-memory-as-chronicle-memory-authority.md](adr-dope-memory-as-chronicle-memory-authority.md) | ADR: dope-memory as chronicle memory authority | Accepted, amended | Establish dope-memory as the canonical chronicle memory layer while excluding PM, workflow, and decision authority. | PM Plane Authority Boundaries, ConPort, Task Orchestrator, Memory Trinity, Serena, dope-context |
| [adr-task-orchestrator-as-workflow-authority.md](adr-task-orchestrator-as-workflow-authority.md) | ADR: Task Orchestrator as workflow authority | Proposed | Delegate workflow legality, blockers, next-action, and progression semantics to Task Orchestrator. | PM Plane Authority Boundaries, dopecon-bridge, Leantime, ConPort |
| [adr-memory-trinity-authority-and-interaction-model.md](adr-memory-trinity-authority-and-interaction-model.md) | ADR: Memory Trinity authority and interaction model | Accepted, amended | Define ConPort, dope-memory, and dope-context as distinct canonical planes with no silent authority escalation. | PM Plane Authority Boundaries, ConPort, dope-memory, dope-context, Serena |
| [adr-serena-as-technical-context-plane.md](adr-serena-as-technical-context-plane.md) | ADR: Serena as technical context plane | Proposed | Bound Serena to technical/code context authority without promoting it into PM, workflow, decision, or chronicle truth. | PM Plane Authority Boundaries, ConPort, dope-memory, dope-context, Memory Trinity |
| [adr-dope-context-as-search-and-retrieval-plane.md](adr-dope-context-as-search-and-retrieval-plane.md) | ADR: dope-context as search and retrieval plane | Accepted, amended | Bound dope-context to retrieval and provenance-aware search rather than canonical PM, workflow, context, or chronicle truth. | PM Plane Authority Boundaries, ConPort, dope-memory, Serena, Memory Trinity |
| [adr-dcp-mcp-ro-0009-chatgpt-mcp-exposure-targets-runtime-resolution-ownership-evidence.md](adr-dcp-mcp-ro-0009-chatgpt-mcp-exposure-targets-runtime-resolution-ownership-evidence.md) | ADR-DCP-MCP-RO-0009: ChatGPT MCP Exposure Targets, Runtime Resolution, and Ownership Evidence | Accepted, amended | Require opaque ChatGPT target IDs, explicit exposure consent, live ownership evidence, and fail-closed runtime resolution before backend calls. | DCP read-only facade, Memory Trinity, Task Orchestrator |
| [adr-dmx-prsteward-soloowner-001.md](adr-dmx-prsteward-soloowner-001.md) | ADR-DMX-PRSTEWARD-SOLOOWNER-001: PR Steward Solo-Owner Security-Release Authorization | Accepted | Exact-head solo-owner security-release path when the trusted roster is a single owner-author; preserves multi-reviewer enforcement otherwise. | PR Steward, security-release gate |
| [adr-dmx-prsteward-org-app-001.md](adr-dmx-prsteward-org-app-001.md) | ADR-DMX-PRSTEWARD-ORG-APP-001: Org-Owned Release-Gate App Approval | Accepted | Allow a dedicated DDD-Enterprises GitHub App to satisfy security-release approval after exact-head audit and CI. | PR Steward, GitHub App, solo maintainer |

## Notes

- These ADRs are intended to be read together as the PM-plane authority spine.
- Surface normalization, write adjudication, and runtime hardening work should resolve back to these ADRs rather than inventing parallel authority models.

## ConPort CRS v2 Wave 1 effective status map

| Filename | Effective status |
|---|---|
| `adr-conport-canonical-record-service-v2.md` | Accepted |
| `adr-conport-as-decision-progress-and-context-authority.md` | Superseded |
| `adr-memory-trinity-authority-and-interaction-model.md` | Accepted, amended |
| `adr-dope-memory-as-chronicle-memory-authority.md` | Accepted, amended |
| `adr-dope-context-as-search-and-retrieval-plane.md` | Accepted, amended |
| `adr-pm-plane-authority-boundaries.md` | Proposed |
| `adr-dopecon-bridge-narrowing-to-adapter-only-role.md` | Proposed |
| `adr-serena-as-technical-context-plane.md` | Proposed |
| `adr-task-orchestrator-as-workflow-authority.md` | Proposed |
| `adr-dcp-mcp-ro-0009-chatgpt-mcp-exposure-targets-runtime-resolution-ownership-evidence.md` | Accepted, amended |
| `adr-conport-migration-foundation-gate.md` | Accepted, amended |
| `adr-208-mcp-config-drift-prevention.md` | Accepted, amended |
| `adr-mcpint-001-catalog-v2-single-source.md` | Accepted, amended |
| `adr-mcpint-002-agent-exposure-and-read-plane.md` | Accepted, amended |
| `adr-mcpint-004-event-ingress-contract.md` | Accepted, amended |
| `adr-213-dual-capture-canonical-ledger.md` | Accepted, amended |
| `adr-201-conport-kg-security-hardening.md` | Deprecated |
| `adr-213-capture-adapters-single-ledger.md` | Deprecated |
| `adr-180-automatic-instance-resume.md` | Deprecated |
| `adr-221-event-stream-rate-limits.md` | Accepted, amended |
| `adr-222-deterministic-vs-llm-boundary.md` | Accepted |
| `adr-001-workflow-centric-ia-and-handoff-packet-model.md` | Proposed |
| `adr-002-pm-mode-authority-split-and-bounded-leantime-write-scope.md` | Proposed |

Wave 1 status effectuation is bound to the [independent acceptance record](../../proof/conport-crs-v2/wave1/WAVE1-ACCEPTANCE.json). Acceptance does not authorize implementation, runtime mutation, merge, or Wave 2.
