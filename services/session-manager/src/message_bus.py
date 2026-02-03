"""
Message Bus - Step 4 of Phase 1
Abstract message bus for AI agent communication

Based on Zen validation:
- Abstract interface allows swapping implementations
- Default: TmuxCapture (no external dependencies)
- Future: Redis Pub/Sub (if multi-machine needed)

Complexity: 0.55 (Medium)
Effort: 5 focus blocks (125 minutes)
"""

from abc import ABC, abstractmethod

import logging

logger = logging.getLogger(__name__)

from typing import Iterator, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json


class EventType(Enum):
    """Types of events in the system."""

    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_OUTPUT = "agent.output"
    AGENT_ERROR = "agent.error"
    COMMAND_SENT = "command.sent"
    COMMAND_COMPLETED = "command.completed"
    CHECKPOINT_SAVED = "checkpoint.saved"
    ENERGY_CHANGED = "energy.changed"
    BREAK_REMINDER = "break.reminder"


@dataclass
class Event:
    """Standard event structure."""

    type: EventType
    source: str  # Agent or component that generated event
    timestamp: datetime
    payload: dict
    correlation_id: Optional[str] = None  # Link related events


class MessageBus(ABC):
    """
    Abstract message bus interface.

    Allows swapping implementations without changing code:
    - TmuxCaptureMessageBus (default, no dependencies)
    - RedisPubSubMessageBus (future, if multi-machine)
    """

    @abstractmethod
    def publish(self, event: Event) -> None:
        """
        Publish event to bus.

        Args:
            event: Event to publish
        """
        pass

    @abstractmethod
    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: Type of events to receive
            callback: Function to call when event received
        """
        pass

    @abstractmethod
    def get_recent_events(
        self, event_type: Optional[EventType] = None, limit: int = 10
    ) -> list[Event]:
        """
        Get recent events from bus.

        Args:
            event_type: Filter by type (None = all types)
            limit: Max events to return

        Returns:
            List of recent events
        """
        pass


class InMemoryMessageBus(MessageBus):
    """
    Simple in-memory message bus for MVP.

    Stores events in memory with circular buffer.
    Good for: Single-process, development, testing
    Not good for: Multi-machine, persistence
    """

    def __init__(self, max_events: int = 1000):
        """
        Initialize in-memory bus.

        Args:
            max_events: Max events to keep in memory
        """
        self.events: list[Event] = []
        self.max_events = max_events
        self.subscribers: dict[EventType, list[Callable]] = {}

    def publish(self, event: Event) -> None:
        """Publish event to memory."""
        # Add to event list
        self.events.append(event)

        # Trim if over max
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        # Notify subscribers
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"⚠️ Subscriber error: {e}")

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """Subscribe to event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)

    def get_recent_events(
        self, event_type: Optional[EventType] = None, limit: int = 10
    ) -> list[Event]:
        """Get recent events, optionally filtered by type."""
        if event_type:
            filtered = [e for e in self.events if e.type == event_type]
            return filtered[-limit:]
        else:
            return self.events[-limit:]


