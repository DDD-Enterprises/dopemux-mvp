"""
Autonomous Controller - Zero-Touch Indexing Coordinator

Coordinates file monitoring, background indexing, and periodic sync
for fully autonomous code indexing operation.
"""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Set

from .watchdog_monitor import WatchdogMonitor
from .indexing_worker import IndexingWorker
from .periodic_sync import PeriodicSync


logger = logging.getLogger(__name__)


@dataclass
class AutonomousConfig:
    """Configuration for autonomous indexing."""

    enabled: bool = True
    debounce_seconds: float = 5.0
    periodic_interval: int = 600  # 10 minutes
    max_retries: int = 3
    retry_backoff: float = 2.0
    include_patterns: list = None
    exclude_patterns: list = None


class AutonomousController:
    """
    Autonomous indexing controller.

    Coordinates three subsystems for zero-touch operation:
    1. WatchdogMonitor - Immediate file change response
    2. IndexingWorker - Background async processing
    3. PeriodicSync - Safety fallback (every 10 min)
    """

    # Class-level registry of active controllers
    _active_controllers: Dict[str, "AutonomousController"] = {}

    def __init__(
        self,
        workspace_path: Path,
        index_callback: Callable[[Path, Optional[Set[str]]], asyncio.Future],
        sync_callback: Callable[[Path], asyncio.Future],
        config: Optional[AutonomousConfig] = None,
    ):
        """
        Initialize autonomous controller.

        Args:
            workspace_path: Absolute workspace path
            index_callback: Async function to trigger indexing
            sync_callback: Async function to trigger sync
            config: Configuration options
        """
        self.workspace_path = workspace_path.resolve()
        self.index_callback = index_callback
        self.sync_callback = sync_callback
        self.config = config or AutonomousConfig()

        # Components
        self.watchdog: Optional[WatchdogMonitor] = None
        self.worker: Optional[IndexingWorker] = None
        self.periodic: Optional[PeriodicSync] = None

        self._initialized: bool = False
        self._running: bool = False

    def _initialize_components(self):
        """Initialize all subsystem components."""
        if self._initialized:
            return

        logger.info(f"Initializing autonomous indexing for {self.workspace_path}")

        # Initialize worker
        self.worker = IndexingWorker(
            workspace_path=self.workspace_path,
            index_callback=self.index_callback,
            max_retries=self.config.max_retries,
            retry_backoff=self.config.retry_backoff,
        )

        # Initialize watchdog with worker callback
        self.watchdog = WatchdogMonitor(
            workspace_path=self.workspace_path,
            callback=self._on_files_changed,
            debounce_seconds=self.config.debounce_seconds,
            include_patterns=self.config.include_patterns,
            exclude_patterns=self.config.exclude_patterns,
        )

        # Initialize periodic sync
        self.periodic = PeriodicSync(
            workspace_path=self.workspace_path,
            sync_callback=self._on_periodic_sync,
            interval_seconds=self.config.periodic_interval,
        )

        self._initialized = True
        logger.info("Components initialized")

    def _on_files_changed(self, changed_files: Set[str]):
        """
        Callback when watchdog detects file changes.

        Args:
            changed_files: Set of changed file paths
        """
        logger.info(
            f"Watchdog detected {len(changed_files)} changed files, "
            f"enqueueing for indexing"
        )

        # Enqueue for worker (must be called from async context)
        asyncio.create_task(self.worker.enqueue_changes(changed_files))

    async def _on_periodic_sync(self, workspace_path: Path) -> dict:
        """
        Callback for periodic sync.

        Args:
            workspace_path: Workspace to sync

        Returns:
            Sync result dictionary
        """
        logger.debug("Periodic sync triggered")

        # Run sync callback
        result = await self.sync_callback(workspace_path)

        # If changes detected, trigger indexing
        if result and result.get("has_changes", False):
            changed_count = result.get("total_changes", 0)
            logger.info(
                f"Periodic sync found {changed_count} changes, "
                f"triggering reindex"
            )

            # Trigger full reindex for changed files
            # (sync_callback should have already identified which files)
            await self.index_callback(workspace_path, None)

        return result

    async def start(self):
        """Start autonomous indexing."""
        if not self.config.enabled:
            logger.info("Autonomous indexing disabled by config")
            return

        if self._running:
            logger.warning("Autonomous indexing already running")
            return

        logger.info(f"Starting autonomous indexing for {self.workspace_path}")

        # Initialize if needed
        if not self._initialized:
            self._initialize_components()

        # Start all components
        await self.worker.start()
        self.watchdog.start()
        await self.periodic.start()

        self._running = True

        # Register in global registry
        workspace_key = str(self.workspace_path)
        AutonomousController._active_controllers[workspace_key] = self

        logger.info(
            f"Autonomous indexing active for {self.workspace_path.name}"
        )

    async def stop(self):
        """Stop autonomous indexing gracefully."""
        if not self._running:
            return

        logger.info(f"Stopping autonomous indexing for {self.workspace_path}")

        # Stop all components
        self.watchdog.stop()
        await self.worker.stop()
        await self.periodic.stop()

        self._running = False

        # Unregister from global registry
        workspace_key = str(self.workspace_path)
        if workspace_key in AutonomousController._active_controllers:
            del AutonomousController._active_controllers[workspace_key]

        logger.info("Autonomous indexing stopped")

    def is_running(self) -> bool:
        """Check if autonomous indexing is running."""
        return self._running

    def get_status(self) -> dict:
        """Get comprehensive status of all components."""
        return {
            "workspace": str(self.workspace_path),
            "running": self._running,
            "enabled": self.config.enabled,
            "watchdog": self.watchdog.get_status() if self.watchdog else None,
            "worker": self.worker.get_stats() if self.worker else None,
            "periodic": self.periodic.get_stats() if self.periodic else None,
        }

    @classmethod
    def get_active_controllers(cls) -> Dict[str, "AutonomousController"]:
        """Get all active autonomous controllers."""
        return cls._active_controllers.copy()

    @classmethod
    async def stop_all(cls):
        """Stop all active autonomous controllers."""
        controllers = list(cls._active_controllers.values())

        for controller in controllers:
            await controller.stop()

        logger.info(f"Stopped {len(controllers)} autonomous controllers")
