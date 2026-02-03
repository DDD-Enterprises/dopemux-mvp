#!/usr/bin/env python3
"""
Test Suite for Parallel Orchestrator (Day 5)

Tests:
- Response aggregation across multiple AIs
- Synchronized output display
- Comparison view generation
- Progress tracking for parallel operations
- Error handling in parallel execution
- Performance metrics

Run with: python test_parallel_orchestrator.py
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from parallel_orchestrator import (
    ParallelOrchestrator,
    AIResponse,
    AggregatedResponse,
    ComparisonMode
)
from command_router_enhanced import CommandResult, ErrorCategory


class MockCommandRouter:
    """Mock command router for testing."""

    def __init__(self, available_ais=None):
        self.available_ais = available_ais or ["claude"]
        self.execution_log = []

    def is_available(self, ai: str) -> bool:
        return ai in self.available_ais

    def get_available_ais(self) -> list:
        return self.available_ais

    async def execute_command(self, ai, command, output_callback=None, error_callback=None, timeout=300, enable_retry=True):
        """Mock command execution."""
        self.execution_log.append((ai, command))

        # Simulate execution
        await asyncio.sleep(0.1)

        # Call callbacks if provided
        if output_callback:
            output_callback(f"Mock response from {ai}")
            output_callback(f"Command: {command}")

        # Return mock result
        return CommandResult(
            return_code=0,
            output=f"Mock output from {ai}",
            error_output="",
            duration_seconds=0.1,
            retry_count=0
        )


class TestParallelExecution:
    """Test parallel execution capabilities."""

    async def test_execute_on_multiple_ais(self):
        """Test executing command on multiple AIs."""
        router = MockCommandRouter(available_ais=["claude", "gemini", "grok"])
        orchestrator = ParallelOrchestrator(router)

        result = await orchestrator.execute_parallel(
            command="test command",
            ai_list=["claude", "gemini", "grok"]
        )

        assert isinstance(result, AggregatedResponse)
        assert len(result.responses) == 3
        assert result.all_succeeded
        assert "claude" in result.responses
        assert "gemini" in result.responses
        assert "grok" in result.responses
        print(f"  ✅ Executed on {len(result.responses)} AIs successfully")

    async def test_skip_unavailable_ais(self):
        """Test that unavailable AIs are skipped."""
        router = MockCommandRouter(available_ais=["claude"])  # Only Claude available
        orchestrator = ParallelOrchestrator(router)

        progress_messages = []

        def capture_progress(ai_name, message):
            progress_messages.append((ai_name, message))

        result = await orchestrator.execute_parallel(
            command="test",
            ai_list=["claude", "gemini", "grok"],
            progress_callback=capture_progress
        )

        # Should only execute on Claude
        assert len(result.responses) == 1
        assert "claude" in result.responses

        # Should have warnings for unavailable
        unavailable_warnings = [m for ai, m in progress_messages if "not available" in m]
        assert len(unavailable_warnings) == 2
        print(f"  ✅ Skipped {len(unavailable_warnings)} unavailable AIs")

    async def test_parallel_output_callbacks(self):
        """Test that output callbacks work during parallel execution."""
        router = MockCommandRouter(available_ais=["claude", "gemini"])
        orchestrator = ParallelOrchestrator(router)

        output_log = []

        def capture_output(ai_name, line):
            output_log.append((ai_name, line))

        await orchestrator.execute_parallel(
            command="test",
            ai_list=["claude", "gemini"],
            output_callback=capture_output
        )

        # Should have received outputs from both AIs
        claude_outputs = [line for ai, line in output_log if ai == "claude"]
        gemini_outputs = [line for ai, line in output_log if ai == "gemini"]

        assert len(claude_outputs) > 0
        assert len(gemini_outputs) > 0
        print(f"  ✅ Received outputs: {len(claude_outputs)} from Claude, {len(gemini_outputs)} from Gemini")


class TestResponseAggregation:
    """Test response aggregation features."""

    async def test_aggregated_response_structure(self):
        """Test AggregatedResponse data structure."""
        router = MockCommandRouter(available_ais=["claude"])
        orchestrator = ParallelOrchestrator(router)

        result = await orchestrator.execute_parallel(
            command="test",
            ai_list=["claude"]
        )

        # Check structure
        assert hasattr(result, 'command')
        assert hasattr(result, 'responses')
        assert hasattr(result, 'total_duration')
        assert hasattr(result, 'all_succeeded')
        assert result.command == "test"
        assert isinstance(result.responses, dict)
        assert isinstance(result.total_duration, float)
        assert isinstance(result.all_succeeded, bool)
        print("  ✅ AggregatedResponse structure valid")

    async def test_execution_history_tracking(self):
        """Test that execution history is tracked."""
        router = MockCommandRouter(available_ais=["claude"])
        orchestrator = ParallelOrchestrator(router)

        # Execute 3 commands
        for i in range(3):
            await orchestrator.execute_parallel(
                command=f"test {i}",
                ai_list=["claude"]
            )

        assert len(orchestrator.execution_history) == 3
        print(f"  ✅ Execution history: {len(orchestrator.execution_history)} entries")


class TestComparisonViews:
    """Test comparison view generation."""

    async def test_side_by_side_comparison(self):
        """Test side-by-side comparison generation."""
        router = MockCommandRouter(available_ais=["claude", "gemini"])
        orchestrator = ParallelOrchestrator(router)

        result = await orchestrator.execute_parallel(
            command="test",
            ai_list=["claude", "gemini"]
        )

        comparison = orchestrator.generate_comparison(result, ComparisonMode.SIDE_BY_SIDE)

        assert "SIDE-BY-SIDE" in comparison
        assert "claude" in comparison.lower()
        assert "gemini" in comparison.lower()
        assert "Duration" in comparison
        print("  ✅ Side-by-side comparison generated")

    async def test_sequential_comparison(self):
        """Test sequential comparison generation."""
        router = MockCommandRouter(available_ais=["claude"])
        orchestrator = ParallelOrchestrator(router)

        result = await orchestrator.execute_parallel(
            command="test",
            ai_list=["claude"]
        )

        comparison = orchestrator.generate_comparison(result, ComparisonMode.SEQUENTIAL)

        assert "SEQUENTIAL" in comparison
        assert "claude" in comparison.lower()
        print("  ✅ Sequential comparison generated")

    async def test_consensus_comparison(self):
        """Test consensus view generation."""
        router = MockCommandRouter(available_ais=["claude", "gemini", "grok"])
        orchestrator = ParallelOrchestrator(router)

        result = await orchestrator.execute_parallel(
            command="test",
            ai_list=["claude", "gemini", "grok"]
        )

        comparison = orchestrator.generate_comparison(result, ComparisonMode.CONSENSUS)

        assert "CONSENSUS" in comparison
        assert "Successful:" in comparison
        print("  ✅ Consensus comparison generated")


class TestStatistics:
    """Test statistics and metrics."""

    async def test_execution_statistics(self):
        """Test execution statistics calculation."""
        router = MockCommandRouter(available_ais=["claude", "gemini"])
        orchestrator = ParallelOrchestrator(router)

        # Execute multiple commands
        for i in range(5):
            await orchestrator.execute_parallel(
                command=f"test {i}",
                ai_list=["claude", "gemini"]
            )

        stats = orchestrator.get_execution_stats()

        assert stats["total_executions"] == 5
        assert stats["all_succeeded_count"] == 5
        assert stats["success_rate"] == 100.0
        assert stats["avg_ais_per_execution"] == 2.0
        print(f"  ✅ Stats: {stats['total_executions']} executions, {stats['success_rate']}% success")


class TestErrorHandling:
    """Test error handling in parallel execution."""

    async def test_mixed_success_failure(self):
        """Test handling when some AIs succeed and others fail."""
        router = MockCommandRouter(available_ais=["claude", "gemini"])
        orchestrator = ParallelOrchestrator(router)

        # Mock router to fail on gemini
        async def mock_execute(ai, command, **kwargs):
            if ai == "gemini":
                return CommandResult(
                    return_code=1,
                    output="",
                    error_output="Mock error",
                    duration_seconds=0.1,
                    error_category=ErrorCategory.UNKNOWN,
                    error_message="Failed"
                )
            return CommandResult(
                return_code=0,
                output="Success",
                error_output="",
                duration_seconds=0.1
            )

        router.execute_command = mock_execute

        result = await orchestrator.execute_parallel(
            command="test",
            ai_list=["claude", "gemini"]
        )

        assert len(result.responses) == 2
        assert not result.all_succeeded  # Mixed results
        assert result.responses["claude"].success
        assert not result.responses["gemini"].success
        print("  ✅ Mixed success/failure handled correctly")


# Test runner
async def run_async_tests():
    """Run all async tests."""
    print("\n" + "="*60)
    print("PARALLEL ORCHESTRATOR TESTS")
    print("="*60 + "\n")

    execution_tests = TestParallelExecution()
    aggregation_tests = TestResponseAggregation()
    comparison_tests = TestComparisonViews()
    stats_tests = TestStatistics()
    error_tests = TestErrorHandling()

    print("TestParallelExecution:")
    await execution_tests.test_execute_on_multiple_ais()
    await execution_tests.test_skip_unavailable_ais()
    await execution_tests.test_parallel_output_callbacks()

    print("\nTestResponseAggregation:")
    await aggregation_tests.test_aggregated_response_structure()
    await aggregation_tests.test_execution_history_tracking()

    print("\nTestComparisonViews:")
    await comparison_tests.test_side_by_side_comparison()
    await comparison_tests.test_sequential_comparison()
    await comparison_tests.test_consensus_comparison()

    print("\nTestStatistics:")
    await stats_tests.test_execution_statistics()

    print("\nTestErrorHandling:")
    await error_tests.test_mixed_success_failure()


if __name__ == "__main__":
    print("="*60)
    print("Parallel Orchestrator Test Suite - Day 5")
    print("="*60)

    try:
        asyncio.run(run_async_tests())
        print("\n✅ All tests passed!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
