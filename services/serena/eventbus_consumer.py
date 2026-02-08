"""
EventBus Consumer for Serena
Subscribes to ConPort decision events and caches decisions
"""

import os

import asyncio
import redis.asyncio as redis
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DecisionCache:
    """In-memory cache of recent decisions"""
    
    def __init__(self, max_size: int = 100):
        self.decisions: Dict[int, dict] = {}
        self.max_size = max_size
        self.by_summary: Dict[str, List[int]] = {}  # For search
    
    def add(self, decision: dict):
        """Add decision to cache"""
        decision_id = decision["id"]
        self.decisions[decision_id] = decision
        
        # Index by summary words for search
        words = decision["summary"].lower().split()
        for word in words:
            if word not in self.by_summary:
                self.by_summary[word] = []
            if decision_id not in self.by_summary[word]:
                self.by_summary[word].append(decision_id)
        
        # Evict old decisions if over max_size
        if len(self.decisions) > self.max_size:
            oldest_id = min(self.decisions.keys())
            self._remove_decision(oldest_id)
        
        logger.debug(f"Cached decision {decision_id}: {decision['summary'][:50]}")
    
    def _remove_decision(self, decision_id: int):
        """Remove decision from cache and indices"""
        if decision_id in self.decisions:
            decision = self.decisions[decision_id]
            del self.decisions[decision_id]
            
            # Remove from word index
            words = decision["summary"].lower().split()
            for word in words:
                if word in self.by_summary and decision_id in self.by_summary[word]:
                    self.by_summary[word].remove(decision_id)
    
    def search(self, query: str, limit: int = 3) -> List[dict]:
        """Search decisions by query string"""
        words = query.lower().split()
        decision_ids = set()
        
        for word in words:
            if word in self.by_summary:
                decision_ids.update(self.by_summary[word])
        
        # Get decisions and sort by ID (newest first)
        results = [
            self.decisions[did]
            for did in sorted(decision_ids, reverse=True)
            if did in self.decisions
        ]
        
        return results[:limit]
    
    def get_recent(self, limit: int = 5) -> List[dict]:
        """Get most recent decisions"""
        sorted_ids = sorted(self.decisions.keys(), reverse=True)
        return [self.decisions[did] for did in sorted_ids[:limit]]
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "total_decisions": len(self.decisions),
            "indexed_words": len(self.by_summary),
            "max_size": self.max_size
        }


class EventBusConsumer:
    """
    EventBus consumer for Serena
    Subscribes to decision events and maintains cache
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        stream_name: str = "conport:events",
        consumer_group: str = "serena",
        consumer_name: str = "serena-1"
    ):
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name

        self.redis = None
        self.cache = DecisionCache()
        self.running = False
        self.task = None

    async def connect(self):
        """Connect to Redis and create consumer group"""
        self.redis = await redis.from_url(self.redis_url)
        
        # Create consumer group if doesn't exist
        try:
            await self.redis.xgroup_create(
                self.stream_name,
                self.consumer_group,
                id='0',
                mkstream=True
            )
            logger.info(f"Created consumer group: {self.consumer_group}")
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            logger.info(f"Consumer group exists: {self.consumer_group}")
    
    async def start(self):
        """Start consuming events"""
        await self.connect()
        self.running = True
        
        logger.info(f"Consuming from {self.stream_name} as {self.consumer_name}")
        
        # Load existing events on startup
        await self._load_existing_events()
        
        while self.running:
            try:
                # Read events (block for 1 second)
                messages = await self.redis.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_name: '>'},
                    count=10,
                    block=1000
                )
                
                for stream, events in messages:
                    for event_id, event_data in events:
                        retry_count = 0
                        while retry_count < 3:
                            try:
                                await self._process_event(event_id, event_data)
                                break
                            except Exception as e:
                                retry_count += 1
                                if retry_count < 3:
                                    await asyncio.sleep(2 ** retry_count)
                                else:
                                    logger.error(f"Max retries exceeded for event {event_id}")
                        
            except asyncio.CancelledError:
                logger.info("Consumer cancelled")
                break
            except Exception as e:
                logger.error(f"Error consuming events: {e}")
                await asyncio.sleep(1)
    
    async def _load_existing_events(self):
        """Load existing events from stream on startup"""
        try:
            # Read last 100 events from the stream
            events = await self.redis.xrange(self.stream_name, count=100)
            
            loaded_count = 0
            for event_id, event_data in events:
                # Keys are bytes when decode_responses is False
                event_type = event_data.get(b'type', b'').decode() if isinstance(event_data.get(b'type'), bytes) else event_data.get('type', '')
                
                if event_type == "decision.logged":
                    data_str = event_data.get(b'data', b'{}').decode() if isinstance(event_data.get(b'data'), bytes) else event_data.get('data', '{}')
                    data = json.loads(data_str)
                    self.cache.add(data)
                    loaded_count += 1
            
            if loaded_count > 0:
                logger.info(f"✅ Loaded {loaded_count} decision(s) from stream")
        except Exception as e:
            logger.warning(f"Could not load existing events: {e}")
    
    async def _process_event(self, event_id: bytes, event_data: dict):
        """Process a single event"""
        try:
            event_type = event_data[b'type'].decode()
            
            if event_type == "decision.logged":
                data = json.loads(event_data[b'data'].decode())
                self.cache.add(data)
                logger.info(f"✅ Cached decision #{data['id']}: {data['summary'][:50]}")
            
            # ACK the message
            await self.redis.xack(
                self.stream_name,
                self.consumer_group,
                event_id
            )
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
    
    async def stop(self):
        """Stop consuming"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        if self.redis:
            await self.redis.close()
    
    def search_decisions(self, query: str, limit: int = 3) -> List[dict]:
        """Search cached decisions"""
        return self.cache.search(query, limit)
    
    def get_recent_decisions(self, limit: int = 5) -> List[dict]:
        """Get recent decisions"""
        return self.cache.get_recent(limit)
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        return self.cache.get_stats()


# Global instance (initialized by LSP server)
consumer: Optional[EventBusConsumer] = None


async def init_consumer(redis_url: str = "redis://localhost:6379"):
    """Initialize the global consumer"""
    global consumer
    consumer = EventBusConsumer(redis_url=redis_url)
    consumer.task = asyncio.create_task(consumer.start())
    logger.info("✅ EventBus consumer initialized")
    return consumer


def get_consumer() -> Optional[EventBusConsumer]:
    """Get the global consumer instance"""
    return consumer


# Standalone test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        """Test the consumer"""
        c = await init_consumer()
        
        logger.info("\n⏳ Waiting for events... (Create a decision to test)")
        logger.info("   Press Ctrl+C to stop\n")
        
        try:
            while True:
                await asyncio.sleep(5)
                
                # Show stats
                stats = c.get_cache_stats()
                print(f"📊 Cache: {stats['total_decisions']} decisions, "
                      f"{stats['indexed_words']} indexed words")
                
                # Show recent
                recent = c.get_recent_decisions(3)
                if recent:
                    logger.info("   Recent decisions:")
                    for d in recent:
                        logger.info(f"   - #{d['id']}: {d['summary'][:60]}")
                logger.info()
                
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping...")
            await c.stop()
    
    asyncio.run(test())
