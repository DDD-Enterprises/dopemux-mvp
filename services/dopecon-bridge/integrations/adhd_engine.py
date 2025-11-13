"""
ADHD Engine Integration for ConPort-KG Event System

Hooks into ADHD Engine cognitive monitoring to emit events when:
- Cognitive state changes (buffered, 30s intervals to prevent event storms)
- Cognitive overload detected (immediate, critical)
- Break recommended (based on session duration)

Events emitted:
- cognitive.state.changed: Buffered state updates (30s intervals)
- adhd.overload.detected: Immediate cognitive overload alert
- break.recommended: Break recommendation based on session time
"""

import asyncio
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class ADHDEventBuffer:
    """
    Event buffer for ADHD state changes.

    Prevents event storms by buffering state changes and emitting
    at regular intervals (default: 30 seconds).

    Features:
    - Configurable buffer interval
    - Automatic flushing on interval
    - Manual flush capability
    - Latest state priority (only emit most recent state)
    """

    def __init__(self, flush_interval_seconds: int = 30):
        """
        Initialize ADHD event buffer.

        Args:
            flush_interval_seconds: Seconds between flushes (default: 30)
        """
        self.flush_interval_seconds = flush_interval_seconds
        self.buffered_state: Optional[Dict[str, Any]] = None
        self.last_flush_time = time.time()
        self.buffer_count = 0

    def buffer_state(self, state: Dict[str, Any]):
        """
        Buffer cognitive state update.

        Only keeps latest state (overwrites previous buffered state).

        Args:
            state: Cognitive state dictionary
        """
        self.buffered_state = state
        self.buffer_count += 1

    def should_flush(self) -> bool:
        """
        Check if buffer should be flushed.

        Returns:
            True if flush_interval has elapsed
        """
        elapsed = time.time() - self.last_flush_time
        return elapsed >= self.flush_interval_seconds

    def get_buffered_state(self) -> Optional[Dict[str, Any]]:
        """
        Get buffered state and mark as flushed.

        Returns:
            Buffered state if exists, None otherwise
        """
        if self.buffered_state is None:
            return None

        state = self.buffered_state
        self.buffered_state = None
        self.last_flush_time = time.time()

        return state

    def get_metrics(self) -> Dict[str, Any]:
        """Get buffer metrics"""
        return {
            "flush_interval_seconds": self.flush_interval_seconds,
            "has_buffered_state": self.buffered_state is not None,
            "buffer_count": self.buffer_count,
            "seconds_since_flush": time.time() - self.last_flush_time
        }


