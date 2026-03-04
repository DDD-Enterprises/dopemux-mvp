#!/usr/bin/env python3
"""
Unit tests for ShieldCoordinator Core Logic

Tests parallel shield activation, false positive detection,
and comprehensive unit test coverage.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from interruption_shield.coordinator import ShieldCoordinator, ShieldConfig, ShieldState
from interruption_shield.shields import DNDShield, SlackShield, NotificationShield
from interruption_shield.monitor import ProductivityMonitor


class TestShieldCoordinator:
    """Test ShieldCoordinator core functionality"""

    @pytest.fixture
    def config(self):
        return ShieldConfig(
            enable_dnd=True,
            enable_slack=True,
            enable_notifications=True,
            monitoring_window_minutes=15,
            productivity_threshold=0.7
        )

    @pytest.fixture
    def coordinator(self, config):
        return ShieldCoordinator(config)

    @pytest.mark.asyncio
    async def test_initialization(self, coordinator, config):
        """Test coordinator initializes with correct configuration"""
        assert coordinator.config == config
        assert isinstance(coordinator.state, ShieldState)
        assert coordinator.state.dnd_active == False
        assert coordinator.state.slack_active == False
        assert coordinator.state.notifications_active == False

    @pytest.mark.asyncio
    async def test_parallel_shield_activation(self, coordinator):
        """Test that shields activate in parallel"""
        # Mock shields to return success
        coordinator.shields['dnd'] = Mock()
        coordinator.shields['dnd'].activate = AsyncMock(return_value={"success": True})
        coordinator.shields['slack'] = Mock()
        coordinator.shields['slack'].activate = AsyncMock(return_value={"success": True})
        coordinator.shields['notifications'] = Mock()
        coordinator.shields['notifications'].activate = AsyncMock(return_value={"success": True})

        # Mock productivity monitor
        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.8)

        result = await coordinator.activate_shields("Test activation")

        assert result["success"] == True
        assert "dnd" in result["results"]
        assert "slack" in result["results"]
        assert "notifications" in result["results"]
        assert result["productivity_baseline"] == 0.8
        assert result["activated_at"] is not None

        # Verify state was updated
        assert coordinator.state.dnd_active == True
        assert coordinator.state.slack_active == True
        assert coordinator.state.notifications_active == True

    @pytest.mark.asyncio
    async def test_false_positive_detection(self, coordinator):
        """Test false positive detection prevents premature deactivation"""
        # Set up activated state
        coordinator.state.activated_at = datetime.now()
        coordinator.state.productivity_baseline = 0.8
        coordinator.state.dnd_active = True

        # Mock low productivity (false positive)
        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.3)

        result = await coordinator.deactivate_shields("Test deactivation")

        assert result["success"] == False
        assert "false positive" in result["error"].lower()
        assert coordinator.state.false_positive_detected == True
        # Shields should remain active
        assert coordinator.state.dnd_active == True

    @pytest.mark.asyncio
    async def test_successful_deactivation(self, coordinator):
        """Test successful shield deactivation"""
        # Set up activated state
        coordinator.state.activated_at = datetime.now() - timedelta(minutes=30)  # Old activation
        coordinator.state.dnd_active = True
        coordinator.state.slack_active = True

        # Mock shields
        coordinator.shields['dnd'] = Mock()
        coordinator.shields['dnd'].deactivate = AsyncMock(return_value={"success": True})
        coordinator.shields['slack'] = Mock()
        coordinator.shields['slack'].deactivate = AsyncMock(return_value={"success": True})
        coordinator.shields['notifications'] = Mock()  # Not active, should be skipped

        # Mock no false positive (high productivity)
        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.9)

        result = await coordinator.deactivate_shields("Test deactivation")

        assert result["success"] == True
        assert result["deactivated_at"] is not None

        # Verify state was reset
        assert coordinator.state.dnd_active == False
        assert coordinator.state.slack_active == False
        assert coordinator.state.activated_at is None

    @pytest.mark.asyncio
    async def test_partial_activation_failure(self, coordinator):
        """Test handling of partial shield activation failures"""
        # Mock shields - one fails
        coordinator.shields['dnd'] = Mock()
        coordinator.shields['dnd'].activate = AsyncMock(return_value={"success": True})
        coordinator.shields['slack'] = Mock()
        coordinator.shields['slack'].activate = AsyncMock(return_value={"success": False, "error": "API error"})
        coordinator.shields['notifications'] = Mock()
        coordinator.shields['notifications'].activate = AsyncMock(return_value={"success": True})

        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.7)

        result = await coordinator.activate_shields("Test activation")

        assert result["success"] == False  # Overall failure due to slack failure
        assert result["results"]["dnd"]["success"] == True
        assert result["results"]["slack"]["success"] == False
        assert result["results"]["notifications"]["success"] == True

        # State should reflect partial success
        assert coordinator.state.dnd_active == True
        assert coordinator.state.slack_active == False  # Failed
        assert coordinator.state.notifications_active == True

    @pytest.mark.asyncio
    async def test_timeout_handling(self, coordinator):
        """Test timeout handling for slow shield activations"""
        # Set short timeout
        coordinator.config.activation_timeout_seconds = 0.1

        # Mock slow shield that actually takes time
        async def slow_activate(reason):
            await asyncio.sleep(0.2)  # Longer than timeout
            return {"success": True}

        coordinator.shields['dnd'] = Mock()
        coordinator.shields['dnd'].activate = slow_activate

        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.7)

        result = await coordinator.activate_shields("Test activation")

        assert result["success"] == False
        assert "timeout" in result["error"].lower()


class TestDNDShield:
    """Test DND Shield functionality"""

    @pytest.fixture
    def shield(self):
        return DNDShield()

    @pytest.mark.asyncio
    async def test_macos_activation(self, shield):
        """Test DND activation updates in-memory shield state."""
        result = await shield.activate("Test reason")

        assert result["success"] is True
        assert result["shield"] == "dnd"
        assert result["active"] is True
        assert result["reason"] == "Test reason"
        assert shield.active is True

    @pytest.mark.asyncio
    async def test_linux_activation(self, shield):
        """Test activation contract is platform-agnostic."""
        result = await shield.activate("Test reason")

        assert result["success"] is True
        assert result["shield"] == "dnd"
        assert shield.last_reason == "Test reason"

    @pytest.mark.asyncio
    async def test_windows_activation(self, shield):
        """Test deactivation resets the active flag."""
        await shield.activate("Test reason")
        result = await shield.deactivate("Done")

        assert result["success"] is True
        assert result["shield"] == "dnd"
        assert result["active"] is False
        assert shield.active is False

    @pytest.mark.asyncio
    async def test_unsupported_system(self, shield):
        """Test status reporting for an idle shield."""
        result = await shield.get_status()

        assert result["success"] is True
        assert result["shield"] == "dnd"
        assert result["active"] is False
        assert result["last_changed_at"] is None


class TestProductivityMonitor:
    """Test ProductivityMonitor functionality"""

    @pytest.fixture
    def monitor(self):
        return ProductivityMonitor(window_minutes=15, threshold=0.7)

    @pytest.mark.asyncio
    async def test_initial_state(self, monitor):
        """Test monitor initial state"""
        assert monitor.window_minutes == 15
        assert monitor.threshold == 0.7
        assert monitor._samples == []
        assert monitor._last_sample_at == ""

    @pytest.mark.asyncio
    async def test_add_sample_tracks_recent_scores(self, monitor):
        """Test adding productivity samples updates rolling state."""
        await monitor.add_sample(0.8)
        await monitor.add_sample(0.6)

        assert monitor._samples == [0.8, 0.6]
        assert monitor._last_sample_at

    @pytest.mark.asyncio
    async def test_productivity_calculation(self, monitor):
        """Test productivity score calculation"""
        await monitor.add_sample(0.8)
        await monitor.add_sample(0.6)
        productivity = await monitor.get_current_productivity()
        assert productivity == pytest.approx(0.7)

    @pytest.mark.asyncio
    async def test_default_productivity_without_samples(self, monitor):
        """Test default neutral productivity when no samples exist."""
        productivity = await monitor.get_current_productivity()
        assert productivity == pytest.approx(0.75)

    def test_metrics_summary(self, monitor):
        """Test monitor stores configured thresholds."""
        assert monitor.window_minutes == 15
        assert monitor.threshold == 0.7


if __name__ == "__main__":
    pytest.main([__file__])
