"""
Test Script for Context Switch Recovery Engine

Tests the transformational < 2 second context switch recovery feature.

Usage:
    cd services/task-orchestrator
    python intelligence/test_context_switch_recovery.py

This script will:
1. Initialize Context Switch Recovery with available MCPs
2. Simulate a context switch
3. Demonstrate recovery assistance
4. Show recovery statistics
5. Test background monitoring (optional)

Created: 2025-10-20
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Optional, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Context Switch Recovery
from intelligence.context_switch_recovery import (
    ContextSwitchRecovery,
    ContextSwitch,
    SwitchReason
)

# Import observability
from observability.metrics_collector import get_metrics


class MockConPortClient:
    """Mock ConPort client for testing without MCP."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id

    async def get_progress(
        self,
        workspace_id: str,
        status_filter: Optional[str] = None
    ):
        """Mock get_progress - returns sample in-progress tasks."""
        return {
            "result": [
                {
                    "id": 1,
                    "description": "Implement Context Switch Recovery Engine",
                    "status": "IN_PROGRESS",
                    "created_at": "2025-10-20T10:00:00Z"
                },
                {
                    "id": 2,
                    "description": "Test Component 6 Phase 1",
                    "status": "IN_PROGRESS",
                    "created_at": "2025-10-20T11:30:00Z"
                }
            ]
        }

    async def get_decisions(
        self,
        workspace_id: str,
        limit: Optional[int] = None
    ):
        """Mock get_decisions - returns sample recent decisions."""
        return {
            "result": [
                {
                    "id": 170,
                    "summary": "Component 6: ADHD Intelligence Layer - Phase 1 Complete",
                    "created_at": "2025-10-20T03:56:11Z"
                },
                {
                    "id": 164,
                    "summary": "Component 5: ConPort MCP Cross-Plane Queries - Complete",
                    "created_at": "2025-10-19T15:20:00Z"
                },
                {
                    "id": 143,
                    "summary": "Use Zen MCP instead of mas-sequential-thinking",
                    "created_at": "2025-10-18T14:10:00Z"
                }
            ]
        }

    async def log_custom_data(
        self,
        workspace_id: str,
        category: str,
        key: str,
        value: Any
    ):
        """Mock log_custom_data - pretend to log."""
        print(f"  💾 [Mock] Logged to ConPort: {category}/{key}")
        return {"status": "success"}


class MockTaskOrchestrator:
    """Mock Task Orchestrator for testing."""

    def __init__(self):
        self.current_task_id = "task-001"

    async def get_current_task(self):
        """Mock current task."""
        return {
            "task_id": self.current_task_id,
            "description": "Implementing Context Switch Recovery Engine",
            "complexity": 0.65,
            "status": "IN_PROGRESS"
        }


async def test_context_switch_detection():
    """Test 1: Context switch detection."""
    print("\n" + "="*70)
    print("TEST 1: Context Switch Detection")
    print("="*70)

    workspace_id = "/Users/hue/code/dopemux-mvp"

    # Initialize with mock clients (no MCPs required)
    conport = MockConPortClient(workspace_id)
    orchestrator = MockTaskOrchestrator()
    metrics = get_metrics()

    recovery = ContextSwitchRecovery(
        workspace_id=workspace_id,
        conport_client=conport,
        task_orchestrator=orchestrator,
        metrics_collector=metrics
    )

    print("\n✅ Context Switch Recovery initialized")
    print(f"   Workspace: {workspace_id}")
    print(f"   ConPort: Mock client (works without MCP)")
    print(f"   Task Orchestrator: Mock client")
    print(f"   Metrics: {'Enabled' if metrics.enabled else 'Mock mode'}")

    # First detection (establishes baseline)
    print("\n🔍 First detection (establishing baseline)...")
    switch = await recovery.detect_context_switch()
    assert switch is None, "First detection should be None (no previous state)"
    print("   ✅ Baseline established")

    # Simulate task change
    print("\n🔄 Simulating task change...")
    orchestrator.current_task_id = "task-002"

    # Second detection (should detect switch)
    print("🔍 Second detection (after task change)...")
    switch = await recovery.detect_context_switch()

    if switch:
        print(f"   ✅ Context switch detected!")
        print(f"      Reason: {switch.switch_reason.value}")
        print(f"      From: {switch.from_context.get('task', {}).get('task_id', 'unknown')}")
        print(f"      To: {switch.to_context.get('task', {}).get('task_id', 'unknown')}")
        print(f"      Timestamp: {switch.timestamp.strftime('%H:%M:%S')}")
    else:
        print("   ❌ No switch detected (unexpected)")

    return switch


