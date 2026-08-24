"""Audit commands for dopemux CLI — prescan, wizard, and status."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from ..console import console
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip
from .extractor_commands import _run_extractor_runner
from .rte_shared import ROUTING_POLICY_CHOICES as _ROUTING_POLICY_CHOICES


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
    type=click.Choice(_ROUTING_POLICY_CHOICES),
    metavar="TEXT",
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

    Delegates to the canonical `dopemux rte status` (v5) implementation
    rather than re-reading run-pointer files directly. TP-RTE-TRUTH-R4-004
    (F-44) retired the standalone reimplementation that lived here: it read
    ``extraction/repo-truth-extractor/v5/latest_run_id.txt`` relative to the
    process's current working directory with no repo-root search, so it
    silently reported "No extraction runs found" whenever invoked from any
    directory other than the repo root — even with a real run present. The
    canonical path resolves the repo root the same way every other `rte`
    subcommand does, so `dopemux audit status` now behaves identically from
    any cwd.
    """
    _run_extractor_runner(pipeline_version="v5", args=["--status"])
