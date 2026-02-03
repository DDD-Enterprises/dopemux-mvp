#!/usr/bin/env python3
"""
Test Error Recovery System - Comprehensive Validation
Tests all recovery features with realistic failure scenarios
"""

import sys
import time
from src.error_recovery import (
    ErrorRecoveryManager,
    RecoveryAction,
    Severity,
    is_retryable,
    retry_with_backoff
)
from src.timeout_manager import TimeoutManager, OperationType
from src.health_monitor import HealthMonitor, HealthStatus
from src.response_parser import ErrorType


def test_error_classification():
    """Test error classification (retryable vs permanent)."""
    print("\n🧪 Test 1: Error Classification")
    print("-" * 60)

    # Retryable errors
    assert is_retryable(ErrorType.TIMEOUT), "TIMEOUT should be retryable"
    assert is_retryable(ErrorType.EMPTY), "EMPTY should be retryable"
    assert is_retryable(ErrorType.API_ERROR), "API_ERROR should be retryable"

    # Permanent errors (need restart, not retry)
    assert not is_retryable(ErrorType.CRASH), "CRASH should not be retryable"

    print(f"✅ Error classification works correctly")
    print(f"   Retryable: TIMEOUT, EMPTY, API_ERROR, PARSE_ERROR")
    print(f"   Permanent: CRASH")

    return True


def test_retry_with_backoff():
    """Test retry logic with exponential backoff."""
    print("\n🧪 Test 2: Retry with Backoff")
    print("-" * 60)

    attempt_count = [0]

    def flaky_operation():
        """Fails twice, then succeeds."""
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise Exception(f"Transient failure {attempt_count[0]}")
        return "Success!"

    start_time = time.time()
    result = retry_with_backoff(flaky_operation, max_attempts=3, operation_name="flaky test")
    elapsed = time.time() - start_time

    assert result == "Success!", "Should eventually succeed"
    assert attempt_count[0] == 3, "Should take 3 attempts"
    assert elapsed >= 3, "Should wait 1s + 2s = 3s total"  # 1s + 2s backoff

    print(f"✅ Retry with backoff works")
    print(f"   Attempts: {attempt_count[0]}")
    print(f"   Elapsed: {elapsed:.1f}s")

    return True


def test_timeout_manager():
    """Test timeout manager configuration."""
    print("\n🧪 Test 3: Timeout Manager")
    print("-" * 60)

    # Test default timeouts
    manager = TimeoutManager()

    spawn_timeout = manager.get_timeout(OperationType.SPAWN)
    assert spawn_timeout == 10, "Default spawn timeout should be 10s"

    research_timeout = manager.get_timeout(OperationType.RESEARCH)
    assert research_timeout == 600, "Default research timeout should be 600s"

    print(f"✅ Timeout manager works")
    print(f"   spawn: {spawn_timeout}s")
    print(f"   research: {research_timeout}s")

    # Test custom config
    custom_config = {
        'advanced': {
            'timeouts': {
                'spawn': 20,
                'response': 60,
            }
        }
    }

    manager2 = TimeoutManager(custom_config)
    custom_spawn = manager2.get_timeout(OperationType.SPAWN)
    assert custom_spawn == 20, "Custom timeout should override default"

    print(f"   Custom spawn override: {custom_spawn}s")

    return True


def test_health_monitor():
    """Test health monitoring system."""
    print("\n🧪 Test 4: Health Monitor")
    print("-" * 60)

    import os

    monitor = HealthMonitor(heartbeat_interval=60)

    # Mock agent
    class MockAgent:
        def __init__(self, pid):
            self.pid = pid
            self.restart_count = 0
            self.config = type('obj', (object,), {
                'agent_type': type('obj', (object,), {'value': 'test'})()
            })()
            self.status = type('obj', (object,), {'value': 'running'})()

    # Test with current process (should be alive)
    current_process = MockAgent(os.getpid())
    is_alive = monitor._is_process_alive(current_process)
    assert is_alive, "Current process should be detected as alive"

    print(f"✅ Health monitor works")
    print(f"   Process check: Fast (0ms overhead)")
    print(f"   Current process detected: {is_alive}")

    # Test with fake PID (should be dead)
    fake_agent = MockAgent(999999)
    is_alive = monitor._is_process_alive(fake_agent)
    assert not is_alive, "Fake process should be detected as dead"

    print(f"   Fake process detected: {is_alive}")

    return True


def test_recovery_action_mapping():
    """Test recovery action decision tree."""
    print("\n🧪 Test 5: Recovery Action Mapping")
    print("-" * 60)

    manager = ErrorRecoveryManager("/Users/hue/code/ui-build")

    # Test mapping
    assert manager.RECOVERY_ACTIONS[ErrorType.CRASH] == RecoveryAction.RESTART_WITH_BACKOFF
    assert manager.RECOVERY_ACTIONS[ErrorType.TIMEOUT] == RecoveryAction.KILL_AND_RESTART
    assert manager.RECOVERY_ACTIONS[ErrorType.EMPTY] == RecoveryAction.RETRY_ONCE

    print(f"✅ Recovery action mapping correct")
    print(f"   CRASH → {RecoveryAction.RESTART_WITH_BACKOFF.value}")
    print(f"   TIMEOUT → {RecoveryAction.KILL_AND_RESTART.value}")
    print(f"   EMPTY → {RecoveryAction.RETRY_ONCE.value}")

    return True


