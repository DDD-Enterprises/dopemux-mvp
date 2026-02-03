"""
Dedicated tests for ReflectionGenerator.

Tests deterministic Top-3 extraction, sorting, and reflection card generation.
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from chronicle.store import ChronicleStore
from reflection.reflection import ReflectionGenerator


class TestReflectionGenerator:
    """Tests for ReflectionGenerator deterministic behavior."""

    def setup_method(self):
        """Create temp database and generator."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.store = ChronicleStore(self.db_path)
        self.store.initialize_schema()
        self.generator = ReflectionGenerator(self.store)
        
        self.workspace_id = "test_ws"
        self.instance_id = "A"
        self.session_id = "session_001"

    def test_empty_window(self):
        """Empty window produces valid card with empty lists."""
        result = self.generator.generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
        )
        
        assert result["reflection_id"] is None
        assert result["trajectory_summary"] == "No activity in window"
        assert result["top_decisions"] == []
        assert result["top_blockers"] == []
        assert result["progress_summary"] == {}  # Empty dict for empty window
        assert result["suggested_next"] == []

    def test_top_decisions_stable_ordering(self):
        """Top decisions use deterministic sort: importance DESC, ts DESC, id ASC."""
        # Insert 5 decisions with specific importance scores
        for i in range(5):
            self.store.insert_work_log_entry(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                category="planning",
                entry_type="decision",
                summary=f"Decision {i}",
                session_id=self.session_id,
                importance_score=10 - i,  # 10, 9, 8, 7, 6
            )
        
        result = self.generator.generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
        )
        
        # Should return Top-3 by importance DESC
        assert len(result["top_decisions"]) == 3
        assert result["top_decisions"][0]["summary"] == "Decision 0"  # importance=10
        assert result["top_decisions"][1]["summary"] == "Decision 1"  # importance=9
        assert result["top_decisions"][2]["summary"] == "Decision 2"  # importance=8

    def test_top_blockers_stable_ordering(self):
        """Top blockers use deterministic sort: importance DESC, ts DESC, id ASC."""
        # Insert 4 blockers
        for i in range(4):
            self.store.insert_work_log_entry(
                workspace_id=self.workspace_id,
                instance_id=self.instance_id,
                category="debugging",
                entry_type="blocker",
                summary=f"Blocker {i}",
                session_id=self.session_id,
                importance_score=8 - i,  # 8, 7, 6, 5
            )
        
        result = self.generator.generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
        )
        
        # Should return Top-3 by importance DESC
        assert len(result["top_blockers"]) == 3
        assert result["top_blockers"][0]["summary"] == "Blocker 0"  # importance=8
        assert result["top_blockers"][1]["summary"] == "Blocker 1"  # importance=7
        assert result["top_blockers"][2]["summary"] == "Blocker 2"  # importance=6

    def test_progress_grouped_by_category(self):
        """Progress summary groups entries by category."""
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="planning",
            entry_type="decision",
            summary="Plan A",
            session_id=self.session_id,
        )
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="implementation",
            entry_type="task_event",
            summary="Implement feature",
            session_id=self.session_id,
        )
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="implementation",
            entry_type="task_event",
            summary="Implement test",
            session_id=self.session_id,
        )
        
        result = self.generator.generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
        )
        
        progress = result["progress_summary"]
        assert progress["total_entries"] == 3
        assert progress["by_type"]["planning"] == 1
        assert progress["by_type"]["implementation"] == 2

    def test_suggested_next_priority_order(self):
        """Suggested next returns max 3 in correct priority order."""
        # Add blocker (priority 1)
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="debugging",
            entry_type="blocker",
            summary="Critical blocker",
            session_id=self.session_id,
            importance_score=9,
        )
        
        # Add decision (priority 2)
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="planning",
            entry_type="decision",
            summary="Important decision",
            session_id=self.session_id,
            importance_score=8,
        )
        
        result = self.generator.generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
        )
        
        next_steps = result["suggested_next"]
        # First step should be resolve blocker
        assert next_steps[0]["type"] == "resolve_blocker"
        assert "Critical blocker" in next_steps[0]["summary"]
        # Second step should be implement decision
        assert next_steps[1]["type"] == "implement_decision"
        assert "Important decision" in next_steps[1]["summary"]

    def test_idempotency_check(self):
        """Idempotency: returns existing reflection if window_end within 5 minutes."""
        # Insert entry
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="planning",
            entry_type="decision",
            summary="Test decision",
            session_id=self.session_id,
        )
        
        # Generate first reflection
        now = datetime.now(timezone.utc)
        window_start = (now - timedelta(hours=2)).isoformat()
        window_end = now.isoformat()
        
        result1 = self.generator.generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
            window_start=window_start,
            window_end=window_end,
        )
        
        # Persist it
        self.store.insert_reflection_card(result1)
        
        # Try to generate another with same window_end (within 5 min)
        window_end2 = (now + timedelta(minutes=2)).isoformat()
        result2 = self.generator.generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
            window_start=window_start,
            window_end=window_end2,
        )
        
        # Should return existing reflection
        assert result2["reflection_id"] == result1["reflection_id"]

    def test_trajectory_sentence_format(self):
        """Trajectory summary is 1 sentence: 'Active in {most_common_category}'."""
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="implementation",
            entry_type="task_event",
            summary="Task 1",
            session_id=self.session_id,
        )
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="implementation",
            entry_type="task_event",
            summary="Task 2",
            session_id=self.session_id,
        )
        self.store.insert_work_log_entry(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            category="debugging",
            entry_type="blocker",
            summary="Debug issue",
            session_id=self.session_id,
        )
        
        result = self.generator.generate_reflection(
            workspace_id=self.workspace_id,
            instance_id=self.instance_id,
            session_id=self.session_id,
        )
        
        # Most common category is "implementation" (2 entries)
        assert result["trajectory_summary"] == "Active in implementation"
