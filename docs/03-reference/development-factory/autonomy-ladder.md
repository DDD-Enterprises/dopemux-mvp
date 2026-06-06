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

- **`LIVE_WRITE_READY` undefined.** No component has been declared `LIVE_WRITE_READY`. The schema exists in `schemas/dcp/` but no component has satisfied its preconditions. Unblocking requires an authorized operator to declare readiness with evidence.
- **`DCP-RED-MERGE-SEAM-0001` active.** The DCP Core (`schemas/dcp/`, `queue_drain.py`) carries an active red-line seam. `queue_drain.py` is HARD-BLOCKED. No batch execution may proceed while this seam is active.
- **RTE S7 gate stub (always-PASS).** The S7 classification gate in the RTE pipeline is a stub that always returns PASS. Any batch execution relying on S7 for routing decisions cannot be trusted. This finding is documented as `F1-CRIT-1` in the RTE audit record.
- **Agent authority unresolved.** The `agents` component (`services/agents/`, `src/dopemux/agent_orchestrator.py`) has no declared operator-facing authority. Three competing agent families exist with no declared boundaries. Running a batch that might invoke agents creates unpredictable authority scope.

## Blockers for L6 Specifically

L6 requires all L3+ blockers to be resolved, plus:

- **`DCP-RED-MERGE-SEAM-0001` must be explicitly lifted by an authorized operator.** This is not a normal gate — it requires a deliberate operator action documented in the obligation ledger. The seam cannot be lifted by the factory itself or by AI review outcome.
- **Live merge authority must be formally delegated.** No component currently holds live merge authority. Delegation requires operator sign-off and must be recorded in the obligation ledger before any live write proceeds.

## Cross-References

- Full red-line register: [red-lines-and-stop-conditions.md](red-lines-and-stop-conditions.md)
- Evidence requirements for unblocking: [evidence-and-proof-flow.md](evidence-and-proof-flow.md)
- Component authority declarations: [architecture.md](architecture.md)
