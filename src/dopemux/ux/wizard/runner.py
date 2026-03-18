"""WizardRunner — orchestrates the 9-stage guided extraction wizard."""

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
from .prescan_stages import run_code_intelligence
from .prompts import run_prompt_setup
from .stages import StageResult, StageStatus, WizardState
from .summary import run_summary


class WizardRunner:
    """Orchestrates the 9-stage guided extraction wizard.

    Per DC3, stages are collapsed for ADHD attention budget:
    - Prescan config merged into Welcome (mode selector)
    - Feature archaeology merged into Corpus Audit (deep mode)
    - Quality gate merged into Summary

    Stages:
        0  Welcome & Mode       — system checks + mode selector
        1  Repo Health           — branch, clean state, root detection
        2  Corpus Audit          — prescan + archaeology (if deep mode)
        3  Prompt Setup          — promptset configuration
        4  Cost Profile          — routing policy selection + savings estimate
        5  Partition Preview     — phase mapping + router intelligence
        6  Code Intelligence     — hotspots, dead code, hubs, coverage
        7  Extraction            — per-phase with intelligence briefs
        8  Summary & QA          — completion summary + quality gate
    """

    def __init__(
        self,
        execute: bool = False,
        educate: bool = True,
        routing_policy: str = "balanced_openrouter",
        workers: int = 10,
        deep_mode: bool = False,
    ) -> None:
        self.state = WizardState(
            execute_mode=execute,
            educate_mode=educate,
            selected_policy=routing_policy,
            workers=workers,
            deep_mode=deep_mode,
            run_id=datetime.now().strftime("RUN-%Y%m%dT%H%M%S"),
        )

    def run(self) -> None:
        """Execute the wizard stages in sequence."""
        stages = [
            (0, "Welcome & Mode", "🔬", run_welcome),
            (1, "Repo Health", "🩺", run_repo_health),
            (2, "Corpus Audit", "📊", run_corpus_audit),
            (3, "Prompt Setup", "⚙️", run_prompt_setup),
            (4, "Cost Profile", "💰", run_cost_selection),
            (5, "Partition Preview", "🧩", run_partition_preview),
            (6, "Code Intelligence", "💻", run_code_intelligence),
            (7, "Extraction", "🚀", run_extraction),
            (8, "Summary & QA", "🏆", run_summary),
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
                    console.print(f"[error]Error in stage {stage_num}: {exc}[/error]")

                result.duration = time.time() - start
                render_stage_complete(stage_num, title, result)

                if result.status == StageStatus.FAILED:
                    console.print(
                        "[error]Stage failed. Aborting wizard.[/error]"
                    )
                    break

        except KeyboardInterrupt:
            console.print("\n[warning]Wizard interrupted by user.[/warning]")

        # Always show summary if we got past stage 2
        if self.state.corpus_stats or self.state.phase_results:
            console.print()
            console.rule("[bold bright_cyan]  Final Summary  [/bold bright_cyan]")
            run_summary(self.state)
