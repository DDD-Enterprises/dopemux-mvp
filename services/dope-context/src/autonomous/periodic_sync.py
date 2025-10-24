"""
Periodic Sync - Fallback Safety Net

Runs periodic change checks to catch any events watchdog might miss.
Lightweight and reliable.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class PeriodicSync:
    """
    Periodic synchronization fallback.

    Runs change detection at regular intervals as safety net.
    """

    def __init__(
        self,
        workspace_path: Path,
        sync_callback: Callable[[Path], asyncio.Future],
        interval_seconds: int = 600,  # 10 minutes default
    ):
        """
        Initialize periodic sync.

        Args:
            workspace_path: Absolute workspace path
            sync_callback: Async function to trigger sync
            interval_seconds: Interval between sync checks
        """
        self.workspace_path = workspace_path.resolve()
        self.sync_callback = sync_callback
        self.interval_seconds = interval_seconds

        self._running: bool = False
        self._sync_task: Optional[asyncio.Task] = None
        self.last_sync: Optional[datetime] = None
        self.sync_count: int = 0
        self.changes_detected: int = 0

    async def _sync_loop(self):
        """Background sync loop."""
        logger.info(
            f"Periodic sync started (interval: {self.interval_seconds}s)"
        )

        while self._running:
            try:
                # Wait for interval
                await asyncio.sleep(self.interval_seconds)

                # Run sync check
                logger.debug("Running periodic sync check")
                result = await self.sync_callback(self.workspace_path)

                self.sync_count += 1
                self.last_sync = datetime.now()

                # Log if changes detected
                if result and result.get("total_changes", 0) > 0:
                    changes = result["total_changes"]
                    self.changes_detected += changes
                    logger.info(
                        f"Periodic sync detected {changes} changes, "
                        f"triggering reindex"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Periodic sync error: {e}")
                # Continue running despite errors

        logger.info("Periodic sync stopped")

    async def start(self):
        """Start periodic sync."""
        if self._running:
            logger.warning("Periodic sync already running")
            return

        logger.info(
            f"Starting periodic sync (every {self.interval_seconds}s)"
        )
        self._running = True
        self._sync_task = asyncio.create_task(self._sync_loop())

    async def stop(self):
        """Stop periodic sync."""
        if not self._running:
            return

        logger.info("Stopping periodic sync")
        self._running = False

        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass

        logger.info("Periodic sync stopped")

    def is_running(self) -> bool:
        """Check if periodic sync is running."""
        return self._running

    def get_stats(self) -> dict:
        """Get periodic sync statistics."""
        return {
            "running": self._running,
            "interval_seconds": self.interval_seconds,
            "sync_count": self.sync_count,
            "changes_detected": self.changes_detected,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }
