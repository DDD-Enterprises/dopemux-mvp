"""
Session Manager for Orchestrator TUI

Day 6: Session persistence with ConPort integration for:
- Auto-save every 30 seconds
- Session restore on startup
- Interrupt recovery
- Command history preservation
- Pane state persistence

ADHD Benefits:
- Zero-friction resume after interruptions
- Preserves mental context across sessions
- Visual indicators of session age
- Automatic state preservation (no manual saves)

Part of IP-005 Day 6: Session persistence
"""

import asyncio
import aiohttp
import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PaneState:
    """State of a single AI output pane."""
    ai_name: str
    output_lines: List[str]
    status: str  # ready, busy, error
    command_history: List[str]
    last_command: Optional[str] = None
    last_update: Optional[str] = None


@dataclass
class TUISessionState:
    """Complete TUI session state for persistence."""
    session_id: str
    workspace_id: str
    session_start: str  # ISO timestamp
    last_active: str  # ISO timestamp
    current_target: str  # claude, gemini, grok
    energy_level: str  # low, medium, high

    # Pane states
    pane_states: Dict[str, PaneState]

    # Progress tracking
    tasks_done: int = 0
    tasks_total: int = 0
    session_progress: int = 0
    break_timer_seconds: int = 1500

    # Statistics
    total_commands: int = 0
    successful_commands: int = 0
    session_duration_minutes: int = 0

    # Metadata
    created_at: Optional[str] = None
    version: str = "1.0"


