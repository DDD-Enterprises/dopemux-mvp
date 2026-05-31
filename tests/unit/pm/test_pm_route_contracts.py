from __future__ import annotations

import sys
from pathlib import Path

import pytest

from dopemux.pm.adapters.orchestrator import SyncTaskOrchestratorAdapter, TaskOrchestratorAdapter

SERVICE_ROOT = Path(__file__).resolve().parents[3] / "services" / "task-orchestrator"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

try:
    from app.main import app  # noqa: E402
except (ImportError, ModuleNotFoundError) as exc:
    pytest.skip(f"task-orchestrator service deps not available: {exc}", allow_module_level=True)


def test_task_orchestrator_runtime_includes_project_workflow_router():
    paths = {
        (route.path, tuple(sorted(getattr(route, "methods", []) or [])))
        for route in app.routes
    }

    assert ("/api/projects/{project_id}/workflow/transition", ("POST",)) in paths
    assert ("/api/pm/work-items/{task_id}/transition", ("POST",)) not in paths


def test_async_task_orchestrator_adapter_defaults_to_active_runtime_port():
    adapter = TaskOrchestratorAdapter()
    assert adapter.base_url == "http://localhost:8000"


def test_sync_task_orchestrator_adapter_uses_project_scoped_transition_path(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("HOME", str(tmp_path))
    captured = {}

    def fake_request(method, path, **kwargs):
        captured["method"] = method
        captured["path"] = path
        captured["json"] = kwargs["json"]

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return {"status": "ok"}

        return Response()

    adapter = SyncTaskOrchestratorAdapter(base_url="http://localhost:8000")
    monkeypatch.setattr(adapter, "_request", fake_request)

    adapter.transition(
        project_id="proj-123",
        workflow_id="wf-1",
        transition_name="start",
        actor="tester",
        idempotency_key="idem-1",
        expected_version=4,
        reason="begin work",
    )

    assert captured == {
        "method": "POST",
        "path": "/api/projects/proj-123/workflow/transition",
        "json": {
            "workflow_id": "wf-1",
            "transition": "start",
            "actor": "tester",
            "idempotency_key": "idem-1",
            "expected_version": 4,
            "reason": "begin work",
        },
    }
