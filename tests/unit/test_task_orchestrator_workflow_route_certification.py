import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
SERVICE_ROOT_STR = str(SERVICE_ROOT)
if SERVICE_ROOT_STR in sys.path:
    sys.path.remove(SERVICE_ROOT_STR)
sys.path.insert(0, SERVICE_ROOT_STR)

# Prevent cross-test module collisions from other services that also expose
# a top-level `app.py` module on sys.path.
for _module_name in list(sys.modules):
    if _module_name == "app" or _module_name.startswith("app."):
        sys.modules.pop(_module_name, None)

# Register a FastMCP stub that accepts the production decorator shape
# `tool(name=..., description=...)` before `app.main` is imported. The
# production registration in app/main.py calls the decorator with keyword
# arguments; a positional-only stub would raise TypeError during import.
if "mcp.server.fastmcp" not in sys.modules:
    class _FastMCPStub:
        def __init__(self, *args, **kwargs):
            self.tools = {}

        def tool(self, *, name=None, description=None):
            def decorator(func):
                self.tools[name or func.__name__] = {
                    "description": description,
                    "handler": func,
                }
                return func

            return decorator

    fastmcp_module = types.ModuleType("mcp.server.fastmcp")
    fastmcp_module.FastMCP = _FastMCPStub
    mcp_module = types.ModuleType("mcp")
    mcp_server_module = types.ModuleType("mcp.server")
    mcp_server_models_module = types.ModuleType("mcp.server.models")
    mcp_server_models_module.InitializationOptions = object
    mcp_server_stdio_module = types.ModuleType("mcp.server.stdio")
    mcp_server_stdio_module.stdio_server = object

    sys.modules["mcp"] = mcp_module
    sys.modules["mcp.server"] = mcp_server_module
    sys.modules["mcp.server.fastmcp"] = fastmcp_module
    sys.modules["mcp.server.models"] = mcp_server_models_module
    sys.modules["mcp.server.stdio"] = mcp_server_stdio_module

from app.main import app  # noqa: E402
from app.api import project_workflow  # noqa: E402
from app.models.workflow import CreateEpicRequest  # noqa: E402
from app.services.workflow_service import WorkflowConflictError, WorkflowService  # noqa: E402


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

    async def claim_custom_data(self, **kwargs):
        key = (kwargs["category"], kwargs["key"])
        value = dict(kwargs["value"])
        fingerprint = value.get("_fingerprint_v1", "")

        if key in self.rows:
            existing = self.rows[key]
            existing_fp = existing.get("value", {}).get("_fingerprint_v1")
            if existing_fp is None:
                return {
                    "result": "LEGACY_UNFINGERPRINTED",
                    "value": existing["value"],
                }
            if existing_fp == fingerprint:
                return {
                    "result": "MATCHED",
                    "value": existing["value"],
                }
            return {
                "result": "CONFLICT",
                "value": existing["value"],
            }

        self.rows[key] = {
            "key": kwargs["key"],
            "value": value,
            "timestamp": value.get("updated_at"),
        }
        return {"result": "CREATED", "value": value}

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
async def test_create_epic_replays_same_idempotency_key_without_duplicate():
    service = WorkflowService(workspace_id="/tmp/workflow-idempotency")
    service.store._client = MemoryBridgeClient()
    request = CreateEpicRequest(
        title="Synthetic epic",
        description="Synthetic persistence test",
        business_value="Validate replay",
        tags=["synthetic"],
        idempotency_key="synthetic-repeat-key",
    )

    try:
        first = await service.create_epic(request)
        second = await service.create_epic(request)
        stored = await service.list_epics(tag="synthetic")

        assert second.id == first.id
        assert first.idempotency_key == "synthetic-repeat-key"
        assert [epic.id for epic in stored] == [first.id]
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_create_epic_rejects_conflicting_idempotency_key_payload():
    service = WorkflowService(workspace_id="/tmp/workflow-idempotency")
    service.store._client = MemoryBridgeClient()
    original = CreateEpicRequest(
        title="Original synthetic epic",
        description="Synthetic persistence test",
        business_value="Validate replay",
        idempotency_key="synthetic-conflict-key",
    )
    conflicting = CreateEpicRequest(
        title="Different synthetic epic",
        description="Synthetic persistence test",
        business_value="Validate replay",
        idempotency_key="synthetic-conflict-key",
    )

    try:
        created = await service.create_epic(original)
        with pytest.raises(WorkflowConflictError):
            await service.create_epic(conflicting)
        stored = await service.list_epics()

        assert [epic.id for epic in stored] == [created.id]
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_reordered_lists_replay_returns_conflict_and_winner_unchanged():
    """Reordered immutable lists are distinct requests: replay conflicts.

    A replayed create that merely reorders acceptance criteria or tags is a
    different immutable request and must conflict, leaving the first
    persisted value untouched.
    """
    service = WorkflowService(workspace_id="/tmp/workflow-reordered-conflict")
    service.store._client = MemoryBridgeClient()
    original = CreateEpicRequest(
        title="Ordered epic",
        description="Synthetic persistence test",
        business_value="Validate replay",
        acceptance_criteria=["alpha", "beta", "gamma"],
        tags=["one", "two"],
        idempotency_key="synthetic-reordered-key",
    )
    reordered_criteria = CreateEpicRequest(
        title="Ordered epic",
        description="Synthetic persistence test",
        business_value="Validate replay",
        acceptance_criteria=["gamma", "beta", "alpha"],
        tags=["one", "two"],
        idempotency_key="synthetic-reordered-key",
    )
    reordered_tags = CreateEpicRequest(
        title="Ordered epic",
        description="Synthetic persistence test",
        business_value="Validate replay",
        acceptance_criteria=["alpha", "beta", "gamma"],
        tags=["two", "one"],
        idempotency_key="synthetic-reordered-key",
    )

    try:
        created = await service.create_epic(original)
        with pytest.raises(WorkflowConflictError):
            await service.create_epic(reordered_criteria)
        with pytest.raises(WorkflowConflictError):
            await service.create_epic(reordered_tags)
        stored = await service.list_epics()

        assert [epic.id for epic in stored] == [created.id]
        assert stored[0].acceptance_criteria == ["alpha", "beta", "gamma"]
        assert stored[0].tags == ["one", "two"]
    finally:
        await service.close()


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
