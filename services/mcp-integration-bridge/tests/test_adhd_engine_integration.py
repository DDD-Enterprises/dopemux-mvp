"""
Tests for ADHD Engine Integration
Validates event buffering, overload detection, and break recommendations
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, AsyncMock

from event_bus import Event, EventBus
from integrations.adhd_engine import (
    ADHDEventBuffer,
    ADHDEngineEventEmitter,
    ADHDEngineIntegrationManager
)


class TestADHDEventBuffer:
    """Test ADHDEventBuffer"""

    def test_buffer_state_stores_latest(self):
        """Test that buffer stores only latest state"""
        buffer = ADHDEventBuffer(flush_interval_seconds=30)

        state1 = {"attention": "focused", "load": 0.5}
        state2 = {"attention": "scattered", "load": 0.8}

        buffer.buffer_state(state1)
        buffer.buffer_state(state2)

        # Should only have latest
        buffered = buffer.get_buffered_state()
        assert buffered == state2

    def test_should_flush_after_interval(self):
        """Test flush timing"""
        buffer = ADHDEventBuffer(flush_interval_seconds=1)

        assert buffer.should_flush() is False  # Just created

        time.sleep(1.1)  # Wait for interval

        assert buffer.should_flush() is True

    def test_get_buffered_state_clears_buffer(self):
        """Test that getting state clears the buffer"""
        buffer = ADHDEventBuffer(flush_interval_seconds=1)

        buffer.buffer_state({"test": "data"})
        state = buffer.get_buffered_state()

        assert state == {"test": "data"}

        # Buffer should now be empty
        state2 = buffer.get_buffered_state()
        assert state2 is None


class TestADHDEngineEventEmitter:
    """Test ADHDEngineEventEmitter"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def emitter(self, event_bus_mock):
        """Create ADHDEngineEventEmitter"""
        return ADHDEngineEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            buffer_interval_seconds=1  # Short interval for testing
        )

    @pytest.mark.asyncio
    async def test_buffers_state_changes(self, emitter):
        """Test that state changes are buffered"""
        await emitter.buffer_state_change("focused", "high", 0.5)

        # Should be buffered, not emitted yet
        assert emitter.buffer.buffered_state is not None

    @pytest.mark.asyncio
    async def test_flush_emits_buffered_state(self, emitter, event_bus_mock):
        """Test that flush emits buffered state"""
        await emitter.buffer_state_change("focused", "high", 0.5)

        # Wait for flush interval
        await asyncio.sleep(1.1)

        # Flush
        result = await emitter.flush_buffered_state()

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "cognitive.state.changed"
        assert event.data["attention_state"] == "focused"
        assert event.data["cognitive_load"] == 0.5

    @pytest.mark.asyncio
    async def test_emits_overload_immediately(self, emitter, event_bus_mock):
        """Test that overload events are emitted immediately (not buffered)"""
        result = await emitter.emit_overload_detected(
            cognitive_load=0.9,
            trigger="too_many_tasks"
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "adhd.overload.detected"
        assert event.data["cognitive_load"] == 0.9
        assert event.data["severity"] == "critical"  # >= 0.9

    @pytest.mark.asyncio
    async def test_no_overload_below_threshold(self, emitter, event_bus_mock):
        """Test that overload not emitted below threshold"""
        result = await emitter.emit_overload_detected(
            cognitive_load=0.6,  # Below 0.8 threshold
            trigger="test"
        )

        assert result is False
        assert not event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_emits_break_recommended(self, emitter, event_bus_mock):
        """Test break recommendation event"""
        result = await emitter.emit_break_recommended(
            session_duration_minutes=45,
            last_break_minutes_ago=45,
            reason="session_duration"
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "break.recommended"
        assert event.data["session_duration_minutes"] == 45
        assert event.data["recommended_break_duration"] == 10  # 45min session = 10min break

    @pytest.mark.asyncio
    async def test_break_duration_scales_with_session(self, emitter):
        """Test that break duration scales with session length"""
        # 30 min session
        duration_30 = emitter._calculate_break_duration(30)
        assert duration_30 == 5

        # 60 min session
        duration_60 = emitter._calculate_break_duration(60)
        assert duration_60 == 10

        # 120 min session
        duration_120 = emitter._calculate_break_duration(120)
        assert duration_120 == 15

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, emitter):
        """Test metrics tracking"""
        emitter.reset_metrics()

        await emitter.buffer_state_change("focused", "high", 0.5)
        await asyncio.sleep(1.1)
        await emitter.flush_buffered_state()

        await emitter.emit_overload_detected(0.9, "trigger")
        await emitter.emit_break_recommended(45, 45)

        metrics = emitter.get_metrics()

        assert metrics["agent"] == "adhd-engine"
        assert metrics["events_emitted"] == 3
        assert metrics["state_change_events"] == 1
        assert metrics["overload_events"] == 1
        assert metrics["break_events"] == 1


class TestADHDEngineIntegrationManager:
    """Test ADHDEngineIntegrationManager"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def manager(self, event_bus_mock):
        """Create ADHDEngineIntegrationManager"""
        return ADHDEngineIntegrationManager(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            buffer_interval_seconds=1
        )

    @pytest.mark.asyncio
    async def test_handles_state_update(self, manager):
        """Test handling state update"""
        await manager.handle_state_update(
            attention_state="focused",
            energy_level="high",
            cognitive_load=0.5
        )

        # Should be buffered
        assert manager.emitter.buffer.buffered_state is not None

    @pytest.mark.asyncio
    async def test_handles_overload_immediately(self, manager, event_bus_mock):
        """Test that overload is handled immediately"""
        await manager.handle_state_update(
            attention_state="scattered",
            energy_level="low",
            cognitive_load=0.9  # Overload!
        )

        # Should emit overload event immediately
        calls = event_bus_mock.publish.call_args_list
        overload_events = [
            call for call in calls
            if call[0][1].type == "adhd.overload.detected"
        ]

        assert len(overload_events) == 1

    @pytest.mark.asyncio
    async def test_background_worker_flushes_automatically(self, manager, event_bus_mock):
        """Test that background worker flushes buffered states"""
        # Start worker
        await manager.start_background_worker()

        # Buffer a state
        await manager.handle_state_update("focused", "high", 0.5)

        # Wait for flush interval + processing time
        await asyncio.sleep(1.5)

        # Stop worker
        await manager.stop_background_worker()

        # Should have emitted state change
        calls = event_bus_mock.publish.call_args_list
        state_events = [
            call for call in calls
            if call[0][1].type == "cognitive.state.changed"
        ]

        assert len(state_events) >= 1

    def test_get_metrics_includes_buffer_status(self, manager):
        """Test that metrics include buffer status"""
        metrics = manager.get_metrics()

        assert "agent" in metrics
        assert metrics["agent"] == "adhd-engine"
        assert "buffer" in metrics
        assert "background_worker_running" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
