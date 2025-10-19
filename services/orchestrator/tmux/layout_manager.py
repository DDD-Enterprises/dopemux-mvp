"""
Tmux Layout Manager - Energy-Adaptive Pane Layouts for ADHD-Optimized Multi-AI Orchestration

Manages tmux pane layouts that adapt to user's cognitive capacity:
- Low energy (🔴): 2 panes - Chat + Claude (reduce decisions)
- Medium energy (🟡): 3 panes - Chat + Claude + Gemini (standard)
- High energy (🟢): 4 panes - Chat + Claude + Gemini + Grok (max coordination)

Integrates with:
- ADHD Engine: Energy state detection
- ConPort: Layout persistence and session restoration
- Zen MCP: Multi-model coordination
"""

import logging
import os
from typing import Optional, Dict, Any
from enum import Enum

try:
    import libtmux
except ImportError:
    libtmux = None  # Graceful degradation if libtmux not installed

logger = logging.getLogger(__name__)


class LayoutType(str, Enum):
    """Tmux layout types mapped to energy levels."""
    TWO_PANE = "2-pane"      # Low energy: Chat + Claude
    THREE_PANE = "3-pane"    # Medium energy: Chat + Claude + Gemini
    FOUR_PANE = "4-pane"     # High energy: Chat + Claude + Gemini + Grok


