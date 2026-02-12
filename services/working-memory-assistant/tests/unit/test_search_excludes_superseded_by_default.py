"""Test that superseded entries are excluded from default search (Packet F).

Validates that:
- Default search excludes superseded entries
- include_superseded=True shows all entries
- Count excludes superseded by default
"""

import pytest
from chronicle.store import ChronicleStore


def test_search_excludes_superseded_by_default(tmp_path):
    db_path = tmp_path / "test_chronicle.db"
    store = ChronicleStore(db_path)
    store.initialize_schema()

    workspace_id = "test-ws"
    instance_id = "A"

    # 1. Create entry
    orig_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        category="implementation",
        entry_type="decision",
        summary="Original",
        source_event_id="evt-1",
        source_event_type="test",
        source_adapter="test",
        source_event_ts_utc="2026-02-11T12:00:00Z",
        promotion_rule="test"
    )

    # 2. Correct it
    corr_id = store.insert_corrected_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        supersedes_entry_id=orig_id,
        correction_type="update",
        summary="Corrected"
    )

    # Default search: should only find Corrected
    results = store.search_work_log(workspace_id, instance_id)
    assert len(results) == 1
    assert results[0]["id"] == corr_id
    assert results[0]["summary"] == "Corrected"

    # Search with include_superseded=True: should find both
    results_all = store.search_work_log(workspace_id, instance_id, include_superseded=True)
    assert len(results_all) == 2
    ids = {r["id"] for r in results_all}
    assert orig_id in ids
    assert corr_id in ids

    # Count also should exclude superseded
    count = store.count_work_log(workspace_id, instance_id)
    assert count == 1


if __name__ == "__main__":
    pytest.main([__file__])
