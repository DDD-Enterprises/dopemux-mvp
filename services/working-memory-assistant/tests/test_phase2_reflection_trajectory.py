"""
Tests for Phase 2: Reflection + Trajectory features.

Covers:
- ReflectionGenerator (deterministic, Top-3 decisions/blockers, progress summary, next steps)
- TrajectoryManager (current stream, last steps, boost factor; persisted in trajectory_state)
- memory.pulse emission
"""

import json
import pytest
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from chronicle.store import ChronicleStore
from dope_memory_main import DopeMemoryMCPServer


class TestReflectionGenerator:
    """Tests for memory_generate_reflection tool."""

    def setup_method(self):
        """Create temp database and server."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.server = DopeMemoryMCPServer(
            data_dir=self.data_dir,
            workspace_id="test_ws",
            instance_id="A",
        )
        self.workspace_id = "test_ws"
        self.instance_id = "A"
        self.session_id = "session_001"

    def test_generate_reflection_no_activity(self):
        """Empty window returns 'No activity in window'."""
        result = self.server.memory_generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
            window_hours=2,
        )

        assert result.success
        assert result.data["reflection_id"] is None
        assert result.data["trajectory"] == "No activity in window"
        assert result.data["top_decisions"] == []
        assert result.data["top_blockers"] == []

    def test_generate_reflection_with_decisions(self):
        """Generates reflection with top-3 decisions."""
        # Insert 5 decisions with varying importance
        for i in range(5):
            self.server.memory_store(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                category="planning",
                entry_type="decision",
                summary=f"Decision {i}",
                session_id=self.session_id,
                importance_score=10 - i,  # 10, 9, 8, 7, 6
            )

        result = self.server.memory_generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
            window_hours=2,
        )

        assert result.success
        assert result.data["reflection_id"] is not None
        assert len(result.data["top_decisions"]) == 3
        # Should be sorted by importance DESC
        assert result.data["top_decisions"][0]["summary"] == "Decision 0"
        assert result.data["top_decisions"][1]["summary"] == "Decision 1"
        assert result.data["top_decisions"][2]["summary"] == "Decision 2"

    def test_generate_reflection_with_blockers(self):
        """Generates reflection with top-3 blockers."""
        # Insert 4 blockers
        for i in range(4):
            self.server.memory_store(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                category="debugging",
                entry_type="blocker",
                summary=f"Blocker {i}",
                session_id=self.session_id,
                importance_score=8 - i,  # 8, 7, 6, 5
            )

        result = self.server.memory_generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
            window_hours=2,
        )

        assert result.success
        assert len(result.data["top_blockers"]) == 3
        assert result.data["top_blockers"][0]["summary"] == "Blocker 0"

    def test_generate_reflection_progress_summary(self):
        """Progress summary includes categories and counts."""
        self.server.memory_store(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="planning",
            entry_type="decision",
            summary="Plan A",
            session_id=self.session_id,
        )
        self.server.memory_store(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="implementation",
            entry_type="task_event",
            summary="Implement feature",
            session_id=self.session_id,
        )
        self.server.memory_store(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="implementation",
            entry_type="task_event",
            summary="Implement test",
            session_id=self.session_id,
        )

        result = self.server.memory_generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
            window_hours=2,
        )

        assert result.success
        progress = result.data["progress"]
        assert progress["total_entries"] == 3
        assert progress["categories"]["planning"] == 1
        assert progress["categories"]["implementation"] == 2

    def test_generate_reflection_next_steps(self):
        """Next steps are deterministic and prioritize blockers."""
        # Add blocker and decision
        self.server.memory_store(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="debugging",
            entry_type="blocker",
            summary="Critical blocker",
            session_id=self.session_id,
            importance_score=9,
        )
        self.server.memory_store(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="planning",
            entry_type="decision",
            summary="Important decision",
            session_id=self.session_id,
            importance_score=8,
        )

        result = self.server.memory_generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
            window_hours=2,
        )

        assert result.success
        next_steps = result.data["next_suggested"]
        # First step should be resolve blocker
        assert next_steps[0]["type"] == "resolve_blocker"
        assert "Critical blocker" in next_steps[0]["summary"]
        # Second step should be implement decision
        assert next_steps[1]["type"] == "implement_decision"

    def test_reflection_persisted_in_db(self):
        """Reflection card is persisted in reflection_cards table."""
        self.server.memory_store(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="planning",
            entry_type="decision",
            summary="Test decision",
            session_id=self.session_id,
        )

        result = self.server.memory_generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
            window_hours=2,
        )

        reflection_id = result.data["reflection_id"]
        assert reflection_id is not None

        # Verify in DB
        store = self.server._get_store(self.workspace_id)
        conn = store.connect()
        row = conn.execute(
            "SELECT * FROM reflection_cards WHERE id = ?",
            (reflection_id,),
        ).fetchone()

        assert row is not None
        assert row["workspace_id"] == self.workspace_id
        assert row["instance_id"] == self.instance_id


class TestTrajectoryManager:
    """Tests for memory_trajectory tool."""

    def setup_method(self):
        """Create temp database and server."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.server = DopeMemoryMCPServer(
            data_dir=self.data_dir,
            workspace_id="test_ws",
            instance_id="A",
        )
        self.workspace_id = "test_ws"
        self.instance_id = "A"

    def test_trajectory_empty_state(self):
        """Empty trajectory returns idle state."""
        result = self.server.memory_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
        )

        assert result.success
        assert result.data["current_stream"] == "idle"
        assert result.data["last_steps"] == []
        assert result.data["boost_factor"] == 1.0

    def test_trajectory_updated_on_reflection(self):
        """Trajectory state is updated when reflection is generated."""
        # Add work entries
        self.server.memory_store(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="implementation",
            entry_type="task_event",
            summary="Implement feature X",
            session_id="session_001",
        )

        # Generate reflection (updates trajectory)
        self.server.memory_generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id="session_001",
            window_hours=2,
        )

        # Fetch trajectory
        result = self.server.memory_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
        )

        assert result.success
        assert result.data["current_stream"] == "Active in implementation"
        assert len(result.data["last_steps"]) > 0

    def test_trajectory_boost_factor_decay(self):
        """Boost factor decays based on time since last update."""
        # Update trajectory state manually
        store = self.server._get_store(self.workspace_id)
        conn = store.connect()
        old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
        
        conn.execute(
            """
            INSERT INTO trajectory_state (
                workspace_id, instance_id, session_id, updated_at_utc,
                current_stream, current_goal_json, last_steps_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.workspace_id,
                self.instance_id,
                "session_001",
                old_timestamp,
                "Active in debugging",
                "{}",
                json.dumps(["Step 1", "Step 2"]),
            ),
        )
        conn.commit()

        result = self.server.memory_trajectory(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
        )

        assert result.success
        # Boost factor should be between 1.0 and 2.0, decayed from 12 hours
        assert 1.0 <= result.data["boost_factor"] <= 2.0
        # 12 hours is half of 24, so boost should be around 1.5
        assert 1.4 <= result.data["boost_factor"] <= 1.6


class TestMemoryReflections:
    """Tests for memory_reflections tool."""

    def setup_method(self):
        """Create temp database and server."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.server = DopeMemoryMCPServer(
            data_dir=self.data_dir,
            workspace_id="test_ws",
            instance_id="A",
        )
        self.workspace_id = "test_ws"
        self.instance_id = "A"

    def test_reflections_empty(self):
        """No reflections returns empty list."""
        result = self.server.memory_reflections(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            limit=3,
        )

        assert result.success
        assert result.data["reflections"] == []
        assert result.data["count"] == 0

    def test_reflections_fetch_recent(self):
        """Fetches recent reflection cards."""
        # Generate 2 reflections
        for i in range(2):
            self.server.memory_store(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                category="planning",
                entry_type="decision",
                summary=f"Decision {i}",
                session_id=f"session_{i}",
            )
            self.server.memory_generate_reflection(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                session_id=f"session_{i}",
                window_hours=2,
            )

        result = self.server.memory_reflections(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            limit=3,
        )

        assert result.success
        assert result.data["count"] == 2
        assert len(result.data["reflections"]) == 2
        # Check structure
        reflection = result.data["reflections"][0]
        assert "id" in reflection
        assert "trajectory" in reflection
        assert "top_decisions" in reflection
        assert "top_blockers" in reflection
        assert "progress" in reflection
        assert "next_suggested" in reflection

    def test_reflections_limit(self):
        """Respects limit parameter."""
        # Generate 5 reflections
        for i in range(5):
            self.server.memory_store(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                category="planning",
                entry_type="decision",
                summary=f"Decision {i}",
                session_id=f"session_{i}",
            )
            self.server.memory_generate_reflection(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                session_id=f"session_{i}",
                window_hours=2,
            )

        result = self.server.memory_reflections(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            limit=2,
        )

        assert result.success
        assert result.data["count"] == 2
        assert len(result.data["reflections"]) == 2
