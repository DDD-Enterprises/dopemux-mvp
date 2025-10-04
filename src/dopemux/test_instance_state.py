#!/usr/bin/env python3
"""
Test script for InstanceState persistence.

Demonstrates ConPort integration for instance crash recovery.
Gracefully handles ConPort unavailability.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dopemux.instance_state import (
    InstanceState,
    InstanceStateManager,
    save_instance_state_sync,
    load_instance_state_sync,
    list_all_instance_states_sync,
    cleanup_instance_state_sync,
)

def test_instance_state_persistence():
    """Test instance state save/load cycle."""

    workspace_id = "/Users/hue/code/dopemux-mvp"
    conport_port = 3007  # Instance A's ConPort

    print("🧪 Testing InstanceState Persistence")
    print("=" * 60)

    # Create test instance state
    test_state = InstanceState(
        instance_id="TEST",
        port_base=9999,
        worktree_path="/tmp/test-worktree",
        git_branch="test/persistence",
        created_at=datetime.now(),
        last_active=datetime.now(),
        status="active",
        last_working_directory="/tmp/test-worktree/src",
        last_focus_context="Testing instance persistence"
    )

    print(f"\n📝 Created test InstanceState:")
    print(f"   Instance ID: {test_state.instance_id}")
    print(f"   Port Base: {test_state.port_base}")
    print(f"   Branch: {test_state.git_branch}")
    print(f"   Status: {test_state.status}")

    # Test 1: Save instance state
    print(f"\n💾 Test 1: Saving instance state...")
    success = save_instance_state_sync(test_state, workspace_id, conport_port)
    if success:
        print("   ✅ Save successful!")
    else:
        print("   ⚠️ Save failed (ConPort might not be running)")
        print("   Tip: Start ConPort with 'dopemux start' in another terminal")

    # Test 2: Load instance state
    print(f"\n📖 Test 2: Loading instance state...")
    loaded_state = load_instance_state_sync("TEST", workspace_id, conport_port)
    if loaded_state:
        print("   ✅ Load successful!")
        print(f"   Instance ID: {loaded_state.instance_id}")
        print(f"   Status: {loaded_state.status}")
        print(f"   Branch: {loaded_state.git_branch}")
    else:
        print("   ⚠️ Load failed (state not found or ConPort unavailable)")

    # Test 3: List all instance states
    print(f"\n📋 Test 3: Listing all instance states...")
    all_states = list_all_instance_states_sync(workspace_id, conport_port)
    if all_states:
        print(f"   ✅ Found {len(all_states)} instance(s):")
        for state in all_states:
            print(f"      - {state.instance_id}: {state.status} on {state.git_branch}")
    else:
        print("   ⚠️ No instances found (or ConPort unavailable)")

    # Test 4: Cleanup test state
    print(f"\n🧹 Test 4: Cleaning up test state...")
    success = cleanup_instance_state_sync("TEST", workspace_id, conport_port)
    if success:
        print("   ✅ Cleanup successful!")
    else:
        print("   ⚠️ Cleanup failed (or already cleaned)")

    # Test 5: Verify cleanup
    print(f"\n🔍 Test 5: Verifying cleanup...")
    loaded_state = load_instance_state_sync("TEST", workspace_id, conport_port)
    if loaded_state is None:
        print("   ✅ State successfully removed!")
    else:
        print("   ❌ State still exists (cleanup may have failed)")

    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("\nNote: If ConPort is not running, all operations will fail gracefully.")
    print("Start ConPort with: dopemux start")


def test_async_usage():
    """Demonstrate async API usage pattern."""
    import asyncio

    print("\n\n🔄 Testing Async API Usage")
    print("=" * 60)

    workspace_id = "/Users/hue/code/dopemux-mvp"

    async def async_test():
        manager = InstanceStateManager(workspace_id, conport_port=3007)

        try:
            # Create test state
            test_state = InstanceState(
                instance_id="ASYNC_TEST",
                port_base=8888,
                worktree_path="/tmp/async-test",
                git_branch="test/async",
                created_at=datetime.now(),
                last_active=datetime.now(),
                status="active"
            )

            print("\n💾 Saving state (async)...")
            saved = await manager.save_instance_state(test_state)
            print(f"   Result: {'✅ Success' if saved else '⚠️ Failed'}")

            print("\n📖 Loading state (async)...")
            loaded = await manager.load_instance_state("ASYNC_TEST")
            print(f"   Result: {'✅ Found' if loaded else '⚠️ Not found'}")

            print("\n📋 Listing states (async)...")
            all_states = await manager.list_all_instance_states()
            print(f"   Result: Found {len(all_states)} instance(s)")

            print("\n🧹 Cleaning up (async)...")
            cleaned = await manager.cleanup_instance_state("ASYNC_TEST")
            print(f"   Result: {'✅ Success' if cleaned else '⚠️ Failed'}")

        finally:
            await manager._close_session()

    asyncio.run(async_test())
    print("\n✅ Async tests completed!")


if __name__ == "__main__":
    test_instance_state_persistence()
    test_async_usage()
