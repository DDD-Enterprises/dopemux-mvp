"""
Tmux Layout Manager - Step 1 of Phase 1
ADHD-optimized adaptive pane layouts based on energy state

Complexity: 0.35 (Low-Medium)
Effort: 4 focus blocks (100 minutes)
"""

from typing import Literal, Optional

import logging

logger = logging.getLogger(__name__)

import libtmux
from pathlib import Path
import yaml
import os


EnergyLevel = Literal["low", "medium", "high"]


class TmuxLayoutManager:
    """
    ADHD-optimized tmux layout manager with energy-adaptive pane counts.

    Layouts:
    - Low energy: 2 panes (minimize choices)
    - Medium energy: 3 panes (balanced)
    - High energy: 4 panes (parallel monitoring)
    """

    def __init__(self, session_name: str = "dopemux-orchestrator"):
        """
        Initialize layout manager.

        Args:
            session_name: Name of tmux session to manage
        """
        # Auto-suffix workspace when using default session name
        ws = os.getenv("WORKSPACE_ID") or os.getenv("DOPEMUX_WORKSPACE") or ""
        if session_name == "dopemux-orchestrator" and ws:
            session_name = f"{session_name}-{ws}"
        self.session_name = session_name
        self.server = libtmux.Server()
        self.session: Optional[libtmux.Session] = None
        self.panes: dict[str, libtmux.Pane] = {}
        self.current_layout: Optional[str] = None

    def create_session(
        self,
        energy_level: EnergyLevel = "medium",
        start_directory: Optional[Path] = None,
    ) -> libtmux.Session:
        """
        Create or get tmux session with energy-appropriate layout.

        Args:
            energy_level: Current ADHD energy state
            start_directory: Working directory for session

        Returns:
            libtmux.Session object

        Raises:
            RuntimeError: If session creation fails
        """
        # Try to get existing session
        try:
            self.session = self.server.sessions.get(session_name=self.session_name)
            logger.info(f"✅ Found existing session: {self.session_name}")
        except Exception as e:
            # Create new session
            start_dir = str(start_directory) if start_directory else None
            self.session = self.server.new_session(
                session_name=self.session_name,
                start_directory=start_dir,
            )
            logger.info(f"✨ Created new session: {self.session_name}")

        # Apply layout for energy level
        self.apply_layout(energy_level)

        return self.session

    def apply_layout(self, energy_level: EnergyLevel) -> dict[str, libtmux.Pane]:
        """
        Apply energy-appropriate pane layout.

        Args:
            energy_level: Current energy state

        Returns:
            Dictionary mapping pane names to libtmux.Pane objects
        """
        if not self.session:
            raise RuntimeError("No active session. Call create_session() first.")

        # Clear existing panes (except first)
        window = self.session.active_window
        if not window:
            window = self.session.windows[0]

        # Kill all panes except the first one
        for pane in window.panes[1:]:
            pane.cmd("kill-pane")

        # Create layout based on energy
        if energy_level == "low":
            self.panes = self._create_low_energy_layout(window)
            self.current_layout = "low_2_pane"
        elif energy_level == "medium":
            self.panes = self._create_medium_energy_layout(window)
            self.current_layout = "medium_3_pane"
        else:  # high
            self.panes = self._create_high_energy_layout(window)
            self.current_layout = "high_4_pane"

        logger.info(f"🎨 Applied {energy_level} energy layout ({len(self.panes)} panes)")
        return self.panes

    def _create_low_energy_layout(self, window: libtmux.Window) -> dict[str, libtmux.Pane]:
        """
        Low energy: 2 panes (active AI + chat)
        Layout: Horizontal split 60/40

        ┌──────────────┬─────────┐
        │ Pane 0       │ Pane 1  │
        │ Active AI    │ Chat    │
        │ (60%)        │ (40%)   │
        └──────────────┴─────────┘
        """
        main_pane = window.panes[0]

        # Split horizontally (side by side)
        chat_pane = window.split_window(
            target=main_pane.id,
            vertical=True,  # Vertical split creates side-by-side
            percent=40,
        )

        return {
            "ai_primary": main_pane,
            "chat": chat_pane,
        }

    def _create_medium_energy_layout(self, window: libtmux.Window) -> dict[str, libtmux.Pane]:
        """
        Medium energy: 3 panes (2 AI instances + chat)
        Layout: Main-vertical with bottom chat

        ┌───────────┬──────────┐
        │ Pane 0    │ Pane 1   │
        │ Claude    │ Gemini   │
        │           │          │
        ├───────────┴──────────┤
        │ Pane 2: Chat         │
        └──────────────────────┘
        """
        main_pane = window.panes[0]

        # Split right for second AI
        ai_secondary = window.split_window(
            target=main_pane.id,
            vertical=True,
            percent=50,
        )

        # Split bottom for chat (split the main pane)
        chat_pane = window.split_window(
            target=main_pane.id,
            vertical=False,  # Horizontal split creates top/bottom
            percent=30,
        )

        return {
            "ai_primary": main_pane,
            "ai_secondary": ai_secondary,
            "chat": chat_pane,
        }

    def _create_high_energy_layout(self, window: libtmux.Window) -> dict[str, libtmux.Pane]:
        """
        High energy: 4 panes (3 AI instances + chat)
        Layout: Tiled 2x2

        ┌───────────┬──────────┐
        │ Pane 0    │ Pane 1   │
        │ Claude    │ Gemini   │
        ├───────────┼──────────┤
        │ Pane 2    │ Pane 3   │
        │ Grok      │ Chat     │
        └───────────┴──────────┘
        """
        main_pane = window.panes[0]

        # Split right for second AI (top row)
        ai_secondary = window.split_window(
            target=main_pane.id,
            vertical=True,
            percent=50,
        )

        # Split bottom for third AI (left column)
        ai_tertiary = window.split_window(
            target=main_pane.id,
            vertical=False,
            percent=50,
        )

        # Split right for chat (bottom row)
        chat_pane = window.split_window(
            target=ai_tertiary.id,
            vertical=True,
            percent=50,
        )

        # Apply tiled layout for even distribution
        window.select_layout("tiled")

        return {
            "ai_claude": main_pane,
            "ai_gemini": ai_secondary,
            "ai_grok": ai_tertiary,
            "chat": chat_pane,
        }

    def switch_layout(self, new_energy: EnergyLevel) -> None:
        """
        Switch to different energy layout (adaptive interface).

        Args:
            new_energy: Target energy level
        """
        if not self.session:
            raise RuntimeError("No active session")

        logger.info(f"🔄 Switching from {self.current_layout} to {new_energy} energy layout...")

        # Save current pane states before switching
        pane_states = self._capture_pane_states()

        # Apply new layout
        self.apply_layout(new_energy)

        # Restore what we can
        self._restore_pane_states(pane_states)

        logger.info(f"✅ Layout switched to {new_energy} energy")

    def _capture_pane_states(self) -> dict:
        """Capture current state of all panes before layout change."""
        states = {}
        for name, pane in self.panes.items():
            try:
                states[name] = {
                    "history": pane.cmd("capture-pane", "-p").stdout,
                    "id": pane.id,
                }
            except Exception as e:
                logger.info(f"⚠️ Could not capture {name}: {e}")
        return states

    def _restore_pane_states(self, states: dict) -> None:
        """Attempt to restore pane states after layout change."""
        # Best effort restoration - may not be perfect
        # This is a placeholder for now
        pass

    def get_pane(self, name: str) -> Optional[libtmux.Pane]:
        """
        Get pane by name.

        Args:
            name: Pane name (e.g., 'chat', 'ai_claude')

        Returns:
            libtmux.Pane or None if not found
        """
        return self.panes.get(name)

    def send_to_pane(self, pane_name: str, command: str, enter: bool = True) -> None:
        """
        Send command to specific pane.

        Args:
            pane_name: Target pane name
            command: Command string to send
            enter: Whether to send Enter key after command
        """
        pane = self.get_pane(pane_name)
        if not pane:
            raise ValueError(f"Pane not found: {pane_name}")

        pane.send_keys(command, enter=enter)

    def destroy_session(self) -> None:
        """Destroy the tmux session."""
        if self.session:
            self.session.kill()
            logger.info(f"🗑️ Destroyed session: {self.session_name}")
            self.session = None
            self.panes = {}


if __name__ == "__main__":
    """Test the layout manager"""
    import sys

    energy = sys.argv[1] if len(sys.argv) > 1 else "medium"

    if energy not in ["low", "medium", "high"]:
        logger.info(f"Usage: python tmux_manager.py [low|medium|high]")
        sys.exit(1)

    manager = TmuxLayoutManager()
    session = manager.create_session(energy_level=energy)

    logger.info(f"\n✅ Session created: {session.name}")
    logger.info(f"📊 Panes: {len(manager.panes)}")
    for name, pane in manager.panes.items():
        logger.info(f"  - {name}: {pane.id}")

    logger.info(f"\n💡 Attach with: tmux attach -t {session.name}")
