"""
Working Memory Assistant - Performance Validation Tests

Validates the 20-30x performance improvement targets for interrupt recovery.
"""

import asyncio
import time
import statistics
from wma_core import WorkingMemoryAssistant, SnapshotResult, RecoveryResult

async def benchmark_snapshot_performance(wma: WorkingMemoryAssistant, iterations: int = 10) -> dict:
    """Benchmark snapshot capture performance with incremental support"""
    times = []
    compression_ratios = []

    for i in range(iterations):
        start_time = time.perf_counter()
        result = await wma.trigger_snapshot("performance_test", allow_incremental=True)
        end_time = time.perf_counter()

        if result.success:
            times.append(result.capture_time_ms)
            compression_ratios.append(result.compression_ratio)
            print(f"✅ Iteration {i+1}: {result.capture_time_ms:.1f}ms, compression {result.compression_ratio:.2f}x")
        else:
            print(f"❌ Iteration {i+1} failed: {result.error}")

    return {
        'iterations': len(times),
        'average_time_ms': statistics.mean(times) if times else 0,
        'median_time_ms': statistics.median(times) if times else 0,
        'min_time_ms': min(times) if times else 0,
        'max_time_ms': max(times) if times else 0,
        'target_met': all(t < 200 for t in times),  # <200ms target
        'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0,
        'average_compression_ratio': statistics.mean(compression_ratios) if compression_ratios else 1.0
    }

async def benchmark_recovery_performance(wma: WorkingMemoryAssistant, iterations: int = 5) -> dict:
    """Benchmark recovery performance"""
    times = []

    # Create snapshots for recovery testing
    snapshot_ids = []
    for i in range(iterations):
        result = await wma.trigger_snapshot("recovery_test")
        if result.success:
            snapshot_ids.append(result.snapshot_id)

    # Benchmark recoveries
    for snapshot_id in snapshot_ids:
        start_time = time.perf_counter()
        result = await wma.instant_recovery(snapshot_id)
        end_time = time.perf_counter()

        if result.success:
            times.append(result.recovery_time_ms)
            print(f"✅ Recovery {i+1}: {result.recovery_time_ms:.1f}ms")
        else:
            print(f"❌ Recovery failed for {snapshot_id}")

    return {
        'iterations': len(times),
        'average_time_ms': statistics.mean(times) if times else 0,
        'median_time_ms': statistics.median(times) if times else 0,
        'min_time_ms': min(times) if times else 0,
        'max_time_ms': max(times) if times else 0,
        'target_met': all(t < 2000 for t in times),  # <2s target
        'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0
    }

async def simulate_manual_recovery() -> dict:
    """Simulate traditional manual recovery time"""
    # Simulate manual recovery steps:
    # 1. Remember what you were working on (10-15s)
    # 2. Find the right files (5-10s)
    # 3. Restore cursor position (5-10s)
    # 4. Recollect thought process (10-15s)
    # 5. Check recent changes (5-10s)
    # Total: 35-60 seconds

    step_times = [
        ('recollecting_task', 12.5),  # Average of 10-15s
        ('finding_files', 7.5),        # Average of 5-10s
        ('restoring_cursor', 7.5),     # Average of 5-10s
        ('recollecting_thoughts', 12.5), # Average of 10-15s
        ('checking_changes', 7.5)      # Average of 5-10s
    ]

    total_time = sum(time for _, time in step_times)

    return {
        'total_time_seconds': total_time,
        'total_time_ms': total_time * 1000,
        'steps': step_times,
        'description': 'Traditional manual recovery simulation'
    }

async def test_security_and_privacy():
    """Test security and privacy features"""
    print("\n🔒 Testing Security & Privacy Features...")

    # Test encryption/decryption
    from main import encrypt_sensitive_data, decrypt_sensitive_data

    test_data = "sensitive user task description"
    encrypted = encrypt_sensitive_data(test_data)
    decrypted = decrypt_sensitive_data(encrypted)

    encryption_works = decrypted == test_data and encrypted != test_data

    print(f"  Encryption/Decryption: {'✅ WORKING' if encryption_works else '❌ FAILED'}")
    print(f"  Original: {test_data}")
    print(f"  Encrypted: {encrypted[:20]}...")
    print(f"  Decrypted: {decrypted}")

    return encryption_works

async def test_incremental_snapshots():
    """Test incremental snapshot functionality"""
    print("\n📦 Testing Incremental Snapshots...")

    wma = WorkingMemoryAssistant()
    await wma.initialize()

    # Create initial snapshot
    result1 = await wma.trigger_snapshot("initial", allow_incremental=False)
    print(f"  Full snapshot: {result1.capture_time_ms:.1f}ms")

    # Create incremental snapshot (should be smaller/faster)
    result2 = await wma.trigger_snapshot("incremental", allow_incremental=True)
    print(f"  Incremental snapshot: {result2.capture_time_ms:.1f}ms")

    # Test compression difference
    compression_diff = result1.compression_ratio - result2.compression_ratio
    print(f"  Compression ratio difference: {compression_diff:.2f}")

    return result1.success and result2.success

