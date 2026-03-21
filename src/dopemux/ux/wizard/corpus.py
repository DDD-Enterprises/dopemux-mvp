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
    import os
    from dopemux.ui.prompts import dopemux_confirm

    prescan_script = state.repo_root / "scripts" / "doc_audit_prescan.py"
    if not prescan_script.exists():
        console.print("[bold red]❌  scripts/doc_audit_prescan.py not found[/bold red]")
        return StageResult(status=StageStatus.FAILED, message="Prescan script missing")

    # Stage 2a: Quick heuristic prescan
    console.print("[bold cyan]Running corpus prescan (heuristic mode — fast, no API calls)…[/bold cyan]\n")
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

    # Display heuristic results
    console.print()
    render_corpus_table(state.corpus_stats)

    # Show excluded count
    excluded = state.corpus_stats.get("excluded_count", 0)
    total_scanned = state.corpus_stats.get("total_files_scanned", 0)
    console.print(
        f"\n  [dim]Scanned {total_scanned:,} total files  •  "
        f"{excluded:,} excluded (noise/binaries/vendor)[/dim]"
    )

    # Stage 2b: Offer Grok 420 classification upgrade
    console.print()
    has_grok_key = bool(os.environ.get("XAI_API_KEY"))
    if has_grok_key:
        render_educational_panel(
            "Upgrade: Grok 420 LLM Classification",
            "The heuristic classification above uses file paths and names.\n\n"
            "Grok 420 can provide more accurate authority classification by\n"
            "analyzing actual file content. This costs ~$0.05-0.10 per 10K files\n"
            "but gives higher precision for edge cases.\n\n"
            "[bold]Your XAI_API_KEY is set.[/bold] You can upgrade to Grok classification now.",
        )
        if dopemux_confirm("[cyan]Use Grok 420 for LLM-based classification?[/cyan]", default=False):
            console.print("[bold cyan]Running prescan with Grok 420…[/bold cyan]\n")
            cmd = [
                sys.executable,
                str(prescan_script),
                "direct",
                "--verbose",
                "--model",
                "grok-4.20-beta-0309-non-reasoning",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(state.repo_root),
                timeout=600,  # Grok calls take longer
            )
            if result.returncode != 0:
                console.print(
                    "[bold yellow]⚠️   Grok call failed, using heuristic results[/bold yellow]"
                )
                if state.educate_mode:
                    console.print(
                        "[dim]This can happen if the API is unavailable or "
                        "your quota is exhausted.[/dim]"
                    )
            else:
                # Reload stats from Grok response
                try:
                    grok_response_path = (
                        state.repo_root / "extraction" / "prescan" / "grok_response.json"
                    )
                    if grok_response_path.exists():
                        with open(grok_response_path) as f:
                            grok_data = json.load(f)
                        # Merge Grok classifications into state
                        state.grok_response = grok_data
                        console.print(
                            f"[bold green]✓ Grok classified {len(grok_data.get('classifications', []))} files[/bold green]"
                        )
                except (json.JSONDecodeError, OSError):
                    console.print("[dim]Could not parse Grok response[/dim]")
    else:
        if state.educate_mode:
            render_educational_panel(
                "Grok 420 Optional Upgrade",
                "The prescan supports Grok 420 (xAI) for LLM-based classification.\n\n"
                "This gives more accurate authority detection for edge cases,\n"
                "especially in mixed-content repositories.\n\n"
                "[bold]Your XAI_API_KEY is not set.[/bold] To enable Grok:\n"
                "  export XAI_API_KEY=xai-...\n\n"
                "Or ask an admin to provision API credentials.",
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
