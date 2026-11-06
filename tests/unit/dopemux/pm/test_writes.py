import pytest

from src.dopemux.pm.writes import (
    PMActionKind,
    PMWriteConfig,
    classify_pm_action,
    classify_pm_write,
    is_workflow_significant_payload,
    pm_log_decision,
    pm_log_progress,
    pm_transition_command,
    pm_transition_work_item,
    pm_update_work_item,
)
from src.dopemux.pm.models import PMTaskStatus


class MockLeantimeClient:
    def __init__(self):
        self.calls = []

    def update_ticket(self, task_id, payload):
        self.calls.append(("update_ticket", task_id, payload))


class MockLegacyLeantimeClient:
    def __init__(self):
        self.calls = []

    def update_task(self, task_id, updates, idempotency_key):
        self.calls.append(("update_task", task_id, updates, idempotency_key))


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
        return {"status": "success"}


class MockConportClient:
    def __init__(self):
        self.calls = []

    def record_progress(self, task_id, progress_notes, is_decision, idempotency_key):
        self.calls.append(("record_progress", task_id, progress_notes, is_decision, idempotency_key))


class MockMemoryClient:
    def __init__(self, *, result=None):
        self.calls = []
        self.result = result or {"entry_id": "chron-1", "success": True}

    def append_chronicle(self, task_id, progress_notes, is_decision, idempotency_key):
        self.calls.append(("append_chronicle", task_id, progress_notes, is_decision, idempotency_key))
        return self.result


def test_classify_pm_write_splits_metadata_and_workflow_fields():
    metadata_fields, workflow_fields = classify_pm_write(
        {
            "title": "new title",
            "status": PMTaskStatus.IN_PROGRESS.value,
            "notes": "operator note",
            "promote": True,
        }
    )

    assert metadata_fields == ["title", "notes"]
    assert workflow_fields == ["status", "promote"]


def test_classify_pm_write_fails_closed_for_unknown_state_like_fields():
    metadata_fields, workflow_fields = classify_pm_write(
        {
            "custom_state": "pending",
            "notes": "value",
        }
    )

    assert metadata_fields == ["notes"]
    assert workflow_fields == ["custom_state"]


def test_classify_pm_write_does_not_trip_on_substring_collisions():
    metadata_fields, workflow_fields = classify_pm_write(
        {
            "statement": "status report",
            "notes": "operator notes",
        }
    )

    assert metadata_fields == ["statement", "notes"]
    assert workflow_fields == []


def test_is_workflow_significant_payload_detects_status_like_fields():
    assert is_workflow_significant_payload({"status": PMTaskStatus.DONE.value}) is True
    assert is_workflow_significant_payload({"workflow_state": "blocked"}) is True
    assert is_workflow_significant_payload({"title": "hello"}) is False


def test_classify_pm_action_routes_metadata_to_leantime():
    assert classify_pm_action({"title": "Updated title"}) == PMActionKind.METADATA_UPDATE


def test_classify_pm_action_rejects_unproven_metadata_fields():
    with pytest.raises(ValueError) as exc:
        classify_pm_action({"tags": ["blocked", "ops"]})

    assert "Unsupported metadata fields" in str(exc.value)


def test_pm_update_work_item_rejects_significant_fields():
    config = PMWriteConfig(
        leantime_client=MockLeantimeClient(),
        orchestrator_client=None,
        conport_client=None,
        memory_client=None,
    )
    with pytest.raises(ValueError) as exc:
        pm_update_work_item(config, "task-1", {"status": PMTaskStatus.DONE.value}, "key-1")
    assert "status" in str(exc.value)


def test_pm_update_work_item_rejects_unproven_metadata_fields():
    config = PMWriteConfig(
        leantime_client=MockLeantimeClient(),
        orchestrator_client=None,
        conport_client=None,
        memory_client=None,
    )
    with pytest.raises(ValueError) as exc:
        pm_update_work_item(config, "task-1", {"tags": ["x"]}, "key-1")
    assert "Unsupported metadata fields" in str(exc.value)


def test_pm_update_work_item_fail_closed_missing_client():
    config = PMWriteConfig(leantime_client=None, orchestrator_client=None, conport_client=None, memory_client=None)
    with pytest.raises(RuntimeError) as exc:
        pm_update_work_item(config, "task-1", {"title": "new title"}, "key-1")
    assert "Leantime client" in str(exc.value)


def test_pm_update_work_item_success_uses_update_ticket_payload():
    client = MockLeantimeClient()
    config = PMWriteConfig(leantime_client=client, orchestrator_client=None, conport_client=None, memory_client=None)
    receipt = pm_update_work_item(
        config,
        "task-1",
        {"title": "new title", "notes": "operator note"},
        "key-idem-1",
    )

    assert receipt.success
    assert receipt.canonical_system == "leantime"
    assert receipt.operation_type == PMActionKind.METADATA_UPDATE.value
    assert client.calls == [
        (
            "update_ticket",
            "task-1",
            {"ticketId": "task-1", "headline": "new title", "description": "operator note"},
        )
    ]


