import pytest
from pydantic import ValidationError

from chronicle.store import ChronicleStore
from dope_memory_main import DopeMemoryMCPServer, MemoryCorrectRequest


@pytest.fixture
def correction(tmp_path, monkeypatch):
    store = ChronicleStore(tmp_path / "ledger.sqlite")
    store.initialize_schema()
    entry = store.insert_work_log_entry(
        "ws",
        "A",
        "planning",
        "decision",
        "Original",
        source_event_id="event",
        source_event_type="test",
        source_adapter="test",
        source_event_ts_utc="2026-11-04T10:00:00Z",
        promotion_rule="test",
    )
    server = DopeMemoryMCPServer("ws")
    monkeypatch.setattr(server, "_get_store", lambda workspace: store)
    yield store, server, entry
    store.close()


def test_replay_receipt_reports_stored_correction_type(correction):
    store, server, entry = correction
    first = server.memory_correct(
        "ws", "A", entry, "update", corrected_summary="First", idempotency_key="key"
    )
    replay = server.memory_correct(
        "ws", "A", entry, "retraction", idempotency_key="key"
    )
    assert replay.success
    assert replay.data["new_entry_id"] == first.data["new_entry_id"]
    assert replay.data["correction_type"] == "update"
    assert (
        store.get_entry_by_id("ws", "A", replay.data["new_entry_id"])["summary"]
        == "First"
    )


@pytest.mark.parametrize("kind", ["update", "summary", "tags", "category", "outcome"])
def test_new_correction_requires_its_payload_without_writing(correction, kind):
    store, server, entry = correction
    result = server.memory_correct("ws", "A", entry, kind)
    assert not result.success
    assert "requires" in result.error
    assert (
        store.connect().execute("SELECT count(*) FROM work_log_entries").fetchone()[0]
        == 1
    )


def test_keyed_retry_still_precedes_new_payload_validation(correction):
    _, server, entry = correction
    first = server.memory_correct(
        "ws", "A", entry, "tags", corrected_tags=[], idempotency_key="key"
    )
    replay = server.memory_correct("ws", "A", entry, "tags", idempotency_key="key")
    assert first.success and replay.success
    assert replay.data == first.data


def test_rest_rejects_unadvertised_fields_instead_of_ignoring_them():
    with pytest.raises(ValidationError, match="Extra inputs"):
        MemoryCorrectRequest(
            entry_id="a", correction_type="tags", details={"not": "supported"}
        )
