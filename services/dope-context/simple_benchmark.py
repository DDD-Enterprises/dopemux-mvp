"""Simple performance benchmark using indexed data."""
import asyncio
import time
import statistics
from src.search.dense_search import MultiVectorSearch, SearchProfile

async def benchmark_search_only():
    """Benchmark search performance on indexed data."""
    print("🔍 dope-context Search Performance")
    print("=" * 70)
    
    search = MultiVectorSearch(collection_name='dopemux_source')
    
    # Use fixed test vectors (already indexed data)
    test_vec = [0.1] * 1024
    profiles = [
        ('implementation', SearchProfile.implementation()),
        ('debugging', SearchProfile.debugging()),
        ('exploration', SearchProfile.exploration())
    ]
    
    print("\n📊 Search Latency by Profile:")
    print("-" * 70)
    
    all_times = []
    
    for profile_name, profile in profiles:
        times = []
        for _ in range(5):
            start = time.time()
            results = await search.search(
                query_content_vector=test_vec,
                query_title_vector=test_vec,
                query_breadcrumb_vector=test_vec,
                profile=profile
            )
            times.append((time.time() - start) * 1000)
        
        avg = statistics.mean(times)
        all_times.extend(times)
        
        print(f"\n{profile_name.upper()}:")
        print(f"  Min: {min(times):.1f}ms")
        print(f"  Avg: {avg:.1f}ms")
        print(f"  Max: {max(times):.1f}ms")
        print(f"  Results: {len(results)}")
        print(f"  Status: {'✅ PASS' if avg < 500 else '⚠️ SLOW'}")
    
    # Overall stats
    overall_avg = statistics.mean(all_times)
    print(f"\n{'=' * 70}")
    print(f"OVERALL PERFORMANCE")
    print(f"{'=' * 70}")
    print(f"Average: {overall_avg:.1f}ms")
    print(f"P50: {statistics.median(all_times):.1f}ms")
    print(f"P95: {sorted(all_times)[int(len(all_times)*0.95)]:.1f}ms")
    print(f"Target: <500ms → {'✅ PASS' if overall_avg < 500 else '❌ FAIL'}")
    
    # Collection info
    info = await search.get_collection_info()
    print(f"\n📊 Collection: {info['name']}")
    print(f"   Vectors: {info['vectors_count']}")
    print(f"   Status: {info['status']}")

asyncio.run(benchmark_search_only())
