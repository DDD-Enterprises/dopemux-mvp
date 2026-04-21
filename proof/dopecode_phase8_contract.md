# dopeCode Phase 8 Contract

## 1. Scope
Phase 8 adds durable event-shaped execution receipts for the existing dopeCode mutation lifecycle so dopemux can consume, replay, and display operator history without moving PM, memory, retrieval, or control-plane authority into dopeCode.

## 2. Authoritative Surfaces
- `services/serena/dopecode/execution_receipts.py` is the canonical dopeCode event receipt writer and replay guard.
- `services/serena/dopecode/runtime.py` remains the runtime bundle and now wires the shared receipt store into mutation surfaces.
- `services/serena/dopecode/transform/write_layer.py` remains the bounded file mutation authority and now emits durable lifecycle receipts for supported mutation operations.
- `services/serena/dopecode/transform/refactor_layer.py` remains the bounded symbol refactor authority and now emits top-level lifecycle receipts for preview/apply outcomes.
- `src/dopemux/execution/dopecode_receipts.py` is the dopemux-side reader and presenter for the dopeCode receipt ledger. It is a consumer only, not a mutation authority.
- `services/serena/mcp_server.py` remains the operator-facing MCP surface and continues to pass through dopeCode payloads without becoming the receipt writer.

## 3. Event Receipt Model
- Durable receipts are stored at `.dopemux/dopecode/execution_receipts.jsonl` inside the active workspace root.
- Each stored line is a canonical JSON object with schema version `dopecode.execution_receipt.v1`.
- Each receipt includes deterministic `event_id`, `idempotency_key`, `mutation_id`, `event_type`, `lifecycle_stage`, `ts_utc`, `workspace_id`, `workspace_root`, `operation`, `operation_class`, `execution_mode`, `execution_status`, and bounded `payload`.
- `mutation_id` groups semantically identical preview/apply requests for the same bounded mutation intent.
- `event_id` is computed from the canonical event core, including `ts_utc`, so separate operator invocations remain distinct while duplicate persistence of the same event remains idempotent.
- `payload` is bounded to operator-relevant fields such as files, counts, summary, and deterministic mutation metadata. Full source contents and arbitrary process output are not persisted.

## 4. Replay and Fail-Closed Rules
- Appending the exact same event a second time must replay safely and return the existing stored event without appending a duplicate ledger line.
- Reusing an existing `idempotency_key` with different event content must raise a replay mismatch error.
- Corrupt JSONL, schema drift, workspace identity mismatch, or unsupported event types must fail closed during both write-side append and dopemux-side read/replay.
- dopemux replay is dedupe-only. It does not re-execute mutations or promote receipt history into PM or memory truth.

## 5. Control-Plane Boundary
- dopeCode remains workspace-scoped for all mutation.
- No write may escape `DOPEMUX_WORKSPACE_ROOT`.
- dopeCode writes its own bounded execution receipt ledger only; it does not become PM truth, memory truth, retrieval truth, or project authority.
- dopemux consumes the receipt ledger as operator history only. It does not become a code mutation engine through this reader.

## 6. Known Limits
- Phase 8 does not backfill prior dopeCode operations; history begins when this ledger exists.
- Receipt replay protects the durable ledger and dopemux history view, not repeated intentional mutation requests issued at different times.
- Failure events are limited to supported return paths and explicit replay/persistence failures; exceptions raised before receipt construction remain visible through existing tool errors rather than synthetic placeholder receipts.
- `proof/dopecode_phase7_*` artifacts named by the task packet were not present in this checkout; Phase 8 was anchored to current runtime truth and the existing Phase 6 proof artifacts instead.
