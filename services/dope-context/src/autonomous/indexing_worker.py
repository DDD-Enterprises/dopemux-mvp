"""Background indexing worker for autonomous dope-context updates."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Optional, Set


logger = logging.getLogger(__name__)


class IndexingWorker:
    """
    Async queue worker that batches filesystem changes and triggers indexing.
    """

    def __init__(
        self,
        workspace_path: Path,
        index_callback: Callable[[Path, Optional[Set[str]]], Awaitable[None]],
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ):
        self.workspace_path = workspace_path.resolve()
        self.index_callback = index_callback
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

        self._queue: asyncio.Queue[Optional[Set[str]]] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running = False

        self._queued_batches = 0
        self._processed_batches = 0
        self._failed_batches = 0
        self._last_error: Optional[str] = None
        self._last_processed_at: Optional[str] = None

    async def start(self):
        """Start the worker loop."""
        if self._running:
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._run())

    async def stop(self):
        """Stop the worker loop gracefully."""
        if not self._running:
            return

        self._running = False
        await self._queue.put(None)

        if self._worker_task:
            await self._worker_task

    async def enqueue_changes(self, changed_files: Set[str]):
        """Queue changed files for processing."""
        if not changed_files:
            return

        await self._queue.put(set(changed_files))
        self._queued_batches += 1

    async def _run(self):
        while self._running:
            item = await self._queue.get()
            if item is None:
                self._queue.task_done()
                break

            combined_changes = set(item)

            # Opportunistically merge queued batches to reduce duplicate indexing work.
            while not self._queue.empty():
                next_item = self._queue.get_nowait()
                if next_item is None:
                    self._queue.task_done()
                    self._running = False
                    break
                combined_changes.update(next_item)
                self._queue.task_done()

            success = await self._run_with_retries(combined_changes)
            if success:
                self._processed_batches += 1
                self._last_processed_at = datetime.now().isoformat()
            else:
                self._failed_batches += 1

            self._queue.task_done()

    async def _run_with_retries(self, changed_files: Set[str]) -> bool:
        for attempt in range(1, self.max_retries + 1):
            try:
                await self.index_callback(self.workspace_path, changed_files)
                return True
            except Exception as exc:
                self._last_error = str(exc)
                logger.warning(
                    "Indexing worker attempt %s/%s failed for %s: %s",
                    attempt,
                    self.max_retries,
                    self.workspace_path,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_backoff ** attempt)
        return False

    def get_stats(self) -> dict:
        """Return worker metrics for health/status APIs."""
        return {
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "queued_batches": self._queued_batches,
            "processed_batches": self._processed_batches,
            "failed_batches": self._failed_batches,
            "last_processed_at": self._last_processed_at,
            "last_error": self._last_error,
        }
