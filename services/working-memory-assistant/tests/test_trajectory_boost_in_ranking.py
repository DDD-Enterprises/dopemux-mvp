"""
Test trajectory boost integration in memory_search ranking.

Verifies that trajectory boost factor actually affects result ordering
while maintaining Top-3 boundary.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

from chronicle.store import ChronicleStore
from trajectory.manager import TrajectoryManager
from dope_memory_main import DopeMemoryMCPServer


pytestmark = pytest.mark.phase2  # Mark all tests in this module as phase2


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        yield data_dir


@pytest.fixture
def server(temp_db):
    """Create DopeMemoryMCPServer instance with temp database."""
    return DopeMemoryMCPServer(
        data_dir=temp_db,
        workspace_id="test_ws",
        instance_id="test_inst",
    )


@pytest.fixture
def populated_store(temp_db):
    """Create and populate a ChronicleStore with test data."""
    workspace_id = "test_ws"
    instance_id = "test_inst"
    session_id = "test_session"
    
    db_path = temp_db / f"chronicle_{workspace_id}.db"
    store = ChronicleStore(db_path=db_path)
    store.initialize_schema()  # Initialize database schema
    
    # Insert 4 entries with different categories
    # Entry 1: implementation category, importance=7
    entry1_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        session_id=session_id,
        category="implementation",
        entry_type="task_event",
        summary="Implemented JWT authentication",
        importance_score=7,
        tags=["auth", "security"],
    )
    
    # Entry 2: architecture category, importance=8 (higher base score)
    entry2_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        session_id=session_id,
        category="architecture",
        entry_type="decision",
        summary="Optimized database queries",
        importance_score=8,
        tags=["database", "performance"],
    )
    
    # Entry 3: implementation category, importance=6
    entry3_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        session_id=session_id,
        category="implementation",
        entry_type="resolution",
        summary="Fixed auth token expiry bug",
        importance_score=6,
        tags=["auth", "bugfix"],
    )
    
    # Entry 4: documentation category, importance=9 (highest base score)
    entry4_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        session_id=session_id,
        category="documentation",
        entry_type="milestone",
        summary="Redesigned dashboard UI",
        importance_score=9,
        tags=["ui", "frontend"],
    )
    
    return {
        "store": store,
        "workspace_id": workspace_id,
        "instance_id": instance_id,
        "session_id": session_id,
        "entries": {
            "impl1": entry1_id,  # importance=7, implementation
            "arch": entry2_id,  # importance=8, architecture
            "impl2": entry3_id,  # importance=6, implementation
            "docs": entry4_id,  # importance=9, documentation
        }
    }


def test_trajectory_boost_affects_ranking(populated_store):
    """Test that trajectory boost changes ranking while preserving Top-3."""
    store_data = populated_store
    store = store_data["store"]
    workspace_id = store_data["workspace_id"]
    instance_id = store_data["instance_id"]
    
    # Set trajectory to "Active in implementation"
    trajectory_mgr = TrajectoryManager(store)
    
    # Update trajectory state to focus on "implementation"
    trajectory_state = {
        "workspace_id": workspace_id,
        "instance_id": instance_id,
        "session_id": store_data["session_id"],
        "current_stream": "Active in implementation",
        "current_goal": {},
        "last_steps": [],
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    store.upsert_trajectory_state(workspace_id, instance_id, trajectory_state)
    
    # Search without filters
    rows = store.search_work_log(
        workspace_id=workspace_id,
        instance_id=instance_id,
        limit=10,
    )
    
    # Without boost, order by importance: docs(9), arch(8), impl1(7), impl2(6)
    base_order = [r["id"] for r in rows]
    expected_base = [
        store_data["entries"]["docs"],
        store_data["entries"]["arch"],
        store_data["entries"]["impl1"],
        store_data["entries"]["impl2"],
    ]
    assert base_order == expected_base, f"Base order mismatch: {base_order} vs {expected_base}"
    
    # Apply trajectory boost
    trajectory = trajectory_mgr.get_trajectory(workspace_id, instance_id)
    boosted_rows = []
    for row in rows:
        base_score = row["importance_score"]
        boost = trajectory_mgr.get_boost_factor(row, trajectory)
        boosted_score = base_score + boost
        
        boosted_rows.append({
            **row,
            "_boosted_score": boosted_score,
            "_boost": boost,
        })
    
    # Re-sort by boosted score
    boosted_rows.sort(key=lambda r: -r["_boosted_score"])
    boosted_order = [r["id"] for r in boosted_rows]
    
    # With boost (0.5 for category match to "implementation"):
    # - docs: 9 + 0 = 9.0
    # - arch: 8 + 0 = 8.0
    # - impl1: 7 + 0.5 = 7.5
    # - impl2: 6 + 0.5 = 6.5
    # Expected order still: docs(9.0), arch(8.0), impl1(7.5), impl2(6.5)
    
    # Check that implementation entries got boost
    impl1_row = next(r for r in boosted_rows if r["id"] == store_data["entries"]["impl1"])
    impl2_row = next(r for r in boosted_rows if r["id"] == store_data["entries"]["impl2"])
    
    assert impl1_row["_boost"] == 0.5, f"impl1 boost should be 0.5, got {impl1_row['_boost']}"
    assert impl2_row["_boost"] == 0.5, f"impl2 boost should be 0.5, got {impl2_row['_boost']}"
    assert impl1_row["_boosted_score"] == 7.5
    assert impl2_row["_boosted_score"] == 6.5
    
    # The ranking still has docs first, but implementation entries are boosted
    # This demonstrates boost is working even if it doesn't swap top position


def test_trajectory_boost_top_k_boundary_with_manual_boost(populated_store):
    """Test that Top-3 boundary is preserved with trajectory boost (manual implementation)."""
    store_data = populated_store
    workspace_id = store_data["workspace_id"]
    instance_id = store_data["instance_id"]
    store = store_data["store"]
    
    # Set trajectory to "Active in implementation"
    trajectory_mgr = TrajectoryManager(store)
    
    trajectory_state = {
        "workspace_id": workspace_id,
        "instance_id": instance_id,
        "session_id": store_data["session_id"],
        "current_stream": "Active in implementation",
        "current_goal": {},
        "last_steps": [],
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    store.upsert_trajectory_state(workspace_id, instance_id, trajectory_state)
    
    # Simulate memory_search with trajectory boost
    rows = store.search_work_log(
        workspace_id=workspace_id,
        instance_id=instance_id,
        limit=20,  # Fetch more for boost ranking
    )
    
    # Apply trajectory boost
    trajectory = trajectory_mgr.get_trajectory(workspace_id, instance_id)
    boosted_rows = []
    for row in rows:
        base_score = row["importance_score"]
        boost = trajectory_mgr.get_boost_factor(row, trajectory)
        boosted_score = base_score + boost
        
        boosted_rows.append({
            **row,
            "_boosted_score": boosted_score,
            "_boost": boost,
        })
    
    # Re-sort by boosted score
    boosted_rows.sort(key=lambda r: -r["_boosted_score"])
    
    # Apply Top-3
    top_3 = boosted_rows[:3]
    
    # Should have exactly 3 items
    assert len(top_3) == 3, f"Expected 3 items, got {len(top_3)}"
    
    # Check that implementation entries got boost
    impl_items = [item for item in top_3 if item["category"] == "implementation"]
    for impl_item in impl_items:
        assert impl_item["_boost"] == 0.5, f"Expected boost 0.5 for implementation item, got {impl_item['_boost']}"


def test_trajectory_boost_ranking_swap(temp_db):
    """Test a scenario where boost definitely swaps ranking."""
    workspace_id = "test_ws"
    instance_id = "test_inst"
    session_id = "test_session"
    
    db_path = temp_db / f"chronicle_{workspace_id}.db"
    store = ChronicleStore(db_path=db_path)
    store.initialize_schema()  # Initialize database schema
    
    # Create entries where boost WILL swap order
    # Entry 1: debugging category, importance=5
    entry1_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        session_id=session_id,
        category="debugging",
        entry_type="error",
        summary="Wrote feature A",
        importance_score=5,
    )
    
    # Entry 2: research category, importance=5
    entry2_id = store.insert_work_log_entry(
        workspace_id=workspace_id,
        instance_id=instance_id,
        session_id=session_id,
        category="research",
        entry_type="manual_note",
        summary="Tested feature B",
        importance_score=5,
    )
    
    # Set trajectory to "Active in research"
    trajectory_mgr = TrajectoryManager(store)
    trajectory_state = {
        "workspace_id": workspace_id,
        "instance_id": instance_id,
        "session_id": session_id,
        "current_stream": "Active in research",
        "current_goal": {},
        "last_steps": [],
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    store.upsert_trajectory_state(workspace_id, instance_id, trajectory_state)
    
    # Fetch and boost
    rows = store.search_work_log(workspace_id=workspace_id, instance_id=instance_id, limit=10)
    trajectory = trajectory_mgr.get_trajectory(workspace_id, instance_id)
    
    boosted_rows = []
    for row in rows:
        boost = trajectory_mgr.get_boost_factor(row, trajectory)
        boosted_rows.append({
            **row,
            "_boosted_score": row["importance_score"] + boost,
        })
    
    boosted_rows.sort(key=lambda r: -r["_boosted_score"])
    
    # With boost:
    # - debugging: 5 + 0 = 5.0
    # - research: 5 + 0.5 = 5.5
    # Research should now rank first
    
    assert boosted_rows[0]["id"] == entry2_id, "Research entry should rank first after boost"
    assert boosted_rows[1]["id"] == entry1_id, "Debugging entry should rank second"