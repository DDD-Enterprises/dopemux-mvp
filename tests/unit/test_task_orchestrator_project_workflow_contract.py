from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import sys

import pytest

from dopemux.pm.models import PMTask, PMTaskStatus
from dopemux.pm.store import InMemoryPMTaskStore

SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

try:
    from app.api import project_workflow  # noqa: E402
    from task_orchestrator.models import TaskStatus  # noqa: E402
except (ImportError, ModuleNotFoundError) as exc:
    pytest.skip(f"task-orchestrator service deps not available: {exc}", allow_module_level=True)


@dataclass
class RuntimeTask:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    dependencies: list[str] = field(default_factory=list)
    assigned_agent: object = None


@dataclass
class RuntimeStub:
    tasks: dict[str, RuntimeTask]
    pm_store: InMemoryPMTaskStore


@pytest.fixture
def runtime_stub():
    store = InMemoryPMTaskStore()
    now = datetime.now(timezone.utc)
    ready_pm = PMTask(
        task_id="wf-ready",
        title="Ready task",
        description="Can start now",
        source="test",
        status=PMTaskStatus.TODO,
        created_at_utc=now,
        updated_at_utc=now,
    )
    blocked_pm = PMTask(
        task_id="wf-blocked",
        title="Blocked task",
        description="Waiting on dependency",
        source="test",
        status=PMTaskStatus.TODO,
        created_at_utc=now,
        updated_at_utc=now,
    )
    done_pm = PMTask(
        task_id="wf-done",
        title="Done task",
        description="Already finished",
        source="test",
        status=PMTaskStatus.DONE,
        created_at_utc=now,
        updated_at_utc=now,
    )
    store.create(ready_pm)
    store.create(blocked_pm)
    store.create(done_pm)

    return RuntimeStub(
        tasks={
            "wf-ready": RuntimeTask(id="wf-ready", title="Ready task", priority=5),
            "wf-blocked": RuntimeTask(
                id="wf-blocked",
                title="Blocked task",
                priority=3,
                dependencies=["wf-done", "wf-missing"],
            ),
            "wf-done": RuntimeTask(id="wf-done", title="Done task", status=TaskStatus.COMPLETED, priority=1),
        },
        pm_store=store,
    )


@pytest.mark.asyncio
async def test_get_project_workflow_queue_uses_runtime_state(monkeypatch, runtime_stub):
    monkeypatch.setattr(project_workflow, "_task_runtime", lambda request=None: runtime_stub)

    result = await project_workflow.get_project_workflow_queue("proj-123", request=None)

    assert result.project_id == "proj-123"
    assert result.legality_result == "allowed"
    assert result.queue_items[0]["id"] == "wf-ready"
    assert result.blockers == ["wf-blocked"]


@pytest.mark.asyncio
async def test_get_project_workflow_state_reports_allowed_transitions(monkeypatch, runtime_stub):
    monkeypatch.setattr(project_workflow, "_task_runtime", lambda request=None: runtime_stub)

    result = await project_workflow.get_project_workflow_state("proj-123", request=None)

    assert result.project_id == "proj-123"
    assert result.legality_result == "allowed"
    assert result.state["task_count"] == 3
    assert result.state["ready_count"] == 1
    assert "start" in result.allowed_transitions
    assert "block" in result.allowed_transitions
    assert "done" not in result.allowed_transitions


@pytest.mark.asyncio
async def test_transition_project_workflow_returns_real_receipt(monkeypatch, runtime_stub):
    monkeypatch.setattr(project_workflow, "_task_runtime", lambda request=None: runtime_stub)
    request = project_workflow.TransitionWorkflowRequest(
        workflow_id="wf-ready",
        transition="start",
        actor="tester",
        idempotency_key="idem-1",
        expected_version=1,
        reason="begin work",
    )

    result = await project_workflow.execute_transition_project_workflow("proj-123", request)

    assert result.project_id == "proj-123"
    assert result.workflow_id == "wf-ready"
    assert result.legality_result == "allowed"
    assert result.transition_receipt["canonical_backend"] == "task-orchestrator"
    assert result.transition_receipt["version_after"] == 2
    assert result.resulting_state == {"workflow_id": "wf-ready", "status": "IN_PROGRESS", "version": 2}
    assert runtime_stub.tasks["wf-ready"].status == TaskStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_transition_project_workflow_rejects_illegal_target(monkeypatch, runtime_stub):
    monkeypatch.setattr(project_workflow, "_task_runtime", lambda request=None: runtime_stub)
    request = project_workflow.TransitionWorkflowRequest(
        workflow_id="wf-done",
        transition="start",
        actor="tester",
        idempotency_key="idem-2",
        expected_version=1,
    )

    result = await project_workflow.execute_transition_project_workflow("proj-123", request)

    assert result.project_id == "proj-123"
    assert result.workflow_id == "wf-done"
    assert result.legality_result == "illegal"
    assert result.transition_receipt["status"] == "illegal"
    assert result.resulting_state["current_status"] == "DONE"
