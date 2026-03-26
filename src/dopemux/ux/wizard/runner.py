"""WizardRunner — orchestrates the 8-stage guided extraction wizard."""

from __future__ import annotations

import time
from datetime import datetime

from dopemux.console import console

from .corpus import run_corpus_audit
from .cost_profiles import run_cost_selection
from .display import render_stage_complete, render_stage_header
from .extraction import run_extraction
from .partitions import run_partition_preview
from .preflight import run_repo_health, run_welcome
from .prompts import run_prompt_setup
from .stages import StageResult, StageStatus, WizardState
from .summary import run_summary


class WizardRunner:
    """Orchestrates the 7-stage guided extraction wizard.

    Stages:
        0  Welcome & system checks
        1  Repository health
        2  Corpus audit (prescan)
        3  Prompt system setup
        4  Cost profile selection
        5  Partition preview
        6  Extraction (phase-by-phase)
        7  Summary & next steps
    """

    def __init__(
        self,
        execute: bool = False,
        educate: bool = True,
        routing_policy: str = "balanced_openrouter",
        workers: int = 10,
    ) -> None:
        self.state = WizardState(
            execute_mode=execute,
            educate_mode=educate,
            selected_policy=routing_policy,
            workers=workers,
            run_id=datetime.now().strftime("RUN-%Y%m%dT%H%M%S"),
        )

    def run(self) -> None:
        """Execute the wizard stages in sequence."""
        stages = [
            (0, "Welcome", "🔬", run_welcome),
            (1, "Repo Health", "🩺", run_repo_health),
            (2, "Corpus Audit", "📊", run_corpus_audit),
            (3, "Prompt Setup", "⚙️", run_prompt_setup),
            (4, "Cost Profile", "💰", run_cost_selection),
            (5, "Partition Preview", "🧩", run_partition_preview),
            (6, "Extraction", "🚀", run_extraction),
            (7, "Summary", "🏆", run_summary),
        ]

        try:
            for stage_num, title, icon, func in stages:
                render_stage_header(stage_num, title, icon)
                start = time.time()

                try:
                    result = func(self.state)
                except Exception as exc:
                    result = StageResult(
                        status=StageStatus.FAILED,
                        message=f"Unexpected error: {exc}",
                    )
                    console.print(f"[bold red]Error in stage {stage_num}: {exc}[/bold red]")

                result.duration = time.time() - start
                render_stage_complete(stage_num, title, result)

                if result.status == StageStatus.FAILED:
                    console.print(
                        "[bold red]Stage failed. Aborting wizard.[/bold red]"
                    )
                    break

        except KeyboardInterrupt:
            console.print("\n[yellow]Wizard interrupted by user.[/yellow]")

        # Always show summary if we got past stage 2
        if self.state.corpus_stats or self.state.phase_results:
            console.print()
            console.rule("[bold bright_cyan]  Final Summary  [/bold bright_cyan]")
            run_summary(self.state)
