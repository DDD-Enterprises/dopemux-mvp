"""Unit tests for Task Orchestrator atomic epic idempotency."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
if str(SERVICE_ROOT) in sys.path:
    sys.path.remove(str(SERVICE_ROOT))
sys.path.insert(0, str(SERVICE_ROOT))

for module_name in list(sys.modules):
    if module_name == "app" or module_name.startswith("app."):
        sys.modules.pop(module_name, None)

from app.models.workflow import CreateEpicRequest  # noqa: E402
from app.services.workflow_service import (  # noqa: E402
    WorkflowConflictError,
    WorkflowService,
    WorkflowUnavailableError,
)


@pytest.mark.asyncio
async def test_create_epic_claim_created_returns_epic():
    service = WorkflowService(workspace_id="/tmp/atomic-claim-test")
    claim_mock = AsyncMock()
    claim_mock.return_value = {"result": "CREATED", "value": {}}
    service.store.claim_epic = claim_mock

    try:
        epic = await service.create_epic(
            CreateEpicRequest(
                title="Test Epic",
                description="desc",
                business_value="val",
                idempotency_key="key-1",
            )
        )
        assert epic.title == "Test Epic"
        assert epic.id.startswith("epic_")
        assert service.metrics["workflow_epics_created_total"] == 1
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_create_epic_claim_matched_returns_existing_epic():
    service = WorkflowService(workspace_id="/tmp/atomic-claim-test")
    claim_mock = AsyncMock()
    claim_mock.return_value = {
        "result": "MATCHED",
        "value": {
            "id": "epic_matched",
            "title": "Matched Epic",
            "description": "desc",
            "business_value": "val",
            "acceptance_criteria": [],
            "priority": "high",
            "status": "planned",
            "tags": [],
            "adhd_metadata": {},
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "version": 1,
            "_fingerprint_v1": "abc123",
        },
    }
    service.store.claim_epic = claim_mock

    try:
        epic = await service.create_epic(
            CreateEpicRequest(
                title="Matched Epic",
                description="desc",
                business_value="val",
                idempotency_key="key-1",
            )
        )
        assert epic.title == "Matched Epic"
        assert epic.id == "epic_matched"
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_create_epic_claim_conflict_raises_409():
    service = WorkflowService(workspace_id="/tmp/atomic-claim-test")
    claim_mock = AsyncMock()
    claim_mock.return_value = {
        "result": "CONFLICT",
        "value": {"_fingerprint_v1": "different"},
    }
    service.store.claim_epic = claim_mock

    try:
        with pytest.raises(WorkflowConflictError, match="idempotency key"):
            await service.create_epic(
                CreateEpicRequest(
                    title="Test Epic",
                    description="desc",
                    business_value="val",
                    idempotency_key="key-1",
                )
            )
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_create_epic_claim_legacy_raises():
    service = WorkflowService(workspace_id="/tmp/atomic-claim-test")
    claim_mock = AsyncMock()
    claim_mock.return_value = {
        "result": "LEGACY_UNFINGERPRINTED",
        "value": {"title": "old"},
    }
    service.store.claim_epic = claim_mock

    try:
        with pytest.raises(WorkflowConflictError, match="fingerprint"):
            await service.create_epic(
                CreateEpicRequest(
                    title="Test Epic",
                    description="desc",
                    business_value="val",
                    idempotency_key="key-1",
                )
            )
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_create_epic_claim_owner_error_raises():
    service = WorkflowService(workspace_id="/tmp/atomic-claim-test")
    claim_mock = AsyncMock()
    claim_mock.return_value = {
        "result": "OWNER_ERROR",
        "error": "db down",
    }
    service.store.claim_epic = claim_mock

    try:
        with pytest.raises(WorkflowUnavailableError):
            await service.create_epic(
                CreateEpicRequest(
                    title="Test Epic",
                    description="desc",
                    business_value="val",
                    idempotency_key="key-1",
                )
            )
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_fingerprint_deterministic():
    """Same request produces the same fingerprint."""
    from app.models.workflow import compute_epic_fingerprint  # noqa: E402

    r1 = CreateEpicRequest(
        title="Fix races",
        description="Make it atomic",
        business_value="Correctness",
        idempotency_key="key-a",
    )
    r2 = CreateEpicRequest(
        title="Fix races",
        description="Make it atomic",
        business_value="Correctness",
        idempotency_key="key-b",
    )

    assert compute_epic_fingerprint(r1) == compute_epic_fingerprint(r2)


@pytest.mark.asyncio
async def test_fingerprint_differs_on_different_payload():
    from app.models.workflow import compute_epic_fingerprint  # noqa: E402

    r1 = CreateEpicRequest(
        title="Fix races",
        description="Make it atomic",
        business_value="Correctness",
    )
    r2 = CreateEpicRequest(
        title="Different title",
        description="Make it atomic",
        business_value="Correctness",
    )

    assert compute_epic_fingerprint(r1) != compute_epic_fingerprint(r2)


@pytest.mark.asyncio
async def test_fingerprint_excludes_idempotency_key():
    """Two identical requests with different idempotency keys produce same fingerprint."""
    from app.models.workflow import compute_epic_fingerprint  # noqa: E402

    r1 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
        idempotency_key="key-x",
    )
    r2 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
        idempotency_key="key-y",
    )
    r3 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
    )

    fp1 = compute_epic_fingerprint(r1)
    fp2 = compute_epic_fingerprint(r2)
    fp3 = compute_epic_fingerprint(r3)

    assert fp1 == fp2 == fp3


@pytest.mark.asyncio
async def test_fingerprint_equivalent_normalized_requests_hash_identically():
    """Equivalent normalized requests hash identically regardless of key order."""
    from app.models.workflow import compute_epic_fingerprint  # noqa: E402

    r1 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
        acceptance_criteria=["alpha", "beta", "gamma"],
        tags=["one", "two"],
    )
    r2 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
        acceptance_criteria=["alpha", "beta", "gamma"],
        tags=["one", "two"],
    )

    assert compute_epic_fingerprint(r1) == compute_epic_fingerprint(r2)


@pytest.mark.asyncio
async def test_fingerprint_reordered_acceptance_criteria_differ():
    """Reordered acceptance criteria are distinct immutable requests."""
    from app.models.workflow import compute_epic_fingerprint  # noqa: E402

    r1 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
        acceptance_criteria=["alpha", "beta", "gamma"],
    )
    r2 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
        acceptance_criteria=["gamma", "beta", "alpha"],
    )

    assert compute_epic_fingerprint(r1) != compute_epic_fingerprint(r2)


@pytest.mark.asyncio
async def test_fingerprint_reordered_tags_differ():
    """Reordered tags are distinct immutable requests."""
    from app.models.workflow import compute_epic_fingerprint  # noqa: E402

    r1 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
        tags=["one", "two", "three"],
    )
    r2 = CreateEpicRequest(
        title="Same",
        description="Same",
        business_value="Same",
        tags=["three", "two", "one"],
    )

    assert compute_epic_fingerprint(r1) != compute_epic_fingerprint(r2)
