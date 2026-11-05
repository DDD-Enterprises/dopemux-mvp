import json
from datetime import datetime, timezone

import pytest
from chronicle.store import ChronicleStore


@pytest.fixture
def store(tmp_path):
    value = ChronicleStore(tmp_path / "ledger.sqlite")
    value.initialize_schema()
    yield value
    value.close()


def original(store, key="a", workspace="ws"):
    return store.insert_work_log_entry(
        workspace,
        "A",
        "planning",
        "decision",
        "Original",
        source_event_id=key,
        source_event_type="test",
        source_adapter="test",
        source_event_ts_utc=datetime.now(timezone.utc).isoformat(),
        promotion_rule="test",
        session_id="session",
        tags=["keep"],
        details={"keep": True},
        linked_files=[{"path": "a.py"}],
        linked_commits=["abc"],
        linked_decisions=["d"],
    )


def correct(store, target, **kwargs):
    return store.insert_corrected_work_log_entry(
        "ws", "A", target, "update", "Fixed", **kwargs
    )


def test_one_key_two_targets_has_distinct_correct_identities(store):
    a, b = original(store), original(store, "b")
    first = correct(store, a, idempotency_key="same")
    second = correct(store, b, idempotency_key="same")
    assert first != second
    assert store.get_entry_by_id("ws", "A", second)["supersedes_entry_id"] == b


def test_keyed_correction_retains_event_time_and_window_membership(store):
    a = original(store)
    before = store.get_entry_by_id("ws", "A", a)
    b = correct(store, a, idempotency_key="key")
    after = store.get_entry_by_id("ws", "A", b)
    assert after["source_event_ts_utc"] == before["source_event_ts_utc"]
    assert b in {x["id"] for x in store.search_work_log("ws", "A", time_range="today")}
    assert store.get_entry_by_id("ws", "A", a) == before


def test_omitted_metadata_is_preserved_and_explicit_empty_tags_clear(store):
    a = original(store)
    before = store.get_entry_by_id("ws", "A", a)
    b = correct(store, a)
    after = store.get_entry_by_id("ws", "A", b)
    for key in [
        "tags_json",
        "details_json",
        "linked_files_json",
        "linked_commits_json",
        "linked_decisions_json",
    ]:
        assert after[key] == before[key]
    c = correct(store, b, corrected_tags=[])
    assert json.loads(store.get_entry_by_id("ws", "A", c)["tags_json"]) == []


def test_legacy_keyed_replay_preserves_old_identity_and_first_write_wins(store):
    a = original(store)
    legacy = store.insert_work_log_entry(
        "ws",
        "A",
        "planning",
        "decision",
        "Legacy",
        source_event_id="manual:legacy",
        source_event_type="correction.update",
        source_adapter="mcp-server",
        source_event_ts_utc="1970-01-01T00:00:00Z",
        promotion_rule="correction.update",
        supersedes_entry_id=a,
    )
    assert correct(store, a, idempotency_key="legacy") == legacy
    assert store.get_entry_by_id("ws", "A", legacy)["summary"] == "Legacy"


def test_new_keyed_replay_is_first_write_wins(store):
    a = original(store)
    first = correct(store, a, idempotency_key="key")
    second = store.insert_corrected_work_log_entry(
        "ws", "A", a, "update", "Changed", idempotency_key="key"
    )
    assert first == second
    assert store.get_entry_by_id("ws", "A", first)["summary"] == "Fixed"


def test_invalid_correction_type_is_rejected_before_writing(store):
    a = original(store)
    with pytest.raises(ValueError, match="correction_type"):
        store.insert_corrected_work_log_entry("ws", "A", a, "typo", "Bad")
    assert store.get_entry_by_id("ws", "A", a)
    assert len(store.search_work_log("ws", "A")) == 1
