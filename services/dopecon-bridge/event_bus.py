"""
Redis Streams Event Bus for DopeconBridge
Async event coordination between ConPort, ADHD Engine, and Dashboard
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

import redis.asyncio as redis

from event_deduplication import EventDeduplicator
from cache import MultiTierCache
from rate_limiter import RateLimiter
from monitoring import DopeconBridgeMetrics

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Defined event types for Dopemux coordination.
    
    Event categories:
    - Session: Work session lifecycle
    - Progress: Task completion and progress
    - Activity: File/window/app activity (from watchers)
    - ADHD State: Energy, attention, and state changes
    - Detection: Outputs from ADHD detectors
    - Calendar/Social: Meeting and communication events
    - Medication: Medication tracking events
    - User Actions: Explicit user-triggered events
    """
    
    # ─────────────────────────────────────────────────────────────
    # Session Events
    # ─────────────────────────────────────────────────────────────
    SESSION_STARTED = "session_started"
    SESSION_PAUSED = "session_paused"
    SESSION_COMPLETED = "session_completed"
    SESSION_RESUMED = "session_resumed"
    
    # ─────────────────────────────────────────────────────────────
    # Progress Events
    # ─────────────────────────────────────────────────────────────
    TASKS_IMPORTED = "tasks_imported"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_SWITCHED = "task_switched"
    PROGRESS_UPDATED = "progress_updated"
    DECISION_LOGGED = "decision_logged"
    GIT_COMMIT = "git_commit"
    
    # ─────────────────────────────────────────────────────────────
    # Activity Events (from Workspace Watcher, Desktop Commander)
    # ─────────────────────────────────────────────────────────────
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"
    FILE_CLOSED = "file_closed"
    FILE_ACTIVITY = "file_activity"           # Generic file action
    WINDOW_SWITCHED = "window_switched"       # Desktop Commander
    APP_FOCUSED = "app_focused"               # Desktop Commander
    TAB_SWITCHED = "tab_switched"             # Browser MCP
    IDLE_DETECTED = "idle_detected"
    ACTIVITY_RESUMED = "activity_resumed"
    
    # ─────────────────────────────────────────────────────────────
    # ADHD State Events
    # ─────────────────────────────────────────────────────────────
    ADHD_STATE_CHANGED = "adhd_state_changed"
    ENERGY_CHANGED = "energy_changed"
    ATTENTION_CHANGED = "attention_changed"
    BREAK_SUGGESTED = "break_suggested"
    BREAK_ACCEPTED = "break_accepted"
    BREAK_REFUSED = "break_refused"
    BREAK_COMPLETED = "break_completed"
    BREAK_REMINDER = "break_reminder"
    
    # ─────────────────────────────────────────────────────────────
    # Detection Events (outputs from ADHD services)
    # ─────────────────────────────────────────────────────────────
    HYPERFOCUS_DETECTED = "hyperfocus_detected"
    HYPERFOCUS_WARNING = "hyperfocus_warning"
    HYPERFOCUS_CRITICAL = "hyperfocus_critical"
    OVERWHELM_DETECTED = "overwhelm_detected"
    OVERWHELM_CIRCUIT_BREAKER = "overwhelm_circuit_breaker"
    PROCRASTINATION_DETECTED = "procrastination_detected"
    CONTEXT_SWITCH_DETECTED = "context_switch_detected"
    UNTRACKED_WORK_DETECTED = "untracked_work_detected"
    ABANDONMENT_WARNING = "abandonment_warning"
    
    # ─────────────────────────────────────────────────────────────
    # Calendar/Social Events
    # ─────────────────────────────────────────────────────────────
    MEETING_STARTED = "meeting_started"
    MEETING_ENDED = "meeting_ended"
    MEETING_UPCOMING = "meeting_upcoming"     # Warning before meeting
    SOCIAL_BATTERY_LOW = "social_battery_low"
    SOCIAL_BATTERY_CRITICAL = "social_battery_critical"
    
    # ─────────────────────────────────────────────────────────────
    # Medication Events
    # ─────────────────────────────────────────────────────────────
    MEDICATION_LOGGED = "medication_logged"
    MEDICATION_REMINDER = "medication_reminder"
    MEDICATION_WINDOW_ENTERED = "medication_window_entered"
    MEDICATION_WINDOW_EXITING = "medication_window_exiting"
    
    # ─────────────────────────────────────────────────────────────
    # User Actions (explicit user-triggered)
    # ─────────────────────────────────────────────────────────────
    USER_FEEDBACK = "user_feedback"
    THOUGHT_CAPTURED = "thought_captured"
    CONTEXT_SAVED = "context_saved"
    CONTEXT_RESTORED = "context_restored"
    WIND_DOWN_STARTED = "wind_down_started"
    WIND_DOWN_COMPLETED = "wind_down_completed"
    
    # ─────────────────────────────────────────────────────────────
    # Claude Code Integration Events
    # ─────────────────────────────────────────────────────────────
    CLAUDE_PROMPT_RECEIVED = "claude_prompt_received"
    CLAUDE_TOOL_STARTED = "claude_tool_started"
    CLAUDE_TOOL_COMPLETED = "claude_tool_completed"
    CLAUDE_SESSION_STOPPED = "claude_session_stopped"


