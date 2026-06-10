"""
Regression tests: insert_work_log_entry must fail closed on constraint violations.

Previously, INSERT OR IGNORE silently swallowed CHECK constraint failures
(e.g. category="testing") while the function still returned the deterministic
entry_id — callers reported created=True for entries that were never written.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest

from chronicle.store import ChronicleStore


WORKSPACE_ID = "test_ws"
INSTANCE_ID = "test_inst"


@pytest.fixture
def store(tmp_path: Path) -> Iterator[ChronicleStore]:
    s = ChronicleStore(db_path=tmp_path / "chronicle.db")
    s.initialize_schema()
    yield s
    s.close()


def _entry_kwargs(**overrides):
    kwargs = dict(
        workspace_id=WORKSPACE_ID,
        instance_id=INSTANCE_ID,
        category="implementation",
        entry_type="manual_note",
        summary="A valid entry",
        source_event_id="manual-test-0001",
        source_event_type="manual.memory_store",
        source_adapter="mcp-server",
        source_event_ts_utc="2026-06-10T00:00:00+00:00",
        promotion_rule="manual",
    )
    kwargs.update(overrides)
    return kwargs


def _count_entries(store: ChronicleStore) -> int:
    return store.connect().execute(
        "SELECT COUNT(*) FROM work_log_entries"
    ).fetchone()[0]


class TestInsertWorkLogEntryFailClosed:
    def test_invalid_category_raises_and_writes_nothing(self, store):
        with pytest.raises(ValueError, match="category"):
            store.insert_work_log_entry(**_entry_kwargs(category="testing"))
        assert _count_entries(store) == 0

    def test_invalid_entry_type_raises_and_writes_nothing(self, store):
        with pytest.raises(ValueError, match="entry_type"):
            store.insert_work_log_entry(**_entry_kwargs(entry_type="bogus"))
        assert _count_entries(store) == 0

    def test_invalid_outcome_raises_and_writes_nothing(self, store):
        with pytest.raises(ValueError, match="outcome"):
            store.insert_work_log_entry(**_entry_kwargs(outcome="finished"))
        assert _count_entries(store) == 0

    def test_invalid_workflow_phase_raises_and_writes_nothing(self, store):
        with pytest.raises(ValueError, match="workflow_phase"):
            store.insert_work_log_entry(**_entry_kwargs(workflow_phase="testing"))
        assert _count_entries(store) == 0

    def test_out_of_range_importance_score_raises_and_writes_nothing(self, store):
        with pytest.raises(ValueError, match="importance_score"):
            store.insert_work_log_entry(**_entry_kwargs(importance_score=11))
        assert _count_entries(store) == 0

    def test_valid_insert_is_actually_written(self, store):
        entry_id = store.insert_work_log_entry(**_entry_kwargs())
        assert _count_entries(store) == 1
        assert store.get_entry_by_id(WORKSPACE_ID, INSTANCE_ID, entry_id) is not None

    def test_idempotent_replay_still_succeeds(self, store):
        """Same provenance twice = legitimate IGNORE case, must not raise."""
        first = store.insert_work_log_entry(**_entry_kwargs())
        second = store.insert_work_log_entry(**_entry_kwargs())
        assert first == second
        assert _count_entries(store) == 1
