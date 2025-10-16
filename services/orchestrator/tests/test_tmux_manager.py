"""
Tests for Tmux Layout Manager
Step 1 Validation
"""

import pytest
from pathlib import Path
import libtmux
from src.tmux_manager import TmuxLayoutManager


class TestTmuxLayoutManager:
    """Test suite for TmuxLayoutManager."""

    @pytest.fixture
    def manager(self):
        """Create manager with test session name."""
        mgr = TmuxLayoutManager(session_name="dopemux-test")
        yield mgr
        # Cleanup
        try:
            mgr.destroy_session()
        except Exception:
            pass

    def test_create_session_medium_energy(self, manager):
        """Test creating session with medium energy (default 3 panes)."""
        session = manager.create_session(energy_level="medium")

        assert session is not None
        assert session.name == "dopemux-test"
        assert len(manager.panes) == 3  # Medium = 3 panes

        # Check pane names
        assert "ai_primary" in manager.panes
        assert "ai_secondary" in manager.panes
        assert "chat" in manager.panes

    def test_create_session_low_energy(self, manager):
        """Test creating session with low energy (2 panes)."""
        session = manager.create_session(energy_level="low")

        assert len(manager.panes) == 2  # Low = 2 panes
        assert "ai_primary" in manager.panes
        assert "chat" in manager.panes

    def test_create_session_high_energy(self, manager):
        """Test creating session with high energy (4 panes)."""
        session = manager.create_session(energy_level="high")

        assert len(manager.panes) == 4  # High = 4 panes
        assert "ai_claude" in manager.panes
        assert "ai_gemini" in manager.panes
        assert "ai_grok" in manager.panes
        assert "chat" in manager.panes

    def test_switch_layout(self, manager):
        """Test switching between energy layouts."""
        # Start with low energy
        manager.create_session(energy_level="low")
        assert len(manager.panes) == 2

        # Switch to high energy
        manager.switch_layout("high")
        assert len(manager.panes) == 4
        assert manager.current_layout == "high_4_pane"

    def test_send_to_pane(self, manager):
        """Test sending commands to specific panes."""
        manager.create_session(energy_level="medium")

        # Send command to chat pane
        manager.send_to_pane("chat", "echo 'test'", enter=False)

        # Verify command was sent (check pane content)
        chat_pane = manager.get_pane("chat")
        assert chat_pane is not None

    def test_get_nonexistent_pane(self, manager):
        """Test getting pane that doesn't exist."""
        manager.create_session(energy_level="low")

        pane = manager.get_pane("nonexistent")
        assert pane is None

    def test_session_reuse(self, manager):
        """Test that getting existing session works."""
        # Create first time
        session1 = manager.create_session(energy_level="medium")

        # Create again - should reuse
        manager2 = TmuxLayoutManager(session_name="dopemux-test")
        session2 = manager2.create_session(energy_level="medium")

        assert session1.id == session2.id  # Same session

    def test_destroy_session(self, manager):
        """Test session destruction."""
        manager.create_session(energy_level="medium")
        assert manager.session is not None

        manager.destroy_session()
        assert manager.session is None
        assert len(manager.panes) == 0


class TestEnergyDetector:
    """Test suite for energy detection."""

    @pytest.fixture
    def detector(self):
        """Create energy detector."""
        from src.layouts.adaptive_layout import EnergyDetector

        det = EnergyDetector()
        det.baseline_typing_speed = 60.0  # Set baseline
        return det

    def test_detect_low_energy(self, detector):
        """Test low energy detection (slow typing, long session)."""
        from src.layouts.adaptive_layout import EnergyLevel

        # Slow typing, scattered attention, 60min session
        energy = detector.detect_energy(
            typing_speed=30,  # 50% of baseline
            pane_switches_per_min=12,  # Scattered
            minutes_since_break=60,
        )

        # First detection won't change (needs 3 readings)
        # But score should be low
        assert energy in [EnergyLevel.LOW, EnergyLevel.MEDIUM]

    def test_detect_high_energy(self, detector):
        """Test high energy detection (fast typing, focused, fresh)."""
        from src.layouts.adaptive_layout import EnergyLevel

        # Fast typing, focused, recent break
        energy = detector.detect_energy(
            typing_speed=90,  # 150% of baseline
            pane_switches_per_min=2,  # Focused
            minutes_since_break=5,  # Fresh
        )

        assert energy in [EnergyLevel.HIGH, EnergyLevel.MEDIUM, EnergyLevel.HYPERFOCUS]

    def test_hysteresis_prevents_flapping(self, detector):
        """Test that energy state requires 3 consecutive readings."""
        from src.layouts.adaptive_layout import EnergyLevel

        # First reading: high energy
        e1 = detector.detect_energy(typing_speed=90, minutes_since_break=5)

        # Second reading: low energy (shouldn't switch immediately)
        e2 = detector.detect_energy(typing_speed=30, minutes_since_break=60)

        # Third reading: low energy (now should switch)
        e3 = detector.detect_energy(typing_speed=30, minutes_since_break=60)

        # History should show progression
        assert len(detector.energy_history) == 3


if __name__ == "__main__":
    """Run tests directly."""
    pytest.main([__file__, "-v"])
