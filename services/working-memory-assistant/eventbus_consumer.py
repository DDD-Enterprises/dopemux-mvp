"""
Dope-Memory EventBus Consumer — Real-time Event Ingestion.

Subscribes to activity.events.v1 stream and processes events through
the promotion engine to create curated work_log_entries.

Per spec:
- Input stream: activity.events.v1
- Output stream: memory.derived.v1
- Consumer group: dope-memory-ingestor
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import redis.asyncio as redis

from chronicle.store import ChronicleStore
from promotion.redactor import Redactor
from promotion.promotion import PromotionEngine
from reflection.reflection import ReflectionGenerator
from trajectory.manager import TrajectoryManager

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
INPUT_STREAM = os.getenv("DOPE_MEMORY_INPUT_STREAM", "activity.events.v1")
OUTPUT_STREAM = os.getenv("DOPE_MEMORY_OUTPUT_STREAM", "memory.derived.v1")
CONSUMER_GROUP = os.getenv("DOPE_MEMORY_CONSUMER_GROUP", "dope-memory-ingestor")
DATA_DIR = Path(os.getenv("DOPE_MEMORY_DATA_DIR", str(Path.home() / ".dope-memory")))

# Phase 2 Configuration
# All timing parameters are configurable via environment variables
DOPE_MEMORY_IDLE_MINUTES = int(os.getenv("DOPE_MEMORY_IDLE_MINUTES", "20"))
DOPE_MEMORY_PULSE_INTERVAL_SECONDS = int(os.getenv("DOPE_MEMORY_PULSE_INTERVAL_SECONDS", "2700"))  # 45 minutes default
DOPE_MEMORY_PULSE_JITTER_SECONDS = int(os.getenv("DOPE_MEMORY_PULSE_JITTER_SECONDS", "300"))  # 5 minutes jitter
DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES = int(os.getenv("DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES", "30"))
DOPE_MEMORY_REFLECTION_MAX_WINDOW_HOURS = int(os.getenv("DOPE_MEMORY_REFLECTION_MAX_WINDOW_HOURS", "2"))
DOPE_MEMORY_REFLECTION_COOLDOWN_SECONDS = int(os.getenv("DOPE_MEMORY_REFLECTION_COOLDOWN_SECONDS", "300"))  # Not used currently, but available
ENABLE_DOPECONTEXT_INDEX = os.getenv("ENABLE_DOPECONTEXT_INDEX", "false").lower() == "true"
DOPECONTEXT_URL = os.getenv("DOPECONTEXT_URL", "http://localhost:3010")

# Legacy env vars for backward compatibility (deprecated)
IDLE_MINUTES = DOPE_MEMORY_IDLE_MINUTES
PULSE_INTERVAL_SECONDS = DOPE_MEMORY_PULSE_INTERVAL_SECONDS
REFLECTION_MIN_WINDOW_MINUTES = DOPE_MEMORY_REFLECTION_MIN_WINDOW_MINUTES
REFLECTION_MAX_WINDOW_HOURS = DOPE_MEMORY_REFLECTION_MAX_WINDOW_HOURS

# High-signal events that reset last_activity_at
HIGH_SIGNAL_EVENTS = {
    "decision.logged",
    "task.completed",
    "task.failed",
    "task.blocked",
    "error.encountered",
    "manual.memory_store",
    "workflow.phase_changed",
}

# Heartbeat events: reset idle timer but don't trigger reflections
# These represent activity but not work worth capturing
HEARTBEAT_EVENTS = {
    "message.sent",
    "file.opened",
    "git.commit.created",
}


class SessionTracker:
    """Track session state for idle detection and reflection boundaries.
    
    Per (workspace_id, instance_id, session_id):
    - last_activity_at: Last high-signal event
    - last_pulse_at: Last pulse emission
    - last_reflection_window_end: Last reflection generated
    - ended_at: Explicit session end timestamp
    """
    
    def __init__(self, clock=None):
        """Initialize SessionTracker.
        
        Args:
            clock: Optional callable that returns current datetime (for testing).
                   Defaults to lambda: datetime.now(timezone.utc)
        """
        self._sessions: dict[tuple[str, str, str], dict[str, Any]] = {}
        self._clock = clock or (lambda: datetime.now(timezone.utc))
    
    def _session_key(self, workspace_id: str, instance_id: str, session_id: str) -> tuple[str, str, str]:
        """Generate session key."""
        return (workspace_id, instance_id, session_id or "")
    
    def update_activity(self, workspace_id: str, instance_id: str, session_id: str, is_heartbeat: bool = False) -> None:
        """Update last_activity_at for high-signal event or heartbeat.
        
        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            session_id: Session identifier
            is_heartbeat: If True, only resets idle timer (no reflection trigger)
        """
        key = self._session_key(workspace_id, instance_id, session_id)
        now = self._clock()
        
        if key not in self._sessions:
            self._sessions[key] = {
                "workspace_id": workspace_id,
                "instance_id": instance_id,
                "session_id": session_id,
                "last_activity_at": now,
                "last_pulse_at": None,
                "last_reflection_window_end": None,
                "ended_at": None,
                "is_heartbeat_only": is_heartbeat,  # Track if last activity was heartbeat
            }
        else:
            self._sessions[key]["last_activity_at"] = now
            self._sessions[key]["is_heartbeat_only"] = is_heartbeat
    
    def mark_pulse(self, workspace_id: str, instance_id: str, session_id: str) -> None:
        """Mark pulse emission time."""
        key = self._session_key(workspace_id, instance_id, session_id)
        if key in self._sessions:
            self._sessions[key]["last_pulse_at"] = self._clock()
    
    def mark_reflection(self, workspace_id: str, instance_id: str, session_id: str) -> None:
        """Mark reflection generation time."""
        key = self._session_key(workspace_id, instance_id, session_id)
        if key in self._sessions:
            self._sessions[key]["last_reflection_window_end"] = self._clock()
    
    def mark_ended(self, workspace_id: str, instance_id: str, session_id: str) -> None:
        """Mark explicit session end."""
        key = self._session_key(workspace_id, instance_id, session_id)
        if key in self._sessions:
            self._sessions[key]["ended_at"] = self._clock()
    
    def is_idle(self, workspace_id: str, instance_id: str, session_id: str) -> bool:
        """Check if session is idle (> IDLE_MINUTES since last activity)."""
        key = self._session_key(workspace_id, instance_id, session_id)
        if key not in self._sessions:
            return False
        
        session = self._sessions[key]
        if session["ended_at"]:
            return True  # Already ended
        
        last_activity = session["last_activity_at"]
        now = self._clock()
        idle_seconds = (now - last_activity).total_seconds()
        
        return idle_seconds >= (IDLE_MINUTES * 60)
    
    def should_generate_reflection(self, workspace_id: str, instance_id: str, session_id: str) -> bool:
        """Check if reflection should be generated.
        
        Triggers:
        - Explicit session end
        - Idle threshold exceeded
        - Periodic boundary (REFLECTION_MAX_WINDOW_HOURS)
        - Minimum window duration met (REFLECTION_MIN_WINDOW_MINUTES)
        """
        key = self._session_key(workspace_id, instance_id, session_id)
        if key not in self._sessions:
            return False
        
        session = self._sessions[key]
        now = self._clock()
        
        # Signal A: Explicit end
        if session["ended_at"]:
            return True
        
        # Check minimum window duration
        last_reflection = session["last_reflection_window_end"]
        if last_reflection:
            since_last_reflection = (now - last_reflection).total_seconds() / 60
            if since_last_reflection < REFLECTION_MIN_WINDOW_MINUTES:
                return False  # Too soon
        
        # Signal B: Idle end
        if self.is_idle(workspace_id, instance_id, session_id):
            return True
        
        # Periodic boundary (max window)
        if last_reflection:
            hours_since = (now - last_reflection).total_seconds() / 3600
            if hours_since >= REFLECTION_MAX_WINDOW_HOURS:
                return True
        
        return False
    
    def get_active_sessions(self) -> list[tuple[str, str, str]]:
        """Get all active (non-ended) session keys."""
        active = []
        for key, session in self._sessions.items():
            if not session["ended_at"]:
                active.append(key)
        return active


class EventBusConsumer:
    """
    EventBus consumer for Dope-Memory.

    Subscribes to activity.events.v1 and:
    1. Stores all events in raw_activity_events (with TTL)
    2. Promotes eligible events to work_log_entries
    3. Publishes derived events to memory.derived.v1
    """

    def __init__(
        self,
        redis_url: str = REDIS_URL,
        redis_password: Optional[str] = REDIS_PASSWORD,
        data_dir: Path = DATA_DIR,
        input_stream: str = INPUT_STREAM,
        output_stream: str = OUTPUT_STREAM,
        consumer_group: str = CONSUMER_GROUP,
    ):
        self.redis_url = redis_url
        self.redis_password = redis_password
        self.data_dir = data_dir
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.consumer_group = consumer_group
        self.consumer_name = f"consumer-{uuid.uuid4().hex[:8]}"

        self.redis_client: Optional[redis.Redis] = None
        self.redactor = Redactor()
        self.promotion_engine = PromotionEngine()
        self._stores: dict[str, ChronicleStore] = {}
        self._running = False
        
        # Phase 2: Session tracking
        self.session_tracker = SessionTracker()
        self._pulse_task: Optional[asyncio.Task] = None
        self._session_monitor_task: Optional[asyncio.Task] = None
        
        # Phase 2: Trajectory managers per workspace
        self._trajectory_managers: dict[str, TrajectoryManager] = {}

    async def initialize(self) -> None:
        """Initialize Redis connection and create consumer group."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                password=self.redis_password,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            await self.redis_client.ping()
            logger.info(f"✅ Dope-Memory EventBus consumer connected to Redis")

            # Create consumer group (idempotent)
            try:
                await self.redis_client.xgroup_create(
                    self.input_stream, self.consumer_group, id="0", mkstream=True
                )
                logger.info(f"✅ Created consumer group: {self.consumer_group}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
                # Group already exists

            # Ensure data directory
            self.data_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"❌ Failed to initialize EventBus consumer: {e}")
            raise

    def _get_store(self, workspace_id: str) -> ChronicleStore:
        """Get or create ChronicleStore for workspace."""
        if workspace_id not in self._stores:
            db_path = self.data_dir / workspace_id / "chronicle.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            store = ChronicleStore(db_path)
            store.initialize_schema()
            self._stores[workspace_id] = store
        return self._stores[workspace_id]

    async def start(self) -> None:
        """Start consuming events."""
        if not self.redis_client:
            await self.initialize()

        self._running = True
        logger.info(
            f"📥 Starting Dope-Memory EventBus consumer: "
            f"{self.input_stream} -> {self.consumer_group}/{self.consumer_name}"
        )
        
        # Start background pulse emission task
        self._pulse_task = asyncio.create_task(self._pulse_emission_loop())
        
        # Start session monitoring task (idle detection)
        self._session_monitor_task = asyncio.create_task(self._session_monitor_loop())

        while self._running:
            try:
                # Read from stream (blocking with 1s timeout)
                events = await self.redis_client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={self.input_stream: ">"},
                    count=10,
                    block=1000,
                )

                if events:
                    for stream_name, messages in events:
                        for msg_id, msg_data in messages:
                            try:
                                await self._process_message(msg_id, msg_data)
                                await self.redis_client.xack(
                                    self.input_stream, self.consumer_group, msg_id
                                )
                            except Exception as e:
                                logger.error(f"❌ Error processing message {msg_id}: {e}")
                                # Don't ack - message will be retried

            except redis.RedisError as e:
                logger.error(f"❌ Redis error in consumer: {e}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ Unexpected error in consumer: {e}")
                await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop consuming events."""
        self._running = False
        
        # Cancel background tasks
        for task in [self._pulse_task, self._session_monitor_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        if self.redis_client:
            await self.redis_client.close()
        logger.info("📭 Dope-Memory EventBus consumer stopped")

    async def _process_message(self, msg_id: bytes, msg_data: dict[bytes, bytes]) -> None:
        """Process a single event message."""
        # Parse event envelope
        try:
            event = self._parse_event(msg_data)
        except Exception as e:
            logger.warning(f"⚠️  Failed to parse event {msg_id}: {e}")
            return

        workspace_id = event.get("workspace_id", "default")
        instance_id = event.get("instance_id", "A")
        event_type = event.get("type", "unknown")
        source = event.get("source", "unknown")
        data = event.get("data", {})
        session_id = event.get("session_id")

        logger.debug(f"📨 Processing event: {event_type} from {source}")
        
        # Phase 2: Track high-signal activity
        if event_type in HIGH_SIGNAL_EVENTS:
            self.session_tracker.update_activity(workspace_id, instance_id, session_id or "", is_heartbeat=False)
        elif event_type in HEARTBEAT_EVENTS:
            # Heartbeat: reset idle timer but don't trigger reflection
            self.session_tracker.update_activity(workspace_id, instance_id, session_id or "", is_heartbeat=True)
        
        # Phase 2: Signal A - Explicit session end
        if event_type == "session.ended":
            self.session_tracker.mark_ended(workspace_id, instance_id, session_id or "")
            await self._handle_session_end(workspace_id, instance_id, session_id)
            return
        
        # Phase 2: Signal C - Workflow completion trigger (reflection boundary)
        if event_type in ("task.completed", "task.failed", "workflow.deployment_started"):
            if self.session_tracker.should_generate_reflection(workspace_id, instance_id, session_id or ""):
                await self._generate_reflection_boundary(workspace_id, instance_id, session_id)

        store = self._get_store(workspace_id)

        # Step 1: Redact payload
        redacted_data = self.redactor.redact_payload(data)

        # Step 2: Store raw event (with TTL)
        store.insert_raw_event(
            workspace_id=workspace_id,
            instance_id=instance_id,
            event_id=event.get("id", str(uuid.uuid4())),
            event_type=event_type,
            source=source,
            payload=redacted_data,
            ts_utc=event.get("ts", datetime.now(timezone.utc).isoformat()),
            session_id=event.get("session_id"),
        )

        # Step 3: Attempt promotion
        # The promotion engine expects the data payload fields at top level
        entry = self.promotion_engine.promote(event_type, redacted_data)

        if entry:
            entry_id = store.insert_work_log_entry(
                workspace_id=workspace_id,
                instance_id=instance_id,
                category=entry.category,
                entry_type=entry.entry_type,
                summary=entry.summary,
                session_id=event.get("session_id"),
                importance_score=entry.importance_score,
                tags=entry.tags,
                details=entry.details,
                reasoning=entry.reasoning,
                outcome=entry.outcome,
                linked_files=entry.linked_files,
                linked_commits=entry.linked_commits,
                linked_decisions=entry.linked_decisions,
            )

            logger.info(f"✅ Promoted {event_type} -> {entry.category}/{entry.entry_type} ({entry_id})")
            
            # Phase 2: Update trajectory state
            await self._update_trajectory(workspace_id, instance_id, {
                "id": entry_id,
                "category": entry.category,
                "entry_type": entry.entry_type,
                "summary": entry.summary,
                "session_id": event.get("session_id"),
                "tags": entry.tags or [],
            })

            # Step 4: Publish derived event
            await self._publish_derived_event(
                event_type="worklog.created",
                data={
                    "entry_id": entry_id,
                    "category": entry.category,
                    "entry_type": entry.entry_type,
                    "importance_score": entry.importance_score,
                    "summary": entry.summary[:100],
                },
                workspace_id=workspace_id,
                instance_id=instance_id,
            )
            
            # Phase 2: Index in DopeContext (best-effort)
            if ENABLE_DOPECONTEXT_INDEX:
                await self._index_in_dopecontext(
                    entry_id=entry_id,
                    workspace_id=workspace_id,
                    category=entry.category,
                    summary=entry.summary,
                    details=entry.details,
                )
        else:
            logger.debug(f"⏭️  Event {event_type} not promoted (raw-only)")

    def _parse_event(self, msg_data: dict[bytes, bytes]) -> dict[str, Any]:
        """Parse event from Redis message data."""
        # Handle both string and binary keys/values
        result = {}
        for key, value in msg_data.items():
            key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            val_str = value.decode("utf-8") if isinstance(value, bytes) else value

            # Parse JSON fields
            if key_str == "data":
                try:
                    result[key_str] = json.loads(val_str)
                except json.JSONDecodeError:
                    result[key_str] = {"raw": val_str}
            else:
                result[key_str] = val_str

        # Map old event type field to new
        if "event_type" in result and "type" not in result:
            result["type"] = result["event_type"]

        return result

    async def _publish_derived_event(
        self,
        event_type: str,
        data: dict[str, Any],
        workspace_id: str,
        instance_id: str,
    ) -> None:
        """Publish derived event to output stream."""
        if not self.redis_client:
            return

        try:
            event_envelope = {
                b"id": str(uuid.uuid4()).encode(),
                b"ts": datetime.now(timezone.utc).isoformat().encode(),
                b"workspace_id": workspace_id.encode(),
                b"instance_id": instance_id.encode(),
                b"type": event_type.encode(),
                b"source": b"dope-memory",
                b"data": json.dumps(data).encode(),
            }
            msg_id = await self.redis_client.xadd(self.output_stream, event_envelope)
            logger.debug(f"📤 Published {event_type} to {self.output_stream} ({msg_id.decode()})")
        except Exception as e:
            logger.warning(f"⚠️  Failed to publish derived event: {e}")

    # ═════════════════════════════════════════════════════════════════
    # Phase 2: Pulse Emission
    # ═════════════════════════════════════════════════════════════════

    async def _pulse_emission_loop(self) -> None:
        """Background task to emit memory.pulse events periodically."""
        import random
        
        # Add jitter to avoid synchronization storms
        jitter = random.randint(-DOPE_MEMORY_PULSE_JITTER_SECONDS, DOPE_MEMORY_PULSE_JITTER_SECONDS)
        interval = DOPE_MEMORY_PULSE_INTERVAL_SECONDS + jitter
        
        logger.info(f"🫀 Pulse emission loop started (interval: {interval}s)")
        
        while self._running:
            try:
                await asyncio.sleep(interval)
                
                # Emit pulse for each active session
                for session_key in self.session_tracker.get_active_sessions():
                    workspace_id, instance_id, session_id = session_key
                    await self._emit_pulse(workspace_id, instance_id, session_id)
                    
            except asyncio.CancelledError:
                logger.info("🫀 Pulse emission loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Pulse emission error: {e}")
                await asyncio.sleep(60)  # Back off on error

    async def _session_monitor_loop(self) -> None:
        """Background task to check for idle sessions (Signal B)."""
        logger.info(f"👁️ Session monitor started (idle threshold: {DOPE_MEMORY_IDLE_MINUTES}min)")
        
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Check each active session for idle
                for session_key in self.session_tracker.get_active_sessions():
                    workspace_id, instance_id, session_id = session_key
                    
                    # Signal B: Idle detection
                    if self.session_tracker.is_idle(workspace_id, instance_id, session_id):
                        if self.session_tracker.should_generate_reflection(workspace_id, instance_id, session_id):
                            await self._handle_idle_end(workspace_id, instance_id, session_id)
                    
            except asyncio.CancelledError:
                logger.info("👁️ Session monitor cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Session monitor error: {e}")
                await asyncio.sleep(60)

    async def _emit_pulse(
        self, workspace_id: str, instance_id: str, session_id: str
    ) -> None:
        """Emit memory.pulse for a session."""
        try:
            store = self._get_store(workspace_id)
            
            # Get trajectory state
            trajectory_state = store.get_trajectory_state(workspace_id, instance_id)
            if not trajectory_state:
                return  # No activity yet
            
            # Get recent reflections for constraints
            reflections = store.get_reflection_cards(workspace_id, instance_id, limit=1)
            
            constraints = []
            suggested_next = []
            
            if reflections:
                latest = reflections[0]
                constraints = latest["top_decisions"] + latest["top_blockers"]
                suggested_next = latest["next_suggested"]
            
            trajectory = trajectory_state.get("current_stream", "idle")
            
            # Emit pulse event
            await self._publish_derived_event(
                event_type="memory.pulse",
                data={
                    "trajectory": trajectory,
                    "constraints": constraints[:5],  # Top 5
                    "suggested_next": suggested_next,
                    "source_entry_ids": [],
                },
                workspace_id=workspace_id,
                instance_id=instance_id,
            )
            
            self.session_tracker.mark_pulse(workspace_id, instance_id, session_id)
            logger.debug(f"🫀 Emitted memory.pulse for {workspace_id}/{instance_id}")
            
        except Exception as e:
            logger.warning(f"⚠️  Pulse emission failed: {e}")

    async def _handle_session_end(
        self, workspace_id: str, instance_id: str, session_id: Optional[str]
    ) -> None:
        """Handle explicit session end (Signal A): generate reflection + force pulse."""
        try:
            await self._generate_reflection_boundary(workspace_id, instance_id, session_id)
            await self._emit_pulse(workspace_id, instance_id, session_id or "")
            logger.info(f"✨ Handled explicit session end for {workspace_id}/{instance_id}")
        except Exception as e:
            logger.error(f"❌ Session end handler failed: {e}")

    async def _handle_idle_end(
        self, workspace_id: str, instance_id: str, session_id: str
    ) -> None:
        """Handle idle session end (Signal B): generate reflection + mark ended."""
        try:
            await self._generate_reflection_boundary(workspace_id, instance_id, session_id)
            self.session_tracker.mark_ended(workspace_id, instance_id, session_id)
            logger.info(f"😴 Handled idle session end for {workspace_id}/{instance_id}")
        except Exception as e:
            logger.error(f"❌ Idle end handler failed: {e}")

    async def _generate_reflection_boundary(
        self, workspace_id: str, instance_id: str, session_id: Optional[str]
    ) -> None:
        """Generate reflection card (idempotent)."""
        try:
            store = self._get_store(workspace_id)
            
            # Generate reflection card
            gen = ReflectionGenerator(store)
            card = gen.generate_reflection(
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id,
            )
            
            if card["reflection_id"]:
                # Check idempotency: hash-based key
                # For now, simple check: don't generate if one exists in last 5 minutes
                existing = store.get_reflection_cards(workspace_id, instance_id, session_id=session_id, limit=1)
                if existing:
                    last_ts = datetime.fromisoformat(existing[0]["ts_utc"])
                    now = datetime.now(timezone.utc)
                    if (now - last_ts).total_seconds() < 300:  # 5 minutes
                        logger.debug(f"⏭️  Skipping duplicate reflection (too recent)")
                        return
                
                # Persist reflection
                store.insert_reflection_card(card)
                
                # Emit reflection.created event
                await self._publish_derived_event(
                    event_type="reflection.created",
                    data={
                        "reflection_id": card["reflection_id"],
                        "window_start": card["window_start"],
                        "window_end": card["window_end"],
                        "trajectory": card["trajectory_summary"],
                    },
                    workspace_id=workspace_id,
                    instance_id=instance_id,
                )
                
                # Mark in tracker
                self.session_tracker.mark_reflection(workspace_id, instance_id, session_id or "")
                
                logger.info(f"✨ Generated reflection card: {card['reflection_id']}")
            
        except Exception as e:
            logger.error(f"❌ Reflection generation failed: {e}")

    # ═════════════════════════════════════════════════════════════════
    # Phase 2: Trajectory Management
    # ═════════════════════════════════════════════════════════════════

    def _get_trajectory_manager(self, workspace_id: str) -> TrajectoryManager:
        """Get or create TrajectoryManager for workspace."""
        if workspace_id not in self._trajectory_managers:
            store = self._get_store(workspace_id)
            self._trajectory_managers[workspace_id] = TrajectoryManager(store)
        return self._trajectory_managers[workspace_id]

    async def _update_trajectory(
        self, workspace_id: str, instance_id: str, entry: dict[str, Any]
    ) -> None:
        """Update trajectory state with new entry."""
        try:
            mgr = self._get_trajectory_manager(workspace_id)
            mgr.update_trajectory(workspace_id, instance_id, entry)
        except Exception as e:
            logger.warning(f"⚠️  Failed to update trajectory: {e}")

    # ═════════════════════════════════════════════════════════════════
    # Phase 2: DopeContext Indexing (Best-Effort)
    # ═════════════════════════════════════════════════════════════════

    async def _index_in_dopecontext(
        self,
        entry_id: str,
        workspace_id: str,
        category: str,
        summary: str,
        details: Optional[dict[str, Any]],
    ) -> None:
        """Index work log entry in DopeContext (non-blocking, best-effort)."""
        if not ENABLE_DOPECONTEXT_INDEX:
            return
        
        try:
            import aiohttp
            
            payload = {
                "collection": "worklog_index",
                "document": {
                    "id": entry_id,
                    "workspace_id": workspace_id,
                    "category": category,
                    "summary": summary,
                    "details": details or {},
                    "indexed_at": datetime.now(timezone.utc).isoformat(),
                },
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{DOPECONTEXT_URL}/index",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status == 200:
                        logger.debug(f"✅ Indexed {entry_id} in DopeContext")
                    else:
                        logger.warning(f"⚠️  DopeContext indexing failed: {resp.status}")
        except Exception as e:
            # Best-effort: log and continue
            logger.debug(f"⚠️  DopeContext indexing error (non-blocking): {e}")


async def run_consumer() -> None:
    """Run the EventBus consumer (entry point)."""
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    consumer = EventBusConsumer()
    await consumer.initialize()
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(run_consumer())
