
import pytest
import sqlite3
from datetime import datetime, timezone, timedelta
from chronicle.store import ChronicleStore

def test_store_uses_event_time_as_authoritative(tmp_path):
    """Verify that ts_utc comes from source_event_ts_utc, NOT wall clock.
    
    Packet D §5.3: Event time is authoritative for chronology.
    """
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    # Event from the past
    past_ts = "2020-01-01T12:00:00+00:00"
    
    entry_id = store.insert_work_log_entry(
        workspace_id="ws-1",
        instance_id="A",
        category="planning",
        entry_type="decision",
        summary="Test Decision",
        source_event_id="evt-1",
        source_event_type="decision.logged",
        source_adapter="test",
        source_event_ts_utc=past_ts,
        promotion_rule="decision_logged",
    )
    
    # Verify DB content
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT ts_utc, created_at_utc FROM work_log_entries WHERE id = ?", (entry_id,)).fetchone()
    
    assert row["ts_utc"] == past_ts, "Stored ts_utc MUST match source event time"
    
    # Verify created_at_utc is recent (wall clock)
    created_at = datetime.fromisoformat(row["created_at_utc"])
    now = datetime.now(timezone.utc)
    assert (now - created_at).total_seconds() < 10, "created_at_utc should be wall clock time"

def test_store_promotion_processing_time(tmp_path):
    """Verify promotion_ts_utc is recorded."""
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    entry_id = store.insert_work_log_entry(
        workspace_id="ws-1",
        instance_id="A",
        category="planning",
        entry_type="decision",
        summary="Test",
        source_event_id="evt-1",
        source_event_type="type",
        source_adapter="adapter",
        source_event_ts_utc="2022-01-01T00:00:00Z",
        promotion_rule="rule",
    )
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT promotion_ts_utc FROM work_log_entries WHERE id = ?", (entry_id,)).fetchone()
    
    assert row["promotion_ts_utc"] is not None
