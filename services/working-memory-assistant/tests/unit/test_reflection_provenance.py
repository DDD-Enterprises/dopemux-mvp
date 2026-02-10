
import pytest
import sqlite3
import json
from chronicle.store import ChronicleStore

def test_reflection_persists_source_entry_ids(tmp_path):
    """Verify that reflection cards persist source_entry_ids_json fully.
    
    Packet D Risk Register §9.6: Verify provenance chain preservation.
    """
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    # Inputs
    source_ids = ["e1", "e2", "e3"]
    
    card = {
        "reflection_id": "ref-1",
        "workspace_id": "ws-1",
        "instance_id": "A",
        "session_id": "sess-1",
        "window_start": "2026-02-09T10:00:00Z",
        "window_end": "2026-02-09T14:00:00Z",
        "trajectory_summary": "Summary",
        "top_decisions": [],
        "top_blockers": [],
        "progress_summary": {},
        "suggested_next": [],
        "source_entry_ids": source_ids
    }
    
    store.insert_reflection_card(card)
    
    # Verify DB content directly
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT source_entry_ids_json FROM reflection_cards WHERE id = 'ref-1'").fetchone()
    
    assert row["source_entry_ids_json"] is not None
    assert json.loads(row["source_entry_ids_json"]) == source_ids

def test_reflection_retrieval_returns_source_ids(tmp_path):
    """Verify get_reflection_cards returns parsed source_entry_ids."""
    db_path = tmp_path / "test.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    source_ids = ["a", "b"]
    card = {
        "reflection_id": "ref-1",
        "workspace_id": "ws-1",
        "instance_id": "A",
        "window_start": "now",
        "window_end": "now",
        "trajectory_summary": "T",
        "top_decisions": [],
        "top_blockers": [],
        "progress_summary": {},
        "suggested_next": [],
        "source_entry_ids": source_ids
    }
    store.insert_reflection_card(card)
    
    cards = store.get_reflection_cards("ws-1", "A")
    assert len(cards) == 1
    assert cards[0]["source_entry_ids"] == source_ids