@dataclass
class Event:
    """Structured event with type and data"""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    source: Optional[str] = None
    workspace_path: Optional[str] = None  # Multi-workspace tracking

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_redis_dict(self) -> Dict[str, str]:
        """Convert to Redis Stream message format"""
        return {
            "event_type": self.type,
            "timestamp": self.timestamp,
            "source": self.source or "dopecon-bridge",
            "data": json.dumps(self.data)
        }

    @classmethod
    def from_redis_dict(cls, msg_data: Dict[bytes, bytes]) -> 'Event':
        """Parse from Redis Stream message"""
        return cls(
            type=msg_data[b"event_type"].decode("utf-8"),
            timestamp=msg_data[b"timestamp"].decode("utf-8"),
            source=msg_data.get(b"source", b"unknown").decode("utf-8"),
            data=json.loads(msg_data[b"data"].decode("utf-8"))
        )


class EventBus:
    """
    Redis Streams-based event bus for async coordination

    Features:
    - Publish events to named streams
    - Subscribe with consumer groups for load balancing
    - Automatic consumer group creation
    - Message acknowledgment
    - ADHD-optimized: Non-blocking, resilient to interruptions
    """

    def __init__(
        self,
        redis_url: str,
        password: Optional[str] = None,
        enable_deduplication: bool = True,
        enable_cache: bool = True,
        enable_rate_limiting: bool = True,
        enable_monitoring: bool = True
    ):
        """
        Initialize EventBus with Redis connection

        Args:
            redis_url: Redis connection URL
            password: Optional Redis password
            enable_deduplication: Enable event deduplication (default: True)
            enable_cache: Enable multi-tier caching (default: True)
            enable_rate_limiting: Enable rate limiting (default: True)
            enable_monitoring: Enable Prometheus metrics (default: True)
        """
        self.redis_url = redis_url
        self.password = password
        self.redis_client: Optional[redis.Redis] = None
        self._subscribers: Dict[str, bool] = {}  # Track active subscribers

        # Phase 2 features
        self.enable_deduplication = enable_deduplication
        self.deduplicator: Optional[EventDeduplicator] = None

        # Phase 3 features
        self.enable_cache = enable_cache
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_monitoring = enable_monitoring
        self.cache: Optional[MultiTierCache] = None
        self.rate_limiter: Optional[RateLimiter] = None
        self.metrics: Optional[DopeconBridgeMetrics] = None

    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                password=self.password if self.password else None,
                decode_responses=False,  # Keep binary for Stream compatibility
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("✅ EventBus Redis connection established")

            # Initialize Phase 2 features
            if self.enable_deduplication:
                self.deduplicator = EventDeduplicator(
                    redis_client=self.redis_client,
                    ttl_seconds=300
                )
                logger.info("✅ EventBus deduplication enabled (5min window)")

            # Initialize Phase 3 features
            if self.enable_cache:
                self.cache = MultiTierCache(
                    redis_client=self.redis_client,
                    memory_ttl=5,
                    redis_ttl=60
                )
                logger.info("✅ EventBus multi-tier cache enabled")

            if self.enable_rate_limiting:
                self.rate_limiter = RateLimiter(
                    redis_client=self.redis_client,
                    user_limit_per_minute=100,
                    workspace_limit_per_minute=1000
                )
                logger.info("✅ EventBus rate limiting enabled (100/1000 req/min)")

            if self.enable_monitoring:
                self.metrics = DopeconBridgeMetrics()
                logger.info("✅ EventBus Prometheus monitoring enabled")

        except Exception as e:
            logger.error(f"❌ EventBus Redis initialization failed: {e}")
            raise

    async def publish(self, stream: str, event: Event, user_id: Optional[str] = None, workspace_id: Optional[str] = None) -> Optional[str]:
        """
        Publish event to Redis Stream with Phase 3 features.

        Args:
            stream: Stream name (e.g., "dopemux:events")
            event: Event to publish
            user_id: Optional user ID for rate limiting
            workspace_id: Optional workspace ID for rate limiting

        Returns:
            Message ID from Redis, or None if deduplicated/rate-limited
        """
        if not self.redis_client:
            raise RuntimeError("EventBus not initialized")

        import time
        start_time = time.time()

        try:
            # Phase 3: Check rate limit
            if self.rate_limiter and (user_id or workspace_id):
                allowed, retry_after = await self.rate_limiter.check_limit(user_id, workspace_id)
                if not allowed:
                    logger.warning(f"⏭️  Rate limit exceeded for {user_id or workspace_id}, retry after {retry_after}s")
                    if self.metrics:
                        self.metrics.record_event_published(event.source or "unknown", event.type, 0)
                    return None

            # Phase 2: Check for duplicate
            if self.deduplicator:
                event_data = {
                    "type": event.type,
                    "data": event.data,
                    "source": event.source
                }

                is_duplicate = await self.deduplicator.is_duplicate(event_data)

                # Phase 3: Record dedup check in metrics
                if self.metrics:
                    self.metrics.record_dedup_check(is_duplicate)

                if is_duplicate:
                    logger.debug(f"⏭️  Skipped duplicate event: {event.type}")
                    return None

                # Mark as processed
                await self.deduplicator.mark_processed(event_data)

            # Publish to Redis
            msg_id = await self.redis_client.xadd(
                stream,
                event.to_redis_dict()
            )

            # Phase 3: Record metrics
            if self.metrics:
                latency = time.time() - start_time
                self.metrics.record_event_published(event.source or "unknown", event.type, latency)
                self.metrics.record_agent_event(event.source or "unknown", event.type)

            logger.info(f"📤 Published {event.type} to {stream} (ID: {msg_id.decode()})")
            return msg_id.decode()

        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
            if self.metrics:
                self.metrics.record_agent_emission_error(event.source or "unknown")
            raise

    async def subscribe(
        self,
        stream: str,
        consumer_group: str,
        consumer_name: Optional[str] = None
    ) -> AsyncGenerator[Tuple[str, Event], None]:
        """
        Subscribe to Redis Stream with consumer group

        Args:
            stream: Stream name to subscribe to
            consumer_group: Consumer group name for load balancing
            consumer_name: Optional consumer name (auto-generated if not provided)

        Yields:
            Tuple of (message_id, Event)
        """
        if not self.redis_client:
            raise RuntimeError("EventBus not initialized")

        # Generate consumer name if not provided
        if not consumer_name:
            consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"

        # Create consumer group if not exists
        try:
            await self.redis_client.xgroup_create(
                stream,
                consumer_group,
                id='0',
                mkstream=True  # Create stream if it doesn't exist
            )
            logger.info(f"✅ Created consumer group: {consumer_group} on {stream}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"❌ Failed to create consumer group: {e}")
                raise
            # Group already exists, continue

        # Mark as active subscriber
        subscriber_key = f"{stream}:{consumer_group}:{consumer_name}"
        self._subscribers[subscriber_key] = True

        logger.info(f"📥 Subscribing to {stream} as {consumer_group}/{consumer_name}")

        try:
            # Read events from stream
            while self._subscribers.get(subscriber_key, False):
                try:
                    # Read from stream (blocking with 1 second timeout)
                    events = await self.redis_client.xreadgroup(
                        groupname=consumer_group,
                        consumername=consumer_name,
                        streams={stream: '>'},
                        count=10,
                        block=1000
                    )

                    # Process received events
                    if events:
                        for stream_name, messages in events:
                            for msg_id, msg_data in messages:
                                try:
                                    # Parse event
                                    event = Event.from_redis_dict(msg_data)

                                    # Yield to consumer
                                    yield msg_id.decode(), event

                                    # Acknowledge message
                                    await self.redis_client.xack(
                                        stream,
                                        consumer_group,
                                        msg_id
                                    )

                                except Exception as e:
                                    logger.error(f"❌ Error processing message {msg_id}: {e}")
                                    # Don't ack, message will be retried

                except redis.RedisError as e:
                    logger.error(f"❌ Redis error in subscriber: {e}")
                    # Wait before retry
                    await asyncio.sleep(1)

        finally:
            # Cleanup on exit
            self._subscribers.pop(subscriber_key, None)
            logger.info(f"📭 Unsubscribed: {consumer_group}/{consumer_name}")

    async def unsubscribe(self, stream: str, consumer_group: str, consumer_name: str):
        """Stop a specific subscriber"""
        subscriber_key = f"{stream}:{consumer_group}:{consumer_name}"
        self._subscribers[subscriber_key] = False

    async def close(self):
        """Close Redis connection and stop all subscribers"""
        # Stop all subscribers
        for key in list(self._subscribers.keys()):
            self._subscribers[key] = False

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
            logger.info("📪 EventBus closed")

    async def get_stream_info(self, stream: str) -> Dict[str, Any]:
        """Get information about a stream (for debugging/monitoring)"""
        if not self.redis_client:
            raise RuntimeError("EventBus not initialized")

        try:
            info = await self.redis_client.xinfo_stream(stream)
            return {
                "length": info.get(b"length", 0),
                "groups": info.get(b"groups", 0),
                "first_entry": info.get(b"first-entry"),
                "last_entry": info.get(b"last-entry")
            }
        except redis.ResponseError:
            # Stream doesn't exist
            return {"length": 0, "groups": 0}


# Convenience functions for common event types

async def publish_tasks_imported(bus: EventBus, task_count: int, sprint_id: str):
    """Publish tasks_imported event"""
    event = Event(
        type=EventType.TASKS_IMPORTED,
        data={"task_count": task_count, "sprint_id": sprint_id}
    )
    await bus.publish("dopemux:events", event)


async def publish_session_started(bus: EventBus, task_id: str, duration_minutes: int = 25):
    """Publish session_started event"""
    event = Event(
        type=EventType.SESSION_STARTED,
        data={"task_id": task_id, "duration_minutes": duration_minutes}
    )
    await bus.publish("dopemux:events", event)


async def publish_progress_updated(bus: EventBus, task_id: str, status: str, progress: float):
    """Publish progress_updated event"""
    event = Event(
        type=EventType.PROGRESS_UPDATED,
        data={"task_id": task_id, "status": status, "progress": progress}
    )
    await bus.publish("dopemux:events", event)
