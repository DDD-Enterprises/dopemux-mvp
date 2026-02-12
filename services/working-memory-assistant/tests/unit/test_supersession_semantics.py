"""Packet F — Supersession, Correction & Trust Semantics Tests.

Tests verify the Packet F invariants from DESIGN_DELTA:
  - Linear chains (no branching), max depth 10
  - Superseded entries hidden from default search/replay/count
  - Chain annotations computed correctly
  - Manual correction workflow + retraction semantics
  - Reflection staleness detection
"""

import json
import sqlite3

import pytest

from chronicle.store import ChronicleStore, MAX_CHAIN_DEPTH


# ─── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path):
    """Fresh ChronicleStore with schema + v1.2.1 scoped supersession index."""
    db_path = tmp_path / "test.db"
    s = ChronicleStore(db_path)
    s.initialize_schema()

    return s


def _make_entry(store, summary, *, session_id="sess-1", supersedes=None, evt_n=None):
    """Helper: insert a work log entry with minimal boilerplate."""
    n = evt_n or id(summary)  # unique per call
    return store.insert_work_log_entry(
        workspace_id="ws-1",
        instance_id="A",
        category="planning",
        entry_type="decision",
        summary=summary,
        source_event_id=f"evt-{n}-{summary[:8]}",
        source_event_type="test",
        source_adapter="test_harness",
        source_event_ts_utc=f"2026-02-09T12:{n % 60:02d}:00Z",
        promotion_rule="auto.test",
        session_id=session_id,
        supersedes_entry_id=supersedes,
    )


# ─── 1. Existing baseline ────────────────────────────────────────────────

def test_supersession_creates_new_entry(store):
    """Verify that supersession creates a new immutable entry pointing to the old one.

    Packet D §6.2: Corrections must be additive. Old entry remains.
    """
    id1 = _make_entry(store, "Original", evt_n=1)
    id2 = _make_entry(store, "Corrected", supersedes=id1, evt_n=2)

    conn = sqlite3.connect(str(store.db_path))
    conn.row_factory = sqlite3.Row

    row1 = conn.execute("SELECT * FROM work_log_entries WHERE id = ?", (id1,)).fetchone()
    row2 = conn.execute("SELECT * FROM work_log_entries WHERE id = ?", (id2,)).fetchone()

    assert row1 is not None, "Original entry must persist (immutable)"
    assert row2 is not None, "New entry must be created"
    assert row2["supersedes_entry_id"] == id1
    assert row1["summary"] == "Original", "Old entry content must remain unchanged"


# ─── 2. Fork prevention (UNIQUE constraint) ─────────────────────────────

def test_fork_prevention_unique_constraint(store):
    """Two entries cannot supersede the same entry (linear chains only).

    Packet F §3.2 + Packet G: scoped UNIQUE index enforces this within scope.
    """
    id1 = _make_entry(store, "Origin", evt_n=10)
    _make_entry(store, "Correction-A", supersedes=id1, evt_n=11)

    # Second supersession of same entry must fail (head-targeting check)
    with pytest.raises(ValueError, match="already superseded"):
        _make_entry(store, "Correction-B", supersedes=id1, evt_n=12)


# ─── 3. Chain depth limit ────────────────────────────────────────────────

def test_chain_depth_limit_10(store):
    """Supersession chain cannot exceed MAX_CHAIN_DEPTH entries.

    Packet F §3.4: Maximum 10 entries per chain.
    """
    ids = []
    current = _make_entry(store, "v0", evt_n=100)
    ids.append(current)

    # Build chain of exactly MAX_CHAIN_DEPTH entries (v0 + 9 corrections = 10)
    for i in range(1, MAX_CHAIN_DEPTH):
        current = _make_entry(store, f"v{i}", supersedes=current, evt_n=100 + i)
        ids.append(current)

    assert len(ids) == MAX_CHAIN_DEPTH

    # 11th entry must be rejected
    with pytest.raises(ValueError, match="depth limit exceeded"):
        _make_entry(store, "v-overflow", supersedes=current, evt_n=200)


# ─── 4. Cycle detection ─────────────────────────────────────────────────

def test_cycle_detection(store):
    """Cannot create a supersession that would form a cycle.

    This is enforced by head-targeting: you can only supersede the head,
    and the new entry becomes the head. A cycle would require superseding
    a non-head, which is rejected.
    """
    id1 = _make_entry(store, "A", evt_n=20)
    id2 = _make_entry(store, "B", supersedes=id1, evt_n=21)

    # Trying to supersede id1 again (non-head) to create cycle fails
    with pytest.raises(ValueError, match="already superseded"):
        _make_entry(store, "C-cycle", supersedes=id1, evt_n=22)


# ─── 5. Search excludes superseded by default ────────────────────────────

def test_search_excludes_superseded_by_default(store):
    """Default search hides superseded entries. Packet F §5.1."""
    id1 = _make_entry(store, "Old decision", evt_n=30)
    id2 = _make_entry(store, "New decision", supersedes=id1, evt_n=31)
    id3 = _make_entry(store, "Unrelated", evt_n=32)

    results = store.search_work_log("ws-1", "A", limit=10)
    result_ids = {r["id"] for r in results}

    assert id1 not in result_ids, "Superseded entry must be hidden"
    assert id2 in result_ids, "Head entry must be visible"
    assert id3 in result_ids, "Unrelated entry must be visible"


