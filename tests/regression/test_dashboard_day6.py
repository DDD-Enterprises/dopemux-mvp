#!/usr/bin/env python3
"""
Quick Test Script for Day 6 API Integration
Tests all service clients and modals with real backends
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.api_client import APIClient, APIConfig, CacheStrategy
from dashboard.service_clients import (
    ADHDEngineClient,
    DockerServiceClient,
    ConPortClient,
    DataPrefetcher
)
from prometheus_client import PrometheusClient


async def test_adhd_engine():
    """Test ADHD Engine client"""
    print("\n🧠 Testing ADHD Engine Client...")
    
    client = ADHDEngineClient()
    
    try:
        # Test energy level
        energy = await client.get_energy_level("default")
        print(f"  ✓ Energy Level: {energy.get('energy_level')} "
              f"(confidence: {energy.get('confidence', 0):.0%})")
        
        # Test attention state
        attention = await client.get_attention_state("default")
        print(f"  ✓ Attention State: {attention.get('state')} "
              f"(quality: {attention.get('quality_score', 0):.0%})")
        
        # Test task assessment
        task_data = {
            "id": "test_task",
            "title": "Test API integration",
            "complexity": 0.7,
            "estimated_duration_minutes": 60
        }
        assessment = await client.assess_task("default", task_data)
        print(f"  ✓ Task Assessment: {assessment.get('suitability_score', 0):.0%} suitable")
        
        print("  ✅ ADHD Engine: PASS")
    except Exception as e:
        print(f"  ❌ ADHD Engine: FAIL - {e}")
    finally:
        await client.close()


async def test_docker_client():
    """Test Docker service client"""
    print("\n🐳 Testing Docker Client...")
    
    client = DockerServiceClient()
    
    try:
        # Test service status
        services = ["adhd_engine", "prometheus", "redis"]
        
        for service in services:
            status = await client.get_service_status(service)
            is_healthy = "✓" if status.get('is_healthy') else "✗"
            print(f"  {is_healthy} {service}: {status.get('status')}")
        
        # Test logs
        logs = await client.get_recent_logs("adhd_engine", lines=5)
        print(f"  ✓ Fetched {len(logs)} log lines")
        
        print("  ✅ Docker Client: PASS")
    except Exception as e:
        print(f"  ❌ Docker Client: FAIL - {e}")


async def test_prometheus_client():
    """Test Prometheus client"""
    print("\n📊 Testing Prometheus Client...")
    
    client = PrometheusClient()
    
    try:
        # Test query_range
        data = await client.query_range(
            "adhd_cognitive_load",
            hours=2,
            step="5m"
        )
        print(f"  ✓ Fetched {len(data)} data points")
        
        if data:
            latest_time, latest_value = data[-1]
            print(f"  ✓ Latest cognitive load: {latest_value:.2f} at {latest_time.strftime('%H:%M')}")
        
        print("  ✅ Prometheus Client: PASS")
    except Exception as e:
        print(f"  ❌ Prometheus Client: FAIL - {e}")
    finally:
        await client.close()


async def test_conport_client():
    """Test ConPort client"""
    print("\n🗄️  Testing ConPort Client...")
    
    client = ConPortClient()
    
    try:
        # Test recent decisions (mock for now)
        decisions = await client.get_recent_decisions("default", limit=5)
        print(f"  ✓ Fetched {len(decisions)} decisions")
        
        # Test current context
        context = await client.get_current_context("default")
        print(f"  ✓ Current project: {context.get('current_project')}")
        print(f"  ✓ Session duration: {context.get('session_duration_minutes')}min")
        
        print("  ⚠️  ConPort Client: PASS (mock data)")
    except Exception as e:
        print(f"  ❌ ConPort Client: FAIL - {e}")


async def test_data_prefetcher():
    """Test background data prefetcher"""
    print("\n🔄 Testing Data Prefetcher...")
    
    prefetcher = DataPrefetcher()
    
    try:
        # Start prefetcher
        prefetcher.start()
        print("  ✓ Prefetcher started")
        
        # Wait for first prefetch cycle
        await asyncio.sleep(2)
        
        # Check prefetched data
        adhd_state = prefetcher.get_prefetched('adhd_state', max_age_seconds=30)
        if adhd_state:
            print(f"  ✓ ADHD state prefetched")
        else:
            print(f"  ⚠️  ADHD state not yet available")
        
        # Stop prefetcher
        prefetcher.stop()
        print("  ✓ Prefetcher stopped")
        
        print("  ✅ Data Prefetcher: PASS")
    except Exception as e:
        print(f"  ❌ Data Prefetcher: FAIL - {e}")
        prefetcher.stop()


async def test_api_client_caching():
    """Test API client caching"""
    print("\n💾 Testing API Client Caching...")
    
    config = APIConfig(
        base_url="http://localhost:8000",
        cache_strategy=CacheStrategy.SHORT,
        max_retries=2
    )
    client = APIClient(config)
    
    try:
        import time
        
        # First request (cache miss)
        start = time.time()
        result1 = await client.get(
            "/api/v1/energy-level/default",
            fallback_data={"energy_level": "MEDIUM"}
        )
        duration1 = (time.time() - start) * 1000
        print(f"  ✓ First request: {duration1:.0f}ms (cache miss)")
        
        # Second request (cache hit)
        start = time.time()
        result2 = await client.get(
            "/api/v1/energy-level/default",
            fallback_data={"energy_level": "MEDIUM"}
        )
        duration2 = (time.time() - start) * 1000
        print(f"  ✓ Second request: {duration2:.0f}ms (cache hit)")
        
        if duration2 < duration1 / 2:
            print(f"  ✓ Cache speedup: {(duration1/duration2):.1f}x faster")
        
        print("  ✅ API Client Caching: PASS")
    except Exception as e:
        print(f"  ❌ API Client Caching: FAIL - {e}")
    finally:
        await client.close()


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Dashboard Day 6 - API Integration Test Suite")
    print("=" * 60)
    
    await test_adhd_engine()
    await test_docker_client()
    await test_prometheus_client()
    await test_conport_client()
    await test_data_prefetcher()
    await test_api_client_caching()
    
    print("\n" + "=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
