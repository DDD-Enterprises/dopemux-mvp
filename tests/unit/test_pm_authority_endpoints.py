from __future__ import annotations

import sys
from pathlib import Path

import pytest

import dopemux.pm.reads as pm_reads
from dopemux.pm.adapters.conport import ConPortAdapter
from dopemux.pm.adapters.dope_memory import DopeMemoryAdapter
from dopemux.pm.adapters.orchestrator import (
    SyncTaskOrchestratorAdapter,
    TaskOrchestratorAdapter,
)
from dopemux.pm.models import PMTaskStatus
from dopemux.pm.writes import (
    PMActionKind,
    PMWriteConfig,
    pm_log_decision,
    pm_log_progress,
    pm_transition_work_item,
    pm_update_work_item,
)


class RecordingLeantimeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, object | None]] = []

    def update_ticket(self, task_id: str, payload: dict[str, object]) -> None:
        self.calls.append(("update_ticket", task_id, payload))


class RecordingOrchestratorClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def transition(
        self,
        *,
        project_id: str,
        workflow_id: str,
        transition_name: str,
        actor: str,
        idempotency_key: str,
        expected_version: int,
        reason: str,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "project_id": project_id,
                "workflow_id": workflow_id,
                "transition_name": transition_name,
                "actor": actor,
                "idempotency_key": idempotency_key,
                "expected_version": expected_version,
                "reason": reason,
            }
        )
        return {"status": "success"}


class RecordingConPortClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, bool, str]] = []

    def record_progress(
        self,
        task_id: str,
        progress_notes: str,
        is_decision: bool,
        idempotency_key: str,
    ) -> None:
        self.calls.append(
            ("record_progress", task_id, progress_notes, is_decision, idempotency_key)
        )


class RecordingMemoryClient:
    def __init__(self, result: dict[str, object] | None = None) -> None:
        self.calls: list[tuple[str, str, str, bool, str]] = []
        self.result = result or {"entry_id": "receipt-1"}

    def append_chronicle(
        self,
        task_id: str,
        progress_notes: str,
        is_decision: bool,
        idempotency_key: str,
    ) -> dict[str, object]:
        self.calls.append(
            ("append_chronicle", task_id, progress_notes, is_decision, idempotency_key)
        )
        return self.result


def test_pm_endpoint_defaults_match_declared_authority_ports(monkeypatch):
    monkeypatch.delenv("TASK_ORCHESTRATOR_URL", raising=False)
    monkeypatch.delenv("CONPORT_URL", raising=False)
    monkeypatch.delenv("CONPORT_CONTEXT_URL", raising=False)
    monkeypatch.delenv("DOPE_MEMORY_URL", raising=False)
    monkeypatch.delenv("LEANTIME_API_URL", raising=False)
    monkeypatch.delenv("LEANTIME_URL", raising=False)
    monkeypatch.setenv("LEANTIME_API_TOKEN", "test-token")

    async_orchestrator = TaskOrchestratorAdapter()
    sync_orchestrator = SyncTaskOrchestratorAdapter()
    try:
        assert async_orchestrator.base_url == "http://localhost:8000"
        assert sync_orchestrator.base_url == "http://localhost:8000"
    finally:
        sync_orchestrator.close()

    assert ConPortAdapter().base_url == "http://localhost:3004"
    assert pm_reads._conport_context_client().base_url == "http://localhost:3005"
    assert DopeMemoryAdapter().base_url == "http://localhost:3020"

    leantime_client = pm_reads._leantime_client()
    assert leantime_client.base_url == "http://localhost:8080"
    assert leantime_client.endpoint == "http://localhost:8080/api/jsonrpc"


def test_task_orchestrator_sync_transition_uses_project_workflow_endpoint(monkeypatch):
    captured: dict[str, object] = {}

    def fake_request(method: str, path: str, **kwargs):
        captured["method"] = method
        captured["path"] = path
        captured["json"] = kwargs["json"]

        class Response:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict[str, object]:
                return {"status": "ok"}

        return Response()

    adapter = SyncTaskOrchestratorAdapter(base_url="http://localhost:8000")
    try:
        monkeypatch.setattr(adapter, "_request", fake_request)
        adapter.transition(
            project_id="proj-1",
            workflow_id="wf-1",
            transition_name="start",
            actor="dopemux",
            idempotency_key="idem-1",
            expected_version=3,
            reason="begin work",
        )
    finally:
        adapter.close()

    assert captured == {
        "method": "POST",
        "path": "/api/projects/proj-1/workflow/transition",
        "json": {
            "workflow_id": "wf-1",
            "transition": "start",
            "actor": "dopemux",
            "idempotency_key": "idem-1",
            "expected_version": 3,
            "reason": "begin work",
        },
    }


def test_pm_tools_router_and_project_workflow_runtime_routes_are_explicit():
    service_root = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))

    try:
        from app.main import app
        from app.api.pm_tools import router as pm_tools_router
    except (ImportError, ModuleNotFoundError) as exc:
        pytest.skip(f"task-orchestrator service deps not available: {exc}")

    app_routes = {
        (route.path, tuple(sorted(getattr(route, "methods", []) or [])))
        for route in app.routes
    }
    pm_tool_routes = {
        (route.path, tuple(sorted(getattr(route, "methods", []) or [])))
        for route in pm_tools_router.routes
    }

    assert ("/api/pm/work-items/{task_id}/update", ("POST",)) in pm_tool_routes
    assert ("/api/pm/work-items/{task_id}/transition", ("POST",)) in pm_tool_routes
    assert ("/api/pm/work-items/{task_id}/progress", ("POST",)) in pm_tool_routes
    assert ("/api/projects/{project_id}/workflow/transition", ("POST",)) in app_routes


