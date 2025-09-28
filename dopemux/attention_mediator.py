"""
Attention Mediator for ADHD-Optimized Event Filtering

Intelligently filters and batches events based on user's cognitive state and focus patterns.
"""

import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from .event_bus import EventBus, DopemuxEvent, Priority, CognitiveLoad


class FocusState(Enum):
    """User's current focus state for ADHD accommodation."""
    DEEP = "deep"              # Deep focus session, minimal interruptions
    PRODUCTIVE = "productive"   # Working but can handle some notifications
    SCATTERED = "scattered"     # Attention is scattered, batch everything
    TRANSITIONING = "transitioning"  # Between tasks, can handle more info
    BREAK = "break"            # On break, deliver queued items
    OFFLINE = "offline"        # Not actively working


class InterruptionTolerance(Enum):
    """How much interruption the user can handle."""
    NONE = "none"         # No interruptions at all
    CRITICAL = "critical" # Only critical/error events
    LOW = "low"          # Critical + high priority events
    MEDIUM = "medium"    # Normal filtering
    HIGH = "high"        # Most events allowed through


@dataclass
class AttentionProfile:
    """User's current attention state and preferences."""
    focus_state: FocusState
    interruption_tolerance: InterruptionTolerance
    current_task_context: str
    session_start_time: datetime
    last_activity_time: datetime
    break_suggested_at: Optional[datetime] = None
    total_focus_minutes_today: int = 0


@dataclass
class EventBatch:
    """Batched events for delivery during breaks."""
    events: List[DopemuxEvent]
    created_at: datetime
    category: str  # productivity, celebration, information
    priority_level: Priority


