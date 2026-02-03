"""
Shared types and exceptions for tmux integration.
"""
from dataclasses import dataclass

class TmuxError(RuntimeError):
    """Raised when tmux operations fail."""


@dataclass
class PaneInfo:
    """Lightweight representation of a tmux pane."""
    pane_id: str
    title: str
    command: str
    window: str
    session: str
    path: str
    active: bool

    @property
    def label(self) -> str:
        """Return a human-readable label for the pane."""
        return self.title or self.window or self.pane_id

# Backward compatibility alias
TmuxPane = PaneInfo
