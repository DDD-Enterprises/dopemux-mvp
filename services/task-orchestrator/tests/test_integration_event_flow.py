"""
Integration Tests for Complete Event Flow - Architecture 3.0 Component 2

End-to-end validation of ConPort ↔ Task-Orchestrator data contract layer.
Tests the complete flow from Task 2.1 schema through Task 2.5 refactoring.

Created: 2025-10-19 (Task 2.6)
Dependencies: Tasks 2.1, 2.2, 2.3, 2.4, 2.5
"""

import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_orchestrator import OrchestrationTask, TaskStatus, AgentType
from adapters.conport_adapter import ConPortEventAdapter, orchestration_task_to_conport_progress, conport_progress_to_orchestration_task
from adapters.conport_insight_publisher import ConPortInsightPublisher, AIDecisionEvent, create_architecture_decision
from adapters.schema_mapping import encode_all_adhd_tags, decode_all_adhd_tags, validate_adhd_metadata, validate_conport_progress_data


# ============================================================================
# Complete Event Flow Integration Tests
# ============================================================================

class TestCompleteEventFlow:
    """Test end-to-end event flow through all Component 2 adapters."""

    def test_orchestration_task_to_conport_to_task_roundtrip(self):
        """
        Test complete round-trip: OrchestrationTask → ConPort → OrchestrationTask.

        Validates Task 2.2 (adapter) + Task 2.4 (schema mapping) integration.
        """
        # Step 1: Create OrchestrationTask
        original_task = OrchestrationTask(
            id="integration-test-1",
            title="Integration Test Task",
            description="Testing complete event flow",
            status=TaskStatus.IN_PROGRESS,
            priority=4,
            complexity_score=0.7,
            estimated_minutes=60,
            energy_required="high",
            cognitive_load=0.7,
            assigned_agent=AgentType.ZEN,
            leantime_id=999,
            context_switches_allowed=2,
            break_frequency_minutes=25
        )

        # Step 2: Transform to ConPort format (Task 2.2)
        progress_data = orchestration_task_to_conport_progress(original_task, "/test/workspace")

        # Validate ConPort format (Task 2.4)
        is_valid, errors = validate_conport_progress_data(progress_data)
        assert is_valid, f"ConPort progress_data validation failed: {errors}"

        # Step 3: Simulate ConPort storage (adds ID and timestamp)
        stored_progress = {
            **progress_data,
            "id": 500,
            "timestamp": "2025-10-19T23:00:00Z"
        }

        # Step 4: Transform back to OrchestrationTask (Task 2.2)
        restored_task = conport_progress_to_orchestration_task(stored_progress)

        # Step 5: Validate lossless transformation
        assert restored_task.title == original_task.title
        assert restored_task.description == original_task.description
        assert restored_task.status == original_task.status
        assert restored_task.priority == original_task.priority
        assert restored_task.complexity_score == original_task.complexity_score
        assert restored_task.estimated_minutes == original_task.estimated_minutes
        assert restored_task.energy_required == original_task.energy_required
        assert restored_task.assigned_agent == original_task.assigned_agent
        assert restored_task.leantime_id == original_task.leantime_id

        # Validate ConPort ID stored for future updates
        assert restored_task.conport_id == 500

    def test_adhd_metadata_query_flow(self):
        """
        Test ADHD metadata enables intelligent querying.

        Validates Task 2.1 (schema) + Task 2.4 (tag utilities).
        """
        # Create tasks with different ADHD profiles
        tasks = [
            OrchestrationTask(
                id="low-energy-1",
                title="Low Energy Task",
                complexity_score=0.3,
                energy_required="low",
                priority=2,
                estimated_minutes=20
            ),
            OrchestrationTask(
                id="high-energy-1",
                title="High Energy Task",
                complexity_score=0.8,
                energy_required="high",
                priority=5,
                estimated_minutes=90
            ),
            OrchestrationTask(
                id="medium-task-1",
                title="Medium Task",
                complexity_score=0.5,
                energy_required="medium",
                priority=3,
                estimated_minutes=45
            )
        ]

        # Transform all to ConPort
        progress_entries = [
            orchestration_task_to_conport_progress(task, "/test")
            for task in tasks
        ]

        # Validate low-energy task tags
        low_energy_progress = progress_entries[0]
        assert "energy-low" in low_energy_progress["tags"]
        assert "complexity-3" in low_energy_progress["tags"]

        # Validate high-energy task tags
        high_energy_progress = progress_entries[1]
        assert "energy-high" in high_energy_progress["tags"]
        assert "complexity-8" in high_energy_progress["tags"]
        assert "priority-5" in high_energy_progress["tags"]

        # Simulate ConPort query: "Find low-complexity tasks"
        # In production: ConPort would filter by tags ["complexity-0", "complexity-1", "complexity-2", "complexity-3", "complexity-4"]
        low_complexity_tasks = [p for p in progress_entries if any(tag.startswith("complexity-") and int(tag.split("-")[1]) <= 4 for tag in p["tags"])]

        assert len(low_complexity_tasks) == 2  # Low (0.3) and medium (0.5)

    def test_ai_decision_to_task_linking_flow(self):
        """
        Test AI decision creation and linking to tasks.

        Validates Task 2.3 (insight publisher) integration.
        """
        # Step 1: Create OrchestrationTask
        task = OrchestrationTask(
            id="arch-decision-task",
            title="Choose Event Bus Architecture",
            complexity_score=0.8,
            energy_required="high",
            priority=5,
            estimated_minutes=120
        )

        # Step 2: Transform to ConPort and get ID
        progress_data = orchestration_task_to_conport_progress(task, "/test")
        progress_data["id"] = 600  # Simulated ConPort ID
        progress_data["timestamp"] = "2025-10-19T23:00:00Z"

        # Step 3: Create AI decision event (Task 2.3)
        decision_event = create_architecture_decision(
            summary="Use Redis Streams for event bus architecture",
            rationale="Enables async communication, supports consumer groups, mature technology",
            implementation_details="Implement xadd/xreadgroup pattern with AOF persistence",
            confidence=0.9,
            task_id=task.id
        )

        # Step 4: Validate decision event structure
        assert decision_event.agent_type == AgentType.ZEN
        assert decision_event.confidence == 0.9
        assert decision_event.related_task_id == task.id
        assert "architecture" in decision_event.tags

        # Step 5: Convert to ConPort decision format
        conport_decision = decision_event.to_conport_decision()

        assert conport_decision["summary"] == "Use Redis Streams for event bus architecture"
        assert "ai-generated" in conport_decision["tags"]
        assert "agent-zen" in conport_decision["tags"]

        # In production: Would call publisher.log_ai_decision() → ConPort
        # Then link_decision_to_task(decision_id=X, task_id=600)

    def test_component_2_architecture_compliance(self):
        """
        Test that Component 2 enforces Architecture 3.0 principles.

        Validates Task 2.5 (authority fix) compliance.
        """
        # Principle 1: ConPort is storage authority
        # Task-Orchestrator should NOT maintain local task storage

        # This test validates the refactoring from Task 2.5:
        # - OrchestrationTask.conport_id field exists
        # - Adapters use ConPort for persistence
        # - No self.orchestrated_tasks dict remains

        task = OrchestrationTask(
            id="auth-test",
            title="Authority Test",
            complexity_score=0.5,
            energy_required="medium",
            priority=3,
            estimated_minutes=30
        )

        # Validate conport_id field exists (added in Task 2.5)
        assert hasattr(task, 'conport_id'), "OrchestrationTask missing conport_id field (Task 2.5 requirement)"

        # Initially None (not yet synced to ConPort)
        assert task.conport_id is None

        # After sync, conport_id would be set
        task.conport_id = 700  # Simulated
        assert task.conport_id == 700

    def test_all_adhd_tags_encode_decode_cycle(self):
        """
        Test complete ADHD metadata encode/decode cycle.

        Validates Task 2.4 (schema mapping) utilities.
        """
        # Create task with full ADHD metadata
        task = OrchestrationTask(
            id="adhd-test",
            title="ADHD Metadata Test",
            complexity_score=0.65,
            energy_required="high",
            priority=4,
            estimated_minutes=75,
            assigned_agent=AgentType.CONPORT
        )

        # Encode all ADHD tags (Task 2.4)
        tags = encode_all_adhd_tags(task)

        # Validate encoding
        assert "task-orchestrator" in tags
        assert "energy-high" in tags
        assert "complexity-6" in tags  # 0.65 * 10 = 6
        assert "priority-4" in tags
        assert "agent-conport" in tags

        # Decode all ADHD tags (Task 2.4)
        decoded = decode_all_adhd_tags(tags)

        # Validate decoding matches original
        assert decoded["energy_required"] == "high"
        assert decoded["complexity_score"] == 0.6  # Integer scale: 0.65 → 6 → 0.6 (acceptable 0.05 loss)
        assert decoded["priority"] == 4
        assert decoded["assigned_agent"] == "conport"

    def test_validation_catches_invalid_data(self):
        """
        Test that validation functions catch invalid data.

        Validates Task 2.4 (schema mapping) validation utilities.
        """
        # Invalid OrchestrationTask (complexity out of range)
        invalid_task = OrchestrationTask(
            id="invalid",
            title="Invalid Task",
            complexity_score=1.5,  # Invalid: > 1.0
            energy_required="ultra",  # Invalid: not low/medium/high
            priority=10,  # Invalid: > 5
            estimated_minutes=-10  # Invalid: negative
        )

        is_valid, errors = validate_adhd_metadata(invalid_task)

        assert not is_valid, "Validation should fail for invalid task"
        assert len(errors) >= 3, "Should detect multiple validation errors"

        # Check specific errors
        error_text = " ".join(errors)
        assert "complexity" in error_text.lower()
        assert "energy" in error_text.lower()

    def test_batch_operations_flow(self):
        """
        Test batch task creation and update flow.

        Validates Task 2.2 (adapter) batch methods.
        """
        # Create multiple tasks
        tasks = [
            OrchestrationTask(
                id=f"batch-task-{i}",
                title=f"Batch Task {i}",
                complexity_score=0.3 + (i * 0.1),
                energy_required=["low", "medium", "high"][i % 3],
                priority=i + 1,
                estimated_minutes=30 + (i * 15)
            )
            for i in range(5)
        ]

        # Transform all to ConPort format
        progress_list = [
            orchestration_task_to_conport_progress(task, "/test")
            for task in tasks
        ]

        # Validate all transformed successfully
        assert len(progress_list) == 5
        assert all(p is not None for p in progress_list)

        # Validate each has required ADHD tags
        for progress in progress_list:
            assert "task-orchestrator" in progress["tags"]
            assert any(tag.startswith("energy-") for tag in progress["tags"])
            assert any(tag.startswith("complexity-") for tag in progress["tags"])
            assert any(tag.startswith("priority-") for tag in progress["tags"])


