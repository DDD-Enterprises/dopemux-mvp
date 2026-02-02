"""
ADHD Engine Event Emitter - Publish events to EventBus from API routes.

Phase 7: Full I/O Wiring

This module provides a simple interface for routes to emit events to the
EventBus (Redis Streams) without needing direct access to the EventBus instance.

Events emitted here are consumed by the ADHDEventListener for implicit triggering.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis.asyncio not available - event emission will be logged only")


@dataclass
class Event:
    """Structured event for EventBus publishing."""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    source: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_redis_dict(self) -> Dict[str, str]:
        """Convert to Redis Stream message format."""
        return {
            "event_type": self.type,
            "timestamp": self.timestamp or datetime.utcnow().isoformat(),
            "source": self.source or "adhd_engine",
            "data": json.dumps(self.data)
        }


class ADHDEventEmitter:
    """
    Singleton event emitter for ADHD Engine routes.
    
    Publishes events to Redis Streams for consumption by ADHDEventListener
    and other subscribers.
    """
    
    _instance: Optional['ADHDEventEmitter'] = None
    _lock = asyncio.Lock()
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize event emitter.
        
        Args:
            redis_url: Redis connection URL (default from env)
        """
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL", 
            "redis://localhost:6379/0"
        )
        self.stream_name = "dopemux:events"
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    @classmethod
    async def get_instance(cls) -> 'ADHDEventEmitter':
        """Get or create singleton instance."""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                await cls._instance.connect()
            return cls._instance
    
    async def connect(self):
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            logger.info("Redis not available - events will be logged only")
            return
        
        try:
            self._redis = redis.from_url(self.redis_url)
            await self._redis.ping()
            self._connected = True
            logger.info(f"✅ ADHD Event Emitter connected to Redis")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e} - events will be logged only")
            self._connected = False
    
    async def emit(
        self,
        event_type: str,
        data: Dict[str, Any],
        source: str = "adhd_engine_api"
    ) -> bool:
        """
        Emit an event to the EventBus.
        
        Args:
            event_type: Type of event (e.g., "claude_prompt_received")
            data: Event payload
            source: Source identifier
            
        Returns:
            True if event was published successfully
        """
        event = Event(
            type=event_type,
            data=data,
            source=source
        )
        
        # Always log the event
        logger.debug(f"📤 Emitting event: {event_type} from {source}")
        
        if not self._connected or not self._redis:
            logger.debug(f"Event logged (Redis unavailable): {event_type}")
            return False
        
        try:
            # Publish to Redis Stream
            await self._redis.xadd(
                self.stream_name,
                event.to_redis_dict(),
                maxlen=10000  # Keep reasonable stream length
            )
            logger.debug(f"✅ Event published: {event_type}")
            return True
            
        except Exception as e:
            logger.warning(f"Event publication failed: {e}")
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._connected = False

    async def subscribe(
        self,
        stream: str,
        consumer_group: str,
        consumer_name: str,
        count: int = 10,
        block: int = 2000
    ) -> AsyncGenerator[Tuple[str, Event], None]:
        """
        Subscribe to events from Redis Stream.
        
        Args:
            stream: Stream name
            consumer_group: Consumer group name
            consumer_name: Consumer name
            count: Max messages per batch
            block: Block time in ms
            
        Yields:
            (message_id, Event)
        """
        if not self._connected or not self._redis:
            await self.connect()
            
        if not self._connected:
            logger.warning("Allocating disconnected iterator due to Redis failure")
            return
            
        # Ensure consumer group exists
        try:
            await self._redis.xgroup_create(stream, consumer_group, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                logger.warning(f"Error creating consumer group: {e}")
                
        while True:
            try:
                # Read new messages using consumer group
                # > means read only new messages
                streams = {stream: ">"}
                messages = await self._redis.xreadgroup(
                    consumer_group, 
                    consumer_name, 
                    streams, 
                    count=count, 
                    block=block
                )
                
                if not messages:
                    # No new messages, yield to event loop then continue
                    # Since this is an async generatator, we don't yield None unless caller expects it
                    # But if we don't yield, we must ensure we don't busy loop if block=0
                    # With block=2000, redis blocks for 2s.
                    continue
                
                for stream_name, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        try:
                            # Reconstruct event
                            data_str = msg_data.get(b"data", b"{}").decode("utf-8")
                            
                            event = Event(
                                type=msg_data.get(b"event_type", b"").decode("utf-8"),
                                data=json.loads(data_str),
                                timestamp=msg_data.get(b"timestamp", b"").decode("utf-8"),
                                source=msg_data.get(b"source", b"").decode("utf-8")
                            )
                            
                            yield msg_id.decode("utf-8"), event
                            
                            # Ack message
                            await self._redis.xack(stream, consumer_group, msg_id)
                            
                        except Exception as e:
                            logger.error(f"Error processing message {msg_id}: {e}")
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Subscription loop error: {e}")
                await asyncio.sleep(1)


# Event type constants (matching EventType enum in DopeconBridge)
class EventTypes:
    """Event type constants for consistent naming."""
    
    # Claude Code hook events
    CLAUDE_PROMPT_RECEIVED = "claude_prompt_received"
    CLAUDE_TOOL_STARTED = "claude_tool_started"
    CLAUDE_TOOL_COMPLETED = "claude_tool_completed"
    CLAUDE_SESSION_STOPPED = "claude_session_stopped"
    
    # File activity events
    FILE_OPENED = "file_opened"
    FILE_SAVED = "file_saved"
    FILE_ACTIVITY = "file_activity"
    
    # Progress events
    PROGRESS_LOGGED = "progress_logged"
    TASK_COMPLETED = "task_completed"
    
    # Context events
    CONTEXT_SAVED = "context_saved"
    CONTEXT_SWITCH = "context_switch"


# Convenience functions for common event patterns
async def emit_claude_prompt(
    prompt_summary: str,
    signals: Dict[str, Any],
    adhd_state: Dict[str, Any]
) -> bool:
    """Emit event for Claude Code prompt analysis."""
    emitter = await ADHDEventEmitter.get_instance()
    return await emitter.emit(
        EventTypes.CLAUDE_PROMPT_RECEIVED,
        {
            "prompt_summary": prompt_summary[:100],  # Truncate for privacy
            "signals": signals,
            "adhd_state": adhd_state,
        },
        source="prompt_analyzer_hook"
    )


async def emit_claude_tool(
    tool_name: str,
    success: bool,
    user_id: str = "default"
) -> bool:
    """Emit event for Claude Code tool completion."""
    emitter = await ADHDEventEmitter.get_instance()
    return await emitter.emit(
        EventTypes.CLAUDE_TOOL_COMPLETED,
        {
            "tool": tool_name,
            "success": success,
            "user_id": user_id
        },
        source="log_progress_hook"
    )


async def emit_context_saved(
    user_id: str,
    reason: str,
    prompt_hint: str = ""
) -> bool:
    """Emit event for context save."""
    emitter = await ADHDEventEmitter.get_instance()
    return await emitter.emit(
        EventTypes.CONTEXT_SAVED,
        {
            "user_id": user_id,
            "reason": reason,
            "prompt_hint": prompt_hint[:50]
        },
        source="save_context_hook"
    )
