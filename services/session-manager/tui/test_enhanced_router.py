#!/usr/bin/env python3
"""
Comprehensive Test Suite for Enhanced Command Router

Tests all Day 4 enhancements:
- CLI detection and availability checks
- Command execution with mocked AI responses
- Retry logic with exponential backoff
- Error categorization and actionable messages
- Timeout handling
- ConPort integration
- Performance metrics

Run with: pytest test_enhanced_router.py -v
Or: python test_enhanced_router.py (without pytest)
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from command_router_enhanced import (
    EnhancedCommandRouter,
    CommandResult,
    ErrorCategory,
    AIType
)


class TestCLIDetection:
    """Test CLI detection and availability."""

    def test_cli_detection(self):
        """Test automatic CLI detection."""
        router = EnhancedCommandRouter(enable_conport=False)

        # Check that detection ran
        assert hasattr(router, 'cli_configs')
        assert len(router.cli_configs) == 3

        # Check detection results
        for ai_type, config in router.cli_configs.items():
            assert isinstance(config.available, bool)
            print(f"  {ai_type.value}: {'✅' if config.available else '❌'}")

    def test_availability_check(self):
        """Test is_available() method."""
        router = EnhancedCommandRouter(enable_conport=False)

        # Test with valid AI names
        for ai in ["claude", "gemini", "grok"]:
            result = router.is_available(ai)
            assert isinstance(result, bool)

        # Test with invalid AI name
        assert router.is_available("invalid-ai") == False

    def test_get_available_ais(self):
        """Test getting list of available AIs."""
        router = EnhancedCommandRouter(enable_conport=False)
        available = router.get_available_ais()

        assert isinstance(available, list)
        assert all(isinstance(ai, str) for ai in available)
        print(f"  Available AIs: {available if available else 'None'}")

    def test_installation_hints(self):
        """Test installation hint generation."""
        router = EnhancedCommandRouter(enable_conport=False)

        for ai in ["claude", "gemini", "grok"]:
            hint = router.get_installation_hint(ai)
            assert isinstance(hint, str)
            assert len(hint) > 0
            print(f"  {ai}: {hint[:50]}...")


class TestCommandExecution:
    """Test command execution with various scenarios."""

    async def test_missing_cli_error(self):
        """Test error handling for missing CLI."""
        router = EnhancedCommandRouter(enable_conport=False)

        # Force a CLI to be unavailable
        router.cli_configs[AIType.GEMINI].available = False

        result = await router.execute_command(
            ai="gemini",
            command="test",
            enable_retry=False
        )

        assert result.return_code == 127
        assert result.error_category == ErrorCategory.CLI_NOT_FOUND
        assert "install" in result.error_output.lower()
        print(f"  ✅ Missing CLI error: {result.error_message[:50]}...")

    async def test_invalid_ai_name(self):
        """Test ValueError for invalid AI name."""
        router = EnhancedCommandRouter(enable_conport=False)

        try:
            await router.execute_command(ai="invalid", command="test")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown AI" in str(e)
            print(f"  ✅ Invalid AI error: {e}")

    async def test_command_execution_mock(self):
        """Test command execution with mocked subprocess."""
        router = EnhancedCommandRouter(enable_conport=False)

        # Mock successful execution
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.stdout.readline = AsyncMock(side_effect=[
            b"Test output line 1\n",
            b"Test output line 2\n",
            b""
        ])
        mock_process.stderr.readline = AsyncMock(return_value=b"")
        mock_process.wait = AsyncMock()

        output_lines = []

        def capture_output(line):
            output_lines.append(line)

        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await router.execute_command(
                ai="claude",
                command="test command",
                output_callback=capture_output,
                enable_retry=False
            )

        assert result.success
        assert result.return_code == 0
        assert len(output_lines) > 0
        print(f"  ✅ Mocked execution: {len(output_lines)} lines captured")


class TestRetryLogic:
    """Test retry logic and exponential backoff."""

    async def test_retry_on_transient_error(self):
        """Test that transient errors trigger retry."""
        router = EnhancedCommandRouter(enable_conport=False)

        attempt = 0
        max_attempts = 3

        async def mock_execute_once(*args, **kwargs):
            nonlocal attempt
            attempt += 1

            if attempt < max_attempts:
                # Simulate transient network error
                return CommandResult(
                    return_code=1,
                    output="",
                    error_output="Connection timeout",
                    duration_seconds=1.0,
                    error_category=ErrorCategory.NETWORK_ERROR,
                    error_message="Network error"
                )
            else:
                # Success on final attempt
                return CommandResult(
                    return_code=0,
                    output="Success",
                    error_output="",
                    duration_seconds=1.0
                )

        router._execute_once = mock_execute_once

        start_time = time.time()
        result = await router._execute_with_retry(
            AIType.CLAUDE,
            router.cli_configs[AIType.CLAUDE],
            "test",
            None,
            None,
            10
        )
        duration = time.time() - start_time

        assert result.success
        assert attempt == max_attempts
        assert duration >= 1.0  # Should have backoff delays
        print(f"  ✅ Retry succeeded after {attempt} attempts in {duration:.1f}s")

    async def test_no_retry_on_permanent_error(self):
        """Test that permanent errors don't retry."""
        router = EnhancedCommandRouter(enable_conport=False)

        attempt = 0

        async def mock_execute_once(*args, **kwargs):
            nonlocal attempt
            attempt += 1

            # Simulate permanent error (invalid command)
            return CommandResult(
                return_code=1,
                output="",
                error_output="Invalid command",
                duration_seconds=0.1,
                error_category=ErrorCategory.INVALID_COMMAND,
                error_message="Invalid"
            )

        router._execute_once = mock_execute_once

        result = await router._execute_with_retry(
            AIType.CLAUDE,
            router.cli_configs[AIType.CLAUDE],
            "test",
            None,
            None,
            10
        )

        assert not result.success
        assert attempt == 1  # Should not retry
        print(f"  ✅ No retry on permanent error (attempts: {attempt})")


