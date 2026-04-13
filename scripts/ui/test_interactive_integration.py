#!/usr/bin/env python3
"""
Comprehensive test suite for interactive tmux-MetaMCP integration.
Tests all the functional components we just built.
"""

import subprocess
import time
import json
import sys
from pathlib import Path


class InteractiveIntegrationTester:
    """Test suite for tmux-MetaMCP interactive functionality."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.controller_path = Path(__file__).parent / "tmux_metamcp_controller.py"
        self.updater_path = Path(__file__).parent / "realtime_status_updater.py"
        self.test_results = []

    def run_test(self, name: str, test_func):
        """Run a single test and record results."""
        print(f"🧪 Testing: {name}")
        try:
            result = test_func()
            if result:
                print(f"   ✅ PASS")
                self.test_results.append((name, True, None))
            else:
                print(f"   ❌ FAIL")
                self.test_results.append((name, False, "Test returned False"))
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            self.test_results.append((name, False, str(e)))
        print()

    def test_controller_basic_commands(self) -> bool:
        """Test basic controller command functionality."""
        commands = ['status', 'break_reminder', 'role_menu']

        for command in commands:
            result = subprocess.run([
                'python', str(self.controller_path), command
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                print(f"      Command '{command}' failed: {result.stderr}")
                return False

        return True

    def test_role_switching(self) -> bool:
        """Test role switching functionality."""
        roles = ['developer', 'researcher', 'planner', 'reviewer']

        for role in roles:
            result = subprocess.run([
                'python', str(self.controller_path), 'switch_role', role
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                print(f"      Role switch to '{role}' failed: {result.stderr}")
                return False

            # Check that output contains expected elements
            output = result.stdout
            if role not in output.lower():
                print(f"      Role '{role}' not found in output")
                return False

        return True

    def test_quick_role_switching(self) -> bool:
        """Test quick role switching with single letters."""
        quick_roles = {
            'd': 'developer',
            'r': 'researcher',
            'p': 'planner',
            'v': 'reviewer'
        }

        for letter, role in quick_roles.items():
            result = subprocess.run([
                'python', str(self.controller_path), 'quick_switch', letter
            ], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                print(f"      Quick switch '{letter}' failed: {result.stderr}")
                return False

            # Check that output contains the expected role
            output = result.stdout.lower()
            if role not in output:
                print(f"      Quick switch '{letter}' didn't switch to {role}")
                return False

        return True

    def test_status_updater(self) -> bool:
        """Test real-time status updater."""
        result = subprocess.run([
            'python', str(self.updater_path)
        ], capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            print(f"      Status updater failed: {result.stderr}")
            return False

        output = result.stdout
        # Check for expected status bar components
        required_elements = ['#[fg=', 'tools', 'ADHD']

        for element in required_elements:
            if element not in output:
                print(f"      Missing element '{element}' in status bar")
                return False

        return True

    def test_tmux_config_syntax(self) -> bool:
        """Test tmux configuration syntax."""
        try:
            # Test tmux config parsing
            result = subprocess.run([
                'tmux', '-f', '/Users/hue/.tmux.conf', '-C', 'list-keys'
            ], capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                print(f"      Tmux config syntax error: {result.stderr}")
                return False

            # Check that our custom keybindings are present
            output = result.stdout
            expected_bindings = ['bind-key d', 'bind-key r', 'bind-key B', 'bind-key M']

            for binding in expected_bindings:
                if binding not in output:
                    print(f"      Missing keybinding: {binding}")
                    return False

            return True

        except FileNotFoundError:
            print("      Tmux not available for testing")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling in controller."""
        # Test invalid role
        result = subprocess.run([
            'python', str(self.controller_path), 'switch_role', 'invalid_role'
        ], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            print("      Should have failed with invalid role")
            return False

        # Test invalid command
        result = subprocess.run([
            'python', str(self.controller_path), 'invalid_command'
        ], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            print("      Should have failed with invalid command")
            return False

        return True

    def test_adhd_break_reminders(self) -> bool:
        """Test ADHD break reminder functionality."""
        result = subprocess.run([
            'python', str(self.controller_path), 'break_reminder'
        ], capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            print(f"      Break reminder failed: {result.stderr}")
            return False

        output = result.stdout
        # Check for ADHD-friendly elements
        adhd_elements = ['🧠', 'break', 'water', 'walk']

        found_elements = sum(1 for element in adhd_elements if element in output.lower())
        if found_elements < 2:
            print(f"      Not enough ADHD-friendly elements found")
            return False

        return True

    def demonstration_mode(self):
        """Interactive demonstration of all features."""
        print("🎯 Interactive Demonstration Mode")
        print("=" * 50)
        print()

        print("Testing role switching...")
        for role in ['developer', 'researcher', 'planner']:
            print(f"\n🔄 Switching to {role} role:")
            result = subprocess.run([
                'python', str(self.controller_path), 'switch_role', role
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"❌ Failed: {result.stderr}")

        print("\n" + "="*50)
        print("🧠 Testing break reminder:")
        result = subprocess.run([
            'python', str(self.controller_path), 'break_reminder'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)

        print("\n" + "="*50)
        print("📊 Current status bar output:")
        result = subprocess.run([
            'python', str(self.updater_path)
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(result.stdout)

    def run_all_tests(self):
        """Run the complete test suite."""
        print("🚀 MetaMCP Interactive Integration Test Suite")
        print("=" * 55)
        print()

        # Run all tests
        self.run_test("Controller Basic Commands", self.test_controller_basic_commands)
        self.run_test("Role Switching", self.test_role_switching)
        self.run_test("Quick Role Switching", self.test_quick_role_switching)
        self.run_test("Real-time Status Updater", self.test_status_updater)
        self.run_test("Tmux Config Syntax", self.test_tmux_config_syntax)
        self.run_test("Error Handling", self.test_error_handling)
        self.run_test("ADHD Break Reminders", self.test_adhd_break_reminders)

        # Print summary
        print("📊 Test Results Summary:")
        print("=" * 30)

        passed = sum(1 for _, success, _ in self.test_results if success)
        total = len(self.test_results)

        for name, success, error in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status:8} {name}")
            if error and not success:
                print(f"         Error: {error}")

        print()
        print(f"🎯 Results: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Interactive integration is ready!")
            print()
            print("🚀 Quick Start Commands:")
            print("   tmux new-session                    # Start tmux with MetaMCP")
            print("   C-b d                               # Switch to developer role")
            print("   C-b r                               # Switch to researcher role")
            print("   C-b B                               # Get break reminder")
            print("   C-b M                               # Show role menu")
        else:
            print("⚠️  Some tests failed. Check the errors above.")

        return passed == total


def main():
    """Main test runner."""
    tester = InteractiveIntegrationTester()

    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        tester.demonstration_mode()
    else:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()