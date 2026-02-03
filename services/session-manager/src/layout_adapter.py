"""
Tmux Layout Manager - Step 1 of Phase 1
ADHD-optimized adaptive pane layouts based on energy state

Complexity: 0.35 (Low-Medium)
Effort: 4 focus blocks (100 minutes)
"""

from typing import Literal, Optional

import logging

logger = logging.getLogger(__name__)

from typing import Literal, Optional, Dict
import logging
from pathlib import Path
import os
import sys

# Add src to path to allow absolute imports if running standalone
sys.path.append(str(Path(__file__).parents[3] / "src"))

from dopemux.tmux.controller import TmuxController
from dopemux.tmux.layouts import EnergyLayoutManager, EnergyLevel

logger = logging.getLogger(__name__)

class TmuxLayoutManager:
    """
    ADHD-optimized tmux layout manager adapter.
    Delegates to Core dopemux.tmux components.
    """

    def __init__(self, session_name: str = "dopemux-orchestrator"):
        # Auto-suffix workspace when using default session name
        ws = os.getenv("WORKSPACE_ID") or os.getenv("DOPEMUX_WORKSPACE") or ""
        if session_name == "dopemux-orchestrator" and ws:
            session_name = f"{session_name}-{ws}"
        self.session_name = session_name
        
        # Initialize Core Controller
        self.controller = TmuxController()
        self.layout_manager = EnergyLayoutManager(self.controller)
        self.panes: Dict[str, str] = {} # Map name -> pane_id for compatibility

    def create_session(
        self,
        energy_level: EnergyLevel = "medium",
        start_directory: Optional[Path] = None,
    ):
        """
        Create or get tmux session using Core Controller.
        """
        # Check if session exists (using list_panes filtered by session as proxy)
        existing = [p for p in self.controller.list_panes() if p.session == self.session_name]
        
        if existing:
            logger.info(f"✅ Found existing session: {self.session_name}")
        else:
            # Create new session
            # Core Controller 'open' can allow creating session implicitly via backend?
            # Or use low-level backend.
            # CliTmuxBackend uses `tmux_utils.create_session`
            from dopemux.mobile import tmux_utils
            tmux_utils.create_session(
                self.session_name,
                start_directory=str(start_directory) if start_directory else None
            )
            logger.info(f"✨ Created new session: {self.session_name}")

        # Apply layout
        self.apply_layout(energy_level)
        return self # Return self as a handle

    def apply_layout(self, energy_level: EnergyLevel) -> Dict[str, str]:
        """Apply energy layout using the shared manager."""
        self.layout_manager.apply_layout(self.session_name, energy_level)
        
        # Re-fetch panes to populate self.panes for compatibility
        all_panes = self.controller.list_panes(session=self.session_name)
        # Naming convention mapping is lost since we aren't returning the dict directly
        # but for compatibility we can try to guess or just return IDs
        self.panes = {f"pane_{i}": p.pane_id for i, p in enumerate(all_panes)}
        return self.panes

    def switch_layout(self, new_energy: EnergyLevel) -> None:
        """Switch layout."""
        self.apply_layout(new_energy)

    def send_to_pane(self, pane_name: str, command: str, enter: bool = True) -> None:
        """Send to pane by ID (if pane_name is an ID) or try to resolve."""
        # For compatibility, if pane_name is in self.panes dict, use that ID
        target_id = self.panes.get(pane_name, pane_name)
        self.controller.send_keys(target_id, command, enter=enter)

    def destroy_session(self) -> None:
        """Kill the session."""
        self.controller.backend.kill_session(self.session_name)

if __name__ == "__main__":
    energy = sys.argv[1] if len(sys.argv) > 1 else "medium"
    manager = TmuxLayoutManager()
    manager.create_session(energy_level=energy)
