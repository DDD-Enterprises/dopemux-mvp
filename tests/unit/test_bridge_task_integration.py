from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "dopecon-bridge"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from dopecon_bridge.models import TaskStatus  # noqa: E402
from dopecon_bridge.services.task_integration import TaskIntegrationService  # noqa: E402


class DummyResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status = status
        self._payload = payload or {}
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        return self._payload

    async def text(self):
        return self._text


@pytest.mark.asyncio
async def test_get_priority_queue_routes_through_task_orchestrator_pm_read(monkeypatch):
    service = TaskIntegrationService()

    async def fake_priority_queue(project_id: str):
        class Result:
            def model_dump(self):
                return {
                    "canonical_backend": "task-orchestrator",
                    "project_id": project_id,
                    "legality_result": "allowed",
                    "queue_items": [{"id": "wf-1", "title": "Canonical task"}],
                }

        return Result()

    monkeypatch.setattr(
        "dopecon_bridge.services.task_integration.pm_get_priority_queue",
        fake_priority_queue,
    )

    result = await service.get_priority_queue("proj-123")

    assert result["canonical_backend"] == "task-orchestrator"
    assert result["queue_items"][0]["id"] == "wf-1"


@pytest.mark.asyncio
async def test_update_task_status_uses_project_scoped_deterministic_idempotency_key():
    service = TaskIntegrationService()
    service.mcp_manager = AsyncMock()
    service.mcp_manager.initialize = AsyncMock()
    service.mcp_manager.session = MagicMock()
    service.mcp_manager.session.post.return_value = DummyResponse(
        status=200,
        payload={"legality_result": "allowed"},
    )
    service.mcp_manager.call_tool = AsyncMock(return_value={"id": "lt-1"})

    result = await service.update_task_status(
        "task-123",
        TaskStatus.IN_PROGRESS,
        assigned_to="alex",
        project_id="proj-123",
    )

    post_url = service.mcp_manager.session.post.call_args.args[0]
    post_payload = service.mcp_manager.session.post.call_args.kwargs["json"]

    assert "/api/projects/proj-123/workflow/transition" in post_url
    assert post_payload["idempotency_key"] == "bridge-trans-proj-123-task-123-in_progress-alex"
    assert result["project_id"] == "proj-123"
