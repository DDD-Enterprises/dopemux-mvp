"""
Unit Tests for ConPort Event Adapter

Tests bidirectional transformations, ADHD metadata preservation,
and error handling for Architecture 3.0 Component 2.

Created: 2025-10-19 (Task 2.2)
"""

import pytest
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_orchestrator import OrchestrationTask, TaskStatus, AgentType
from adapters.conport_adapter import (
    orchestration_task_to_conport_progress,
    conport_progress_to_orchestration_task,
    safe_orchestration_task_to_conport_progress,
    encode_energy_tag,
    encode_complexity_tag,
    encode_priority_tag,
    decode_energy_tag,
    decode_complexity_tag,
    decode_priority_tag
)


# ============================================================================
# Tag Encoding/Decoding Tests
# ============================================================================

class TestADHDTagUtils:
    """Test ADHD metadata tag encoding and decoding."""

    def test_encode_energy_tags(self):
        """Test energy level tag encoding."""
        assert encode_energy_tag("low") == "energy-low"
        assert encode_energy_tag("medium") == "energy-medium"
        assert encode_energy_tag("high") == "energy-high"
        assert encode_energy_tag("HIGH") == "energy-high"  # Lowercase conversion

    def test_encode_complexity_tags(self):
        """Test complexity score tag encoding (0.0-1.0 → 0-10)."""
        assert encode_complexity_tag(0.0) == "complexity-0"
        assert encode_complexity_tag(0.35) == "complexity-3"
        assert encode_complexity_tag(0.6) == "complexity-6"
        assert encode_complexity_tag(1.0) == "complexity-10"

        # Clamping
        assert encode_complexity_tag(-0.5) == "complexity-0"  # Clamp to 0
        assert encode_complexity_tag(1.5) == "complexity-10"  # Clamp to 10

    def test_encode_priority_tags(self):
        """Test priority tag encoding."""
        assert encode_priority_tag(1) == "priority-1"
        assert encode_priority_tag(3) == "priority-3"
        assert encode_priority_tag(5) == "priority-5"

        # Clamping
        assert encode_priority_tag(0) == "priority-1"  # Clamp to 1
        assert encode_priority_tag(10) == "priority-5"  # Clamp to 5

    def test_decode_energy_tags(self):
        """Test energy level tag decoding."""
        assert decode_energy_tag("energy-low") == "low"
        assert decode_energy_tag("energy-medium") == "medium"
        assert decode_energy_tag("energy-high") == "high"
        assert decode_energy_tag("other-tag") is None  # Non-energy tag

    def test_decode_complexity_tags(self):
        """Test complexity tag decoding (0-10 → 0.0-1.0)."""
        assert decode_complexity_tag("complexity-0") == 0.0
        assert decode_complexity_tag("complexity-3") == 0.3
        assert decode_complexity_tag("complexity-6") == 0.6
        assert decode_complexity_tag("complexity-10") == 1.0
        assert decode_complexity_tag("other-tag") is None  # Non-complexity tag

    def test_decode_priority_tags(self):
        """Test priority tag decoding."""
        assert decode_priority_tag("priority-1") == 1
        assert decode_priority_tag("priority-3") == 3
        assert decode_priority_tag("priority-5") == 5
        assert decode_priority_tag("other-tag") is None  # Non-priority tag


# ============================================================================
# Transformation Tests
# ============================================================================

