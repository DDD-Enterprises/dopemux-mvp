from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
MODULE_PATH = SERVICE_ROOT / "app" / "main.py"


class _Entity:
    def __init__(self, **data):
        self._data = dict(data)
        for key, value in self._data.items():
            setattr(self, key, value)

    def dict(self):
        return dict(self._data)


def _idea() -> _Entity:
    return _Entity(
        id="idea_123",
        title="Improve workflow API",
        description="Capture ADR-197 runtime parity",
        source="brainstorm",
        creator="tester",
        tags=["roadmap"],
        status="new",
        created_at="2026-02-08T00:00:00+00:00",
        updated_at="2026-02-08T00:00:00+00:00",
        promoted_to_epic_id=None,
    )


def _epic() -> _Entity:
    return _Entity(
        id="epic_456",
        title="Workflow Epic",
        description="Promoted idea",
        business_value="Higher planning throughput",
        acceptance_criteria=["has tests", "has docs"],
        priority="high",
        status="planned",
        created_from_idea_id="idea_123",
        leantime_project_id=None,
        tags=["roadmap"],
        adhd_metadata={
            "estimated_complexity": 0.4,
            "required_energy_level": "medium",
            "can_work_parallel": True,
        },
        created_at="2026-02-08T00:00:10+00:00",
        updated_at="2026-02-08T00:00:10+00:00",
    )


def _load_task_orchestrator_module():
    service_root_str = str(SERVICE_ROOT)
    if service_root_str in sys.path:
        sys.path.remove(service_root_str)
    sys.path.insert(0, service_root_str)

    # Prevent cross-test collisions with other services exposing top-level app.py.
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            sys.modules.pop(module_name, None)

    module_name = f"task_orchestrator_main_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_workflow_service():
    return SimpleNamespace(
        create_idea=AsyncMock(return_value=_idea()),
        list_ideas=AsyncMock(return_value=[_idea()]),
        update_idea=AsyncMock(return_value=_idea()),
        promote_idea=AsyncMock(
            return_value={
                "idea": _Entity(**{**_idea().dict(), "status": "promoted", "promoted_to_epic_id": "epic_456"}),
                "epic": _epic(),
                "already_promoted": False,
                "warning": None,
            }
        ),
        create_epic=AsyncMock(return_value=_epic()),
        list_epics=AsyncMock(return_value=[_epic()]),
        update_epic=AsyncMock(return_value=_epic()),
    )


def _build_client(module, workflow_service):
    class _Coordinator:
        def __init__(self, service):
            self.workflow_service = service

        async def shutdown(self):
            return None

    async def _create_plane_coordinator(_workspace_id: str):
        return _Coordinator(workflow_service)

    module.create_plane_coordinator = _create_plane_coordinator
    return TestClient(module.app)


def test_create_workflow_idea_contract():
    module = _load_task_orchestrator_module()
    workflow_service = _build_workflow_service()

    with _build_client(module, workflow_service) as client:
        response = client.post(
            "/api/workflow/ideas",
            json={
                "title": "New idea",
                "description": "Keep API additive",
                "source": "brainstorm",
                "creator": "hue",
                "tags": ["docs", "api"],
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["idea_id"] == "idea_123"
    assert payload["status"] == "new"
    assert "idea" in payload
    assert payload["idea"]["title"] == "Improve workflow API"
    assert workflow_service.create_idea.await_count == 1
    request = workflow_service.create_idea.await_args.args[0]
    assert request.title == "New idea"
    assert request.tags == ["docs", "api"]


def test_list_workflow_ideas_passes_filters():
    module = _load_task_orchestrator_module()
    workflow_service = _build_workflow_service()

    with _build_client(module, workflow_service) as client:
        response = client.get(
            "/api/workflow/ideas",
            params={"status": "new", "tag": "roadmap", "limit": 9},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["ideas"][0]["id"] == "idea_123"
    assert workflow_service.list_ideas.await_args.kwargs == {
        "status": "new",
        "tag": "roadmap",
        "limit": 9,
    }


def test_promote_workflow_idea_contract():
    module = _load_task_orchestrator_module()
    workflow_service = _build_workflow_service()

    with _build_client(module, workflow_service) as client:
        response = client.post("/api/workflow/ideas/idea_123/promote", json={})

    assert response.status_code == 201
    payload = response.json()
    assert payload["idea_id"] == "idea_123"
    assert payload["epic_id"] == "epic_456"
    assert payload["already_promoted"] is False
    assert "warning" in payload
    assert workflow_service.promote_idea.await_count == 1
    assert workflow_service.promote_idea.await_args.args[0] == "idea_123"
    request = workflow_service.promote_idea.await_args.args[1]
    assert request.sync_to_leantime is True


def test_create_workflow_epic_contract():
    module = _load_task_orchestrator_module()
    workflow_service = _build_workflow_service()

    with _build_client(module, workflow_service) as client:
        response = client.post(
            "/api/workflow/epics",
            json={
                "title": "Epic",
                "description": "Description",
                "business_value": "Value",
                "priority": "high",
            },
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["epic_id"] == "epic_456"
    assert payload["status"] == "planned"
    assert "epic" in payload


def test_workflow_not_found_maps_to_404():
    module = _load_task_orchestrator_module()
    workflow_service = _build_workflow_service()
    workflow_service.update_idea.side_effect = module.WorkflowNotFoundError("idea not found")

    with _build_client(module, workflow_service) as client:
        response = client.patch(
            "/api/workflow/ideas/idea_missing",
            json={"status": "under-review"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "idea not found"


def test_workflow_conflict_maps_to_409():
    module = _load_task_orchestrator_module()
    workflow_service = _build_workflow_service()
    workflow_service.update_epic.side_effect = module.WorkflowConflictError("invalid transition")

    with _build_client(module, workflow_service) as client:
        response = client.patch(
            "/api/workflow/epics/epic_456",
            json={"status": "planned"},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "invalid transition"


def test_workflow_unavailable_maps_to_503():
    module = _load_task_orchestrator_module()
    workflow_service = _build_workflow_service()
    workflow_service.list_epics.side_effect = module.WorkflowUnavailableError("bridge down")

    with _build_client(module, workflow_service) as client:
        response = client.get("/api/workflow/epics")

    assert response.status_code == 503
    assert response.json()["detail"] == "bridge down"


def test_workflow_value_error_maps_to_400():
    module = _load_task_orchestrator_module()
    workflow_service = _build_workflow_service()
    workflow_service.list_ideas.side_effect = ValueError("bad filter")

    with _build_client(module, workflow_service) as client:
        response = client.get("/api/workflow/ideas")

    assert response.status_code == 400
    assert response.json()["detail"] == "bad filter"
