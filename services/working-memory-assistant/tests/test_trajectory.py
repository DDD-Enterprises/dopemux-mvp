"""
Dedicated tests for TrajectoryManager.

Tests trajectory state management and boost factor calculation.
"""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from chronicle.store import ChronicleStore
from trajectory.manager import TrajectoryManager


class TestTrajectoryManager:
    """Tests for TrajectoryManager deterministic behavior."""

    def setup_method(self):
        """Create temp database and manager."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.store = ChronicleStore(self.db_path)
        self.store.initialize_schema()
        self.manager = TrajectoryManager(self.store)
        
        self.workspace_id = "test_ws"
        self.instance_id = "A"
        self.session_id = "session_001"

    def test_update_trajectory_shape(self):
        """update_trajectory stores and returns correct shape."""
        entry = {
            "id": "entry_001",
            "summary": "Implement feature X",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "entry_type": "task_event",
            "category": "implementation",
            "session_id": self.session_id,
        }
        
        result = self.manager.update_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            entry=entry,
        )
        
        # Check shape
        assert result["workspace_id"] == self.workspace_id
        assert result["instance_id"] == self.instance_id
        assert result["session_id"] == self.session_id
        assert "current_stream" in result
        assert "current_goal" in result
        assert "last_steps" in result
        assert "updated_at_utc" in result

    def test_last_steps_rolling_window(self):
        """last_steps maintains rolling window of max 3, newest first."""
        # Insert 5 high-signal entries
        for i in range(5):
            entry = {
                "id": f"entry_{i}",
                "summary": f"Task {i}",
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "entry_type": "task_event",
                "category": "implementation",
                "session_id": self.session_id,
            }
            self.manager.update_trajectory(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                entry=entry,
            )
        
        # Fetch final state
        state = self.manager.get_trajectory(self.workspace_id, self.instance_id)
        
        # Should have max 3 steps, newest first
        assert len(state["last_steps"]) == 3
        assert state["last_steps"][0]["summary"] == "Task 4"  # Most recent
        assert state["last_steps"][1]["summary"] == "Task 3"
        assert state["last_steps"][2]["summary"] == "Task 2"

    def test_boost_factor_category_match(self):
        """Boost factor is 0.5 if entry category matches trajectory stream."""
        # Create trajectory state with stream "Active in implementation"
        entry1 = {
            "id": "entry_001",
            "summary": "Implement feature",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "entry_type": "task_event",
            "category": "implementation",
            "session_id": self.session_id,
        }
        trajectory = self.manager.update_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            entry=entry1,
        )
        
        # Test entry with matching category
        entry2 = {
            "id": "entry_002",
            "summary": "Another implementation task",
            "category": "implementation",
            "tags_json": "[]",
        }
        
        boost = self.manager.get_boost_factor(entry2, trajectory)
        assert boost == 0.5

    def test_boost_factor_tag_overlap(self):
        """Boost factor is 0.2 if tags overlap."""
        # Create trajectory state
        entry1 = {
            "id": "entry_001",
            "summary": "Planning task",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "entry_type": "decision",
            "category": "planning",
            "session_id": self.session_id,
        }
        trajectory = self.manager.update_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            entry=entry1,
        )
        
        # Manually add tags to current_goal
        trajectory["current_goal"] = {"tags": ["feature-x", "backend"]}
        self.store.upsert_trajectory_state(self.workspace_id, self.instance_id, trajectory)
        trajectory = self.manager.get_trajectory(self.workspace_id, self.instance_id)
        
        # Test entry with tag overlap (different category, so no 0.5 boost)
        entry2 = {
            "id": "entry_002",
            "summary": "Debug feature-x",
            "category": "debugging",  # Different category
            "tags_json": json.dumps(["feature-x", "frontend"]),
        }
        
        boost = self.manager.get_boost_factor(entry2, trajectory)
        # Should get 0.2 for tag overlap (not 0.5 because category doesn't match)
        assert boost == 0.2

    def test_boost_factor_file_overlap(self):
        """Boost factor is 0.1 if linked files overlap."""
        # Create trajectory with entry that has linked files
        entry1 = {
            "id": "entry_001",
            "summary": "Work on auth.py",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "entry_type": "decision",  # Changed from "implementation" to valid entry_type
            "category": "implementation",
            "session_id": self.session_id,
            "linked_files_json": json.dumps([{"path": "src/auth.py"}]),
        }
        
        # Store entry in work log so it can be referenced
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category=entry1["category"],
            entry_type=entry1["entry_type"],
            summary=entry1["summary"],
            session_id=entry1["session_id"],
            linked_files=[{"path": "src/auth.py"}],
        )
        
        trajectory = self.manager.update_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            entry=entry1,
        )
        
        # Manually update last_steps to include linked_files
        trajectory["last_steps"][0]["linked_files"] = [{"path": "src/auth.py"}]
        self.store.upsert_trajectory_state(self.workspace_id, self.instance_id, trajectory)
        trajectory = self.manager.get_trajectory(self.workspace_id, self.instance_id)
        
        # Test entry with file overlap (different category and no tags)
        entry2 = {
            "id": "entry_002",
            "summary": "Fix auth.py bug",
            "category": "debugging",  # Different category
            "tags_json": "[]",
            "linked_files_json": json.dumps([{"path": "src/auth.py"}]),
        }
        
        boost = self.manager.get_boost_factor(entry2, trajectory)
        assert boost == 0.1

    def test_boost_factor_none(self):
        """Boost factor is 0.0 if no overlap."""
        # Create trajectory
        entry1 = {
            "id": "entry_001",
            "summary": "Planning task",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "entry_type": "decision",
            "category": "planning",
            "session_id": self.session_id,
        }
        trajectory = self.manager.update_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            entry=entry1,
        )
        
        # Test entry with no overlap
        entry2 = {
            "id": "entry_002",
            "summary": "Unrelated debugging",
            "category": "debugging",  # Different category
            "tags_json": "[]",
        }
        
        boost = self.manager.get_boost_factor(entry2, trajectory)
        assert boost == 0.0

    def test_boost_factor_capped_at_05(self):
        """Boost factor is capped at 0.5 even if multiple criteria match."""
        # Create trajectory
        entry1 = {
            "id": "entry_001",
            "summary": "Implementation task",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "entry_type": "task_event",
            "category": "implementation",
            "session_id": self.session_id,
        }
        trajectory = self.manager.update_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            entry=entry1,
        )
        
        # Add tags to trajectory
        trajectory["current_goal"] = {"tags": ["feature-x"]}
        self.store.upsert_trajectory_state(self.workspace_id, self.instance_id, trajectory)
        trajectory = self.manager.get_trajectory(self.workspace_id, self.instance_id)
        
        # Entry with category match + tag match
        entry2 = {
            "id": "entry_002",
            "summary": "Continue implementation",
            "category": "implementation",  # Matches → 0.5
            "tags_json": json.dumps(["feature-x"]),  # Matches → +0.2
        }
        
        boost = self.manager.get_boost_factor(entry2, trajectory)
        # Should be capped at 0.5, not 0.7
        assert boost == 0.5

    def test_current_stream_format(self):
        """Current stream is formatted as 'Active in {category}'."""
        entry = {
            "id": "entry_001",
            "summary": "Debug issue",
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "entry_type": "blocker",
            "category": "debugging",
            "session_id": self.session_id,
        }
        
        trajectory = self.manager.update_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            entry=entry,
        )
        
        assert trajectory["current_stream"] == "Active in debugging"

    def test_get_trajectory_returns_none_if_not_exists(self):
        """get_trajectory returns None if no state exists."""
        result = self.manager.get_trajectory(
            workspace_id="nonexistent_ws",
            instance_id="nonexistent_inst",
        )
        assert result is None
