import pytest
import sys
import os

sys.path.insert(0, os.path.abspath("services/task-orchestrator"))

from fastapi.testclient import TestClient
from app.main import app
from src.dopemux.pm.models import PMTaskStatus

client = TestClient(app)

class MockCoordinator:
    def __init__(self, mode="none"):
        if mode == "none":
            self.leantime_client = None
            self.workflow_service = None
            self.conport_client = None
            self.memory_client = None
        elif mode == "error":
            class BrokenOrchestrator:
                def transition(self, *args, **kwargs):
                    raise Exception("DB error")
            class BrokenConport:
                def record_progress(self, *args, **kwargs):
                    raise Exception("DB error")
            class BrokenLeantime:
                def update_task(self, *args, **kwargs):
                    raise Exception("DB error")
                def update_status(self, *args, **kwargs):
                    raise Exception("DB error")

            self.leantime_client = BrokenLeantime()
            self.workflow_service = BrokenOrchestrator()
            self.conport_client = BrokenConport()
            self.memory_client = None

def setup_app_state(mode):
    app.state.coordinator = MockCoordinator(mode=mode)

def test_pm_update_work_item_fail_closed_via_api():
    setup_app_state("none")
    response = client.post(
        "/api/pm/work-items/task-1/update",
        json={"idempotency_key": "key1", "updates": {"title": "test"}}
    )
    assert response.status_code == 500
    assert "Leantime client" in response.json()["detail"]

def test_pm_update_work_item_invalid_fields():
    setup_app_state("none")
    response = client.post(
        "/api/pm/work-items/task-1/update",
        json={"idempotency_key": "key1", "updates": {"status": "IN_PROGRESS"}}
    )
    assert response.status_code == 400
    assert "workflow-significant fields" in response.json()["detail"]

def test_pm_transition_work_item_fail_closed():
    setup_app_state("none")
    response = client.post(
        "/api/pm/work-items/task-1/transition",
        json={"idempotency_key": "key2", "new_status": "IN_PROGRESS", "reason": "starting", "expected_version": 1}
    )
    assert response.status_code == 500
    assert "Task Orchestrator client" in response.json()["detail"]

def test_pm_log_progress_fail_closed():
    setup_app_state("none")
    response = client.post(
        "/api/pm/work-items/task-1/progress",
        json={"idempotency_key": "key3", "progress_notes": "did work", "is_decision": False}
    )
    assert response.status_code == 500
    assert "ConPort client" in response.json()["detail"]

def test_pm_update_work_item_api_500():
    setup_app_state("error")
    response = client.post(
        "/api/pm/work-items/task-1/update",
        json={"idempotency_key": "key1", "updates": {"title": "test"}}
    )
    assert response.status_code == 500
    assert "Canonical write failed" in response.json()["detail"]

def test_pm_transition_work_item_api_500():
    setup_app_state("error")
    response = client.post(
        "/api/pm/work-items/task-1/transition",
        json={"idempotency_key": "key2", "new_status": "IN_PROGRESS", "reason": "starting", "expected_version": 1}
    )
    assert response.status_code == 500
    assert "Canonical write failed" in response.json()["detail"]

def test_pm_log_progress_api_500():
    setup_app_state("error")
    response = client.post(
        "/api/pm/work-items/task-1/progress",
        json={"idempotency_key": "key3", "progress_notes": "did work", "is_decision": False}
    )
    assert response.status_code == 500
    assert "Canonical write failed" in response.json()["detail"]

def test_pm_transition_work_item_api_400():
    setup_app_state("none")
    response = client.post(
        "/api/pm/work-items/task-1/transition",
        json={"idempotency_key": "key2", "new_status": "FAKE_STATUS", "reason": "starting", "expected_version": 1}
    )
    assert response.status_code in (400, 422)

def test_pm_update_work_item_invalid_task_id_type_api():
    setup_app_state("none")
    response = client.post(
        "/api/pm/work-items/123/update",
        json={"idempotency_key": "key1", "updates": {"title": "test"}}
    )
    assert response.status_code in (500, 422)
