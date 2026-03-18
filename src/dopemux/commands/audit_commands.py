"""Audit commands for dopemux CLI — prescan, wizard, and status."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel

from ..console import console


@click.group()
@click.pass_context
def audit(ctx):
    """🔬 Documentation audit and guided extraction wizard.

    Analyze your repository's documentation corpus, estimate costs,
    and run guided extraction with the repo-truth-extractor pipeline.
    """
    pass


@audit.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--force", is_flag=True, help="Skip corpus size safety limit")
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Custom TOML config path",
)
@click.pass_context
def prescan(ctx, verbose: bool, force: bool, config: Optional[str]):
    """📊 Run documentation corpus pre-scan audit.

    Walks the repository, classifies files by authority class,
    and generates corpus statistics without making any API calls.

    Outputs go to extraction/prescan/:
    corpus_manifest.json, corpus_stats.json, run_metadata.json
    """
    script = Path("scripts/doc_audit_prescan.py")
    if not script.exists():
        console.print("[error]❌  scripts/doc_audit_prescan.py not found[/error]")
        raise SystemExit(1)

    cmd = [sys.executable, str(script), "dry-run"]
    if verbose:
        cmd.append("--verbose")
    if force:
        cmd.append("--force")
    if config:
        cmd.extend(["--config", config])

    console.print(
        Panel(
            "[mint]📊  Running corpus pre-scan audit…[/mint]",
            border_style="info",
        )
    )
    result = subprocess.run(cmd, cwd=str(Path.cwd()))
    raise SystemExit(result.returncode)


@audit.command()
@click.option(
    "--execute",
    is_flag=True,
    help="Enable actual extraction (default: preview only)",
)
@click.option(
    "--educate/--no-educate",
    default=True,
    help="Show educational explanations at each stage",
)
@click.option(
    "--routing-policy",
    default="balanced_openrouter",
    show_default=True,
    help="LLM routing policy for extraction",
)
@click.option(
    "--workers",
    "-w",
    default=10,
    show_default=True,
    help="Partition worker count",
)
@click.pass_context
def wizard(ctx, execute: bool, educate: bool, routing_policy: str, workers: int):
    """🧙 Guided extraction wizard — interactive walkthrough.

    Walks you through the complete extraction pipeline:
    repo health → corpus audit → prompt setup → cost selection →
    partition preview → phase-by-phase extraction.

    Default mode is preview-only. Use --execute to enable actual extraction.
    """
    from ..ux.wizard import WizardRunner

    runner = WizardRunner(
        execute=execute,
        educate=educate,
        routing_policy=routing_policy,
        workers=workers,
    )
    runner.run()


@audit.command()
@click.pass_context
def status(ctx):
    """📋 Show status of last extraction run."""
    latest_file = Path("extraction/repo-truth-extractor/v5/latest_run_id.txt")
    if not latest_file.exists():
        console.print("[warning]No extraction runs found.[/warning]")
        raise SystemExit(0)

    run_id = latest_file.read_text().strip()
    run_dir = Path(f"extraction/repo-truth-extractor/v5/runs/{run_id}")
    console.print(f"[bold]Latest run:[/bold]  {run_id}")
    console.print(f"[bold]Location:[/bold]   {run_dir}")

    if run_dir.exists():
        phase_dirs = sorted(
            d.name for d in run_dir.iterdir() if d.is_dir() and len(d.name) == 1
        )
        if phase_dirs:
            console.print(f"[bold]Phases:[/bold]     {', '.join(phase_dirs)}")
        else:
            console.print("[bold]Phases:[/bold]     [text.dim]none found[/text.dim]")

        # Show directory sizes
        total_size = sum(
            f.stat().st_size
            for f in run_dir.rglob("*")
            if f.is_file()
        )
        console.print(f"[bold]Total size:[/bold] {total_size / (1024 * 1024):.1f} MB")
    else:
        console.print(f"[warning]Run directory not found: {run_dir}[/warning]")
