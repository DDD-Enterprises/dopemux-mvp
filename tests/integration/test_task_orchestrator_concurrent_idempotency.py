"""Integration test for concurrent epic idempotency across simulated replicas."""
import asyncio
import json
import sys
import uuid
from pathlib import Path

import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
if str(SERVICE_ROOT) in sys.path:
    sys.path.remove(str(SERVICE_ROOT))
sys.path.insert(0, str(SERVICE_ROOT))

for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        sys.modules.pop(module_name, None)

from app.models.workflow import CreateEpicRequest, compute_epic_fingerprint  # noqa: E402
from app.services.workflow_service import (  # noqa: E402
    WorkflowConflictError,
    WorkflowService,
    WorkflowUnavailableError,
)


class SharedAtomicClaimStore:
    """Simulates ConPort PostgreSQL with atomic claim semantics in memory.

    Multiple WorkflowService instances share this store through their
    store.claim_epic() path — it is the shared persistence owner.
    """

    def __init__(self):
        self.rows = {}
        self.insert_log = []

    async def claim_epic(self, **kwargs):
        epic_id = kwargs["epic_id"]
        value = dict(kwargs["value"])
        fingerprint = value.get("_fingerprint_v1", "")

        self.insert_log.append(("attempt", epic_id, fingerprint))

        if epic_id in self.rows:
            existing = self.rows[epic_id]
            existing_fp = existing.get("value", {}).get("_fingerprint_v1")
            if existing_fp is None:
                self.insert_log.append(("legacy", epic_id))
                return {
                    "result": "LEGACY_UNFINGERPRINTED",
                    "value": existing["value"],
                }
            if existing_fp == fingerprint:
                self.insert_log.append(("matched", epic_id, fingerprint))
                return {
                    "result": "MATCHED",
                    "value": existing["value"],
                }
            self.insert_log.append(("conflict", epic_id, fingerprint))
            return {
                "result": "CONFLICT",
                "value": existing["value"],
            }

        self.rows[epic_id] = {"key": epic_id, "value": value}
        self.insert_log.append(("created", epic_id, fingerprint))
        return {"result": "CREATED", "value": value}

    async def get_custom_data(self, **kwargs):
        category = kwargs["category"]
        key = kwargs.get("key")
        items = []
        for row_key, row in self.rows.items():
            if key is None or row_key == key:
                items.append({"key": row_key, "value": row["value"]})
        return items

    async def save_custom_data(self, **kwargs):
        key = kwargs["key"]
        value = dict(kwargs.get("value", {}))
        self.rows[key] = {"key": key, "value": value}
        return True

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_two_replica_identical_concurrent_claims():
    """Two independent service instances, 20 concurrent identical create calls.

    Assertions:
    - Exactly one Created
    - At least 19 MATCHED
    - Only one persisted value per identity
    """
    shared_store = SharedAtomicClaimStore()

    request = CreateEpicRequest(
        title="Concurrent identical epic",
        description="Testing concurrent idempotency",
        business_value="Prove atomics work",
        priority="high",
        idempotency_key="concurrent-identical-key",
    )

    async def create_on_service(service_id):
        svc = WorkflowService(workspace_id="/workspace/shared")
        svc.store._client = shared_store
        svc.store.claim_epic = shared_store.claim_epic
        try:
            epic = await svc.create_epic(request)
            return ("ok", epic.id)
        except WorkflowConflictError:
            return ("conflict", None)
        except WorkflowUnavailableError:
            return ("unavailable", None)
        finally:
            await svc.close()

    tasks = [create_on_service(i % 2) for i in range(20)]
    results = await asyncio.gather(*tasks)

    assert len([r for r in results if r[0] == "ok"]) >= 20, "All calls should succeed"
    assert len([r for r in results if r[0] == "conflict"]) == 0

    ok_ids = [r[1] for r in results if r[0] == "ok"]
    assert len(set(ok_ids)) == 1, "All Created/MATCHED should return same epic ID"

    created = sum(1 for entry in shared_store.insert_log if entry[0] == "created")
    matched = sum(1 for entry in shared_store.insert_log if entry[0] == "matched")
    assert created == 1, f"Expected 1 CREATED, got {created}"
    assert matched >= 19, f"Expected >=19 MATCHED, got {matched}"

    assert len(shared_store.rows) == 1


@pytest.mark.asyncio
async def test_two_replica_conflicting_concurrent_claims():
    """Two services, 20 concurrent claims with different fingerprints on same identity.

    Assertions:
    - Exactly one Created
    - At least 19 CONFLICT raised
    - Only one persisted value
    """
    shared_store = SharedAtomicClaimStore()
    base_idempotency_key = None  # Same epic ID, different payloads

    async def create_conflicting(idx):
        svc = WorkflowService(workspace_id="/workspace/shared")
        svc.store._client = shared_store
        svc.store.claim_epic = shared_store.claim_epic
        try:
            req = CreateEpicRequest(
                title=f"Conflict-{idx}",
                description="Different payload for conflicting test",
                business_value=f"Value-{idx}",
                idempotency_key="conflicting-concurrent-key",
            )
            epic = await svc.create_epic(req)
            return ("ok", epic.id)
        except WorkflowConflictError:
            return ("conflict", None)
        except WorkflowUnavailableError:
            return ("unavailable", None)
        finally:
            await svc.close()

    tasks = [create_conflicting(i) for i in range(20)]
    results = await asyncio.gather(*tasks)

    ok_results = [r for r in results if r[0] == "ok"]
    conflict_results = [r for r in results if r[0] == "conflict"]
    assert len(ok_results) == 1, f"Expected 1 ok, got {len(ok_results)}"
    assert len(conflict_results) == 19, f"Expected 19 conflicts, got {len(conflict_results)}"

    assert len(shared_store.rows) == 1

    created = sum(1 for entry in shared_store.insert_log if entry[0] == "created")
    conflicted = sum(1 for entry in shared_store.insert_log if entry[0] == "conflict")
    assert created == 1
    assert conflicted >= 19


@pytest.mark.asyncio
async def test_restart_replay_idempotency():
    """After first claim creates, a subsequent call matches."""
    shared_store = SharedAtomicClaimStore()

    request = CreateEpicRequest(
        title="Restart replay epic",
        description="Testing restart idempotency",
        business_value="Replay safety",
        idempotency_key="restart-replay-key",
    )

    svc1 = WorkflowService(workspace_id="/tmp/svc-restart")
    svc1.store._client = shared_store
    svc1.store.claim_epic = shared_store.claim_epic
    epic1 = await svc1.create_epic(request)
    await svc1.close()

    created = sum(1 for e in shared_store.insert_log if e[0] == "created")
    assert created == 1

    svc2 = WorkflowService(workspace_id="/tmp/svc-restart")
    svc2.store._client = shared_store
    svc2.store.claim_epic = shared_store.claim_epic
    epic2 = await svc2.create_epic(request)
    await svc2.close()

    assert epic2.id == epic1.id
    assert len(shared_store.rows) == 1

    matched = sum(1 for e in shared_store.insert_log if e[0] == "matched")
    assert matched == 1
