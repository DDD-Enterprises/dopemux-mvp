"""
Parallel AI Orchestrator

Day 5: Enhanced multi-AI parallel execution with:
- Response aggregation across multiple AIs
- Synchronized output display
- Response comparison capabilities
- Progress tracking for parallel operations
- ADHD-optimized result presentation

Part of IP-005 Day 5: Multi-AI coordination
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional
from enum import Enum


class ComparisonMode(Enum):
    """Modes for comparing AI responses."""
    SIDE_BY_SIDE = "side_by_side"  # Show outputs next to each other
    SEQUENTIAL = "sequential"  # Show one after another
    DIFF = "diff"  # Highlight differences
    CONSENSUS = "consensus"  # Show agreements/disagreements


@dataclass
class AIResponse:
    """Response from a single AI."""
    ai_name: str
    command: str
    output: str
    error_output: str
    return_code: int
    duration_seconds: float
    timestamp: datetime
    success: bool


@dataclass
class AggregatedResponse:
    """Aggregated responses from multiple AIs."""
    command: str
    responses: Dict[str, AIResponse]
    total_duration: float
    all_succeeded: bool
    comparison: Optional[str] = None


class ParallelOrchestrator:
    """
    Orchestrates parallel command execution across multiple AIs.

    Features:
    - Executes commands on multiple AIs concurrently
    - Aggregates responses for comparison
    - Tracks progress across all executions
    - Generates comparison views
    - ADHD-optimized: Clear progress, visual indicators
    """

    def __init__(self, command_router):
        """
        Initialize parallel orchestrator.

        Args:
            command_router: Enhanced command router instance
        """
        self.command_router = command_router
        self.execution_history: List[AggregatedResponse] = []

    async def execute_parallel(
        self,
        command: str,
        ai_list: List[str],
        progress_callback: Optional[Callable[[str, str], None]] = None,
        output_callback: Optional[Callable[[str, str], None]] = None,
        error_callback: Optional[Callable[[str, str], None]] = None
    ) -> AggregatedResponse:
        """
        Execute command on multiple AIs in parallel.

        Args:
            command: Command to execute
            ai_list: List of AI names to execute on
            progress_callback: Called with (ai_name, progress_message)
            output_callback: Called with (ai_name, output_line)
            error_callback: Called with (ai_name, error_message)

        Returns:
            Aggregated response from all AIs
        """
        start_time = datetime.now()

        # Filter to available AIs only
        available_ais = [
            ai for ai in ai_list
            if self.command_router.is_available(ai)
        ]

        if not available_ais:
            # No AIs available
            return AggregatedResponse(
                command=command,
                responses={},
                total_duration=0.0,
                all_succeeded=False,
                comparison="❌ No AI CLIs available"
            )

        # Notify about unavailable AIs
        unavailable = set(ai_list) - set(available_ais)
        if unavailable and progress_callback:
            for ai in unavailable:
                progress_callback(ai, f"⚠️ {ai} CLI not available, skipping")

        # Create per-AI callbacks
        def make_output_cb(ai_name: str):
            def callback(line: str):
                if output_callback:
                    output_callback(ai_name, line)
            return callback

        def make_error_cb(ai_name: str):
            def callback(line: str):
                if error_callback:
                    error_callback(ai_name, line)
            return callback

        # Execute in parallel
        tasks = []
        for ai in available_ais:
            if progress_callback:
                progress_callback(ai, f"🚀 Starting execution...")

            task = self.command_router.execute_command(
                ai=ai,
                command=command,
                output_callback=make_output_cb(ai),
                error_callback=make_error_cb(ai),
                timeout=300,
                enable_retry=True
            )
            tasks.append((ai, task))

        # Wait for all to complete
        results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        # Aggregate responses
        responses = {}
        for (ai_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                # Execution raised an exception
                responses[ai_name] = AIResponse(
                    ai_name=ai_name,
                    command=command,
                    output="",
                    error_output=str(result),
                    return_code=-1,
                    duration_seconds=0.0,
                    timestamp=datetime.now(),
                    success=False
                )
            else:
                # Normal CommandResult
                responses[ai_name] = AIResponse(
                    ai_name=ai_name,
                    command=command,
                    output=result.output,
                    error_output=result.error_output,
                    return_code=result.return_code,
                    duration_seconds=result.duration_seconds,
                    timestamp=datetime.now(),
                    success=result.success
                )

        # Calculate total duration
        total_duration = (datetime.now() - start_time).total_seconds()

        # Check if all succeeded
        all_succeeded = all(r.success for r in responses.values())

        # Create aggregated response
        aggregated = AggregatedResponse(
            command=command,
            responses=responses,
            total_duration=total_duration,
            all_succeeded=all_succeeded
        )

        # Track in history
        self.execution_history.append(aggregated)

        return aggregated

    def generate_comparison(
        self,
        aggregated: AggregatedResponse,
        mode: ComparisonMode = ComparisonMode.SIDE_BY_SIDE
    ) -> str:
        """
        Generate comparison view of AI responses.

        Args:
            aggregated: Aggregated response to compare
            mode: Comparison mode

        Returns:
            Formatted comparison string
        """
        if not aggregated.responses:
            return "No responses to compare"

        if mode == ComparisonMode.SIDE_BY_SIDE:
            return self._generate_side_by_side(aggregated)
        elif mode == ComparisonMode.SEQUENTIAL:
            return self._generate_sequential(aggregated)
        elif mode == ComparisonMode.CONSENSUS:
            return self._generate_consensus(aggregated)
        else:
            return self._generate_sequential(aggregated)

    def _generate_side_by_side(self, aggregated: AggregatedResponse) -> str:
        """Generate side-by-side comparison."""
        lines = ["=" * 60]
        lines.append("📊 SIDE-BY-SIDE COMPARISON")
        lines.append("=" * 60)
        lines.append(f"Command: {aggregated.command}")
        lines.append(f"Duration: {aggregated.total_duration:.1f}s")
        lines.append("")

        # Show each AI response
        for ai_name, response in aggregated.responses.items():
            status = "✅" if response.success else "❌"
            lines.append(f"{status} {ai_name.upper()} ({response.duration_seconds:.1f}s)")
            lines.append("-" * 60)

            if response.success:
                # Show first 5 lines of output
                all_lines = response.output.split('\n')
                output_lines = all_lines[:5]
                for line in output_lines:
                    lines.append(f"  {line}")
                if len(all_lines) > 5:
                    remaining = len(all_lines) - 5
                    lines.append(f"  ... (+{remaining} more lines)")
            else:
                lines.append(f"  Error: {response.error_output[:100]}")

            lines.append("")

        return "\n".join(lines)

    def _generate_sequential(self, aggregated: AggregatedResponse) -> str:
        """Generate sequential comparison."""
        lines = ["=" * 60]
        lines.append("📋 SEQUENTIAL COMPARISON")
        lines.append("=" * 60)

        for ai_name, response in aggregated.responses.items():
            status = "✅" if response.success else "❌"
            lines.append(f"\n{status} {ai_name.upper()}")
            lines.append(f"Duration: {response.duration_seconds:.1f}s")
            lines.append("-" * 60)
            lines.append(response.output if response.success else f"Error: {response.error_output}")

        return "\n".join(lines)

    def _generate_consensus(self, aggregated: AggregatedResponse) -> str:
        """Generate consensus view (agreements/disagreements)."""
        lines = ["=" * 60]
        lines.append("🤝 CONSENSUS ANALYSIS")
        lines.append("=" * 60)
        lines.append(f"Command: {aggregated.command}")
        lines.append("")

        successful = [r for r in aggregated.responses.values() if r.success]
        failed = [r for r in aggregated.responses.values() if not r.success]

        lines.append(f"✅ Successful: {len(successful)}/{len(aggregated.responses)}")
        lines.append(f"❌ Failed: {len(failed)}/{len(aggregated.responses)}")
        lines.append("")

        if successful:
            lines.append("Successful AIs:")
            for response in successful:
                lines.append(f"  • {response.ai_name} ({response.duration_seconds:.1f}s)")

        if failed:
            lines.append("\nFailed AIs:")
            for response in failed:
                lines.append(f"  • {response.ai_name}: {response.error_output[:50]}...")

        # TODO: Actual consensus detection (similar outputs)
        lines.append("\nNote: Advanced consensus detection coming in future update")

        return "\n".join(lines)

    def get_execution_stats(self) -> dict:
        """Get statistics about parallel executions."""
        if not self.execution_history:
            return {"total": 0, "avg_duration": 0.0, "success_rate": 0.0}

        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e.all_succeeded)
        avg_duration = sum(e.total_duration for e in self.execution_history) / total

        return {
            "total_executions": total,
            "all_succeeded_count": successful,
            "success_rate": (successful / total) * 100,
            "avg_duration": avg_duration,
            "avg_ais_per_execution": sum(
                len(e.responses) for e in self.execution_history
            ) / total
        }


# Singleton instance
_orchestrator_instance: Optional[ParallelOrchestrator] = None


def get_parallel_orchestrator(command_router) -> ParallelOrchestrator:
    """Get or create parallel orchestrator singleton."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ParallelOrchestrator(command_router)
    return _orchestrator_instance