# ─── 6. Search include_superseded flag ───────────────────────────────────

def test_search_include_superseded(store):
    """include_superseded=True returns all entries with chain annotations.

    Packet F §5.2.
    """
    id1 = _make_entry(store, "Old", evt_n=40)
    id2 = _make_entry(store, "New", supersedes=id1, evt_n=41)

    results = store.search_work_log("ws-1", "A", limit=10, include_superseded=True)
    result_ids = {r["id"] for r in results}

    assert id1 in result_ids, "Superseded entries must be returned"
    assert id2 in result_ids

    # Check chain annotations
    old_entry = next(r for r in results if r["id"] == id1)
    new_entry = next(r for r in results if r["id"] == id2)

    assert old_entry["is_head"] is False
    assert old_entry["superseded_by"] == id2
    assert new_entry["is_head"] is True
    assert new_entry["supersedes"] == id1
    assert new_entry["chain_position"] is not None
    assert new_entry["chain_position"]["depth"] == 2


# ─── 7. Replay current mode ─────────────────────────────────────────────

def test_replay_current_mode(store):
    """Default replay hides superseded entries. Packet F §5.3."""
    id1 = _make_entry(store, "Step-1", session_id="sess-replay", evt_n=50)
    id2 = _make_entry(store, "Step-1-corrected", session_id="sess-replay",
                      supersedes=id1, evt_n=51)
    id3 = _make_entry(store, "Step-2", session_id="sess-replay", evt_n=52)

    results = store.replay_work_log("ws-1", "A", "sess-replay", limit=50)
    result_ids = [r["id"] for r in results]

    assert id1 not in result_ids
    assert id2 in result_ids
    assert id3 in result_ids


# ─── 8. Replay full mode ────────────────────────────────────────────────

def test_replay_full_mode(store):
    """replay_full includes superseded entries with annotations.

    Packet F §5.3.
    """
    id1 = _make_entry(store, "Step-1", session_id="sess-full", evt_n=60)
    id2 = _make_entry(store, "Step-1-fix", session_id="sess-full",
                      supersedes=id1, evt_n=61)

    results = store.replay_work_log("ws-1", "A", "sess-full", limit=50,
                                     mode="replay_full")
    result_ids = [r["id"] for r in results]

    assert id1 in result_ids, "Superseded entry must appear in full replay"
    assert id2 in result_ids

    old = next(r for r in results if r["id"] == id1)
    assert old["is_head"] is False
    assert old["superseded_by"] == id2


# ─── 9. Count excludes superseded ────────────────────────────────────────

def test_count_excludes_superseded(store):
    """count_work_log excludes superseded entries. Packet F §7.3."""
    _make_entry(store, "Kept", evt_n=70)
    id_old = _make_entry(store, "Will-be-superseded", evt_n=71)
    _make_entry(store, "Superseder", supersedes=id_old, evt_n=72)

    count = store.count_work_log("ws-1", "A")
    # 3 inserted, but 1 is superseded → visible = 2
    assert count == 2


# ─── 10. correct_entry with summary correction ──────────────────────────

def test_correct_entry_summary(store):
    """correct_entry creates a correcting entry with correction.summary rule."""
    id1 = _make_entry(store, "Typo summry", evt_n=80)

    id2 = store.correct_entry(
        "ws-1", "A", id1, "summary",
        corrected_summary="Fixed summary",
    )

    new = store.get_entry_by_id("ws-1", "A", id2)
    assert new is not None
    assert new["summary"] == "Fixed summary"
    assert new["supersedes_entry_id"] == id1
    assert new["promotion_rule"] == "correction.summary"
    assert new["source_adapter"] == "manual_correction"
    assert new["source_event_id"].startswith("manual:")


# ─── 11. Retraction semantics ───────────────────────────────────────────

def test_correct_entry_retraction(store):
    """Retraction sets outcome='abandoned', [RETRACTED] prefix, score=1.

    DESIGN_DELTA §6.4: outcome='abandoned' (storage).
    """
    id1 = _make_entry(store, "Bad data", evt_n=90)

    id2 = store.retract_entry("ws-1", "A", id1, reason="Data was fabricated")

    retracted = store.get_entry_by_id("ws-1", "A", id2)
    assert retracted["outcome"] == "abandoned"
    assert retracted["summary"].startswith("[RETRACTED]")
    assert "Data was fabricated" in retracted["summary"]
    assert retracted["importance_score"] == 1
    assert retracted["promotion_rule"] == "correction.retraction"

    # Original is still there, immutable
    original = store.get_entry_by_id("ws-1", "A", id1)
    assert original["summary"] == "Bad data"


# ─── 12. Must target chain head ─────────────────────────────────────────

