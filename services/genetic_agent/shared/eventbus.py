"""Simple EventBus for inter-module communication."""

from typing import Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Event data class."""
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    source: str = "unknown"

class EventType(Enum):
    """Event types."""
    REPAIR_STARTED = "repair_started"
    REPAIR_COMPLETED = "repair_completed"
    ERROR = "error"
    STATUS_UPDATE = "status_update"

class SimpleEventBus:
    """Simple event bus implementation."""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event type."""
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event type."""
        with self.lock:
            if event_type in self.subscribers:
                self.subscribers[event_type] = [
                    cb for cb in self.subscribers[event_type] if cb != callback
                ]

    def publish(self, event: Event):
        """Publish event to subscribers."""
        with self.lock:
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")

    def get_subscribers_count(self) -> Dict[str, int]:
        """Get subscriber counts per event type."""
        with self.lock:
            return {k: len(v) for k, v in self.subscribers.items()}

# Global event bus instance
event_bus = SimpleEventBus()
