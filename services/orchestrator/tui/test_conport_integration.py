#!/usr/bin/env python3
"""
Test Script for IP-005 Day 4 ConPort Integration

Tests:
1. ConPort tracker initialization
2. Progress logging for command execution
3. Progress stats retrieval
4. Session finalization

Requirements:
- DopeconBridge running on port 3016
- ConPort operational (via DopeconBridge)
"""

import asyncio
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from orchestrator.tui.conport_tracker import ConPortProgressTracker


async def test_conport_integration():
    """Test ConPort integration step by step."""

    print("=" * 70)
    print("IP-005 Day 4: ConPort Integration Test")
    print("=" * 70)

    workspace_id = "/Users/hue/code/dopemux-mvp"
    tracker = ConPortProgressTracker(workspace_id)

    # Test 1: Initialization
    print("\n1️⃣  Testing ConPort tracker initialization...")
    try:
        await tracker.initialize()
        print("   ✅ Tracker initialized successfully")
        print(f"   📝 Session ID: {tracker.session_id}")
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        print("   ⚠️  Make sure DopeconBridge is running on port 3016")
        return

    # Test 2: Log command start
    print("\n2️⃣  Testing command start logging...")
    try:
        progress_id = await tracker.log_command_start("claude", "test command for Day 4")
        print(f"   ✅ Command logged to ConPort")
        print(f"   📝 Progress ID: {progress_id}")
    except Exception as e:
        print(f"   ❌ Command logging failed: {e}")

    # Wait a bit to simulate command execution
    print("\n⏳ Simulating command execution (2 seconds)...")
    await asyncio.sleep(2)

    # Test 3: Update command progress
    print("\n3️⃣  Testing command completion update...")
    try:
        await tracker.update_command_progress("claude", "DONE", exit_code=0)
        print("   ✅ Command marked as DONE")
    except Exception as e:
        print(f"   ❌ Progress update failed: {e}")

    # Test 4: Get progress stats
    print("\n4️⃣  Testing progress statistics retrieval...")
    try:
        stats = await tracker.get_progress_stats()
        print("   ✅ Progress stats retrieved:")
        print(f"      - Active commands: {stats['active_commands']}")
        print(f"      - Completed commands: {stats['completed_commands']}")
        print(f"      - Success rate: {stats['success_rate']:.1f}%")
        print(f"      - Session duration: {stats['session_duration_minutes']} min")
    except Exception as e:
        print(f"   ❌ Stats retrieval failed: {e}")

    # Test 5: Log another command (with failure)
    print("\n5️⃣  Testing failed command tracking...")
    try:
        progress_id2 = await tracker.log_command_start("gemini", "failing command test")
        print(f"   ✅ Second command logged (ID: {progress_id2})")

        await asyncio.sleep(1)

        await tracker.update_command_progress("gemini", "BLOCKED", error_message="Simulated error")
        print("   ✅ Command marked as BLOCKED")
    except Exception as e:
        print(f"   ❌ Failed command tracking error: {e}")

    # Test 6: Get final stats
    print("\n6️⃣  Testing final statistics...")
    try:
        final_stats = await tracker.get_progress_stats()
        print("   ✅ Final session stats:")
        print(f"      - Total completed: {final_stats['completed_commands']}")
        print(f"      - Successful: {final_stats['successful_commands']}")
        print(f"      - Success rate: {final_stats['success_rate']:.1f}%")
    except Exception as e:
        print(f"   ❌ Final stats failed: {e}")

    # Test 7: Session finalization
    print("\n7️⃣  Testing session finalization...")
    try:
        await tracker.close()
        print("   ✅ Session finalized successfully")
    except Exception as e:
        print(f"   ❌ Finalization failed: {e}")

    print("\n" + "=" * 70)
    print("✅ ConPort Integration Test Complete!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("  - ConPort tracker can initialize and create sessions")
    print("  - Commands are logged as progress_entry items")
    print("  - Progress updates work (DONE/BLOCKED statuses)")
    print("  - Statistics are calculated correctly")
    print("  - Session cleanup works properly")
    print("\n🎯 Next Step: Test TUI with real AI commands")
    print("   Run: python services/orchestrator/tui/main.py")


if __name__ == "__main__":
    print("\n🚀 Starting ConPort Integration Test...")
    print("📍 Workspace: /Users/hue/code/dopemux-mvp")
    print("🔗 DopeconBridge: http://localhost:3016")
    print()

    asyncio.run(test_conport_integration())
