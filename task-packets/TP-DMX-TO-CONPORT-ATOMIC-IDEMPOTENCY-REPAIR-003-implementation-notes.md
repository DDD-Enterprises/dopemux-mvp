---
id: TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-003-implementation-notes
title: Tp Dmx To Conport Atomic Idempotency Repair 003 Implementation Notes
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-30'
last_review: '2026-07-30'
next_review: '2026-10-28'
prelude: Tp Dmx To Conport Atomic Idempotency Repair 003 Implementation Notes (explanation)
  for dopemux documentation and developer workflows.
---
# TP-DMX-TO-CONPORT-ATOMIC-IDEMPOTENCY-REPAIR-003 — Implementation Notes

## Claim endpoint design

```python
POST /api/custom_data/claim
{
  "workspace_id": "...",
  "category": "...",
  "key": "...",
  "value": {
    "_fingerprint_v1": "sha256-hex...",
    ...payload...
  }
}
```

Response:
```json
{"result": "CREATED"|"MATCHED"|"CONFLICT"|"LEGACY_UNFINGERPRINTED", "value": {...}}
```

## Implementation (asyncpg transaction)

```python
async with self.db_pool.acquire() as conn:
    async with conn.transaction():
        row = await conn.fetchrow("""
            INSERT INTO custom_data (workspace_id, category, key, value, updated_at)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (workspace_id, category, key) DO NOTHING
            RETURNING value
        """, workspace_id, category, key, json.dumps(value))

        if row is not None:
            return {"result": "CREATED", "value": json.loads(row["value"])}

        # Row already exists — read back
        row = await conn.fetchrow("""
            SELECT value FROM custom_data
            WHERE workspace_id = $1 AND category = $2 AND key = $3
        """, workspace_id, category, key)

        existing = json.loads(row["value"])
        existing_fp = existing.get("_fingerprint_v1")
        if existing_fp is None:
            return {"result": "LEGACY_UNFINGERPRINTED", "value": existing}
        if existing_fp == fingerprint:
            return {"result": "MATCHED", "value": existing}
        return {"result": "CONFLICT", "value": existing}
```

## Fingerprint computation

```python
import hashlib, json

FINGERPRINT_PREFIX = b"workflow_epic_create:v1"

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

def normalize_request(request: CreateEpicRequest) -> dict:
    return {
        "title": request.title,
        "description": request.description,
        "business_value": request.business_value,
        "acceptance_criteria": sorted(request.acceptance_criteria),
        "priority": request.priority,
        "status": request.status,
        "created_from_idea_id": request.created_from_idea_id,
        "tags": sorted(request.tags) if request.tags else [],
        "adhd_metadata": request.adhd_metadata.dict() if hasattr(request.adhd_metadata, "dict") else dict(request.adhd_metadata),
    }

def compute_fingerprint(request: CreateEpicRequest) -> str:
    normalized = normalize_request(request)
    preimage = FINGERPRINT_PREFIX + b"\x00" + canonical_json(normalized).encode("utf-8")
    return hashlib.sha256(preimage).hexdigest()
```

This goes in `workflow_service.py` because it's the canonical fingerprint owner for workflow epics.

## Test design

### test_custom_data_atomic_claim.py (ConPort)
- `test_first_claim_returns_created` — INSERT succeeds, returns CREATED
- `test_identical_second_claim_returns_matched` — same fingerprint → MATCHED
- `test_different_second_claim_returns_conflict` — different fingerprint → CONFLICT
- `test_legacy_row_returns_legacy_unfingerprinted` — existing row without `_fingerprint_v1`
- `test_20_concurrent_identical_claims` — all 20 observe either CREATED or MATCHED
- `test_20_concurrent_conflicting_claims` — one CREATED, rest CONFLICT
- `test_generic_upsert_still_works` — original endpoint unchanged
