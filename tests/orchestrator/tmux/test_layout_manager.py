"""
Tests for TmuxLayoutManager - Energy-Adaptive Layouts

Tests cover:
- Layout creation for different energy levels
- Energy adaptation transitions
- Pane count verification
- Session initialization
- ConPort persistence (mocked)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/orchestrator'))

from tmux.layout_manager import (
    TmuxLayoutManager,
    LayoutType,
    EnergyLevel,
    get_layout_for_energy,
    get_pane_count
)


class TestLayoutTypeMapping:
    """Test layout type utilities."""

    def test_get_layout_for_energy_low(self):
        """Test low energy maps to 2-pane."""
        assert get_layout_for_energy("low") == LayoutType.TWO_PANE
        assert get_layout_for_energy("very_low") == LayoutType.TWO_PANE

    def test_get_layout_for_energy_medium(self):
        """Test medium energy maps to 3-pane."""
        assert get_layout_for_energy("medium") == LayoutType.THREE_PANE

    def test_get_layout_for_energy_high(self):
        """Test high energy maps to 4-pane."""
        assert get_layout_for_energy("high") == LayoutType.FOUR_PANE
        assert get_layout_for_energy("hyperfocus") == LayoutType.FOUR_PANE

    def test_get_layout_for_energy_default(self):
        """Test unknown energy defaults to 3-pane."""
        assert get_layout_for_energy("unknown") == LayoutType.THREE_PANE

    def test_get_pane_count(self):
        """Test pane count mapping."""
        assert get_pane_count(LayoutType.TWO_PANE) == 2
        assert get_pane_count(LayoutType.THREE_PANE) == 3
        assert get_pane_count(LayoutType.FOUR_PANE) == 4


class TestTmuxLayoutManager:
    """Test TmuxLayoutManager with mocked tmux."""

    @pytest.fixture
    def mock_tmux_server(self):
        """Mock libtmux server."""
        with patch('tmux.layout_manager.libtmux') as mock_libtmux:
            # Mock server and session
            mock_server = Mock()
            mock_session = Mock()
            mock_window = Mock()
            mock_pane = Mock()

            # Setup mock chain
            mock_libtmux.Server.return_value = mock_server
            mock_server.find_where.side_effect = Exception("Session not found")
            mock_server.new_session.return_value = mock_session
            mock_session.windows = [mock_window]
            mock_window.panes = [mock_pane]

            # Mock pane operations
            mock_pane.cmd = Mock()
            mock_window.split_window = Mock(return_value=mock_pane)

            yield {
                "server": mock_server,
                "session": mock_session,
                "window": mock_window,
                "pane": mock_pane
            }

    def test_initialization_new_session(self, mock_tmux_server):
        """Test creating new tmux session."""
        manager = TmuxLayoutManager(session_name="test-dopemux")
        manager.initialize()

        # Verify new session created
        mock_tmux_server["server"].new_session.assert_called_once_with(
            session_name="test-dopemux",
            window_name="dopemux-main"
        )
        assert manager.session is not None

    def test_initialization_existing_session(self, mock_tmux_server):
        """Test attaching to existing session."""
        # Mock finding existing session
        mock_tmux_server["server"].find_where.side_effect = None
        mock_tmux_server["server"].find_where.return_value = mock_tmux_server["session"]

        manager = TmuxLayoutManager(session_name="test-dopemux")
        manager.initialize()

        # Verify attached to existing
        mock_tmux_server["server"].find_where.assert_called_once()
        assert manager.session is not None

    def test_create_two_pane_layout(self, mock_tmux_server):
        """Test 2-pane layout creation."""
        manager = TmuxLayoutManager()
        manager.initialize()

        # Create 2-pane layout
        manager.create_layout(LayoutType.TWO_PANE, "low")

        # Verify layout created
        assert manager.current_layout == LayoutType.TWO_PANE
        # Verify split_window called once (creates 2nd pane)
        mock_tmux_server["window"].split_window.assert_called()

    def test_create_three_pane_layout(self, mock_tmux_server):
        """Test 3-pane layout creation."""
        manager = TmuxLayoutManager()
        manager.initialize()

        manager.create_layout(LayoutType.THREE_PANE, "medium")

        assert manager.current_layout == LayoutType.THREE_PANE
        # Verify split_window called twice (creates 2nd and 3rd panes)
        assert mock_tmux_server["window"].split_window.call_count == 2

    def test_create_four_pane_layout(self, mock_tmux_server):
        """Test 4-pane layout creation."""
        manager = TmuxLayoutManager()
        manager.initialize()

        manager.create_layout(LayoutType.FOUR_PANE, "high")

        assert manager.current_layout == LayoutType.FOUR_PANE
        # Verify split_window called three times (creates 2nd, 3rd, and 4th panes)
        assert mock_tmux_server["window"].split_window.call_count == 3

    def test_adapt_layout_to_energy_changes(self, mock_tmux_server):
        """Test layout adapts when energy changes."""
        manager = TmuxLayoutManager()
        manager.initialize()

        # Start with low energy (2 panes)
        manager.adapt_layout_to_energy("low")
        assert manager.current_layout == LayoutType.TWO_PANE

        # Increase to medium energy (3 panes)
        manager.adapt_layout_to_energy("medium")
        assert manager.current_layout == LayoutType.THREE_PANE

        # Increase to high energy (4 panes)
        manager.adapt_layout_to_energy("high")
        assert manager.current_layout == LayoutType.FOUR_PANE

    def test_adapt_layout_no_change_when_same(self, mock_tmux_server):
        """Test layout doesn't recreate if energy level maps to same layout."""
        manager = TmuxLayoutManager()
        manager.initialize()

        # Create initial layout
        manager.adapt_layout_to_energy("low")
        initial_call_count = mock_tmux_server["window"].split_window.call_count

        # Call with same energy level
        manager.adapt_layout_to_energy("low")

        # Verify no new splits (layout unchanged)
        assert mock_tmux_server["window"].split_window.call_count == initial_call_count

    def test_get_pane_info(self, mock_tmux_server):
        """Test retrieving pane information."""
        manager = TmuxLayoutManager(session_name="test-session")
        manager.initialize()
        manager.create_layout(LayoutType.THREE_PANE, "medium")

        info = manager.get_pane_info()

        assert info["session_name"] == "test-session"
        assert info["layout_type"] == "3-pane"
        assert "panes" in info

    @pytest.mark.asyncio
    async def test_save_layout_to_conport(self, mock_tmux_server):
        """Test layout persistence to ConPort."""
        manager = TmuxLayoutManager()
        manager.initialize()
        manager.create_layout(LayoutType.TWO_PANE, "low")

        # Save layout
        success = await manager.save_layout_to_conport()

        # Should succeed (even if just logging for now)
        assert success is True

    def test_close(self, mock_tmux_server):
        """Test cleanup."""
        manager = TmuxLayoutManager()
        manager.initialize()

        manager.close()

        # Session reference should be cleared
        assert manager.session is None


class TestEnergyLevelEnum:
    """Test EnergyLevel enum values."""

    def test_energy_level_values(self):
        """Test all energy levels defined."""
        assert EnergyLevel.VERY_LOW.value == "very_low"
        assert EnergyLevel.LOW.value == "low"
        assert EnergyLevel.MEDIUM.value == "medium"
        assert EnergyLevel.HIGH.value == "high"
        assert EnergyLevel.HYPERFOCUS.value == "hyperfocus"


class TestLayoutTypeEnum:
    """Test LayoutType enum values."""

    def test_layout_type_values(self):
        """Test all layout types defined."""
        assert LayoutType.TWO_PANE.value == "2-pane"
        assert LayoutType.THREE_PANE.value == "3-pane"
        assert LayoutType.FOUR_PANE.value == "4-pane"


# Integration test markers
pytestmark = pytest.mark.unit  # All tests are unit tests
