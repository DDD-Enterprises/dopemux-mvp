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

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from event_bus import Event, EventBus

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
        """
        Emit event when task progress updates.

        Args:
            task_id: Task identifier
            task_title: Task title/description
            old_status: Previous status
            new_status: New status (TODO/IN_PROGRESS/DONE/BLOCKED)
            progress_percentage: Completion percentage (0-100)
            complexity: Optional task complexity (0.0-1.0)
            energy_required: Optional energy level (low/medium/high)

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="task.progress.updated",
                data={
                    "task_id": task_id,
                    "title": task_title,
                    "old_status": old_status,
                    "new_status": new_status,
                    "progress_percentage": progress_percentage,
                    "complexity": complexity,
                    "energy_required": energy_required,
                    "workspace_id": self.workspace_id,
                    "status_transition": f"{old_status} → {new_status}"
                },
                source="task-orchestrator"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.progress_events += 1

                # Track specific status changes
                if new_status == "DONE":
                    self.completion_events += 1
                elif new_status == "BLOCKED":
                    self.blocked_events += 1

                logger.info(
                    f"📤 Emitted task.progress.updated: {task_title[:50]}... "
                    f"({old_status} → {new_status})"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit progress event: {e}")

        return False

    async def emit_task_completed(
        self,
        task_id: str,
        task_title: str,
        duration_minutes: int,
        complexity: Optional[float] = None
    ) -> bool:
        """
        Emit event when task completes.

        Args:
            task_id: Task identifier
            task_title: Task title
            duration_minutes: Time taken to complete
            complexity: Task complexity

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="task.completed",
                data={
                    "task_id": task_id,
                    "title": task_title,
                    "duration_minutes": duration_minutes,
                    "complexity": complexity,
                    "workspace_id": self.workspace_id,
                    "completion_timestamp": datetime.utcnow().isoformat()
                },
                source="task-orchestrator"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.completion_events += 1
                logger.info(f"📤 Emitted task.completed: {task_title[:50]}...")
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit completion event: {e}")

        return False

    async def emit_task_blocked(
        self,
        task_id: str,
        task_title: str,
        blocker_reason: str,
        recommended_actions: Optional[List[str]] = None
    ) -> bool:
        """
        Emit event when task becomes blocked.

        Args:
            task_id: Task identifier
            task_title: Task title
            blocker_reason: Reason task is blocked
            recommended_actions: Optional actions to unblock

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="task.blocked",
                data={
                    "task_id": task_id,
                    "title": task_title,
                    "blocker_reason": blocker_reason,
                    "recommended_actions": recommended_actions or [
                        "Identify blocking dependency",
                        "Re-estimate task complexity",
                        "Break into smaller sub-tasks",
                        "Seek help or clarification"
                    ],
                    "workspace_id": self.workspace_id,
                    "severity": "medium"
                },
                source="task-orchestrator"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.blocked_events += 1
                logger.warning(f"⚠️  Emitted task.blocked: {task_title[:50]}...")
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit blocked event: {e}")

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
        """
        Handle task status change.

        Args:
            task_id: Task identifier
            task_title: Task title
            old_status: Previous status
            new_status: New status
            progress_percentage: Completion percentage
            complexity: Optional complexity
            energy_required: Optional energy level
        """
        if not self.enable_progress_events:
            return

        # Emit progress update event
        await self.emitter.emit_task_progress_updated(
            task_id=task_id,
            task_title=task_title,
            old_status=old_status,
            new_status=new_status,
            progress_percentage=progress_percentage,
            complexity=complexity,
            energy_required=energy_required
        )

        # If completed, emit completion event
        if new_status == "DONE":
            await self.emitter.emit_task_completed(
                task_id=task_id,
                task_title=task_title,
                duration_minutes=0,  # Would calculate from task start time
                complexity=complexity
            )

        # If blocked, emit blocked event
        elif new_status == "BLOCKED":
            await self.emitter.emit_task_blocked(
                task_id=task_id,
                task_title=task_title,
                blocker_reason="Status changed to BLOCKED"
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics"""
        return self.emitter.get_metrics()
