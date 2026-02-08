"""Parallel command orchestration helpers for the session-manager TUI."""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

from .command_router_enhanced import CommandResult, ErrorCategory, EnhancedCommandRouter


logger = logging.getLogger(__name__)


class ComparisonMode(str, Enum):
    """Output modes for response comparison formatting."""

    SIDE_BY_SIDE = "side_by_side"
    SUMMARY = "summary"


@dataclass
class AggregatedResponse:
    """Parallel execution result container."""

    command: str
    responses: Dict[str, CommandResult]
    started_at: str
    ended_at: str
    total_duration: float
    all_succeeded: bool


class ParallelOrchestrator:
    """Executes one command across multiple AI CLIs concurrently."""

    def __init__(self, command_router: EnhancedCommandRouter):
        self.command_router = command_router

    async def execute_parallel(
        self,
        command: str,
        ai_list: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, str], None]] = None,
        output_callback: Optional[Callable[[str, str], None]] = None,
        error_callback: Optional[Callable[[str, str], None]] = None,
        timeout: int = 300,
    ) -> AggregatedResponse:
        """Run command concurrently for each AI in `ai_list`."""
        targets = ai_list or ["claude", "gemini", "grok"]
        started_dt = datetime.now()
        start_time = time.perf_counter()
        responses: Dict[str, CommandResult] = {}

        def _emit_progress(ai_name: str, message: str):
            if progress_callback:
                progress_callback(ai_name, message)

        async def _execute_for_ai(ai_name: str) -> tuple[str, CommandResult]:
            if not self.command_router.is_available(ai_name):
                return ai_name, CommandResult(
                    return_code=127,
                    output="",
                    error_output=f"{ai_name} CLI not available",
                    duration_seconds=0.0,
                    error_category=ErrorCategory.CLI_NOT_FOUND,
                    error_message=self.command_router.get_installation_hint(ai_name),
                )

            _emit_progress(ai_name, "▶ Starting command")
            ai_start = time.perf_counter()

            try:
                result = await self.command_router.execute_command(
                    ai=ai_name,
                    command=command,
                    output_callback=(
                        (lambda line: output_callback(ai_name, line))
                        if output_callback
                        else None
                    ),
                    error_callback=(
                        (lambda line: error_callback(ai_name, line))
                        if error_callback
                        else None
                    ),
                    timeout=timeout,
                    enable_retry=True,
                )
                _emit_progress(
                    ai_name,
                    f"✔ Finished ({result.duration_seconds:.1f}s)"
                    if result.success
                    else f"✖ Failed ({result.duration_seconds:.1f}s)",
                )
                return ai_name, result
            except Exception as exc:
                duration = time.perf_counter() - ai_start
                _emit_progress(ai_name, f"✖ Error ({duration:.1f}s)")
                return ai_name, CommandResult(
                    return_code=-1,
                    output="",
                    error_output=str(exc),
                    duration_seconds=duration,
                    error_category=ErrorCategory.UNKNOWN,
                    error_message=f"Unexpected orchestration error: {exc}",
                )

        results = await asyncio.gather(*[_execute_for_ai(ai) for ai in targets])
        for ai_name, result in results:
            responses[ai_name] = result

        total_duration = time.perf_counter() - start_time
        all_succeeded = bool(responses) and all(result.success for result in responses.values())

        return AggregatedResponse(
            command=command,
            responses=responses,
            started_at=started_dt.isoformat(),
            ended_at=datetime.now().isoformat(),
            total_duration=total_duration,
            all_succeeded=all_succeeded,
        )

    def generate_comparison(
        self,
        aggregated: AggregatedResponse,
        mode: ComparisonMode = ComparisonMode.SIDE_BY_SIDE,
    ) -> str:
        """Render aggregated response as markdown text."""
        if mode == ComparisonMode.SUMMARY:
            return self._render_summary(aggregated)
        return self._render_side_by_side(aggregated)

    def _render_summary(self, aggregated: AggregatedResponse) -> str:
        lines = [
            "## Parallel Execution Summary",
            f"- Command: `{aggregated.command}`",
            f"- Duration: {aggregated.total_duration:.2f}s",
            f"- All Succeeded: {'yes' if aggregated.all_succeeded else 'no'}",
        ]

        for ai_name, result in aggregated.responses.items():
            status = "success" if result.success else "failed"
            lines.append(
                f"- {ai_name}: {status} (exit={result.return_code}, {result.duration_seconds:.2f}s)"
            )

        return "\n".join(lines)

    def _render_side_by_side(self, aggregated: AggregatedResponse) -> str:
        lines = [
            f"# Comparison: `{aggregated.command}`",
            f"Duration: {aggregated.total_duration:.2f}s",
            "",
        ]

        for ai_name, result in aggregated.responses.items():
            status = "SUCCESS" if result.success else "FAILED"
            lines.append(f"## {ai_name.upper()} ({status})")
            lines.append(
                f"Exit Code: {result.return_code} | Duration: {result.duration_seconds:.2f}s"
            )
            lines.append("")

            body = result.output.strip() if result.output.strip() else result.error_output.strip()
            if not body:
                body = result.error_message or "(no output)"
            lines.append(body[:8000])
            lines.append("")

        return "\n".join(lines)


_orchestrator_instance: Optional[ParallelOrchestrator] = None


def get_parallel_orchestrator(command_router: EnhancedCommandRouter) -> ParallelOrchestrator:
    """Get singleton parallel orchestrator bound to the current command router."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ParallelOrchestrator(command_router)
    return _orchestrator_instance
