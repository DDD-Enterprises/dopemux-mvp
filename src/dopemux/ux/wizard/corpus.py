"""Stage 2: Corpus audit — run doc_audit_prescan and visualise results."""

from __future__ import annotations

import json
import subprocess
import sys

from dopemux.console import console

from .display import render_corpus_table, render_educational_panel, render_intelligence_report
from .stages import AUTHORITY_CLASSES, StageResult, StageStatus, WizardState


def run_corpus_audit(state: WizardState) -> StageResult:
    """Stage 2 — Run the prescan script and parse + display results."""
    import os
    from rich.prompt import Confirm

    prescan_script = state.repo_root / "scripts" / "doc_audit_prescan.py"
    if not prescan_script.exists():
        console.print("[bold red]❌  scripts/doc_audit_prescan.py not found[/bold red]")
        return StageResult(status=StageStatus.FAILED, message="Prescan script missing")

    # ── Stage 2a: Quick heuristic prescan ────────────────────────────────
    console.print(
        "[bold cyan]Running corpus prescan "
        "(heuristic mode — fast, no API calls)…[/bold cyan]\n"
    )
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
        return StageResult(
            status=StageStatus.FAILED, message="Prescan subprocess failed"
        )

    # Parse outputs
    prescan_dir = state.repo_root / "extraction" / "prescan"
    stats_path = prescan_dir / "corpus_stats.json"
    manifest_path = prescan_dir / "corpus_manifest.json"

    if not stats_path.exists():
        console.print(
            "[bold red]❌  corpus_stats.json not found after prescan[/bold red]"
        )
        return StageResult(status=StageStatus.FAILED, message="Prescan output missing")

    try:
        with open(stats_path) as f:
            state.corpus_stats = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        console.print(f"[bold red]Failed to parse corpus_stats.json: {exc}[/bold red]")
        return StageResult(status=StageStatus.FAILED, message="Stats JSON parse error")

    if manifest_path.exists():
        try:
            with open(manifest_path) as f:
                state.corpus_manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            state.corpus_manifest = None

    state.corpus_included_count = state.corpus_stats.get("included_count", 0)
    state.corpus_total_size = state.corpus_stats.get("total_included_size", 0)

    # Display heuristic results
    console.print()
    render_corpus_table(state.corpus_stats)

    excluded = state.corpus_stats.get("excluded_count", 0)
    total_scanned = state.corpus_stats.get("total_files_scanned", 0)
    console.print(
        f"\n  [dim]Scanned {total_scanned:,} total files  •  "
        f"{excluded:,} excluded (noise/binaries/vendor)[/dim]"
    )

    # ── Stage 2b: Full intelligence passes (free, no API) ──────────────────
    console.print()
    if state.educate_mode:
        render_educational_panel(
            "Full Intelligence Passes (Free — No API Cost)",
            "The prescan can run deep analysis using your local codebase:\n\n"
            "  • [bold]Git intelligence[/bold]: lifecycle, ghosts, dupes, chains, co-change\n"
            "  • [bold]Code intelligence[/bold]: AST, import graph, entry points, complexity\n"
            "  • [bold]Architecture[/bold]: compose topology, services, event flows, API routes\n"
            "  • [bold]Features[/bold]: flags, CLI commands, MCP tools, completeness\n\n"
            "Takes ~60-90s. Produces prescan_intelligence.json and extraction\n"
            "artifacts (skip list, routing hints, partition hints) for optimized runs.",
        )

    if Confirm.ask(
        "[cyan]Run full intelligence passes (free, ~60-90s)?[/cyan]", default=True
    ):
        console.print("[bold cyan]Running full intelligence passes…[/bold cyan]\n")
        cmd_full = [
            sys.executable,
            str(prescan_script),
            "dry-run",
            "--full-passes",
            "--force",
        ]
        full_result = subprocess.run(
            cmd_full,
            capture_output=True,
            text=True,
            cwd=str(state.repo_root),
            timeout=300,
        )
        if full_result.returncode != 0:
            console.print(
                "[yellow]⚠️  Full passes failed, continuing with heuristic results[/yellow]"
            )
        else:
            state.git_passes_run = True
            intel_path = prescan_dir / "prescan_intelligence.json"
            if intel_path.exists():
                try:
                    with open(intel_path) as f:
                        state.intelligence_report = json.load(f)
                    render_intelligence_report(state.intelligence_report)
                except (json.JSONDecodeError, OSError):
                    pass

    # ── Stage 2c: Grok 420 classification upgrade ─────────────────────────
    console.print()
    has_grok_key = bool(os.environ.get("XAI_API_KEY"))
    if has_grok_key:
        render_educational_panel(
            "Optional: Grok 420 LLM Classification",
            "The heuristic classification uses file paths and names.\n\n"
            "Grok 420 analyzes actual file content for more accurate authority\n"
            "classification. Costs ~$0.05-0.10 per 10K files.\n\n"
            "[bold]Your XAI_API_KEY is set.[/bold]",
        )
        if Confirm.ask(
            "[cyan]Use Grok 420 for LLM-based classification?[/cyan]", default=False
        ):
            console.print("[bold cyan]Running prescan with Grok 420…[/bold cyan]\n")
            cmd_grok = [
                sys.executable,
                str(prescan_script),
                "direct",
                "--verbose",
                "--model",
                "grok-4.20-beta-0309-non-reasoning",
            ]
            result = subprocess.run(
                cmd_grok,
                capture_output=True,
                text=True,
                cwd=str(state.repo_root),
                timeout=600,
            )
            if result.returncode != 0:
                console.print(
                    "[bold yellow]⚠️  Grok call failed, using heuristic results[/bold yellow]"
                )
            else:
                grok_response_path = prescan_dir / "grok_response.json"
                if grok_response_path.exists():
                    try:
                        with open(grok_response_path) as f:
                            grok_data = json.load(f)
                        state.grok_response = grok_data
                        n = len(grok_data.get("classifications", []))
                        console.print(
                            f"[bold green]✓ Grok classified {n} files[/bold green]"
                        )
                    except (json.JSONDecodeError, OSError):
                        console.print("[dim]Could not parse Grok response[/dim]")
    else:
        if state.educate_mode:
            render_educational_panel(
                "Grok 420 Optional Upgrade",
                "The prescan supports Grok 420 (xAI) for LLM-based classification.\n\n"
                "[bold]Your XAI_API_KEY is not set.[/bold] To enable:\n"
                "  export XAI_API_KEY=xai-...",
            )

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
        message=(
            f"{state.corpus_included_count:,} files, "
            f"{state.corpus_total_size / (1024 * 1024):.1f} MB"
        ),
        data={
            "included": state.corpus_included_count,
            "size": state.corpus_total_size,
            "git_passes_run": state.git_passes_run,
        },
    )
