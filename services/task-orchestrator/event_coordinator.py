"""
Event-Driven Coordination System for Task Orchestrator

Real-time event processing for seamless PM automation with ADHD optimizations.
Handles coordination between Leantime, AI agents, and local systems.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types for coordination."""
    # Leantime events
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    SPRINT_STARTED = "sprint_started"
    SPRINT_ENDED = "sprint_ended"

    # AI agent events
    AGENT_ASSIGNED = "agent_assigned"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETED = "agent_completed"
    AGENT_BLOCKED = "agent_blocked"

    # ADHD events
    BREAK_NEEDED = "break_needed"
    CONTEXT_SWITCH = "context_switch"
    FOCUS_MODE_CHANGED = "focus_mode_changed"
    ENERGY_LEVEL_CHANGED = "energy_level_changed"

    # System events
    SYNC_REQUIRED = "sync_required"
    CONFLICT_DETECTED = "conflict_detected"
    AUTOMATION_TRIGGERED = "automation_triggered"


class EventPriority(int, Enum):
    """Event priority levels for ADHD-aware processing."""
    CRITICAL = 1      # Immediate attention required
    HIGH = 2          # Process within 1 minute
    MEDIUM = 3        # Process within 5 minutes
    LOW = 4           # Process within 15 minutes
    BACKGROUND = 5    # Process when resources available


