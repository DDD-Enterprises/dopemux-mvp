import pytest
from typing import Any, Dict

from dopemux.pm.api import (
    PMWriteBoundary,
    classify_pm_write,
    is_workflow_significant_payload,
)


def test_classify_pm_write():
    metadata_fields, workflow_fields = classify_pm_write(
        {
            "title": "New Title",
            "status": "in_progress",
            "description": "Details",
        }
    )

    assert "title" in metadata_fields
    assert "description" in metadata_fields
    assert "status" in workflow_fields


def test_classify_pm_write_unrecognized_status():
    metadata_fields, workflow_fields = classify_pm_write(
        {
            "custom_state": "closed",
            "notes": "value",
        }
    )
    assert "custom_state" in workflow_fields
    assert "notes" in metadata_fields


def test_is_workflow_significant_payload():
    assert is_workflow_significant_payload({"status": "done"}) is True
    assert is_workflow_significant_payload({"title": "Updated", "description": "Notes"}) is False
    assert is_workflow_significant_payload({"title": "Updated", "state": "closed"}) is True


class MockLeantime:
    async def update_ticket(self, id: str, data: Dict[str, Any]):
        return {"success": True}


class MockOrchestrator:
    async def transition_task(self, project_id: str, id: str, transition: str, data: Dict[str, Any]):
        return {"success": True, "project_id": project_id, "id": id, "transition": transition}


class MockConport:
    async def record_progress(self, id: str, description: str, is_decision: bool, idempotency_key: str | None):
        return {"success": True}


class MockMemory:
    async def append_chronicle(self, id: str, description: str, is_decision: bool, idempotency_key: str | None):
        return {"success": True}


class FailingLeantime:
    async def update_ticket(self, id: str, data: Dict[str, Any]):
        raise Exception("Leantime offline")


class FailingOrchestrator:
    async def transition_task(self, project_id: str, id: str, transition: str, data: Dict[str, Any]):
        raise Exception("Task Orchestrator offline")


@pytest.mark.asyncio
async def test_pm_update_work_item_metadata_only():
    boundary = PMWriteBoundary(leantime_client=MockLeantime())

    result = await boundary.pm_update_work_item(
        "task_1",
        {
            "title": "Updated Metadata",
            "assignee": "jules",
        },
    )

    assert result["success"] is True
    assert result["operation_type"] == "metadata_update"
    assert result["canonical_backend"] == "leantime"
    assert result["reflection_state"] == "succeeded"


@pytest.mark.asyncio
async def test_pm_update_work_item_empty():
    boundary = PMWriteBoundary(leantime_client=MockLeantime())
    result = await boundary.pm_update_work_item("task_1", {})
    assert result["success"] is False
    assert "Empty payload" in result["error"]


@pytest.mark.asyncio
async def test_pm_update_work_item_rejects_unproven_metadata():
    boundary = PMWriteBoundary(leantime_client=MockLeantime())
    result = await boundary.pm_update_work_item("task_1", {"tags": ["ops"]})
    assert result["success"] is False
    assert "Unsupported metadata fields" in result["error"]


@pytest.mark.asyncio
async def test_pm_update_work_item_leantime_fails():
    boundary = PMWriteBoundary(leantime_client=FailingLeantime())
    result = await boundary.pm_update_work_item("task_1", {"title": "Updated Title"})
    assert result["success"] is False
    assert result["reflection_state"] == "failed"
    assert result["reconciliation_state"] == "failed"
    assert "Leantime offline" in result["error"]


@pytest.mark.asyncio
async def test_pm_update_work_item_rejected_mixed():
    boundary = PMWriteBoundary(leantime_client=MockLeantime())

    result = await boundary.pm_update_work_item(
        "task_2",
        {
            "title": "Updated Title",
            "status": "in_progress",
        },
    )

    assert result["success"] is False
    assert "payload included workflow-significant fields" in result["error"]
    assert result["reflection_state"] == "failed"
    assert result["reconciliation_state"] == "rejected"


@pytest.mark.asyncio
async def test_pm_transition_work_item_success():
    boundary = PMWriteBoundary(orchestrator_client=MockOrchestrator(), project_id="proj-3")

    result = await boundary.pm_transition_work_item("task_3", "start")

    assert result["success"] is True
    assert result["canonical_backend"] == "task_orchestrator"
    assert result["operation_type"] == "transition"
    assert result["reflection_state"] == "not_requested"
    assert result["reconciliation_state"] == "synchronized"


@pytest.mark.asyncio
async def test_pm_transition_work_item_orchestrator_fails():
    boundary = PMWriteBoundary(orchestrator_client=FailingOrchestrator())
    result = await boundary.pm_transition_work_item("task_5", "done")

    assert result["success"] is False
    assert result["reflection_state"] == "failed"
    assert "Task Orchestrator offline" in result["error"]


@pytest.mark.asyncio
async def test_pm_transition_work_item_no_clients_fails_closed():
    boundary = PMWriteBoundary()
    result = await boundary.pm_transition_work_item("task_6", "done")
    assert result["success"] is False
    assert "Task Orchestrator client unavailable" in result["error"]


@pytest.mark.asyncio
async def test_pm_log_progress_requires_conport():
    boundary = PMWriteBoundary()
    result = await boundary.pm_log_progress("task_1", {"msg": "update"})
    assert result["success"] is False
    assert result["canonical_backend"] == "conport"


@pytest.mark.asyncio
async def test_pm_log_progress_success_with_memory_mirror():
    boundary = PMWriteBoundary(
        conport_client=MockConport(),
        memory_client=MockMemory(),
    )
    result = await boundary.pm_log_progress("task_1", {"description": "update", "idempotency_key": "idem-1"})
    assert result["success"] is True
    assert result["canonical_backend"] == "conport"
    assert result["operation_type"] == "log_progress"
    assert result["reflection_state"] == "succeeded"
