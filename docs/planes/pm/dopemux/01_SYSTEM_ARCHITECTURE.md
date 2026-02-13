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
- **OBSERVED: Service Root**: `services/` contains 20+ services including `task-orchestrator`, `adhd_engine`, `dopecon-bridge`, and `session-manager`.
- **OBSERVED: Infrastructure**: `compose.yml` defines the canonical stack (Postgres/AGE, Redis, Qdrant).
- **OBSERVED: Control Plane Services**:
- **OBSERVED: Control Plane Services**:
  - `task-orchestrator` (Port 8000): FastAPI service with `jpickly` integration (`services/task-orchestrator/app/main.py`). Un-deprecated via `ADR-203`.
  - `adhd-engine` (Port 8095): Real-time cognitive load management (`services/adhd_engine/`).
  - `dopecon-bridge` (Port 3016): Event bus and pattern detection (`services/dopecon-bridge/`).
- **OBSERVED: Intelligence Plane**:
  - `genetic-agent` (Port 8000): AI code repair (`services/genetic_agent/`).
  - `dope-memory` (Port 3020): Working memory assistant (`services/working-memory-assistant/`).
  - `ml-risk-assessment`: Predictive risk engine extracted from orchestrator (referenced in `ADR-203`).
- **OBSERVED: Leantime Integration**: `services/leantime-bridge` (Port 3015) and `docker/leantime` (Port 8080).

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
2. context -> retrieval and shaping
3. routing -> choose runner/model
4. execution -> TaskX runs packet
5. artifacts -> deterministic outputs
6. memory -> ConPort and state stores

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
