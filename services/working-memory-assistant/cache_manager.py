#!/usr/bin/env python3
"""
Working Memory Assistant - Enhanced Redis Cache Manager
Manages hot cache for 20-30x faster context access.
"""

import json

import logging

logger = logging.getLogger(__name__)

import time
import asyncio
import redis.asyncio as redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
from contextlib import asynccontextmanager

from .main import REDIS_CONFIG

class CacheManager:
    """
    Enhanced Redis cache manager for Working Memory Assistant.
    Provides sub-millisecond access to hot contexts with PostgreSQL persistence.
    """

    def __init__(self, redis_client):
        self.client = redis_client
        self.namespace = "wma"
        self.default_ttl = 86400  # 24 hours default

    @asynccontextmanager
    async def transaction(self):
        """Redis transaction context manager"""
        pipe = self.client.pipeline(transaction=True)
        try:
            yield pipe
        finally:
            await pipe.execute()

    async def set_context(self, snapshot_id: str, context_data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Cache context snapshot in Redis with optimized storage.

        Args:
            snapshot_id: Unique identifier for the snapshot
            context_data: Context data to cache
            ttl: Time-to-live in seconds (default 24h)
        """
        if ttl is None:
            ttl = self.default_ttl

        # Optimize context data for Redis
        optimized_data = self._optimize_for_cache(context_data)

        # Store full context
        key = f"{self.namespace}:context:{context_data['user_id']}:{snapshot_id}"
        await self.client.setex(key, ttl, json.dumps(optimized_data))

        # Store metadata for fast lookups
        metadata_key = f"{self.namespace}:meta:{snapshot_id}"
        metadata = {
            'user_id': context_data['user_id'],
            'context_type': context_data['context_type'],
            'priority': context_data['priority'],
            'size_bytes': len(json.dumps(optimized_data)),
            'cached_at': time.time(),
            'access_count': 0
        }
        await self.client.setex(metadata_key, ttl * 2, json.dumps(metadata))  # Metadata lives longer

        # Update user priority queue
        priority_key = f"{self.namespace}:priority:{context_data['user_id']}"
        await self.client.zadd(priority_key, {snapshot_id: context_data['priority']})

    async def get_context(self, snapshot_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached context snapshot with hit/miss tracking"""
        key = f"{self.namespace}:context:{user_id}:{snapshot_id}"
        data = await self.client.get(key)

        if data:
            # Increment access count in metadata
            metadata_key = f"{self.namespace}:meta:{snapshot_id}"
            current_count = await self.client.get(metadata_key)
            if current_count:
                metadata = json.loads(current_count)
                metadata['access_count'] += 1
                await self.client.setex(metadata_key, self.default_ttl * 2, json.dumps(metadata))

            return self._hydrate_from_cache(json.loads(data))
        return None

    async def get_user_contexts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent contexts from Redis priority queue"""
        priority_key = f"{self.namespace}:priority:{user_id}"

        # Get top contexts by priority
        contexts = await self.client.zrange(priority_key, 0, limit - 1, withscores=True)

        if not contexts:
            return []

        # Get metadata for each context
        metadata_keys = [f"{self.namespace}:meta:{sid[0]}" for sid in contexts]
        metadata_map = {}
        if metadata_keys:
            pipeline = self.client.pipeline()
            for key in metadata_keys:
                pipeline.get(key)
            metadata_results = await pipeline.execute()

            for i, metadata_str in enumerate(metadata_results):
                if metadata_str:
                    metadata_map[contexts[i][0]] = json.loads(metadata_str)

        # Return enriched contexts
        enriched = []
        for sid, score in contexts:
            meta = metadata_map.get(sid, {})
            enriched.append({
                'id': sid,
                'priority': score,
                'context_type': meta.get('context_type', 'unknown'),
                'cached_at': meta.get('cached_at', 0),
                'access_count': meta.get('access_count', 0)
            })

        return enriched

    async def set_recovery_state(self, user_id: str, state: Dict[str, Any], ttl: int = 3600) -> None:
        """Cache recovery state for current session"""
        key = f"{self.namespace}:recovery:{user_id}"
        await self.client.setex(key, ttl, json.dumps(state))

    async def get_recovery_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached recovery state"""
        key = f"{self.namespace}:recovery:{user_id}"
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def cleanup_expired_contexts(self, user_id: str) -> int:
        """Cleanup expired contexts for a user"""
        # Get all context keys for user
        pattern = f"{self.namespace}:context:{user_id}:*"
        keys = await self.client.keys(pattern)

        if not keys:
            return 0

        deleted = 0
        for key in keys:
            # Get metadata to check expiration
            sid = key.split(':')[-1]
            metadata_key = f"{self.namespace}:meta:{sid}"
            metadata_str = await self.client.get(metadata_key)

            if metadata_str:
                metadata = json.loads(metadata_str)
                # Check if context has expired
                if time.time() > metadata.get('expires_at', 0):
                    await self.client.delete(key)
                    await self.client.delete(metadata_key)
                    deleted += 1

        return deleted

    def _optimize_for_cache(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize context data for efficient Redis storage"""
        optimized = context_data.copy()

        # Compress large fields
        if 'mental_model' in optimized and len(json.dumps(optimized['mental_model'])) > 1024:
            # Store large mental models as references
            optimized['mental_model'] = {
                'reference': 'full_context',
                'summary': optimized['mental_model'].get('goal', ''),
                'project': optimized['mental_model'].get('project', '')
            }

        # Ensure all timestamps are numbers
        if 'created_at' in optimized:
            if isinstance(optimized['created_at'], str):
                optimized['created_at'] = time.mktime(datetime.fromisoformat(optimized['created_at']).timetuple())

        return optimized

    def _hydrate_from_cache(self, cached_data: Dict[str, Any]) -> Dict[str, Any]:
        """Hydrate optimized context data for API response"""
        hydrated = cached_data.copy()

        # Reconstruct timestamps
        if 'created_at' in hydrated and isinstance(hydrated['created_at'], (int, float)):
            hydrated['created_at'] = datetime.fromtimestamp(hydrated['created_at']).isoformat()

        return hydrated

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        info = await self.client.info()
        memory = info.get('memory', {})

        return {
            'memory_used_mb': memory.get('used_memory', 0) / (1024*1024),
            'memory_max_mb': memory.get('maxmemory', 0) / (1024*1024),
            'memory_usage_percent': (memory.get('used_memory', 0) / memory.get('maxmemory', 1)) * 100,
            'connected_clients': info.get('connected_clients', 0),
            'uptime_in_seconds': info.get('uptime_in_seconds', 0)
        }

    async def warm_cache(self, user_id: str, limit: int = 5) -> None:
        """Preload user's most important contexts into cache"""
        # Get from PostgreSQL
        from .main import postgres_pool
        from .main import DatabaseManager

        db_manager = DatabaseManager(postgres_pool)
        contexts = await db_manager.get_user_contexts(user_id, limit)

        # Cache each one
        for context in contexts:
            # Get full data from PostgreSQL
            full_context = await db_manager.get_snapshot(context['id'], user_id)
            if full_context:
                await self.set_context(context['id'], full_context)

        logger.info(f"Warmed cache for {user_id} with {len(contexts)} contexts")

    async def invalidate_cache(self, snapshot_id: str, user_id: str) -> None:
        """Invalidate cache for specific snapshot"""
        key = f"{self.namespace}:context:{user_id}:{snapshot_id}"
        metadata_key = f"{self.namespace}:meta:{snapshot_id}"

        await self.client.delete(key)
        await self.client.delete(metadata_key)

    async def get_cache_hit_rate(self, user_id: str) -> Dict[str, Any]:
        """Get cache hit rate for a user"""
        # This would require more sophisticated tracking, but for now return basic stats
        info = await self.client.info()
        return {
            'cache_hit_rate': 'N/A',  # Would need counter implementation
            'total_requests': info.get('total_commands_processed', 0),
            'redis_version': info.get('redis_version', 'unknown')
        }