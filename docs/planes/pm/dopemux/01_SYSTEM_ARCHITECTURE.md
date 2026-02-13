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

TODO: Link to actual code artifacts that define the system structure.

## Open questions

TODO: List architectural unknowns and how to resolve them.

## Components (names as contracts)

Supervisor runtime:
- Policy Engine (limits/cost/quality)
- Packet Generator (chunked)
- Dispatch (runner adapter)
- ADHD engine (focus windows, output caps)
- MCPServerManager (lifecycle and health)

Execution runtime:
- TaskX (deterministic orchestration)
- Runners (claude-code | codex | copilot)

MCP fabric:
- Serena
- ConPort
- Dope-Context
- Context7
- Zen
- TODO: Others

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