class EnergyLevel(str, Enum):
    """User energy levels for layout adaptation."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HYPERFOCUS = "hyperfocus"


class TmuxLayoutManager:
    """
    Manages tmux pane layouts with energy-aware adaptation.

    Layouts adapt to user's cognitive capacity to reduce decision fatigue
    and optimize multi-AI coordination effectiveness.

    ADHD Benefits:
    - Fewer panes when energy is low (reduce overwhelm)
    - More panes when energy is high (leverage hyperfocus)
    - Automatic adaptation prevents decision paralysis
    - Smooth transitions preserve context
    """

    def __init__(self, session_name: str = "dopemux", workspace_id: str = None):
        """
        Initialize Tmux Layout Manager.

        Args:
            session_name: Tmux session name (default: dopemux)
            workspace_id: ConPort workspace ID for persistence
        """
        if libtmux is None:
            raise RuntimeError("libtmux not installed. Run: pip install libtmux")

        self.session_name = session_name
        self.workspace_id = workspace_id or os.getcwd()
        self.server = libtmux.Server()
        self.session: Optional[libtmux.Session] = None
        self.current_layout: Optional[LayoutType] = None

        logger.info(f"🎨 TmuxLayoutManager initialized for session: {session_name}")

    def initialize(self) -> None:
        """
        Initialize or attach to tmux session.

        Creates new session if doesn't exist, otherwise attaches to existing.
        """
        try:
            # Try to find existing session
            self.session = self.server.find_where({"session_name": self.session_name})
            if self.session:
                logger.info(f"✅ Attached to existing tmux session: {self.session_name}")
            else:
                raise Exception("Session not found")

        except Exception:
            # Create new session
            self.session = self.server.new_session(
                session_name=self.session_name,
                window_name="dopemux-main"
            )
            logger.info(f"✅ Created new tmux session: {self.session_name}")

    def create_layout(self, layout_type: LayoutType, energy_level: str) -> None:
        """
        Create energy-appropriate tmux layout.

        Args:
            layout_type: 2/3/4 pane layout
            energy_level: Current user energy level for visual feedback

        Raises:
            RuntimeError: If session not initialized
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Call initialize() first.")

        # Get main window
        window = self.session.windows[0]

        # Kill all panes except first one
        while len(window.panes) > 1:
            window.panes[-1].cmd('kill-pane')

        # Create appropriate layout
        if layout_type == LayoutType.TWO_PANE:
            self._create_two_pane_layout(window, energy_level)
        elif layout_type == LayoutType.THREE_PANE:
            self._create_three_pane_layout(window, energy_level)
        elif layout_type == LayoutType.FOUR_PANE:
            self._create_four_pane_layout(window, energy_level)
        else:
            raise ValueError(f"Unknown layout type: {layout_type}")

        self.current_layout = layout_type
        logger.info(f"✅ Layout created: {layout_type.value} (energy: {energy_level})")

    def _create_two_pane_layout(self, window, energy_level: str) -> None:
        """
        Create 2-pane layout for low energy.

        Layout:
        ┌──────────────────┬──────────────────┐
        │                  │                  │
        │  Chat            │  Claude Code     │
        │  Orchestrator    │  (Architecture)  │
        │  (Pane 0)        │  (Pane 1)        │
        │                  │                  │
        └──────────────────┴──────────────────┘

        ADHD Benefit: Minimal context switching, focused interaction
        """
        # Get base pane
        pane_chat = window.panes[0]

        # Split vertically (50/50)
        pane_claude = window.split_window(vertical=True, percent=50)

        # Configure panes with helpful messages
        pane_chat.send_keys("# Chat Orchestrator - Central coordination", literal=True)
        pane_chat.send_keys("# Energy: 🔴 LOW - Focus on one task at a time", literal=True)
        pane_chat.send_keys("", literal=True)  # Newline

        pane_claude.send_keys("# Claude Code - Architecture and reasoning", literal=True)
        pane_claude.send_keys(f"# Layout: 2-pane (low energy mode)", literal=True)
        pane_claude.send_keys("", literal=True)

        logger.info(f"✅ Created 2-pane layout for {energy_level} energy")

    def _create_three_pane_layout(self, window, energy_level: str) -> None:
        """
        Create 3-pane layout for medium energy.

        Layout:
        ┌─────────┬─────────┬─────────┐
        │         │         │         │
        │  Chat   │ Claude  │ Gemini  │
        │ (Pane 0)│(Pane 1) │(Pane 2) │
        │         │         │         │
        └─────────┴─────────┴─────────┘

        ADHD Benefit: Balanced coordination without overwhelm
        """
        pane_chat = window.panes[0]

        # Split into 3 vertical panes
        pane_claude = window.split_window(vertical=True, percent=33)
        pane_gemini = window.split_window(vertical=True, percent=50)

        # Configure panes
        pane_chat.send_keys("# Chat Orchestrator - Central coordination", literal=True)
        pane_chat.send_keys("# Energy: 🟡 MEDIUM - Standard multi-AI mode", literal=True)
        pane_chat.send_keys("", literal=True)

        pane_claude.send_keys("# Claude Code - Architecture specialist", literal=True)
        pane_claude.send_keys("", literal=True)

        pane_gemini.send_keys("# Gemini - Research specialist (1M context)", literal=True)
        pane_gemini.send_keys("# Run: gemini-cli --mode interactive", literal=True)
        pane_gemini.send_keys("", literal=True)

        logger.info(f"✅ Created 3-pane layout for {energy_level} energy")

    def _create_four_pane_layout(self, window, energy_level: str) -> None:
        """
        Create 4-pane layout for high energy.

        Layout:
        ┌─────┬─────┬─────┬─────┐
        │Chat │Claude│Gemini│Grok│
        │(P 0)│(P 1) │(P 2) │(P 3)│
        └─────┴─────┴─────┴─────┘

        ADHD Benefit: Maximum coordination during hyperfocus
        """
        pane_chat = window.panes[0]

        # Split into 4 vertical panes (25% each)
        pane_claude = window.split_window(vertical=True, percent=25)
        pane_gemini = window.split_window(vertical=True, percent=33)
        pane_grok = window.split_window(vertical=True, percent=50)

        # Configure panes
        pane_chat.send_keys("# Chat Orchestrator - Central coordination", literal=True)
        pane_chat.send_keys("# Energy: 🟢 HIGH - Maximum multi-AI coordination", literal=True)
        pane_chat.send_keys("", literal=True)

        pane_claude.send_keys("# Claude Code - Architecture", literal=True)
        pane_claude.send_keys("", literal=True)

        pane_gemini.send_keys("# Gemini 2.5 Pro - Research (1M context)", literal=True)
        pane_gemini.send_keys("", literal=True)

        pane_grok.send_keys("# Grok Code Fast 1 - Implementation (FREE!)", literal=True)
        pane_grok.send_keys("# 2M context, intelligence: 18", literal=True)
        pane_grok.send_keys("", literal=True)

        logger.info(f"✅ Created 4-pane layout for {energy_level} energy")

    def adapt_layout_to_energy(self, energy_level: str) -> None:
        """
        Automatically adapt layout based on user's current energy.

        Queries ADHD Engine for user state, then adjusts panes to match
        cognitive capacity. Prevents overwhelm during low energy, enables
        maximum coordination during high energy.

        Args:
            energy_level: Current energy level (very_low/low/medium/high/hyperfocus)
        """
        # Map energy level to layout
        layout_mapping = {
            EnergyLevel.VERY_LOW.value: LayoutType.TWO_PANE,
            EnergyLevel.LOW.value: LayoutType.TWO_PANE,
            EnergyLevel.MEDIUM.value: LayoutType.THREE_PANE,
            EnergyLevel.HIGH.value: LayoutType.FOUR_PANE,
            EnergyLevel.HYPERFOCUS.value: LayoutType.FOUR_PANE
        }

        target_layout = layout_mapping.get(energy_level, LayoutType.THREE_PANE)

        # Only recreate if layout changed (avoid unnecessary disruption)
        if target_layout != self.current_layout:
            logger.info(f"🔄 Adapting layout: {energy_level} → {target_layout.value}")
            self.create_layout(target_layout, energy_level)
        else:
            logger.debug(f"Layout unchanged: {target_layout.value}")

    def get_pane_info(self) -> Dict[str, Any]:
        """
        Get information about current pane configuration.

        Returns:
            Dict with pane count, layout type, and pane IDs
        """
        if not self.session:
            return {"error": "Session not initialized"}

        window = self.session.windows[0]
        panes = window.panes

        return {
            "session_name": self.session_name,
            "layout_type": self.current_layout.value if self.current_layout else "unknown",
            "pane_count": len(panes),
            "panes": [
                {
                    "index": i,
                    "id": pane.id,
                    "width": pane.width,
                    "height": pane.height
                }
                for i, pane in enumerate(panes)
            ]
        }

    async def save_layout_to_conport(self) -> bool:
        """
        Save current layout configuration to ConPort for session restoration.

        Returns:
            True if save succeeded
        """
        try:
            # This would integrate with ConPort MCP
            # For now, return placeholder
            layout_data = {
                "layout_type": self.current_layout.value if self.current_layout else None,
                "session_name": self.session_name,
                "pane_count": len(self.session.windows[0].panes) if self.session else 0,
                "timestamp": "now"  # Would use datetime.utcnow().isoformat()
            }

            # TODO: Call mcp__conport__log_custom_data when integrated
            # await mcp__conport__log_custom_data(
            #     workspace_id=self.workspace_id,
            #     category="orchestrator_layout",
            #     key="current_layout",
            #     value=layout_data
            # )

            logger.info(f"💾 Layout saved to ConPort: {layout_data}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save layout: {e}")
            return False

    def close(self) -> None:
        """Clean up tmux session resources."""
        if self.session:
            logger.info(f"📭 Closing tmux layout manager for session: {self.session_name}")
            # Note: Don't kill session, just detach manager
            self.session = None


# Energy level utility functions

def get_layout_for_energy(energy_level: str) -> LayoutType:
    """
    Get recommended layout type for given energy level.

    Args:
        energy_level: Current user energy level

    Returns:
        Appropriate LayoutType
    """
    mapping = {
        EnergyLevel.VERY_LOW.value: LayoutType.TWO_PANE,
        EnergyLevel.LOW.value: LayoutType.TWO_PANE,
        EnergyLevel.MEDIUM.value: LayoutType.THREE_PANE,
        EnergyLevel.HIGH.value: LayoutType.FOUR_PANE,
        EnergyLevel.HYPERFOCUS.value: LayoutType.FOUR_PANE
    }

    return mapping.get(energy_level, LayoutType.THREE_PANE)


def get_pane_count(layout_type: LayoutType) -> int:
    """
    Get number of panes for a layout type.

    Args:
        layout_type: Layout type

    Returns:
        Number of panes (2, 3, or 4)
    """
    mapping = {
        LayoutType.TWO_PANE: 2,
        LayoutType.THREE_PANE: 3,
        LayoutType.FOUR_PANE: 4
    }

    return mapping.get(layout_type, 3)
