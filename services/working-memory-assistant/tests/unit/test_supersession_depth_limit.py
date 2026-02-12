"""Test supersession chain depth limit (Packet F).

Validates that chains cannot exceed MAX_CHAIN_DEPTH (10 by default).
"""

import pytest
from chronicle.store import ChronicleStore, MAX_CHAIN_DEPTH


def test_supersession_depth_limit(tmp_path):
    db_path = tmp_path / "test_chronicle.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()

    workspace_id = "test-ws"
    instance_id = "A"

    # Create a chain of entries
    current_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        category="implementation",
        entry_type="decision",
        summary="Entry 1",
        source_event_id="evt-1",
        source_event_type="test",
        source_adapter="test",
        source_event_ts_utc="2026-02-11T12:00:00Z",
        promotion_rule="test"
    )

    for i in range(2, MAX_CHAIN_DEPTH + 1):
        current_id = store.insert_corrected_work_log_entry(
            workspace_id=workspace_id,
            instance_id=instance_id,
            supersedes_entry_id=current_id,
            correction_type="update",
            summary=f"Entry {i}"
        )

    # Attempting to add the 11th entry should fail
    with pytest.raises(ValueError, match=f"Supersession chain depth limit exceeded"):
        store.insert_corrected_work_log_entry(
            workspace_id=workspace_id,
            instance_id=instance_id,
            supersedes_entry_id=current_id,
            correction_type="update",
            summary="Entry 11 (invalid depth)"
        )


if __name__ == "__main__":
    pytest.main([__file__])
