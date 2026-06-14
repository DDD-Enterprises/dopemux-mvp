# dopeCode Phase 9 Contract

## 1. Scope
Phase 9 adds deterministic multi-step mutation orchestration and explicit resumable execution for bounded dopeCode mutation plans without widening dopeCode into PM, memory, retrieval, or control-plane authority.

## 2. Authoritative Surfaces
- `services/serena/dopecode/transform/orchestration.py` is the canonical plan/state model for supported multi-step mutation orchestration.
- `services/serena/dopecode/transform/write_layer.py` remains the bounded file mutation authority and now uses explicit orchestration state for supported batch patch execution.
- `services/serena/dopecode/transform/refactor_layer.py` remains the bounded refactor authority and now executes symbol rename through explicit ordered steps.
- `services/serena/mcp_server.py` remains the operator-facing tool surface and now exposes explicit `resume` flags for supported bounded plan resumes.
- `src/dopemux/execution/dopecode_receipts.py` remains a reader/presenter only and now derives current plan state from durable receipt payloads.

## 3. Plan Model
- Supported orchestration plans use schema version `dopecode.orchestration_state.v1`.
- Each plan has deterministic `plan_id`, `mutation_id`, `operation`, `operation_class`, ordered `steps`, `status_counts`, `current_step_id`, `blocked_reason`, and `next_action`.
- Each step has deterministic `step_id`, `sequence`, `step_type`, `title`, `file`, `depends_on`, `status`, and bounded `operation` metadata.
- Supported step types are limited to:
  - `apply_patch`
  - `verify_file_sha`
- Unsupported step types fail closed.

## 4. Execution and Resume Rules
- Step statuses are explicit: `pending`, `ready`, `blocked`, `running`, `applied`, `failed`, `skipped`, and `verified`.
- Successful steps are not re-executed on resume. Prior successful steps remain authoritative for the current plan snapshot.
- Resume is explicit. If a prior plan is blocked or partially failed, rerunning the same mutation without `resume=true` must not continue execution.
- `apply_patch` steps fail closed if current file content no longer matches the planned `before_sha256`.
- Verification steps fail closed if the expected content hash is not present.
- Plans only resume from durable receipt history already stored inside the active workspace.

## 5. Receipt and Reader Rules
- Plan snapshots are stored inside the existing dopeCode execution receipt payload; Phase 9 does not create a second mutation authority store.
- Receipts expose plan-level and step-level state in a replay-safe form through the existing receipt ledger.
- `src/dopemux/execution/dopecode_receipts.py` derives active plan summaries, including current step title, blocked reason, and next action, from those stored snapshots.

## 6. Boundary Rules
- dopeCode remains workspace-scoped for all mutation.
- No mutation may escape `DOPEMUX_WORKSPACE_ROOT`.
- No shell-based editing or arbitrary subprocess mutation is introduced.
- dopemux remains a control-plane reader/presenter, not a dopeCode execution writer.

## 7. Known Limits
- Phase 9 orchestration support is bounded to supported patch and rename flows. Unsupported plan shapes remain blocked or fall back to existing fail-closed bounded behavior.
- `running` is an explicit execution state in the in-memory state machine, but durable replay reconstructs stable checkpoints after each bounded call rather than a live streaming step trace.
- Branch creation for the requested Phase 9 branch was not verifiable in this environment because `.git` ref writes were blocked by the sandbox.
