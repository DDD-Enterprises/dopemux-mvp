"""Stage 2: Corpus audit — run doc_audit_prescan and visualise results."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from dopemux.console import console

from .display import render_corpus_table, render_educational_panel
from .stages import AUTHORITY_CLASSES, StageResult, StageStatus, WizardState


def run_corpus_audit(state: WizardState) -> StageResult:
    """Stage 2 — Run the prescan script and parse + display results."""
    prescan_script = state.repo_root / "scripts" / "doc_audit_prescan.py"
    if not prescan_script.exists():
        console.print("[bold red]❌  scripts/doc_audit_prescan.py not found[/bold red]")
        return StageResult(status=StageStatus.FAILED, message="Prescan script missing")

    # Run prescan in dry-run mode (safe — no API calls)
    console.print("[bold cyan]Running corpus prescan (dry-run, safe — no API calls)…[/bold cyan]\n")
    cmd = [sys.executable, str(prescan_script), "dry-run", "--verbose", "--force"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(state.repo_root),
        timeout=300,
    )

    if result.returncode != 0:
        console.print(f"[bold red]Prescan failed (exit {result.returncode})[/bold red]")
        if result.stderr:
            console.print(f"[red]{result.stderr[:500]}[/red]")
        return StageResult(status=StageStatus.FAILED, message="Prescan subprocess failed")

    # Parse outputs
    prescan_dir = state.repo_root / "extraction" / "prescan"
    stats_path = prescan_dir / "corpus_stats.json"
    manifest_path = prescan_dir / "corpus_manifest.json"

    if not stats_path.exists():
        console.print("[bold red]❌  corpus_stats.json not found after prescan[/bold red]")
        return StageResult(status=StageStatus.FAILED, message="Prescan output missing")

    try:
        with open(stats_path) as f:
            state.corpus_stats = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        console.print(f"[bold red]Failed to parse corpus_stats.json: {exc}[/bold red]")
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
        f"\n  [dim]Scanned {total_scanned:,} total files  •  "
        f"{excluded:,} excluded (noise/binaries/vendor)[/dim]"
    )

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