@dataclass
class CoordinationEvent:
    """Event for system coordination."""
    id: str
    event_type: EventType
    priority: EventPriority
    source_system: str
    target_systems: List[str]

    # Event data
    task_id: Optional[str] = None
    data: Dict[str, Any] = None
    context: Dict[str, Any] = None

    # ADHD metadata
    cognitive_load: float = 0.5
    interruption_allowed: bool = True
    focus_required: bool = False

    # Timing
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None

    # Processing state
    attempts: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.context is None:
            self.context = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class EventCoordinator:
    """
    Event-driven coordination system for seamless PM automation.

    Features:
    - Real-time event processing with priority queues
    - ADHD-aware event scheduling and batching
    - Multi-system coordination with conflict resolution
    - Implicit automation trigger detection
    - Context preservation across system boundaries
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

        # Event processing infrastructure
        self.event_queues: Dict[EventPriority, asyncio.PriorityQueue] = {}
        self.event_processors: Dict[EventType, List[Callable]] = {}
        self.event_filters: List[Callable] = []

        # ADHD optimization
        self.current_focus_mode = "normal"
        self.current_energy_level = "medium"
        self.active_context_switches = 0
        self.last_break_time = datetime.now(timezone.utc)

        # Processing state
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.metrics = {
            "events_processed": 0,
            "events_filtered": 0,
            "automation_triggers": 0,
            "adhd_accommodations": 0,
            "sync_conflicts": 0
        }

    async def initialize(self) -> None:
        """Initialize event coordination system."""
        logger.info("🔄 Initializing Event Coordinator...")

        # Initialize Redis connection
        self.redis_client = redis.from_url(
            self.redis_url,
            db=3,  # Separate DB for events
            decode_responses=True
        )
        await self.redis_client.ping()

        # Initialize priority queues
        for priority in EventPriority:
            self.event_queues[priority] = asyncio.PriorityQueue()

        # Register default event processors
        self._register_default_processors()

        # Start worker pool
        await self._start_event_workers()

        self.running = True
        logger.info("✅ Event Coordinator ready for real-time coordination!")

    def _register_default_processors(self) -> None:
        """Register default event processors."""
        # Task lifecycle processors
        self.register_processor(EventType.TASK_CREATED, self._process_task_created)
        self.register_processor(EventType.TASK_UPDATED, self._process_task_updated)
        self.register_processor(EventType.TASK_COMPLETED, self._process_task_completed)

        # Sprint lifecycle processors
        self.register_processor(EventType.SPRINT_STARTED, self._process_sprint_started)
        self.register_processor(EventType.SPRINT_ENDED, self._process_sprint_ended)

        # ADHD accommodation processors
        self.register_processor(EventType.BREAK_NEEDED, self._process_break_needed)
        self.register_processor(EventType.CONTEXT_SWITCH, self._process_context_switch)
        self.register_processor(EventType.FOCUS_MODE_CHANGED, self._process_focus_mode_changed)

        # System coordination processors
        self.register_processor(EventType.SYNC_REQUIRED, self._process_sync_required)
        self.register_processor(EventType.CONFLICT_DETECTED, self._process_conflict_detected)

    async def _start_event_workers(self) -> None:
        """Start event processing workers with priority handling."""
        # Start workers for each priority level
        priority_workers = {
            EventPriority.CRITICAL: 3,   # 3 workers for critical events
            EventPriority.HIGH: 2,       # 2 workers for high priority
            EventPriority.MEDIUM: 2,     # 2 workers for medium priority
            EventPriority.LOW: 1,        # 1 worker for low priority
            EventPriority.BACKGROUND: 1  # 1 worker for background
        }

        for priority, worker_count in priority_workers.items():
            for i in range(worker_count):
                worker = asyncio.create_task(
                    self._event_worker(priority, f"{priority.name.lower()}-{i}")
                )
                self.workers.append(worker)

        logger.info(f"👥 Started {len(self.workers)} event processing workers")

    async def _event_worker(self, priority: EventPriority, worker_id: str) -> None:
        """Event processing worker for specific priority level."""
        logger.debug(f"🚀 Event worker {worker_id} started")

        while self.running:
            try:
                # Get event from priority queue
                queue = self.event_queues[priority]
                _, event = await asyncio.wait_for(queue.get(), timeout=5.0)

                # Process event with ADHD considerations
                await self._process_event(event, worker_id)

            except asyncio.TimeoutError:
                # No events at this priority, continue
                continue
            except Exception as e:
                logger.error(f"Event worker {worker_id} error: {e}")
                await asyncio.sleep(1.0)

        logger.debug(f"🛑 Event worker {worker_id} stopped")

    async def _process_event(self, event: CoordinationEvent, worker_id: str) -> None:
        """Process individual coordination event."""
        try:
            start_time = datetime.now(timezone.utc)

            # Apply ADHD filtering
            if not await self._should_process_event(event):
                self.metrics["events_filtered"] += 1
                logger.debug(f"🎯 Event filtered (ADHD): {event.event_type}")
                return

            # Check if event has expired
            if event.expires_at and datetime.now(timezone.utc) > event.expires_at:
                logger.warning(f"⏰ Event expired: {event.id}")
                return

            # Get processors for this event type
            processors = self.event_processors.get(event.event_type, [])

            if not processors:
                logger.warning(f"No processors registered for {event.event_type}")
                return

            # Execute processors in parallel
            results = await asyncio.gather(
                *[processor(event) for processor in processors],
                return_exceptions=True
            )

            # Check for errors
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                logger.error(f"Event processing errors: {errors}")
                event.error_message = str(errors[0])

            # Update processing metadata
            event.processed_at = datetime.now(timezone.utc)
            processing_time = (event.processed_at - start_time).total_seconds()

            # Store processing history in Redis
            await self._store_event_history(event, processing_time)

            self.metrics["events_processed"] += 1
            logger.debug(f"✅ Event processed by {worker_id}: {event.event_type} in {processing_time:.3f}s")

        except Exception as e:
            logger.error(f"Event processing failed: {e}")
            event.attempts += 1
            event.error_message = str(e)

            # Retry logic with exponential backoff
            if event.attempts < event.max_attempts:
                delay = 2 ** event.attempts  # Exponential backoff
                logger.info(f"🔄 Retrying event {event.id} in {delay}s (attempt {event.attempts + 1})")

                # Re-queue with delay
                asyncio.create_task(self._delayed_requeue(event, delay))

    async def _delayed_requeue(self, event: CoordinationEvent, delay: float) -> None:
        """Re-queue event after delay."""
        await asyncio.sleep(delay)
        await self.emit_event(event)

    # Event Emission and Registration

    async def emit_event(self, event: CoordinationEvent) -> bool:
        """Emit coordination event for processing."""
        try:
            # Assign unique ID if not present
            if not hasattr(event, 'id') or not event.id:
                event.id = f"{event.event_type}_{datetime.now().timestamp()}"

            # Apply ADHD filtering before queuing
            if not await self._should_process_event(event):
                return False

            # Queue event by priority
            priority_queue = self.event_queues[event.priority]
            await priority_queue.put((event.priority.value, event))

            logger.debug(f"📤 Event emitted: {event.event_type} (priority: {event.priority.name})")
            return True

        except Exception as e:
            logger.error(f"Failed to emit event: {e}")
            return False

    def register_processor(self, event_type: EventType, processor: Callable) -> None:
        """Register event processor for specific event type."""
        if event_type not in self.event_processors:
            self.event_processors[event_type] = []

        self.event_processors[event_type].append(processor)
        logger.debug(f"📝 Registered processor for {event_type}")

    def register_filter(self, filter_func: Callable) -> None:
        """Register event filter for ADHD optimization."""
        self.event_filters.append(filter_func)
        logger.debug("🎯 Registered event filter")

    # ADHD-Aware Event Processing

    async def _should_process_event(self, event: CoordinationEvent) -> bool:
        """Determine if event should be processed based on ADHD state."""
        try:
            # Apply custom filters
            for filter_func in self.event_filters:
                if not await filter_func(event):
                    return False

            # Check focus mode restrictions
            if self.current_focus_mode == "deep":
                # In deep focus, only allow critical events
                if event.priority not in [EventPriority.CRITICAL, EventPriority.HIGH]:
                    return False

                # Block interrupting events unless critical
                if not event.interruption_allowed and event.priority != EventPriority.CRITICAL:
                    return False

            # Check energy level matching
            if self.current_energy_level == "low":
                # Low energy: avoid high cognitive load events
                if event.cognitive_load > 0.7:
                    return False

            # Check for event flooding (ADHD protection)
            recent_events = await self._get_recent_event_count(event.event_type)
            if recent_events > 10:  # More than 10 similar events in last minute
                logger.warning(f"🌊 Event flooding detected: {event.event_type}")
                return False

            return True

        except Exception as e:
            logger.error(f"Event filtering failed: {e}")
            return True  # Default to processing on error

    async def _get_recent_event_count(self, event_type: EventType) -> int:
        """Get count of recent events of same type."""
        try:
            key = f"events:recent:{event_type.value}"
            count = await self.redis_client.get(key)
            return int(count) if count else 0

        except Exception:
            return 0

    # Default Event Processors

    async def _process_task_created(self, event: CoordinationEvent) -> None:
        """Process task creation event."""
        try:
            task_data = event.data
            logger.info(f"📋 Processing task creation: {task_data.get('title', 'Unknown')}")

            # 1. Auto-decompose if task is too large for ADHD
            estimated_minutes = task_data.get("estimated_minutes", 25)
            if estimated_minutes > 25:
                await self._trigger_adhd_decomposition(event)

            # 2. Assign optimal AI agent
            optimal_agent = await self._determine_optimal_agent(task_data)
            if optimal_agent:
                await self._assign_agent_to_task(event.task_id, optimal_agent)

            # 3. Setup ConPort tracking
            await self._setup_conport_tracking(event)

            # 4. Cache task context for quick access
            await self._cache_task_context(event)

        except Exception as e:
            logger.error(f"Task creation processing failed: {e}")

    async def _process_task_updated(self, event: CoordinationEvent) -> None:
        """Process task update event."""
        try:
            task_data = event.data
            logger.debug(f"📝 Processing task update: {event.task_id}")

            # Check for status changes requiring action
            new_status = task_data.get("status")
            if new_status == "in_progress":
                await self._handle_task_start(event)
            elif new_status == "completed":
                await self._handle_task_completion(event)
            elif new_status == "blocked":
                await self._handle_task_blocked(event)

            # Sync changes to all systems
            await self._propagate_task_update(event)

        except Exception as e:
            logger.error(f"Task update processing failed: {e}")

    async def _process_sprint_started(self, event: CoordinationEvent) -> None:
        """Process sprint start with implicit automation."""
        try:
            sprint_data = event.data
            sprint_id = sprint_data.get("sprint_id", "unknown")

            logger.info(f"🚀 Processing sprint start: {sprint_id}")

            # 1. Auto-setup ConPort sprint context
            sprint_context = {
                "sprint_id": sprint_id,
                "mode": "PLAN",
                "focus": "Sprint execution",
                "auto_managed": True,
                "adhd_optimized": True
            }

            # 2. Analyze sprint tasks for ADHD optimization
            sprint_tasks = sprint_data.get("tasks", [])
            for task in sprint_tasks:
                # Auto-decompose large tasks
                if task.get("estimated_minutes", 0) > 25:
                    await self._emit_auto_decomposition_event(task)

            # 3. Setup progress tracking automation
            await self._setup_sprint_progress_automation(sprint_id)

            # 4. Update Claude.md context automatically
            await self._update_claude_context_for_sprint(sprint_id, sprint_context)

            self.metrics["automation_triggers"] += 1

        except Exception as e:
            logger.error(f"Sprint start processing failed: {e}")

    async def _process_break_needed(self, event: CoordinationEvent) -> None:
        """Process break requirement with gentle ADHD accommodation."""
        try:
            task_data = event.data
            task_title = task_data.get("title", "current task")

            # 1. Pause current task gently
            await self._pause_task_gracefully(event.task_id)

            # 2. Preserve context for resumption
            context_preservation = {
                "task_id": event.task_id,
                "pause_reason": "break_needed",
                "context_snapshot": task_data,
                "resume_guidance": f"You were working on: {task_title}",
                "break_duration": "5-10 minutes recommended"
            }

            await self._store_context_preservation(context_preservation)

            # 3. Send gentle break notification
            break_notification = {
                "message": f"☕ Great progress on '{task_title}'! Time for a healthy break.",
                "duration_worked": task_data.get("duration_worked", "unknown"),
                "resume_context": "Context preserved for smooth resumption",
                "break_suggestions": ["5-minute walk", "Hydrate", "Stretch"]
            }

            await self._emit_break_notification(break_notification)

            self.metrics["adhd_accommodations"] += 1

        except Exception as e:
            logger.error(f"Break processing failed: {e}")

    async def _process_context_switch(self, event: CoordinationEvent) -> None:
        """Handle context switch with ADHD support."""
        try:
            self.active_context_switches += 1

            # Track context switching patterns
            if self.active_context_switches > 5:  # Excessive switching
                # Suggest focus mode
                focus_suggestion = {
                    "reason": "excessive_context_switching",
                    "switches_count": self.active_context_switches,
                    "suggestion": "Consider enabling focus mode to reduce distractions",
                    "recommended_action": "focus_mode_deep"
                }

                await self._emit_focus_suggestion(focus_suggestion)

            # Reset counter periodically
            if self.active_context_switches > 10:
                self.active_context_switches = 0

        except Exception as e:
            logger.error(f"Context switch processing failed: {e}")

    # System Integration Methods

    async def _trigger_adhd_decomposition(self, event: CoordinationEvent) -> None:
        """Trigger automatic ADHD task decomposition."""
        try:
            decomposition_event = CoordinationEvent(
                id=f"decomp_{event.task_id}",
                event_type=EventType.AUTOMATION_TRIGGERED,
                priority=EventPriority.HIGH,
                source_system="orchestrator",
                target_systems=["adhd_decomposer"],
                task_id=event.task_id,
                data={
                    "automation_type": "adhd_decomposition",
                    "original_task": event.data,
                    "target_duration": 25,
                    "preserve_context": True
                },
                cognitive_load=0.3,  # Low cognitive load for automation
                interruption_allowed=False
            )

            await self.emit_event(decomposition_event)

        except Exception as e:
            logger.error(f"ADHD decomposition trigger failed: {e}")

    async def _setup_conport_tracking(self, event: CoordinationEvent) -> None:
        """Setup ConPort progress tracking for task."""
        try:
            tracking_event = CoordinationEvent(
                id=f"track_{event.task_id}",
                event_type=EventType.AUTOMATION_TRIGGERED,
                priority=EventPriority.MEDIUM,
                source_system="orchestrator",
                target_systems=["conport"],
                task_id=event.task_id,
                data={
                    "automation_type": "progress_tracking_setup",
                    "task_context": event.data,
                    "tracking_type": "automatic"
                }
            )

            await self.emit_event(tracking_event)

        except Exception as e:
            logger.error(f"ConPort tracking setup failed: {e}")

    async def _update_claude_context_for_sprint(
        self,
        sprint_id: str,
        sprint_context: Dict[str, Any]
    ) -> None:
        """Automatically update Claude.md context for sprint."""
        try:
            # Store dynamic context that Claude.md can read
            context_key = f"claude_context:{self.workspace_id}:sprint:{sprint_id}"

            dynamic_context = {
                "active_sprint": sprint_id,
                "mode": sprint_context.get("mode", "PLAN"),
                "focus_area": sprint_context.get("focus", "Sprint execution"),
                "auto_managed": True,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "adhd_optimizations": {
                    "task_chunking": "automatic",
                    "break_management": "enabled",
                    "progress_tracking": "implicit",
                    "context_preservation": "active"
                }
            }

            await self.redis_client.setex(
                context_key,
                86400,  # 24 hours
                json.dumps(dynamic_context)
            )

            logger.info(f"📝 Updated Claude.md context for sprint {sprint_id}")

        except Exception as e:
            logger.error(f"Claude.md context update failed: {e}")

    # Utility Methods

    async def _store_event_history(self, event: CoordinationEvent, processing_time: float) -> None:
        """Store event processing history for analysis."""
        try:
            history_entry = {
                "event_id": event.id,
                "event_type": event.event_type.value,
                "priority": event.priority.name,
                "processing_time": processing_time,
                "cognitive_load": event.cognitive_load,
                "target_systems": event.target_systems,
                "success": event.error_message is None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Store in Redis with 7-day TTL
            history_key = f"events:history:{event.event_type.value}"
            await self.redis_client.lpush(
                history_key,
                json.dumps(history_entry)
            )

            # Keep only recent history
            await self.redis_client.ltrim(history_key, 0, 999)
            await self.redis_client.expire(history_key, 604800)  # 7 days

        except Exception as e:
            logger.error(f"Failed to store event history: {e}")

    # Placeholder methods for integration points
    async def _determine_optimal_agent(self, task_data: Dict[str, Any]) -> Optional[str]:
        """Determine optimal AI agent for task."""
        # Placeholder - would analyze task content and complexity
        return "conport"

    async def _assign_agent_to_task(self, task_id: str, agent: str) -> None:
        """Assign AI agent to task."""
        # Placeholder - would dispatch to specific agent
        pass

    async def _cache_task_context(self, event: CoordinationEvent) -> None:
        """Cache task context for quick access."""
        # Placeholder - would store in Redis
        pass

    async def _handle_task_start(self, event: CoordinationEvent) -> None:
        """Handle task start event."""
        # Placeholder - would setup monitoring and tracking
        pass

    async def _handle_task_completion(self, event: CoordinationEvent) -> None:
        """Handle task completion event."""
        # Placeholder - would update all systems and trigger next actions
        pass

    async def _handle_task_blocked(self, event: CoordinationEvent) -> None:
        """Handle task blocked event."""
        # Placeholder - would analyze blockers and suggest solutions
        pass

    async def _propagate_task_update(self, event: CoordinationEvent) -> None:
        """Propagate task update to all systems."""
        # Placeholder - would sync to Leantime, ConPort, local systems
        pass

    async def _pause_task_gracefully(self, task_id: str) -> None:
        """Pause task with context preservation."""
        # Placeholder - would preserve current state
        pass

    async def _store_context_preservation(self, context: Dict[str, Any]) -> None:
        """Store context for later resumption."""
        # Placeholder - would store in Redis/ConPort
        pass

    async def _emit_break_notification(self, notification: Dict[str, Any]) -> None:
        """Emit break notification."""
        # Placeholder - would send to UI/notification system
        pass

    async def _emit_focus_suggestion(self, suggestion: Dict[str, Any]) -> None:
        """Emit focus mode suggestion."""
        # Placeholder - would send to focus management system
        pass

    async def _emit_auto_decomposition_event(self, task: Dict[str, Any]) -> None:
        """Emit automatic decomposition event."""
        # Placeholder - would trigger decomposition
        pass

    async def _setup_sprint_progress_automation(self, sprint_id: str) -> None:
        """Setup automated progress tracking for sprint."""
        # Placeholder - would configure automatic progress monitoring
        pass

    # Health and Monitoring

    async def get_coordination_health(self) -> Dict[str, Any]:
        """Get comprehensive coordination system health."""
        try:
            # Check component health
            redis_healthy = await self.redis_client.ping() if self.redis_client else False

            # Check worker health
            active_workers = len([w for w in self.workers if not w.done()])

            # Check queue health
            queue_sizes = {
                priority.name: queue.qsize()
                for priority, queue in self.event_queues.items()
            }

            # Overall status assessment
            if redis_healthy and active_workers == len(self.workers):
                if max(queue_sizes.values()) < 50:
                    status = "🚀 Excellent"
                else:
                    status = "⚠️ Busy"
            else:
                status = "🔴 Degraded"

            return {
                "overall_status": status,
                "components": {
                    "redis_coordination": "🟢 Connected" if redis_healthy else "🔴 Disconnected",
                    "workers_active": f"{active_workers}/{len(self.workers)}",
                    "queue_sizes": queue_sizes
                },
                "metrics": self.metrics,
                "adhd_state": {
                    "focus_mode": self.current_focus_mode,
                    "energy_level": self.current_energy_level,
                    "context_switches": self.active_context_switches,
                    "last_break": self.last_break_time.isoformat()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Coordination health check failed: {e}")
            return {"overall_status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Shutdown event coordinator gracefully."""
        logger.info("🛑 Shutting down Event Coordinator...")

        # Stop processing
        self.running = False

        # Cancel workers
        if self.workers:
            for worker in self.workers:
                worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ Event Coordinator shutdown complete")


# Factory function for easy initialization
async def create_event_coordinator(
    redis_url: str = "redis://localhost:6379",
    workspace_id: str = "/Users/hue/code/dopemux-mvp"
) -> EventCoordinator:
    """Create and initialize event coordinator."""
    coordinator = EventCoordinator(redis_url)
    await coordinator.initialize()
    return coordinator