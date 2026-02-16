---
title: "System Architecture"
plane: "pm"
component: "dopemux"
status: "skeleton"
---

# System Architecture

## Purpose

One page that explains the whole system at 10,000 ft without lying.

TODO: 5-10 lines “why this exists” and “what is in scope”.

## Scope

TODO: Define the boundaries and responsibilities of the system architecture.

## Non-negotiable invariants

TODO: List the architectural invariants that must never be violated.

## FACT ANCHORS (Repo-derived)

- **OBSERVED: Two-Plane Coordinator**: `services/task-orchestrator/app/core/coordinator.py` implements the `PlaneCoordinator` linking PM and Cognitive planes.
- **OBSERVED: Plane Types**: `PlaneType` enum defines `PROJECT_MANAGEMENT` (pm) and `COGNITIVE` (cognitive) planes.
- **OBSERVED: Core Services**: codebase confirms `task-orchestrator`, `adhd-engine`, and `conport` as primary components.
- **OBSERVED: Event Bus**: `redis` is used for real-time coordination and sync operations.
- **OBSERVED: Service Registry**: `services/task-orchestrator/app/main.py` defines registry and discovery endpoints.

## Open questions
- **Global Rollups**: How do we aggregate multi-repo stats without breaking isolation?
- *Resolution*: Define a separate "Observer" plane that reads-only from multiple approved roots.

## Components (contract status)

**Supervisor Plane (OBSERVED)**:
- `task-orchestrator`: Real service, handles dispatch and tool execution.
- `adhd-engine`: Real service, manages focus windows.
- `dopecon-bridge`: Real service, event bus.

**Execution Plane (OBSERVED)**:
- `TaskX`: Integration via `task-orchestrator` (see `services/task-orchestrator/tests/week2_integration.py`).
- Runners: Configured via `config/models.yaml` (FUTURE/INFERRED).

**MCP Fabric (OBSERVED)**:
- `conport` (3004): Knowledge Graph.
- `pal` (3003): Reasoning.
- `serena` (3006): ADHD Interface.
- `dope-context` (3010): Semantic Search.
- `gptr-mcp` (3009): Deep Research.

State stores:
- workspace state store
- project state store
- global rollups (optional)

TODO: Confirm which of these exist today vs planned. Label as OBSERVED / PLANNED.

## Data flows (high-level)
1. request -> supervisor intake
1. context -> retrieval and shaping
1. routing -> choose runner/model
1. execution -> TaskX runs packet
1. artifacts -> deterministic outputs
1. memory -> ConPort and state stores

TODO: Add a diagram of the actual current flow once verified.

## Trust boundaries
- workspace isolation
- runner isolation
- MCP tool trust model
- artifact determinism boundary

TODO: Define what is allowed to cross boundaries and what is forbidden.

## Diagram (ASCII)

```text
Supervisor
|- Policy Engine (limits/cost/quality)
|- Packet Generator (chunked)
|- Dispatch (runner adapter)
|
v
TaskX (deterministic orchestration)
|
v
Runners (claude-code | codex | copilot)
|
v
MCP Fabric (Serena/ConPort/Dope-Context/Zen/Context7)
|
v
State Stores (graph/sqlite/rollups)
```

## Failure modes at architecture level

TODO: List top failure modes and what layer owns mitigation.

## Acceptance criteria

TODO: Define what “works” means for the overall system in 5 bullets.
