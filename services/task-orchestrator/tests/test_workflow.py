import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import app.api.project_workflow as project_workflow_api
from app.api.project_workflow import (
    get_project_workflow_blockers,
    get_project_workflow_queue,
    get_project_workflow_state,
)
from app.models.workflow import (
    CreateEpicRequest,
    CreateIdeaRequest,
    PromoteIdeaRequest,
    UpdateEpicRequest,
    UpdateIdeaRequest,
    WorkflowEpic,
    WorkflowIdea,
)
from app.services.workflow_service import WorkflowService, WorkflowConflictError, WorkflowUnavailableError

class MockStore:
    def __init__(self):
        self.ideas = {}
        self.epics = {}
        self.audits = {}
        self.fail_audit = False

    async def get_idea(self, idea_id):
        return self.ideas.get(idea_id)

    async def get_epic(self, epic_id):
        return self.epics.get(epic_id)

    async def get_idea_by_idempotency_key(self, key):
        for val in self.ideas.values():
            if val.get("idempotency_key") == key:
                return val
        return None

    async def get_epic_by_idempotency_key(self, key):
        for val in self.epics.values():
            if val.get("idempotency_key") == key:
                return val
        return None

    async def save_idea(self, idea_data):
        self.ideas[idea_data["id"]] = idea_data
        return True

    async def save_epic(self, epic_data):
        self.epics[epic_data["id"]] = epic_data
        return True
        
    async def save_audit_record(self, record):
        if self.fail_audit:
            return False
        self.audits[record["id"]] = record
        return True

    async def close(self):
        pass

@pytest.fixture
def mock_store():
    return MockStore()

@pytest.fixture
def service(mock_store):
    svc = WorkflowService(workspace_id="test", store=mock_store)
    return svc

@pytest.mark.asyncio
async def test_direct_status_mutation_blocked_idea(service):
    idea = await service.create_idea(CreateIdeaRequest(title="T", description="D"))
    with pytest.raises(WorkflowConflictError, match="direct status mutation blocked"):
        await service.update_idea(idea.id, UpdateIdeaRequest(status="promoted"))

@pytest.mark.asyncio
async def test_duplicate_create(service):
    req1 = CreateIdeaRequest(title="T1", description="D1", idempotency_key="create_key")
    idea1 = await service.create_idea(req1)
    
    req2 = CreateIdeaRequest(title="T2", description="D2", idempotency_key="create_key")
    idea2 = await service.create_idea(req2)
    
    # Should return the same idea and not duplicate mutation
    assert idea1.id == idea2.id
    assert idea2.title == "T1"

@pytest.mark.asyncio
async def test_stale_version_rejected(service):
    idea = await service.create_idea(CreateIdeaRequest(title="T", description="D"))
    req = UpdateIdeaRequest(title="T2")
    req.version = idea.version - 1
    with pytest.raises(WorkflowConflictError, match="stale version update rejected"):
        await service.update_idea(idea.id, req)

@pytest.mark.asyncio
async def test_idempotent_idea_update(service):
    idea = await service.create_idea(CreateIdeaRequest(title="T", description="D"))
    
    req1 = UpdateIdeaRequest(title="T2", idempotency_key="update_key")
    idea1 = await service.update_idea(idea.id, req1)
    
    # Same update idempotency key
    req2 = UpdateIdeaRequest(title="T3", idempotency_key="update_key")
    idea2 = await service.update_idea(idea.id, req2)
    
    assert idea1.title == "T2"
    assert idea2.title == "T2"
    assert idea1.version == idea2.version

@pytest.mark.asyncio
async def test_conflicting_linked_id_overwrite(service):
    epic = await service.create_epic(CreateEpicRequest(title="E1", description="D1", business_value="BV"))
    
    # First update sets leantime_project_id
    req1 = UpdateEpicRequest(leantime_project_id=10)
    epic = await service.update_epic(epic.id, req1)
    
    # Second update conflicts
    req2 = UpdateEpicRequest(leantime_project_id=20)
    with pytest.raises(WorkflowConflictError, match="conflicting linked-ID overwrite fails closed"):
        await service.update_epic(epic.id, req2)
        
    # Second update matches (should succeed)
    req3 = UpdateEpicRequest(leantime_project_id=10)
    epic = await service.update_epic(epic.id, req3)
    assert epic.leantime_project_id == 10

@pytest.mark.asyncio
async def test_promote_idea_audit_failure(service, mock_store):
    idea = await service.create_idea(CreateIdeaRequest(title="T", description="D"))
    mock_store.fail_audit = True
    
    with pytest.raises(WorkflowUnavailableError, match="failed to persist workflow transition audit"):
        await service.promote_idea(idea.id, PromoteIdeaRequest(business_value="test value"))
        
    # Check that idea was not promoted
    stored_idea = await service.get_idea(idea.id)
    assert stored_idea.status == "new"


