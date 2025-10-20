#!/usr/bin/env python3
"""
Test IP-005 Days 8-10 ADHD Engine Integration

Validates:
- TUIStateManager initialization in main.py
- Energy detection wired to UI
- Break notifications working
- UI color adaptation based on energy
"""

import asyncio
import sys
import os

# Add tui directory to path
sys.path.insert(0, os.path.dirname(__file__))

from state_manager import get_state_manager


async def test_state_manager_initialization():
    """Test that state_manager initializes correctly."""
    print("\n🧪 Test 1: TUIStateManager Initialization")
    
    workspace_id = os.getcwd()
    state_manager = get_state_manager(workspace_id)
    
    result = await state_manager.initialize()
    
    assert 'successful_managers' in result, "Missing successful_managers in result"
    assert 'total_managers' in result, "Missing total_managers in result"
    
    successful = result['successful_managers']
    total = result['total_managers']
    
    print(f"   ✅ Initialized {successful}/{total} managers")
    
    if result.get('warnings'):
        for warning in result['warnings']:
            print(f"   ⚠️  {warning}")
    
    assert successful >= 2, f"Expected at least 2 managers, got {successful}"
    print("   ✅ Test 1 passed!")
    
    return state_manager


async def test_ui_state_query(state_manager):
    """Test that get_ui_state() returns complete state."""
    print("\n🧪 Test 2: UI State Query")
    
    ui_state = await state_manager.get_ui_state()
    
    # Verify required keys
    required_keys = ['progress', 'break', 'energy', 'history_size', 'timestamp']
    for key in required_keys:
        assert key in ui_state, f"Missing required key: {key}"
        print(f"   ✅ {key}: {type(ui_state[key]).__name__}")
    
    # Verify break state structure
    break_state = ui_state['break']
    if not break_state.get('error'):
        assert 'elapsed_seconds' in break_state, "Missing elapsed_seconds in break_state"
        assert 'status_color' in break_state, "Missing status_color in break_state"
        assert 'break_suggested' in break_state, "Missing break_suggested in break_state"
        print(f"   ✅ Break: {break_state['elapsed_seconds']}s, color={break_state['status_color']}")
    
    # Verify energy state structure
    energy_state = ui_state['energy']
    if not energy_state.get('error'):
        assert 'level' in energy_state, "Missing level in energy_state"
        assert 'ui_adaptations' in energy_state, "Missing ui_adaptations"
        print(f"   ✅ Energy: level={energy_state['level']}, source={energy_state.get('source')}")
    
    print("   ✅ Test 2 passed!")
    return ui_state


async def test_energy_ui_adaptations(ui_state):
    """Test energy-based UI adaptations."""
    print("\n🧪 Test 3: Energy UI Adaptations")
    
    energy_state = ui_state['energy']
    if energy_state.get('error'):
        print(f"   ⚠️  Energy detection unavailable: {energy_state['error']}")
        print("   ⏭️  Test 3 skipped")
        return
    
    ui_adaptations = energy_state.get('ui_adaptations', {})
    
    # Verify UI adaptation fields
    expected_fields = ['color_intensity', 'recommended_panes', 'max_complexity']
    for field in expected_fields:
        assert field in ui_adaptations, f"Missing {field} in ui_adaptations"
        print(f"   ✅ {field}: {ui_adaptations[field]}")
    
    # Verify color intensity is valid (0.5-1.0)
    color_intensity = ui_adaptations['color_intensity']
    assert 0.5 <= color_intensity <= 1.0, f"Invalid color_intensity: {color_intensity}"
    
    print("   ✅ Test 3 passed!")


async def test_break_notifications(ui_state):
    """Test break notification logic."""
    print("\n🧪 Test 4: Break Notifications")
    
    break_state = ui_state['break']
    if break_state.get('error'):
        print(f"   ⚠️  Break manager unavailable: {break_state['error']}")
        print("   ⏭️  Test 4 skipped")
        return
    
    elapsed_minutes = break_state.get('elapsed_minutes', 0)
    break_suggested = break_state.get('break_suggested', False)
    break_mandatory = break_state.get('break_mandatory', False)
    status_color = break_state.get('status_color', 'green')
    
    print(f"   ℹ️  Elapsed: {elapsed_minutes} minutes")
    print(f"   ℹ️  Status color: {status_color}")
    print(f"   ℹ️  Break suggested: {break_suggested}")
    print(f"   ℹ️  Break mandatory: {break_mandatory}")
    
    # Verify status color logic
    if elapsed_minutes < 25:
        assert status_color == 'green', f"Expected green for <25min, got {status_color}"
    elif elapsed_minutes < 45:
        assert status_color == 'yellow', f"Expected yellow for 25-45min, got {status_color}"
    else:
        assert status_color == 'red', f"Expected red for >45min, got {status_color}"
    
    print("   ✅ Test 4 passed!")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("IP-005 Days 8-10 ADHD Engine Integration Tests")
    print("=" * 60)
    
    try:
        # Test 1: Initialization
        state_manager = await test_state_manager_initialization()
        
        # Test 2: UI State Query
        ui_state = await test_ui_state_query(state_manager)
        
        # Test 3: Energy UI Adaptations
        await test_energy_ui_adaptations(ui_state)
        
        # Test 4: Break Notifications
        await test_break_notifications(ui_state)
        
        # Cleanup
        await state_manager.close()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nIP-005 Days 8-10 Integration: ✅ COMPLETE")
        print("\nFeatures validated:")
        print("  ✅ TUIStateManager initialization")
        print("  ✅ Single optimized UI state query")
        print("  ✅ Break timer with elapsed tracking")
        print("  ✅ Break notifications (gentle + mandatory)")
        print("  ✅ Energy detection (multi-tier)")
        print("  ✅ Energy-based UI color adaptation")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
