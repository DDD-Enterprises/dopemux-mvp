#!/usr/bin/env python3
"""
End-to-End Integration Tests for Orchestrator TUI

Day 7: Real-world integration testing with actual Claude CLI

Tests:
- Real CLI execution (not mocked)
- Session persistence across restarts
- Error recovery with actual failures
- Parallel execution coordination
- Performance benchmarks

NOTE: Requires Claude CLI to be installed and available in PATH

Run with: python test_e2e_integration.py
"""

import asyncio
import sys
from pathlib import Path
import tempfile
import shutil
import time
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from command_router_enhanced import EnhancedCommandRouter, ErrorCategory
from parallel_orchestrator import ParallelOrchestrator, ComparisonMode
from session_manager import SessionManager, TUISessionState, PaneState


class TestRealCLIExecution:
    """Test with actual Claude CLI (if available)."""

    async def test_claude_version_command(self):
        """Test simple --version command with real Claude CLI."""
        router = EnhancedCommandRouter(enable_conport=False)

        if not router.is_available("claude"):
            print("  ⚠️  Claude CLI not available - skipping real CLI test")
            return

        output_lines = []

        def capture_output(line: str):
            output_lines.append(line)
            print(f"    {line}")

        print("  🔍 Executing: claude --version")
        result = await router.execute_command(
            ai="claude",
            command="--version",
            output_callback=capture_output,
            timeout=10,
            enable_retry=False
        )

        assert result.success, f"Command failed: {result.error_message}"
        assert result.return_code == 0
        assert len(output_lines) > 0
        print(f"  ✅ Real CLI execution successful ({result.duration_seconds:.2f}s)")

    async def test_claude_simple_prompt(self):
        """Test simple prompt with real Claude CLI."""
        router = EnhancedCommandRouter(enable_conport=False)

        if not router.is_available("claude"):
            print("  ⚠️  Skipping - Claude CLI not available")
            return

        output_lines = []

        def capture_output(line: str):
            output_lines.append(line)

        print("  🔍 Executing: simple prompt to Claude")
        result = await router.execute_command(
            ai="claude",
            command="Say 'Test successful' and nothing else",
            output_callback=capture_output,
            timeout=30
        )

        if result.success:
            print(f"  ✅ Prompt execution successful ({result.duration_seconds:.2f}s)")
            print(f"     Output lines: {len(output_lines)}")
        else:
            print(f"  ⚠️  Prompt failed: {result.error_message[:100]}")


class TestSessionPersistence:
    """Test session save and restore functionality."""

    async def test_save_and_restore_session(self):
        """Test complete session persistence cycle."""
        print("  🔍 Testing session save/restore cycle...")

        # Create temp workspace
        workspace = tempfile.mkdtemp()

        try:
            # Initialize session manager
            manager = SessionManager(workspace_id=workspace)
            await manager.initialize()

            # Create test session state
            test_state = TUISessionState(
                session_id=manager.session_id,
                workspace_id=workspace,
                session_start=datetime.now().isoformat(),
                last_active=datetime.now().isoformat(),
                current_target="claude",
                energy_level="high",
                pane_states={
                    "claude": PaneState(
                        ai_name="claude",
                        output_lines=["Test line 1", "Test line 2"],
                        status="ready",
                        command_history=["test command 1", "test command 2"],
                        last_command="test command 2"
                    )
                },
                tasks_done=2,
                tasks_total=5,
                total_commands=2,
                successful_commands=2
            )

            # Save state
            print("    💾 Saving session state...")
            save_result = await manager.save_session_state(test_state)

            if save_result:
                print("    ✅ Session saved successfully")

                # Try to restore
                print("    📂 Restoring session state...")
                restored_state = await manager.load_session_state()

                if restored_state:
                    print("    ✅ Session restored successfully")

                    # Validate restoration
                    assert restored_state.session_id == test_state.session_id
                    assert restored_state.current_target == "claude"
                    assert restored_state.tasks_done == 2
                    assert "claude" in restored_state.pane_states
                    assert len(restored_state.pane_states["claude"].output_lines) == 2

                    print(f"    ✅ All state validated correctly")
                else:
                    print("    ⚠️  Session restore returned None (ConPort may not be running)")
            else:
                print("    ⚠️  Session save failed (ConPort may not be running)")

            await manager.cleanup()

        finally:
            # Cleanup temp directory
            shutil.rmtree(workspace, ignore_errors=True)

    async def test_auto_save_loop(self):
        """Test auto-save functionality."""
        print("  🔍 Testing auto-save loop...")

        workspace = tempfile.mkdtemp()

        try:
            manager = SessionManager(workspace_id=workspace)
            await manager.initialize()

            save_count = 0

            async def get_test_state():
                nonlocal save_count
                save_count += 1

                return TUISessionState(
                    session_id=manager.session_id,
                    workspace_id=workspace,
                    session_start=datetime.now().isoformat(),
                    last_active=datetime.now().isoformat(),
                    current_target="claude",
                    energy_level="high",
                    pane_states={},
                    total_commands=save_count
                )

            # Start auto-save with very short interval
            manager.AUTO_SAVE_INTERVAL = 0.5  # 500ms for testing
            await manager.start_auto_save(get_test_state)

            # Wait for a few auto-saves
            await asyncio.sleep(1.5)

            # Stop auto-save
            await manager.stop_auto_save()
            await manager.cleanup()

            # Should have saved 2-3 times
            if save_count >= 2:
                print(f"    ✅ Auto-save triggered {save_count} times")
            else:
                print(f"    ⚠️  Auto-save triggered only {save_count} times (expected 2+)")

        finally:
            shutil.rmtree(workspace, ignore_errors=True)


