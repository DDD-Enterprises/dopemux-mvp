"""
TUI State Manager - Central Coordinator for Orchestrator TUI

CRITICAL ARCHITECTURE COMPONENT:
Prevents main.py complexity explosion by coordinating all state managers.

Coordinates:
- ConPortProgressTracker (Day 4) - Command progress logging
- PomodoroBreakManager (Day 5) - Break reminders
- EnergyDetector (Day 5) - Energy level detection
- CommandHistoryManager (Day 5) - Command history
- TmuxLayoutManager (Optional) - Terminal integration

Benefits:
- Keeps main.py at ~400 lines (ADHD-friendly file size)
- Parallel initialization of all managers (faster startup)
- Single get_ui_state() call (optimized UI updates)
- Clean testing boundaries (test managers independently + coordinator)
- Easy to add new managers without touching main.py

Architecture Pattern: Coordinator/Facade
- Provides simplified interface to complex subsystem
- Handles parallel operations automatically
- Coordinates cross-manager interactions
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from .conport_tracker import ConPortProgressTracker, get_progress_tracker
from .break_manager import PomodoroBreakManager, get_break_manager
from .energy_detector import EnergyDetector, get_energy_detector
from .command_history import CommandHistoryManager, get_history_manager

logger = logging.getLogger(__name__)


class TUIStateManager:
    """
    Central coordinator for all TUI state and integration managers.

    Responsibilities:
    - Initialize all managers in parallel
    - Coordinate command lifecycle (start/complete)
    - Provide single optimized UI state query
    - Handle manager interactions (e.g., breaks affect energy)
    - Graceful degradation if any manager fails
    """

    def __init__(self, workspace_id: str):
        """
        Initialize TUI state manager.

        Args:
            workspace_id: Absolute path to workspace (/Users/hue/code/dopemux-mvp)
        """
        self.workspace_id = workspace_id

        # Initialize all managers (using singletons for consistency)
        self.progress = get_progress_tracker(workspace_id)
        self.breaks = get_break_manager(workspace_id)
        self.energy = get_energy_detector(workspace_id)
        self.history = get_history_manager(workspace_id)

        # Optional tmux integration
        self.tmux_enabled = False
        self.tmux_manager = None

        # State
        self._initialized = False
        self.initialization_results: Dict[str, bool] = {}

        logger.info(f"🎛️  TUI State Manager created for {workspace_id}")

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize all managers in parallel.

        Returns:
            Dictionary with initialization results and any warnings
        """
        if self._initialized:
            return {"already_initialized": True}

        logger.info("🚀 Initializing all TUI state managers in parallel...")

        # Parallel initialization for speed
        results = await asyncio.gather(
            self.progress.initialize(),
            self.breaks.initialize(),
            self.energy.initialize(),
            self.history.initialize(),
            return_exceptions=True
        )

        # Check results
        manager_names = ["progress", "breaks", "energy", "history"]
        for i, result in enumerate(results):
            manager = manager_names[i]
            if isinstance(result, Exception):
                self.initialization_results[manager] = False
                logger.error(f"❌ {manager} initialization failed: {result}")
            else:
                self.initialization_results[manager] = True
                logger.info(f"✅ {manager} initialized")

        self._initialized = True

        # Summary
        successful = sum(self.initialization_results.values())
        total = len(self.initialization_results)

        return {
            "initialized": True,
            "successful_managers": successful,
            "total_managers": total,
            "managers": self.initialization_results,
            "warnings": [] if successful == total else [
                f"{name} failed" for name, success in self.initialization_results.items() if not success
            ]
        }

    async def close(self):
        """Clean up all managers and finalize session."""
        logger.info("🔒 Closing all TUI state managers...")

        # Close all managers in parallel
        close_tasks = [
            self.progress.close(),
            self.breaks.close(),
            self.energy.close(),
            self.history.close()
        ]

        await asyncio.gather(*close_tasks, return_exceptions=True)

        self._initialized = False
        logger.info("✅ All managers closed successfully")

    # === Command Lifecycle Coordination ===

    async def on_command_start(self, ai: str, command: str) -> Dict[str, Any]:
        """
        Coordinate all actions when command starts.

        Args:
            ai: AI executing the command (claude/gemini/grok)
            command: Command being executed

        Returns:
            Dictionary with progress_id and any warnings
        """
        # Record activity for break timer
        self.breaks.record_activity()

        # Add to history (sync, with privacy filter)
        history_added = self.history.add_command(ai, command)

        # Log to ConPort progress
        progress_id = await self.progress.log_command_start(ai, command)

        return {
            "progress_id": progress_id,
            "history_added": history_added,
            "timestamp": datetime.now().isoformat()
        }

    async def on_command_complete(self, ai: str, exit_code: int, error_message: str = None) -> Dict[str, Any]:
        """
        Coordinate all actions when command completes.

        Args:
            ai: AI that executed
            exit_code: Command exit code
            error_message: Error message if failed

        Returns:
            Dictionary with status and any special notifications (e.g., break needed)
        """
        status = "DONE" if exit_code == 0 else "BLOCKED"

        # Update progress in ConPort
        await self.progress.update_command_progress(ai, status, exit_code, error_message)

        # Save to command history with result
        if self.history._initialized:
            # Get the last command from history
            recent_commands = self.history.get_recent(1)
            if recent_commands:
                last_command = recent_commands[0]
                # Extract command text (remove @ai prefix)
                command_text = last_command.split(maxsplit=1)[1] if " " in last_command else last_command
                await self.history.save_command(ai, command_text, exit_code)

        # Check if break needed
        break_needed = self.breaks.should_suggest_break()
        break_mandatory = self.breaks.should_mandate_break()

        result = {
            "status": status,
            "break_suggested": break_needed,
            "break_mandatory": break_mandatory
        }

        if break_needed:
            elapsed = self.breaks.get_elapsed_minutes()
            result["break_message"] = f"☕ {elapsed} minutes focused - break recommended!"

        if break_mandatory:
            result["break_message"] = f"🚨 {self.breaks.get_elapsed_minutes()} min! Please take a break (hyperfocus protection)"

        return result

    async def get_ui_state(self) -> Dict[str, Any]:
        """
        Get complete UI state from all managers (single optimized call).

        Returns:
            Dictionary with progress, break, energy, history state
        """
        # Parallel queries for speed
        progress_stats, break_state, energy_state = await asyncio.gather(
            self.progress.get_progress_stats(),
            self.breaks.get_state_async(),
            self.energy.get_current_energy_async(),
            return_exceptions=True
        )

        # Handle exceptions gracefully
        if isinstance(progress_stats, Exception):
            logger.error(f"Progress stats failed: {progress_stats}")
            progress_stats = {"error": str(progress_stats)}

        if isinstance(break_state, Exception):
            logger.error(f"Break state failed: {break_state}")
            break_state = {"error": str(break_state)}

        if isinstance(energy_state, Exception):
            logger.error(f"Energy state failed: {energy_state}")
            energy_state = {"error": str(energy_state)}

        # Sync query for history (fast, no await needed)
        history_count = self.history.get_count()

        return {
            "progress": progress_stats,
            "break": break_state,
            "energy": energy_state,
            "history_size": history_count,
            "timestamp": datetime.now().isoformat()
        }

    async def refresh_energy(self) -> str:
        """
        Manually refresh energy level detection.

        Returns:
            New energy level
        """
        new_energy = await self.energy.detect_energy()
        logger.info(f"🔄 Energy refreshed: {new_energy.value}")
        return new_energy.value

    def get_history_navigation(self, direction: str) -> Optional[str]:
        """
        Navigate command history.

        Args:
            direction: "up" or "down"

        Returns:
            Command from history or None
        """
        if direction == "up":
            return self.history.navigate_up()
        elif direction == "down":
            return self.history.navigate_down()
        else:
            logger.warning(f"Invalid navigation direction: {direction}")
            return None

    def enable_tmux_mode(self, session_name: str = "dopemux"):
        """
        Enable optional tmux integration.

        Args:
            session_name: Tmux session name
        """
        try:
            from ..tmux.layout_manager import TmuxLayoutManager
            self.tmux_manager = TmuxLayoutManager(session_name, self.workspace_id)
            self.tmux_enabled = True
            logger.info(f"✅ Tmux mode enabled: {session_name}")
        except Exception as e:
            logger.error(f"❌ Failed to enable tmux mode: {e}")
            self.tmux_enabled = False

    async def adapt_tmux_layout_to_energy(self):
        """Adapt tmux layout based on current energy (if tmux enabled)."""
        if not self.tmux_enabled or not self.tmux_manager:
            return

        try:
            energy_level = self.energy.current_energy.value
            self.tmux_manager.adapt_layout_to_energy(energy_level)
            logger.info(f"🎨 Tmux layout adapted to {energy_level}")
        except Exception as e:
            logger.error(f"❌ Tmux layout adaptation failed: {e}")

    # === Health and Status ===

    def get_manager_health(self) -> Dict[str, str]:
        """
        Get health status of all managers.

        Returns:
            Dictionary with manager name -> status
        """
        return {
            "progress": "healthy" if self.progress._initialized else "not_initialized",
            "breaks": "healthy" if self.breaks._initialized else "not_initialized",
            "energy": "healthy" if self.energy._initialized else "not_initialized",
            "history": "healthy" if self.history._initialized else "not_initialized",
            "tmux": "enabled" if self.tmux_enabled else "disabled"
        }


# Singleton instance
_state_manager: Optional[TUIStateManager] = None


def get_state_manager(workspace_id: str = None) -> TUIStateManager:
    """Get singleton TUI state manager instance."""
    global _state_manager

    if _state_manager is None:
        if workspace_id is None:
            workspace_id = os.getcwd()
        _state_manager = TUIStateManager(workspace_id)

    return _state_manager
