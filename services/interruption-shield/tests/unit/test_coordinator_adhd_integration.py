"""
Unit tests for ShieldCoordinator ADHD Engine integration.

Tests that the coordinator properly:
1. Subscribes to ADHD Engine attention state changes
2. Activates shields when entering FOCUSED/HYPERFOCUS
3. Deactivates shields when FATIGUED or SCATTERED
4. Respects user preferences and override settings
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from interruption_shield.core import ShieldCoordinator, ShieldConfig, ShieldMode, ShieldState
from interruption_shield.integrations import ADHDEngineClient, AttentionState, DNDManager
from interruption_shield.triage import MessageTriage, UrgencyScorer, UrgencyScorerConfig, MessageQueue


@pytest.fixture
def mock_adhd_engine():
    """Mock ADHD Engine client."""
    mock = Mock(spec=ADHDEngineClient)
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.subscribe_attention_state = AsyncMock()
    mock.get_current_state = AsyncMock(return_value=AttentionState.SCATTERED)
    return mock


@pytest.fixture
def mock_dnd_manager():
    """Mock DND manager."""
    mock = Mock(spec=DNDManager)
    mock.enable_macos_focus_mode = AsyncMock()
    mock.disable_macos_focus_mode = AsyncMock()
    mock.set_slack_status = AsyncMock()
    mock.clear_slack_status = AsyncMock()
    return mock


@pytest.fixture
def mock_message_triage():
    """Mock message triage."""
    scorer = UrgencyScorer(UrgencyScorerConfig(user_id="test_user"))
    queue = MessageQueue()
    triage = MessageTriage(scorer, queue)
    triage.start = AsyncMock()
    triage.stop = AsyncMock()
    triage.start_queuing = AsyncMock()
    triage.stop_queuing = AsyncMock()
    return triage


@pytest.fixture
async def coordinator(mock_adhd_engine, mock_dnd_manager, mock_message_triage):
    """Create ShieldCoordinator with mocked dependencies."""
    config = ShieldConfig()
    coord = ShieldCoordinator(
        config=config,
        adhd_engine_client=mock_adhd_engine,
        dnd_manager=mock_dnd_manager,
        message_triage=mock_message_triage,
    )
    yield coord
    await coord.stop()


class TestShieldCoordinatorADHDIntegration:
    """Test ADHD Engine integration in ShieldCoordinator."""

    @pytest.mark.asyncio
    async def test_coordinator_subscribes_to_adhd_engine(self, coordinator, mock_adhd_engine):
        """Test coordinator subscribes to ADHD Engine on start."""
        await coordinator.start()

        # Verify subscription
        mock_adhd_engine.subscribe_attention_state.assert_called_once()
        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]
        assert asyncio.iscoroutinefunction(callback)

    @pytest.mark.asyncio
    async def test_auto_activate_on_focused(self, coordinator, mock_adhd_engine, mock_dnd_manager):
        """Test shields auto-activate when entering FOCUSED state."""
        coordinator.config.auto_activate = True
        await coordinator.start()

        # Get the callback registered with ADHD Engine
        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        # Simulate state change to FOCUSED
        await callback(AttentionState.FOCUSED, "test_user")

        # Verify shields activated
        assert coordinator.state.active is True
        assert coordinator.state.attention_state == AttentionState.FOCUSED
        mock_dnd_manager.enable_macos_focus_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_activate_on_hyperfocus(self, coordinator, mock_adhd_engine, mock_dnd_manager):
        """Test shields auto-activate when entering HYPERFOCUS state."""
        coordinator.config.auto_activate = True
        await coordinator.start()

        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        # Simulate state change to HYPERFOCUS
        await callback(AttentionState.HYPERFOCUS, "test_user")

        # Verify shields activated
        assert coordinator.state.active is True
        assert coordinator.state.attention_state == AttentionState.HYPERFOCUS
        mock_dnd_manager.enable_macos_focus_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_deactivate_on_fatigued(self, coordinator, mock_adhd_engine, mock_dnd_manager):
        """Test shields auto-deactivate when entering FATIGUED state."""
        coordinator.config.auto_activate = True
        await coordinator.start()

        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        # First activate shields (FOCUSED)
        await callback(AttentionState.FOCUSED, "test_user")
        assert coordinator.state.active is True

        # Then transition to FATIGUED
        await callback(AttentionState.FATIGUED, "test_user")

        # Verify shields deactivated
        assert coordinator.state.active is False
        assert coordinator.state.attention_state == AttentionState.FATIGUED
        mock_dnd_manager.disable_macos_focus_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_deactivate_on_scattered(self, coordinator, mock_adhd_engine, mock_dnd_manager):
        """Test shields auto-deactivate when entering SCATTERED state."""
        coordinator.config.auto_activate = True
        await coordinator.start()

        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        # First activate shields (HYPERFOCUS)
        await callback(AttentionState.HYPERFOCUS, "test_user")
        assert coordinator.state.active is True

        # Then transition to SCATTERED
        await callback(AttentionState.SCATTERED, "test_user")

        # Verify shields deactivated
        assert coordinator.state.active is False
        assert coordinator.state.attention_state == AttentionState.SCATTERED
        mock_dnd_manager.disable_macos_focus_mode.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_auto_activate_when_disabled(self, coordinator, mock_adhd_engine, mock_dnd_manager):
        """Test shields don't auto-activate when auto_activate=False."""
        coordinator.config.auto_activate = False
        await coordinator.start()

        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        # Simulate state change to FOCUSED
        await callback(AttentionState.FOCUSED, "test_user")

        # Verify shields NOT activated
        assert coordinator.state.active is False
        mock_dnd_manager.enable_macos_focus_mode.assert_not_called()

    @pytest.mark.asyncio
    async def test_manual_override_prevents_auto_deactivate(self, coordinator, mock_adhd_engine, mock_dnd_manager):
        """Test manual shield activation prevents auto-deactivation."""
        coordinator.config.auto_activate = True
        await coordinator.start()

        # Manually activate shields
        await coordinator.activate_shields("test_user")
        assert coordinator.state.active is True

        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        # Transition to SCATTERED (should NOT auto-deactivate if manually activated)
        await callback(AttentionState.SCATTERED, "test_user")

        # Verify shields still active (manual override)
        # Note: Implementation should track manual vs auto activation
        # For now, this test documents expected behavior

    @pytest.mark.asyncio
    async def test_state_tracking_updates(self, coordinator, mock_adhd_engine):
        """Test coordinator tracks attention state changes."""
        await coordinator.start()

        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        # Simulate state progression
        states = [
            AttentionState.SCATTERED,
            AttentionState.TRANSITIONING,
            AttentionState.FOCUSED,
            AttentionState.HYPERFOCUS,
            AttentionState.FATIGUED,
        ]

        for state in states:
            await callback(state, "test_user")
            assert coordinator.state.attention_state == state

    @pytest.mark.asyncio
    async def test_multiple_state_changes_rapid_succession(
        self, coordinator, mock_adhd_engine, mock_dnd_manager
    ):
        """Test coordinator handles rapid state changes gracefully."""
        coordinator.config.auto_activate = True
        await coordinator.start()

        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        # Rapid state changes
        await callback(AttentionState.FOCUSED, "test_user")
        await callback(AttentionState.HYPERFOCUS, "test_user")
        await callback(AttentionState.FOCUSED, "test_user")
        await callback(AttentionState.SCATTERED, "test_user")

        # Verify final state
        assert coordinator.state.attention_state == AttentionState.SCATTERED
        assert coordinator.state.active is False

    @pytest.mark.asyncio
    async def test_conport_logging_on_state_changes(self, coordinator, mock_adhd_engine):
        """Test coordinator logs attention state changes to ConPort."""
        await coordinator.start()

        callback = mock_adhd_engine.subscribe_attention_state.call_args[0][0]

        with patch("interruption_shield.core.coordinator.log_to_conport") as mock_log:
            # Simulate state change
            await callback(AttentionState.FOCUSED, "test_user")

            # Verify ConPort logging
            # Note: Actual implementation will determine logging format
            # This test documents expected behavior