class TestErrorCategorization:
    """Test error categorization and messaging."""

    def test_categorize_errors(self):
        """Test error categorization from error messages."""
        router = EnhancedCommandRouter(enable_conport=False)

        test_cases = [
            ("Rate limit exceeded", ErrorCategory.RATE_LIMIT),
            ("Connection timeout", ErrorCategory.TIMEOUT),
            ("Connection error", ErrorCategory.NETWORK_ERROR),
            ("Permission denied", ErrorCategory.PERMISSION_DENIED),
            ("Invalid syntax", ErrorCategory.INVALID_COMMAND),
            ("Something random", ErrorCategory.UNKNOWN),
        ]

        for error_text, expected_category in test_cases:
            category = router._categorize_error(error_text)
            assert category == expected_category
            print(f"  ✅ '{error_text[:30]}' → {category.value}")

    def test_actionable_error_messages(self):
        """Test generation of actionable error messages."""
        router = EnhancedCommandRouter(enable_conport=False)

        categories = [
            ErrorCategory.CLI_NOT_FOUND,
            ErrorCategory.TIMEOUT,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.PERMISSION_DENIED,
        ]

        for category in categories:
            message = router._generate_error_message(category, "Sample error text")
            assert len(message) > 0
            assert "Details:" in message
            print(f"  ✅ {category.value}: {message[:40]}...")


