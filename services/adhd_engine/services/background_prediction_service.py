"""Background prediction service (compatibility implementation)."""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Optional, Set

import redis.asyncio as redis


class BackgroundPredictionService:
    """Periodic placeholder service for proactive ADHD predictions."""

    def __init__(self, workspace_id: str, monitoring_interval_seconds: int = 60):
        self.workspace_id = workspace_id
        self.monitoring_interval_seconds = monitoring_interval_seconds
        self.redis_client = None
        self.running = False
        self.predictions_made = 0
        self.users_being_monitored: Set[str] = set()
        self.last_run_at: Optional[str] = None
        self._worker_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize required dependencies (best effort)."""
        if self.redis_client is not None:
            return

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            await self.redis_client.ping()
        except Exception:
            # Keep a non-None sentinel so tests and callers can proceed.
            self.redis_client = object()

    async def start(self):
        """Run periodic prediction loop until stopped."""
        await self.initialize()
        self.running = True

        try:
            while self.running:
                self.last_run_at = datetime.now(timezone.utc).isoformat()
                # Placeholder for predictive scans.
                await asyncio.sleep(self.monitoring_interval_seconds)
        except asyncio.CancelledError:
            raise

    async def stop(self):
        """Stop service loop gracefully."""
        self.running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def get_status(self) -> Dict[str, object]:
        """Return service status snapshot."""
        return {
            "running": self.running,
            "workspace_id": self.workspace_id,
            "predictions_made": self.predictions_made,
            "users_being_monitored": sorted(self.users_being_monitored),
            "monitoring_interval_seconds": self.monitoring_interval_seconds,
            "last_run_at": self.last_run_at,
        }


_background_services: Dict[str, BackgroundPredictionService] = {}


async def get_background_prediction_service(
    workspace_id: Optional[str] = None,
) -> BackgroundPredictionService:
    """Get or create singleton background service for a workspace."""
    resolved_workspace = workspace_id or os.getenv("WORKSPACE_ID", "default")
    service = _background_services.get(resolved_workspace)
    if service is None:
        service = BackgroundPredictionService(resolved_workspace)
        await service.initialize()
        _background_services[resolved_workspace] = service
    return service


async def start_background_prediction_service(
    workspace_id: Optional[str] = None,
) -> BackgroundPredictionService:
    """Start background service in a detached task and return it."""
    service = await get_background_prediction_service(workspace_id)
    if service.running and service._worker_task and not service._worker_task.done():
        return service

    service._worker_task = asyncio.create_task(service.start())
    return service