class ADHDEngineEventEmitter:
    """
    Event emitter for ADHD Engine cognitive monitoring.

    Features:
    - Buffered state change events (30s intervals)
    - Immediate overload alerts (not buffered)
    - Break recommendations
    - Event storm prevention
    - ADHD-optimized: Minimal overhead
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        buffer_interval_seconds: int = 30,
        overload_threshold: float = 0.8,
        enable_events: bool = True
    ):
        """
        Initialize ADHD Engine event emitter.

        Args:
            event_bus: EventBus instance for publishing
            workspace_id: Workspace ID for event context
            buffer_interval_seconds: Buffering interval for state changes (default: 30)
            overload_threshold: Cognitive load threshold for overload (default: 0.8)
            enable_events: Enable event emission (default: True)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.buffer_interval_seconds = buffer_interval_seconds
        self.overload_threshold = overload_threshold
        self.enable_events = enable_events

        # Event buffer for state changes
        self.buffer = ADHDEventBuffer(flush_interval_seconds=buffer_interval_seconds)

        # Metrics
        self.events_emitted = 0
        self.state_change_events = 0
        self.overload_events = 0
        self.break_events = 0
        self.emission_errors = 0

    async def buffer_state_change(
        self,
        attention_state: str,
        energy_level: str,
        cognitive_load: float
    ):
        """
        Buffer cognitive state change (will be emitted on next flush).

        Args:
            attention_state: Current attention state (focused/scattered/transitioning)
            energy_level: Current energy level (high/medium/low)
            cognitive_load: Current cognitive load (0.0-1.0)
        """
        if not self.enable_events:
            return

        state = {
            "attention_state": attention_state,
            "energy_level": energy_level,
            "cognitive_load": cognitive_load,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.buffer.buffer_state(state)

    async def flush_buffered_state(self) -> bool:
        """
        Flush buffered state if interval elapsed.

        Returns:
            True if state was flushed and event emitted
        """
        if not self.enable_events:
            return False

        if not self.buffer.should_flush():
            return False

        state = self.buffer.get_buffered_state()

        if state is None:
            return False

        try:
            event = Event(
                type="cognitive.state.changed",
                data={
                    **state,
                    "workspace_id": self.workspace_id,
                    "buffer_interval_seconds": self.buffer_interval_seconds
                },
                source="adhd-engine"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.state_change_events += 1
                logger.debug(
                    f"📤 Emitted cognitive.state.changed (buffered): "
                    f"{state['attention_state']}, load: {state['cognitive_load']:.2f}"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit buffered state: {e}")

        return False

    async def emit_overload_detected(
        self,
        cognitive_load: float,
        trigger: str,
        recommended_actions: Optional[List[str]] = None
    ) -> bool:
        """
        Emit immediate event when cognitive overload detected.

        NOT BUFFERED - emitted immediately for critical alerts.

        Args:
            cognitive_load: Current cognitive load (should be >0.8)
            trigger: What triggered the overload
            recommended_actions: Optional specific recommendations

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        # Only emit if actually overloaded
        if cognitive_load < self.overload_threshold:
            return False

        try:
            event = Event(
                type="adhd.overload.detected",
                data={
                    "cognitive_load": cognitive_load,
                    "trigger": trigger,
                    "threshold": self.overload_threshold,
                    "workspace_id": self.workspace_id,
                    "severity": "critical" if cognitive_load >= 0.9 else "high",
                    "recommended_actions": recommended_actions or [
                        "Take immediate break (5-10 minutes)",
                        "Reduce concurrent task complexity",
                        "Enable focus mode (disable notifications)",
                        "Close non-essential applications",
                        "Consider task switching to lower complexity work"
                    ]
                },
                source="adhd-engine"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.overload_events += 1
                logger.warning(
                    f"⚠️  Emitted adhd.overload.detected: "
                    f"load {cognitive_load:.2f} (trigger: {trigger})"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit overload event: {e}")

        return False

    async def emit_break_recommended(
        self,
        session_duration_minutes: int,
        last_break_minutes_ago: int,
        reason: str = "session_duration"
    ) -> bool:
        """
        Emit event when break is recommended.

        Args:
            session_duration_minutes: Current session duration
            last_break_minutes_ago: Minutes since last break
            reason: Reason for break recommendation

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="break.recommended",
                data={
                    "session_duration_minutes": session_duration_minutes,
                    "last_break_minutes_ago": last_break_minutes_ago,
                    "reason": reason,
                    "workspace_id": self.workspace_id,
                    "recommended_break_duration": self._calculate_break_duration(
                        session_duration_minutes
                    ),
                    "reminder": "ADHD productivity improves with regular breaks"
                },
                source="adhd-engine"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.break_events += 1
                logger.info(
                    f"📤 Emitted break.recommended: "
                    f"{session_duration_minutes}min session, "
                    f"{last_break_minutes_ago}min since break"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit break event: {e}")

        return False

    def _calculate_break_duration(self, session_duration: int) -> int:
        """
        Calculate recommended break duration based on session length.

        Args:
            session_duration: Session duration in minutes

        Returns:
            Recommended break duration in minutes
        """
        if session_duration >= 90:
            return 15  # Long session = longer break
        elif session_duration >= 45:
            return 10
        else:
            return 5

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get event emission metrics.

        Returns:
            Dictionary with emission stats
        """
        metrics = {
            "agent": "adhd-engine",
            "events_emitted": self.events_emitted,
            "state_change_events": self.state_change_events,
            "overload_events": self.overload_events,
            "break_events": self.break_events,
            "emission_errors": self.emission_errors,
            "events_enabled": self.enable_events,
            "buffer_interval_seconds": self.buffer_interval_seconds,
            "overload_threshold": self.overload_threshold
        }

        # Add buffer metrics
        metrics["buffer"] = self.buffer.get_metrics()

        return metrics

    def reset_metrics(self):
        """Reset emission metrics"""
        self.events_emitted = 0
        self.state_change_events = 0
        self.overload_events = 0
        self.break_events = 0
        self.emission_errors = 0


class ADHDEngineIntegrationManager:
    """
    Manages ADHD Engine integration with ConPort-KG event system.

    Provides:
    - Event emitter with buffering
    - Background worker for automatic flushing
    - Overload detection and alerting
    - Break recommendation tracking
    - Metrics aggregation
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        buffer_interval_seconds: int = 30,
        enable_state_events: bool = True,
        enable_overload_events: bool = True,
        enable_break_events: bool = True,
        overload_threshold: float = 0.8
    ):
        """
        Initialize ADHD Engine integration manager.

        Args:
            event_bus: EventBus instance
            workspace_id: Workspace ID
            buffer_interval_seconds: Buffering interval for state changes (default: 30)
            enable_state_events: Enable state change events (default: True)
            enable_overload_events: Enable overload events (default: True)
            enable_break_events: Enable break events (default: True)
            overload_threshold: Cognitive load threshold for overload (default: 0.8)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_state_events = enable_state_events
        self.enable_overload_events = enable_overload_events
        self.enable_break_events = enable_break_events

        # Create event emitter
        self.emitter = ADHDEngineEventEmitter(
            event_bus=event_bus,
            workspace_id=workspace_id,
            buffer_interval_seconds=buffer_interval_seconds,
            overload_threshold=overload_threshold,
            enable_events=True
        )

        # Background worker
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False

        logger.info(
            f"✅ ADHD Engine integration initialized "
            f"(buffer: {buffer_interval_seconds}s, overload: {overload_threshold})"
        )

    async def handle_state_update(
        self,
        attention_state: str,
        energy_level: str,
        cognitive_load: float
    ):
        """
        Handle cognitive state update from ADHD Engine.

        State changes are buffered and emitted every 30s to prevent storms.

        Args:
            attention_state: focused/scattered/transitioning
            energy_level: high/medium/low
            cognitive_load: 0.0-1.0
        """
        if not self.enable_state_events:
            return

        # Buffer the state (will be flushed on interval)
        await self.emitter.buffer_state_change(
            attention_state=attention_state,
            energy_level=energy_level,
            cognitive_load=cognitive_load
        )

        # Check for overload (emit immediately, not buffered)
        if self.enable_overload_events and cognitive_load >= self.emitter.overload_threshold:
            await self.emitter.emit_overload_detected(
                cognitive_load=cognitive_load,
                trigger="high_cognitive_load"
            )

    async def handle_break_needed(
        self,
        session_duration_minutes: int,
        last_break_minutes_ago: int,
        reason: str = "session_duration"
    ):
        """
        Handle break recommendation from ADHD Engine.

        Args:
            session_duration_minutes: Current session duration
            last_break_minutes_ago: Time since last break
            reason: Reason for break recommendation
        """
        if not self.enable_break_events:
            return

        await self.emitter.emit_break_recommended(
            session_duration_minutes=session_duration_minutes,
            last_break_minutes_ago=last_break_minutes_ago,
            reason=reason
        )

    async def start_background_worker(self):
        """
        Start background worker to flush buffered states periodically.

        This ensures state changes are emitted even if no new updates arrive.
        """
        self.running = True
        self.worker_task = asyncio.create_task(self._buffer_flush_worker())
        logger.info(f"▶️  Started ADHD Engine buffer flush worker ({self.emitter.buffer_interval_seconds}s interval)")

    async def _buffer_flush_worker(self):
        """Background worker that flushes buffer periodically"""
        while self.running:
            try:
                # Check and flush if interval elapsed
                if self.emitter.buffer.should_flush():
                    await self.emitter.flush_buffered_state()

                # Sleep for 1 second, check again
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Buffer flush worker error: {e}")
                await asyncio.sleep(5)

    async def stop_background_worker(self):
        """Stop background worker"""
        self.running = False

        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        logger.info("⏹️  Stopped ADHD Engine buffer flush worker")

    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics"""
        metrics = self.emitter.get_metrics()
        metrics["background_worker_running"] = self.running
        return metrics
