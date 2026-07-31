# TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-003 — Plan

## Approach

Replace the pre-read/upsert race with an atomic claim at ConPort PostgreSQL.

**Insert claim**: ConPort exposes new `POST /api/custom_data/claim` that atomically inserts with `ON CONFLICT DO NOTHING RETURNING (value)` and returns the claim result.

**Fingerprint**: Embedded in `value._fingerprint_v1` inside the JSONB column. No schema migration needed.

## Changes per slice

### Slice A: Packet and design records (this file + research + packet JSON)

### Slice B: ConPort atomic owner operation
- Add `POST /api/custom_data/claim` to `enhanced_server.py`
- Logic:
  1. Validate request has `workspace_id`, `category`, `key`, `value` (with `_fingerprint_v1`)
  2. In transaction: `INSERT ... ON CONFLICT DO NOTHING RETURNING value, created_at`
  3. If inserted → return `CREATED` with persisted value
  4. If not inserted → SELECT existing row → compare `_fingerprint_v1`
     - Same fingerprint → `MATCHED`
     - Different fingerprint → `CONFLICT`
     - Missing fingerprint → `LEGACY_UNFINGERPRINTED`
  5. Generic upsert remains unchanged
- Tests: `test_custom_data_atomic_claim.py`

### Slice C: Bridge propagation
- Add `POST /kg/custom_data/claim` route to dopecon-bridge `routes.py`
- Add `claim_custom_data()` method to dopecon-bridge `clients.py` (ConPort client)
- Add `claim_custom_data()` to shared `AsyncDopeconBridgeClient` and sync `DopeconBridgeClient`
- Bridge never becomes lock owner — purely a proxy

### Slice D: Task Orchestrator replacement
- Remove pre-read from `create_epic()` in `workflow_service.py`
- Add fingerprint computation + atomic claim path
- Add `claim_epic()` to `workflow_store.py`
- Normalization helper for fingerprint v1
- Handle all 5 claim results (CREATED, MATCHED, CONFLICT, LEGACY_UNFINGERPRINTED, OWNER_ERROR)

### Slice E: Concurrency proof
- Isolated live proof with two TO processes sharing one ConPort owner
- 20 identical concurrent rounds + 20 conflicting concurrent rounds + restart replay
- Verify exactly one persisted value per identity, zero overwrites, zero token leaks

## Files touched

| File | Change |
|------|--------|
| `task-packets/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-003.json` | NEW — packet |
| `task-packets/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-003-research.md` | NEW |
| `task-packets/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-003-plan.md` | NEW |
| `task-packets/TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-003-implementation-notes.md` | NEW |
| `docker/mcp-servers-source/conport/enhanced_server.py` | MODIFY — add claim endpoint |
| `docker/mcp-servers-source/conport/tests/test_custom_data_atomic_claim.py` | NEW |
| `docker/mcp-servers-source/conport/tests/test_mcp_custom_data.py` | VERIFY compatibility |
| `services/dopecon-bridge/dopecon_bridge/routes.py` | MODIFY — add claim route |
| `services/dopecon-bridge/dopecon_bridge/clients.py` | MODIFY — add claim client |
| `services/shared/dopecon_bridge_client/client.py` | MODIFY — add sync+async methods |
| `services/task-orchestrator/app/models/workflow.py` | MODIFY — add fingerprint helper |
| `services/task-orchestrator/app/services/workflow_store.py` | MODIFY — add claim_epic |
| `services/task-orchestrator/app/services/workflow_service.py` | MODIFY — atomic create |
| `tests/arch/test_task_orchestrator_conport_persistence_contract.py` | MODIFY — update contract |
| `tests/unit/test_task_orchestrator_workflow_store.py` | MODIFY — claim tests |
| `tests/unit/test_task_orchestrator_workflow_route_certification.py` | MODIFY — atomic assert |
| `tests/unit/test_task_orchestrator_workflow_atomic_idempotency.py` | NEW |
| `tests/integration/test_task_orchestrator_concurrent_idempotency.py` | NEW |

## No changes
- `schema.sql` — no migration under this packet
- Redis, local stores, in-process mutexes — not used
- Canonical services — not mutated
