import pytest
from dopemux.pm.reads import (
    PMBlockersResult,
    PMDecisionContextResult,
    PMPriorityQueueResult,
    PMProjectContextResult,
    PMProjectKnowledgeResult,
    PMSprintSnapshotResult,
    PMTechnicalContextResult,
    PMWorkflowStateResult,
    pm_get_blockers,
    pm_get_decision_context,
    pm_get_priority_queue,
    pm_get_project_context,
    pm_get_sprint_snapshot,
    pm_get_technical_context,
    pm_get_workflow_state,
    pm_search_project_knowledge,
)


class FakeConPortContextClient:
    def __init__(self, payload):
        self.payload = payload
        self.closed = False

    async def get_active_context(self, workspace_id: str):
        assert workspace_id == "proj-123"
        return self.payload

    async def close(self):
        self.closed = True


class FakeLeantimeResponse:
    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error


class FakeLeantimeClient:
    def __init__(self, project_payload, tickets_payload):
        self.project_payload = project_payload
        self.tickets_payload = tickets_payload
        self.connected = False
        self.disconnected = False

    async def connect(self):
        self.connected = True
        return True

    async def disconnect(self):
        self.disconnected = True

    async def get_project(self, project_id: int):
        assert project_id == 123
        return self.project_payload

    async def get_tickets(self, project_id: int, limit: int = 100):
        assert project_id == 123
        assert limit == 100
        return self.tickets_payload


class FakeConPortDecisionClient:
    def __init__(self, payload):
        self.payload = payload

    async def search_decisions(self, limit: int = 5):
        assert limit == 5
        return self.payload


class FakeAsyncSearchClient:
    def __init__(self, payload, method_name):
        self.payload = payload
        self.method_name = method_name

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def search_all(self, query: str, top_k: int = 5):
        assert self.method_name == "search_all"
        assert query == "release notes"
        assert top_k == 3
        return self.payload

    async def find_symbol(self, query: str):
        assert self.method_name == "find_symbol"
        assert query == "TaskCoordinator"
        return self.payload


@pytest.mark.asyncio
async def test_pm_get_project_context_routes_to_conport(monkeypatch):
    fake_client = FakeConPortContextClient(
        {
            "active_context": "Packet 06 planning",
            "decision_ids": ["dec-1"],
            "linked_ids": {"conport_context": "ctx-123"},
        }
    )
    monkeypatch.setattr(
        "dopemux.pm.reads._conport_context_client",
        lambda: fake_client,
    )

    result = await pm_get_project_context("proj-123")

    assert isinstance(result, PMProjectContextResult)
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "conport"
    assert result.provenance.source == "conport"
    assert result.provenance.query_mode == "project_context"
    assert result.supporting_sources[0].backend == "conport"
    assert result.context_data["active_context"] == "Packet 06 planning"
    assert result.linked_ids["project"] == "proj-123"
    assert result.linked_ids["conport_context"] == "ctx-123"
    assert fake_client.closed is True


@pytest.mark.asyncio
async def test_pm_get_priority_queue():
    result = await pm_get_priority_queue("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "task-orchestrator"
    assert result.provenance.source == "task-orchestrator"
    assert result.queue_items == [] # Stubbed to fail-closed empty list

@pytest.mark.asyncio
async def test_pm_get_blockers():
    result = await pm_get_blockers("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "task-orchestrator"
    assert result.provenance.source == "task-orchestrator"
    assert result.active_blockers == [] # Stubbed to fail-closed empty list

@pytest.mark.asyncio
async def test_pm_get_workflow_state():
    result = await pm_get_workflow_state("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "task-orchestrator"
    assert result.provenance.source == "task-orchestrator"
    assert result.state == {} # Stubbed to fail-closed empty dict
    assert result.allowed_transitions == []

@pytest.mark.asyncio
async def test_pm_get_sprint_snapshot_routes_to_leantime(monkeypatch):
    fake_client = FakeLeantimeClient(
        project_payload=FakeLeantimeResponse(success=True, data={"id": 123, "name": "PM Sprint"}),
        tickets_payload=FakeLeantimeResponse(
            success=True,
            data=[{"id": 1, "headline": "Boundary"}, {"id": 2, "headline": "Reads"}],
        ),
    )
    monkeypatch.setattr(
        "dopemux.pm.reads._leantime_client",
        lambda: fake_client,
    )

    result = await pm_get_sprint_snapshot("123")

    assert isinstance(result, PMSprintSnapshotResult)
    assert result.project_id == "123"
    assert result.canonical_backend == "leantime"
    assert result.provenance.source == "leantime"
    assert result.snapshot_data["project"]["name"] == "PM Sprint"
    assert result.snapshot_data["ticket_count"] == 2
    assert result.linked_ids["leantime_project"] == "123"
    assert fake_client.connected is True
    assert fake_client.disconnected is True


@pytest.mark.asyncio
async def test_pm_get_sprint_snapshot_fails_closed_for_non_numeric_project_id():
    result = await pm_get_sprint_snapshot("proj-123")

    assert result.canonical_backend == "leantime"
    assert result.snapshot_data == {}
    assert result.error == "invalid Leantime project id: proj-123"


@pytest.mark.asyncio
async def test_pm_get_decision_context(monkeypatch):
    fake_client = FakeConPortDecisionClient({"decisions": [{"id": "d-1"}]})
    monkeypatch.setattr("dopemux.pm.reads._conport", fake_client)

    result = await pm_get_decision_context("proj-123")

    assert result.project_id == "proj-123"
    assert result.canonical_backend == "conport"
    assert result.provenance.source == "conport"
    assert result.decisions[0]["id"] == "d-1"


@pytest.mark.asyncio
async def test_pm_search_project_knowledge_routes_to_dope_context(monkeypatch):
    fake_client = FakeAsyncSearchClient(
        {"results": [{"path": "docs/pm.md", "summary": "PM contract", "score": 0.91}]},
        "search_all",
    )
    monkeypatch.setattr(
        "dopemux.pm.reads._dope_context_client",
        lambda: fake_client,
    )

    result = await pm_search_project_knowledge("proj-123", "release notes", top_k=3)

    assert isinstance(result, PMProjectKnowledgeResult)
    assert result.canonical_backend == "dope-context"
    assert result.provenance.source == "dope-context"
    assert result.query == "release notes"
    assert result.evidence[0]["source_ref"] == "docs/pm.md"
    assert result.evidence[0]["confidence"] == 0.91


@pytest.mark.asyncio
async def test_pm_get_technical_context_routes_to_serena(monkeypatch):
    fake_client = FakeAsyncSearchClient(
        {"symbols": [{"name": "TaskCoordinator", "file_path": "task_coordinator.py", "line": 42}]},
        "find_symbol",
    )
    monkeypatch.setattr(
        "dopemux.pm.reads._serena_client",
        lambda: fake_client,
    )

    result = await pm_get_technical_context("proj-123", "TaskCoordinator")

    assert isinstance(result, PMTechnicalContextResult)
    assert result.canonical_backend == "serena"
    assert result.provenance.source == "serena"
    assert result.query == "TaskCoordinator"
    assert result.technical_findings[0]["symbol"] == "TaskCoordinator"
    assert result.technical_findings[0]["file_path"] == "task_coordinator.py"
