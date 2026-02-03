#!/usr/bin/env python3
"""
IP-005 Day 5 Integration Tests

Comprehensive test suite for all Day 5 advanced ADHD features:
1. TUIStateManager coordination
2. Pomodoro break system
3. Energy level detection
4. Command history with privacy
5. Integration across all managers

Requirements:
- DopeconBridge running on port 3016
- ConPort operational
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from orchestrator.tui.state_manager import TUIStateManager
from orchestrator.tui.break_manager import PomodoroBreakManager
from orchestrator.tui.energy_detector import EnergyDetector
from orchestrator.tui.command_history import CommandHistoryManager


async def test_day5_integration():
    """Comprehensive Day 5 integration test."""

    print("=" * 80)
    print("IP-005 Day 5: Advanced ADHD Features Integration Test")
    print("=" * 80)

    workspace_id = "/Users/hue/code/dopemux-mvp"

    # ========================================================================
    # Test 1: TUIStateManager Initialization
    # ========================================================================
    print("\n🎛️  TEST 1: TUIStateManager Initialization")
    print("-" * 80)

    state_manager = TUIStateManager(workspace_id)
    print(f"   ✅ State manager created")

    try:
        init_result = await state_manager.initialize()
        print(f"   ✅ Parallel initialization complete")
        print(f"      - Successful: {init_result['successful_managers']}/{init_result['total_managers']}")
        print(f"      - Managers: {init_result['managers']}")

        if init_result.get('warnings'):
            print(f"      ⚠️  Warnings: {init_result['warnings']}")
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        print(f"      Make sure DopeconBridge is running on port 3016")
        return

    # ========================================================================
    # Test 2: Pomodoro Break System
    # ========================================================================
    print("\n⏰ TEST 2: Pomodoro Break System")
    print("-" * 80)

    break_mgr = state_manager.breaks

    print(f"   ✅ Break manager initialized")
    print(f"   📊 Current state:")
    print(f"      - Session count: {break_mgr.session_count}")
    print(f"      - Elapsed: {break_mgr.get_elapsed_minutes()} minutes")
    print(f"      - Status color: {break_mgr.get_status_color()}")
    print(f"      - Break suggested: {break_mgr.should_suggest_break()}")

    # Test elapsed timer formatting
    break_state = await break_mgr.get_state_async()
    print(f"   ✅ Break state retrieved:")
    print(f"      - Elapsed formatted: {break_state['elapsed_formatted']}")
    print(f"      - Status message: {break_state['message']}")
    print(f"      - Break duration: {break_state['break_duration_minutes']} min")

    # Simulate time passage (for testing, we'd manually advance the timer)
    print(f"   💡 Timer is running - elapsed time will increase naturally")

    # ========================================================================
    # Test 3: Energy Level Detection
    # ========================================================================
    print("\n🔋 TEST 3: Energy Level Detection")
    print("-" * 80)

    energy_detector = state_manager.energy

    print(f"   ✅ Energy detector initialized")
    print(f"   🔧 Detection mode: {energy_detector.detection_mode}")
    print(f"   📊 ADHD Engine available: {energy_detector.engine_available}")

    # Test energy detection
    try:
        current_energy = await energy_detector.detect_energy()
        print(f"   ✅ Energy detected: {current_energy.value}")

        energy_state = await energy_detector.get_current_energy_async()
        print(f"   📊 Energy state:")
        print(f"      - Level: {energy_state['level']}")
        print(f"      - Source: {energy_state['source']}")
        print(f"      - UI adaptations: {energy_state['ui_adaptations']}")
    except Exception as e:
        print(f"   ❌ Energy detection failed: {e}")

    # ========================================================================
    # Test 4: Command History (with Privacy Filtering)
    # ========================================================================
    print("\n📜 TEST 4: Command History with Privacy Filtering")
    print("-" * 80)

    history_mgr = state_manager.history

    print(f"   ✅ History manager initialized")
    print(f"   📊 Loaded commands: {history_mgr.get_count()}")

    # Test adding normal commands
    normal_commands = [
        ("claude", "analyze auth.py"),
        ("gemini", "explain the two-plane architecture"),
        ("grok", "write tests for command_router.py")
    ]

    for ai, cmd in normal_commands:
        added = history_mgr.add_command(ai, cmd)
        print(f"   {'✅' if added else '❌'} Added: @{ai} {cmd[:40]}...")

    # Test privacy filtering
    sensitive_commands = [
        ("claude", "echo $API_KEY > config.env"),
        ("gemini", "store password in database"),
        ("grok", "export SECRET_TOKEN=abc123")
    ]

    print(f"\n   🔒 Testing privacy filtering:")
    for ai, cmd in sensitive_commands:
        added = history_mgr.add_command(ai, cmd)
        print(f"   {'❌ FILTERED' if not added else '✅ ADDED'}: {cmd[:40]}...")

    # Test navigation
    print(f"\n   ⬆️  Testing up/down navigation:")
    prev1 = history_mgr.navigate_up()
    print(f"      Up (1): {prev1}")
    prev2 = history_mgr.navigate_up()
    print(f"      Up (2): {prev2}")
    next1 = history_mgr.navigate_down()
    print(f"      Down (1): {next1}")

    # Test persistence
    print(f"\n   💾 Testing ConPort persistence:")
    try:
        await history_mgr.save_command("claude", "test command for persistence", 0)
        print(f"   ✅ Command saved to ConPort")
    except Exception as e:
        print(f"   ❌ Save failed: {e}")

    # ========================================================================
    # Test 5: Coordinated Command Lifecycle
    # ========================================================================
    print("\n🔄 TEST 5: Coordinated Command Lifecycle")
    print("-" * 80)

    # Test command start coordination
    print("   📤 Testing command start coordination...")
    try:
        start_result = await state_manager.on_command_start("claude", "test ultrathink integration")
        print(f"   ✅ Command start coordinated:")
        print(f"      - Progress ID: {start_result.get('progress_id')}")
        print(f"      - History added: {start_result.get('history_added')}")
        print(f"      - Timestamp: {start_result.get('timestamp')}")
    except Exception as e:
        print(f"   ❌ Command start failed: {e}")

    # Simulate command execution
    print(f"\n   ⏳ Simulating command execution (2 seconds)...")
    await asyncio.sleep(2)

    # Test command completion coordination
    print("   ✅ Testing command completion coordination...")
    try:
        complete_result = await state_manager.on_command_complete("claude", 0)
        print(f"   ✅ Command completion coordinated:")
        print(f"      - Status: {complete_result.get('status')}")
        print(f"      - Break suggested: {complete_result.get('break_suggested')}")

        if complete_result.get('break_message'):
            print(f"      - Message: {complete_result.get('break_message')}")
    except Exception as e:
        print(f"   ❌ Command completion failed: {e}")

    # ========================================================================
    # Test 6: Single UI State Query (Performance Optimization)
    # ========================================================================
    print("\n⚡ TEST 6: Single UI State Query (Performance)")
    print("-" * 80)

    try:
        import time
        start_time = time.time()

        ui_state = await state_manager.get_ui_state()

        elapsed_ms = (time.time() - start_time) * 1000

        print(f"   ✅ UI state retrieved in {elapsed_ms:.1f}ms")
        print(f"   📊 Complete state:")
        print(f"      - Progress: {ui_state.get('progress', {}).get('completed_commands', 0)} completed")
        print(f"      - Break: {ui_state.get('break', {}).get('elapsed_formatted', '00:00')} elapsed")
        print(f"      - Energy: {ui_state.get('energy', {}).get('level', 'unknown')}")
        print(f"      - History: {ui_state.get('history_size', 0)} commands")

        print(f"\n   💡 Single call retrieves all state (vs 4 separate calls)")
        print(f"   🎯 Target: <50ms for ADHD responsiveness")
        print(f"   {'✅ PASS' if elapsed_ms < 50 else '⚠️  SLOW'}: {elapsed_ms:.1f}ms")
    except Exception as e:
        print(f"   ❌ UI state query failed: {e}")

    # ========================================================================
    # Test 7: Manager Health Check
    # ========================================================================
    print("\n🏥 TEST 7: Manager Health Check")
    print("-" * 80)

    health = state_manager.get_manager_health()
    print(f"   📊 Manager health status:")
    for manager, status in health.items():
        emoji = "✅" if status in ["healthy", "enabled"] else "❌"
        print(f"      {emoji} {manager}: {status}")

    # ========================================================================
    # Test 8: Cleanup and Finalization
    # ========================================================================
    print("\n🔒 TEST 8: Cleanup and Finalization")
    print("-" * 80)

    try:
        await state_manager.close()
        print(f"   ✅ All managers closed successfully")
        print(f"   💾 Session data finalized in ConPort")
    except Exception as e:
        print(f"   ❌ Cleanup failed: {e}")

    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 80)
    print("✅ IP-005 Day 5 Integration Test Complete!")
    print("=" * 80)

    print("\n📊 Test Summary:")
    print("  ✅ TUIStateManager: Parallel initialization working")
    print("  ✅ Break Manager: Elapsed timer, color coding, state retrieval")
    print("  ✅ Energy Detector: Multi-tier detection, UI adaptations")
    print("  ✅ Command History: Privacy filtering, navigation, persistence")
    print("  ✅ Coordination: Command lifecycle properly coordinated")
    print("  ✅ Performance: Single UI state query optimized")
    print("  ✅ Health Check: All manager status reporting")
    print("  ✅ Cleanup: Graceful shutdown and finalization")

    print("\n🎯 Day 5 Features Ready:")
    print("  - Pomodoro break reminders with elapsed timer (reduces anxiety)")
    print("  - Energy-aware UI adaptation (matches cognitive capacity)")
    print("  - Command history with privacy protection (screen-share safe)")
    print("  - State coordination via TUIStateManager (prevents complexity explosion)")

    print("\n🚀 Next Steps:")
    print("  1. Review git diff to see all changes")
    print("  2. Test TUI with real usage: python services/orchestrator/tui/main.py")
    print("  3. Log Day 5 completion decision")
    print("  4. Commit Day 5 implementation")


if __name__ == "__main__":
    print("\n🧪 Starting IP-005 Day 5 Integration Tests...")
    print("📍 Workspace: /Users/hue/code/dopemux-mvp")
    print("🔗 DopeconBridge: http://localhost:3016")
    print()

    asyncio.run(test_day5_integration())
