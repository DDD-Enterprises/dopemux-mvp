"""
Indexing Worker - Background Processing

Processes file changes and triggers incremental indexing.
Includes retry logic and error recovery.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class WorkerStats:
    """Worker statistics for monitoring."""

    tasks_processed: int = 0
    tasks_succeeded: int = 0
    tasks_failed: int = 0
    last_run: Optional[datetime] = None
    last_error: Optional[str] = None
    total_files_indexed: int = 0


class IndexingWorker:
    """
    Background worker for processing indexing tasks.

    Handles queued file changes with retry logic and error recovery.
    """

    def __init__(
        self,
        workspace_path: Path,
        index_callback: Callable[[Path, Set[str]], asyncio.Future],
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ):
        """
        Initialize indexing worker.

        Args:
            workspace_path: Absolute workspace path
            index_callback: Async function to trigger indexing
            max_retries: Maximum retry attempts
            retry_backoff: Backoff multiplier for retries
        """
        self.workspace_path = workspace_path.resolve()
        self.index_callback = index_callback
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self.queue: asyncio.Queue = asyncio.Queue()
        self.stats = WorkerStats()
        self._running: bool = False
        self._worker_task: Optional[asyncio.Task] = None

    async def enqueue_changes(self, changed_files: Set[str]):
        """
        Add file changes to processing queue.

        Args:
            changed_files: Set of file paths that changed
        """
        if not changed_files:
            return

        logger.info(f"Enqueueing {len(changed_files)} files for indexing")
        await self.queue.put(changed_files)

    async def _process_queue(self):
        """Process indexing queue (background loop)."""
        logger.info("Indexing worker started")

        while self._running:
            try:
                # Wait for changes (with timeout for checking _running)
                try:
                    changed_files = await asyncio.wait_for(
                        self.queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Process changes with retries
                await self._process_with_retry(changed_files)

            except Exception as e:
                logger.error(f"Worker error: {e}")
                self.stats.last_error = str(e)

        logger.info("Indexing worker stopped")

    async def _process_with_retry(self, changed_files: Set[str]):
        """
        Process file changes with retry logic.

        Args:
            changed_files: Set of file paths to index
        """
        self.stats.tasks_processed += 1

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Processing {len(changed_files)} files (attempt {attempt})"
                )

                # Trigger indexing via callback
                await self.index_callback(self.workspace_path, changed_files)

                # Success!
                self.stats.tasks_succeeded += 1
                self.stats.total_files_indexed += len(changed_files)
                self.stats.last_run = datetime.now()

                logger.info(f"Successfully indexed {len(changed_files)} files")
                return

            except Exception as e:
                logger.warning(
                    f"Indexing attempt {attempt} failed: {e}"
                )

                if attempt < self.max_retries:
                    # Exponential backoff
                    wait_time = self.retry_backoff ** attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    # Max retries exceeded
                    logger.error(
                        f"Failed to index {len(changed_files)} files after "
                        f"{self.max_retries} attempts"
                    )
                    self.stats.tasks_failed += 1
                    self.stats.last_error = str(e)

    async def start(self):
        """Start background worker."""
        if self._running:
            logger.warning("Worker already running")
            return

        logger.info("Starting indexing worker")
        self._running = True
        self._worker_task = asyncio.create_task(self._process_queue())

    async def stop(self):
        """Stop worker gracefully."""
        if not self._running:
            return

        logger.info("Stopping indexing worker")
        self._running = False

        # Wait for current task to complete
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Worker did not stop gracefully, cancelling")
                self._worker_task.cancel()

        logger.info("Indexing worker stopped")

    def is_running(self) -> bool:
        """Check if worker is running."""
        return self._running

    def get_stats(self) -> dict:
        """Get worker statistics."""
        return {
            "tasks_processed": self.stats.tasks_processed,
            "tasks_succeeded": self.stats.tasks_succeeded,
            "tasks_failed": self.stats.tasks_failed,
            "success_rate": (
                self.stats.tasks_succeeded / self.stats.tasks_processed * 100
                if self.stats.tasks_processed > 0
                else 0.0
            ),
            "total_files_indexed": self.stats.total_files_indexed,
            "last_run": self.stats.last_run.isoformat() if self.stats.last_run else None,
            "last_error": self.stats.last_error,
            "queue_size": self.queue.qsize(),
        }
