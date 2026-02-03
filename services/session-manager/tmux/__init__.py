"""
Tmux module for Dopemux Orchestrator TUI.

Provides energy-adaptive tmux layout management for multi-AI coordination.
"""

from .layout_manager import (
    TmuxLayoutManager,
    LayoutType,
    EnergyLevel,
    get_layout_for_energy,
    get_pane_count
)

__all__ = [
    "TmuxLayoutManager",
    "LayoutType",
    "EnergyLevel",
    "get_layout_for_energy",
    "get_pane_count"
]