class AttentionMediator:
    """ADHD-optimized event filtering and delivery service."""

    def __init__(
        self,
        event_bus: EventBus,
        instance_id: str,
        delivery_callback: Callable[[DopemuxEvent], None],
        batch_callback: Optional[Callable[[EventBatch], None]] = None
    ):
        self.event_bus = event_bus
        self.instance_id = instance_id
        self.delivery_callback = delivery_callback
        self.batch_callback = batch_callback

        # User state
        self.attention_profile = AttentionProfile(
            focus_state=FocusState.PRODUCTIVE,
            interruption_tolerance=InterruptionTolerance.MEDIUM,
            current_task_context="general",
            session_start_time=datetime.now(),
            last_activity_time=datetime.now()
        )

        # Event management
        self.event_queue: List[DopemuxEvent] = []
        self.batches: Dict[str, EventBatch] = {}
        self.subscription_id: Optional[str] = None

        # Timers
        self.focus_timer_task: Optional[asyncio.Task] = None
        self.batch_delivery_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the attention mediator service."""
        # Subscribe to all events for this instance
        namespace_pattern = f"instance.{self.instance_id}.*"
        self.subscription_id = await self.event_bus.subscribe(
            namespace_pattern=namespace_pattern,
            callback=self._process_event,
            consumer_group=f"attention_mediator_{self.instance_id}"
        )

        # Start background tasks
        self.focus_timer_task = asyncio.create_task(self._focus_timer())
        self.batch_delivery_task = asyncio.create_task(self._batch_delivery_timer())

        print(f"🧠 Attention Mediator started for instance {self.instance_id}")

    async def stop(self):
        """Stop the attention mediator service."""
        if self.subscription_id:
            await self.event_bus.unsubscribe(self.subscription_id)

        if self.focus_timer_task:
            self.focus_timer_task.cancel()

        if self.batch_delivery_task:
            self.batch_delivery_task.cancel()

        print(f"🧠 Attention Mediator stopped for instance {self.instance_id}")

    def update_focus_state(
        self,
        new_state: FocusState,
        task_context: str = "",
        interruption_tolerance: Optional[InterruptionTolerance] = None
    ):
        """Update user's focus state and preferences."""
        old_state = self.attention_profile.focus_state

        self.attention_profile.focus_state = new_state
        self.attention_profile.last_activity_time = datetime.now()

        if task_context:
            self.attention_profile.current_task_context = task_context

        if interruption_tolerance:
            self.attention_profile.interruption_tolerance = interruption_tolerance

        # Handle state transitions
        if new_state == FocusState.DEEP and old_state != FocusState.DEEP:
            # Entering deep focus - increase filtering
            self.attention_profile.interruption_tolerance = InterruptionTolerance.CRITICAL
            print(f"🎯 Entering deep focus mode - minimal interruptions")

        elif new_state == FocusState.BREAK and old_state != FocusState.BREAK:
            # Starting break - deliver batched events
            asyncio.create_task(self._deliver_break_notifications())

        elif new_state == FocusState.SCATTERED:
            # Scattered attention - batch everything
            self.attention_profile.interruption_tolerance = InterruptionTolerance.NONE
            print(f"🌪️ Scattered attention mode - batching all events")

    def _process_event(self, event: DopemuxEvent):
        """Process incoming event through ADHD filter."""
        asyncio.create_task(self._async_process_event(event))

    async def _async_process_event(self, event: DopemuxEvent):
        """Async processing of events."""
        # Update activity time
        self.attention_profile.last_activity_time = datetime.now()

        # Determine if event should be delivered immediately
        should_deliver = self._should_deliver_immediately(event)

        if should_deliver:
            # Deliver immediately
            await self._deliver_event(event)
        else:
            # Add to queue for later delivery
            await self._queue_event(event)

    def _should_deliver_immediately(self, event: DopemuxEvent) -> bool:
        """Determine if event should bypass filtering."""
        # Always deliver critical events
        if event.envelope.priority == Priority.CRITICAL:
            return True

        # Always deliver error events
        if "error" in event.envelope.type.lower():
            return True

        # Check interruption tolerance
        tolerance = self.attention_profile.interruption_tolerance

        if tolerance == InterruptionTolerance.NONE:
            return False

        if tolerance == InterruptionTolerance.CRITICAL:
            return event.envelope.priority == Priority.CRITICAL

        if tolerance == InterruptionTolerance.LOW:
            return event.envelope.priority in [Priority.CRITICAL, Priority.HIGH]

        # Check ADHD metadata
        adhd_meta = event.envelope.adhd_metadata

        # Don't interrupt if attention is required but user is in deep focus
        if (adhd_meta.attention_required and
            self.attention_profile.focus_state == FocusState.DEEP):
            return False

        # Don't deliver if not interruption safe and user is focused
        if (not adhd_meta.interruption_safe and
            self.attention_profile.focus_state in [FocusState.DEEP, FocusState.PRODUCTIVE]):
            return False

        # Check cognitive load against current state
        if adhd_meta.cognitive_load in [CognitiveLoad.HIGH, CognitiveLoad.CRITICAL]:
            # High cognitive load events need careful handling
            if self.attention_profile.focus_state == FocusState.DEEP:
                return False  # Queue for later
            elif self.attention_profile.focus_state == FocusState.SCATTERED:
                return False  # User can't handle more cognitive load

        # Check context matching
        if (adhd_meta.focus_context != "general" and
            adhd_meta.focus_context != self.attention_profile.current_task_context):
            # Context doesn't match current focus
            if event.envelope.priority == Priority.NORMAL:
                return False

        return True

    async def _deliver_event(self, event: DopemuxEvent):
        """Deliver event to user immediately."""
        try:
            self.delivery_callback(event)
        except Exception as e:
            print(f"Error delivering event: {e}")

    async def _queue_event(self, event: DopemuxEvent):
        """Queue event for later delivery."""
        self.event_queue.append(event)

        # Batch similar events
        await self._update_batches(event)

        # Limit queue size to prevent memory issues
        if len(self.event_queue) > 100:
            # Remove oldest low-priority events
            self.event_queue = [
                e for e in self.event_queue[-80:]
                if e.envelope.priority in [Priority.CRITICAL, Priority.HIGH]
            ] + [e for e in self.event_queue[-20:]]

    async def _update_batches(self, event: DopemuxEvent):
        """Update event batches for organized delivery."""
        # Determine batch category
        category = self._get_batch_category(event)

        if category not in self.batches:
            self.batches[category] = EventBatch(
                events=[],
                created_at=datetime.now(),
                category=category,
                priority_level=event.envelope.priority
            )

        batch = self.batches[category]
        batch.events.append(event)

        # Update priority if this event is higher
        if event.envelope.priority.value > batch.priority_level.value:
            batch.priority_level = event.envelope.priority

        # Limit batch size
        if len(batch.events) > 20:
            batch.events = batch.events[-15:]  # Keep most recent

    def _get_batch_category(self, event: DopemuxEvent) -> str:
        """Categorize event for batching."""
        event_type = event.envelope.type

        if "celebration" in event_type or "completed" in event_type:
            return "celebration"
        elif "progress" in event_type or "task" in event_type:
            return "productivity"
        elif "error" in event_type or "blocked" in event_type:
            return "issues"
        elif "decision" in event_type or "pattern" in event_type:
            return "knowledge"
        else:
            return "information"

    async def _deliver_break_notifications(self):
        """Deliver batched events during break time."""
        if not self.batches:
            return

        print(f"☕ Break time - delivering {len(self.batches)} event batches")

        # Sort batches by priority
        sorted_batches = sorted(
            self.batches.values(),
            key=lambda b: (b.priority_level.value, len(b.events)),
            reverse=True
        )

        # Deliver batches
        for batch in sorted_batches:
            if self.batch_callback:
                try:
                    self.batch_callback(batch)
                except Exception as e:
                    print(f"Error delivering batch: {e}")
            else:
                # Fallback: deliver individual events
                for event in batch.events:
                    await self._deliver_event(event)

        # Clear batches
        self.batches.clear()
        self.event_queue.clear()

    async def _focus_timer(self):
        """Background timer for focus session management."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                session_duration = now - self.attention_profile.session_start_time
                idle_time = now - self.attention_profile.last_activity_time

                # Suggest break after long focus sessions
                if (self.attention_profile.focus_state == FocusState.DEEP and
                    session_duration > timedelta(minutes=25) and
                    not self.attention_profile.break_suggested_at):

                    await self._suggest_break()

                # Auto-transition to scattered if idle too long
                elif idle_time > timedelta(minutes=10):
                    if self.attention_profile.focus_state != FocusState.OFFLINE:
                        self.update_focus_state(FocusState.SCATTERED)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Focus timer error: {e}")

    async def _suggest_break(self):
        """Suggest a break to the user."""
        self.attention_profile.break_suggested_at = datetime.now()

        # Create a gentle break suggestion event
        break_event = DopemuxEvent.create(
            event_type="attention.break.suggested",
            namespace=f"instance.{self.instance_id}.adhd",
            payload={
                "message": "🌱 Consider taking a 5-minute break",
                "focus_duration_minutes": 25,
                "suggestion_type": "gentle",
                "can_dismiss": True
            },
            priority=Priority.LOW,
            adhd_metadata=event.envelope.adhd_metadata  # Use existing metadata structure
        )

        # Always deliver break suggestions (they're designed to be gentle)
        await self._deliver_event(break_event)

    async def _batch_delivery_timer(self):
        """Periodic delivery of batched events during productive states."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                # Only deliver during productive or transitioning states
                if self.attention_profile.focus_state in [FocusState.PRODUCTIVE, FocusState.TRANSITIONING]:
                    if self.batches:
                        # Deliver only celebration and low-priority information
                        celebration_batches = [
                            batch for batch in self.batches.values()
                            if batch.category in ["celebration", "information"]
                            and batch.priority_level == Priority.LOW
                        ]

                        for batch in celebration_batches:
                            if self.batch_callback:
                                self.batch_callback(batch)
                            # Remove delivered batch
                            if batch.category in self.batches:
                                del self.batches[batch.category]

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Batch delivery timer error: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current attention mediator status."""
        return {
            "instance_id": self.instance_id,
            "attention_profile": asdict(self.attention_profile),
            "queued_events": len(self.event_queue),
            "active_batches": len(self.batches),
            "batch_details": {
                category: len(batch.events)
                for category, batch in self.batches.items()
            },
            "subscription_active": self.subscription_id is not None
        }