def test_metadata_write_is_canonical_leantime_only():
    leantime = RecordingLeantimeClient()
    orchestrator = RecordingOrchestratorClient()
    conport = RecordingConPortClient()
    memory = RecordingMemoryClient()
    config = PMWriteConfig(
        leantime_client=leantime,
        orchestrator_client=orchestrator,
        conport_client=conport,
        memory_client=memory,
        project_id="proj-1",
    )

    receipt = pm_update_work_item(
        config=config,
        task_id="task-1",
        updates={"title": "Updated", "notes": "Operator note"},
        idempotency_key="idem-meta",
    )

    assert receipt.canonical_system == "leantime"
    assert receipt.operation_type == PMActionKind.METADATA_UPDATE.value
    assert receipt.mirror_receipts == []
    assert leantime.calls == [
        (
            "update_ticket",
            "task-1",
            {
                "ticketId": "task-1",
                "headline": "Updated",
                "description": "Operator note",
            },
        )
    ]
    assert orchestrator.calls == []
    assert conport.calls == []
    assert memory.calls == []


def test_workflow_transition_is_canonical_task_orchestrator_not_leantime():
    leantime = RecordingLeantimeClient()
    orchestrator = RecordingOrchestratorClient()
    config = PMWriteConfig(
        leantime_client=leantime,
        orchestrator_client=orchestrator,
        conport_client=RecordingConPortClient(),
        memory_client=RecordingMemoryClient(),
        project_id="proj-1",
    )

    receipt = pm_transition_work_item(
        config=config,
        task_id="wf-1",
        new_status=PMTaskStatus.IN_PROGRESS,
        reason="start work",
        idempotency_key="idem-transition",
        expected_version=7,
    )

    assert receipt.canonical_system == "task-orchestrator"
    assert receipt.operation_type == PMActionKind.WORKFLOW_TRANSITION.value
    assert receipt.version == 8
    assert receipt.mirror_receipts == []
    assert orchestrator.calls == [
        {
            "project_id": "proj-1",
            "workflow_id": "wf-1",
            "transition_name": "start",
            "actor": "dopemux",
            "idempotency_key": "idem-transition",
            "expected_version": 7,
            "reason": "start work",
        }
    ]
    assert leantime.calls == []


def test_progress_write_is_canonical_conport_with_dope_memory_mirror_receipt():
    conport = RecordingConPortClient()
    memory = RecordingMemoryClient({"entry_id": "chronicle-9"})
    config = PMWriteConfig(
        leantime_client=RecordingLeantimeClient(),
        orchestrator_client=RecordingOrchestratorClient(),
        conport_client=conport,
        memory_client=memory,
    )

    receipt = pm_log_progress(
        config=config,
        task_id="task-1",
        progress_notes="Reached validation",
        idempotency_key="idem-progress",
    )

    assert receipt.canonical_system == "conport"
    assert receipt.operation_type == PMActionKind.PROGRESS_LOG.value
    assert receipt.reconciliation_state == "SYNCED"
    assert conport.calls == [
        ("record_progress", "task-1", "Reached validation", False, "idem-progress")
    ]
    assert receipt.mirror_receipts[0].system == "dope-memory"
    assert receipt.mirror_receipts[0].success is True
    assert receipt.mirror_receipts[0].persisted_id == "chronicle-9"
    assert memory.calls == [
        ("append_chronicle", "task-1", "Reached validation", False, "idem-progress")
    ]


def test_decision_write_is_canonical_conport_and_memory_is_not_pm_state():
    conport = RecordingConPortClient()
    config = PMWriteConfig(
        leantime_client=None,
        orchestrator_client=None,
        conport_client=conport,
        memory_client=RecordingMemoryClient(),
    )

    receipt = pm_log_decision(
        config=config,
        task_id="task-1",
        decision_notes="Keep PM authority split by concern",
        idempotency_key="idem-decision",
    )

    assert receipt.canonical_system == "conport"
    assert receipt.operation_type == PMActionKind.DECISION_LOG.value
    assert receipt.mirror_receipts[0].system == "dope-memory"
    assert receipt.mirror_receipts[0].system != receipt.canonical_system
    assert conport.calls == [
        (
            "record_progress",
            "task-1",
            "Keep PM authority split by concern",
            True,
            "idem-decision",
        )
    ]


def test_missing_dope_memory_mirror_does_not_promote_memory_to_canonical_state():
    conport = RecordingConPortClient()
    config = PMWriteConfig(
        leantime_client=None,
        orchestrator_client=None,
        conport_client=conport,
        memory_client=None,
    )

    receipt = pm_log_progress(
        config=config,
        task_id="task-1",
        progress_notes="Mirror unavailable",
        idempotency_key="idem-missing-memory",
    )

    assert receipt.canonical_system == "conport"
    assert receipt.reconciliation_state == "PARTIAL"
    assert receipt.mirror_receipts[0].system == "dope-memory"
    assert receipt.mirror_receipts[0].success is False
    assert receipt.mirror_receipts[0].error == "Memory client missing"