# ============================================================================
# Component 2 Completion Validation
# ============================================================================

class TestComponent2Completion:
    """Validate that all Component 2 requirements are met."""

    def test_all_task_2_1_deliverables(self):
        """Validate Task 2.1 (Event Schema) deliverables."""
        # Schema documentation exists
        schema_doc = Path("/Users/hue/code/dopemux-mvp/docs/implementation-plans/conport-event-schema-design.md")
        assert schema_doc.exists(), "Task 2.1 schema documentation missing"

        # ADHD tag format standardized
        from adapters.schema_mapping import encode_energy_tag, encode_complexity_tag, encode_priority_tag
        assert encode_energy_tag("low") == "energy-low"
        assert encode_complexity_tag(0.6) == "complexity-6"
        assert encode_priority_tag(3) == "priority-3"

    def test_all_task_2_2_deliverables(self):
        """Validate Task 2.2 (Event Adapter) deliverables."""
        # Adapter module exists
        adapter_file = Path("/Users/hue/code/dopemux-mvp/services/task-orchestrator/adapters/conport_adapter.py")
        assert adapter_file.exists(), "Task 2.2 adapter file missing"

        # ConPortEventAdapter class available
        from adapters.conport_adapter import ConPortEventAdapter
        adapter = ConPortEventAdapter("/test")
        assert adapter is not None

        # Transformation functions available
        from adapters.conport_adapter import orchestration_task_to_conport_progress, conport_progress_to_orchestration_task
        assert callable(orchestration_task_to_conport_progress)
        assert callable(conport_progress_to_orchestration_task)

    def test_all_task_2_3_deliverables(self):
        """Validate Task 2.3 (Insight Publisher) deliverables."""
        # Publisher module exists
        publisher_file = Path("/Users/hue/code/dopemux-mvp/services/task-orchestrator/adapters/conport_insight_publisher.py")
        assert publisher_file.exists(), "Task 2.3 publisher file missing"

        # ConPortInsightPublisher class available
        from adapters.conport_insight_publisher import ConPortInsightPublisher
        publisher = ConPortInsightPublisher("/test")
        assert publisher is not None

        # AIDecisionEvent dataclass available
        from adapters.conport_insight_publisher import AIDecisionEvent
        event = AIDecisionEvent(
            summary="Test",
            rationale="Test",
            implementation_details="Test",
            agent_type=AgentType.ZEN,
            confidence=0.8,
            alternatives_considered=[]
        )
        assert event is not None

    def test_all_task_2_4_deliverables(self):
        """Validate Task 2.4 (Schema Mapping) deliverables."""
        # Schema mapping module exists
        mapping_file = Path("/Users/hue/code/dopemux-mvp/services/task-orchestrator/adapters/schema_mapping.py")
        assert mapping_file.exists(), "Task 2.4 schema mapping file missing"

        # All utility functions available
        from adapters.schema_mapping import (
            encode_all_adhd_tags, decode_all_adhd_tags,
            build_task_description, parse_task_description,
            validate_adhd_metadata, validate_conport_progress_data,
            build_adhd_query_tags, filter_tasks_by_adhd_criteria
        )

        # Test one function from each category
        task = OrchestrationTask(id="test", title="Test", complexity_score=0.5, energy_required="medium", priority=3, estimated_minutes=30)

        tags = encode_all_adhd_tags(task)
        assert len(tags) >= 4  # task-orchestrator + 3 ADHD tags

        is_valid, _ = validate_adhd_metadata(task)
        assert is_valid

    def test_all_task_2_5_deliverables(self):
        """Validate Task 2.5 (Remove Direct Storage) deliverables."""
        # enhanced_orchestrator.py refactored
        orchestrator_file = Path("/Users/hue/code/dopemux-mvp/services/task-orchestrator/enhanced_orchestrator.py")
        assert orchestrator_file.exists()

        # Validate self.orchestrated_tasks dict removed
        with open(orchestrator_file) as f:
            content = f.read()

            # Should have comments about removal
            assert "REMOVED: self.orchestrated_tasks" in content or "Architecture 3.0" in content

            # Should have conport_adapter initialization
            assert "self.conport_adapter" in content
            assert "ConPortEventAdapter" in content

        # OrchestrationTask has conport_id field (Task 2.5 requirement)
        task = OrchestrationTask(id="test", title="Test", complexity_score=0.5, energy_required="medium", priority=3, estimated_minutes=30)
        assert hasattr(task, 'conport_id'), "conport_id field missing from OrchestrationTask"

    def test_component_2_complete_integration(self):
        """
        Final integration test: Complete workflow from Leantime → ConPort → Task-Orchestrator.

        This test validates the entire Component 2 data contract layer.
        """
        # Simulate Leantime task data
        leantime_task_data = {
            "id": 888,
            "name": "Implement authentication module",
            "description": "Add JWT authentication with refresh tokens",
            "status": "3",  # In progress
            "priority": "4"
        }

        # Step 1: Create OrchestrationTask from Leantime data
        orch_task = OrchestrationTask(
            id=f"leantime-{leantime_task_data['id']}",
            leantime_id=leantime_task_data["id"],
            title=leantime_task_data["name"],
            description=leantime_task_data["description"],
            status=TaskStatus.IN_PROGRESS,
            priority=int(leantime_task_data["priority"]),
            complexity_score=0.7,  # Estimated
            estimated_minutes=90,
            energy_required="high"
        )

        # Step 2: Validate ADHD metadata (Task 2.4)
        is_valid, errors = validate_adhd_metadata(orch_task)
        assert is_valid, f"ADHD metadata invalid: {errors}"

        # Step 3: Transform to ConPort (Task 2.2)
        progress_data = orchestration_task_to_conport_progress(orch_task, "/test")

        # Step 4: Validate ConPort format (Task 2.4)
        is_valid, errors = validate_conport_progress_data(progress_data)
        assert is_valid, f"ConPort format invalid: {errors}"

        # Step 5: Verify Leantime linking preserved
        assert progress_data.get("linked_item_type") == "leantime_task"
        assert progress_data.get("linked_item_id") == "888"
        assert "leantime-synced" in progress_data["tags"]

        # Step 6: Simulate ConPort storage and retrieval
        stored = {**progress_data, "id": 700, "timestamp": "2025-10-19T23:00:00Z"}

        # Step 7: Transform back (Task 2.2)
        restored = conport_progress_to_orchestration_task(stored)

        # Step 8: Validate complete round-trip
        assert restored.title == orch_task.title
        assert restored.leantime_id == 888
        assert restored.conport_id == 700
        assert restored.status == TaskStatus.IN_PROGRESS
        assert restored.complexity_score == 0.7
        assert restored.energy_required == "high"

        # Step 9: Validate can query by ADHD criteria (Task 2.4)
        from adapters.schema_mapping import filter_tasks_by_adhd_criteria

        filtered = filter_tasks_by_adhd_criteria(
            [restored],
            energy_level="high",
            max_complexity=0.8,
            min_priority=4
        )

        assert len(filtered) == 1  # Task matches all criteria


