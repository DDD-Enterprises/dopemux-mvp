"""Audit commands for dopemux CLI — prescan, wizard, and status."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from ..console import console
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip


@click.group()
@click.pass_context
def audit(ctx):
    """
    🔬 Documentation Audit: Corpus analysis and guided extraction HUD

    Orchestrates the high-fidelity analysis of the project's documentation 
    corpus. Synchronizes daemon sensors to estimate costs, identify 
    authority classes, and prepare the cockpit for extraction rituals.
    """
    pass


@audit.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="📊 Deep Telemetry: Enable high-fidelity signal monitoring during the scan.",
)
@click.option(
    "--force",
    is_flag=True,
    help="🚀 Force Extraction: Override corpus size safety limits and proceed with the ritual.",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="🛠️  Ritual Config: Specify a custom configuration coordinate for the scan.",
)
@click.pass_context
def prescan(ctx, verbose: bool, force: bool, config: Optional[str]):
    """
    📊 Pre-Ignition Audit: Execute non-destructive documentation corpus scan

    Activates cockpit sensors to classify documentation artifacts by 
    authority class. Generates corpus statistics and estimates ritual 
    costs without engaging external LLM providers.
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
        styled_panel(
            "[mint]📊  Running corpus pre-scan audit…[/mint]",
            border_style="panel.border",
        )
    )
    result = subprocess.run(cmd, cwd=str(Path.cwd()))
    raise SystemExit(result.returncode)


@audit.command()
@click.option(
    "--execute",
    is_flag=True,
    help="⚡ Ignite Engines: Engage LLM providers for actual extraction (default: preview only).",
)
@click.option(
    "--educate/--no-educate",
    default=True,
    help="🧠 Cognitive Overlay: Provide educational HUD tips at each ritual stage.",
)
@click.option(
    "--routing-policy",
    default="cost",
    show_default=True,
    help="🧠 Cognitive Routing: LLM policy for the extraction ritual. Use cost for the bounded first-run lane.",
)
@click.option(
    "--workers",
    "-w",
    default=1,
    show_default=True,
    help="⚡ Ritual Workers: Number of concurrent workers for partitioning. Keep this at 1 for deterministic first runs.",
)
@click.pass_context
def wizard(ctx, execute: bool, educate: bool, routing_policy: str, workers: int):
    """
    🧙 Ritual Guide: Guided extraction flight-deck walkthrough

    Engages the interactive cockpit walkthrough for the extraction pipeline. 
    Synchronizes across ritual phases, from health assessment to 
    high-fidelity materialization.
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
    """
    📋 Diagnostic HUD: Show telemetry from the latest ritual session

    Retrieves current cockpit telemetry for the most recent repo-truth-extractor 
    run, detailing phase progression and total payload size.
    """
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
            console.print("[bold]Phases:[/bold]     [dim]none found[/dim]")

        # Show directory sizes
        total_size = sum(
            f.stat().st_size
            for f in run_dir.rglob("*")
            if f.is_file()
        )
        console.print(f"[bold]Total size:[/bold] {total_size / (1024 * 1024):.1f} MB")
    else:
        console.print(f"[warning]Run directory not found: {run_dir}[/warning]")
