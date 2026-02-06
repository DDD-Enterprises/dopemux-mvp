"""State coordinator for session-manager TUI components."""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from .break_manager import get_break_manager
from .command_history import get_history_manager
from .conport_tracker import get_progress_tracker
from .energy_detector import get_energy_detector


logger = logging.getLogger(__name__)


class TUIStateManager:
    """
    Coordinates TUI state across progress tracking, breaks, energy, and history.
    """

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.progress = get_progress_tracker(workspace_id)
        self.breaks = get_break_manager(workspace_id)
        self.energy = get_energy_detector(workspace_id)
        self.history = get_history_manager(workspace_id)
        self._initialized = False

    async def initialize(self) -> Dict[str, Any]:
        """Initialize all backing managers concurrently."""
        managers = {
            "progress": self.progress.initialize(),
            "breaks": self.breaks.initialize(),
            "energy": self.energy.initialize(),
            "history": self.history.initialize(),
        }

        results = await asyncio.gather(*managers.values(), return_exceptions=True)
        warnings = []
        successful = 0

        for name, result in zip(managers.keys(), results):
            if isinstance(result, Exception):
                warnings.append(f"{name} manager initialization failed: {result}")
            else:
                successful += 1

        self._initialized = successful > 0
        return {
            "successful_managers": successful,
            "total_managers": len(managers),
            "managers": list(managers.keys()),
            "warnings": warnings,
        }

    async def on_command_start(self, ai: str, command: str) -> Dict[str, Any]:
        """Coordinate state updates when a command starts."""
        if not self._initialized:
            await self.initialize()

        history_added = self.history.add_command(ai, command)
        self.breaks.record_activity()
        progress_id = await self.progress.log_command_start(ai, command)

        return {
            "progress_id": progress_id,
            "history_added": history_added,
            "timestamp": datetime.now().isoformat(),
        }

    async def on_command_complete(
        self,
        ai: str,
        exit_code: int,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Coordinate state updates when a command completes."""
        status = "DONE" if exit_code == 0 else "BLOCKED"

        active_command = self.progress.active_commands.get(ai)
        command_text = active_command.command if active_command else ""

        await self.progress.update_command_progress(
            ai_name=ai,
            status=status,
            exit_code=exit_code,
            error_message=error_message,
        )

        if command_text:
            await self.history.save_command(ai, command_text, exit_code)

        self.breaks.record_activity()
        break_state = await self.breaks.get_state_async()
        break_suggested = bool(break_state.get("break_suggested", False))

        return {
            "status": status,
            "break_suggested": break_suggested,
            "break_message": break_state.get("message") if break_suggested else None,
        }

    async def get_ui_state(self) -> Dict[str, Any]:
        """Fetch complete UI state in one call for efficient TUI refresh."""
        if not self._initialized:
            await self.initialize()

        # Refresh current energy before exposing state.
        await self.energy.detect_energy()

        progress_task = self.progress.get_progress_stats()
        break_task = self.breaks.get_state_async()
        energy_task = self.energy.get_current_energy_async()

        progress, break_state, energy = await asyncio.gather(
            progress_task,
            break_task,
            energy_task,
        )

        return {
            "progress": progress,
            "break": break_state,
            "energy": energy,
            "history_size": self.history.get_count(),
            "recent_commands": self.history.get_recent(10),
        }

    def get_history_navigation(self, direction: str) -> Optional[str]:
        """Navigate command history for up/down arrow handling."""
        direction_norm = (direction or "").lower()
        if direction_norm == "up":
            return self.history.navigate_up()
        if direction_norm == "down":
            return self.history.navigate_down()
        return None

    def get_manager_health(self) -> Dict[str, str]:
        """Return coarse health status for each manager."""
        return {
            "progress": "healthy" if self.progress._initialized else "degraded",
            "breaks": "healthy" if self.breaks._initialized else "degraded",
            "energy": "healthy" if self.energy._initialized else "degraded",
            "history": "healthy" if self.history._initialized else "degraded",
            "state_manager": "enabled" if self._initialized else "disabled",
        }

    async def close(self):
        """Close all managers gracefully."""
        await asyncio.gather(
            self.progress.close(),
            self.breaks.close(),
            self.energy.close(),
            self.history.close(),
            return_exceptions=True,
        )
        self._initialized = False


_state_manager_instance: Optional[TUIStateManager] = None


def get_state_manager(workspace_id: Optional[str] = None) -> TUIStateManager:
    """Get singleton TUI state manager."""
    global _state_manager_instance

    resolved_workspace = workspace_id or os.getcwd()
    if _state_manager_instance is None or _state_manager_instance.workspace_id != resolved_workspace:
        _state_manager_instance = TUIStateManager(resolved_workspace)
    return _state_manager_instance
