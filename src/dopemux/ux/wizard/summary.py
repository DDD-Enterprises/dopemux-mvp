"""Stage 8: Completion summary and next-steps recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from dopemux.console import console

from .display import render_next_steps, render_summary_panel
from .stages import PHASE_INFO, StageResult, StageStatus, WizardState


def _parse_timeline(run_dir: Path) -> Dict[str, Any]:
    """Parse telemetry/terminal_timeline.jsonl for stats if it exists."""
    timeline_path = run_dir / "telemetry" / "terminal_timeline.jsonl"
    stats: Dict[str, Any] = {
        "events": 0,
        "retries": 0,
        "escalations": 0,
        "failures": 0,
    }

    if not timeline_path.exists():
        return stats

    try:
        with open(timeline_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    stats["events"] += 1
                    event_type = event.get("type", "")
                    if "retry" in event_type.lower():
                        stats["retries"] += 1
                    elif "escalat" in event_type.lower():
                        stats["escalations"] += 1
                    elif "fail" in event_type.lower():
                        stats["failures"] += 1
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass

    return stats


def run_summary(state: WizardState) -> StageResult:
    """Stage 8 — Display final summary, telemetry stats, and next steps."""

    # Main summary panel
    render_summary_panel(state)

    # Phase-by-phase breakdown (if any phases were executed)
    if state.phase_results:
        console.print("\n[bold]Phase Results:[/bold]\n")
        for phase_key, result in sorted(state.phase_results.items()):
            info = PHASE_INFO.get(phase_key, {"icon": "❓", "name": phase_key})
            if result.status == StageStatus.COMPLETED:
                status_str = "[green]✓ Complete[/green]"
            elif result.status == StageStatus.SKIPPED:
                status_str = "[yellow]⏭ Skipped[/yellow]"
            elif result.status == StageStatus.FAILED:
                status_str = f"[red]✗ Failed[/red]  {result.message}"
            else:
                status_str = f"[dim]{result.status.value}[/dim]"

            duration_str = f" ({result.duration:.1f}s)" if result.duration > 0 else ""
            console.print(
                f"  {info['icon']}  [bold]{phase_key}[/bold] {info['name']:22s}  {status_str}{duration_str}"
            )

    # Telemetry stats (if extraction was run)
    if state.execute_mode and state.run_id:
        run_dir = (
            state.repo_root
            / "extraction"
            / "repo-truth-extractor"
            / "v5"
            / "runs"
            / state.run_id
        )
        if run_dir.exists():
            console.print(f"\n[bold]Artifacts:[/bold]  {run_dir}\n")

            # List phase directories
            phase_dirs = sorted(
                d.name for d in run_dir.iterdir() if d.is_dir() and len(d.name) == 1
            )
            if phase_dirs:
                console.print(f"  Phase directories: {', '.join(phase_dirs)}")

            # Parse timeline
            timeline_stats = _parse_timeline(run_dir)
            if timeline_stats["events"] > 0:
                console.print(
                    f"  Telemetry events: {timeline_stats['events']}  "
                    f"(retries: {timeline_stats['retries']}, "
                    f"escalations: {timeline_stats['escalations']}, "
                    f"failures: {timeline_stats['failures']})"
                )

    # Next steps
    render_next_steps(state)

    return StageResult(
        status=StageStatus.COMPLETED,
        message="Summary displayed",
    )