async def test_adhd_integration():
    """Test ADHD Engine integration"""
    print("\n🧠 Testing ADHD Engine Integration...")

    try:
        from adhd_integration import ADHDEngineIntegration

        integration = ADHDEngineIntegration()
        adhd_context = await integration.get_adhd_context("test_user")

        has_energy = 'energy_level' in adhd_context.__dict__
        has_attention = 'attention_state' in adhd_context.__dict__
        has_cognitive = 'cognitive_load' in adhd_context.__dict__

        integration_works = has_energy and has_attention and has_cognitive
        print(f"  ADHD Context Retrieval: {'✅ WORKING' if integration_works else '❌ FAILED'}")

        if integration_works:
            print(f"  Energy Level: {adhd_context.energy_level}")
            print(f"  Attention State: {adhd_context.attention_state}")
            print(f"  Cognitive Load: {adhd_context.cognitive_load}")

        return integration_works

    except Exception as e:
        print(f"  ADHD Integration: ❌ FAILED ({e})")
        return False

async def run_comprehensive_test_suite():
    """Run comprehensive test suite including security, integration, and performance"""
    print("🧪 Working Memory Assistant - Comprehensive Test Suite")
    print("=" * 70)

    results = {}

    # Security & Privacy Tests
    results['security'] = await test_security_and_privacy()

    # Incremental Snapshot Tests
    results['incremental'] = await test_incremental_snapshots()

    # ADHD Integration Tests
    results['adhd'] = await test_adhd_integration()

    # Performance Benchmarks
    print("\n🚀 Running Performance Benchmarks...")
    performance_results = await run_comprehensive_benchmark()
    results['performance'] = performance_results['all_targets_met']

    # Summary
    print("\n📋 Test Suite Results")
    print("=" * 40)

    test_results = [
        ('Security & Privacy', results['security']),
        ('Incremental Snapshots', results['incremental']),
        ('ADHD Integration', results['adhd']),
        ('Performance Targets', results['performance'])
    ]

    all_passed = all(result for _, result in test_results)

    for test_name, passed in test_results:
        status = '✅' if passed else '❌'
        print(f"  {status} {test_name}")

    print(f"\n🏆 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return {
        'test_results': results,
        'all_passed': all_passed,
        'performance_details': performance_results
    }

async def validate_20x_improvement(wma_recovery: dict, manual_recovery: dict) -> dict:
    """Validate 20-30x performance improvement target"""
    wma_avg_ms = wma_recovery['average_time_ms']
    manual_avg_ms = manual_recovery['total_time_ms']

    ratio = manual_avg_ms / wma_avg_ms if wma_avg_ms > 0 else 0
    target_range_low = 20.0
    target_range_high = 30.0

    # Check if within target range
    in_range = target_range_low <= ratio <= target_range_high
    status = 'PASSED' if in_range else 'NEEDS OPTIMIZATION' if ratio >= target_range_low else 'FAILED'

    return {
        'wma_time_ms': wma_avg_ms,
        'manual_time_ms': manual_avg_ms,
        'improvement_ratio': ratio,
        'target_range': f"{target_range_low}-{target_range_high}x",
        'in_target_range': in_range,
        'meets_minimum': ratio >= target_range_low,
        'exceeds_target': ratio >= target_range_high,
        'target_met': ratio >= target_range_low,
        'validation_passed': ratio >= target_range_low,
        'description': f'{ratio:.1f}x improvement ({status})'
    }

