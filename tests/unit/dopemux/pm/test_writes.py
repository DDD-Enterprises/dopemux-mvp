import pytest
from dopemux.pm.writes import (
    classify_pm_write,
    is_workflow_significant_payload,
    pm_update_work_item,
    pm_transition_work_item,
    pm_log_progress,
    PMWriteConfig,
    CanonicalReceipt
)
from dopemux.pm.models import PMTaskStatus

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
    def transition(
        self,
        *,
        project_id,
        workflow_id,
        transition_name,
        actor,
        idempotency_key,
        expected_version,
        reason,
    ):
        self.calls.append(
            (
                "transition",
                project_id,
                workflow_id,
                transition_name,
                actor,
                reason,
                expected_version,
                idempotency_key,
            )
        )
        return {
            "legality_result": "allowed",
            "transition_receipt": {"version_after": expected_version + 1},
            "resulting_state": {"version": expected_version + 1},
        }

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

def test_classify_pm_write_splits_metadata_and_workflow_fields():
    metadata_fields, workflow_fields = classify_pm_write(
        {
            "title": "new title",
            "status": PMTaskStatus.IN_PROGRESS.value,
            "priority": "high",
            "promote": True,
        }
    )

    assert metadata_fields == ["title", "priority"]
    assert workflow_fields == ["status", "promote"]

def test_classify_pm_write_fails_closed_for_unknown_state_like_fields():
    metadata_fields, workflow_fields = classify_pm_write(
        {
            "custom_state": "pending",
            "other_field": "value",
        }
    )

    assert metadata_fields == ["other_field"]
    assert workflow_fields == ["custom_state"]


def test_classify_pm_write_does_not_trip_on_substring_collisions():
    metadata_fields, workflow_fields = classify_pm_write(
        {
            "statement": "status report",
            "phase_notes": "operator notes",
        }
    )

    assert metadata_fields == ["statement", "phase_notes"]
    assert workflow_fields == []

def test_is_workflow_significant_payload_detects_status_like_fields():
    assert is_workflow_significant_payload({"status": PMTaskStatus.DONE.value}) is True
    assert is_workflow_significant_payload({"workflow_state": "blocked"}) is True
    assert is_workflow_significant_payload({"title": "hello"}) is False

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

def test_pm_update_work_item_rejects_unknown_state_like_fields():
    config = PMWriteConfig(
        leantime_client=MockLeantimeClient(),
        orchestrator_client=None,
        conport_client=None,
        memory_client=None,
    )
    with pytest.raises(ValueError) as exc:
        pm_update_work_item(config, "task-1", {"my_state": "done"}, "key-1")
    assert "my_state" in str(exc.value)

def test_pm_update_work_item_rejects_empty_payload():
    config = PMWriteConfig(
        leantime_client=MockLeantimeClient(),
        orchestrator_client=None,
        conport_client=None,
        memory_client=None,
    )
    with pytest.raises(ValueError) as exc:
        pm_update_work_item(config, "task-1", {}, "key-1")
    assert "No metadata fields provided" in str(exc.value)

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
    assert receipt.operation_type == "metadata_update"
    assert receipt.reflection_state == "succeeded"
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
    assert receipt.operation_type == "transition"
    assert receipt.reflection_state == "degraded"
    assert receipt.reconciliation_state == "PARTIAL"
    assert len(orch_client.calls) == 1
    assert orch_client.calls[0] == (
        "transition",
        "default",
        "task-1",
        "in_progress",
        "dopemux",
        "starting work",
        1,
        "key-2",
    )
    
    mirror = receipt.mirror_receipts[0]
    assert mirror.system == "leantime"
    assert not mirror.success
    assert "Leantime is down" in mirror.error

def test_pm_transition_work_item_successful_reflection():
    orch_client = MockOrchestratorClient()
    leantime_client = MockLeantimeClient()
    config = PMWriteConfig(
        leantime_client=leantime_client,
        orchestrator_client=orch_client,
        conport_client=None,
        memory_client=None,
    )

    receipt = pm_transition_work_item(
        config=config,
        task_id="task-1",
        new_status=PMTaskStatus.IN_PROGRESS,
        reason="starting work",
        idempotency_key="key-2",
        expected_version=3,
    )

    assert receipt.success
    assert receipt.reflection_state == "succeeded"
    assert receipt.reconciliation_state == "SYNCED"
    assert orch_client.calls[-1] == (
        "transition",
        "default",
        "task-1",
        "in_progress",
        "dopemux",
        "starting work",
        3,
        "key-2",
    )
    assert leantime_client.calls[-1] == ("update_status", "task-1", PMTaskStatus.IN_PROGRESS.value, "key-2")

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
    assert receipt.operation_type == "log_progress"
    assert receipt.reflection_state == "degraded"
    assert receipt.reconciliation_state == "PARTIAL"
    assert len(conport_client.calls) == 1
    
    mirror = receipt.mirror_receipts[0]
    assert mirror.system == "dope-memory"
    assert not mirror.success
    assert mirror.error == "Memory client missing"
