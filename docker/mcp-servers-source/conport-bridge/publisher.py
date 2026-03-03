"""Redis Streams Event Publisher"""
import redis
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publish events to Redis Streams"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.stream_name = "conport:events"
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping()
            logger.info(f"✅ Connected to Redis, stream: {self.stream_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    def publish(self, event: Dict[str, Any]) -> str:
        """
        Publish event to Redis Stream
        
        Returns: Event ID (timestamp-sequence)
        """
        try:
            # Add to stream
            event_id = self.redis.xadd(
                self.stream_name,
                {
                    "type": event["event_type"],
                    "source": event["source"],
                    "timestamp": event["timestamp"],
                    "data": json.dumps(event["data"])
                }
            )
            
            logger.info(f"📤 Published {event['event_type']} -> {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Error publishing event: {e}")
            raise
    
    def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            logger.info("Redis connection closed")


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    pub = EventPublisher()
    
    # Test event
    event = {
        "event_type": "decision.logged",
        "source": "test",
        "timestamp": "2025-10-28T18:41:00Z",
        "data": {
            "id": 1,
            "summary": "Test decision from event bridge"
        }
    }
    
    event_id = pub.publish(event)
    print(f"✅ Published: {event_id}")
    
    pub.close()