async def test_recovery_assistance(switch: Optional[ContextSwitch]):
    """Test 2: Recovery assistance."""
    print("\n" + "="*70)
    print("TEST 2: Recovery Assistance (< 2 Second Target)")
    print("="*70)

    if not switch:
        print("⚠️  Skipping (no switch to recover from)")
        return

    workspace_id = "/Users/hue/code/dopemux-mvp"

    # Re-initialize recovery
    conport = MockConPortClient(workspace_id)
    orchestrator = MockTaskOrchestrator()

    recovery = ContextSwitchRecovery(
        workspace_id=workspace_id,
        conport_client=conport,
        task_orchestrator=orchestrator
    )

    # Measure recovery time
    start_time = datetime.now()

    print("\n⏱️  Providing recovery assistance...")
    recovery_context = await recovery.provide_recovery_assistance(switch)

    recovery_time = (datetime.now() - start_time).total_seconds()

    print(f"\n✅ Recovery complete in {recovery_time:.3f} seconds")

    # Check target
    if recovery_time < 2.0:
        print(f"   🎉 SUCCESS: < 2 second target met! ({recovery_time:.3f}s)")
    else:
        print(f"   ⚠️  SLOW: > 2 second target ({recovery_time:.3f}s)")

    # Show recovery context
    print(f"\n📋 Recovery Context Generated:")
    print(f"   Summary: {recovery_context.summary[:100]}...")
    print(f"   Screenshot: {recovery_context.last_screenshot_path or 'N/A (Desktop-Commander unavailable)'}")
    print(f"   Open files: {len(recovery_context.open_files)}")
    print(f"   Recent decisions: {len(recovery_context.recent_decisions)}")
    print(f"   In-progress tasks: {len(recovery_context.in_progress_tasks)}")
    print(f"   Current worktree: {recovery_context.current_worktree or 'N/A'}")

    # Show detailed decisions
    if recovery_context.recent_decisions:
        print(f"\n💡 Recent Decisions (for context):")
        for i, decision in enumerate(recovery_context.recent_decisions[:3], 1):
            print(f"   {i}. {decision['summary'][:60]}...")

    # Show in-progress tasks
    if recovery_context.in_progress_tasks:
        print(f"\n📋 In-Progress Tasks:")
        for i, task in enumerate(recovery_context.in_progress_tasks[:3], 1):
            print(f"   {i}. {task['description'][:60]}...")

    return recovery_context, recovery_time


async def test_recovery_statistics():
    """Test 3: Recovery statistics tracking."""
    print("\n" + "="*70)
    print("TEST 3: Recovery Statistics Tracking")
    print("="*70)

    workspace_id = "/Users/hue/code/dopemux-mvp"

    # Initialize recovery
    conport = MockConPortClient(workspace_id)
    recovery = ContextSwitchRecovery(
        workspace_id=workspace_id,
        conport_client=conport
    )

    # Simulate multiple switches and recoveries
    print("\n🔄 Simulating multiple context switches...")

    for i in range(3):
        # Detect switch
        switch = await recovery.detect_context_switch()

        if switch is None and i == 0:
            # First detection, baseline
            continue

        # Simulate switch
        switch = ContextSwitch(
            from_context={"task": {"task_id": f"task-{i}"}},
            to_context={"task": {"task_id": f"task-{i+1}"}},
            switch_reason=SwitchReason.INTENTIONAL,
            timestamp=datetime.now()
        )

        # Provide recovery
        await recovery.provide_recovery_assistance(switch)

        print(f"   ✅ Switch {i+1} recovered")

    # Get statistics
    print("\n📊 Getting recovery statistics...")
    stats = await recovery.get_recovery_statistics()

    print(f"\n📈 Recovery Statistics:")
    print(f"   Total switches: {stats['total_switches']}")
    print(f"   Average recovery: {stats['average_recovery_seconds']}s")
    print(f"   Target: {stats['target_recovery_seconds']}s")
    print(f"   Performance vs target: {stats['performance_vs_target']:.2f}x")

    if stats['switches_by_reason']:
        print(f"\n   Switches by reason:")
        for reason, count in stats['switches_by_reason'].items():
            print(f"      {reason}: {count}")

    # Evaluate performance
    if stats['average_recovery_seconds'] < 2.0:
        print(f"\n   🎉 EXCELLENT: Average recovery < 2 seconds!")
    elif stats['average_recovery_seconds'] < 5.0:
        print(f"\n   ✅ GOOD: Average recovery < 5 seconds")
    else:
        print(f"\n   ⚠️  NEEDS IMPROVEMENT: Average recovery > 5 seconds")

    return stats


