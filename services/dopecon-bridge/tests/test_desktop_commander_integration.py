"""
Tests for Desktop Commander Integration
Validates workspace switch events and context loss detection
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from event_bus import Event, EventBus
from integrations.desktop_commander import (
    DesktopCommanderEventEmitter,
    DesktopCommanderIntegrationManager
)


class TestDesktopCommanderEventEmitter:
    """Test DesktopCommanderEventEmitter"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def emitter(self, event_bus_mock):
        """Create DesktopCommanderEventEmitter"""
        return DesktopCommanderEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace"
        )

    @pytest.mark.asyncio
    async def test_emits_workspace_switched_event(self, emitter, event_bus_mock):
        """Test workspace switch event emission"""
        result = await emitter.emit_workspace_switched(
            from_workspace="/workspace/project-a",
            to_workspace="/workspace/project-b",
            switch_type="manual"
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "workspace.switched"
        assert event.data["from_workspace"] == "/workspace/project-a"
        assert event.data["to_workspace"] == "/workspace/project-b"
        assert event.data["switch_type"] == "manual"
        assert event.source == "desktop-commander"

    @pytest.mark.asyncio
    async def test_emits_context_lost_event(self, emitter, event_bus_mock):
        """Test context loss event emission"""
        result = await emitter.emit_context_lost(
            workspace="/workspace/project-a",
            reason="unexpected_switch",
            recovery_data={"last_file": "auth.py", "cursor_line": 42}
        )

        assert result is True
        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "context.lost"
        assert event.data["workspace"] == "/workspace/project-a"
        assert event.data["reason"] == "unexpected_switch"
        assert event.data["severity"] == "high"

    @pytest.mark.asyncio
    async def test_tracks_recent_switches(self, emitter, event_bus_mock):
        """Test that recent switches are tracked"""
        await emitter.emit_workspace_switched("/ws/a", "/ws/b", "manual")
        await emitter.emit_workspace_switched("/ws/b", "/ws/c", "manual")
        await emitter.emit_workspace_switched("/ws/c", "/ws/a", "manual")

        assert len(emitter.recent_switches) == 3

    @pytest.mark.asyncio
    async def test_limits_recent_switches_to_10(self, emitter, event_bus_mock):
        """Test that recent switches are limited to 10"""
        # Emit 15 switch events
        for i in range(15):
            await emitter.emit_workspace_switched(f"/ws/{i}", f"/ws/{i+1}", "manual")

        # Should only keep last 10
        assert len(emitter.recent_switches) == 10

    def test_calculates_switch_frequency(self, emitter):
        """Test switch frequency calculation"""
        # Add switches over known time period
        now = datetime.utcnow()

        # Add 12 switches over 1 hour (12/hour)
        for i in range(12):
            timestamp = (now - timedelta(minutes=60 - i*5)).isoformat() + "Z"
            emitter.recent_switches.append({
                "from": f"/ws/{i}",
                "to": f"/ws/{i+1}",
                "timestamp": timestamp,
                "type": "manual"
            })

        frequency = emitter.get_switch_frequency(time_window_minutes=60)

        # Should be approximately 12 switches per hour
        assert 10 <= frequency <= 14, f"Expected ~12/hour, got {frequency}"

    @pytest.mark.asyncio
    async def test_events_can_be_disabled(self, event_bus_mock):
        """Test that events can be disabled"""
        emitter = DesktopCommanderEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            enable_events=False
        )

        result = await emitter.emit_workspace_switched("/ws/a", "/ws/b")

        assert result is False
        assert not event_bus_mock.publish.called

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, emitter):
        """Test metrics tracking"""
        emitter.reset_metrics()

        await emitter.emit_workspace_switched("/ws/a", "/ws/b", "manual")
        await emitter.emit_workspace_switched("/ws/b", "/ws/c", "forced")
        await emitter.emit_context_lost("/ws/c", "unexpected")

        metrics = emitter.get_metrics()

        assert metrics["agent"] == "desktop-commander"
        assert metrics["events_emitted"] == 3
        assert metrics["switch_events"] == 2
        assert metrics["context_lost_events"] == 1
        assert "switches_per_hour" in metrics

    @pytest.mark.asyncio
    async def test_handles_publish_errors_gracefully(self, event_bus_mock):
        """Test graceful error handling"""
        event_bus_mock.publish = AsyncMock(side_effect=Exception("EventBus down"))

        emitter = DesktopCommanderEventEmitter(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace"
        )

        result = await emitter.emit_workspace_switched("/ws/a", "/ws/b")

        assert result is False
        assert emitter.emission_errors == 1


class TestDesktopCommanderIntegrationManager:
    """Test DesktopCommanderIntegrationManager"""

    @pytest.fixture
    async def event_bus_mock(self):
        """Create mock EventBus"""
        bus = Mock(spec=EventBus)
        bus.publish = AsyncMock(return_value="msg-123")
        return bus

    @pytest.fixture
    def manager(self, event_bus_mock):
        """Create DesktopCommanderIntegrationManager"""
        return DesktopCommanderIntegrationManager(
            event_bus=event_bus_mock,
            workspace_id="/test/workspace",
            excessive_switch_threshold=10
        )

    @pytest.mark.asyncio
    async def test_handles_workspace_switch(self, manager, event_bus_mock):
        """Test handling workspace switch"""
        await manager.handle_workspace_switch(
            from_workspace="/workspace/project-a",
            to_workspace="/workspace/project-b",
            switch_type="manual",
            context_data={"file": "auth.py", "line": 42}
        )

        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "workspace.switched"

    @pytest.mark.asyncio
    async def test_handles_context_loss(self, manager, event_bus_mock):
        """Test handling context loss"""
        await manager.handle_context_loss(
            workspace="/workspace/project-a",
            reason="unexpected_close",
            recovery_data={"unsaved_changes": True}
        )

        assert event_bus_mock.publish.called

        call_args = event_bus_mock.publish.call_args
        event = call_args[0][1]

        assert event.type == "context.lost"
        assert event.data["severity"] == "high"

    @pytest.mark.asyncio
    async def test_warns_on_excessive_switching(self, manager, event_bus_mock, caplog):
        """Test that excessive switching triggers warning"""
        # Add many recent switches to emitter
        now = datetime.utcnow()

        for i in range(15):
            timestamp = (now - timedelta(minutes=60 - i*4)).isoformat() + "Z"
            manager.emitter.recent_switches.append({
                "from": f"/ws/{i}",
                "to": f"/ws/{i+1}",
                "timestamp": timestamp,
                "type": "manual"
            })

        # Handle another switch (should trigger warning)
        with caplog.at_level("WARNING"):
            await manager.handle_workspace_switch("/ws/15", "/ws/16")

        # Check for warning about excessive switching
        assert any("Excessive workspace switching" in record.message for record in caplog.records)

    def test_get_metrics_includes_threshold(self, manager):
        """Test that metrics include threshold"""
        metrics = manager.get_metrics()

        assert metrics["agent"] == "desktop-commander"
        assert "excessive_switch_threshold" in metrics
        assert metrics["excessive_switch_threshold"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