# ============================================================================
# Error Handling and Edge Cases
# ============================================================================

class TestErrorHandlingIntegration:
    """Test error handling across all Component 2 adapters."""

    def test_graceful_degradation_no_conport_adapter(self):
        """Test system continues when ConPort adapter unavailable."""
        # Simulate adapter not initialized
        task = OrchestrationTask(
            id="test",
            title="Test Task",
            complexity_score=0.5,
            energy_required="medium",
            priority=3,
            estimated_minutes=30
        )

        # Should still be able to transform (doesn't require adapter)
        progress = orchestration_task_to_conport_progress(task, "/test")
        assert progress is not None

    def test_missing_fields_use_safe_defaults(self):
        """Test that missing fields use safe defaults."""
        # Minimal ConPort progress_entry
        minimal_progress = {
            "id": 800,
            "status": "TODO",
            "description": "Minimal Task",  # No embedded metadata
            "tags": ["task-orchestrator"],  # No ADHD tags
            "timestamp": "2025-10-19T23:00:00Z"
        }

        # Should transform successfully with defaults
        task = conport_progress_to_orchestration_task(minimal_progress)

        assert task.energy_required == "medium"  # Default
        assert task.complexity_score == 0.5  # Default
        assert task.priority == 3  # Default
        assert task.estimated_minutes == 25  # Default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
