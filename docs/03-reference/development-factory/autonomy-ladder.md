---
id: autonomy-ladder
title: Autonomy Ladder
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-06'
last_review: '2026-06-06'
next_review: '2026-09-04'
prelude: Autonomy Ladder (reference) for dopemux documentation and developer workflows.
---
# Autonomy Ladder (L0–L6)

## Levels

| Level | Name | Description | Current Status |
|-------|------|-------------|----------------|
| L0 | Manual Planning | Human authors all packets, architecture, decisions | operational |
| L1 | Packet Factory | AI generates Execution Capsule packets from architecture | operational / READY_WITH_RISKS |
| L2 | Supervised Single Execution | AI executes one capsule under continuous operator supervision | cautious / supervised only |
| L3 | Supervised Batch | AI runs a queue of capsules with supervisor checkpoints | blocked |
| L4 | Auto Repair Loop | AI detects failures and self-patches within scope | blocked |
| L5 | Auto PR + Review + Readiness | AI opens PRs, runs AI review, checks readiness without intervention | partial advisory only |
| L6 | Live Write / Execution Orchestration | Fully autonomous execution including live merge writes | blocked |

## Blockers for L3+

The following conditions block L3 and all levels above it:

- **`LIVE_WRITE_READY` undefined.** No schema defines `LIVE_WRITE_READY` — verification (VG-006) confirmed it appears only as blocker statements, references, and test guards that *actively forbid* defining it as a schema property (`tests/dcp/test_dcp_0002_contract_derivation.py`). It is `UNDEFINED_AND_BLOCKING`. Unblocking requires defining the contract (`TP-DMX-LIVE-WRITE-READY-SCHEMA-001`) and an authorized operator declaring readiness with evidence.
- **`DCP-RED-MERGE-SEAM-0001` active.** The DCP Core (`schemas/dcp/`, `queue_drain.py`) carries an active red-line seam. `queue_drain.py` is HARD-BLOCKED. No batch execution may proceed while this seam is active. (Executable `RedLaneScanner` enforcement exists but is not yet wired into CI/steward — see red-lines doc.)
- **RTE S7 truth-split gate (verify-and-close).** The earlier `F1-CRIT-1` audit finding described S7 as an always-PASS stub. At HEAD `8042f9f9f` the implementation is present and wired (`collect_truth_split` emits blockers into `all_blockers`) — the stub claim is stale. The remaining blocker is *verification*: the gate must be run against injected drift and confirmed to FAIL before batch execution can rely on it (`TP-RTE-S7-DRIFT-FIX-001`, re-scoped). Until that verification runs, batch execution still cannot trust S7.
- **Agent authority unresolved.** The `agents` component (`services/agents/`, `src/dopemux/agent_orchestrator.py`) has no declared operator-facing authority. Three competing agent families exist with no declared boundaries. Running a batch that might invoke agents creates unpredictable authority scope.

## Blockers for L6 Specifically

L6 requires all L3+ blockers to be resolved, plus:

- **`DCP-RED-MERGE-SEAM-0001` must be explicitly lifted by an authorized operator.** This is not a normal gate — it requires a deliberate operator action documented in the obligation ledger. The seam cannot be lifted by the factory itself or by AI review outcome.
- **Live merge authority must be formally delegated.** No component currently holds live merge authority. Delegation requires operator sign-off and must be recorded in the obligation ledger before any live write proceeds.

## Cross-References

- Full red-line register: [red-lines-and-stop-conditions.md](red-lines-and-stop-conditions.md)
- Evidence requirements for unblocking: [evidence-and-proof-flow.md](evidence-and-proof-flow.md)
- Component authority declarations: [architecture.md](architecture.md)
