"""
Tests for Task-Orchestrator Integration
Validates task progress event emission and bidirectional communication
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock

from event_bus import Event, EventBus
from integrations.task_orchestrator import (
    TaskOrchestratorEventEmitter,
    TaskOrchestratorIntegrationManager
)


class TestTaskOrchestratorEventEmitter:
    """Test TaskOrchestratorEventEmitter"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def emitter(self, event_bus_mock):
        """Create TaskOrchestratorEventEmitter"""
        return TaskOrchestratorEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace"
        )

    @pytest.mark.asyncio
    async def test_emits_task_progress_updated(self, emitter, event_bus_mock):
        """Test task progress update event"""
        result = await emitter.emit_task_progress_updated(
            task_id="task-123",
            task_title="Implement authentication",
            old_status="TODO",
            new_status="IN_PROGRESS",
            progress_percentage=25.0,
            complexity=0.6,
            energy_required="high"
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "task.progress.updated"
        assert event.data["task_id"] == "task-123"
        assert event.data["new_status"] == "IN_PROGRESS"
        assert event.data["status_transition"] == "TODO → IN_PROGRESS"
        assert event.source == "task-orchestrator"

    @pytest.mark.asyncio
    async def test_emits_task_completed(self, emitter, event_bus_mock):
        """Test task completion event"""
        result = await emitter.emit_task_completed(
            task_id="task-123",
            task_title="Implement authentication",
            duration_minutes=45,
            complexity=0.6
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "task.completed"
        assert event.data["duration_minutes"] == 45
        assert "completion_timestamp" in event.data

    @pytest.mark.asyncio
    async def test_emits_task_blocked(self, emitter, event_bus_mock):
        """Test task blocked event"""
        result = await emitter.emit_task_blocked(
            task_id="task-123",
            task_title="Deploy to production",
            blocker_reason="Waiting for infrastructure setup"
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "task.blocked"
        assert event.data["blocker_reason"] == "Waiting for infrastructure setup"
        assert event.data["severity"] == "medium"

    @pytest.mark.asyncio
    async def test_tracks_completion_events_separately(self, emitter):
        """Test that completion events are tracked separately"""
        emitter.reset_metrics()

        await emitter.emit_task_progress_updated(
            "t1", "Task 1", "TODO", "IN_PROGRESS"
        )
        await emitter.emit_task_progress_updated(
            "t1", "Task 1", "IN_PROGRESS", "DONE"  # Completion
        )

        metrics = emitter.get_metrics()

        assert metrics["progress_events"] == 2
        assert metrics["completion_events"] == 1  # DONE status tracked

    @pytest.mark.asyncio
    async def test_tracks_blocked_events_separately(self, emitter):
        """Test that blocked events are tracked separately"""
        emitter.reset_metrics()

        await emitter.emit_task_progress_updated(
            "t1", "Task 1", "IN_PROGRESS", "BLOCKED"
        )
        await emitter.emit_task_blocked("t2", "Task 2", "Dependencies missing")

        metrics = emitter.get_metrics()

        assert metrics["blocked_events"] == 2  # Both tracked

    @pytest.mark.asyncio
    async def test_events_can_be_disabled(self, event_bus_mock):
        """Test that events can be disabled"""
        emitter = TaskOrchestratorEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            enable_events=False
        )

        result = await emitter.emit_task_progress_updated(
            "t1", "Task", "TODO", "IN_PROGRESS"
        )

        assert result is False
        assert not event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, emitter):
        """Test metrics tracking"""
        emitter.reset_metrics()

        await emitter.emit_task_progress_updated("t1", "Task 1", "TODO", "IN_PROGRESS")
        await emitter.emit_task_progress_updated("t1", "Task 1", "IN_PROGRESS", "DONE")
        await emitter.emit_task_blocked("t2", "Task 2", "Blocked")

        metrics = emitter.get_metrics()

        assert metrics["agent"] == "task-orchestrator"
        assert metrics["events_emitted"] == 3
        assert metrics["progress_events"] == 2
        assert metrics["completion_events"] == 1
        assert metrics["blocked_events"] == 1


class TestTaskOrchestratorIntegrationManager:
    """Test TaskOrchestratorIntegrationManager"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def manager(self, event_bus_mock):
        """Create TaskOrchestratorIntegrationManager"""
        return TaskOrchestratorIntegrationManager(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace"
        )

    @pytest.mark.asyncio
    async def test_handles_task_status_change(self, manager, event_bus_mock):
        """Test handling task status change"""
        await manager.handle_task_status_change(
            task_id="task-123",
            task_title="Implement feature",
            old_status="TODO",
            new_status="IN_PROGRESS",
            progress_percentage=10.0,
            complexity=0.5
        )

        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "task.progress.updated"

    @pytest.mark.asyncio
    async def test_emits_completion_event_when_done(self, manager, event_bus_mock):
        """Test that DONE status triggers completion event"""
        await manager.handle_task_status_change(
            task_id="task-123",
            task_title="Task",
            old_status="IN_PROGRESS",
            new_status="DONE"
        )

        # Should emit both progress_updated AND task_completed
        assert event_bus_mock.publish.call_count == 2

        event_types = [
            call[0][1].type
            for call in event_bus_mock.publish.call_args_list
        ]

        assert "task.progress.updated" in event_types
        assert "task.completed" in event_types

    @pytest.mark.asyncio
    async def test_emits_blocked_event_when_blocked(self, manager, event_bus_mock):
        """Test that BLOCKED status triggers blocked event"""
        await manager.handle_task_status_change(
            task_id="task-123",
            task_title="Task",
            old_status="IN_PROGRESS",
            new_status="BLOCKED"
        )

        # Should emit both progress_updated AND task_blocked
        assert event_bus_mock.publish.call_count == 2

        event_types = [
            call[0][1].type
            for call in event_bus_mock.publish.call_args_list
        ]

        assert "task.progress.updated" in event_types
        assert "task.blocked" in event_types

    def test_get_metrics_returns_emitter_metrics(self, manager):
        """Test that manager returns emitter metrics"""
        metrics = manager.get_metrics()

        assert metrics["agent"] == "task-orchestrator"
        assert "events_emitted" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