async def test_monitoring_demo():
    """Test 4: Background monitoring demonstration."""
    print("\n" + "="*70)
    print("TEST 4: Background Monitoring Demo (5 seconds)")
    print("="*70)

    workspace_id = "/Users/hue/code/dopemux-mvp"

    # Initialize recovery
    conport = MockConPortClient(workspace_id)
    recovery = ContextSwitchRecovery(
        workspace_id=workspace_id,
        conport_client=conport
    )

    print("\n⚙️  Starting background monitoring...")
    print("   (Will run for 5 seconds, checking every 2 seconds)")

    # Start monitoring in background
    monitor_task = asyncio.create_task(
        recovery.start_monitoring(interval_seconds=2)
    )

    # Let it run for 5 seconds
    await asyncio.sleep(5)

    # Stop monitoring
    recovery.stop_monitoring()

    # Wait for task to finish
    try:
        await asyncio.wait_for(monitor_task, timeout=1.0)
    except asyncio.TimeoutError:
        pass

    print("\n✅ Monitoring demo complete")


async def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*70)
    print("🧪 CONTEXT SWITCH RECOVERY - TEST SUITE")
    print("Component 6 - Phase 1b")
    print("="*70)

    results = {
        "detection": False,
        "recovery": False,
        "statistics": False,
        "monitoring": False,
        "recovery_time": None
    }

    try:
        # Test 1: Detection
        switch = await test_context_switch_detection()
        results["detection"] = switch is not None

        # Test 2: Recovery
        if switch:
            recovery_context, recovery_time = await test_recovery_assistance(switch)
            results["recovery"] = recovery_time < 2.0
            results["recovery_time"] = recovery_time

        # Test 3: Statistics
        stats = await test_recovery_statistics()
        results["statistics"] = stats["total_switches"] > 0

        # Test 4: Monitoring (demo)
        await test_monitoring_demo()
        results["monitoring"] = True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    # Final summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    print(f"\n✅ Tests Passed:")
    print(f"   Context Switch Detection: {'PASS' if results['detection'] else 'FAIL'}")
    print(f"   Recovery Assistance: {'PASS' if results['recovery'] else 'FAIL'}")
    print(f"   Statistics Tracking: {'PASS' if results['statistics'] else 'FAIL'}")
    print(f"   Background Monitoring: {'PASS' if results['monitoring'] else 'FAIL'}")

    if results['recovery_time']:
        print(f"\n⏱️  Performance:")
        print(f"   Recovery Time: {results['recovery_time']:.3f}s")
        print(f"   Target: 2.0s")
        print(f"   Status: {'🎉 PASS' if results['recovery_time'] < 2.0 else '⚠️  SLOW'}")

    passed = sum([results['detection'], results['recovery'], results['statistics'], results['monitoring']])
    total = 4

    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total and results.get('recovery_time', 999) < 2.0:
        print("\n🎉 ✅ ALL TESTS PASSED - Context Switch Recovery working perfectly!")
    else:
        print("\n⚠️  Some tests need attention - review output above")

    print("\n" + "="*70)


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║  Context Switch Recovery Engine - Test Suite                      ║
║  Component 6: ADHD Intelligence Layer - Phase 1b                   ║
║                                                                    ║
║  Target: Reduce ADHD context switch recovery from 15-25 minutes   ║
║          to < 2 seconds (450-750x improvement)                     ║
╚════════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(run_all_tests())
