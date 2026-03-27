# Implementation Plan - TP-DSER-004: Sequential Multi-Packet Execution Bridge

## Objective
Implement a sequential multi-packet execution bridge ("sequencer") that runs a planned set of task packets one after another under a strict dependency order. This provides a minimum viable orchestration path until native series support is fully integrated.

## Key Files & Context
- **Launcher**: `src/dopemux_pr_merge_specialist/dopetask_packet_launcher.py` (Already has tracing)
- **Runner**: `src/dopemux_pr_merge_specialist/dopetask_sequential_plan_runner.py` (New)
- **Result Artifact**: `SEQUENTIAL_PLAN_RESULT.json`
- **Deliverables**:
    - `DopetaskSequentialPlanRunner` module.
    - `docs/integrations/dopetask/SEQUENTIAL_MULTI_PACKET_EXECUTION.md`
    - Fixture-backed sequencer tests.

## Implementation Steps

### Phase 1: Discovery & Trace Extension - [COMPLETED]
- [x] Analyze `DopetaskPacketLauncher` interface.
- [x] Confirm `PacketLaunchTrace` already contains `tp_id`, `success`, `bundle_path`, `error`, and `computed_at`.

### Phase 2: Sequential Runner Implementation
1.  **Define Plan & Result Models**:
    - `SequentialPlan`: `plan_id`, `base_branch`, `packets` (list of `tp_id` and `depends_on`).
    - `SequentialPlanResult`: `plan_id`, `status` (SUCCESS/FAILED/ABORTED), `traces` (list of `PacketLaunchTrace`), `failure_point` (tp_id or None).
2.  **Implement `DopetaskSequentialPlanRunner`**:
    - **Validation**:
        - Ensure all `depends_on` references exist within the plan.
        - Basic cycle detection (though plans are expected to be strictly sequential).
    - **Execution Loop**:
        - Iterate through the ordered `packets` list.
        - For each packet, verify all `depends_on` packets completed successfully in prior steps.
        - Call `launcher.launch(tp_id, context)`.
        - Capture the `PacketLaunchTrace`.
        - **Fail-Stop**: If `success` is `False`, record the failure and stop the sequence.
    - **Artifact Emission**:
        - Write `SEQUENTIAL_PLAN_RESULT.json` to the configured `bundle_root`.

### Phase 3: Validation & Documentation
1.  **Unit Testing**:
    - `tests/unit/test_dopetask_sequential_plan_runner.py`:
        - Test a 4-packet successful chain.
        - Test fail-stop behavior (packet 2 fails, 3 and 4 never run).
        - Test validation failure for missing dependencies.
        - Test result artifact content and existence.
2.  **Documentation**:
    - Create `docs/integrations/dopetask/SEQUENTIAL_MULTI_PACKET_EXECUTION.md` explicitly stating the sequential-only limitation and "stairs before elevator" design principle.

## Verification & Testing
- **Test Command**: `pytest tests/unit/test_dopetask_sequential_plan_runner.py`
- **Manual Verification**: Run a mock plan and inspect the generated `SEQUENTIAL_PLAN_RESULT.json`.

## Alternatives Considered
- **Native Series Integration**: Rejected. This TP is a bridge; native integration requires more extensive adapter/orchestrator changes.
- **Parallel Execution**: Rejected by scope. This is a sequencer, not a generic DAG orchestrator.
