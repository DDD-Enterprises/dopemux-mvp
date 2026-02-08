from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.models.workflow import (  # noqa: E402
    CreateIdeaRequest,
    PromoteIdeaRequest,
    UpdateIdeaRequest,
)
from app.services.workflow_service import (  # noqa: E402
    WorkflowConflictError,
    WorkflowService,
)


class InMemoryWorkflowStore:
    def __init__(self) -> None:
        self.ideas = {}
        self.epics = {}

    async def close(self) -> None:
        return None

    async def save_idea(self, idea):
        self.ideas[idea["id"]] = dict(idea)
        return True

    async def save_epic(self, epic):
        self.epics[epic["id"]] = dict(epic)
        return True

    async def get_idea(self, idea_id):
        item = self.ideas.get(idea_id)
        return dict(item) if item else None

    async def get_epic(self, epic_id):
        item = self.epics.get(epic_id)
        return dict(item) if item else None

    async def list_ideas(self, status=None, tag=None, limit=50):
        rows = list(self.ideas.values())
        if status:
            rows = [row for row in rows if row.get("status") == status]
        if tag:
            rows = [row for row in rows if tag in (row.get("tags") or [])]
        rows.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        return [dict(row) for row in rows[:limit]]

    async def list_epics(self, status=None, priority=None, tag=None, limit=50):
        rows = list(self.epics.values())
        if status:
            rows = [row for row in rows if row.get("status") == status]
        if priority:
            rows = [row for row in rows if row.get("priority") == priority]
        if tag:
            rows = [row for row in rows if tag in (row.get("tags") or [])]
        rows.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        return [dict(row) for row in rows[:limit]]


class FakeBridgeClient:
    def __init__(self, *, success=True, payload=None, error=None):
        self.success = success
        self.payload = payload or {}
        self.error = error

    async def route_pm(self, **kwargs):
        return SimpleNamespace(
            success=self.success,
            data=self.payload,
            error=self.error,
        )

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_promote_idea_is_idempotent():
    store = InMemoryWorkflowStore()
    service = WorkflowService(workspace_id="/tmp/ws", store=store)
    await service.bridge_client.aclose()
    service.bridge_client = FakeBridgeClient(success=True, payload={"project_id": 101})

    idea = await service.create_idea(
        CreateIdeaRequest(
            title="Idea title",
            description="Idea description",
            source="brainstorm",
            creator="tester",
            tags=["flow"],
        )
    )

    first = await service.promote_idea(idea.id, PromoteIdeaRequest(sync_to_leantime=True))
    second = await service.promote_idea(idea.id, PromoteIdeaRequest(sync_to_leantime=True))

    assert first["already_promoted"] is False
    assert second["already_promoted"] is True
    assert first["epic"].id == second["epic"].id
    assert first["epic"].leantime_project_id == 101


@pytest.mark.asyncio
async def test_promote_idea_degrades_when_leantime_sync_fails():
    store = InMemoryWorkflowStore()
    service = WorkflowService(workspace_id="/tmp/ws", store=store)
    await service.bridge_client.aclose()
    service.bridge_client = FakeBridgeClient(success=False, error="pm route unavailable")

    idea = await service.create_idea(
        CreateIdeaRequest(
            title="Offline sync idea",
            description="Should still create epic",
            source="other",
            creator="tester",
        )
    )

    result = await service.promote_idea(idea.id, PromoteIdeaRequest(sync_to_leantime=True))

    assert result["epic"].leantime_project_id is None
    assert "pm route unavailable" in str(result["warning"])
    assert service.metrics["workflow_promotion_failures_total"] == 1


@pytest.mark.asyncio
async def test_promoted_idea_cannot_be_demoted():
    store = InMemoryWorkflowStore()
    service = WorkflowService(workspace_id="/tmp/ws", store=store)
    await service.bridge_client.aclose()
    service.bridge_client = FakeBridgeClient(success=True, payload={"project_id": 9})

    idea = await service.create_idea(
        CreateIdeaRequest(
            title="One-way state",
            description="Promotion should be one-way",
            source="user-request",
            creator="tester",
        )
    )
    await service.promote_idea(idea.id, PromoteIdeaRequest(sync_to_leantime=False))

    with pytest.raises(WorkflowConflictError):
        await service.update_idea(idea.id, UpdateIdeaRequest(status="approved"))
