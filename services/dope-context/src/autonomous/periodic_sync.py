"""Periodic sync fallback loop for autonomous indexing."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Optional


logger = logging.getLogger(__name__)


class PeriodicSync:
    """
    Runs workspace sync on a fixed interval to catch missed file events.
    """

    def __init__(
        self,
        workspace_path: Path,
        sync_callback: Callable[[Path], Awaitable[dict]],
        interval_seconds: int = 600,
    ):
        self.workspace_path = workspace_path.resolve()
        self.sync_callback = sync_callback
        self.interval_seconds = interval_seconds

        self._task: Optional[asyncio.Task] = None
        self._running = False

        self._sync_count = 0
        self._changes_detected = 0
        self._last_run_at: Optional[str] = None
        self._last_result: Optional[dict] = None
        self._last_error: Optional[str] = None

    async def start(self):
        """Start periodic sync task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        """Stop periodic sync task."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self):
        while self._running:
            await asyncio.sleep(self.interval_seconds)
            if not self._running:
                break

            try:
                result = await self.sync_callback(self.workspace_path)
                self._sync_count += 1
                self._last_run_at = datetime.now().isoformat()
                self._last_result = result

                changes = int(result.get("total_changes", result.get("changes", 0)))
                has_changes = bool(result.get("has_changes", changes > 0))
                if has_changes:
                    self._changes_detected += changes if changes > 0 else 1

            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._last_error = str(exc)
                logger.warning("Periodic sync failed for %s: %s", self.workspace_path, exc)

    def get_stats(self) -> dict:
        """Return periodic sync health/status metrics."""
        return {
            "running": self._running,
            "interval_seconds": self.interval_seconds,
            "sync_count": self._sync_count,
            "changes_detected": self._changes_detected,
            "last_run_at": self._last_run_at,
            "last_error": self._last_error,
            "last_result": self._last_result,
        }
