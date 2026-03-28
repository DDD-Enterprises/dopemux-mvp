---
id: sequential-multi-packet-execution
title: Sequential Multi Packet Execution
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-27'
last_review: '2026-03-27'
next_review: '2026-06-25'
prelude: Sequential Multi Packet Execution (explanation) for dopemux documentation
  and developer workflows.
---
# Sequential Multi-Packet Execution Bridge (TP-DSER-004)

## Status
- **Type**: Sequencer (Not full Orchestrator)
- **Design Principle**: "Stairs before Elevator" 🫠
- **Date**: 2026-03-27

## Objective
Provide a controlled, sequential execution path for multiple Task Packets with strict dependency ordering. This bridge allows the Gemini CLI to execute complex multi-packet chains safely while preserving proof and traceability.

## Input Contract
The sequencer accepts an internal `SequentialPlan`:
```json
{
  "plan_id": "PLAN-ID",
  "base_branch": "main",
  "packets": [
    {"tp_id": "TP-001", "depends_on": []},
    {"tp_id": "TP-002", "depends_on": ["TP-001"]}
  ]
}
```

## Execution Semantics
1. **Validation**: The plan is validated for missing dependencies and correct ordering (dependency N must be defined before N+1).
2. **Sequential Launch**: Packets are launched one at a time via `DopetaskPacketLauncher`.
3. **Prerequisite Check**: Packet N can only run if all its `depends_on` entries successfully completed in prior steps of the same run.
4. **Fail-Stop**: Execution stops immediately on the first packet failure. Subsequent packets are aborted.

## Aggregate Result
The sequencer emits a `SEQUENTIAL_PLAN_RESULT.json` artifact containing:
- Full launch traces for attempted packets.
- Success/Failure/Aborted status.
- Exact failure point (TP ID).
- Timing metadata.

## Limitations
- **Sequential Only**: No parallel execution of independent roots.
- **Single-PR Boundary**: This bridge does not yet integrate with native series finalization (PR merge).
- **Execution Only**: This does not replace the read-only Series Contract (TP-DSER-003).
