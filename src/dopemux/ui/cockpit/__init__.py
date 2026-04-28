"""Dopemux Cockpit TUI package.

Architecture-safe operator control surface. PM authority is split across
Leantime (metadata), task-orchestrator (workflow), ConPort (decisions/
progress), dope-memory (chronicle), dope-context (retrieval). The
dopecon-bridge surface is adapter/proxy only and never canonical
authority.

This package emits no live writes and no PM mutations. The first slice
ships static / demo data clearly labeled as such.
"""

from .render import (
    TOO_SMALL_MESSAGE,
    TOP_LEVEL_MODES,
    PaneDeclaration,
    Top3Block,
    render_pm,
    viewport_supported,
)

__all__ = [
    "TOO_SMALL_MESSAGE",
    "TOP_LEVEL_MODES",
    "PaneDeclaration",
    "Top3Block",
    "render_pm",
    "viewport_supported",
]
