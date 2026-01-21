"""
Cache Manager - Redis caching with ADHD optimizations

This module provides intelligent caching with compression, ADHD-friendly formatting,
and performance monitoring for the Claude Brain service.
"""

import asyncio
import json
import logging
import time
import zlib
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Union
from datetime import datetime, timedelta

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    data: Any
    compressed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    ttl_seconds: Optional[int] = None


@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    compression_savings: int = 0
    avg_response_time: float = 0.0
    memory_usage_mb: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests


class ADHDFormatter:
    """
    ADHD-friendly response formatting.

    Adds visual indicators, progressive disclosure, and cognitive load management.
    """

    @staticmethod
    def format_response(response: str, cognitive_load: float = 0.5) -> str:
        """Format response for ADHD-friendly consumption."""
        formatted = response

        # Add visual indicators
        formatted = ADHDFormatter._add_visual_indicators(formatted)

        # Apply progressive disclosure based on cognitive load
        if cognitive_load > 0.7:  # High cognitive load
            formatted = ADHDFormatter._apply_progressive_disclosure(formatted)
        elif cognitive_load < 0.3:  # Low cognitive load
            formatted = ADHDFormatter._add_detailed_guidance(formatted)

        # Add cognitive load warnings
        formatted = ADHDFormatter._add_cognitive_warnings(formatted, cognitive_load)

        return formatted

    @staticmethod
    def _add_visual_indicators(text: str) -> str:
        """Add visual indicators for better scanning."""
        lines = text.split('\n')
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append(line)
                continue

            # Add indicators based on content
            if any(word in line.lower() for word in ['important', 'critical', 'key']):
                line = f"🎯 {line}"
            elif any(word in line.lower() for word in ['warning', 'caution', 'note']):
                line = f"⚠️ {line}"
            elif any(word in line.lower() for word in ['success', 'complete', 'done']):
                line = f"✅ {line}"
            elif any(word in line.lower() for word in ['error', 'failed', 'problem']):
                line = f"❌ {line}"
            elif any(word in line.lower() for word in ['tip', 'hint', 'idea']):
                line = f"💡 {line}"
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '•', '-')):
                # Already has list formatting
                pass
            elif len(line) < 80 and not line.endswith(('.', '!', '?', ':')):
                # Short line, might be a header
                line = f"📌 {line}"

            formatted_lines.append(line)

        return '\n'.join(formatted_lines)

    @staticmethod
    def _apply_progressive_disclosure(text: str) -> str:
        """Apply progressive disclosure for high cognitive load."""
        lines = text.split('\n')
        essential_lines = []
        detailed_lines = []

        for line in lines:
            # Consider short, indicator-containing lines as essential
            if (len(line.strip()) < 100 and
                any(indicator in line for indicator in ['✅', '❌', '⚠️', '💡', '🎯', '📌'])):
                essential_lines.append(line)
            else:
                detailed_lines.append(line)

        if detailed_lines:
            essential_lines.append("")
            essential_lines.append("💡 **Details available:** Use 'show more' or scroll for complete information")

        return '\n'.join(essential_lines)

    @staticmethod
    def _add_detailed_guidance(text: str) -> str:
        """Add detailed guidance for low cognitive load."""
        if len(text.split()) > 50:
            lines = text.split('\n')
            enhanced_lines = []

            for i, line in enumerate(lines):
                enhanced_lines.append(line)
                # Add helpful context every few lines
                if i > 0 and i % 5 == 0:
                    enhanced_lines.append("💭 **Taking it step by step - you're doing great!**")

            return '\n'.join(enhanced_lines)

        return text

    @staticmethod
    def _add_cognitive_warnings(text: str, cognitive_load: float) -> str:
        """Add cognitive load warnings."""
        word_count = len(text.split())

        if cognitive_load > 0.8 and word_count > 200:
            warning = f"\n\n⚠️ **High Cognitive Load Detected** ({cognitive_load:.1f})\n"
            warning += "This response contains detailed information. Take breaks and focus on one section at a time.\n"
            return warning + text

        if word_count > 500:
            sections = text.split('\n\n')
            if len(sections) > 3:
                return f"📚 **Comprehensive Response** ({word_count} words, {len(sections)} sections)\n\n{text}"

        return text


