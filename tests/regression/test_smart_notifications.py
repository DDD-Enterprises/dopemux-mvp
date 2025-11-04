#!/usr/bin/env python3
"""
Test Smart Notifications Feature
Quick Win 4: Automated ADHD-aware notification system
"""

import asyncio
import sys
from datetime import datetime
from dopemux_dashboard import (
    NotificationManager,
    NotificationPriority,
    AutoTriggerMonitor,
    MetricsFetcher,
)


async def test_notification_manager():
    """Test NotificationManager cooldown and flow protection"""
    print("\n" + "="*60)
    print("TEST 1: NotificationManager")
    print("="*60)
    
    manager = NotificationManager()
    
    # Test 1: Basic notification allowed
    can_first = manager.can_notify("test1", NotificationPriority.MEDIUM)
    assert can_first, "❌ First notification should be allowed"
    # Actually send it to track timestamp
    await manager.notify("test1", "Test", "Message", NotificationPriority.MEDIUM)
    print("✅ First notification allowed")
    
    # Test 2: Cooldown prevents duplicate
    can_duplicate = manager.can_notify("test1", NotificationPriority.MEDIUM)
    assert not can_duplicate, "❌ Duplicate should be blocked (cooldown)"
    print("✅ Cooldown prevents duplicate")
    
    # Test 3: Different event allowed
    assert manager.can_notify("test2", NotificationPriority.MEDIUM), "❌ Different event should be allowed"
    print("✅ Different event allowed")
    
    # Test 4: Flow protection blocks medium priority
    manager.update_flow_state(True)
    assert not manager.can_notify("test3", NotificationPriority.MEDIUM), "❌ Flow should block medium priority"
    print("✅ Flow protection blocks medium priority")
    
    # Test 5: High priority bypasses flow
    assert manager.can_notify("test4", NotificationPriority.HIGH), "❌ High priority should bypass flow"
    print("✅ High priority bypasses flow protection")
    
    # Test 6: Toggle enabled/disabled
    manager.toggle_enabled()
    assert not manager.enabled, "❌ Toggle should disable"
    assert not manager.can_notify("test5", NotificationPriority.HIGH), "❌ Disabled should block all"
    print("✅ Toggle disables all notifications")
    
    manager.toggle_enabled()
    assert manager.enabled, "❌ Toggle should re-enable"
    print("✅ Toggle re-enables notifications")
    
    print("\n🎉 NotificationManager: ALL TESTS PASSED")


async def test_auto_triggers():
    """Test AutoTriggerMonitor notification logic"""
    print("\n" + "="*60)
    print("TEST 2: AutoTriggerMonitor")
    print("="*60)
    
    # Create mocked fetcher (no real API calls)
    class MockFetcher:
        async def get_adhd_state(self):
            return {
                "energy_level": "high",
                "attention_state": "focused",
                "cognitive_load": 0.5,
                "flow_state": {"active": False, "duration": 0},
                "session_time": "30m",
                "break_info": {"recommended_in": 25, "minutes_since": 5}
            }
        
        async def get_services_health(self):
            return {
                "ConPort": {"status": "healthy", "latency_ms": 10},
                "ADHD Engine": {"status": "healthy", "latency_ms": 5},
            }
    
    fetcher = MockFetcher()
    manager = NotificationManager()
    monitor = AutoTriggerMonitor(fetcher, manager)
    
    # Test cognitive load trigger (should NOT trigger at 0.5)
    print("\n📊 Testing cognitive load...")
    await monitor.check_triggers()
    assert "cognitive_overload" not in manager.last_notifications, "❌ Should not trigger at 50% load"
    print("✅ No notification at 50% cognitive load")
    
    # Test high cognitive load (should trigger)
    fetcher.get_adhd_state = lambda: asyncio.sleep(0).then(lambda: {
        "energy_level": "high",
        "attention_state": "focused",
        "cognitive_load": 0.9,  # 90% - CRITICAL!
        "flow_state": {"active": False, "duration": 0},
        "session_time": "30m",
        "break_info": {"recommended_in": 25, "minutes_since": 5}
    })
    
    async def mock_adhd_high():
        return {
            "energy_level": "high",
            "attention_state": "focused",
            "cognitive_load": 0.9,
            "flow_state": {"active": False, "duration": 0},
            "session_time": "30m",
            "break_info": {"recommended_in": 25, "minutes_since": 5}
        }
    
    fetcher.get_adhd_state = mock_adhd_high
    await monitor.check_triggers()
    assert "cognitive_overload" in manager.last_notifications, "❌ Should trigger at 90% load"
    print("✅ Notification triggered at 90% cognitive load")
    
    # Test break timing
    async def mock_adhd_break_soon():
        return {
            "energy_level": "medium",
            "attention_state": "focused",
            "cognitive_load": 0.5,
            "flow_state": {"active": False, "duration": 0},
            "session_time": "55m",
            "break_info": {"recommended_in": 3, "minutes_since": 57}  # 3 min warning!
        }
    
    fetcher.get_adhd_state = mock_adhd_break_soon
    await monitor.check_triggers()
    assert "break_soon" in manager.last_notifications, "❌ Should trigger break warning"
    print("✅ Break warning triggered at 3min")
    
    # Test flow state celebration (RESET notification manager to avoid cooldowns)
    manager.last_notifications.clear()  # Clear previous notifications
    manager.update_flow_state(False)  # Make sure we're not in flow state
    
    # First set previous state to NOT in flow
    async def mock_adhd_no_flow():
        return {
            "energy_level": "high",
            "attention_state": "focused",
            "cognitive_load": 0.5,  # Low load to avoid cognitive_overload trigger
            "flow_state": {"active": False, "duration": 0},
            "session_time": "30m",
            "break_info": {"recommended_in": 25, "minutes_since": 5}
        }
    
    fetcher.get_adhd_state = mock_adhd_no_flow
    await monitor.check_triggers()  # This sets previous_state with flow=False
    
    # Now transition to flow state
    async def mock_adhd_flow():
        return {
            "energy_level": "high",
            "attention_state": "focused",
            "cognitive_load": 0.7,
            "flow_state": {"active": True, "duration": 5},  # Flow started!
            "session_time": "30m",
            "break_info": {"recommended_in": 25, "minutes_since": 5}
        }
    
    fetcher.get_adhd_state = mock_adhd_flow
    await monitor.check_triggers()  # This should detect the transition
    assert "flow_started" in manager.last_notifications, "❌ Should celebrate flow start"
    print("✅ Flow state achievement celebrated")
    
    print("\n🎉 AutoTriggerMonitor: ALL TESTS PASSED")


