"""
Week 6: TwoPlaneOrchestrator Integration Tests

Tests cross-plane routing with real REST endpoints (week6_test_server.py)
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from two_plane_orchestrator import TwoPlaneOrchestrator, Plane

async def test_cognitive_to_pm_query():
    """Test 1: Cognitive → PM (get_tasks query)"""
    print("\n" + "="*70)
    print("Test 1: Cognitive → PM (Get Tasks)")
    print("="*70)

    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3017",  # Week 6 test server
        strict_mode=False
    )

    await orchestrator.initialize()

    response = await orchestrator.cognitive_to_pm(
        operation="get_tasks",
        data={"status": "TODO"},
        requester="MemoryAgent"
    )

    print(f"\nResponse: {response}")
    assert response["success"] is True, "Request should succeed"
    assert "tasks" in response["data"], "Should return tasks"
    assert response["data"]["source"] == "pm_plane", "Should come from PM plane"
    print("✅ Test passed!")

    await orchestrator.close()

async def test_pm_to_cognitive_query():
    """Test 2: PM → Cognitive (get_complexity query)"""
    print("\n" + "="*70)
    print("Test 2: PM → Cognitive (Get Complexity)")
    print("="*70)

    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3017",
        strict_mode=False
    )

    await orchestrator.initialize()

    response = await orchestrator.pm_to_cognitive(
        operation="get_complexity",
        data={"file": "auth.py", "function": "login"},
        requester="Leantime"
    )

    print(f"\nResponse: {response}")
    assert response["success"] is True, "Request should succeed"
    assert "complexity" in response["data"], "Should return complexity"
    assert response["data"]["source"] == "cognitive_plane", "Should come from Cognitive plane"
    print("✅ Test passed!")

    await orchestrator.close()

async def test_pm_to_cognitive_adhd():
    """Test 3: PM → Cognitive (get_adhd_state query)"""
    print("\n" + "="*70)
    print("Test 3: PM → Cognitive (Get ADHD State)")
    print("="*70)

    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3017",
        strict_mode=False
    )

    await orchestrator.initialize()

    response = await orchestrator.pm_to_cognitive(
        operation="get_adhd_state",
        data={},
        requester="Leantime"
    )

    print(f"\nResponse: {response}")
    assert response["success"] is True, "Request should succeed"
    assert "energy" in response["data"], "Should return energy level"
    assert "attention" in response["data"], "Should return attention state"
    assert "cognitive_load" in response["data"], "Should return cognitive load"
    print("✅ Test passed!")

    await orchestrator.close()

async def test_authority_metrics():
    """Test 4: Metrics and compliance tracking"""
    print("\n" + "="*70)
    print("Test 4: Authority Metrics")
    print("="*70)

    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3017",
        strict_mode=False
    )

    await orchestrator.initialize()

    # Make a few requests
    await orchestrator.cognitive_to_pm("get_tasks", {}, "test")
    await orchestrator.pm_to_cognitive("get_complexity", {}, "test")

    # Get compliance report
    report = await orchestrator.get_authority_compliance_report()

    print(f"\nCompliance Report:")
    print(f"  Total Requests: {report['total_requests']}")
    print(f"  Successful Routes: {report['successful_routes']}")
    print(f"  Compliance Rate: {report['compliance_rate']:.1f}%")

    assert report['total_requests'] == 2, "Should have 2 requests"
    assert report['successful_routes'] == 2, "Should have 2 successful"
    print("✅ Test passed!")

    await orchestrator.close()

async def test_authority_violation_warn_mode():
    """Test 5: Authority violation in warn mode (allows with warning)"""
    print("\n" + "="*70)
    print("Test 5: Authority Violation (Warn Mode)")
    print("="*70)

    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3017",
        strict_mode=False  # Warn only, don't block
    )

    await orchestrator.initialize()

    # PM tries to write to decisions (authority violation)
    response = await orchestrator.pm_to_cognitive(
        operation="update_decision",  # WRITE operation
        data={"decision_id": "123", "status": "approved"},
        requester="Leantime"
    )

    print(f"\nResponse: {response}")
    print(f"Metrics: Violations = {orchestrator.metrics['authority_violations']}")

    # Should succeed but log violation
    assert response["success"] is True, "Request should proceed in warn mode"
    assert orchestrator.metrics["authority_violations"] == 1, "Should track violation"
    print("✅ Test passed! Violation logged but request proceeded")

    await orchestrator.close()

async def test_authority_violation_strict_mode():
    """Test 6: Authority violation in strict mode (blocks)"""
    print("\n" + "="*70)
    print("Test 6: Authority Violation (Strict Mode)")
    print("="*70)

    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3017",
        strict_mode=True  # BLOCK violations
    )

    await orchestrator.initialize()

    # PM tries to write to decisions (authority violation)
    try:
        response = await orchestrator.pm_to_cognitive(
            operation="update_decision",  # WRITE operation
            data={"decision_id": "123", "status": "approved"},
            requester="Leantime"
        )
        print(f"❌ Should have raised ValueError!")
        assert False, "Should have blocked the violation"

    except ValueError as e:
        print(f"\n🚫 Correctly blocked: {e}")
        print(f"Metrics: Violations = {orchestrator.metrics['authority_violations']}")
        assert "Authority violation" in str(e), "Should raise authority violation error"
        assert orchestrator.metrics["authority_violations"] == 1, "Should track violation"
        print("✅ Test passed! Violation blocked in strict mode")

    await orchestrator.close()

async def test_health_check():
    """Test 7: Health check functionality"""
    print("\n" + "="*70)
    print("Test 7: Health Check")
    print("="*70)

    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3017",
        strict_mode=False
    )

    await orchestrator.initialize()

    health = await orchestrator.health_check()

    print(f"\nHealth Status:")
    print(f"  Orchestrator: {health['orchestrator']}")
    print(f"  Bridge Connected: {health['bridge_connected']}")
    print(f"  Bridge Status: {health['bridge_status']}")
    print(f"  Authority Rules: {health['authority_rules']}")

    assert health["orchestrator"] == "healthy", "Orchestrator should be healthy"
    assert health["bridge_connected"] is True, "Bridge should be connected"
    assert health["authority_rules"] == 5, "Should have 5 authority rules"
    print("✅ Test passed!")

    await orchestrator.close()

async def test_metrics_summary():
    """Test 8: Metrics summary functionality"""
    print("\n" + "="*70)
    print("Test 8: Metrics Summary")
    print("="*70)

    orchestrator = TwoPlaneOrchestrator(
        workspace_id="/Users/hue/code/dopemux-mvp",
        bridge_url="http://localhost:3017",
        strict_mode=False
    )

    await orchestrator.initialize()

    # Make several requests
    await orchestrator.cognitive_to_pm("get_tasks", {}, "test1")
    await orchestrator.pm_to_cognitive("get_complexity", {}, "test2")
    await orchestrator.pm_to_cognitive("get_adhd_state", {}, "test3")

    summary = await orchestrator.get_metrics_summary()

    print(f"\nMetrics Summary:")
    print(f"  Total Requests: {summary['total_requests']}")
    print(f"  Success Rate: {summary['success_rate']}%")
    print(f"  Compliance Rate: {summary['compliance_rate']}%")
    print(f"  PM → Cognitive: {summary['request_patterns']['pm_to_cognitive']}")
    print(f"  Cognitive → PM: {summary['request_patterns']['cognitive_to_pm']}")

    assert summary['total_requests'] == 3, "Should have 3 requests"
    assert summary['success_rate'] == 100.0, "All should succeed"
    assert summary['request_patterns']['pm_to_cognitive'] == 2, "Should have 2 PM → Cognitive"
    assert summary['request_patterns']['cognitive_to_pm'] == 1, "Should have 1 Cognitive → PM"
    print("✅ Test passed!")

    await orchestrator.close()

async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("WEEK 6: TwoPlaneOrchestrator Integration Tests")
    print("="*70)
    print("\nPrerequisite: week6_test_server.py running on port 3017")

    tests = [
        ("Cognitive → PM Query", test_cognitive_to_pm_query),
        ("PM → Cognitive Complexity", test_pm_to_cognitive_query),
        ("PM → Cognitive ADHD State", test_pm_to_cognitive_adhd),
        ("Authority Metrics", test_authority_metrics),
        ("Authority Violation (Warn Mode)", test_authority_violation_warn_mode),
        ("Authority Violation (Strict Mode)", test_authority_violation_strict_mode),
        ("Health Check", test_health_check),
        ("Metrics Summary", test_metrics_summary),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ Test '{name}' failed: {e}")
            failed += 1

    print("\n" + "="*70)
    print(f"Test Results: {passed}/{len(tests)} passed")
    print("="*70)

    if failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
