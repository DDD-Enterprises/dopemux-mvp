"""Unit tests for ShieldCoordinator."""

import pytest
from datetime import datetime

from interruption_shield.core.coordinator import ShieldCoordinator
from interruption_shield.core.models import AttentionState, ShieldMode


class TestShieldCoordinator:
    """Test suite for ShieldCoordinator functionality."""

    @pytest.mark.asyncio
    async def test_shield_activation_on_focused_state(
        self,
        default_config,
        mock_adhd_engine,
        mock_dnd_manager
    ):
        """Test that shields activate when FOCUSED state detected."""
        coordinator = ShieldCoordinator(
            config=default_config,
            adhd_engine_client=mock_adhd_engine,
            dnd_manager=mock_dnd_manager
        )

        # Trigger FOCUSED state
        await coordinator.on_attention_state_changed(
            AttentionState.FOCUSED,
            user_id="test_user"
        )

        # Verify shields activated
        assert coordinator.state.active is True
        assert coordinator.state.attention_state == AttentionState.FOCUSED
        assert mock_dnd_manager.focus_mode_enabled is True

    @pytest.mark.asyncio
    async def test_shield_deactivation_on_scattered_state(
        self,
        default_config,
        mock_adhd_engine,
        mock_dnd_manager
    ):
        """Test that shields deactivate when SCATTERED state detected."""
        coordinator = ShieldCoordinator(
            config=default_config,
            adhd_engine_client=mock_adhd_engine,
            dnd_manager=mock_dnd_manager
        )

        # First activate
        await coordinator.on_attention_state_changed(
            AttentionState.FOCUSED,
            user_id="test_user"
        )

        assert coordinator.state.active is True

        # Then deactivate
        await coordinator.on_attention_state_changed(
            AttentionState.SCATTERED,
            user_id="test_user"
        )

        # Verify shields deactivated
        assert coordinator.state.active is False
        assert mock_dnd_manager.focus_mode_enabled is False

    @pytest.mark.asyncio
    async def test_manual_override(
        self,
        default_config,
        mock_adhd_engine,
        mock_dnd_manager
    ):
        """Test manual shield override functionality."""
        coordinator = ShieldCoordinator(
            config=default_config,
            adhd_engine_client=mock_adhd_engine,
            dnd_manager=mock_dnd_manager
        )

        # Activate shields
        await coordinator.activate_shields("test_user")
        assert coordinator.state.active is True

        # Manual override (don't await - runs in background)
        asyncio.create_task(coordinator.manual_override("test_user", duration_minutes=1))

        # Should deactivate immediately
        await asyncio.sleep(0.1)
        assert coordinator.state.active is False

    @pytest.mark.asyncio
    async def test_no_activation_when_auto_activate_disabled(
        self,
        default_config,
        mock_adhd_engine,
        mock_dnd_manager
    ):
        """Test that shields don't activate if auto_activate is False."""
        config = default_config
        config.auto_activate = False

        coordinator = ShieldCoordinator(
            config=config,
            adhd_engine_client=mock_adhd_engine,
            dnd_manager=mock_dnd_manager
        )

        # Trigger FOCUSED state
        await coordinator.on_attention_state_changed(
            AttentionState.FOCUSED,
            user_id="test_user"
        )

        # Verify shields did NOT activate
        assert coordinator.state.active is False
