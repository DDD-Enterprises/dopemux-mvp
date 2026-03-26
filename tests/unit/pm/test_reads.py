import httpx
import pytest

from dopemux.pm import reads as pm_reads
from dopemux.pm.reads import (
    PMBlockersResult,
    PMDecisionContextResult,
    PMPriorityQueueResult,
    PMProjectContextResult,
    PMWorkflowStateResult,
    pm_get_blockers,
    pm_get_decision_context,
    pm_get_priority_queue,
    pm_get_project_context,
    pm_get_sprint_snapshot,
    pm_get_workflow_state,
)


@pytest.mark.asyncio
async def test_pm_get_project_context():
    result = await pm_get_project_context("proj-123")
    assert isinstance(result, PMProjectContextResult)
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "orchestrator"
    assert result.provenance.source == "leantime"
    assert result.provenance.query_mode == "project_context"
    assert result.supporting_sources[0].backend == "leantime"
    assert result.context_data == {}


@pytest.mark.asyncio
async def test_pm_get_priority_queue_routes_to_task_orchestrator(monkeypatch):
    async def fake_get_queue(project_id: str):
        assert project_id == "proj-123"
        return {
            "linked_ids": {"workflow": "wf-1"},
            "legality_result": "allowed",
            "blockers": ["needs-owner"],
            "next_action": {"workflow_id": "wf-1"},
            "queue_items": [{"id": "wf-1", "title": "Implement boundary"}],
        }

    monkeypatch.setattr(pm_reads._orchestrator, "get_queue", fake_get_queue)

    result = await pm_get_priority_queue("proj-123")
    assert isinstance(result, PMPriorityQueueResult)
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "task-orchestrator"
    assert result.provenance.source == "task-orchestrator"
    assert result.supporting_sources[0].backend == "task-orchestrator"
    assert result.legality_result == "allowed"
    assert result.queue_items[0]["id"] == "wf-1"


@pytest.mark.asyncio
async def test_pm_get_priority_queue_fails_closed_on_http_error(monkeypatch):
    async def boom(project_id: str):
        raise httpx.HTTPStatusError(
            "upstream unavailable",
            request=httpx.Request("GET", f"http://example.test/{project_id}"),
            response=httpx.Response(503),
        )

    monkeypatch.setattr(pm_reads._orchestrator, "get_queue", boom)

    result = await pm_get_priority_queue("proj-123")
    assert result.canonical_backend == "task-orchestrator"
    assert result.legality_result == "unavailable"
    assert result.queue_items == []
    assert result.error is None


@pytest.mark.asyncio
async def test_pm_get_blockers_routes_to_task_orchestrator(monkeypatch):
    async def fake_get_blockers(project_id: str):
        return {
            "linked_ids": {"workflow": "wf-2"},
            "legality_result": "blocked",
            "blockers": ["external-dependency"],
            "active_blockers": [{"id": "blk-1", "summary": "Waiting on API"}],
        }

    monkeypatch.setattr(pm_reads._orchestrator, "get_blockers", fake_get_blockers)

    result = await pm_get_blockers("proj-123")
    assert isinstance(result, PMBlockersResult)
    assert result.canonical_backend == "task-orchestrator"
    assert result.provenance.source == "task-orchestrator"
    assert result.legality_result == "blocked"
    assert result.active_blockers[0]["id"] == "blk-1"


@pytest.mark.asyncio
async def test_pm_get_workflow_state_routes_to_task_orchestrator(monkeypatch):
    async def fake_get_state(project_id: str):
        return {
            "linked_ids": {"workflow": "wf-3"},
            "legality_result": "allowed",
            "state": {"status": "in_progress"},
            "allowed_transitions": ["done"],
        }

    monkeypatch.setattr(pm_reads._orchestrator, "get_state", fake_get_state)

    result = await pm_get_workflow_state("proj-123")
    assert isinstance(result, PMWorkflowStateResult)
    assert result.canonical_backend == "task-orchestrator"
    assert result.provenance.source == "task-orchestrator"
    assert result.state == {"status": "in_progress"}
    assert result.allowed_transitions == ["done"]


@pytest.mark.asyncio
async def test_pm_get_sprint_snapshot():
    result = await pm_get_sprint_snapshot("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "orchestrator"
    assert result.provenance.source == "leantime"
    assert result.snapshot_data == {}


@pytest.mark.asyncio
async def test_pm_get_decision_context_routes_to_conport(monkeypatch):
    async def fake_search_decisions(limit: int = 5):
        assert limit == 5
        return {"decisions": [{"id": "d-1", "summary": "Use canonical queue"}]}

    monkeypatch.setattr(pm_reads._conport, "search_decisions", fake_search_decisions)

    result = await pm_get_decision_context("proj-123")
    assert isinstance(result, PMDecisionContextResult)
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "conport"
    assert result.provenance.source == "conport"
    assert result.decisions[0]["id"] == "d-1"