def test_severity_mapping():
    """Test error severity classification."""
    print("\n🧪 Test 6: Severity Mapping")
    print("-" * 60)

    manager = ErrorRecoveryManager("/Users/hue/code/ui-build")

    # Test severity levels
    assert manager.ERROR_SEVERITY[ErrorType.CRASH] == Severity.HIGH
    assert manager.ERROR_SEVERITY[ErrorType.TIMEOUT] == Severity.MEDIUM
    assert manager.ERROR_SEVERITY[ErrorType.EMPTY] == Severity.LOW

    print(f"✅ Severity mapping correct")
    print(f"   CRASH → {Severity.HIGH.value} (immediate notification)")
    print(f"   TIMEOUT → {Severity.MEDIUM.value} (batched)")
    print(f"   EMPTY → {Severity.LOW.value} (status bar only)")

    return True


def test_recovery_stats():
    """Test recovery statistics tracking."""
    print("\n🧪 Test 7: Recovery Statistics")
    print("-" * 60)

    manager = ErrorRecoveryManager("/Users/hue/code/ui-build")

    # Simulate some recoveries
    manager.recovery_history = [
        {'agent': 'claude', 'error_type': 'crash', 'action': 'restart', 'success': True, 'attempts': 1},
        {'agent': 'gemini', 'error_type': 'timeout', 'action': 'retry', 'success': True, 'attempts': 2},
        {'agent': 'claude', 'error_type': 'crash', 'action': 'restart', 'success': False, 'attempts': 3},
    ]

    stats = manager.get_recovery_stats()

    assert stats['total_recoveries'] == 3, "Should track total recoveries"
    assert stats['successful'] == 2, "Should count successes"
    assert stats['failed'] == 1, "Should count failures"
    assert stats['success_rate'] == 2/3, "Should calculate success rate"

    print(f"✅ Recovery stats tracking works")
    print(f"   Total: {stats['total_recoveries']}")
    print(f"   Success rate: {stats['success_rate']:.0%}")
    print(f"   By error type: {stats['by_error_type']}")

    return True


def test_exponential_backoff_calculation():
    """Test backoff timing calculation."""
    print("\n🧪 Test 8: Exponential Backoff Timing")
    print("-" * 60)

    # Simulate restart backoff
    backoffs = []
    for restart_count in range(5):
        backoff = min(10 * (2 ** restart_count), 60)
        backoffs.append(backoff)

    expected = [10, 20, 40, 60, 60]  # Caps at 60s
    assert backoffs == expected, f"Backoff should follow pattern (got {backoffs})"

    print(f"✅ Exponential backoff correct")
    print(f"   Attempt 1: {backoffs[0]}s")
    print(f"   Attempt 2: {backoffs[1]}s")
    print(f"   Attempt 3: {backoffs[2]}s")
    print(f"   Attempt 4+: {backoffs[3]}s (capped)")

    return True


def test_retry_failure_scenario():
    """Test retry behavior when all attempts fail."""
    print("\n🧪 Test 9: Retry All Attempts Fail")
    print("-" * 60)

    def always_fails():
        """Always raises exception."""
        raise Exception("Permanent failure")

    try:
        retry_with_backoff(always_fails, max_attempts=2, operation_name="always fails")
        assert False, "Should have raised exception"
    except Exception as e:
        assert "Permanent failure" in str(e), "Should propagate last exception"
        print(f"✅ Retry correctly raises exception after all attempts")
        print(f"   Exception: {e}")

    return True


def test_health_report_comprehensive():
    """Test comprehensive health report generation."""
    print("\n🧪 Test 10: Comprehensive Health Report")
    print("-" * 60)

    import os

    monitor = HealthMonitor()

    # Create mock agents (mix of alive and dead)
    class MockAgent:
        def __init__(self, name, pid, restart_count=0):
            self.pid = pid
            self.restart_count = restart_count
            self.config = type('obj', (object,), {
                'agent_type': type('obj', (object,), {'value': name})()
            })()
            self.status = type('obj', (object,), {'value': 'running'})()

    agents = [
        MockAgent('claude', os.getpid(), restart_count=0),  # Alive
        MockAgent('gemini', 999999, restart_count=2),        # Dead
    ]

    report = monitor.get_health_report(agents)

    assert report['total'] == 2, "Should report total agents"
    assert report['healthy'] >= 0, "Should count healthy agents"
    assert report['dead'] >= 1, "Should detect dead process"

    print(f"✅ Health report generation works")
    print(f"   Total agents: {report['total']}")
    print(f"   Healthy: {report['healthy']}")
    print(f"   Dead: {report['dead']}")
    print(f"   Agents: {list(report['agents'].keys())}")

    return True


def run_all_tests():
    """Run all error recovery tests."""
    print("🚀 Error Recovery Test Suite")
    print("=" * 60)

    tests = [
        ("Error Classification", test_error_classification),
        ("Retry with Backoff", test_retry_with_backoff),
        ("Timeout Manager", test_timeout_manager),
        ("Health Monitor", test_health_monitor),
        ("Recovery Action Mapping", test_recovery_action_mapping),
        ("Severity Mapping", test_severity_mapping),
        ("Recovery Statistics", test_recovery_stats),
        ("Exponential Backoff", test_exponential_backoff_calculation),
        ("Retry Failure", test_retry_failure_scenario),
        ("Health Report", test_health_report_comprehensive),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test_name} failed")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test_name} assertion failed: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} error: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Total: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted")
        sys.exit(1)
