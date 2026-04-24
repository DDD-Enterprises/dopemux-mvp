"""Code intelligence summary helper for prescan flows.

Other prescan stages (prescan config, archaeology, quality gate) are merged
into existing stages per DC3: prescan config → welcome, archaeology → corpus
audit, quality gate → summary.
"""

from __future__ import annotations

from dopemux.console import console

from .display import render_code_intel_summary, render_educational_panel
from .stages import StageResult, StageStatus, WizardState


def run_code_intelligence(state: WizardState) -> StageResult:
    """Display code intelligence summary.

    Shows dead code candidates, complexity hotspots, coverage gaps,
    hub files, and extraction priority ordering.
    """
    report = state.code_intelligence
    if not report:
        console.print("  [text.dim]No code intelligence data available (prescan may not have run).[/text.dim]")
        return StageResult(
            status=StageStatus.SKIPPED,
            message="No code intelligence available",
        )

    summary = report.get("summary", {})
    total_code = summary.get("total_code_files", 0)
    if total_code == 0:
        console.print("  [text.dim]No code files detected in corpus.[/text.dim]")
        return StageResult(
            status=StageStatus.SKIPPED,
            message="No code files in corpus",
        )

    # Render the combined code intelligence display
    render_code_intel_summary(report)

    # Educational content
    if state.educate_mode:
        render_educational_panel(
            "How code intelligence works",
            "The prescan analyses your codebase to build a structural map:\n\n"
            "  • PageRank scores identify architecturally important files\n"
            "  • Hotspot matrix combines churn × complexity to find risky code\n"
            "  • Dead code detection flags unreachable files (advisory only)\n"
            "  • Test mapping connects source files to their test counterparts\n\n"
            "This intelligence feeds into extraction: important files get\n"
            "priority processing, dead code is deprioritized, and partition\n"
            "context briefs give the LLM structural awareness.",
        )

    return StageResult(
        status=StageStatus.COMPLETED,
        message=(
            f"{total_code} code files, "
            f"{summary.get('hotspots', 0)} hotspots, "
            f"{summary.get('orphan_candidates', 0)} orphan candidates"
        ),
        data={"summary": summary},
    )