class TestOrchestrationTaskToConPortProgress:
    """Test OrchestrationTask → ConPort progress_entry transformation."""

    def test_basic_transformation(self):
        """Test transformation of minimal OrchestrationTask."""
        task = OrchestrationTask(
            id="task-123",
            title="Test Task",
            description="Test description",
            status=TaskStatus.PENDING,
            complexity_score=0.5,
            estimated_minutes=30,
            energy_required="medium",
            priority=3
        )

        result = orchestration_task_to_conport_progress(task, "/test/workspace")

        assert result["workspace_id"] == "/test/workspace"
        assert result["status"] == "TODO"
        assert "Test Task" in result["description"]
        assert "task-orchestrator" in result["tags"]
        assert "energy-medium" in result["tags"]
        assert "complexity-5" in result["tags"]
        assert "priority-3" in result["tags"]

    def test_status_mapping_comprehensive(self):
        """Test all TaskStatus values map correctly."""
        test_cases = [
            (TaskStatus.PENDING, "TODO"),
            (TaskStatus.IN_PROGRESS, "IN_PROGRESS"),
            (TaskStatus.COMPLETED, "DONE"),
            (TaskStatus.BLOCKED, "BLOCKED"),
            (TaskStatus.NEEDS_BREAK, "IN_PROGRESS"),  # Lossy mapping
            (TaskStatus.CONTEXT_SWITCH, "IN_PROGRESS"),  # Lossy mapping
            (TaskStatus.PAUSED, "BLOCKED")  # Lossy mapping
        ]

        for task_status, expected_conport_status in test_cases:
            task = OrchestrationTask(
                id="test",
                title="Test",
                status=task_status,
                complexity_score=0.5,
                estimated_minutes=25,
                energy_required="medium",
                priority=3
            )
            result = orchestration_task_to_conport_progress(task, "/test")
            assert result["status"] == expected_conport_status

    def test_leantime_linking(self):
        """Test Leantime task linking."""
        task = OrchestrationTask(
            id="task-123",
            title="Linked Task",
            leantime_id=999,
            complexity_score=0.5,
            estimated_minutes=25,
            energy_required="medium",
            priority=3
        )

        result = orchestration_task_to_conport_progress(task, "/test")

        assert "leantime-synced" in result["tags"]
        assert result.get("linked_item_type") == "leantime_task"
        assert result.get("linked_item_id") == "999"
        assert result.get("link_relationship_type") == "tracks_implementation"

    def test_agent_assignment_tagging(self):
        """Test agent assignment creates correct tag."""
        task = OrchestrationTask(
            id="task-123",
            title="Agent Task",
            assigned_agent=AgentType.ZEN,
            complexity_score=0.7,
            estimated_minutes=60,
            energy_required="high",
            priority=4
        )

        result = orchestration_task_to_conport_progress(task, "/test")

        assert "agent-zen" in result["tags"]


class TestConPortProgressToOrchestrationTask:
    """Test ConPort progress_entry → OrchestrationTask transformation."""

    def test_basic_reverse_transformation(self):
        """Test reverse transformation of minimal progress_entry."""
        progress = {
            "id": 999,
            "status": "TODO",
            "description": "Test Task | Test description | Duration: 30m | Complexity: 0.5 | Energy: medium",
            "tags": ["task-orchestrator", "energy-medium", "complexity-5", "priority-3"],
            "timestamp": "2025-10-19T22:00:00Z"
        }

        task = conport_progress_to_orchestration_task(progress)

        assert task.id == "conport-999"
        assert task.conport_id == 999  # Stores ConPort ID
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.status == TaskStatus.PENDING
        assert task.complexity_score == 0.5  # From tag (authoritative)
        assert task.energy_required == "medium"  # From tag
        assert task.priority == 3  # From tag
        assert task.estimated_minutes == 30  # From description

    def test_tags_override_description(self):
        """Test that tags are authoritative over description metadata."""
        progress = {
            "id": 999,
            "status": "TODO",
            "description": "Task | Desc | Duration: 30m | Complexity: 0.3 | Energy: low",  # Says 0.3
            "tags": ["task-orchestrator", "energy-high", "complexity-7", "priority-5"],  # Says 0.7
            "timestamp": "2025-10-19T22:00:00Z"
        }

        task = conport_progress_to_orchestration_task(progress)

        # Tags win (authoritative)
        assert task.complexity_score == 0.7  # From tag, not description (0.3)
        assert task.energy_required == "high"  # From tag, not description (low)
        assert task.priority == 5  # From tag

    def test_leantime_linking_reverse(self):
        """Test Leantime link restoration."""
        progress = {
            "id": 999,
            "status": "IN_PROGRESS",
            "description": "Task | Desc",
            "tags": ["task-orchestrator", "energy-medium", "complexity-5", "priority-3", "leantime-synced"],
            "timestamp": "2025-10-19T22:00:00Z",
            "linked_item_type": "leantime_task",
            "linked_item_id": "888"
        }

        task = conport_progress_to_orchestration_task(progress)

        assert task.leantime_id == 888

    def test_missing_tags_use_defaults(self):
        """Test that missing tags fall back to safe defaults."""
        progress = {
            "id": 999,
            "status": "TODO",
            "description": "Minimal Task",
            "tags": ["task-orchestrator"],  # Only required tag, no ADHD tags
            "timestamp": "2025-10-19T22:00:00Z"
        }

        task = conport_progress_to_orchestration_task(progress)

        # Defaults applied
        assert task.energy_required == "medium"
        assert task.complexity_score == 0.5
        assert task.priority == 3
        assert task.estimated_minutes == 25


