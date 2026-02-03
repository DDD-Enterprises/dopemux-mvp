"""
ADHD-optimized energy layouts for Tmux.
Ported from services/orchestrator/src/tmux_manager.py.
"""
import logging
from typing import Literal, Optional, Dict, List
from .controller import TmuxController, PaneInfo

logger = logging.getLogger(__name__)

EnergyLevel = Literal["low", "medium", "high"]

class EnergyLayoutManager:
    """Manages pane layouts based on user energy levels."""

    def __init__(self, controller: TmuxController):
        self.controller = controller

    def apply_layout(self, session_name: str, energy_level: EnergyLevel) -> None:
        """
        Apply energy-appropriate pane layout to the active window of the session.
        
        Args:
            session_name: Target session
            energy_level: 'low', 'medium', or 'high'
        """
        # 1. Identify active window in session
        panes = self.controller.list_panes(session=session_name)
        if not panes:
            logger.warning(f"No panes found for session {session_name}")
            return

        active_pane = next((p for p in panes if p.active), panes[0])
        window_name = active_pane.window
        
        # Get all panes in that window, ordered (assumes list_panes returns ordered)
        window_panes = [p for p in panes if p.window == window_name]
        
        # 2. Reset to single pane (keep first one)
        if len(window_panes) > 1:
            for pane in window_panes[1:]:
                try:
                    self.controller.backend.kill_pane(pane.pane_id)
                except Exception as e:
                    logger.warning(f"Failed to kill pane {pane.pane_id}: {e}")
        
        # Refresh main pane info after killing others
        # We assume the first pane (index 0) remains and is now active or at least exists
        main_pane = window_panes[0]
        
        # 3. Apply specific layout
        if energy_level == "low":
            self._create_low_energy_layout(main_pane)
        elif energy_level == "medium":
            self._create_medium_energy_layout(main_pane)
        elif energy_level == "high":
            self._create_high_energy_layout(main_pane)
            
        logger.info(f"🎨 Applied {energy_level} energy layout to {session_name}:{window_name}")

    def _create_low_energy_layout(self, main_pane: PaneInfo) -> None:
        """
        Low energy: 2 panes (active AI + chat)
        Layout: Horizontal split 60/40
        """
        # Pane 1: Chat (40%) - split vertical = side-by-side
        self.controller.backend.split_window(
            target=main_pane.pane_id,
            command="", # Default shell
            vertical=True, # Side by side
            percent=40,
            session=main_pane.session,
            start_directory=None,
            focus=False,
            environment={}
        )

    def _create_medium_energy_layout(self, main_pane: PaneInfo) -> None:
        """
        Medium energy: 3 panes (2 AI instances + chat)
        Layout: Main-vertical with bottom chat
        """
        # Pane 1: Secondary AI (50% right)
        right_pane_id = self.controller.backend.split_window(
            target=main_pane.pane_id,
            command="",
            vertical=True,
            percent=50,
            session=main_pane.session,
            start_directory=None,
            focus=False,
            environment={}
        )
        
        # Pane 2: Chat (30% bottom of main)
        self.controller.backend.split_window(
            target=main_pane.pane_id,
            command="",
            vertical=False, # Bottom
            percent=30,
            session=main_pane.session,
            start_directory=None,
            focus=False,
            environment={}
        )

    def _create_high_energy_layout(self, main_pane: PaneInfo) -> None:
        """
        High energy: 4 panes (3 AI instances + chat)
        Layout: Tiled 2x2
        """
        # Split right (Top Row: Main | Secondary)
        sec_pane_id = self.controller.backend.split_window(
            target=main_pane.pane_id,
            command="",
            vertical=True,
            percent=50,
            session=main_pane.session,
            start_directory=None,
            focus=False,
            environment={}
        )
        
        # Split bottom left (Main | Tert) -> Wait, layout logic is tricky without 'select-layout tiled'
        # Orchestrator used 'tiled'
        
        # Bottom Left
        tert_pane_id = self.controller.backend.split_window(
            target=main_pane.pane_id,
            command="",
            vertical=False,
            percent=50,
            session=main_pane.session,
            start_directory=None,
            focus=False,
            environment={}
        )
        
        # Bottom Right using sec_pane (Secondary | Chat)
        self.controller.backend.split_window(
            target=sec_pane_id,
            command="",
            vertical=False,
            percent=50,
            session=main_pane.session,
            start_directory=None,
            focus=False,
            environment={}
        )
        
        # Force tiled layout
        # We need a primitive for select-layout in controller backend?
        # Checked `tmux_utils.py` -> `set_layout` exists.
        # Core Controller `backend` doesn't expose it clearly in BaseBackend but CliBackend uses tmux_utils.
        
        # Workaround: Import tmux_utils directly or extend backend. 
        # For now, let's assume we can add `set_layout` to backend or use the utils through a backchannel.
        # Actually `dopemux/mobile/tmux_utils.py` has `set_layout`.
        from dopemux.mobile import tmux_utils
        tmux_utils.set_layout(main_pane.window, "tiled")
