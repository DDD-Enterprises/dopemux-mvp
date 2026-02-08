"""
Watchdog Monitor - File System Event Monitoring

Monitors workspace for file changes using watchdog library.
Implements debouncing to batch rapid save events.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Callable, List, Optional, Set

try:
    from watchdog.observers import Observer  # type: ignore
    from watchdog.events import FileSystemEventHandler, FileSystemEvent  # type: ignore
except ImportError:  # pragma: no cover - exercised in constrained envs
    Observer = None  # type: ignore

    class FileSystemEventHandler:  # type: ignore
        """Fallback handler so imports succeed without watchdog."""

        def __init__(self, *args, **kwargs):
            self._watchdog_unavailable = True

    class FileSystemEvent:  # type: ignore
        """Fallback event."""

        is_directory: bool = False
        src_path: str = ""


logger = logging.getLogger(__name__)


class DebouncedFileHandler(FileSystemEventHandler):
    """
    File system event handler with debouncing.

    Collects file events and triggers callback after quiet period.
    """

    def __init__(
        self,
        callback: Callable[[Set[str]], None],
        debounce_seconds: float = 5.0,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
    ):
        """
        Initialize debounced handler.

        Args:
            callback: Function to call with changed file paths
            debounce_seconds: Wait time after last event before triggering
            include_patterns: File patterns to include (e.g., ["*.py"])
            exclude_patterns: Patterns to exclude (e.g., ["__pycache__"])
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.include_patterns = include_patterns or ["*.py", "*.js", "*.ts", "*.tsx"]
        self.exclude_patterns = exclude_patterns or [
            "__pycache__",
            "*.pyc",
            "node_modules",
            ".git",
            "dist",
            "build",
            ".venv",
            "venv",
        ]

        self.changed_files: Set[str] = set()
        self.last_event_time: float = 0.0
        self.debounce_task: asyncio.Task = None
        self._loop: asyncio.AbstractEventLoop = None

    def _should_ignore(self, path: str) -> bool:
        """Check if path should be ignored."""
        path_lower = path.lower()

        # Check exclusions
        for pattern in self.exclude_patterns:
            pattern_clean = pattern.replace("*", "").lower()
            if pattern_clean in path_lower:
                return True

        # Check if matches include pattern
        path_obj = Path(path)
        for pattern in self.include_patterns:
            if path_obj.match(pattern):
                return False

        # No pattern matched
        return True

    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event."""
        # Ignore directories
        if event.is_directory:
            return

        # Get file path
        file_path = event.src_path

        # Filter by patterns
        if self._should_ignore(file_path):
            return

        # Add to changed files
        self.changed_files.add(file_path)
        self.last_event_time = time.time()

        # Schedule debounced callback
        self._schedule_callback()

    def _schedule_callback(self):
        """Schedule callback after debounce period."""
        if self._loop is None:
            # Get or create event loop
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("No running event loop for debounce scheduling")
                return

        # Cancel existing task
        if self.debounce_task and not self.debounce_task.done():
            self.debounce_task.cancel()

        # Schedule new task
        self.debounce_task = self._loop.create_task(self._wait_and_callback())

    async def _wait_and_callback(self):
        """Wait for quiet period then trigger callback."""
        try:
            while True:
                await asyncio.sleep(self.debounce_seconds)

                # Check if quiet period elapsed
                elapsed = time.time() - self.last_event_time
                if elapsed >= self.debounce_seconds:
                    # Quiet period complete, trigger callback
                    if self.changed_files:
                        files = self.changed_files.copy()
                        self.changed_files.clear()

                        logger.info(
                            f"Debounce complete: {len(files)} files changed, "
                            f"triggering indexing"
                        )

                        # Call callback
                        self.callback(files)

                    break

        except asyncio.CancelledError:
            # Task was cancelled, restart debounce timer
            pass
        except Exception as e:
            logger.error(f"Error in debounce callback: {e}")


class WatchdogMonitor:
    """
    File system monitor for autonomous indexing.

    Uses watchdog library to detect file changes and trigger reindexing.
    """

    def __init__(
        self,
        workspace_path: Path,
        callback: Callable[[Set[str]], None],
        debounce_seconds: float = 5.0,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
    ):
        """
        Initialize watchdog monitor.

        Args:
            workspace_path: Absolute workspace path to monitor
            callback: Function to call with changed file paths
            debounce_seconds: Wait time after last event
            include_patterns: File patterns to monitor
            exclude_patterns: Patterns to ignore
        """
        self.workspace_path = workspace_path.resolve()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns

        self.observer: Optional[Observer] = None
        self.event_handler: DebouncedFileHandler = None
        self._running: bool = False

    def start(self):
        """Start monitoring workspace."""
        if self._running:
            logger.warning("Watchdog already running")
            return

        if Observer is None:
            raise RuntimeError(
                "watchdog package is required for autonomous indexing. "
                "Install it with `pip install watchdog`."
            )

        logger.info(f"Starting watchdog monitor for {self.workspace_path}")

        # Create event handler
        self.event_handler = DebouncedFileHandler(
            callback=self.callback,
            debounce_seconds=self.debounce_seconds,
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns,
        )

        # Create and start observer
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.workspace_path),
            recursive=True,
        )
        self.observer.start()

        self._running = True
        logger.info(f"Watchdog monitoring {self.workspace_path}")

    def stop(self):
        """Stop monitoring."""
        if not self._running:
            return

        logger.info("Stopping watchdog monitor")

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5.0)

        self._running = False
        logger.info("Watchdog stopped")

    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running

    def get_status(self) -> dict:
        """Get monitor status."""
        return {
            "running": self._running,
            "workspace": str(self.workspace_path),
            "debounce_seconds": self.debounce_seconds,
            "pending_changes": len(self.event_handler.changed_files)
            if self.event_handler
            else 0,
        }
