"""Simple EventBus for inter-module communication."""

from typing import Dict, Any, List, Callable
import inspect
from datetime import datetime
from enum import Enum
import logging
import threading

logger = logging.getLogger(__name__)

class Event:
    """Event container compatible with legacy and current callsites."""

    def __init__(
        self,
        *,
        type: str | None = None,
        event_type: str | None = None,
        payload: Dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        source: str = "unknown",
    ):
        resolved_type = type or event_type
        if not resolved_type:
            raise ValueError("Event requires 'type' or 'event_type'")

        self.type = resolved_type
        self.payload = payload or {}
        self.timestamp = timestamp or datetime.now()
        self.source = source

    @property
    def event_type(self) -> str:
        """Compatibility alias used by legacy event handlers."""
        return self.type

class EventType(Enum):
    """Event types."""
    REPAIR_STARTED = "repair_started"
    REPAIR_COMPLETED = "repair_completed"
    ERROR = "error"
    STATUS_UPDATE = "status_update"

class SimpleEventBus:
    """Simple event bus implementation."""

    def __init__(self, *_args, **_kwargs):
        # Accept ignored constructor args for compatibility with previous API.
        self.subscribers: Dict[str, List[tuple[Callable, Callable | None]]] = {}
        self.lock = threading.Lock()

    async def subscribe(
        self,
        event_type: str,
        callback: Callable,
        filter_fn: Callable | None = None,
    ):
        """Subscribe to event type."""
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append((callback, filter_fn))

    async def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event type."""
        with self.lock:
            if event_type in self.subscribers:
                self.subscribers[event_type] = [
                    (cb, f) for cb, f in self.subscribers[event_type] if cb != callback
                ]

    async def publish(self, event: Event):
        """Publish event to subscribers."""
        event_type = event.event_type
        with self.lock:
            subscribers = list(self.subscribers.get(event_type, []))

        for callback, filter_fn in subscribers:
            try:
                if filter_fn and not filter_fn(event):
                    continue
                result = callback(event)
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                logger.error(f"Error in callback: {e}")

    def get_subscribers_count(self) -> Dict[str, int]:
        """Get subscriber counts per event type."""
        with self.lock:
            return {k: len(v) for k, v in self.subscribers.items()}

# Global event bus instance
event_bus = SimpleEventBus()