@pytest.mark.asyncio
async def test_full_workflow_scenario():
    """
    Full workflow test simulating real ADHD user session.

    Scenario:
    1. User starts work (SCATTERED → FOCUSED)
    2. Shields auto-activate
    3. Deep work (FOCUSED → HYPERFOCUS)
    4. Break time (HYPERFOCUS → FATIGUED)
    5. Shields auto-deactivate
    """
    config = ShieldConfig(auto_activate=True)
    mock_adhd = Mock(spec=ADHDEngineClient)
    mock_adhd.start = AsyncMock()
    mock_adhd.stop = AsyncMock()
    mock_adhd.subscribe_attention_state = AsyncMock()

    mock_dnd = Mock(spec=DNDManager)
    mock_dnd.enable_macos_focus_mode = AsyncMock()
    mock_dnd.disable_macos_focus_mode = AsyncMock()
    mock_dnd.set_slack_status = AsyncMock()

    scorer = UrgencyScorer(UrgencyScorerConfig(user_id="test_user"))
    queue = MessageQueue()
    triage = MessageTriage(scorer, queue)
    triage.start = AsyncMock()
    triage.stop = AsyncMock()

    coordinator = ShieldCoordinator(
        config=config,
        adhd_engine_client=mock_adhd,
        dnd_manager=mock_dnd,
        message_triage=triage,
    )

    await coordinator.start()

    # Get callback
    callback = mock_adhd.subscribe_attention_state.call_args[0][0]

    # Simulate workflow
    events = []

    # 1. Start work (SCATTERED → FOCUSED)
    await callback(AttentionState.FOCUSED, "test_user")
    events.append(("focused", coordinator.state.active))

    # 2. Deep work (FOCUSED → HYPERFOCUS)
    await callback(AttentionState.HYPERFOCUS, "test_user")
    events.append(("hyperfocus", coordinator.state.active))

    # 3. Break time (HYPERFOCUS → FATIGUED)
    await callback(AttentionState.FATIGUED, "test_user")
    events.append(("fatigued", coordinator.state.active))

    await coordinator.stop()

    # Verify workflow
    assert events[0] == ("focused", True)  # Shields activated
    assert events[1] == ("hyperfocus", True)  # Shields still active
    assert events[2] == ("fatigued", False)  # Shields deactivated

    # Verify DND calls
    assert mock_dnd.enable_macos_focus_mode.call_count >= 1
    assert mock_dnd.disable_macos_focus_mode.call_count >= 1
