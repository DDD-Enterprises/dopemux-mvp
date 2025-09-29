"""
Serena v2 Redis Configuration Optimizer

ADHD-optimized Redis configuration for sub-millisecond cache performance
and intelligent memory management for navigation intelligence.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisOptimizer:
    """
    Redis configuration optimizer for ADHD navigation performance.

    Features:
    - Sub-millisecond cache response optimization
    - Memory usage optimization for large codebases
    - Connection pooling for concurrent navigation
    - ADHD-friendly configuration validation
    - Automatic performance tuning
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None

    async def optimize_for_navigation(self) -> Dict[str, Any]:
        """Optimize Redis configuration for navigation intelligence."""
        optimization_results = {
            "connection_optimized": False,
            "memory_optimized": False,
            "performance_tuned": False,
            "adhd_config_applied": False,
            "recommendations": []
        }

        try:
            # Connect to Redis
            self.client = redis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()

            # 1. Optimize connection settings
            connection_results = await self._optimize_connection_settings()
            optimization_results["connection_optimized"] = connection_results["success"]
            optimization_results["recommendations"].extend(connection_results.get("recommendations", []))

            # 2. Optimize memory settings
            memory_results = await self._optimize_memory_settings()
            optimization_results["memory_optimized"] = memory_results["success"]
            optimization_results["recommendations"].extend(memory_results.get("recommendations", []))

            # 3. Tune for ADHD performance targets
            performance_results = await self._tune_adhd_performance()
            optimization_results["performance_tuned"] = performance_results["success"]
            optimization_results["recommendations"].extend(performance_results.get("recommendations", []))

            # 4. Apply ADHD-specific configuration
            adhd_results = await self._apply_adhd_configuration()
            optimization_results["adhd_config_applied"] = adhd_results["success"]
            optimization_results["recommendations"].extend(adhd_results.get("recommendations", []))

            logger.info(f"🚀 Redis optimization complete: {sum(1 for k, v in optimization_results.items() if k.endswith('_optimized') and v)}/4 optimizations successful")

            return optimization_results

        except Exception as e:
            logger.error(f"Redis optimization failed: {e}")
            optimization_results["error"] = str(e)
            return optimization_results
        finally:
            if self.client:
                await self.client.close()

    async def _optimize_connection_settings(self) -> Dict[str, Any]:
        """Optimize Redis connection settings for navigation performance."""
        try:
            recommendations = []

            # Check current connection configuration
            info = await self.client.info()

            # Connection optimization recommendations
            connected_clients = info.get("connected_clients", 0)
            max_clients = info.get("maxclients", 10000)

            if connected_clients > 50:
                recommendations.append("🔗 High client count detected - consider connection pooling")

            # Timeout settings for ADHD responsiveness
            timeout_config = await self.client.config_get("timeout")
            current_timeout = int(timeout_config.get("timeout", 0))

            if current_timeout == 0:
                recommendations.append("⏱️ Consider setting client timeout for memory management")
            elif current_timeout > 300:  # 5 minutes
                recommendations.append("⚡ Client timeout is high - consider reducing for ADHD responsiveness")

            # TCP keepalive for stable connections
            tcp_keepalive = await self.client.config_get("tcp-keepalive")
            keepalive_value = int(tcp_keepalive.get("tcp-keepalive", 0))

            if keepalive_value == 0:
                recommendations.append("🔌 Enable TCP keepalive for stable long-running connections")

            return {
                "success": True,
                "connected_clients": connected_clients,
                "max_clients": max_clients,
                "timeout": current_timeout,
                "tcp_keepalive": keepalive_value,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Connection optimization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _optimize_memory_settings(self) -> Dict[str, Any]:
        """Optimize Redis memory settings for navigation cache."""
        try:
            recommendations = []

            # Check memory usage
            info = await self.client.info("memory")
            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0)

            # Memory optimization for navigation cache
            if max_memory == 0:
                recommendations.append("💾 Consider setting maxmemory limit for stable performance")
            elif used_memory > max_memory * 0.8:
                recommendations.append("⚠️ Memory usage high - consider increasing limit or enabling eviction")

            # Eviction policy for navigation cache
            eviction_policy = await self.client.config_get("maxmemory-policy")
            current_policy = eviction_policy.get("maxmemory-policy", "noeviction")

            # For navigation cache, LRU is ideal for ADHD users (keep frequently accessed items)
            if current_policy == "noeviction":
                recommendations.append("🧠 ADHD Optimization: Consider 'allkeys-lru' eviction for navigation cache")
            elif current_policy not in ["allkeys-lru", "volatile-lru"]:
                recommendations.append("🎯 Consider LRU eviction policy for better ADHD navigation cache management")

            # Key expiration settings
            active_expire_cycle_time = await self.client.config_get("hz")
            hz_value = int(active_expire_cycle_time.get("hz", 10))

            if hz_value < 10:
                recommendations.append("⚡ Increase active expiration frequency for responsive cache cleanup")

            return {
                "success": True,
                "used_memory_mb": round(used_memory / 1024 / 1024, 1),
                "max_memory_mb": round(max_memory / 1024 / 1024, 1) if max_memory > 0 else "unlimited",
                "eviction_policy": current_policy,
                "expiration_hz": hz_value,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _tune_adhd_performance(self) -> Dict[str, Any]:
        """Tune Redis for ADHD performance requirements."""
        try:
            recommendations = []

            # Test current performance
            performance_tests = []

            # Test 1: Cache set/get performance
            test_key = "adhd_perf_test"
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}

            # Measure SET performance
            import time
            start_time = time.time()
            await self.client.set(test_key, json.dumps(test_data), ex=60)
            set_time_ms = (time.time() - start_time) * 1000
            performance_tests.append(("cache_set", set_time_ms))

            # Measure GET performance
            start_time = time.time()
            retrieved_data = await self.client.get(test_key)
            get_time_ms = (time.time() - start_time) * 1000
            performance_tests.append(("cache_get", get_time_ms))

            # Cleanup test key
            await self.client.delete(test_key)

            # Analyze performance for ADHD requirements
            avg_cache_time = (set_time_ms + get_time_ms) / 2

            if avg_cache_time > 5.0:  # >5ms is slow for ADHD users
                recommendations.append("🚨 Cache operations slow - check Redis configuration and network")
            elif avg_cache_time > 2.0:  # >2ms is acceptable but not optimal
                recommendations.append("⚡ Cache operations could be faster - consider Redis tuning")
            else:
                recommendations.append("✅ Excellent cache performance for ADHD navigation")

            # Test pipelining for batch operations
            start_time = time.time()
            pipeline = self.client.pipeline()
            for i in range(10):
                pipeline.set(f"batch_test_{i}", f"data_{i}", ex=60)
            await pipeline.execute()
            pipeline_time_ms = (time.time() - start_time) * 1000

            # Cleanup batch test keys
            await self.client.delete(*[f"batch_test_{i}" for i in range(10)])

            if pipeline_time_ms > 20.0:  # >20ms for 10 operations
                recommendations.append("📦 Batch operations could be optimized for better ADHD prefetching")
            else:
                recommendations.append("🚀 Excellent batch performance for intelligent prefetching")

            return {
                "success": True,
                "performance_tests": {
                    test_name: f"{duration:.2f}ms"
                    for test_name, duration in performance_tests
                },
                "average_cache_time_ms": round(avg_cache_time, 2),
                "batch_operation_time_ms": round(pipeline_time_ms, 2),
                "adhd_performance_rating": (
                    "🚀 Excellent" if avg_cache_time < 2.0 else
                    "✅ Good" if avg_cache_time < 5.0 else
                    "⚠️ Needs Tuning"
                ),
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Performance tuning failed: {e}")
            return {"success": False, "error": str(e)}

    async def _apply_adhd_configuration(self) -> Dict[str, Any]:
        """Apply ADHD-specific Redis configuration optimizations."""
        try:
            recommendations = []
            config_applied = []

            # ADHD-optimized configuration settings
            adhd_optimizations = {
                # Faster expiration cleanup for responsive cache management
                "hz": 50,  # Increased from default 10

                # Optimize for small, frequent cache operations (navigation cache pattern)
                "hash-max-ziplist-entries": 1024,  # Good for symbol data
                "hash-max-ziplist-value": 1024,    # Good for navigation context

                # Optimize memory allocation for frequent small allocations
                "activedefrag": "yes",  # Automatic defragmentation
                "active-defrag-ignore-bytes": "100mb",  # Start defrag at 100MB

                # Lazy freeing for better responsiveness
                "lazyfree-lazy-eviction": "yes",
                "lazyfree-lazy-expire": "yes",
                "lazyfree-lazy-server-del": "yes"
            }

            # Apply configurations that are safe to change
            safe_configs = ["hz", "activedefrag", "lazyfree-lazy-eviction"]

            for config_key, config_value in adhd_optimizations.items():
                if config_key in safe_configs:
                    try:
                        # Get current value
                        current_config = await self.client.config_get(config_key)
                        current_value = current_config.get(config_key, "unknown")

                        # Apply optimization if different
                        if str(current_value) != str(config_value):
                            await self.client.config_set(config_key, config_value)
                            config_applied.append(f"{config_key}: {current_value} → {config_value}")
                            logger.debug(f"🔧 Applied Redis config: {config_key} = {config_value}")

                    except Exception as e:
                        logger.debug(f"Could not apply {config_key} config: {e}")
                        recommendations.append(f"⚙️ Manually configure {config_key}={config_value} for optimal ADHD performance")

            # Additional recommendations for manual configuration
            recommendations.extend([
                "🧠 ADHD Performance: Use dedicated Redis instance for navigation cache",
                "⚡ Network: Ensure Redis is on localhost or low-latency connection",
                "💾 Memory: Allocate 512MB-1GB for navigation cache depending on codebase size",
                "🔄 Persistence: Consider disabling Redis persistence for pure cache usage"
            ])

            return {
                "success": True,
                "configurations_applied": config_applied,
                "adhd_optimizations": adhd_optimizations,
                "safe_configs_available": safe_configs,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"ADHD configuration failed: {e}")
            return {"success": False, "error": str(e)}

    async def generate_optimal_config(self) -> str:
        """Generate optimal Redis configuration file for ADHD navigation."""
        config_template = """
# Serena v2 Layer 1 - ADHD-Optimized Redis Configuration
# Optimized for sub-millisecond navigation cache performance

# Memory Management for Navigation Cache
maxmemory 512mb
maxmemory-policy allkeys-lru  # Keep frequently accessed navigation data

# ADHD Performance Optimizations
hz 50                          # Faster expiration cleanup
timeout 300                    # 5-minute client timeout for memory management
tcp-keepalive 60              # Stable connections for navigation sessions

# Lazy Freeing for Responsiveness (reduce blocking operations)
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes

# Optimize for Small Frequent Operations (navigation cache pattern)
hash-max-ziplist-entries 1024
hash-max-ziplist-value 1024
set-max-intset-entries 1024

# Memory Defragmentation for Long Sessions
activedefrag yes
active-defrag-ignore-bytes 100mb
active-defrag-threshold-lower 10

# Disable Persistence for Pure Cache Usage (optional)
# save ""
# appendonly no

# Network Optimization
tcp-backlog 511
maxclients 1000

# Logging (minimal for performance)
loglevel notice
syslog-enabled no

# ADHD-Specific Comments:
# - Sub-2ms cache operations for instant navigation
# - LRU eviction preserves frequently accessed code symbols
# - Lazy freeing prevents navigation blocking
# - Active defragmentation maintains performance during long coding sessions
# - Conservative resource limits prevent system overwhelm
"""

        return config_template.strip()


# Validation and testing functions
async def validate_redis_for_adhd_navigation(redis_url: str = "redis://localhost:6379") -> Dict[str, Any]:
    """Validate Redis configuration for ADHD navigation requirements."""
    validation_results = {
        "connection_healthy": False,
        "performance_acceptable": False,
        "memory_sufficient": False,
        "adhd_compliant": False,
        "issues": [],
        "recommendations": []
    }

    try:
        client = redis.from_url(redis_url, decode_responses=True)

        # Test connection
        await client.ping()
        validation_results["connection_healthy"] = True

        # Test performance (ADHD requirement: <2ms cache operations)
        import time

        test_times = []
        for i in range(10):
            start_time = time.time()
            await client.set(f"perf_test_{i}", f"data_{i}", ex=60)
            await client.get(f"perf_test_{i}")
            operation_time = (time.time() - start_time) * 1000
            test_times.append(operation_time)

        # Cleanup test keys
        await client.delete(*[f"perf_test_{i}" for i in range(10)])

        avg_time = sum(test_times) / len(test_times)
        validation_results["average_operation_time_ms"] = round(avg_time, 2)

        if avg_time < 2.0:
            validation_results["performance_acceptable"] = True
        else:
            validation_results["issues"].append(f"Cache operations slow: {avg_time:.1f}ms (target: <2ms)")

        # Check memory configuration
        info = await client.info("memory")
        used_memory_mb = info.get("used_memory", 0) / 1024 / 1024
        max_memory = info.get("maxmemory", 0)

        if max_memory > 0:
            validation_results["memory_sufficient"] = True
        else:
            validation_results["issues"].append("No memory limit set - could cause system issues")

        # ADHD compliance check
        config_checks = {
            "maxmemory-policy": ["allkeys-lru", "volatile-lru"],  # LRU good for navigation
            "hz": lambda x: int(x) >= 10,  # Fast expiration
            "lazyfree-lazy-eviction": ["yes"]  # Non-blocking operations
        }

        compliant_configs = 0
        total_configs = len(config_checks)

        for config_key, expected_values in config_checks.items():
            try:
                current_config = await client.config_get(config_key)
                current_value = current_config.get(config_key, "")

                if callable(expected_values):
                    if expected_values(current_value):
                        compliant_configs += 1
                elif current_value in expected_values:
                    compliant_configs += 1
                else:
                    validation_results["issues"].append(f"Non-optimal {config_key}: {current_value}")

            except Exception:
                validation_results["issues"].append(f"Could not check {config_key} configuration")

        validation_results["adhd_compliant"] = compliant_configs >= (total_configs * 0.7)

        # Generate recommendations
        if not validation_results["performance_acceptable"]:
            validation_results["recommendations"].append("🚀 Optimize Redis for sub-2ms cache operations")

        if not validation_results["adhd_compliant"]:
            validation_results["recommendations"].append("🧠 Apply ADHD-optimized Redis configuration")

        if validation_results["connection_healthy"] and validation_results["performance_acceptable"]:
            validation_results["recommendations"].append("✅ Redis ready for ADHD navigation intelligence")

        await client.close()

        return validation_results

    except Exception as e:
        logger.error(f"Redis validation failed: {e}")
        validation_results["error"] = str(e)
        return validation_results


async def quick_redis_health_check() -> Dict[str, Any]:
    """Quick Redis health check for Layer 1 deployment readiness."""
    try:
        client = redis.from_url("redis://localhost:6379", decode_responses=True)

        # Basic connectivity
        await client.ping()

        # Performance test
        import time
        start_time = time.time()
        await client.set("health_test", "ok", ex=10)
        cached_value = await client.get("health_test")
        operation_time = (time.time() - start_time) * 1000

        await client.delete("health_test")
        await client.close()

        status = "🚀 Ready" if operation_time < 2.0 else "✅ Good" if operation_time < 5.0 else "⚠️ Slow"

        return {
            "redis_available": True,
            "operation_time_ms": round(operation_time, 2),
            "status": status,
            "adhd_ready": operation_time < 5.0
        }

    except Exception as e:
        return {
            "redis_available": False,
            "error": str(e),
            "status": "🔴 Unavailable"
        }


if __name__ == "__main__":
    # Quick validation when run directly
    async def main():
        print("🗄️ Redis ADHD Navigation Validation")
        health = await quick_redis_health_check()
        print(f"Status: {health['status']}")

        if health["redis_available"]:
            print(f"Performance: {health['operation_time_ms']}ms")
            print(f"ADHD Ready: {'✅ Yes' if health['adhd_ready'] else '⚠️ Needs optimization'}")

    asyncio.run(main())