# ============================================================================
# Lossless Round-Trip Tests
# ============================================================================

class TestLosslessTransformation:
    """Test that round-trip transformation preserves business data."""

    def test_roundtrip_preserves_business_fields(self):
        """Test full round-trip transformation."""
        # Original task
        original = OrchestrationTask(
            id="task-123",
            title="Round-Trip Test",
            description="Testing lossless transformation",
            status=TaskStatus.IN_PROGRESS,
            priority=4,
            complexity_score=0.7,
            estimated_minutes=60,
            energy_required="high",
            cognitive_load=0.7,
            assigned_agent=AgentType.CONPORT,
            leantime_id=555
        )

        # Transform to ConPort
        progress_data = orchestration_task_to_conport_progress(original, "/test/workspace")

        # Simulate ConPort storage (adds ID and timestamp)
        stored_progress = {
            **progress_data,
            "id": 999,
            "timestamp": "2025-10-19T22:00:00Z"
        }

        # Transform back
        restored = conport_progress_to_orchestration_task(stored_progress)

        # Validate business fields preserved (acceptable losses: IDs, timestamps)
        assert restored.title == original.title
        assert restored.description == original.description
        assert restored.status == original.status  # IN_PROGRESS → IN_PROGRESS
        assert restored.priority == original.priority
        assert restored.complexity_score == original.complexity_score
        assert restored.estimated_minutes == original.estimated_minutes
        assert restored.energy_required == original.energy_required
        assert restored.assigned_agent == original.assigned_agent
        assert restored.leantime_id == original.leantime_id

        # Acceptable ID changes
        assert restored.id == "conport-999"  # Changed (expected)
        assert restored.conport_id == 999  # Added (enhancement)

    def test_all_status_values_roundtrip(self):
        """Test all TaskStatus values survive round-trip (some lossy)."""
        test_statuses = [
            (TaskStatus.PENDING, TaskStatus.PENDING),  # Lossless
            (TaskStatus.IN_PROGRESS, TaskStatus.IN_PROGRESS),  # Lossless
            (TaskStatus.COMPLETED, TaskStatus.COMPLETED),  # Lossless
            (TaskStatus.BLOCKED, TaskStatus.BLOCKED),  # Lossless
            (TaskStatus.NEEDS_BREAK, TaskStatus.IN_PROGRESS),  # Lossy (acceptable)
            (TaskStatus.CONTEXT_SWITCH, TaskStatus.IN_PROGRESS),  # Lossy (acceptable)
            (TaskStatus.PAUSED, TaskStatus.BLOCKED)  # Lossy (acceptable)
        ]

        for original_status, expected_restored_status in test_statuses:
            task = OrchestrationTask(
                id="test",
                title="Status Test",
                status=original_status,
                complexity_score=0.5,
                estimated_minutes=25,
                energy_required="medium",
                priority=3
            )

            progress = orchestration_task_to_conport_progress(task, "/test")
            progress["id"] = 1
            progress["timestamp"] = "2025-10-19T22:00:00Z"

            restored = conport_progress_to_orchestration_task(progress)

            assert restored.status == expected_restored_status


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestSafeTransformations:
    """Test error handling and graceful degradation."""

    def test_safe_transform_invalid_task(self):
        """Test safe transformation handles invalid task."""
        task = OrchestrationTask(
            id="",  # Invalid: empty ID
            title="",  # Invalid: empty title
            complexity_score=0.5,
            estimated_minutes=25,
            energy_required="medium",
            priority=3
        )

        result = safe_orchestration_task_to_conport_progress(task, "/test")

        assert result is None  # Should return None, not raise exception

    def test_safe_transform_invalid_complexity(self):
        """Test safe transformation clamps invalid complexity."""
        task = OrchestrationTask(
            id="test",
            title="Test",
            complexity_score=1.5,  # Invalid: > 1.0
            estimated_minutes=25,
            energy_required="medium",
            priority=3
        )

        result = safe_orchestration_task_to_conport_progress(task, "/test")

        assert result is not None  # Should succeed with clamping
        assert "complexity-10" in result["tags"]  # Clamped to 1.0 → 10

    def test_safe_transform_invalid_workspace(self):
        """Test safe transformation rejects invalid workspace_id."""
        task = OrchestrationTask(
            id="test",
            title="Test",
            complexity_score=0.5,
            estimated_minutes=25,
            energy_required="medium",
            priority=3
        )

        # Relative path (invalid - must be absolute)
        result = safe_orchestration_task_to_conport_progress(task, "relative/path")

        assert result is None  # Should reject non-absolute path


