import pytest
import importlib.util
from pathlib import Path

# Dynamic import to handle hyphenated directory name
spec = importlib.util.spec_from_file_location(
    "chronicle_store", 
    Path(__file__).parents[4] / "services/working-memory-assistant/chronicle/store.py"
)
chronicle_store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chronicle_store)
ChronicleStore = chronicle_store.ChronicleStore

def test_retraction_tombstone(tmp_path):
    db_path = tmp_path / "test_chronicle.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()
    
    workspace_id = "test-ws"
    instance_id = "A"
    session_id = "test-session"
    
    # 1. Create entry
    orig_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        session_id=session_id,
        category="implementation",
        entry_type="decision",
        summary="Mistake",
        source_event_id="evt-1",
        source_event_type="test",
        source_adapter="test",
        source_event_ts_utc="2026-02-11T12:00:00Z",
        promotion_rule="test"
    )
    
    # 2. Retract it
    retract_id = store.insert_corrected_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        supersedes_entry_id=orig_id,
        correction_type="retraction",
        summary="Wait, that was wrong"
    )
    
    # Default search: should find the retraction (tombstone), NOT the original
    results = store.search_work_log(workspace_id, instance_id)
    assert len(results) == 1
    assert results[0]["id"] == retract_id
    assert results[0]["summary"] == "[RETRACTED] Wait, that was wrong"
    assert results[0]["outcome"] == "abandoned"
    assert results[0]["importance_score"] <= 3

    # Full replay should show the chain
    replay = store.replay_work_log(workspace_id, instance_id, session_id=results[0]["session_id"], mode="replay_full")
    assert len(replay) == 2
    
if __name__ == "__main__":
    pytest.main([__file__])
