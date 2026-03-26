from pathlib import Path
import sys

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.api import project_workflow
from dopemux.pm.reads import (
    PMPriorityQueueResult,
    PMReadProvenance,
    PMReadSupportingSource,
    PMWorkflowStateResult,
)


@pytest.mark.asyncio
async def test_get_project_workflow_queue_passes_through_legality_result(monkeypatch):
    async def fake_priority_queue(project_id: str):
        return PMPriorityQueueResult(
            canonical_backend="task-orchestrator",
            project_id=project_id,
            linked_ids={"workflow": "wf-1"},
            provenance=PMReadProvenance(
                source="task-orchestrator",
                query_mode="priority_queue",
                project_id=project_id,
            ),
            supporting_sources=[
                PMReadSupportingSource(kind="canonical", backend="task-orchestrator", entity_ids=[project_id])
            ],
            legality_result="blocked",
            blockers=["needs-review"],
            next_action={"workflow_id": "wf-1"},
            queue_items=[{"id": "wf-1", "title": "Review authority"}],
        )

    monkeypatch.setattr(project_workflow, "pm_get_priority_queue", fake_priority_queue)

    result = await project_workflow.get_project_workflow_queue("proj-123")

    assert result.project_id == "proj-123"
    assert result.legality_result == "blocked"
    assert result.blockers == ["needs-review"]
    assert result.queue_items[0]["id"] == "wf-1"


@pytest.mark.asyncio
async def test_get_project_workflow_state_passes_through_allowed_transitions(monkeypatch):
    async def fake_workflow_state(project_id: str):
        return PMWorkflowStateResult(
            canonical_backend="task-orchestrator",
            project_id=project_id,
            linked_ids={"workflow": "wf-2"},
            provenance=PMReadProvenance(
                source="task-orchestrator",
                query_mode="workflow_state",
                project_id=project_id,
            ),
            supporting_sources=[
                PMReadSupportingSource(kind="canonical", backend="task-orchestrator", entity_ids=[project_id])
            ],
            legality_result="allowed",
            blockers=[],
            next_action=None,
            state={"status": "ready"},
            allowed_transitions=["start", "block"],
        )

    monkeypatch.setattr(project_workflow, "pm_get_workflow_state", fake_workflow_state)

    result = await project_workflow.get_project_workflow_state("proj-123")

    assert result.project_id == "proj-123"
    assert result.legality_result == "allowed"
    assert result.state == {"status": "ready"}
    assert result.allowed_transitions == ["start", "block"]


@pytest.mark.asyncio
async def test_transition_project_workflow_fails_closed_when_runtime_binding_missing():
    request = project_workflow.TransitionWorkflowRequest(workflow_id="wf-3", transition="start")

    result = await project_workflow.transition_project_workflow("proj-123", request)

    assert result.project_id == "proj-123"
    assert result.workflow_id == "wf-3"
    assert result.legality_result == "unavailable"
    assert result.transition_receipt["status"] == "unavailable"
    assert result.resulting_state == {}
