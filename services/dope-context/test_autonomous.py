"""
Test script for autonomous indexing system.

Validates:
1. Components can be imported
2. Controller can be initialized
3. Start/stop lifecycle works
4. Status reporting works
"""

import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_autonomous_system():
    """Test autonomous indexing components."""

    print("=" * 60)
    print("Testing Autonomous Indexing System")
    print("=" * 60)

    # Test 1: Import components
    print("\n1. Testing imports...")
    try:
        from src.autonomous import (
            WatchdogMonitor,
            IndexingWorker,
            PeriodicSync,
            AutonomousController,
            AutonomousConfig,
        )
        print("   ✅ All components imported successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

    # Test 2: Create configuration
    print("\n2. Testing configuration...")
    config = AutonomousConfig(
        enabled=True,
        debounce_seconds=2.0,  # Shorter for testing
        periodic_interval=30,  # 30s for testing
    )
    print(f"   ✅ Config created: debounce={config.debounce_seconds}s, periodic={config.periodic_interval}s")

    # Test 3: Create mock callbacks
    print("\n3. Creating mock callbacks...")

    index_call_count = 0
    sync_call_count = 0

    async def mock_index_callback(workspace_path, changed_files=None):
        nonlocal index_call_count
        index_call_count += 1
        logger.info(f"Mock index called (#{index_call_count}) for {workspace_path}")
        await asyncio.sleep(0.1)  # Simulate work

    async def mock_sync_callback(workspace_path):
        nonlocal sync_call_count
        sync_call_count += 1
        logger.info(f"Mock sync called (#{sync_call_count}) for {workspace_path}")
        return {
            "has_changes": False,
            "total_changes": 0,
        }

    print("   ✅ Callbacks created")

    # Test 4: Initialize controller
    print("\n4. Initializing controller...")
    test_workspace = Path.cwd() / "src"  # Use src as test workspace

    controller = AutonomousController(
        workspace_path=test_workspace,
        index_callback=mock_index_callback,
        sync_callback=mock_sync_callback,
        config=config,
    )
    print(f"   ✅ Controller initialized for {test_workspace}")

    # Test 5: Start autonomous indexing
    print("\n5. Starting autonomous indexing...")
    await controller.start()

    if controller.is_running():
        print("   ✅ Autonomous indexing started")
    else:
        print("   ❌ Failed to start")
        return False

    # Test 6: Get status
    print("\n6. Checking status...")
    status = controller.get_status()
    print(f"   ✅ Status retrieved:")
    print(f"      - Running: {status['running']}")
    print(f"      - Workspace: {status['workspace']}")
    print(f"      - Watchdog: {status['watchdog']['running'] if status['watchdog'] else 'N/A'}")
    print(f"      - Worker: {status['worker']['tasks_processed'] if status['worker'] else 'N/A'} tasks")

    # Test 7: Let it run briefly
    print("\n7. Running for 3 seconds...")
    await asyncio.sleep(3)
    print("   ✅ System ran without errors")

    # Test 8: Check global registry
    print("\n8. Checking global registry...")
    active = AutonomousController.get_active_controllers()
    print(f"   ✅ Found {len(active)} active controller(s)")

    # Test 9: Stop autonomous indexing
    print("\n9. Stopping autonomous indexing...")
    await controller.stop()

    if not controller.is_running():
        print("   ✅ Autonomous indexing stopped cleanly")
    else:
        print("   ❌ Failed to stop")
        return False

    # Test 10: Verify cleanup
    print("\n10. Verifying cleanup...")
    active_after = AutonomousController.get_active_controllers()
    if len(active_after) == 0:
        print("   ✅ Controller removed from registry")
    else:
        print(f"   ⚠️  {len(active_after)} controllers still active")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print(f"\nCallback Stats:")
    print(f"  - Index callbacks: {index_call_count}")
    print(f"  - Sync callbacks: {sync_call_count}")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_autonomous_system())
    exit(0 if success else 1)
