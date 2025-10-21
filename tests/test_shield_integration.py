#!/usr/bin/env python3
"""
Integration Tests for Environmental Interruption Shield

Tests full shield coordinator with ConPort integration:
- End-to-end shield activation/deactivation workflows
- ConPort event logging and state storage
- Productivity monitoring and false positive detection
- Circuit breaker functionality for degraded ConPort operation
- ADHD-optimized performance validation (fast timeouts, graceful degradation)

Integration Test Coverage:
- ConPort HTTP client integration
- Shield state persistence and retrieval
- Event logging for debugging and analytics
- Fallback behavior when ConPort unavailable
- Parallel shield operations with error handling
"""

import asyncio
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import httpx

from interruption_shield.coordinator import ShieldCoordinator, ShieldConfig, ShieldState
from interruption_shield.conport_client import ShieldConPortClient, get_shield_conport_client
from interruption_shield.shields import DNDShield, SlackShield, NotificationShield
from interruption_shield.monitor import ProductivityMonitor


class TestShieldConPortIntegration:
    """Test ConPort integration for shield event logging"""

    @pytest.fixture
    def conport_client(self):
        return ShieldConPortClient("test_workspace", "http://localhost:3016")

    @pytest.mark.asyncio
    async def test_shield_activation_logging(self, conport_client):
        """Test logging shield activation to ConPort progress entries"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "progress_123", "status": "success"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

            result = await conport_client.log_shield_activation(
                "Test focused work",
                {"dnd": {"success": True}, "slack": {"success": True}},
                0.8,
                datetime.now()
            )

            assert result == True
            # Verify HTTP call was made
            mock_client.return_value.__aenter__.return_value.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_conport_fallback_on_failure(self, conport_client):
        """Test fallback logging when ConPort is unavailable"""
        # Mock failed HTTP response
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timeout")
            )

            result = await conport_client.log_shield_activation(
                "Test work",
                {"dnd": {"success": True}},
                0.7,
                datetime.now()
            )

            assert result == False
            # Verify fallback log contains the event
            fallback_log = conport_client.get_fallback_log()
            assert len(fallback_log) == 1
            assert fallback_log[0]["operation"] == "🛡️ Activated interruption shields: Test work"

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, conport_client):
        """Test circuit breaker opens after repeated failures"""
        # Mock HTTP failures
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=Exception("Network error")
            )

            # Trigger multiple failures to open circuit breaker
            for _ in range(4):  # More than threshold of 3
                await conport_client._call_conport_api("POST", "/test", {}, "test operation")

            # Verify circuit breaker is open (should have opened after 3 failures)
            assert conport_client.circuit_open == True

    @pytest.mark.asyncio
    async def test_shield_state_storage(self, conport_client):
        """Test storing shield state in ConPort custom data"""
        mock_response = Mock()
        mock_response.status_code = 201

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

            state_data = {
                "dnd_active": True,
                "slack_active": False,
                "notifications_active": True,
                "activated_at": datetime.now().isoformat(),
                "productivity_baseline": 0.8
            }

            result = await conport_client.store_shield_state(state_data)

            assert result == True
            # Verify the request was made with correct data
            call_args = mock_client.return_value.__aenter__.return_value.request.call_args
            request_data = json.loads(call_args[1]['content'])
            assert request_data["category"] == "interruption_shield_state"
            assert request_data["key"] == "current_state"


class TestFullShieldCoordinatorIntegration:
    """Test complete shield coordinator with all integrations"""

    @pytest.fixture
    def config(self):
        return ShieldConfig(
            enable_dnd=True,
            enable_slack=True,
            enable_notifications=True,
            conport_workspace_id="/Users/hue/code/dopemux-mvp",
            monitoring_window_minutes=15,
            productivity_threshold=0.7
        )

    @pytest.fixture
    def coordinator(self, config):
        return ShieldCoordinator(config)

    @pytest.mark.asyncio
    async def test_end_to_end_shield_workflow(self, coordinator):
        """Test complete shield activation and deactivation workflow"""
        # Mock all shield activations to succeed
        for shield_name in ['dnd', 'slack', 'notifications']:
            if coordinator.shields[shield_name]:
                coordinator.shields[shield_name].activate = AsyncMock(return_value={"success": True})
                coordinator.shields[shield_name].deactivate = AsyncMock(return_value={"success": True})

        # Mock productivity monitor
        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.8)

        # Mock ConPort client
        coordinator.conport_client = Mock()
        coordinator.conport_client.log_shield_activation = AsyncMock(return_value=True)
        coordinator.conport_client.store_shield_state = AsyncMock(return_value=True)
        coordinator.conport_client.log_shield_deactivation = AsyncMock(return_value=True)

        # Test activation
        activation_result = await coordinator.activate_shields("Integration test")

        assert activation_result["success"] == True
        assert coordinator.state.dnd_active == True
        assert coordinator.state.slack_active == True
        assert coordinator.state.notifications_active == True
        assert coordinator.state.activated_at is not None

        # Verify ConPort logging was called
        coordinator.conport_client.log_shield_activation.assert_called_once()
        coordinator.conport_client.store_shield_state.assert_called()

        # Mock deactivation scenario (no false positive)
        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.9)  # High productivity

        # Test deactivation
        deactivation_result = await coordinator.deactivate_shields("Test complete")

        assert deactivation_result["success"] == True
        assert coordinator.state.dnd_active == False
        assert coordinator.state.slack_active == False
        assert coordinator.state.notifications_active == False
        assert coordinator.state.activated_at is None

        # Verify deactivation logging
        coordinator.conport_client.log_shield_deactivation.assert_called_once()

    @pytest.mark.asyncio
    async def test_false_positive_prevention_integration(self, coordinator):
        """Test false positive detection in integrated workflow"""
        # Set up activated state
        coordinator.state.activated_at = datetime.now() - timedelta(minutes=10)  # Within monitoring window
        coordinator.state.productivity_baseline = 0.8
        coordinator.state.dnd_active = True

        # Mock shields
        coordinator.shields['dnd'].deactivate = AsyncMock(return_value={"success": True})

        # Mock low productivity (false positive condition)
        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.4)  # Significant drop

        # Mock ConPort event logging
        coordinator.conport_client = Mock()
        coordinator.conport_client.log_shield_event = AsyncMock(return_value=True)
        coordinator.conport_client.log_shield_deactivation = AsyncMock(return_value=True)

        # Attempt deactivation - should be prevented
        result = await coordinator.deactivate_shields("False positive test")

        assert result["success"] == False
        assert "false positive" in result["error"].lower()
        assert coordinator.state.false_positive_detected == True
        assert coordinator.state.dnd_active == True  # Shields remain active

        # Verify false positive event was logged
        coordinator.conport_client.log_shield_event.assert_called()
        call_args = coordinator.conport_client.log_shield_event.call_args
        assert call_args[0][0] == "false_positive"  # event_type

    @pytest.mark.asyncio
    async def test_conport_failure_graceful_degradation(self, coordinator):
        """Test graceful degradation when ConPort is unavailable"""
        # Mock all shield operations
        for shield_name in ['dnd', 'slack', 'notifications']:
            if coordinator.shields[shield_name]:
                coordinator.shields[shield_name].activate = AsyncMock(return_value={"success": True})

        # Mock productivity
        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.8)

        # Mock ConPort client failures (simulate network issues)
        coordinator.conport_client = Mock()
        coordinator.conport_client.log_shield_activation = AsyncMock(return_value=False)  # ConPort down
        coordinator.conport_client.store_shield_state = AsyncMock(return_value=False)

        # Shield activation should still work despite ConPort failure
        result = await coordinator.activate_shields("ConPort failure test")

        assert result["success"] == True  # Shields still activate
        assert coordinator.state.dnd_active == True  # State updated
        # But logging failed
        coordinator.conport_client.log_shield_activation.assert_called_once()

    @pytest.mark.asyncio
    async def test_shield_status_reporting_integration(self, coordinator):
        """Test integrated shield status reporting"""
        # Set up some state
        coordinator.state.dnd_active = True
        coordinator.state.activated_at = datetime.now()
        coordinator.state.productivity_baseline = 0.75

        # Mock individual shield status checks
        coordinator.shields['dnd'].get_status = AsyncMock(return_value={
            "active": True, "system": "Darwin", "method": "defaults"
        })
        coordinator.shields['slack'].get_status = AsyncMock(return_value={
            "configured": False, "error": "No token"
        })

        status = await coordinator.get_shield_status()

        # Verify overall state
        assert status["state"]["dnd_active"] == True
        assert status["state"]["activated_at"] is not None
        assert status["state"]["productivity_baseline"] == 0.75

        # Verify individual shield status
        assert status["shields"]["dnd"]["active"] == True
        assert status["shields"]["slack"]["configured"] == False

    @pytest.mark.asyncio
    async def test_adhd_performance_requirements(self, coordinator):
        """Test ADHD-optimized performance requirements"""
        import time

        # Mock all shields with realistic timing
        async def slow_activate(reason):
            await asyncio.sleep(0.1)  # Simulate real shield activation time
            return {"success": True}

        for shield_name in ['dnd', 'slack', 'notifications']:
            if coordinator.shields[shield_name]:
                coordinator.shields[shield_name].activate = slow_activate

        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.8)

        # Measure activation time
        start_time = time.time()
        result = await coordinator.activate_shields("Performance test")
        end_time = time.time()

        activation_time = end_time - start_time

        # ADHD requirement: shield activation should complete within 5 seconds
        # (allowing time for all parallel operations)
        assert activation_time < 5.0, f"Activation took {activation_time:.2f}s, exceeds 5s limit"
        assert result["success"] == True

    @pytest.mark.asyncio
    async def test_callback_system_integration(self, coordinator):
        """Test state change callback system"""
        callback_results = []

        def test_callback(state: ShieldState):
            callback_results.append({
                "dnd_active": state.dnd_active,
                "slack_active": state.slack_active,
                "timestamp": datetime.now()
            })

        # Register callback
        coordinator.add_state_change_callback(test_callback)

        # Mock shield operations
        for shield_name in ['dnd', 'slack', 'notifications']:
            if coordinator.shields[shield_name]:
                coordinator.shields[shield_name].activate = AsyncMock(return_value={"success": True})

        coordinator.monitor.get_current_productivity = AsyncMock(return_value=0.8)

        # Mock ConPort client to prevent HTTP calls
        coordinator.conport_client = Mock()
        coordinator.conport_client.log_shield_activation = AsyncMock(return_value=True)
        coordinator.conport_client.store_shield_state = AsyncMock(return_value=True)

        # Trigger state change
        await coordinator.activate_shields("Callback test")

        # Verify callback was called
        assert len(callback_results) == 1
        assert callback_results[0]["dnd_active"] == True
        assert callback_results[0]["slack_active"] == True


class TestConPortClientGlobalInstance:
    """Test global ConPort client instance management"""

    @pytest.mark.asyncio
    async def test_global_client_singleton(self):
        """Test that global client instances are properly managed"""
        client1 = get_shield_conport_client("workspace_1")
        client2 = get_shield_conport_client("workspace_1")
        client3 = get_shield_conport_client("workspace_2")

        # Same workspace should return same instance
        assert client1 is client2

        # Different workspace should return different instance
        assert client1 is not client3
        assert client2 is not client3

        assert client1.workspace_id == "workspace_1"
        assert client3.workspace_id == "workspace_2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])