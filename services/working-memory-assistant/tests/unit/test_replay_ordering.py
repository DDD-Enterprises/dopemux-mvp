
import pytest
import sqlite3
from chronicle.store import ChronicleStore

def test_replay_ordered_by_event_time(tmp_path):
    """Verify replay_work_log returns entries ordered by source_event_ts_utc ASC.
    
    Packet D §5.4: Replay must follow event time, not insertion time.
    """
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    # helper
    def insert(ts, summary):
        return store.insert_work_log_entry(
            workspace_id="ws-1", instance_id="A", session_id="sess-1",
            category="planning", entry_type="decision", summary=summary,
            source_event_id=f"evt-{summary}", source_event_type="type", source_adapter="adapter",
            source_event_ts_utc=ts, promotion_rule="rule"
        )
            
    # Insert out of order (chronologically)
    id3 = insert("2026-02-09T13:00:00Z", "Third")
    id1 = insert("2026-02-09T11:00:00Z", "First")
    id2 = insert("2026-02-09T12:00:00Z", "Second")
    
    # Replay
    rows = store.replay_work_log("ws-1", "A", "sess-1")
    
    assert len(rows) == 3
    assert rows[0]["id"] == id1
    assert rows[0]["summary"] == "First"
    assert rows[1]["id"] == id2
    assert rows[1]["summary"] == "Second"
    assert rows[2]["id"] == id3
    assert rows[2]["summary"] == "Third"

def test_replay_pagination(tmp_path):
    """Verify cursor-based pagination for replay."""
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    for i in range(5):
        store.insert_work_log_entry(
            workspace_id="ws-1", instance_id="A", session_id="sess-1",
            category="planning", entry_type="decision", summary=f"Item {i}",
            source_event_id=f"evt-{i}", source_event_type="type", source_adapter="adapter",
            source_event_ts_utc=f"2026-02-09T12:00:0{i}Z", promotion_rule="rule"
        )
        
    # Get first 2
    page1 = store.replay_work_log("ws-1", "A", "sess-1", limit=2)
    assert len(page1) == 2
    assert page1[0]["summary"] == "Item 0"
    assert page1[1]["summary"] == "Item 1"
    
    # Next page
    last = page1[-1]
    cursor = (last["source_event_ts_utc"], last["id"])
    page2 = store.replay_work_log("ws-1", "A", "sess-1", limit=2, cursor=cursor)
    
    assert len(page2) == 2
    assert page2[0]["summary"] == "Item 2"
    assert page2[1]["summary"] == "Item 3"
