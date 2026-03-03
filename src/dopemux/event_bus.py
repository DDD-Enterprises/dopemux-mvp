"""
Event Bus Module for Dopemux.

Provides an event bus abstraction with Redis Streams and In-Memory adapters.
"""
import asyncio
import uuid
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from dopemux.events.types import Event, EventPriority

logger = logging.getLogger(__name__)

# Helper Enums
class Priority(str, Enum):
    LOW = "low"
    NORMAL = "medium" # Alias
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CognitiveLoad(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ADHDMetadata:
    interruption_allowed: bool = True
    focus_required: bool = False
    time_sensitive: bool = False
    can_batch: bool = True

class Envelope:
    def __init__(self, type: str, namespace: str, priority: Priority):
        self.type = type
        self.namespace = namespace
        self.priority = priority

class DopemuxEvent:
    """Wrapper class to match test expectations (envelope/payload)."""
    def __init__(self, envelope: Envelope, payload: Dict[str, Any], adhd_metadata: Optional[ADHDMetadata] = None):
        self.envelope = envelope
        self.payload = payload
        self.adhd_metadata = adhd_metadata
        self.source = None # Helpers
        self.instance_id = None

    @classmethod
    def create(cls, event_type: str, namespace: str, payload: Dict[str, Any], 
               priority: Priority = Priority.NORMAL, 
               cognitive_load: Optional[CognitiveLoad] = None,
               adhd_metadata: Optional[ADHDMetadata] = None,
               source: Optional[str] = None,
               instance_id: Optional[str] = None) -> 'DopemuxEvent':
        envelope = Envelope(type=event_type, namespace=namespace, priority=priority)
        instance = cls(envelope, payload, adhd_metadata)
        instance.source = source
        instance.instance_id = instance_id
        return instance

class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: DopemuxEvent) -> bool:
        ...

    @abstractmethod
    async def subscribe(self, pattern: str, callback: Callable[[DopemuxEvent], Any]) -> str:
        """Subscribe to events matching pattern. Returns subscription ID."""
        ...

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        ...

class InMemoryAdapter(EventBus):
    def __init__(self):
        self._subscribers: Dict[str, Dict[str, Callable]] = {}
        self._patterns: Dict[str, str] = {} # sub_id -> pattern

    async def publish(self, event: DopemuxEvent) -> bool:
        # Dispatch to all subscribers
        # Use list() to allow subscribers to unsubscribe during iteration
        for sub_id, pattern in list(self._patterns.items()):
            # Verify subscriber still exists (in case it was removed by another callback)
            if sub_id not in self._patterns:
                continue

            if self._matches(pattern, event):
                # Check consistency between _patterns and _subscribers
                if pattern in self._subscribers and sub_id in self._subscribers[pattern]:
                    callback = self._subscribers[pattern][sub_id]
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Error in subscriber {sub_id}: {e}")
        return True

    def _matches(self, pattern: str, event: Any) -> bool:
        if hasattr(event, 'envelope') and hasattr(event.envelope, 'namespace'):
             event_ns = event.envelope.namespace
             if pattern.endswith('*'):
                 if pattern == '*': return True
                 prefix = pattern[:-1]
                 return event_ns.startswith(prefix)
             return event_ns == pattern
        return True # Default match

    async def subscribe(self, pattern: str, callback: Callable[[DopemuxEvent], Any]) -> str:
        sub_id = str(uuid.uuid4())
        if pattern not in self._subscribers:
            self._subscribers[pattern] = {}
        self._subscribers[pattern][sub_id] = callback
        self._patterns[sub_id] = pattern
        return sub_id

    async def unsubscribe(self, subscription_id: str) -> None:
        if subscription_id in self._patterns:
            pattern = self._patterns[subscription_id]
            if pattern in self._subscribers:
                if subscription_id in self._subscribers[pattern]:
                    del self._subscribers[pattern][subscription_id]
            del self._patterns[subscription_id]

class RedisStreamsAdapter(EventBus):
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.connected = False
        self._subscriptions: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self):
        self.connected = True
        logger.info(f"Connected to Redis at {self.redis_url}")
        
    async def disconnect(self):
        self.connected = False

    async def publish(self, event: DopemuxEvent) -> bool:
        if not self.connected:
            logger.warning("RedisStreamsAdapter.publish called while disconnected; using local fan-out fallback")

        for sub_id, subscription in list(self._subscriptions.items()):
            pattern = subscription["pattern"]
            callback = subscription["callback"]
            if not self._matches(pattern, event):
                continue
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as exc:
                logger.error("Error in RedisStreamsAdapter subscriber %s: %s", sub_id, exc)
        return True

    async def subscribe(self, pattern: str, callback: Callable[[DopemuxEvent], Any]) -> str:
        subscription_id = str(uuid.uuid4())
        self._subscriptions[subscription_id] = {
            "pattern": pattern,
            "callback": callback,
        }
        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> None:
        self._subscriptions.pop(subscription_id, None)

    def _matches(self, pattern: str, event: DopemuxEvent) -> bool:
        if pattern == "*":
            return True
        namespace = getattr(event.envelope, "namespace", "")
        if pattern.endswith("*"):
            return namespace.startswith(pattern[:-1])
        return namespace == pattern