async def test_priority_system():
    """Test notification priority system"""
    print("\n" + "="*60)
    print("TEST 3: Priority System")
    print("="*60)
    
    manager = NotificationManager()
    
    # Scenario: In flow state
    manager.update_flow_state(True)
    
    # High priority should work
    can_high = manager.can_notify("high_test", NotificationPriority.HIGH)
    assert can_high, "❌ High priority should work in flow"
    print("✅ HIGH priority works during flow")
    
    # Medium priority should block
    can_medium = manager.can_notify("medium_test", NotificationPriority.MEDIUM)
    assert not can_medium, "❌ Medium priority should block in flow"
    print("✅ MEDIUM priority blocked during flow")
    
    # Low priority should block
    can_low = manager.can_notify("low_test", NotificationPriority.LOW)
    assert not can_low, "❌ Low priority should block in flow"
    print("✅ LOW priority blocked during flow")
    
    # Exit flow
    manager.update_flow_state(False)
    
    # Now medium should work
    can_medium_no_flow = manager.can_notify("medium_test2", NotificationPriority.MEDIUM)
    assert can_medium_no_flow, "❌ Medium priority should work outside flow"
    print("✅ MEDIUM priority works when not in flow")
    
    print("\n🎉 Priority System: ALL TESTS PASSED")


async def test_cooldown_timing():
    """Test cooldown prevents spam"""
    print("\n" + "="*60)
    print("TEST 4: Cooldown Timing")
    print("="*60)
    
    manager = NotificationManager()
    manager.cooldown_seconds = 2  # 2 seconds for testing
    
    # First notification
    result1 = await manager.notify("spam_test", "Test", "Message 1", NotificationPriority.MEDIUM)
    assert result1, "❌ First notification should send"
    print("✅ First notification sent")
    
    # Immediate duplicate (should block)
    result2 = await manager.notify("spam_test", "Test", "Message 2", NotificationPriority.MEDIUM)
    assert not result2, "❌ Duplicate should be blocked"
    print("✅ Duplicate blocked immediately")
    
    # Wait for cooldown
    print("⏳ Waiting 2 seconds for cooldown...")
    await asyncio.sleep(2.1)
    
    # After cooldown (should work)
    result3 = await manager.notify("spam_test", "Test", "Message 3", NotificationPriority.MEDIUM)
    assert result3, "❌ Should work after cooldown"
    print("✅ Notification sent after cooldown")
    
    print("\n🎉 Cooldown Timing: ALL TESTS PASSED")


async def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("SMART NOTIFICATIONS TEST SUITE")
    print("Quick Win 4: ADHD-Aware Auto-Notifications")
    print("🚀"*30)
    
    try:
        await test_notification_manager()
        await test_auto_triggers()
        await test_priority_system()
        await test_cooldown_timing()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED! 🎉")
        print("="*60)
        print("\nSmart Notifications Features Verified:")
        print("  ✅ Notification cooldown (prevents spam)")
        print("  ✅ Flow protection (non-critical muted)")
        print("  ✅ Priority system (HIGH/MEDIUM/LOW)")
        print("  ✅ Cognitive overload alerts")
        print("  ✅ Break timing warnings")
        print("  ✅ Flow state celebrations")
        print("  ✅ Toggle enable/disable")
        print("  ✅ State transition detection")
        print("\n🎊 Quick Win 4 Complete!")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
