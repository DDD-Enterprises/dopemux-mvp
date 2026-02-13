---
title: "TaskX Integration"
plane: "pm"
component: "dopemux"
status: "proposed"
---

# TaskX Integration Contract

## Purpose
The seam between deterministic engine and stateful runtime. This defines the API between Supervisor (Brain) and TaskX (Muscle).

## Scope
- The command-line interface to TaskX.
- The artifact directory structure and schema.
- The separation of concerns (Policy vs Execution).

## Non-negotiable invariants
1. **One-Way Street**: Supervisor calls TaskX. TaskX NEVER calls Supervisor API.
2. **Stateless Muscle**: TaskX execution result depends ONLY on the input packet and the file system state. It has no internal persistent memory across runs.
3. **Artifact Only**: TaskX communicates back ONLY via Files (JSON artifacts). No stdout parsing for logic.

## FACT ANCHORS (Repo-derived)
- **OBSERVED: Task-Orchestrator Source**: `services/task-orchestrator/` (Entrypoint: `app/main.py`, Core: `enhanced_orchestrator.py`).
- **OBSERVED: TaskX Wrapper**: `scripts/taskx` (Shell wrapper).
- **OBSERVED: Integration Tests**: `services/task-orchestrator/tests/week2_integration.py` (demonstrates wiring).
- **OBSERVED: Output Schema**: `src/taskx/schema/artifacts.py` (external repo concept, referenced in Orchestrator).
- **INFERRED: Environment**: `.taskx_venv/` (Virtualenv for TaskX).
- **INFERRED: Pin File**: `.taskx-pin` (Version pinning).

## Open questions
- **Live Output Streaming**: Can Supervisor stream TaskX stdout in real-time to UI?
  - *Resolution*: Yes, via subprocess pipe reading in `Dispatch`.
- **Live Output Streaming**: Can Supervisor stream TaskX stdout in real-time to UI?
  - *Resolution*: Yes, via subprocess pipe reading in `Dispatch`.

## TaskX responsibilities (Muscle)
- **Deterministic Orchestration**: Run steps 1, 2, 3 in order.
- **Runner Sandboxing**: Execute the specific runner (Claude, Codex) requested.
- **Artifact Generation**: Produce `RUN_REPORT.json` faithfully recording what happened.
- **Refusal**: If a step fails or violates a local guardrail, produce `REFUSAL_REPORT.json`.

## Dopemux responsibilities (Brain)
- **Packet Generation**: Create the `route_plan.json` (The "Packet").
- **Policy Enforcement**: Decide *which* runner to use.
- **Memory Persistence**: Read `RUN_REPORT.json` and save relevant bits to ConPort.
- **Cost Optimization**: Decide if we can afford to run the packet.

## Interface
**Command**:
```bash
taskx orchestrate \
  --packet ./packets/current/packet.json \
  --output ./packets/current/artifacts/ \
  --mode auto
```

**Artifacts**:
1. **ROUTE_PLAN.json** (Input): The instructions.
2. **RUN_REPORT.json** (Output):
   - `status`: "success" | "failure" | "refusal"
   - `steps`: List of executed steps with exit codes and stdout/stderr snippets.
   - `cost`: Token usage (if available from runner).
3. **ARTIFACT_INDEX.json** (Output): List of all files created/modified.

## Key rule: no editing history
- Dopemux NEVER edits a past packet.
- If a run fails, Dopemux creates a **NEW** packet (e.g., `packet_v2.json`) referenced as a child of the failed one.
- History is an append-only DAG (Directed Acyclic Graph) of packets.

## Failure modes
- **Non-Determinism**: TaskX uses `datetime.now()` in a file output without freezing it.
- **Scope Creep**: TaskX starts trying to "auto-fix" errors by querying an LLM itself. (STRICTLY FORBIDDEN).

## Acceptance criteria
1. **Determinism Test**: Run the same Packet twice on the same file state. Resulting artifacts MUST be byte-identical (ignoring timestamps in the artifact metadata itself).
2. **Refusal Test**: Give TaskX a packet with an invalid step. It MUST fail gracefully with a `REFUSAL_REPORT` and not crash.
