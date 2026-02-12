"""Test supersession linearity (no branching/forking) - Packet F.

Validates that:
- Each entry can only be superseded once
- Attempting to supersede an already-superseded entry fails
- Chains must be linear (no trees)
"""

import pytest
from chronicle.store import ChronicleStore


def test_supersession_linearity(tmp_path):
    db_path = tmp_path / "test_chronicle.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()

    workspace_id = "test-ws"
    instance_id = "A"

    # 1. Create original entry
    orig_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        category="implementation",
        entry_type="decision",
        summary="Original decision",
        source_event_id="evt-1",
        source_event_type="test",
        source_adapter="test",
        source_event_ts_utc="2026-02-11T12:00:00Z",
        promotion_rule="test"
    )

    # 2. Create first correction (supersedes original)
    corr1_id = store.insert_corrected_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        supersedes_entry_id=orig_id,
        correction_type="update",
        summary="First correction"
    )

    # 3. Attempt to create second correction for SAME original (branching/forking)
    # This should be caught by the write-path guard
    with pytest.raises(ValueError, match="is already superseded"):
        store.insert_corrected_work_log_entry(
            workspace_id=workspace_id,
            instance_id=instance_id,
            supersedes_entry_id=orig_id,
            correction_type="update",
            summary="Second correction (invalid fork)"
        )


if __name__ == "__main__":
    pytest.main([__file__])
