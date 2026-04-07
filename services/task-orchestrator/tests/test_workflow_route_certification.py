import json
import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.main import app
from app.api import project_workflow
from app.services.workflow_service import WorkflowService


class MemoryBridgeClient:
    def __init__(self):
        self.rows = {}

    async def save_custom_data(self, **kwargs):
        json.dumps(kwargs)
        self.rows[(kwargs["category"], kwargs["key"])] = {
            "key": kwargs["key"],
            "value": dict(kwargs["value"]),
            "timestamp": kwargs["value"].get("updated_at"),
        }
        return True

    async def get_custom_data(self, **kwargs):
        category = kwargs["category"]
        key = kwargs.get("key")
        limit = kwargs.get("limit", 50)
        items = [
            row
            for (row_category, row_key), row in self.rows.items()
            if row_category == category and (key is None or row_key == key)
        ]
        return items[:limit]

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_workflow_route_family_live_certification():
    service = WorkflowService(workspace_id=Path("/tmp/workflow-route-cert"))
    service.store._client = MemoryBridgeClient()
    app.state.coordinator = SimpleNamespace(workflow_service=service)
    prior_service = project_workflow._workflow_service_instance
    project_workflow._workflow_service_instance = service

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            ideas_empty = await client.get("/api/workflow/ideas")
            assert ideas_empty.status_code == 200
            assert ideas_empty.json() == {"count": 0, "ideas": []}

            idea_create = await client.post(
                "/api/workflow/ideas",
                json={"title": "Idea A", "description": "Desc A", "tags": ["x"]},
            )
            assert idea_create.status_code == 201
            idea_id = idea_create.json()["idea_id"]

            ideas_after_create = await client.get("/api/workflow/ideas")
            assert ideas_after_create.status_code == 200
            assert ideas_after_create.json()["count"] == 1
            assert ideas_after_create.json()["ideas"][0]["id"] == idea_id

            idea_patch = await client.patch(
                f"/api/workflow/ideas/{idea_id}",
                json={"title": "Idea A2", "status": "under-review"},
            )
            assert idea_patch.status_code == 200
            assert idea_patch.json()["idea"]["title"] == "Idea A2"
            assert idea_patch.json()["status"] == "under-review"

            idea_missing = await client.patch(
                "/api/workflow/ideas/idea_missing",
                json={"title": "Nope"},
            )
            assert idea_missing.status_code == 404
            assert idea_missing.json()["detail"] == "idea not found: idea_missing"

            epics_empty = await client.get("/api/workflow/epics")
            assert epics_empty.status_code == 200
            assert epics_empty.json() == {"count": 0, "epics": []}

            epic_create = await client.post(
                "/api/workflow/epics",
                json={
                    "title": "Epic A",
                    "description": "Epic Desc",
                    "business_value": "Value",
                    "priority": "high",
                    "status": "planned",
                },
            )
            assert epic_create.status_code == 201
            epic_id = epic_create.json()["epic_id"]

            epics_after_create = await client.get("/api/workflow/epics")
            assert epics_after_create.status_code == 200
            assert epics_after_create.json()["count"] == 1
            assert epics_after_create.json()["epics"][0]["id"] == epic_id

            epic_patch = await client.patch(
                f"/api/workflow/epics/{epic_id}",
                json={"status": "ready", "priority": "critical"},
            )
            assert epic_patch.status_code == 200
            assert epic_patch.json()["status"] == "ready"
            assert epic_patch.json()["epic"]["priority"] == "critical"

            epic_missing = await client.patch(
                "/api/workflow/epics/epic_missing",
                json={"status": "ready"},
            )
            assert epic_missing.status_code == 404
            assert epic_missing.json()["detail"] == "epic not found: epic_missing"

            workflow_state = await client.get("/api/projects/123/workflow/state")
            assert workflow_state.status_code == 200
            assert workflow_state.json()["state"]["ideas"]["under-review"]["count"] == 1
            assert workflow_state.json()["state"]["epics"]["ready"]["count"] == 1

            workflow_queue = await client.get("/api/projects/123/workflow/queue")
            assert workflow_queue.status_code == 200
            assert workflow_queue.json()["queue_items"][0]["workflow_id"] == epic_id
            assert workflow_queue.json()["queue_items"][0]["priority"] == "critical"

            workflow_blockers = await client.get("/api/projects/123/workflow/blockers")
            assert workflow_blockers.status_code == 200
            assert workflow_blockers.json()["active_blockers"] == []

            workflow_missing_project = await client.get("/api/projects/unknown/workflow/state")
            assert workflow_missing_project.status_code == 404
            assert workflow_missing_project.json()["detail"] == "project not found"
    finally:
        project_workflow._workflow_service_instance = prior_service
        del app.state.coordinator
        await service.close()
