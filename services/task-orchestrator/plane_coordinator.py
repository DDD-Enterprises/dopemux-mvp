"""
Plane Coordinator - Enhanced Two-Plane Architecture Coordination

Provides unified coordination mechanisms between PM and Cognitive planes:

- PM Plane (Project Management): Leantime, Task-Master, Task-Orchestrator
- Cognitive Plane (Development): Serena, ConPort, ADHD Engine

Features:
- Unified Coordination API: Single entry point for cross-plane operations
- Event-Driven Coordination: Real-time event routing and handling
- Plane Health Monitoring: Monitor coordination health and performance
- Intelligent Conflict Resolution: Handle conflicts between PM and Cognitive planes
- Coordination Analytics: Track effectiveness and optimization opportunities

Created: 2025-11-05
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import json

from sync_engine import MultiDirectionalSyncEngine, SyncDirection, SyncOperation
from task_coordinator import TaskCoordinator
from adapters.conport_adapter import ConPortEventAdapter
from intelligence.cognitive_load_balancer import CognitiveLoadBalancer

logger = logging.getLogger(__name__)


class PlaneType(str, Enum):
    """Plane types in the two-plane architecture."""
    PROJECT_MANAGEMENT = "pm"
    COGNITIVE = "cognitive"
    INTEGRATION = "integration"


class CoordinationEventType(str, Enum):
    """Types of coordination events."""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    DECISION_MADE = "decision_made"
    PROGRESS_UPDATED = "progress_updated"
    CONFLICT_DETECTED = "conflict_detected"
    BREAK_RECOMMENDED = "break_recommended"
    CONTEXT_SWITCH = "context_switch"
    HEALTH_CHECK = "health_check"
    SYNC_COMPLETED = "sync_completed"


@dataclass
class CoordinationEvent:
    """Represents a coordination event between planes."""
    id: str
    event_type: CoordinationEventType
    source_plane: PlaneType
    target_plane: PlaneType
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    timestamp: datetime = None
    correlation_id: Optional[str] = None
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if not self.correlation_id:
            self.correlation_id = f"{self.event_type}_{self.entity_id}_{int(self.timestamp.timestamp())}"


@dataclass
class PlaneHealth:
    """Health status of a plane."""
    plane: PlaneType
    status: str  # "healthy", "degraded", "unhealthy"
    last_check: datetime
    services: Dict[str, str]  # service_name -> status
    metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)

    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def has_critical_issues(self) -> bool:
        return self.status == "unhealthy" or any("critical" in issue.lower() for issue in self.issues)


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving coordination conflicts."""
    PM_WINS = "pm_wins"           # Project Management plane takes precedence
    COGNITIVE_WINS = "cognitive_wins"  # Cognitive plane takes precedence
    MERGE_INTELLIGENT = "merge_intelligent"  # Smart merge based on context
    ASK_USER = "ask_user"          # Present conflict to user for resolution
    LAST_MODIFIED = "last_modified"  # Use most recent change
    CONSENSUS = "consensus"       # Require agreement from both planes


@dataclass
class CoordinationConflict:
    """Represents a conflict between planes that needs resolution."""
    id: str
    entity_type: str
    entity_id: str
    pm_value: Any
    cognitive_value: Any
    field_name: str
    detected_at: datetime
    resolution_strategy: ConflictResolutionStrategy
    resolved_value: Optional[Any] = None
    resolved_at: Optional[datetime] = None
    resolution_reason: str = ""