def test_correct_must_target_head(store):
    """Correcting a superseded (non-head) entry is rejected. Packet F §6.5."""
    id1 = _make_entry(store, "v1", evt_n=300)
    id2 = _make_entry(store, "v2", supersedes=id1, evt_n=301)

    with pytest.raises(ValueError, match="already superseded"):
        store.correct_entry("ws-1", "A", id1, "summary",
                           corrected_summary="Should fail")


# ─── 13. Manual correction provenance ───────────────────────────────────

def test_manual_correction_provenance(store):
    """Manual corrections use 'manual:<ULID>' source_event_id convention.

    Packet F §6.2.
    """
    id1 = _make_entry(store, "Needs fix", evt_n=310)
    id2 = store.correct_entry("ws-1", "A", id1, "tags",
                              corrected_tags=["bug", "critical"])

    corrected = store.get_entry_by_id("ws-1", "A", id2)
    assert corrected["source_event_id"].startswith("manual:")
    assert corrected["source_adapter"] == "manual_correction"
    assert corrected["source_event_type"] == "manual.correction"
    assert corrected["promotion_rule"] == "correction.tags"
    assert json.loads(corrected["tags_json"]) == ["bug", "critical"]


# ─── 14. Reflection staleness detection ─────────────────────────────────

def test_reflection_staleness_detection(store):
    """Reflection cards referencing superseded entries are flagged stale.

    Packet F §7.1.
    """
    id1 = _make_entry(store, "Decision-A", evt_n=320)
    id2 = _make_entry(store, "Decision-B", evt_n=321)

    # Create a reflection card that references both entries
    conn = sqlite3.connect(str(store.db_path))
    conn.execute(
        """
        INSERT INTO reflection_cards (
            id, workspace_id, instance_id, session_id,
            ts_utc, window_start_utc, window_end_utc,
            trajectory, top_decisions_json, top_blockers_json,
            progress_json, next_suggested_json, source_entry_ids_json,
            created_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "refl-1", "ws-1", "A", "sess-1",
            "2026-02-09T14:00:00Z", "2026-02-09T12:00:00Z", "2026-02-09T14:00:00Z",
            "On track", "[]", "[]", "{}", "[]",
            json.dumps([id1, id2]),
            "2026-02-09T14:00:00Z",
        ),
    )
    conn.commit()
    conn.close()

    # Before supersession: not stale
    cards_before = store.get_reflection_cards("ws-1", "A")
    assert len(cards_before) == 1
    assert cards_before[0]["stale_entries"] == []
    assert cards_before[0]["regeneration_recommended"] is False

    # Supersede id1
    store.close()
    store = ChronicleStore(store.db_path)
    store.initialize_schema()
    _make_entry(store, "Decision-A-fixed", supersedes=id1, evt_n=322)

    # After supersession: stale
    cards_after = store.get_reflection_cards("ws-1", "A")
    assert len(cards_after) == 1
    assert id1 in cards_after[0]["stale_entries"]
    assert id2 not in cards_after[0]["stale_entries"]
    assert cards_after[0]["regeneration_recommended"] is True


# ─── 15. Scoping tests (Packet G) ──────────────────────────────────────

def test_supersession_is_scoped_by_workspace(store):
    """Supersession chains are scoped by workspace/instance.
    
    The same supersedes_entry_id can exist in different workspaces without conflict.
    """
    # Create entry in ws-1
    id1 = store.insert_work_log_entry(
        workspace_id="ws-1", instance_id="A",
        category="planning", entry_type="decision", summary="Entry 1",
        source_event_id="evt-1", source_event_type="test", source_adapter="test",
        source_event_ts_utc="2026-02-11T12:00:00Z", promotion_rule="test"
    )
    
    # Supersede it in ws-1 (should work)
    id1_super = store.insert_corrected_work_log_entry(
        workspace_id="ws-1", instance_id="A",
        supersedes_entry_id=id1, correction_type="update", summary="Correction 1"
    )
    
    # Create entry with SAME ID in ws-2 (simulating ID collision or just independent state)
    # Using explicit ID generation to force collision is hard due to hashing,
    # but we can verify that superseding a non-existent entry in ws-2 fails
    # even if it exists in ws-1.
    
    with pytest.raises(ValueError, match="not found"):
        store.insert_corrected_work_log_entry(
            workspace_id="ws-2", instance_id="A",
            supersedes_entry_id=id1, correction_type="update", summary="Should fail"
        )

def test_chain_resolution_scoped(store):
    """Chain resolution checks must be scoped to workspace."""
    # Create valid chain in ws-1
    id1 = _make_entry(store, "Original", evt_n=900)
    id2 = _make_entry(store, "Corrected", supersedes=id1, evt_n=901)
    
    # In ws-2, id1 does not exist, so is_entry_superseded should be False (or raise not found if we checked existence first)
    # The helpers _is_entry_superseded return False if count=0.
    
    # _is_entry_superseded(ws-2, id1) should be False
    assert store._is_entry_superseded("ws-2", "A", id1) is False
    
    # _resolve_chain_head(ws-2, id1) should return id1 (as it assumes start is valid or just strictly follows chain)
    # In this case, since it's not superseded in ws-2, it is its own head (conceptually).
    assert store._resolve_chain_head("ws-2", "A", id1) == id1