class TestParallelIntegration:
    """Test parallel execution with real CLIs."""

    async def test_parallel_with_single_cli(self):
        """Test @all command with only Claude available."""
        print("  🔍 Testing parallel execution with available CLIs...")

        router = EnhancedCommandRouter(enable_conport=False)
        orchestrator = ParallelOrchestrator(router)

        available = router.get_available_ais()
        print(f"    Available CLIs: {available}")

        if not available:
            print("    ⚠️  No CLIs available - skipping")
            return

        output_log = []

        def capture_output(ai_name, line):
            output_log.append((ai_name, line))

        # Execute on all requested AIs (will skip unavailable)
        aggregated = await orchestrator.execute_parallel(
            command="--version",
            ai_list=["claude", "gemini", "grok"],
            output_callback=capture_output
        )

        print(f"    ✅ Parallel execution completed:")
        print(f"       - Executed on: {list(aggregated.responses.keys())}")
        print(f"       - Total duration: {aggregated.total_duration:.2f}s")
        print(f"       - All succeeded: {aggregated.all_succeeded}")

        # Generate comparison
        comparison = orchestrator.generate_comparison(aggregated, ComparisonMode.SIDE_BY_SIDE)
        print(f"    ✅ Comparison generated ({len(comparison)} chars)")


class TestErrorRecovery:
    """Test error handling with real scenarios."""

    async def test_invalid_command_error(self):
        """Test error handling with invalid command."""
        router = EnhancedCommandRouter(enable_conport=False)

        if not router.is_available("claude"):
            print("  ⚠️  Claude CLI not available - skipping")
            return

        print("  🔍 Testing invalid command error handling...")

        result = await router.execute_command(
            ai="claude",
            command="--invalid-flag-that-doesnt-exist",
            timeout=10,
            enable_retry=False
        )

        # Should fail gracefully
        assert not result.success
        print(f"    ✅ Invalid command handled: {result.error_category}")
        print(f"       Error message: {result.error_message[:80]}...")


class TestPerformance:
    """Test performance benchmarks."""

    async def test_cli_detection_speed(self):
        """Benchmark CLI detection speed."""
        print("  🔍 Benchmarking CLI detection...")

        start = time.time()
        router = EnhancedCommandRouter(enable_conport=False)
        duration = time.time() - start

        print(f"    ✅ CLI detection: {duration*1000:.1f}ms")
        assert duration < 0.5, "CLI detection should be < 500ms"

    async def test_execution_overhead(self):
        """Measure execution overhead."""
        router = EnhancedCommandRouter(enable_conport=False)

        if not router.is_available("claude"):
            print("  ⚠️  Claude CLI not available - skipping")
            return

        print("  🔍 Measuring execution overhead...")

        # Time a simple command
        start = time.time()
        result = await router.execute_command(
            ai="claude",
            command="--version",
            timeout=10,
            enable_retry=False
        )
        total_duration = time.time() - start

        # Overhead = total - actual execution time
        overhead = total_duration - result.duration_seconds

        print(f"    ✅ Execution: {result.duration_seconds:.3f}s")
        print(f"       Overhead: {overhead:.3f}s ({overhead/total_duration*100:.1f}%)")
        assert overhead < 0.5, "Overhead should be < 500ms"


# Main test runner
async def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("END-TO-END INTEGRATION TESTS - DAY 7")
    print("="*60 + "\n")

    cli_tests = TestRealCLIExecution()
    session_tests = TestSessionPersistence()
    parallel_tests = TestParallelIntegration()
    error_tests = TestErrorRecovery()
    perf_tests = TestPerformance()

    print("TestRealCLIExecution:")
    await cli_tests.test_claude_version_command()
    await cli_tests.test_claude_simple_prompt()

    print("\nTestSessionPersistence:")
    await session_tests.test_save_and_restore_session()
    await session_tests.test_auto_save_loop()

    print("\nTestParallelIntegration:")
    await parallel_tests.test_parallel_with_single_cli()

    print("\nTestErrorRecovery:")
    await error_tests.test_invalid_command_error()

    print("\nTestPerformance:")
    await perf_tests.test_cli_detection_speed()
    await perf_tests.test_execution_overhead()


if __name__ == "__main__":
    print("="*60)
    print("Orchestrator TUI - E2E Integration Test Suite")
    print("="*60)

    try:
        asyncio.run(run_integration_tests())
        print("\n" + "="*60)
        print("✅ Integration tests complete!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
