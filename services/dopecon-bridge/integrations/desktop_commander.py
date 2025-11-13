"""
Desktop Commander Integration for ConPort-KG Event System

Hooks into Desktop Commander workspace detection to emit events when:
- Workspace switch occurs (for context capture and recovery)
- Unintentional context loss detected

Events emitted:
- workspace.switched: Workspace change detected
- context.lost: Unintentional workspace switch (potential interruption)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class DesktopCommanderEventEmitter:
    """
    Event emitter for Desktop Commander workspace monitoring.

    Emits events to DopeconBridge for workspace switch tracking
    and context preservation for ADHD recovery.

    Features:
    - Immediate workspace switch events (context capture critical)
    - Unintentional switch detection
    - Switch frequency tracking
    - ADHD-optimized: Enables fast context recovery
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        enable_events: bool = True,
        track_switch_frequency: bool = True
    ):
        """
        Initialize Desktop Commander event emitter.

        Args:
            event_bus: EventBus instance for publishing
            workspace_id: Workspace ID for event context
            enable_events: Enable event emission (default: True)
            track_switch_frequency: Track switch frequency for pattern detection (default: True)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_events = enable_events
        self.track_switch_frequency = track_switch_frequency

        # Metrics
        self.events_emitted = 0
        self.switch_events = 0
        self.context_lost_events = 0
        self.emission_errors = 0

        # Switch frequency tracking (last 10 switches)
        self.recent_switches: List[Dict[str, Any]] = []

    async def emit_workspace_switched(
        self,
        from_workspace: str,
        to_workspace: str,
        switch_type: str = "manual",
        context_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit event when workspace switch occurs.

        Args:
            from_workspace: Previous workspace path
            to_workspace: New workspace path
            switch_type: Type of switch (manual/automatic/forced)
            context_data: Optional context to preserve (files, cursor positions, etc.)

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="workspace.switched",
                data={
                    "from_workspace": from_workspace,
                    "to_workspace": to_workspace,
                    "switch_type": switch_type,
                    "context_data": context_data or {},
                    "workspace_id": self.workspace_id,
                    "adhd_context_capture": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "recovery_priority": "high" if switch_type == "forced" else "medium"
                    }
                },
                source="desktop-commander"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.switch_events += 1

                # Track switch for frequency analysis
                if self.track_switch_frequency:
                    self.recent_switches.append({
                        "from": from_workspace,
                        "to": to_workspace,
                        "timestamp": datetime.utcnow().isoformat(),
                        "type": switch_type
                    })

                    # Keep only last 10 switches
                    if len(self.recent_switches) > 10:
                        self.recent_switches.pop(0)

                logger.info(
                    f"📤 Emitted workspace.switched: "
                    f"{from_workspace.split('/')[-1]} → {to_workspace.split('/')[-1]} "
                    f"({switch_type})"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit workspace switch event: {e}")

        return False

    async def emit_context_lost(
        self,
        workspace: str,
        reason: str,
        recovery_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit event when unintentional context loss detected.

        Args:
            workspace: Workspace where context was lost
            reason: Reason for context loss
            recovery_data: Optional data to aid recovery

        Returns:
            True if event emitted successfully
        """
        if not self.enable_events:
            return False

        try:
            event = Event(
                type="context.lost",
                data={
                    "workspace": workspace,
                    "reason": reason,
                    "recovery_data": recovery_data or {},
                    "workspace_id": self.workspace_id,
                    "severity": "high",
                    "adhd_impact": "Context recovery needed (15-25 min typical)",
                    "recommended_actions": [
                        "Review recent context before switch",
                        "Use ConPort to retrieve last working state",
                        "Check git status for uncommitted work",
                        "Review open files and recent edits"
                    ]
                },
                source="desktop-commander"
            )

            msg_id = await self.event_bus.publish("dopemux:events", event)

            if msg_id:
                self.events_emitted += 1
                self.context_lost_events += 1
                logger.warning(
                    f"⚠️  Emitted context.lost: {workspace} (reason: {reason})"
                )
                return True

        except Exception as e:
            self.emission_errors += 1
            logger.error(f"Failed to emit context lost event: {e}")

        return False

    def get_switch_frequency(self, time_window_minutes: int = 60) -> float:
        """
        Calculate workspace switch frequency.

        Args:
            time_window_minutes: Time window for calculation (default: 60 min)

        Returns:
            Switches per hour
        """
        if not self.recent_switches:
            return 0.0

        # Filter switches within time window
        cutoff = datetime.utcnow() - timedelta(minutes=time_window_minutes)

        recent = [
            s for s in self.recent_switches
            if datetime.fromisoformat(s["timestamp"].replace('Z', '+00:00')).replace(tzinfo=None) >= cutoff
        ]

        if not recent:
            return 0.0

        # Calculate switches per hour
        if len(recent) >= 2:
            first_time = datetime.fromisoformat(recent[0]["timestamp"].replace('Z', '+00:00')).replace(tzinfo=None)
            last_time = datetime.fromisoformat(recent[-1]["timestamp"].replace('Z', '+00:00')).replace(tzinfo=None)
            duration_hours = (last_time - first_time).total_seconds() / 3600

            if duration_hours > 0:
                return len(recent) / duration_hours

        return 0.0

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get event emission metrics.

        Returns:
            Dictionary with emission stats
        """
        return {
            "agent": "desktop-commander",
            "events_emitted": self.events_emitted,
            "switch_events": self.switch_events,
            "context_lost_events": self.context_lost_events,
            "emission_errors": self.emission_errors,
            "events_enabled": self.enable_events,
            "recent_switches_count": len(self.recent_switches),
            "switches_per_hour": round(self.get_switch_frequency(), 2)
        }

    def reset_metrics(self):
        """Reset emission metrics"""
        self.events_emitted = 0
        self.switch_events = 0
        self.context_lost_events = 0
        self.emission_errors = 0
        self.recent_switches.clear()


class DesktopCommanderIntegrationManager:
    """
    Manages Desktop Commander integration with ConPort-KG event system.

    Provides:
    - Event emitter initialization
    - Workspace switch detection and tracking
    - Context loss detection
    - Switch frequency monitoring
    - Metrics aggregation
    """

    def __init__(
        self,
        event_bus: EventBus,
        workspace_id: str,
        enable_switch_events: bool = True,
        enable_context_loss_events: bool = True,
        excessive_switch_threshold: int = 10  # switches per hour
    ):
        """
        Initialize Desktop Commander integration manager.

        Args:
            event_bus: EventBus instance
            workspace_id: Workspace ID
            enable_switch_events: Enable workspace switch events (default: True)
            enable_context_loss_events: Enable context loss events (default: True)
            excessive_switch_threshold: Threshold for excessive switching (default: 10/hour)
        """
        self.event_bus = event_bus
        self.workspace_id = workspace_id
        self.enable_switch_events = enable_switch_events
        self.enable_context_loss_events = enable_context_loss_events
        self.excessive_switch_threshold = excessive_switch_threshold

        # Create event emitter
        self.emitter = DesktopCommanderEventEmitter(
            event_bus=event_bus,
            workspace_id=workspace_id,
            enable_events=True,
            track_switch_frequency=True
        )

        logger.info(
            f"✅ Desktop Commander integration initialized "
            f"(switch events: {enable_switch_events}, "
            f"threshold: {excessive_switch_threshold}/hour)"
        )

    async def handle_workspace_switch(
        self,
        from_workspace: str,
        to_workspace: str,
        switch_type: str = "manual",
        context_data: Optional[Dict[str, Any]] = None
    ):
        """
        Handle workspace switch from Desktop Commander.

        Args:
            from_workspace: Previous workspace
            to_workspace: New workspace
            switch_type: manual/automatic/forced
            context_data: Context to preserve
        """
        if not self.enable_switch_events:
            return

        # Emit workspace switch event
        await self.emitter.emit_workspace_switched(
            from_workspace=from_workspace,
            to_workspace=to_workspace,
            switch_type=switch_type,
            context_data=context_data
        )

        # Check if switching is excessive
        frequency = self.emitter.get_switch_frequency()

        if frequency >= self.excessive_switch_threshold:
            logger.warning(
                f"⚠️  Excessive workspace switching detected: "
                f"{frequency:.1f} switches/hour (threshold: {self.excessive_switch_threshold})"
            )
            # ContextSwitchFrequencyPattern will detect and create insight

    async def handle_context_loss(
        self,
        workspace: str,
        reason: str,
        recovery_data: Optional[Dict[str, Any]] = None
    ):
        """
        Handle context loss detection from Desktop Commander.

        Args:
            workspace: Workspace where context was lost
            reason: Reason for loss
            recovery_data: Data to aid recovery
        """
        if not self.enable_context_loss_events:
            return

        await self.emitter.emit_context_lost(
            workspace=workspace,
            reason=reason,
            recovery_data=recovery_data
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics"""
        metrics = self.emitter.get_metrics()
        metrics["excessive_switch_threshold"] = self.excessive_switch_threshold
        return metrics