class PlaneCoordinator:
    """
    Enhanced coordinator for two-plane architecture operations.

    Provides unified coordination between:
    - PM Plane: Leantime, Task-Master, Task-Orchestrator
    - Cognitive Plane: Serena, ConPort, ADHD Engine

    Features:
    - Unified API for cross-plane operations
    - Event-driven coordination with real-time routing
    - Health monitoring and conflict resolution
    - Analytics and optimization insights
    """

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        # Core coordination components
        self.sync_engine = MultiDirectionalSyncEngine(
            redis_url=redis_url,
            workspace_id=workspace_id,
        )
        self.task_coordinator = TaskCoordinator(workspace_id)
        self.conport_adapter = ConPortEventAdapter(workspace_id)
        self.cognitive_guardian = CognitiveLoadBalancer(workspace_id=workspace_id)

        # Coordination state
        self.plane_health: Dict[PlaneType, PlaneHealth] = {}
        self.active_conflicts: Dict[str, CoordinationConflict] = {}
        self.event_handlers: Dict[CoordinationEventType, List[Callable]] = {}
        self.coordination_metrics = {
            "events_processed": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "sync_operations": 0,
            "health_checks": 0
        }

        # Configuration
        self.health_check_interval = 60  # seconds
        self.max_concurrent_events = 10
        self.event_queue = asyncio.Queue(maxsize=self.max_concurrent_events)
        self.processing_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize the plane coordinator and start background processing."""
        logger.info("🚀 Initializing Plane Coordinator...")

        # Initialize core components
        await self.sync_engine.initialize()

        # Start background event processing
        self.processing_task = asyncio.create_task(self._event_processor())

        # Start health monitoring
        asyncio.create_task(self._health_monitor())

        logger.info("✅ Plane Coordinator ready")

    async def shutdown(self) -> None:
        """Shutdown the plane coordinator gracefully."""
        logger.info("🛑 Shutting down Plane Coordinator...")

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        await self.sync_engine.redis_client.close()
        logger.info("✅ Plane Coordinator shutdown complete")

    # ============================================================================
    # Unified Coordination API
    # ============================================================================

    async def coordinate_operation(
        self,
        operation: str,
        source_plane: PlaneType,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Unified API for cross-plane operations.

        Args:
            operation: Operation name (e.g., "create_task", "update_progress")
            source_plane: Which plane initiated the operation
            data: Operation-specific data
            **kwargs: Additional operation parameters

        Returns:
            Coordination result with success status and data
        """
        logger.info(f"🔄 Coordinating {operation} from {source_plane.value} plane")

        try:
            # Route to appropriate handler
            if operation == "create_task":
                result = await self._coordinate_task_creation(source_plane, data, **kwargs)
            elif operation == "update_progress":
                result = await self._coordinate_progress_update(source_plane, data, **kwargs)
            elif operation == "log_decision":
                result = await self._coordinate_decision_logging(source_plane, data, **kwargs)
            elif operation == "recommend_break":
                result = await self._coordinate_break_recommendation(source_plane, data, **kwargs)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            # Emit coordination event
            event = CoordinationEvent(
                id=f"coord_{operation}_{int(datetime.now().timestamp())}",
                event_type=CoordinationEventType.SYNC_COMPLETED,
                source_plane=source_plane,
                target_plane=PlaneType.INTEGRATION,
                entity_type="coordination_operation",
                entity_id=operation,
                data={"operation": operation, "result": result},
                metadata={"success": result.get("success", False)}
            )
            await self._emit_event(event)

            return result

        except Exception as e:
            logger.error(f"Coordination failed for {operation}: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # Event-Driven Coordination
    # ============================================================================

    def register_event_handler(self, event_type: CoordinationEventType, handler: Callable) -> None:
        """Register an event handler for coordination events."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"📡 Registered handler for {event_type.value}")

    async def emit_coordination_event(
        self,
        event_type: CoordinationEventType,
        source_plane: PlaneType,
        target_plane: PlaneType,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        **kwargs
    ) -> None:
        """Emit a coordination event for processing."""
        event = CoordinationEvent(
            id=f"event_{int(datetime.now().timestamp())}_{entity_id}",
            event_type=event_type,
            source_plane=source_plane,
            target_plane=target_plane,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            **kwargs
        )

        # Add to processing queue (non-blocking)
        try:
            self.event_queue.put_nowait(event)
            logger.debug(f"📨 Queued event: {event_type.value} for {entity_id}")
        except asyncio.QueueFull:
            logger.warning(f"⚠️ Event queue full, dropping {event_type.value} event")

    async def _emit_event(self, event: CoordinationEvent) -> None:
        """Internal event emission with handler invocation."""
        # Call registered handlers
        handlers = self.event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler failed: {e}")

        # Track metrics
        self.coordination_metrics["events_processed"] += 1

    async def _event_processor(self) -> None:
        """Background event processing loop."""
        logger.info("🔄 Started event processor")

        while True:
            try:
                # Get next event
                event = await self.event_queue.get()

                # Process event
                await self._process_coordination_event(event)

                # Mark as processed
                self.event_queue.task_done()

            except asyncio.CancelledError:
                logger.info("🛑 Event processor cancelled")
                break
            except Exception as e:
                logger.error(f"Event processing error: {e}")
                await asyncio.sleep(1.0)

    async def _process_coordination_event(self, event: CoordinationEvent) -> None:
        """Process a coordination event."""
        logger.debug(f"⚙️ Processing {event.event_type.value} event: {event.entity_id}")

        try:
            # Route based on event type and planes
            if event.event_type == CoordinationEventType.TASK_CREATED:
                await self._handle_task_created_event(event)
            elif event.event_type == CoordinationEventType.TASK_UPDATED:
                await self._handle_task_updated_event(event)
            elif event.event_type == CoordinationEventType.DECISION_MADE:
                await self._handle_decision_made_event(event)
            elif event.event_type == CoordinationEventType.CONFLICT_DETECTED:
                await self._handle_conflict_detected_event(event)
            elif event.event_type == CoordinationEventType.BREAK_RECOMMENDED:
                await self._handle_break_recommended_event(event)

            # Emit processing completion
            await self._emit_event(CoordinationEvent(
                id=f"processed_{event.id}",
                event_type=CoordinationEventType.SYNC_COMPLETED,
                source_plane=event.target_plane,
                target_plane=event.source_plane,
                entity_type="event_processing",
                entity_id=event.id,
                data={"original_event": asdict(event)},
                correlation_id=event.correlation_id
            ))

        except Exception as e:
            logger.error(f"Failed to process event {event.id}: {e}")

    # ============================================================================
    # Plane Health Monitoring
    # ============================================================================

    async def _health_monitor(self) -> None:
        """Background health monitoring for all planes."""
        logger.info("🏥 Started plane health monitor")

        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Check health of all planes
                for plane in PlaneType:
                    health = await self._check_plane_health(plane)
                    self.plane_health[plane] = health

                    if not health.is_healthy():
                        logger.warning(f"⚠️ {plane.value} plane unhealthy: {health.issues}")
                        # Emit health alert event
                        await self.emit_coordination_event(
                            CoordinationEventType.HEALTH_CHECK,
                            PlaneType.INTEGRATION,
                            plane,
                            "plane_health",
                            plane.value,
                            {"health": asdict(health)},
                            priority=1
                        )

                self.coordination_metrics["health_checks"] += 1

            except Exception as e:
                logger.error(f"Health monitor error: {e}")

    async def _check_plane_health(self, plane: PlaneType) -> PlaneHealth:
        """Check health of a specific plane."""
        health = PlaneHealth(
            plane=plane,
            status="healthy",
            last_check=datetime.now(timezone.utc),
            services={},
            issues=[]
        )

        try:
            if plane == PlaneType.PROJECT_MANAGEMENT:
                # Check Leantime, Task-Master, Task-Orchestrator
                health.services["leantime"] = await self._check_leantime_health()
                health.services["task_orchestrator"] = "healthy"  # Always healthy if running
                health.services["task_master"] = await self._check_task_master_health()

            elif plane == PlaneType.COGNITIVE:
                # Check Serena, ConPort, ADHD Engine
                health.services["serena"] = await self._check_serena_health()
                health.services["conport"] = await self._check_conport_health()
                health.services["adhd_engine"] = await self._check_adhd_engine_health()

            elif plane == PlaneType.INTEGRATION:
                # Check sync engine and coordination services
                health.services["sync_engine"] = "healthy" if self.sync_engine.running else "unhealthy"
                health.services["event_processor"] = "healthy" if self.processing_task else "unhealthy"

            # Determine overall status
            unhealthy_services = [s for s, status in health.services.items() if status != "healthy"]
            if unhealthy_services:
                health.status = "unhealthy" if len(unhealthy_services) > len(health.services) // 2 else "degraded"
                health.issues.extend([f"Service {s} is {health.services[s]}" for s in unhealthy_services])

        except Exception as e:
            health.status = "unhealthy"
            health.issues.append(f"Health check failed: {e}")


# ============================================================================
# Intelligent Conflict Resolution
# ============================================================================

        return health

    async def _check_leantime_health(self) -> str:
        """Check Leantime service health."""
        # Placeholder - implement actual health check
        return "healthy"

    async def _check_task_master_health(self) -> str:
        """Check Task-Master service health."""
        return "healthy"

    async def _check_serena_health(self) -> str:
        """Check Serena LSP health."""
        return "healthy"

    async def _check_conport_health(self) -> str:
        """Check ConPort service health."""
        try:
            # Use ConPort adapter to check health
            # This would need to be implemented in the adapter
            return "healthy"
        except Exception:
            return "unhealthy"

    async def _check_adhd_engine_health(self) -> str:
        """Check ADHD Engine health."""
        try:
            # Simple HTTP health check
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8080/health") as response:
                    return "healthy" if response.status == 200 else "unhealthy"
        except Exception:
            return "unhealthy"

    # ============================================================================
    # Intelligent Conflict Resolution
    # ============================================================================

    async def resolve_conflict(self, conflict: CoordinationConflict) -> Optional[Any]:
        """
        Resolve a coordination conflict using intelligent strategies.

        Args:
            conflict: The conflict to resolve

        Returns:
            Resolved value or None if resolution failed
        """
        logger.info(f"⚖️ Resolving conflict for {conflict.entity_type}:{conflict.entity_id}")

        strategy = conflict.resolution_strategy

        if strategy == ConflictResolutionStrategy.PM_WINS:
            resolved_value = conflict.pm_value
            reason = "PM plane takes precedence"

        elif strategy == ConflictResolutionStrategy.COGNITIVE_WINS:
            resolved_value = conflict.cognitive_value
            reason = "Cognitive plane takes precedence"

        elif strategy == ConflictResolutionStrategy.LAST_MODIFIED:
            # Would need to track timestamps - placeholder
            resolved_value = conflict.pm_value
            reason = "Using PM value as default"

        elif strategy == ConflictResolutionStrategy.MERGE_INTELLIGENT:
            resolved_value = await self._intelligent_merge(conflict)
            reason = "Intelligent merge applied"

        elif strategy == ConflictResolutionStrategy.ASK_USER:
            # Would trigger user interaction - placeholder
            resolved_value = conflict.pm_value
            reason = "User resolution needed - using PM default"

        else:
            resolved_value = None
            reason = f"Unknown strategy: {strategy}"

        if resolved_value is not None:
            conflict.resolved_value = resolved_value
            conflict.resolved_at = datetime.now(timezone.utc)
            conflict.resolution_reason = reason

            self.coordination_metrics["conflicts_resolved"] += 1

            # Emit resolution event
            await self.emit_coordination_event(
                CoordinationEventType.SYNC_COMPLETED,
                PlaneType.INTEGRATION,
                PlaneType.INTEGRATION,
                "conflict_resolution",
                conflict.id,
                {"conflict": asdict(conflict)},
                correlation_id=conflict.id
            )

        return resolved_value

    async def _intelligent_merge(self, conflict: CoordinationConflict) -> Any:
        """Perform intelligent merging of conflicting values."""
        # Simple strategy: prefer non-empty value, then PM value
        if conflict.pm_value and not conflict.cognitive_value:
            return conflict.pm_value
        elif conflict.cognitive_value and not conflict.pm_value:
            return conflict.cognitive_value
        elif conflict.pm_value == conflict.cognitive_value:
            return conflict.pm_value
        else:
            # Would implement more sophisticated merging logic
            return conflict.pm_value

    # ============================================================================
    # Coordination Analytics
    # ============================================================================

    def get_coordination_metrics(self) -> Dict[str, Any]:
        """Get coordination performance metrics."""
        health_summary = {}
        for plane, health in self.plane_health.items():
            health_summary[plane.value] = {
                "status": health.status,
                "services_healthy": sum(1 for s in health.services.values() if s == "healthy"),
                "total_services": len(health.services),
                "issues": len(health.issues)
            }

        return {
            "metrics": self.coordination_metrics,
            "plane_health": health_summary,
            "active_conflicts": len(self.active_conflicts),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ============================================================================
    # Operation-Specific Coordination Handlers
    # ============================================================================

    async def _coordinate_task_creation(
        self,
        source_plane: PlaneType,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Coordinate task creation across planes."""
        task_data = data["task"]

        if source_plane == PlaneType.PROJECT_MANAGEMENT:
            # PM plane initiated - sync to Cognitive plane
            sync_op = SyncOperation(
                id=f"sync_{task_data['id']}_{int(datetime.now().timestamp())}",
                direction=SyncDirection.LEANTIME_TO_CONPORT,
                source_system="pm_plane",
                target_system="cognitive_plane",
                entity_type="task",
                entity_id=task_data["id"],
                source_data=task_data,
                priority=kwargs.get("priority", 5)
            )
        else:
            # Cognitive plane initiated - sync to PM plane
            sync_op = SyncOperation(
                id=f"sync_{task_data['id']}_{int(datetime.now().timestamp())}",
                direction=SyncDirection.CONPORT_TO_LEANTIME,
                source_system="cognitive_plane",
                target_system="pm_plane",
                entity_type="task",
                entity_id=task_data["id"],
                source_data=task_data,
                priority=kwargs.get("priority", 5)
            )

        success = await self.sync_engine.queue_sync_operation(sync_op)
        self.coordination_metrics["sync_operations"] += 1

        return {"success": success, "sync_operation_id": sync_op.id}

    async def _coordinate_progress_update(
        self,
        source_plane: PlaneType,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Coordinate progress updates across planes."""
        progress_data = data["progress"]

        # Always sync progress updates bidirectionally
        sync_op = SyncOperation(
            id=f"sync_progress_{progress_data.get('task_id', 'unknown')}_{int(datetime.now().timestamp())}",
            direction=SyncDirection.LEANTIME_TO_CONPORT,  # Could be either direction
            source_system=source_plane.value,
            target_system="both",
            entity_type="progress",
            entity_id=progress_data.get("task_id", "unknown"),
            source_data=progress_data,
            priority=kwargs.get("priority", 3)
        )

        success = await self.sync_engine.queue_sync_operation(sync_op)
        self.coordination_metrics["sync_operations"] += 1

        return {"success": success, "sync_operation_id": sync_op.id}

    async def _coordinate_decision_logging(
        self,
        source_plane: PlaneType,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Coordinate decision logging across planes."""
        decision_data = data["decision"]

        # Decisions are primarily cognitive plane concern but should be visible PM-side
        sync_op = SyncOperation(
            id=f"sync_decision_{decision_data.get('id', 'unknown')}_{int(datetime.now().timestamp())}",
            direction=SyncDirection.CONPORT_TO_LEANTIME,
            source_system="cognitive_plane",
            target_system="pm_plane",
            entity_type="decision",
            entity_id=decision_data.get("id", "unknown"),
            source_data=decision_data,
            priority=kwargs.get("priority", 4)
        )

        success = await self.sync_engine.queue_sync_operation(sync_op)
        self.coordination_metrics["sync_operations"] += 1

        return {"success": success, "sync_operation_id": sync_op.id}

    async def _coordinate_break_recommendation(
        self,
        source_plane: PlaneType,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Coordinate break recommendations from cognitive plane."""
        # Break recommendations are cognitive-to-PM coordination
        if source_plane == PlaneType.COGNITIVE:
            await self.emit_coordination_event(
                CoordinationEventType.BREAK_RECOMMENDED,
                PlaneType.COGNITIVE,
                PlaneType.PROJECT_MANAGEMENT,
                "break_recommendation",
                data.get("session_id", "unknown"),
                data,
                priority=1  # High priority for breaks
            )

        return {"success": True, "message": "Break recommendation coordinated"}

    # ============================================================================
    # Event Handlers
    # ============================================================================

    async def _handle_task_created_event(self, event: CoordinationEvent) -> None:
        """Handle task creation events."""
        # Sync to opposite plane
        target_plane = PlaneType.COGNITIVE if event.source_plane == PlaneType.PROJECT_MANAGEMENT else PlaneType.PROJECT_MANAGEMENT

        await self.emit_coordination_event(
            CoordinationEventType.SYNC_COMPLETED,
            event.source_plane,
            target_plane,
            event.entity_type,
            event.entity_id,
            {"action": "create_task", "data": event.data},
            correlation_id=event.correlation_id
        )

    async def _handle_task_updated_event(self, event: CoordinationEvent) -> None:
        """Handle task update events."""
        # Sync update to all relevant planes
        target_plane = PlaneType.COGNITIVE if event.source_plane == PlaneType.PROJECT_MANAGEMENT else PlaneType.PROJECT_MANAGEMENT

        await self.emit_coordination_event(
            CoordinationEventType.SYNC_COMPLETED,
            event.source_plane,
            target_plane,
            event.entity_type,
            event.entity_id,
            {"action": "update_task", "data": event.data},
            correlation_id=event.correlation_id
        )

    async def _handle_decision_made_event(self, event: CoordinationEvent) -> None:
        """Handle decision logging events."""
        # Decisions are primarily for cognitive plane tracking
        await self.emit_coordination_event(
            CoordinationEventType.SYNC_COMPLETED,
            event.source_plane,
            PlaneType.COGNITIVE,
            event.entity_type,
            event.entity_id,
            {"action": "log_decision", "data": event.data},
            correlation_id=event.correlation_id
        )

    async def _handle_conflict_detected_event(self, event: CoordinationEvent) -> None:
        """Handle conflict detection events."""
        conflict_data = event.data
        conflict = CoordinationConflict(**conflict_data)

        self.active_conflicts[conflict.id] = conflict
        self.coordination_metrics["conflicts_detected"] += 1

        # Attempt automatic resolution
        resolved_value = await self.resolve_conflict(conflict)
        if resolved_value is not None:
            logger.info(f"✅ Auto-resolved conflict {conflict.id}")
        else:
            logger.warning(f"⚠️ Manual resolution needed for conflict {conflict.id}")

    async def _handle_break_recommended_event(self, event: CoordinationEvent) -> None:
        """Handle break recommendation events."""
        # Forward break recommendations to PM plane for visibility
        if event.target_plane == PlaneType.PROJECT_MANAGEMENT:
            # Could integrate with task management to pause work
            logger.info(f"☕ Break recommended: {event.data}")


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_plane_coordinator(workspace_id: str) -> PlaneCoordinator:
    """Create and initialize a plane coordinator."""
    coordinator = PlaneCoordinator(workspace_id)
    await coordinator.initialize()
    return coordinator


async def coordinate_task_creation(
    coordinator: PlaneCoordinator,
    source_plane: PlaneType,
    task_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience function for task creation coordination."""
    return await coordinator.coordinate_operation(
        "create_task",
        source_plane,
        {"task": task_data}
    )


async def coordinate_progress_update(
    coordinator: PlaneCoordinator,
    source_plane: PlaneType,
    progress_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Convenience function for progress update coordination."""
    return await coordinator.coordinate_operation(
        "update_progress",
        source_plane,
        {"progress": progress_data}
    )

# Example usage and testing
if __name__ == "__main__":
    async def demo_coordination():
        """Demonstrate plane coordination functionality."""

        # Create coordinator
        coordinator = await create_plane_coordinator("/Users/hue/code/dopemux-mvp")

        # Register event handler
        def handle_task_events(event: CoordinationEvent):
            print(f"📡 Event: {event.event_type.value} for {event.entity_id}")

        coordinator.register_event_handler(
            CoordinationEventType.TASK_CREATED,
            handle_task_events
        )

        # Coordinate task creation
        task_data = {
            "id": "demo_task_001",
            "title": "Implement plane coordination",
            "description": "Enhanced two-plane architecture coordination",
            "complexity_score": 0.7,
            "energy_required": "high"
        }

        result = await coordinate_task_creation(
            coordinator,
            PlaneType.COGNITIVE,
            task_data
        )
        print(f"Task coordination result: {result}")

        # Check coordination health
        metrics = coordinator.get_coordination_metrics()
        print(f"Coordination metrics: {json.dumps(metrics, indent=2, default=str)}")

        # Shutdown
        await coordinator.shutdown()

    asyncio.run(demo_coordination())
