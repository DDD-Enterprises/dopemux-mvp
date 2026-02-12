---
id: PM_PHASE0_CLAIMS_LEDGER
title: Pm Phase0 Claims Ledger
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-12'
last_review: '2026-02-12'
next_review: '2026-05-13'
prelude: Pm Phase0 Claims Ledger (explanation) for dopemux documentation and developer
  workflows.
---
# PM Phase 0 Claims Ledger

Rules:
- Verified claims must end with a citation (line range).
- If not provable from PM-INV-00.outputs, mark UNKNOWN and list required evidence.

## Verified (Phase 0)

1) Task-orchestrator has an explicit ConPort MCP client module (`ConPortMCPClient`). Evidence: `PM-INV-00.outputs/12_services_task-orchestrator_conport_mcp_client.py.nl.txt:L1-L12`, `PM-INV-00.outputs/12_services_task-orchestrator_conport_mcp_client.py.nl.txt:L27-L37`

2) Dopemux includes an event bus implementation in `src/dopemux/event_bus.py` with a core interface and adapters. Evidence: `PM-INV-00.outputs/31_src_dopemux_event_bus.py.nl.txt:L1-L5`, `PM-INV-00.outputs/31_src_dopemux_event_bus.py.nl.txt:L68-L82`, `PM-INV-00.outputs/31_src_dopemux_event_bus.py.nl.txt:L127-L167`

3) Task-orchestrator includes root-level `test_*.py` files (non-standard relative to `services/*/tests/`). Evidence: `PM-INV-00.outputs/11_task_orchestrator_files.txt.nl.txt:L129-L134`, `PM-INV-00.outputs/12_services_task-orchestrator_test_conport_sync.py.nl.txt:L1-L10`

4) Taskmaster service includes a `server.py` module and a `bridge_adapter.py` module. Evidence: `PM-INV-00.outputs/21_taskmaster_files.txt.nl.txt:L3-L4`, `PM-INV-00.outputs/22_services_taskmaster_server.py.nl.txt:L1-L11`, `PM-INV-00.outputs/22_services_taskmaster_bridge_adapter.py.nl.txt:L1-L8`

## Unknown (Phase 0)

1) ConPort is the canonical PM state source (global).
Reason: Presence of ConPort clients/calls in scoped files does not prove canonical enforcement across all PM writers.
Evidence needed: Enforcement points where all PM task writers must persist to ConPort, or runtime guardrails that reject non-ConPort state writes.

2) CLI-created tasks are synced to ConPort.
Reason: Not proven by scoped Phase 0 evidence alone.
Evidence needed: CLI task creation/update execution path plus corresponding ConPort write call sites and tests.

3) ConPort resilience strategy exists (fallback/circuit breaker/degraded mode).
Reason: Not proven by scoped Phase 0 evidence alone.
Evidence needed: Explicit degraded-mode logic paths and failure-mode tests in PM surfaces.