async def run_comprehensive_benchmark():
    """Run comprehensive performance validation"""
    print("🚀 Working Memory Assistant - Performance Validation")
    print("=" * 60)

    # Initialize WMA
    wma = WorkingMemoryAssistant()
    await wma.initialize()

    print("\n📊 Running performance benchmarks...")
    print("-" * 40)

    # Benchmark snapshot performance
    print("\n📸 Testing snapshot capture performance...")
    snapshot_benchmark = await benchmark_snapshot_performance(wma, iterations=10)

    # Benchmark recovery performance
    print("\n🔄 Testing recovery performance...")
    recovery_benchmark = await benchmark_recovery_performance(wma, iterations=5)

    # Simulate manual recovery for comparison
    print("\n⏱️  Simulating manual recovery baseline...")
    manual_recovery = await simulate_manual_recovery()

    # Validate 20-30x improvement target
    improvement = await validate_20x_improvement(recovery_benchmark, manual_recovery)

    print("\n📈 Performance Results")
    print("=" * 40)

    print("\n📸 Snapshot Performance:")
    print(f"  Average time: {snapshot_benchmark['average_time_ms']:.1f}ms")
    print(f"  Target (<200ms): {'✅ MET' if snapshot_benchmark['target_met'] else '❌ FAILED'}")
    print(f"  Consistency (std dev): {snapshot_benchmark['std_dev_ms']:.1f}ms")

    print("\n🔄 Recovery Performance:")
    print(f"  Average time: {recovery_benchmark['average_time_ms']:.1f}ms")
    print(f"  Target (<2000ms): {'✅ MET' if recovery_benchmark['target_met'] else '❌ FAILED'}")
    print(f"  Consistency (std dev): {recovery_benchmark['std_dev_ms']:.1f}ms")

    print("\n⚡ Overall Improvement:")
    print(f"  Manual recovery time: {manual_recovery['total_time_seconds']:.1f}s")
    print(f"  WMA recovery time: {recovery_benchmark['average_time_ms']/1000:.2f}s")
    print(f"  Improvement ratio: {improvement['improvement_ratio']:.1f}x")
    print(f"  Target (20-30x): {'✅ MET' if improvement['target_met'] else '❌ FAILED'}")

    print("\n🏆 Target Validation:")
    targets = [
        ('Snapshot <200ms', snapshot_benchmark['target_met']),
        ('Recovery <2s', recovery_benchmark['target_met']),
        ('20-30x improvement', improvement['target_met'])
    ]

    all_met = all(met for _, met in targets)
    print(f"Overall: {'✅ ALL TARGETS MET' if all_met else '❌ TARGETS NOT MET'}")

    for target, met in targets:
        status = '✅' if met else '❌'
        print(f"  {status} {target}")

    # System status
    print("\n🔧 System Status:")
    status = wma.get_system_status()
    print(f"  Memory usage: {status['memory_manager']['memory_usage_mb']:.1f}MB")
    print(f"  Snapshots stored: {status['snapshot_engine']['total_snapshots_captured']}")
    print(f"  System health: {status['overall_health']}")

    return {
        'snapshot_benchmark': snapshot_benchmark,
        'recovery_benchmark': recovery_benchmark,
        'manual_recovery': manual_recovery,
        'improvement': improvement,
        'all_targets_met': all_met
    }

async def run_stress_test(wma: WorkingMemoryAssistant, concurrent_users: int = 5):
    """Enhanced stress test with concurrent operations and cache validation"""
    print(f"\n🔥 Running enhanced stress test with {concurrent_users} concurrent users...")

    async def user_workflow(user_id: int):
        """Simulate realistic user workflow with cache validation"""
        results = []
        cache_hits = 0
        cache_misses = 0

        for i in range(3):
            # Snapshot with incremental support
            snapshot_result = await wma.trigger_snapshot(f"user_{user_id}_stress_{i}", allow_incremental=True)
            results.append(('snapshot', snapshot_result.capture_time_ms))

            if snapshot_result.success:
                # Recovery with cache check
                recovery_result = await wma.instant_recovery(snapshot_result.snapshot_id)
                results.append(('recovery', recovery_result.recovery_time_ms))

                # Cache validation
                if hasattr(recovery_result, 'cache_hit') and recovery_result.cache_hit:
                    cache_hits += 1
                else:
                    cache_misses += 1

            await asyncio.sleep(0.05)  # Reduced delay for more realistic stress

        return results, cache_hits, cache_misses

    # Run concurrent workflows
    start_time = time.time()
    tasks = [user_workflow(i) for i in range(concurrent_users)]
    results_data = await asyncio.gather(*tasks)
    end_time = time.time()

    # Unpack results
    results = [r[0] for r in results_data]
    total_hits = sum(r[1] for r in results_data)
    total_misses = sum(r[2] for r in results_data)

    # Analyze results
    all_times = []
    total_operations = 0
    for user_results, _, _ in results_data:
        for operation, time_ms in user_results:
            all_times.append(time_ms)
        total_operations += len(user_results)

    total_cache_requests = total_hits + total_misses
    cache_hit_rate = (total_hits / total_cache_requests) * 100 if total_cache_requests > 0 else 0

    print(f"  Total operations: {total_operations}")
    print(f"  Total time: {end_time - start_time:.2f}s")
    print(f"  Average operation time: {statistics.mean(all_times):.1f}ms")
    print(f"  Max operation time: {max(all_times):.1f}ms")
    print(f"  Operations/second: {total_operations / (end_time - start_time):.1f}")
    print(f"  Cache hit rate: {cache_hit_rate:.1f}% ({total_hits}/{total_cache_requests})")

    return {
        'total_operations': total_operations,
        'total_time_seconds': end_time - start_time,
        'average_time_ms': statistics.mean(all_times),
        'max_time_ms': max(all_times),
        'ops_per_second': total_operations / (end_time - start_time),
        'cache_hit_rate': cache_hit_rate,
        'total_cache_hits': total_hits,
        'total_cache_misses': total_misses
    }

if __name__ == "__main__":
    async def main():
        results = await run_comprehensive_benchmark()

        # Optional stress test
        if input("\nRun stress test? (y/N): ").lower().startswith('y'):
            wma = WorkingMemoryAssistant()
            await wma.initialize()
            stress_results = await run_stress_test(wma, concurrent_users=3)
            print(f"\n🔥 Stress test results: {stress_results}")

        print(f"\n🎯 Final Result: {'✅ SUCCESS - All performance targets met!' if results['all_targets_met'] else '❌ FAILURE - Performance targets not met'}")

    asyncio.run(main())