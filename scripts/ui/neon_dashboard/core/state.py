"""Shared state management for the Dope layout dashboard."""

from __future__ import annotations
import logging


import asyncio
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional

from ..config.settings import DopeLayoutSettings, ModeLiteral


logger = logging.getLogger(__name__)

@dataclass(slots=True)
class DashboardState:
    """Serializable dashboard state shared across panes."""

    mode: ModeLiteral = "implementation"
    selected_task_id: Optional[str] = None
    selected_task_name: Optional[str] = None
    active_transient_id: Optional[str] = None
    version: int = 0  # increment whenever the state changes

    @classmethod
    def from_dict(cls, payload: dict) -> "DashboardState":
        mode = payload.get("mode", "implementation")
        if mode not in {"implementation", "pm"}:
            mode = "implementation"
        return cls(
            mode=mode,  # type: ignore[arg-type]
            selected_task_id=payload.get("selected_task_id"),
            selected_task_name=payload.get("selected_task_name"),
            active_transient_id=payload.get("active_transient_id"),
            version=int(payload.get("version", 0) or 0),
        )

    def to_dict(self) -> dict:
        return asdict(self)


class DashboardStateStore:
    """
    A cooperative state store backed by a JSON file on disk.

    Each Textual pane instance polls the file's modification timestamp to
    stay in sync with other panes.  Updates are guarded with an asyncio
    lock to avoid concurrent writes within a single process.
    """

    def __init__(self, settings: DopeLayoutSettings):
        self.settings = settings
        self.path: Path = settings.state_file
        self._state = DashboardState(mode=settings.default_mode)
        self._lock = asyncio.Lock()
        self._mtime: float = 0.0
        self._listeners: list[Callable[[DashboardState], None]] = []
        self._ensure_storage_path()

    def add_listener(self, callback: Callable[[DashboardState], None]) -> None:
        """Register a callback invoked whenever state changes."""
        self._listeners.append(callback)

    def _notify(self) -> None:
        for callback in list(self._listeners):
            try:
                callback(self._state)
            except Exception as e:
                # Listeners should be resilient; ignore failures to avoid loops.
                continue

                logger.error(f"Error: {e}")
    async def load(self) -> DashboardState:
        """Load state from disk if present."""
        if not self.path.exists():
            await self._write_locked(create_parents=True)
            return self._state
        try:
            data = await asyncio.to_thread(self.path.read_text)
            payload = json.loads(data)
        except (json.JSONDecodeError, OSError):
            payload = {}
        self._state = DashboardState.from_dict(payload)
        try:
            self._mtime = self.path.stat().st_mtime
        except OSError:
            self._mtime = time.time()
        self._notify()
        return self._state

    def _ensure_storage_path(self) -> None:
        """Ensure the storage directory exists, falling back if necessary."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = Path.cwd() / ".dopemux" / "dope_dashboard_state.json"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            self.path = fallback

    async def _write_locked(self, create_parents: bool = False) -> None:
        """Persist state to disk under the protection of the asyncio lock."""
        if create_parents:
            self._ensure_storage_path()
        serialized = json.dumps(self._state.to_dict(), indent=2)
        try:
            await asyncio.to_thread(
                self.path.write_text,
                serialized,
            )
        except PermissionError:
            # Final fallback: use a temporary directory inside cwd
            fallback = Path.cwd() / ".dopemux" / "dope_dashboard_state.json"
            fallback.parent.mkdir(parents=True, exist_ok=True)
            self.path = fallback
            await asyncio.to_thread(self.path.write_text, serialized)
        try:
            self._mtime = self.path.stat().st_mtime
        except OSError:
            self._mtime = time.time()

    async def _bump_and_write(self) -> None:
        self._state.version += 1
        await self._write_locked()
        self._notify()

    async def toggle_mode(self) -> ModeLiteral:
        """Toggle between implementation and PM modes."""
        async with self._lock:
            self._state.mode = "pm" if self._state.mode == "implementation" else "implementation"
            await self._bump_and_write()
            return self._state.mode

    async def set_mode(self, mode: ModeLiteral) -> None:
        """Force a specific mode (used by elevated events)."""
        async with self._lock:
            if self._state.mode != mode:
                self._state.mode = mode
                await self._bump_and_write()

    async def set_selected_task(self, task_id: Optional[str], task_name: Optional[str]) -> None:
        """Update the selected task metadata."""
        async with self._lock:
            self._state.selected_task_id = task_id
            self._state.selected_task_name = task_name
            await self._bump_and_write()

    async def set_active_transient(self, transient_id: Optional[str]) -> None:
        """Record the currently visible transient message."""
        async with self._lock:
            self._state.active_transient_id = transient_id
            await self._bump_and_write()

    async def poll_external_updates(self) -> Optional[DashboardState]:
        """
        Check for changes written by other processes.

        Returns the updated state if a change was detected, otherwise None.
        """
        try:
            mtime = self.path.stat().st_mtime
        except OSError:
            return None
        if mtime <= self._mtime:
            return None
        await self.load()
        return self._state

    @property
    def state(self) -> DashboardState:
        """Return the last cached state."""
        return self._state
