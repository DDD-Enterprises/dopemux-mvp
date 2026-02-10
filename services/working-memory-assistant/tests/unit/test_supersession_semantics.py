
import pytest
import sqlite3
from chronicle.store import ChronicleStore

def test_supersession_creates_new_entry(tmp_path):
    """Verify that supersession creates a new immutable entry pointing to the old one.
    
    Packet D §6.2: Corrections must be additive. Old entry remains. New entry has supersedes_entry_id.
    """
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    # Original entry
    id1 = store.insert_work_log_entry(
        workspace_id="ws-1", instance_id="A",
        category="planning", entry_type="decision", summary="Original",
        source_event_id="evt-1", source_event_type="type", source_adapter="adapter",
        source_event_ts_utc="2026-02-09T12:00:00Z", promotion_rule="rule"
    )
    
    # Superseding entry (correction)
    id2 = store.insert_work_log_entry(
        workspace_id="ws-1", instance_id="A",
        category="planning", entry_type="decision", summary="Corrected",
        source_event_id="evt-2", source_event_type="type", source_adapter="manual",
        source_event_ts_utc="2026-02-09T13:00:00Z", promotion_rule="correction",
        supersedes_entry_id=id1  # Point to old entry
    )
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Verify both exist
    row1 = conn.execute("SELECT * FROM work_log_entries WHERE id = ?", (id1,)).fetchone()
    row2 = conn.execute("SELECT * FROM work_log_entries WHERE id = ?", (id2,)).fetchone()
    
    assert row1 is not None, "Original entry must persist (immutable)"
    assert row2 is not None, "New entry must be created"
    
    assert row2["supersedes_entry_id"] == id1, "New entry must reference old entry ID"
    assert row1["summary"] == "Original", "Old entry content must remain unchanged"