class SessionManager:
    """
    Manages TUI session persistence with ConPort.

    Features:
    - Auto-save every 30 seconds
    - Restore session on startup
    - Command history preservation
    - Pane state persistence
    - Integration Bridge HTTP API
    """

    # ConPort Integration Bridge endpoints
    BRIDGE_BASE_URL = "http://localhost:3016"
    CONPORT_CATEGORY = "tui_session_state"
    AUTO_SAVE_INTERVAL = 30  # seconds

    def __init__(self, workspace_id: str, session_id: Optional[str] = None):
        """
        Initialize session manager.

        Args:
            workspace_id: Workspace path for ConPort tracking
            session_id: Optional session ID (generated if not provided)
        """
        self.workspace_id = workspace_id
        self.session_id = session_id or self._generate_session_id()
        self.auto_save_task: Optional[asyncio.Task] = None
        self._http_session: Optional[aiohttp.ClientSession] = None

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"tui_session_{timestamp}"

    async def initialize(self) -> None:
        """Initialize HTTP session for ConPort communication."""
        self._http_session = aiohttp.ClientSession()
        logger.info(f"📡 Session manager initialized: {self.session_id}")

    async def cleanup(self) -> None:
        """Cleanup HTTP session and stop auto-save."""
        if self.auto_save_task:
            self.auto_save_task.cancel()
            try:
                await self.auto_save_task
            except asyncio.CancelledError:
                pass

        if self._http_session:
            await self._http_session.close()

    async def save_session_state(self, state: TUISessionState) -> bool:
        """
        Save session state to ConPort.

        Args:
            state: Current TUI session state

        Returns:
            True if saved successfully
        """
        try:
            # Convert state to JSON
            state_dict = asdict(state)

            # Convert PaneState objects to dicts
            state_dict['pane_states'] = {
                ai: asdict(pane) for ai, pane in state.pane_states.items()
            }

            # Save via Integration Bridge
            url = f"{self.BRIDGE_BASE_URL}/api/custom-data"
            payload = {
                "workspace_id": self.workspace_id,
                "category": self.CONPORT_CATEGORY,
                "key": self.session_id,
                "value": state_dict
            }

            async with self._http_session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    logger.debug(f"💾 Session state saved: {self.session_id}")
                    return True
                else:
                    error_text = await resp.text()
                    logger.warning(f"⚠️ ConPort save failed ({resp.status}): {error_text}")
                    return False

        except asyncio.TimeoutError:
            logger.warning("⏰ ConPort save timed out (non-critical)")
            return False
        except Exception as e:
            logger.warning(f"⚠️ ConPort save failed (non-critical): {e}")
            return False

    async def load_session_state(self, session_id: Optional[str] = None) -> Optional[TUISessionState]:
        """
        Load session state from ConPort.

        Args:
            session_id: Session ID to load (uses current if not provided)

        Returns:
            TUISessionState if found, None otherwise
        """
        target_session = session_id or self.session_id

        try:
            url = f"{self.BRIDGE_BASE_URL}/api/custom-data"
            params = {
                "workspace_id": self.workspace_id,
                "category": self.CONPORT_CATEGORY,
                "key": target_session
            }

            async with self._http_session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    # Extract value from response
                    if isinstance(data, list) and len(data) > 0:
                        state_dict = data[0].get('value', {})
                    elif isinstance(data, dict):
                        state_dict = data.get('value', {})
                    else:
                        return None

                    # Reconstruct PaneState objects
                    if 'pane_states' in state_dict:
                        state_dict['pane_states'] = {
                            ai: PaneState(**pane_data)
                            for ai, pane_data in state_dict['pane_states'].items()
                        }

                    # Reconstruct TUISessionState
                    session_state = TUISessionState(**state_dict)
                    logger.info(f"✅ Session state loaded: {target_session}")
                    return session_state
                else:
                    logger.debug(f"No session state found for {target_session}")
                    return None

        except Exception as e:
            logger.warning(f"⚠️ Session load failed (non-critical): {e}")
            return None

    async def list_recent_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        List recent TUI sessions from ConPort.

        Args:
            limit: Maximum sessions to return

        Returns:
            List of session summaries
        """
        try:
            url = f"{self.BRIDGE_BASE_URL}/api/custom-data"
            params = {
                "workspace_id": self.workspace_id,
                "category": self.CONPORT_CATEGORY
            }

            async with self._http_session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    # Extract session summaries
                    sessions = []
                    for item in data[:limit]:
                        value = item.get('value', {})
                        sessions.append({
                            'session_id': value.get('session_id'),
                            'last_active': value.get('last_active'),
                            'total_commands': value.get('total_commands', 0),
                            'session_duration': value.get('session_duration_minutes', 0)
                        })

                    return sessions
                else:
                    return []

        except Exception as e:
            logger.warning(f"⚠️ Session list failed: {e}")
            return []

    async def start_auto_save(self, get_state_callback) -> None:
        """
        Start auto-save loop.

        Args:
            get_state_callback: Async function that returns current TUISessionState
        """
        async def auto_save_loop():
            while True:
                try:
                    await asyncio.sleep(self.AUTO_SAVE_INTERVAL)

                    # Get current state from TUI
                    state = await get_state_callback()

                    # Save to ConPort
                    await self.save_session_state(state)

                except asyncio.CancelledError:
                    logger.info("Auto-save loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Auto-save error: {e}")
                    # Continue loop despite errors

        self.auto_save_task = asyncio.create_task(auto_save_loop())
        logger.info(f"🔄 Auto-save started (every {self.AUTO_SAVE_INTERVAL}s)")

    async def stop_auto_save(self) -> None:
        """Stop auto-save loop."""
        if self.auto_save_task:
            self.auto_save_task.cancel()
            try:
                await self.auto_save_task
            except asyncio.CancelledError:
                pass
            logger.info("Auto-save stopped")

    def format_session_age(self, last_active_iso: str) -> str:
        """
        Format session age for ADHD-friendly display.

        Args:
            last_active_iso: ISO timestamp string

        Returns:
            Human-readable age string
        """
        try:
            last_active = datetime.fromisoformat(last_active_iso)
            age = datetime.now() - last_active

            if age.total_seconds() < 60:
                return "just now"
            elif age.total_seconds() < 3600:
                minutes = int(age.total_seconds() / 60)
                return f"{minutes}m ago"
            elif age.total_seconds() < 86400:
                hours = int(age.total_seconds() / 3600)
                return f"{hours}h ago"
            else:
                days = int(age.total_seconds() / 86400)
                return f"{days}d ago"

        except Exception:
            return "unknown"


# Singleton instance
_session_manager_instance: Optional[SessionManager] = None


def get_session_manager(workspace_id: str, session_id: Optional[str] = None) -> SessionManager:
    """Get or create session manager singleton."""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager(workspace_id, session_id)
    return _session_manager_instance
