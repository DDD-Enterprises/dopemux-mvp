---
id: ADR-207-architecture-3.0-three-layer-integration
title: Adr 207 Architecture 3.0 Three Layer Integration
type: adr
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-21'
last_review: '2026-02-21'
next_review: '2026-05-22'
prelude: Adr 207 Architecture 3.0 Three Layer Integration (adr) for dopemux documentation
  and developer workflows.
status: proposed
graph_metadata:
  node_type: ADR
  impact: medium
  relates_to: []
---
# Context

The runtime evolved into a distributed stack with overlapping responsibilities
across infrastructure, MCP services, and coordination services. Historical docs
and implementation drift created ambiguity about ownership, integration
contracts, and the correct source of truth for state transitions.

Current code-truth requires:

1. Persistent state and event primitives to be separated from business workflows.
1. A stable memory and retrieval plane that can be consumed by multiple services.
1. A coordination plane that can orchestrate UX/workflow behavior without owning
   foundational data stores.
1. Compatibility-safe evolution across service naming and environment-variable
   aliases while preserving existing contracts.

# Decision

Adopt and enforce a three-layer integration architecture:

1. Infrastructure Layer:
- Foundational data/runtime services (Postgres/AGE, Redis, Qdrant, MySQL for
     Leantime) provide persistence, indexing, and event transport.
1. MCP Layer:
- Model-context and knowledge services (for example ConPort, PAL/Zen,
     dope-context, LiteLLM) provide retrieval, knowledge graph, and tool-facing
     memory/query interfaces.
1. Coordination/Cognitive Layer:
- Workflow and orchestration services (for example dopecon-bridge,
     task-orchestrator, adhd-engine, genetic-agent) implement user-facing
     coordination, ADHD-aware logic, and cross-plane orchestration.

Authority boundaries:

1. ConPort remains the memory/knowledge authority for persisted context and
   decision traces.
1. Dopecon-bridge is the primary cross-plane integration boundary for routed
   events and proxied workflow queries.
1. Task-orchestrator and adhd-engine consume infrastructure and MCP surfaces but
   do not become persistence authorities for shared cross-service context.
1. `services/registry.yaml` and active compose definitions are the operational
   source of truth for service naming/ports; compatibility aliases are permitted
   but must be explicit and documented.

Operational constraints:

1. No-breaking-change policy for public API/CLI/config contracts.
1. Degraded-mode behavior is required when upstream MCP or infrastructure
   dependencies are unavailable.
1. Active docs must be maintained as code-truth for architecture ownership and
   integration paths.

# Consequences

Positive:

1. Clearer ownership boundaries reduce architectural ambiguity and duplicated
   integration logic.
1. Cross-plane workflows become easier to test with explicit contract seams.
1. Runtime hardening can be prioritized per layer (infrastructure reliability,
   MCP correctness, coordination UX/workflow quality).

Tradeoffs:

1. Migration and naming cleanup work is required where legacy aliases remain.
1. Some services still need incremental refactors to fully honor boundary
   ownership (tracked in active audit reports).
1. Documentation and registry/compose parity must be continuously enforced to
   prevent drift regression.

Follow-on enforcement expectations:

1. New service introductions must declare layer and authority ownership.
1. Integration changes must include contract tests for layer boundaries.
1. Architecture docs and audit artifacts must be refreshed when authority or
   routing behavior changes.
