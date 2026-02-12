"""Compatibility session manager for profile switching."""

from __future__ import annotations

from pathlib import Path


class ProfileSessionManager:
    """Persist and restore Dopemux session context around profile changes."""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()

    def _context_manager(self):
        dopemux_dir = self.workspace / ".dopemux"
        if not dopemux_dir.exists():
            return None

        from dopemux.adhd import ContextManager  # lazy import for test monkeypatching

        return ContextManager(self.workspace)

    def save_session(self, reason: str):
        manager = self._context_manager()
        if manager is None:
            return None
        return manager.save_context(reason, force=True)

    def restore_session(self):
        manager = self._context_manager()
        if manager is None:
            return None
        return manager.restore_latest()