class TmuxCaptureMessageBus(MessageBus):
    """
    Message bus using tmux capture-pane for agent output.

    Polls tmux panes periodically to capture AI agent output.
    No external dependencies (just tmux + libtmux).

    Good for: Single-machine, visible monitoring
    Not good for: Multi-machine (no tmux), high-frequency events
    """

    def __init__(self, poll_interval: float = 0.5):
        """
        Initialize tmux capture bus.

        Args:
            poll_interval: Seconds between pane captures
        """
        self.poll_interval = poll_interval
        self.event_buffer: list[Event] = []
        self.subscribers: dict[EventType, list[Callable]] = {}
        self.pane_watchers: dict[str, int] = {}  # pane_id -> last_line_count

    def publish(self, event: Event) -> None:
        """Publish event (stored in buffer)."""
        self.event_buffer.append(event)

        # Notify subscribers
        if event.type in self.subscribers:
            for callback in self.subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"⚠️ Subscriber error: {e}")

    def subscribe(
        self, event_type: EventType, callback: Callable[[Event], None]
    ) -> None:
        """Subscribe to event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)

    def watch_pane(self, pane_id: str, agent_name: str) -> None:
        """
        Start watching a tmux pane for output.

        Args:
            pane_id: Tmux pane ID (e.g., "%0")
            agent_name: Name of agent in this pane
        """
        import subprocess

        try:
            # Get initial line count
            result = subprocess.run(
                ["tmux", "display-message", "-p", "-t", pane_id, "#{pane_height}"],
                capture_output=True,
                text=True,
            )
            self.pane_watchers[pane_id] = 0  # Start at 0

            logger.info(f"👀 Watching pane {pane_id} for {agent_name}")

        except Exception as e:
            logger.error(f"⚠️ Failed to watch pane {pane_id}: {e}")

    def capture_pane_output(self, pane_id: str, agent_name: str) -> list[str]:
        """
        Capture new output from tmux pane.

        Args:
            pane_id: Tmux pane ID
            agent_name: Agent name for event

        Returns:
            New lines since last capture
        """
        import subprocess

        try:
            # Capture full pane content
            result = subprocess.run(
                ["tmux", "capture-pane", "-p", "-t", pane_id],
                capture_output=True,
                text=True,
                check=True,
            )

            all_lines = result.stdout.split("\n")
            last_count = self.pane_watchers.get(pane_id, 0)

            # Get only new lines
            new_lines = all_lines[last_count:]

            # Update tracker
            self.pane_watchers[pane_id] = len(all_lines)

            # Publish output events
            if new_lines:
                for line in new_lines:
                    if line.strip():  # Skip empty lines
                        event = Event(
                            type=EventType.AGENT_OUTPUT,
                            source=agent_name,
                            timestamp=datetime.now(),
                            payload={"output": line},
                        )
                        self.publish(event)

            return new_lines

        except Exception as e:
            logger.error(f"⚠️ Failed to capture pane {pane_id}: {e}")
            return []

    def get_recent_events(
        self, event_type: Optional[EventType] = None, limit: int = 10
    ) -> list[Event]:
        """Get recent events from buffer."""
        if event_type:
            filtered = [e for e in self.event_buffer if e.type == event_type]
            return filtered[-limit:]
        else:
            return self.event_buffer[-limit:]


# Factory for easy creation
def create_message_bus(
    bus_type: str = "in_memory", **kwargs
) -> MessageBus:
    """
    Create message bus instance.

    Args:
        bus_type: "in_memory" or "tmux_capture"
        **kwargs: Additional arguments for bus constructor

    Returns:
        MessageBus instance
    """
    if bus_type == "in_memory":
        return InMemoryMessageBus(**kwargs)
    elif bus_type == "tmux_capture":
        return TmuxCaptureMessageBus(**kwargs)
    else:
        raise ValueError(f"Unknown bus type: {bus_type}")


if __name__ == "__main__":
    """Test message bus."""

    logger.info("Testing InMemoryMessageBus:")
    logger.info("=" * 60)

    bus = create_message_bus("in_memory")

    # Subscribe to agent output
    def on_output(event: Event):
        logger.info(f"📨 Received: {event.source} → {event.payload}")

    bus.subscribe(EventType.AGENT_OUTPUT, on_output)

    # Publish some events
    bus.publish(
        Event(
            type=EventType.AGENT_OUTPUT,
            source="claude",
            timestamp=datetime.now(),
            payload={"output": "Analyzing authentication flow..."},
        )
    )

    bus.publish(
        Event(
            type=EventType.AGENT_OUTPUT,
            source="gemini",
            timestamp=datetime.now(),
            payload={"output": "Found 3 security issues"},
        )
    )

    # Get recent events
    recent = bus.get_recent_events(limit=5)
    logger.info(f"\nRecent events: {len(recent)}")

    logger.info("\n✅ Message bus test complete")