class CacheManager:
    """
    Intelligent caching manager with ADHD optimizations.

    Provides Redis caching, compression, performance monitoring,
    and ADHD-friendly response formatting.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.formatter = ADHDFormatter()

        # Cache configuration
        self.default_ttl = 3600  # 1 hour
        self.compression_threshold = 1024  # Compress responses > 1KB
        self.max_memory_mb = 100  # Redis memory limit

        # Statistics
        self.stats = CacheStats()
        self.start_time = time.time()

        # ADHD context
        self.current_cognitive_load = 0.5
        self.attention_state = "focused"

    async def initialize(self) -> bool:
        """Initialize Redis connection and cache."""
        try:
            logger.info("🗄️ Initializing Cache Manager...")

            self.redis = redis.Redis.from_url(self.redis_url, decode_responses=False)
            await self.redis.ping()

            # Set memory limits
            await self.redis.config_set('maxmemory', f'{self.max_memory_mb}mb')
            await self.redis.config_set('maxmemory-policy', 'allkeys-lru')

            logger.info("✅ Cache Manager initialized with Redis")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize cache: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve cached data."""
        if not self.redis:
            return None

        start_time = time.time()
        self.stats.total_requests += 1

        try:
            # Get compressed data
            compressed_data = await self.redis.get(f"cache:{key}")
            if not compressed_data:
                self.stats.cache_misses += 1
                return None

            # Decompress if needed
            data = self._decompress_data(compressed_data)

            # Parse JSON
            cache_entry = json.loads(data)

            # Update access statistics
            await self._update_access_stats(key)

            # Apply ADHD formatting
            if isinstance(cache_entry.get('data'), str):
                cache_entry['data'] = self.formatter.format_response(
                    cache_entry['data'],
                    self.current_cognitive_load
                )

            self.stats.cache_hits += 1
            response_time = time.time() - start_time
            self.stats.avg_response_time = (
                self.stats.avg_response_time + response_time
            ) / 2

            logger.debug(f"Cache hit for key: {key}")
            return cache_entry.get('data')

        except Exception as e:
            logger.debug(f"Cache retrieval error for key {key}: {e}")
            self.stats.cache_misses += 1
            return None

    async def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Store data in cache."""
        if not self.redis:
            return False

        try:
            # Create cache entry
            cache_entry = {
                'data': data,
                'created_at': datetime.now().isoformat(),
                'compressed': False
            }

            # Serialize to JSON
            json_data = json.dumps(cache_entry, default=str)

            # Compress if above threshold
            if len(json_data.encode('utf-8')) > self.compression_threshold:
                compressed_data = self._compress_data(json_data)
                cache_entry['compressed'] = True
                final_data = compressed_data
                self.stats.compression_savings += len(json_data) - len(compressed_data)
            else:
                final_data = json_data

            # Store in Redis
            ttl_value = ttl or self.default_ttl
            await self.redis.setex(f"cache:{key}", ttl_value, final_data)

            # Store metadata
            await self.redis.setex(
                f"meta:{key}",
                ttl_value,
                json.dumps({
                    'created_at': cache_entry['created_at'],
                    'compressed': cache_entry['compressed'],
                    'size_bytes': len(final_data)
                })
            )

            logger.debug(f"Cached data for key: {key} (TTL: {ttl_value}s)")
            return True

        except Exception as e:
            logger.error(f"Cache storage error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete cached data."""
        if not self.redis:
            return False

        try:
            await self.redis.delete(f"cache:{key}")
            await self.redis.delete(f"meta:{key}")
            await self.redis.delete(f"stats:{key}")
            logger.debug(f"Deleted cache for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache deletion error for key {key}: {e}")
            return False

    async def clear_all(self) -> bool:
        """Clear all cached data."""
        if not self.redis:
            return False

        try:
            # Clear cache keys
            cache_keys = await self.redis.keys("cache:*")
            meta_keys = await self.redis.keys("meta:*")
            stats_keys = await self.redis.keys("stats:*")

            all_keys = cache_keys + meta_keys + stats_keys
            if all_keys:
                await self.redis.delete(*all_keys)

            # Reset statistics
            self.stats = CacheStats()
            self.start_time = time.time()

            logger.info(f"✅ Cleared {len(all_keys)} cache entries")
            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def _update_access_stats(self, key: str) -> None:
        """Update access statistics for a key."""
        try:
            stats_key = f"stats:{key}"
            stats_data = await self.redis.get(stats_key)

            if stats_data:
                stats = json.loads(stats_data.decode('utf-8'))
                stats['access_count'] += 1
                stats['last_accessed'] = datetime.now().isoformat()
            else:
                stats = {
                    'access_count': 1,
                    'last_accessed': datetime.now().isoformat(),
                    'first_accessed': datetime.now().isoformat()
                }

            await self.redis.setex(stats_key, self.default_ttl, json.dumps(stats))

        except Exception as e:
            logger.debug(f"Failed to update access stats for {key}: {e}")

    def _compress_data(self, data: str) -> bytes:
        """Compress data using zlib."""
        return zlib.compress(data.encode('utf-8'))

    def _decompress_data(self, data: bytes) -> str:
        """Decompress data using zlib."""
        try:
            return zlib.decompress(data).decode('utf-8')
        except Exception as e:
            # If decompression fails, assume it's uncompressed
            return data.decode('utf-8')

            logger.error(f"Error: {e}")
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        if not self.redis:
            return {"status": "not_connected"}

        try:
            # Get Redis info
            info = await self.redis.info()
            memory_usage = info.get('used_memory', 0) / (1024 * 1024)  # MB

            # Update stats
            self.stats.memory_usage_mb = memory_usage

            # Get cache size
            cache_keys = await self.redis.keys("cache:*")
            cache_size = len(cache_keys)

            return {
                "status": "operational",
                "cache_size": cache_size,
                "memory_usage_mb": round(memory_usage, 2),
                "hit_rate": round(self.stats.hit_rate, 3),
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "compression_savings_bytes": self.stats.compression_savings,
                "avg_response_time_ms": round(self.stats.avg_response_time * 1000, 2),
                "uptime_seconds": round(time.time() - self.start_time, 0),
                "adhd_context": {
                    "cognitive_load": self.current_cognitive_load,
                    "attention_state": self.attention_state
                }
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}

    def update_adhd_context(self, cognitive_load: float, attention_state: str) -> None:
        """Update ADHD context for formatting decisions."""
        self.current_cognitive_load = cognitive_load
        self.attention_state = attention_state

        logger.debug(f"Updated ADHD context: load={cognitive_load:.1f}, state={attention_state}")

    async def health_check(self) -> bool:
        """Perform cache health check."""
        if not self.redis:
            return False

        try:
            await self.redis.ping()
            return True
        except Exception as e:
            return False</content>
            logger.error(f"Error: {e}")
</xai:function_call">The file content contains invalid XML/HTML markup. Please provide clean Python code only.