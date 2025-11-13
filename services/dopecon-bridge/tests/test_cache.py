"""
Tests for Multi-Tier Caching System
Validates memory, Redis, and database tier behavior
"""

import asyncio
import pytest
import time

import redis.asyncio as redis

from cache import MemoryCache, MultiTierCache


class TestMemoryCache:
    """Test MemoryCache (Tier 1)"""

    def test_get_set_basic(self):
        """Test basic get/set operations"""
        cache = MemoryCache()

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_ttl_expiry(self):
        """Test that entries expire after TTL"""
        cache = MemoryCache(default_ttl=1)

        cache.set("key1", "value1")

        # Immediate get should work
        assert cache.get("key1") == "value1"

        # Wait for expiry
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        """Test LRU eviction when max size reached"""
        cache = MemoryCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # All should exist
        assert cache.get("key1") == "value1"

        # Add 4th item (should evict key2 as LRU)
        cache.set("key4", "value4")

        # key1 was accessed recently, so key2 should be evicted
        assert cache.get("key1") == "value1"  # Still exists
        assert cache.get("key2") is None  # Evicted (was LRU)
        assert cache.get("key4") == "value4"  # New item

    def test_metrics_tracking(self):
        """Test cache metrics"""
        cache = MemoryCache()

        cache.set("key1", "value1")

        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        metrics = cache.get_metrics()

        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["hit_rate_percent"] == 50.0


class TestMultiTierCache:
    """Test MultiTierCache (all 3 tiers)"""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for testing"""
        client = redis.from_url(
            "redis://localhost:6379",
            db=13,  # Cache test database
            decode_responses=True
        )

        # Clear test database
        await client.flushdb()

        yield client

        # Cleanup
        await client.flushdb()
        await client.aclose()

    @pytest.fixture
    def cache(self, redis_client):
        """Create MultiTierCache instance"""
        return MultiTierCache(
            redis_client=redis_client,
            memory_ttl=5,
            redis_ttl=60
        )

    @pytest.mark.asyncio
    async def test_memory_tier_fastest(self, cache):
        """Test that memory tier is fastest"""
        await cache.set("key1", {"data": "value1"})

        # First get from memory
        start = time.time()
        result = await cache.get("key1")
        memory_latency = (time.time() - start) * 1000

        assert result == {"data": "value1"}
        assert memory_latency < 1.0, f"Memory tier should be <1ms, got {memory_latency:.2f}ms"

    @pytest.mark.asyncio
    async def test_redis_tier_on_memory_miss(self, cache):
        """Test Redis tier used when memory misses"""
        # Set in Redis only
        await cache.redis_client.set(
            "key1",
            '{"data": "value1"}',
            ex=60
        )

        # Get should hit Redis and populate memory
        result = await cache.get("key1")

        assert result == {"data": "value1"}
        assert cache.redis_hits == 1

        # Second get should hit memory
        result2 = await cache.get("key1")
        assert cache.memory.hits == 1

    @pytest.mark.asyncio
    async def test_write_through_to_all_tiers(self, cache):
        """Test that writes go to all tiers"""
        await cache.set("key1", {"data": "value1"}, ttl=60)

        # Check memory
        assert cache.memory.get("key1") == {"data": "value1"}

        # Check Redis
        redis_value = await cache.redis_client.get("key1")
        assert redis_value is not None

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache):
        """Test pattern-based cache invalidation"""
        # Set multiple keys with pattern
        await cache.set("pattern:insight:workspace1", {"insight": "A"})
        await cache.set("pattern:insight:workspace2", {"insight": "B"})
        await cache.set("agent:metric:serena", {"events": 10})

        # Invalidate pattern
        await cache.invalidate_pattern("pattern:*")

        # Pattern keys should be gone
        assert await cache.get("pattern:insight:workspace1") is None
        assert await cache.get("pattern:insight:workspace2") is None

        # Other keys should remain
        assert await cache.get("agent:metric:serena") is not None

    @pytest.mark.asyncio
    async def test_delete_from_all_tiers(self, cache):
        """Test deletion removes from all tiers"""
        await cache.set("key1", {"data": "value1"})

        # Verify exists in all tiers
        assert cache.memory.get("key1") is not None
        assert await cache.redis_client.exists("key1")

        # Delete
        await cache.delete("key1")

        # Verify gone from all tiers
        assert cache.memory.get("key1") is None
        assert not await cache.redis_client.exists("key1")

    @pytest.mark.asyncio
    async def test_metrics_track_all_tiers(self, cache):
        """Test metrics from all tiers"""
        await cache.set("key1", "value1")

        # Memory hit
        await cache.get("key1")

        # Clear memory to force Redis hit
        cache.memory.clear()
        await cache.get("key1")

        metrics = cache.get_metrics()

        assert "memory" in metrics
        assert "redis" in metrics
        assert "database" in metrics
        assert "overall" in metrics
        assert metrics["overall"]["target_hit_rate"] == 80.0

    @pytest.mark.asyncio
    async def test_cache_hit_rate_above_target(self, cache):
        """Test that cache hit rate can exceed target"""
        # Set 10 items
        for i in range(10):
            await cache.set(f"key{i}", f"value{i}")

        # Get them multiple times (should all hit memory)
        for _ in range(5):
            for i in range(10):
                await cache.get(f"key{i}")

        metrics = cache.get_metrics()

        # Should have very high hit rate (50 gets, 10 misses on first iteration)
        # = 40 hits / 50 requests = 80%
        assert metrics["overall"]["hit_rate_percent"] >= 80.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
