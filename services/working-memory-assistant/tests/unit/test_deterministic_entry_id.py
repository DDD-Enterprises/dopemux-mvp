
import pytest
import hashlib
import sqlite3
from chronicle.store import ChronicleStore

def test_entry_id_determinism(tmp_path):
    """Verify entry_id is deterministic SHA256 of provenance fields.
    
    Packet D §7.7: entry_id = sha256(source_event_id | promotion_rule | source_event_ts_utc)
    """
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    # Inputs
    sid = "evt-123"
    rule = "decision_logged"
    ts = "2026-02-09T12:00:00Z"
    
    # Expected ID
    fingerprint = f"{sid}|{rule}|{ts}"
    expected_id = hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()
    
    entry_id = store.insert_work_log_entry(
        workspace_id="ws-1",
        instance_id="A",
        category="planning",
        entry_type="decision",
        summary="Test",
        source_event_id=sid,
        source_event_type="type",
        source_adapter="adapter",
        source_event_ts_utc=ts,
        promotion_rule=rule,
    )
    
    assert entry_id == expected_id, "entry_id must match SHA256 of provenance"

def test_idempotent_insertion(tmp_path):
    """Verify that re-inserting the same entry (same provenance) does not error or duplicate.
    
    Packet D §7.7: Re-promotion must be safe and idempotent.
    """
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    kwargs = {
        "workspace_id": "ws-1",
        "instance_id": "A",
        "category": "planning",
        "entry_type": "decision",
        "summary": "Test",
        "source_event_id": "evt-1",
        "source_event_type": "type",
        "source_adapter": "adapter",
        "source_event_ts_utc": "2026-02-09T12:00:00Z",
        "promotion_rule": "rule",
    }
    
    id1 = store.insert_work_log_entry(**kwargs)
    id2 = store.insert_work_log_entry(**kwargs)
    
    assert id1 == id2
    
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM work_log_entries").fetchone()[0]
    assert count == 1, "Should only have 1 entry after duplicate insertion"
