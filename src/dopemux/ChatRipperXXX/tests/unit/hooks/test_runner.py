#!/usr/bin/env python3
"""
Simple test runner for hook validation without pytest dependency
"""

import os
import sys
import json
from datetime import datetime

def test_pre_tool_guard():
    """Test pre_tool_guard.py fixes"""
    print("🧪 Testing pre_tool_guard.py...")

    os.environ['HOOKS_ENABLE_ADAPTIVE_SECURITY'] = '1'
    sys.path.insert(0, '.claude/hooks')

    try:
        from pre_tool_guard import check_legitimate_patterns, evaluate_adaptive_security

        # Test legitimate patterns
        assert check_legitimate_patterns("git status") is True, "git status should be legitimate"
        assert check_legitimate_patterns("python -m pytest") is True, "python -m pytest should be legitimate"
        assert check_legitimate_patterns("rm -rf /") is False, "rm -rf / should not be legitimate"

        # Test risk evaluation with fixed ranges
        result = evaluate_adaptive_security('pip install requests', {'project_type': 'python'})
        assert 0.3 <= result[2] < 0.8, f"Medium risk should be in range 0.3-0.8, got {result[2]}"

        print("✅ pre_tool_guard tests passed")
        return True

    except Exception as e:
        print(f"❌ pre_tool_guard test failed: {e}")
        return False

def test_pre_context_budget():
    """Test pre_context_budget.py token management"""
    print("🧪 Testing pre_context_budget.py...")

    os.environ['HOOKS_ENABLE_SMART_OPTIMIZATION'] = '1'
    sys.path.insert(0, '.claude/hooks')

    try:
        from pre_context_budget import estimate_token_usage

        # Test token estimates
        assert estimate_token_usage("zen", {}) == 29000, "Zen should be 29000 tokens"
        assert estimate_token_usage("task-master-ai", {"withSubtasks": False}) == 1500, "TaskMaster filtered should be 1500"
        assert estimate_token_usage("conport", {"limit": 5}) == 3000, "ConPort with limit should be 3000"

        print("✅ pre_context_budget tests passed")
        return True

    except Exception as e:
        print(f"❌ pre_context_budget test failed: {e}")
        return False

def test_dashboard():
    """Test dashboard.py functionality"""
    print("🧪 Testing dashboard.py...")

    sys.path.insert(0, '.claude/hooks')

    try:
        from dashboard import format_tokens, load_patterns

        # Test token formatting
        assert format_tokens(500) == "500", "500 should format as '500'"
        assert format_tokens(1500) == "1.5k", "1500 should format as '1.5k'"

        # Test loading patterns (should handle missing file gracefully)
        patterns = load_patterns()
        assert isinstance(patterns, dict), "Patterns should be a dictionary"
        assert "sessions" in patterns, "Patterns should have sessions key"

        print("✅ dashboard tests passed")
        return True

    except Exception as e:
        print(f"❌ dashboard test failed: {e}")
        return False

def main():
    """Run all hook tests"""
    print("🚀 Running Hook Validation Tests")
    print("=" * 50)

    tests = [
        ("pre_tool_guard", test_pre_tool_guard),
        ("pre_context_budget", test_pre_context_budget),
        ("dashboard", test_dashboard)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All hook fixes validated successfully!")
        return 0
    else:
        print("⚠️ Some tests failed - hooks may need further fixes")
        return 1

if __name__ == "__main__":
    sys.exit(main())