# ============================================================================
# ADHD Metadata Preservation Tests
# ============================================================================

class TestADHDMetadataPreservation:
    """Test that ADHD metadata survives transformations."""

    def test_energy_levels_preserved(self):
        """Test all energy levels preserved through round-trip."""
        energy_levels = ["low", "medium", "high"]

        for energy in energy_levels:
            task = OrchestrationTask(
                id="test",
                title="Energy Test",
                energy_required=energy,
                complexity_score=0.5,
                estimated_minutes=25,
                priority=3
            )

            progress = orchestration_task_to_conport_progress(task, "/test")
            progress["id"] = 1
            progress["timestamp"] = "2025-10-19T22:00:00Z"

            restored = conport_progress_to_orchestration_task(progress)

            assert restored.energy_required == energy

    def test_complexity_granularity_preserved(self):
        """Test complexity precision preserved (0.1 granularity)."""
        test_values = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]

        for complexity in test_values:
            task = OrchestrationTask(
                id="test",
                title="Complexity Test",
                complexity_score=complexity,
                estimated_minutes=25,
                energy_required="medium",
                priority=3
            )

            progress = orchestration_task_to_conport_progress(task, "/test")
            progress["id"] = 1
            progress["timestamp"] = "2025-10-19T22:00:00Z"

            restored = conport_progress_to_orchestration_task(progress)

            # Allow 0.1 precision loss due to integer scaling
            assert abs(restored.complexity_score - complexity) <= 0.1

    def test_adhd_tags_queryable(self):
        """Test that ADHD tags enable filtering queries."""
        # Create high-energy, high-complexity task
        task = OrchestrationTask(
            id="test",
            title="High Energy Task",
            energy_required="high",
            complexity_score=0.8,
            estimated_minutes=90,
            priority=5
        )

        progress = orchestration_task_to_conport_progress(task, "/test")

        # Verify queryable tags present
        tags = progress["tags"]
        assert "energy-high" in tags  # Can query: "Find energy-high tasks"
        assert "complexity-8" in tags  # Can query: "Find complexity > 6"
        assert "priority-5" in tags  # Can query: "Find critical tasks"

    def test_description_parsing_robust(self):
        """Test description parsing handles various formats."""
        test_cases = [
            {
                "description": "Title | Description | Duration: 45m | Complexity: 0.6 | Energy: high",
                "expected_title": "Title",
                "expected_duration": 45
            },
            {
                "description": "Title Only",
                "expected_title": "Title Only",
                "expected_duration": 25  # Default
            },
            {
                "description": "Title | Description",
                "expected_title": "Title",
                "expected_duration": 25  # Default (no Duration in description)
            }
        ]

        for test_case in test_cases:
            progress = {
                "id": 1,
                "status": "TODO",
                "description": test_case["description"],
                "tags": ["task-orchestrator", "energy-medium", "complexity-5", "priority-3"],
                "timestamp": "2025-10-19T22:00:00Z"
            }

            task = conport_progress_to_orchestration_task(progress)

            assert task.title == test_case["expected_title"]
            assert task.estimated_minutes == test_case["expected_duration"]


# ============================================================================
# Integration Tests (will be expanded in Task 2.6)
# ============================================================================

class TestConPortIntegration:
    """Integration tests for ConPort adapter (placeholder for Task 2.6)."""

    @pytest.mark.skip(reason="Requires ConPort MCP client - implement in Task 2.6")
    async def test_create_and_retrieve_task(self):
        """Test end-to-end task creation and retrieval."""
        pass

    @pytest.mark.skip(reason="Requires ConPort MCP client - implement in Task 2.6")
    async def test_dependency_sync(self):
        """Test dependency linking via ConPort."""
        pass

    @pytest.mark.skip(reason="Requires ConPort MCP client - implement in Task 2.6")
    async def test_batch_operations(self):
        """Test batch create and update operations."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
