# TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-003 — Research Trace

## Owner Primitive Gate

**Schema**: `docker/mcp-servers-source/conport/schema.sql`

```
CREATE TABLE custom_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workspace_id, category, key)
);
```

- **Unique identity**: `(workspace_id, category, key)` with a UNIQUE constraint (line 117)
- **DB driver**: asyncpg via `self.db_pool.acquire()` in `enhanced_server.py`
- **Transaction support**: asyncpg supports `conn.transaction()` — transactional operations are feasible without schema change

**Current upsert** (`enhanced_server.py:1576-1582`):
```python
async with self.db_pool.acquire() as conn:
    await conn.execute("""
        INSERT INTO custom_data (workspace_id, category, key, value, updated_at)
        VALUES ($1, $2, $3, $4, NOW())
        ON CONFLICT (workspace_id, category, key)
        DO UPDATE SET value = $4, updated_at = NOW()
    """, workspace_id, category, key, json.dumps(value))
```

This is a last-write-wins upsert — always overwrites on conflict. This is the correct behavior for generic key-value storage but insufficient for atomic idempotency claims.

**Serializability verdict**: Can serialize without schema change. Use `INSERT ... ON CONFLICT DO NOTHING RETURNING value` inside a transaction.

## Current Epic Create Flow (sequential, race-prone)

1. **Task Orchestrator** `workflow_service.create_epic()`:
   - Computes deterministic `epic_id` from `idempotency_key`
   - Calls `self.store.get_epic(epic_id)` — pre-read
   - If found and matches → return existing (idempotent replay)
   - If found and doesn't match → raise 409
   - If not found → build epic, call `self.store.save_epic(epic)` → upsert

2. **WorkflowStore** `save_epic()`:
   - Calls `upsert_custom_data(Epics_CATEGORY, epic_id, epic_dict)`

3. **WorkflowStore** `upsert_custom_data()`:
   - Calls `AsyncDopeconBridgeClient.save_custom_data()`

4. **DopeconBridge Client** `save_custom_data()`:
   - `POST /kg/custom_data` via HTTP

5. **DopeconBridge routes** `save_custom_data()`:
   - Proxies to `conport_client.save_custom_data()`

6. **DopeconBridge clients** `conport_client.save_custom_data()`:
   - `POST {conport_url}/api/custom_data`

7. **ConPort** `save_custom_data()`:
   - Last-write-wins upsert

**Race window**: Between step 1 (pre-read) and step 2 (upsert), concurrent callers both see absence and both attempt to persist. PostgreSQL UNIQUE constraint ensures only one row BUT the upsert overwrites — a conflicting second caller's payload wins (last-write-wins), silently replacing the first caller's value.

## Design Decision

Use `INSERT ... ON CONFLICT DO NOTHING` with PostgreSQL transaction isolation as the atomic claim. The first inserter wins; the second gets a no-op. Read-back determines MATCHED/CONFLICT/LEGACY_UNFINGERPRINTED.

## Fingerprint v1

Preimage: `workflow_epic_create:v1` + `\x00` + `canonical_json(normalized_request)`

Normalized fields (included):
- title, description, business_value, acceptance_criteria, priority, status, created_from_idea_id, tags, adhd_metadata

Excluded:
- idempotency_key, generated epic ID, timestamps, version, Leantime identifiers, transport/response metadata

Encoding: UTF-8 JSON, sorted keys, compact separators → SHA-256 hex digest.

Fingerprint stored in `value._fingerprint_v1` inside the JSONB blob.

## Files traced

- `docker/mcp-servers-source/conport/schema.sql` — custom_data table, UNIQUE constraint
- `docker/mcp-servers-source/conport/enhanced_server.py` — save/get/delete custom_data implementations, DB pool
- `services/shared/dopecon_bridge_client/client.py` — Sync + Async bridge clients, `save_custom_data`/`get_custom_data`
- `services/dopecon-bridge/dopecon_bridge/routes.py` — `/kg/custom_data` route + auth
- `services/task-orchestrator/app/models/workflow.py` — CreateEpicRequest, WorkflowEpic, ADHDMetadata
- `services/task-orchestrator/app/services/workflow_store.py` — WorkflowStore, upsert/get/save operations
- `services/task-orchestrator/app/services/workflow_service.py` — create_epic with pre-read/upsert race

## Owner

ConPort PostgreSQL `custom_data` table, accessed through ConPort's `enhanced_server.py` REST API. The linearization point must be inside ConPort's PostgreSQL connection.
