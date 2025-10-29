"""Test data collectors."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scripts.neon_dashboard.collectors.base_collector import BaseCollector, CacheEntry
from scripts.neon_dashboard.collectors.pm_collector import PMCollector
from scripts.neon_dashboard.collectors.impl_collector import ImplementationCollector
from scripts.neon_dashboard.config.settings import PMModeSettings, ServiceEndpoints


@pytest.mark.asyncio
async def test_base_collector_cache():
    """Test cache TTL and expiration."""
    collector = BaseCollector(cache_ttl=0.1)
    collector.fetch = AsyncMock(return_value={"test": "data"})
    
    # First call fetches
    result = await collector.get("test")
    assert result == {"test": "data"}
    assert collector.fetch.call_count == 1
    
    # Second call uses cache
    result = await collector.get("test")
    assert result == {"test": "data"}
    assert collector.fetch.call_count == 1
    
    # Wait for cache to expire
    await asyncio.sleep(0.15)
    result = await collector.get("test")
    assert collector.fetch.call_count == 2
    
    await collector.close()


@pytest.mark.asyncio
async def test_pm_collector_fallback():
    """Test PM collector falls back gracefully when services offline."""
    settings = PMModeSettings(
        leantime_url="http://localhost:9999",
        conport_url="http://localhost:9999"
    )
    collector = PMCollector(settings)
    
    data = await collector.fetch()
    
    # Should return fallback data
    assert "epics" in data
    assert "sprint" in data
    assert len(data["epics"]) > 0
    assert data["sprint"]["name"] == "Q1 2025 Sprint"
    
    await collector.close()


@pytest.mark.asyncio
async def test_impl_collector_graceful_degradation():
    """Test implementation collector handles missing services."""
    settings = ServiceEndpoints(
        adhd_engine_url="http://localhost:9999",
        activity_capture_url="http://localhost:9999",
        serena_url="http://localhost:9999"
    )
    collector = ImplementationCollector(settings)
    
    data = await collector.fetch()
    
    # Should return data with None/default values
    assert isinstance(data, dict)
    assert "adhd" in data
    assert "git" in data
    
    await collector.close()


@pytest.mark.asyncio
async def test_http_timeout():
    """Test 2s timeout is enforced."""
    import time
    
    collector = BaseCollector(timeout=0.5)
    
    start = time.time()
    result = await collector._http_json("http://192.0.2.1:9999/slow")
    elapsed = time.time() - start
    
    assert result is None
    assert elapsed < 1.0  # Should timeout well before 1s
    
    await collector.close()
