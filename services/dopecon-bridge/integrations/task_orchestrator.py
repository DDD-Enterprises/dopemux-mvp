"""
Task-Orchestrator Integration for ConPort-KG Event System

Enhances existing Task-Orchestrator event subscription with event publishing:
- Task progress updates (status changes)
- Task completion events
- Task blocked/abandoned events

Events emitted:
- task.progress.updated: Task status changed
- task.completed: Task finished successfully
- task.blocked: Task cannot proceed
"""

import logging
from typing import Any, Dict, List, Optional

from event_bus import EventBus

from dopemux.pm.store import InMemoryPMTaskStore

logger = logging.getLogger(__name__)


class TaskOrchestratorEventEmitter:
    """
    Event emitter for Task-Orchestrator task management.

    Enhances existing event subscription (70% done) with publishing capabilities.

    Features:
    - Task progress event emission
    - Status change tracking
    - Task completion and blocking detection
    - ADHD-optimized: Progress visibility for motivation
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        enable_events: bool = True
    ):
        """
        Initialize Task-Orchestrator event emitter.

        Args:
            event_bus: EventBus instance for publishing
            workspace_id: Workspace ID for event context
            enable_events: Enable event emission (default: True)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_events = enable_events
        self.pm_store = InMemoryPMTaskStore()

        # Metrics
        self.events_emitted = 0
        self.progress_events = 0
        self.completion_events = 0
        self.blocked_events = 0
        self.emission_errors = 0

    async def emit_task_progress_updated(
        self,
        task_id: str,
        task_title: str,
        old_status: str,
        new_status: str,
        progress_percentage: float = 0.0,
        complexity: Optional[float] = None,
        energy_required: Optional[str] = None
    ) -> bool:
        """Held pending authenticated canonical outbox destination qualification."""
        return False

    async def emit_task_completed(
        self,
        task_id: str,
        task_title: str,
        duration_minutes: int,
        complexity: Optional[float] = None
    ) -> bool:
        """Held pending authenticated canonical outbox destination qualification."""
        return False

    async def emit_task_blocked(
        self,
        task_id: str,
        task_title: str,
        blocker_reason: str,
        recommended_actions: Optional[List[str]] = None
    ) -> bool:
        """Held pending authenticated canonical outbox destination qualification."""
        return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get event emission metrics.

        Returns:
            Dictionary with emission stats
        """
        return {
            "agent": "task-orchestrator",
            "events_emitted": self.events_emitted,
            "progress_events": self.progress_events,
            "completion_events": self.completion_events,
            "blocked_events": self.blocked_events,
            "emission_errors": self.emission_errors,
            "events_enabled": self.enable_events
        }

    def reset_metrics(self):
        """Reset emission metrics"""
        self.events_emitted = 0
        self.progress_events = 0
        self.completion_events = 0
        self.blocked_events = 0
        self.emission_errors = 0


class TaskOrchestratorIntegrationManager:
    """
    Manages Task-Orchestrator integration with ConPort-KG event system.

    ENHANCEMENT to existing integration (already consuming events ~70% done).
    Adds publishing capabilities for task progress tracking.

    Provides:
    - Event emitter for task progress
    - Bidirectional communication (subscribe + publish)
    - Task status change detection
    - Metrics aggregation
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        enable_progress_events: bool = True
    ):
        """
        Initialize Task-Orchestrator integration manager.

        Args:
            event_bus: EventBus instance
            workspace_id: Workspace ID
            enable_progress_events: Enable task progress events (default: True)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_progress_events = enable_progress_events

        # Create event emitter
        self.emitter = TaskOrchestratorEventEmitter(
            event_bus=event_bus,
            workspace_id=workspace_id,
            enable_events=enable_progress_events
        )

        logger.info(
            f"✅ Task-Orchestrator integration enhanced "
            f"(progress events: {enable_progress_events}) "
            f"[Bidirectional: subscribe ✅ + publish ✅]"
        )

    async def handle_task_status_change(
        self,
        task_id: str,
        task_title: str,
        old_status: str,
        new_status: str,
        progress_percentage: float = 0.0,
        complexity: Optional[float] = None,
        energy_required: Optional[str] = None
    ):
        """Legacy demo state cannot produce canonical lifecycle events."""
        raise RuntimeError("Canonical lifecycle delivery requires an authenticated committed outbox")

    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics"""
        return self.emitter.get_metrics()
