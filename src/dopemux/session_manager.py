"""
Profile switch session-state helpers.

Provides an explicit ``session_manager`` module path for Epic-3 deliverables.
"""

from pathlib import Path
from typing import Any, Dict, Optional


class ProfileSessionManager:
    """Save and restore workspace context around profile switches."""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = (workspace or Path.cwd()).resolve()

    def save_session(self, reason: str) -> Optional[str]:
        """Persist current workspace context snapshot."""
        if not (self.workspace / ".dopemux").exists():
            return None

        from .adhd import ContextManager

        context_manager = ContextManager(self.workspace)
        return context_manager.save_context(message=reason, force=True)

    def restore_session(self) -> Optional[Dict[str, Any]]:
        """Restore latest workspace context snapshot."""
        if not (self.workspace / ".dopemux").exists():
            return None

        from .adhd import ContextManager

        context_manager = ContextManager(self.workspace)
        return context_manager.restore_latest()