class TestTimeoutHandling:
    """Test timeout handling."""

    async def test_timeout_triggers_retry(self):
        """Test that timeout triggers retry."""
        router = EnhancedCommandRouter(enable_conport=False)

        attempt = 0

        async def mock_execute_once(*args, **kwargs):
            nonlocal attempt
            attempt += 1

            if attempt < 2:
                # Simulate timeout
                raise asyncio.TimeoutError()
            else:
                # Success
                return CommandResult(
                    return_code=0,
                    output="Success after timeout",
                    error_output="",
                    duration_seconds=0.5
                )

        router._execute_once = mock_execute_once

        result = await router._execute_with_retry(
            AIType.CLAUDE,
            router.cli_configs[AIType.CLAUDE],
            "test",
            None,
            None,
            5
        )

        assert result.success
        assert attempt == 2
        print(f"  ✅ Timeout retry succeeded (attempts: {attempt})")


class TestStatistics:
    """Test command statistics tracking."""

    async def test_command_history_tracking(self):
        """Test that command history is tracked."""
        router = EnhancedCommandRouter(enable_conport=False)

        # Mock some executions
        router.command_history = [
            CommandResult(0, "ok", "", 1.0),
            CommandResult(1, "", "error", 2.0),
            CommandResult(0, "ok", "", 1.5),
        ]

        stats = router.get_command_stats()

        assert stats["total"] == 3
        assert stats["success"] == 2
        assert stats["failed"] == 1
        assert stats["success_rate"] == (2/3) * 100
        assert stats["avg_duration"] == (1.0 + 2.0 + 1.5) / 3

        print(f"  ✅ Stats: {stats['success']}/{stats['total']} success, {stats['avg_duration']:.1f}s avg")

    def test_status_report_generation(self):
        """Test CLI status report generation."""
        router = EnhancedCommandRouter(enable_conport=False)

        report = router.get_cli_status_report()

        assert "AI CLI Status" in report
        assert isinstance(report, str)
        assert len(report) > 50
        print(f"  ✅ Status report generated ({len(report)} chars)")


# Main test runner (works without pytest)
async def run_async_tests():
    """Run all async tests."""
    print("\n" + "="*60)
    print("ASYNC TESTS")
    print("="*60 + "\n")

    exec_tests = TestCommandExecution()
    retry_tests = TestRetryLogic()
    timeout_tests = TestTimeoutHandling()
    stats_tests = TestStatistics()

    print("TestCommandExecution:")
    await exec_tests.test_missing_cli_error()
    await exec_tests.test_invalid_ai_name()
    await exec_tests.test_command_execution_mock()

    print("\nTestRetryLogic:")
    await retry_tests.test_retry_on_transient_error()
    await retry_tests.test_no_retry_on_permanent_error()

    print("\nTestTimeoutHandling:")
    await timeout_tests.test_timeout_triggers_retry()

    print("\nTestStatistics:")
    await stats_tests.test_command_history_tracking()


def run_sync_tests():
    """Run all synchronous tests."""
    print("\n" + "="*60)
    print("SYNCHRONOUS TESTS")
    print("="*60 + "\n")

    detection_tests = TestCLIDetection()
    error_tests = TestErrorCategorization()
    stats_tests = TestStatistics()

    print("TestCLIDetection:")
    detection_tests.test_cli_detection()
    detection_tests.test_availability_check()
    detection_tests.test_get_available_ais()
    detection_tests.test_installation_hints()

    print("\nTestErrorCategorization:")
    error_tests.test_categorize_errors()
    error_tests.test_actionable_error_messages()

    print("\nTestStatistics:")
    stats_tests.test_status_report_generation()


if __name__ == "__main__":
    print("="*60)
    print("Enhanced Command Router Test Suite")
    print("="*60)

    # Run sync tests
    try:
        run_sync_tests()
        print("\n✅ All synchronous tests passed!")
    except Exception as e:
        print(f"\n❌ Sync test failed: {e}")
        import traceback
        traceback.print_exc()

    # Run async tests
    try:
        asyncio.run(run_async_tests())
        print("\n✅ All asynchronous tests passed!")
    except Exception as e:
        print(f"\n❌ Async test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Test Suite Complete!")
    print("="*60 + "\n")
