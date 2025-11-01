#!/usr/bin/env python3
"""
Workspace Watcher - Automatic Workspace Switch Detection

Polls active application every 5 seconds and emits workspace.switched events
when application changes, enabling automatic ADHD activity tracking.
"""

import asyncio
import logging
import argparse
import signal
import sys
from typing import Optional

from app_detector import AppDetector
from workspace_mapper import WorkspaceMapper
from event_emitter import WorkspaceSwitchEmitter
from file_activity_checker import FileActivityChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkspaceWatcher:
    """
    Monitors active application and emits workspace switch events.

    Features:
    - Configurable poll interval (default: 5s)
    - OS-specific app detection (macOS/Linux)
    - User-defined app-to-workspace mappings
    - Automatic event emission to Redis Streams
    - Graceful shutdown
    """

    def __init__(
        self,
        poll_interval: int = 5,
        redis_url: str = "redis://redis-primary:6379",
        config_path: str = "config.json"
    ):
        """
        Initialize workspace watcher.

        Args:
            poll_interval: Seconds between app checks (default: 5)
            redis_url: Redis connection URL
            config_path: Path to workspace mappings config
        """
        self.poll_interval = poll_interval
        self.running = False

        # Components
        self.app_detector = AppDetector()
        self.workspace_mapper = WorkspaceMapper(config_path=config_path)
        self.event_emitter = WorkspaceSwitchEmitter(redis_url=redis_url)
        self.file_checker = FileActivityChecker(recency_threshold=30)

        # State
        self.current_app: Optional[str] = None
        self.current_workspace: Optional[str] = None

        # Metrics
        self.polls = 0
        self.switches_detected = 0

    async def initialize(self):
        """Initialize event emitter connection"""
        logger.info("=" * 60)
        logger.info("Workspace Watcher - Initializing...")
        logger.info("=" * 60)

        await self.event_emitter.initialize()

        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info(f"OS: {self.app_detector.os_type}")
        logger.info(f"Workspace mappings: {len(self.workspace_mapper.mappings)}")
        logger.info("")

    async def start(self):
        """Start monitoring active application"""
        self.running = True
        logger.info("Workspace watcher started")
        logger.info("Monitoring active application for workspace switches...")
        logger.info("")

        # Get initial state
        self.current_app = self.app_detector.get_active_app()
        if self.current_app:
            self.current_workspace = self.workspace_mapper.get_workspace(self.current_app)
            logger.info(f"Initial state: {self.current_app} → {self.current_workspace or 'N/A'}")
        else:
            logger.warning("Could not detect initial app")

        logger.info("")

        # Main polling loop
        while self.running:
            try:
                await self._poll_and_check()
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                logger.info("Watcher loop cancelled")
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _poll_and_check(self):
        """Poll active app and check for changes"""
        self.polls += 1

        # Detect current app (use async version to avoid blocking)
        active_app = await self.app_detector.get_active_app_async()

        if not active_app:
            logger.debug(f"Poll #{self.polls}: No app detected")
            return

        # Check if app changed
        if active_app != self.current_app:
            logger.info(f"App change detected: {self.current_app or '?'} → {active_app}")

            # Map to workspaces
            from_workspace = self.current_workspace
            to_workspace = self.workspace_mapper.get_workspace(active_app)

            # Check for recent file activity (if switching to dev workspace)
            file_activity = None
            if to_workspace:
                file_activity = self.file_checker.check_recent_activity(to_workspace)
                if file_activity["has_recent_activity"]:
                    logger.info(
                        f"  File activity: {file_activity['files_modified']} files modified "
                        f"({file_activity['seconds_since_last_save']}s ago)"
                    )

            # Emit event
            success = await self.event_emitter.emit_workspace_switch(
                from_workspace=from_workspace,
                to_workspace=to_workspace,
                from_app=self.current_app or "unknown",
                to_app=active_app,
                file_activity=file_activity  # Include file activity data
            )

            if success:
                self.switches_detected += 1

            # Update current state
            self.current_app = active_app
            self.current_workspace = to_workspace

        else:
            logger.debug(f"Poll #{self.polls}: Still in {active_app}")

    async def stop(self):
        """Stop monitoring"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("Workspace Watcher - Shutting down...")
        logger.info("=" * 60)

        self.running = False

        # Show final metrics
        metrics = self.get_metrics()
        logger.info(f"Total polls: {metrics['polls']}")
        logger.info(f"Switches detected: {metrics['switches_detected']}")
        logger.info(f"Events emitted: {metrics['events_emitted']}")

        await self.event_emitter.close()
        logger.info("Shutdown complete")

    def get_metrics(self) -> dict:
        """Get watcher metrics"""
        emitter_metrics = self.event_emitter.get_metrics()

        return {
            "polls": self.polls,
            "switches_detected": self.switches_detected,
            "events_emitted": emitter_metrics["events_emitted"],
            "emission_errors": emitter_metrics["errors"],
            "current_app": self.current_app,
            "current_workspace": self.current_workspace
        }


async def run_watcher(poll_interval: int = 5):
    """Run workspace watcher"""
    watcher = WorkspaceWatcher(poll_interval=poll_interval)

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def shutdown():
        logger.info("Received shutdown signal")
        asyncio.create_task(watcher.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown)

    # Initialize and start
    await watcher.initialize()
    await watcher.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Workspace Watcher - Automatic workspace switch detection")
    parser.add_argument("--interval", type=int, default=5, help="Poll interval in seconds (default: 5)")
    args = parser.parse_args()

    try:
        asyncio.run(run_watcher(poll_interval=args.interval))
    except KeyboardInterrupt:
        logger.info("Stopped by user")