def test_pm_update_work_item_supports_legacy_update_task_client():
    client = MockLegacyLeantimeClient()
    config = PMWriteConfig(leantime_client=client, orchestrator_client=None, conport_client=None, memory_client=None)

    pm_update_work_item(config, "task-1", {"title": "new title"}, "key-idem-1")

    assert client.calls == [
        (
            "update_task",
            "task-1",
            {"ticketId": "task-1", "headline": "new title"},
            "key-idem-1",
        )
    ]


@pytest.mark.parametrize("new_status", list(PMTaskStatus))
@pytest.mark.parametrize("clients_present", [False, True])
def test_pm_transition_work_item_requires_v2_without_effects(
    new_status, clients_present, monkeypatch
):
    """V1 cannot supply authenticated binding/admission/completion evidence."""
    import src.dopemux.pm.writes as writes_module

    emitted = []
    monkeypatch.setattr(
        writes_module,
        "try_emit_promotable_capture_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    clients = [MockLeantimeClient(), MockOrchestratorClient(),
               MockConportClient(), MockMemoryClient()]
    config = PMWriteConfig(
        leantime_client=clients[0] if clients_present else None,
        orchestrator_client=clients[1] if clients_present else None,
        conport_client=clients[2] if clients_present else None,
        memory_client=clients[3] if clients_present else None,
        project_id="proj-7",
    )

    with pytest.raises(RuntimeError, match="authenticated v2 transition_command"):
        pm_transition_work_item(
            config=config,
            task_id="task-1",
            new_status=new_status,
            reason="legacy request cannot prove admission",
            idempotency_key="key-2",
            expected_version=1,
        )

    assert all(client.calls == [] for client in clients)
    assert emitted == []


@pytest.mark.parametrize("client", [None, MockOrchestratorClient()])
def test_pm_transition_command_rejects_unauthenticated_legacy_client(client):
    config = PMWriteConfig(
        leantime_client=None, orchestrator_client=client,
        conport_client=None, memory_client=None, project_id="proj-7",
    )
    with pytest.raises(RuntimeError, match="Explicit authenticated v2 adapter required"):
        pm_transition_command(config, {})
    if client is not None:
        assert client.calls == []


def test_pm_transition_command_project_mismatch_has_no_transport_effects():
    import httpx
    from src.dopemux.pm.adapters.ownership import SyncOwnershipAdapter

    requests = []
    credentials = []
    adapter = SyncOwnershipAdapter(
        project_id="proj-7", writer_instance_id="writer-7",
        endpoint="https://fixture", principal_id="alice", client_id="client-7",
        credential_supplier=lambda: credentials.append(True) or "Bearer fixture",
        transport=httpx.MockTransport(lambda request: requests.append(request)),
    )
    config = PMWriteConfig(
        leantime_client=None, orchestrator_client=adapter,
        conport_client=None, memory_client=None, project_id="other-project",
    )
    try:
        with pytest.raises(ValueError, match="Adapter project mismatch"):
            pm_transition_command(config, {})
        assert requests == []
        assert credentials == []
    finally:
        adapter.close()


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
        memory_client=None,
    )

    receipt = pm_log_progress(config, "task-1", "progress", "key-idem-3")

    assert receipt.success
    assert receipt.canonical_system == "conport"
    assert receipt.operation_type == PMActionKind.PROGRESS_LOG.value
    assert len(conport_client.calls) == 1
    mirror = receipt.mirror_receipts[0]
    assert mirror.system == "dope-memory"
    assert not mirror.success
    assert mirror.error == "Memory client missing"


def test_pm_log_decision_marks_conport_decision_and_memory_mirror():
    conport_client = MockConportClient()
    memory_client = MockMemoryClient()
    config = PMWriteConfig(
        leantime_client=None,
        orchestrator_client=None,
        conport_client=conport_client,
        memory_client=memory_client,
    )

    receipt = pm_log_decision(config, "task-1", "Ship phase 1 without bridge fan-out", "key-idem-9")

    assert receipt.success
    assert receipt.operation_type == PMActionKind.DECISION_LOG.value
    assert conport_client.calls == [
        (
            "record_progress",
            "task-1",
            "Ship phase 1 without bridge fan-out",
            True,
            "key-idem-9",
        )
    ]
    assert memory_client.calls == [
        (
            "append_chronicle",
            "task-1",
            "Ship phase 1 without bridge fan-out",
            True,
            "key-idem-9",
        )
    ]
    assert receipt.mirror_receipts[0].persisted_id == "chron-1"
