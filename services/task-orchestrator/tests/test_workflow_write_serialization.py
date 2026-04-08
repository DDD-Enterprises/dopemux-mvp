import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest


_UNSET: Any = object()  # sentinel for detecting absent attributes


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app
from app.services.workflow_service import WorkflowService
from app.services.workflow_store import WorkflowStore


class RecordingBridgeClient:
    def __init__(self):
        self.calls = []

    async def save_custom_data(self, **kwargs):
        self.calls.append(kwargs)
        json.dumps(kwargs)
        return True

    async def get_custom_data(self, **kwargs):
        return []

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_workflow_store_normalizes_path_workspace_id_before_custom_data_upsert():
    store = WorkflowStore(workspace_id=Path("/tmp/workflow-store"))
    probe = RecordingBridgeClient()
    store._client = probe

    saved = await store.save_idea({"id": "idea_demo", "title": "Idea", "description": "Desc"})

    assert saved is True
    assert len(probe.calls) == 1
    outbound = probe.calls[0]
    assert outbound["workspace_id"] == "/tmp/workflow-store"
    assert isinstance(outbound["workspace_id"], str)

    await store.close()


@pytest.mark.asyncio
async def test_post_workflow_ideas_succeeds_when_service_workspace_id_is_path():
    service = WorkflowService(workspace_id=Path("/tmp/workflow-route"))
    probe = RecordingBridgeClient()
    service.store._client = probe

    prior_coordinator = getattr(app.state, "coordinator", _UNSET)
    app.state.coordinator = SimpleNamespace(workflow_service=service)

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/workflow/ideas",
                json={"title": "Idea", "description": "Desc"},
            )

        body = response.json()
        assert response.status_code == 201
        assert body["status"] == "new"
        assert body["idea"]["title"] == "Idea"
        assert len(probe.calls) == 1
        assert probe.calls[0]["workspace_id"] == "/tmp/workflow-route"
    finally:
        if prior_coordinator is _UNSET:
            try:
                del app.state.coordinator
            except AttributeError:
                pass
        else:
            app.state.coordinator = prior_coordinator
        await service.close()
