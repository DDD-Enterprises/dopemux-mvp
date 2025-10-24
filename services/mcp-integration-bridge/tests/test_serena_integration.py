"""
Tests for Serena Integration
Validates event emission for complexity analysis and refactoring recommendations
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from event_bus import Event, EventBus
from integrations.serena import SerenaEventEmitter, SerenaIntegrationManager


class TestSerenaEventEmitter:
    """Test SerenaEventEmitter"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def emitter(self, event_bus_mock):
        """Create SerenaEventEmitter"""
        return SerenaEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            complexity_threshold=0.6
        )

    @pytest.mark.asyncio
    async def test_emits_high_complexity_event(self, emitter, event_bus_mock):
        """Test that high complexity events are emitted"""
        result = await emitter.emit_complexity_analyzed(
            file_path="/test/auth.py",
            complexity_score=0.7
        )

        assert result is True, "Should successfully emit event"
        assert event_bus_mock.publish.called, "Should call event_bus.publish"

        # Check event details
        call_args = event_bus_mock.publish.call_args
        stream = call_args[0][0]
        event = call_args[0][1]

        assert stream == "dopemux:events"
        assert event.type == "code.complexity.high"
        assert event.data["file"] == "/test/auth.py"
        assert event.data["complexity"] == 0.7
        assert event.source == "serena"

    @pytest.mark.asyncio
    async def test_no_event_below_threshold(self, emitter, event_bus_mock):
        """Test that events below threshold are not emitted"""
        result = await emitter.emit_complexity_analyzed(
            file_path="/test/simple.py",
            complexity_score=0.3  # Below 0.6 threshold
        )

        assert result is False, "Should not emit below threshold"
        assert not event_bus_mock.publish.called, "Should not publish event"

    @pytest.mark.asyncio
    async def test_emits_refactoring_recommendation(self, emitter, event_bus_mock):
        """Test refactoring recommendation event"""
        result = await emitter.emit_refactoring_recommended(
            file_path="/test/complex.py",
            complexity_score=0.8,
            reasons=["Too complex", "Hard to maintain"],
            recommended_actions=["Break into functions", "Add docs"],
            priority="high"
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "code.refactoring.recommended"
        assert event.data["priority"] == "high"
        assert len(event.data["reasons"]) == 2
        assert len(event.data["recommended_actions"]) == 2

    @pytest.mark.asyncio
    async def test_navigation_event_emission(self, emitter, event_bus_mock):
        """Test code navigation event"""
        result = await emitter.emit_code_navigation(
            from_symbol="authenticate",
            to_symbol="validate_token",
            navigation_type="goto_definition",
            success=True
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "code.navigation.performed"
        assert event.data["from_symbol"] == "authenticate"
        assert event.data["navigation_type"] == "goto_definition"

    @pytest.mark.asyncio
    async def test_events_can_be_disabled(self, event_bus_mock):
        """Test that events can be disabled"""
        emitter = SerenaEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            enable_events=False  # Disabled
        )

        result = await emitter.emit_complexity_analyzed(
            file_path="/test/file.py",
            complexity_score=0.9
        )

        assert result is False, "Should not emit when disabled"
        assert not event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, emitter):
        """Test that emission metrics are tracked"""
        # Reset metrics
        emitter.reset_metrics()

        # Emit some events
        await emitter.emit_complexity_analyzed("/test/file1.py", 0.7)
        await emitter.emit_complexity_analyzed("/test/file2.py", 0.8)
        await emitter.emit_refactoring_recommended(
            "/test/file3.py", 0.9, ["reason"], ["action"]
        )

        metrics = emitter.get_metrics()

        assert metrics["agent"] == "serena"
        assert metrics["events_emitted"] == 3
        assert metrics["high_complexity_events"] == 2
        assert metrics["refactoring_events"] == 1

    @pytest.mark.asyncio
    async def test_handles_publish_errors_gracefully(self, event_bus_mock):
        """Test that publish errors are handled gracefully"""
        # Make publish fail
        event_bus_mock.publish = AsyncMock(side_effect=Exception("Redis down"))

        emitter = SerenaEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace"
        )

        result = await emitter.emit_complexity_analyzed("/test/file.py", 0.7)

        assert result is False, "Should return False on error"
        assert emitter.emission_errors == 1, "Should track errors"


class TestSerenaIntegrationManager:
    """Test SerenaIntegrationManager"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def manager(self, event_bus_mock):
        """Create SerenaIntegrationManager"""
        return SerenaIntegrationManager(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            enable_complexity_events=True
        )

    @pytest.mark.asyncio
    async def test_handles_complexity_result(self, manager, event_bus_mock):
        """Test handling complexity analysis result"""
        await manager.handle_complexity_result(
            file_path="/test/auth.py",
            complexity_score=0.65,
            metrics={"nesting": 3, "lines": 150}
        )

        # Should emit complexity event
        assert event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_emits_refactoring_for_very_high_complexity(self, manager, event_bus_mock):
        """Test that very high complexity triggers refactoring recommendation"""
        await manager.handle_complexity_result(
            file_path="/test/complex.py",
            complexity_score=0.75  # >= 0.7 triggers refactoring
        )

        # Should emit both complexity AND refactoring events
        assert event_bus_mock.publish.call_count == 2

        # Check event types
        calls = event_bus_mock.publish.call_args_list
        event_types = [call[0][1].type for call in calls]

        assert "code.complexity.high" in event_types
        assert "code.refactoring.recommended" in event_types

    @pytest.mark.asyncio
    async def test_critical_priority_for_extreme_complexity(self, manager, event_bus_mock):
        """Test that extreme complexity gets critical priority"""
        await manager.handle_complexity_result(
            file_path="/test/extreme.py",
            complexity_score=0.85  # >= 0.8 should be high priority
        )

        # Find refactoring event
        calls = event_bus_mock.publish.call_args_list
        refactoring_event = None

        for call in calls:
            event = call[0][1]
            if event.type == "code.refactoring.recommended":
                refactoring_event = event
                break

        assert refactoring_event is not None
        assert refactoring_event.data["priority"] == "high"

    def test_get_metrics_returns_emitter_metrics(self, manager):
        """Test that manager returns emitter metrics"""
        metrics = manager.get_metrics()

        assert metrics["agent"] == "serena"
        assert "events_emitted" in metrics
        assert "complexity_threshold" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