@pytest.mark.asyncio
async def test_project_workflow_queue_uses_local_epic_ordering(monkeypatch):
    class WorkflowReadService:
        async def list_ideas(self, limit=1000):
            return []

        async def list_epics(self, limit=1000):
            return [
                WorkflowEpic(
                    id="epic_planned",
                    title="Planned Epic",
                    description="lowest rank",
                    business_value="value",
                    priority="critical",
                    status="planned",
                    updated_at="2026-03-01T00:00:00+00:00",
                ),
                WorkflowEpic(
                    id="epic_ready_high",
                    title="Ready Epic",
                    description="top rank",
                    business_value="value",
                    priority="high",
                    status="ready",
                    updated_at="2026-03-02T00:00:00+00:00",
                ),
                WorkflowEpic(
                    id="epic_ready_medium",
                    title="Second Ready Epic",
                    description="after high priority",
                    business_value="value",
                    priority="medium",
                    status="ready",
                    updated_at="2026-03-03T00:00:00+00:00",
                ),
            ]

    monkeypatch.setattr(project_workflow_api, "_workflow_service", lambda: WorkflowReadService())
    result = await get_project_workflow_queue("proj-123")

    assert result.project_id == "proj-123"
    assert result.legality_result == "available"
    assert [item["workflow_id"] for item in result.queue_items] == [
        "epic_ready_high",
        "epic_ready_medium",
        "epic_planned",
    ]
    assert result.next_action["workflow_id"] == "epic_ready_high"


@pytest.mark.asyncio
async def test_project_workflow_blockers_reflect_local_degraded_epics(monkeypatch):
    class WorkflowReadService:
        async def list_ideas(self, limit=1000):
            return []

        async def list_epics(self, limit=1000):
            return [
                WorkflowEpic(
                    id="epic_blocked",
                    title="Blocked Epic",
                    description="blocked",
                    business_value="value",
                    priority="high",
                    status="ready",
                    leantime_project_id=42,
                    leantime_reflection={"status": "degraded", "warning": "sync lag"},
                ),
                WorkflowEpic(
                    id="epic_clear",
                    title="Clear Epic",
                    description="clear",
                    business_value="value",
                    priority="medium",
                    status="in-progress",
                ),
            ]

    monkeypatch.setattr(project_workflow_api, "_workflow_service", lambda: WorkflowReadService())
    result = await get_project_workflow_blockers("proj-123")

    assert result.project_id == "proj-123"
    assert result.legality_result == "available"
    assert len(result.active_blockers) == 1
    assert result.active_blockers[0]["workflow_id"] == "epic_blocked"
    assert result.active_blockers[0]["reflection_status"] == "degraded"
    assert result.blockers == ["epic_blocked"]


@pytest.mark.asyncio
async def test_project_workflow_state_summarizes_local_records(monkeypatch):
    class WorkflowReadService:
        async def list_ideas(self, limit=1000):
            return [
                WorkflowIdea(
                    id="idea_ready",
                    title="Idea Ready",
                    description="idea",
                    status="approved",
                ),
                WorkflowIdea(
                    id="idea_promoted",
                    title="Idea Promoted",
                    description="idea",
                    status="promoted",
                    promoted_to_epic_id="epic_ready",
                ),
            ]

        async def list_epics(self, limit=1000):
            return [
                WorkflowEpic(
                    id="epic_ready",
                    title="Ready Epic",
                    description="epic",
                    business_value="value",
                    priority="high",
                    status="ready",
                    created_from_idea_id="idea_promoted",
                    leantime_project_id=17,
                ),
                WorkflowEpic(
                    id="epic_done",
                    title="Done Epic",
                    description="epic",
                    business_value="value",
                    priority="low",
                    status="done",
                ),
            ]

    monkeypatch.setattr(project_workflow_api, "_workflow_service", lambda: WorkflowReadService())
    result = await get_project_workflow_state("proj-123")

    assert result.project_id == "proj-123"
    assert result.legality_result == "available"
    assert result.state["ideas"]["approved"]["ids"] == ["idea_ready"]
    assert result.state["ideas"]["promoted"]["ids"] == ["idea_promoted"]
    assert result.state["epics"]["ready"]["ids"] == ["epic_ready"]
    assert result.state["epics"]["done"]["ids"] == ["epic_done"]
    assert result.linked_ids["epic_ready:created_from_idea_id"] == "idea_promoted"
    assert result.linked_ids["epic_ready:leantime_project_id"] == "17"
    assert result.allowed_transitions == []
