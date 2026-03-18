"""Stage 2: Corpus audit — run doc_audit_prescan and visualise results."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from dopemux.console import console

from .display import (
    render_archaeology_table,
    render_batch_plan_table,
    render_corpus_table,
    render_educational_panel,
    render_savings_report,
)
from .stages import AUTHORITY_CLASSES, StageResult, StageStatus, WizardState

logger = logging.getLogger(__name__)


def _load_intelligence_router(prescan_dir: Path) -> object | None:
    """Try to load IntelligenceRouter from prescan output directory."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "services" / "repo-truth-extractor"))
        from lib.intelligence_router import IntelligenceRouter
        return IntelligenceRouter.from_dir(prescan_dir)
    except Exception as exc:
        logger.debug(f"Could not load IntelligenceRouter: {exc}")
        return None


def run_corpus_audit(state: WizardState) -> StageResult:
    """Stage 2 — Run the prescan script and parse + display results.

    Enhanced: passes deep_mode flag, loads batch plan, creates
    IntelligenceRouter, shows archaeology results in deep mode.
    """
    prescan_script = state.repo_root / "scripts" / "doc_audit_prescan.py"
    if not prescan_script.exists():
        console.print("[error]❌  scripts/doc_audit_prescan.py not found[/error]")
        return StageResult(status=StageStatus.FAILED, message="Prescan script missing")

    # Run prescan in dry-run mode (safe — no API calls)
    console.print("[mint]Running corpus prescan (dry-run, safe — no API calls)…[/mint]\n")
    cmd = [sys.executable, str(prescan_script), "dry-run", "--verbose", "--force"]

    # Pass deep mode flag if enabled
    if state.deep_mode:
        cmd.append("--deep")
        console.print("  [text.dim]Deep/history mode enabled — including archived content[/text.dim]\n")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(state.repo_root),
        timeout=300,
    )

    if result.returncode != 0:
        console.print(f"[error]Prescan failed (exit {result.returncode})[/error]")
        if result.stderr:
            console.print(f"[error]{result.stderr[:500]}[/error]")
        return StageResult(status=StageStatus.FAILED, message="Prescan subprocess failed")

    # Parse outputs
    prescan_dir = state.repo_root / "extraction" / "prescan"
    stats_path = prescan_dir / "corpus_stats.json"
    manifest_path = prescan_dir / "corpus_manifest.json"

    if not stats_path.exists():
        console.print("[error]❌  corpus_stats.json not found after prescan[/error]")
        return StageResult(status=StageStatus.FAILED, message="Prescan output missing")

    try:
        with open(stats_path) as f:
            state.corpus_stats = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        console.print(f"[error]Failed to parse corpus_stats.json: {exc}[/error]")
        return StageResult(status=StageStatus.FAILED, message="Stats JSON parse error")

    # Manifest is large — load only included files for phase mapping later
    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                state.corpus_manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            state.corpus_manifest = None  # non-fatal

    # Populate convenience fields
    state.corpus_included_count = state.corpus_stats.get("included_count", 0)
    state.corpus_total_size = state.corpus_stats.get("total_included_size", 0)

    # Display results
    console.print()
    render_corpus_table(state.corpus_stats)

    # Show excluded count
    excluded = state.corpus_stats.get("excluded_count", 0)
    total_scanned = state.corpus_stats.get("total_files_scanned", 0)
    console.print(
        f"\n  [text.dim]Scanned {total_scanned:,} total files  •  "
        f"{excluded:,} excluded (noise/binaries/vendor)[/text.dim]"
    )

    # ── Load prescan intelligence artifacts ────────────────────────────────
    # Batch plan
    batch_plan_path = prescan_dir / "batch_plan.json"
    if batch_plan_path.exists():
        try:
            with open(batch_plan_path) as f:
                state.batch_plan = json.load(f)
            console.print()
            render_batch_plan_table(state.batch_plan)
        except (json.JSONDecodeError, OSError):
            pass

    # Code intelligence report
    code_report_path = prescan_dir / "code_intelligence_report.json"
    if code_report_path.exists():
        try:
            with open(code_report_path) as f:
                state.code_intelligence = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    # Archaeology report (deep mode)
    arch_path = prescan_dir / "archaeology_report.json"
    if arch_path.exists():
        try:
            with open(arch_path) as f:
                state.archaeology_report = json.load(f)
            if state.deep_mode and state.archaeology_report:
                console.print()
                render_archaeology_table(state.archaeology_report)
        except (json.JSONDecodeError, OSError):
            pass

    # Load IntelligenceRouter
    router = _load_intelligence_router(prescan_dir)
    if router:
        state.intelligence_router = router
        # Show token savings estimate
        savings = router.estimate_token_savings(state.corpus_manifest)
        if savings.get("skipped_files_count", 0) > 0:
            console.print()
            render_savings_report(savings, {})

    # Educational content
    if state.educate_mode:
        class_descriptions = "\n".join(
            f"  {meta['icon']}  {cls.capitalize()}: {meta['desc']}"
            for cls, meta in AUTHORITY_CLASSES.items()
        )
        render_educational_panel(
            "What are authority classes?",
            "The prescan classifies every file by its role in the repository:\n\n"
            f"{class_descriptions}\n\n"
            "This classification determines which extraction phases will process each file\n"
            "and helps estimate cost and partition counts.",
        )

    return StageResult(
        status=StageStatus.COMPLETED,
        message=f"{state.corpus_included_count:,} files, {state.corpus_total_size / (1024*1024):.1f} MB",
        data={"included": state.corpus_included_count, "size": state.corpus_total_size},
    )
