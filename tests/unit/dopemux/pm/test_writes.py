import pytest
from src.dopemux.pm.writes import (
    pm_update_work_item,
    pm_transition_work_item,
    pm_log_progress,
    PMWriteConfig,
    CanonicalReceipt
)
from src.dopemux.pm.models import PMTaskStatus

class MockLeantimeClient:
    def __init__(self):
        self.calls = []
    def update_task(self, task_id, updates, idempotency_key):
        self.calls.append(("update_task", task_id, updates, idempotency_key))
    def update_status(self, task_id, status, idempotency_key):
        self.calls.append(("update_status", task_id, status, idempotency_key))

class MockOrchestratorClient:
    def __init__(self):
        self.calls = []
    def transition(self, task_id, new_status, reason, expected_version, idempotency_key):
        self.calls.append(("transition", task_id, new_status, reason, expected_version, idempotency_key))

class MockConportClient:
    def __init__(self):
        self.calls = []
    def record_progress(self, task_id, progress_notes, is_decision, idempotency_key):
        self.calls.append(("record_progress", task_id, progress_notes, is_decision, idempotency_key))

class MockMemoryClient:
    def __init__(self):
        self.calls = []
    def append_chronicle(self, task_id, progress_notes, is_decision, idempotency_key):
        self.calls.append(("append_chronicle", task_id, progress_notes, is_decision, idempotency_key))

def test_pm_update_work_item_rejects_significant_fields():
    config = PMWriteConfig(
        leantime_client=MockLeantimeClient(),
        orchestrator_client=None,
        conport_client=None,
        memory_client=None
    )
    with pytest.raises(ValueError) as exc:
        pm_update_work_item(config, "task-1", {"status": PMTaskStatus.DONE.value}, "key-1")
    assert "status" in str(exc.value)

def test_pm_update_work_item_fail_closed_missing_client():
    config = PMWriteConfig(leantime_client=None, orchestrator_client=None, conport_client=None, memory_client=None)
    with pytest.raises(RuntimeError) as exc:
        pm_update_work_item(config, "task-1", {"title": "new title"}, "key-1")
    assert "Leantime client" in str(exc.value)

def test_pm_update_work_item_success():
    client = MockLeantimeClient()
    config = PMWriteConfig(leantime_client=client, orchestrator_client=None, conport_client=None, memory_client=None)
    receipt = pm_update_work_item(config, "task-1", {"title": "new title"}, "key-idem-1")

    assert receipt.success
    assert receipt.canonical_system == "leantime"
    assert receipt.canonical_id == "task-1"
    assert len(client.calls) == 1
    assert client.calls[0] == ("update_task", "task-1", {"title": "new title"}, "key-idem-1")

def test_pm_transition_work_item_fail_closed():
    config = PMWriteConfig(leantime_client=None, orchestrator_client=None, conport_client=None, memory_client=None)
    with pytest.raises(RuntimeError) as exc:
        pm_transition_work_item(
            config=config,
            task_id="task-1",
            new_status=PMTaskStatus.IN_PROGRESS,
            reason="starting",
            idempotency_key="key-2",
            expected_version=1
        )
    assert "Task Orchestrator client" in str(exc.value)

def test_pm_transition_work_item_partial_failure():
    class BrokenLeantimeClient:
        def update_status(self, task_id, status, idempotency_key):
            raise ConnectionError("Leantime is down")

    orch_client = MockOrchestratorClient()
    config = PMWriteConfig(
        leantime_client=BrokenLeantimeClient(),
        orchestrator_client=orch_client,
        conport_client=None,
        memory_client=None
    )

    receipt = pm_transition_work_item(
        config=config,
        task_id="task-1",
        new_status=PMTaskStatus.IN_PROGRESS,
        reason="starting work",
        idempotency_key="key-2",
        expected_version=1
    )

    # Canonical should succeed, mirror should fail
    assert receipt.success
    assert receipt.canonical_system == "task-orchestrator"
    assert receipt.reconciliation_state == "PARTIAL"
    assert len(orch_client.calls) == 1

    mirror = receipt.mirror_receipts[0]
    assert mirror.system == "leantime"
    assert not mirror.success
    assert "Leantime is down" in mirror.error

def test_pm_log_progress_fail_closed():
    config = PMWriteConfig(leantime_client=None, orchestrator_client=None, conport_client=None, memory_client=None)
    with pytest.raises(RuntimeError) as exc:
        pm_log_progress(config, "task-1", "progress", "key-idem-3")
    assert "ConPort client" in str(exc.value)

def test_pm_log_progress_success_with_missing_mirror():
    conport_client = MockConportClient()
    config = PMWriteConfig(
        leantime_client=None,
        orchestrator_client=None,
        conport_client=conport_client,
        memory_client=None
    )

    receipt = pm_log_progress(config, "task-1", "progress", "key-idem-3")

    assert receipt.success
    assert receipt.canonical_system == "conport"
    assert receipt.reconciliation_state == "PARTIAL"
    assert len(conport_client.calls) == 1

    mirror = receipt.mirror_receipts[0]
    assert mirror.system == "dope-memory"
    assert not mirror.success
    assert mirror.error == "Memory client missing"
