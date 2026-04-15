"""
Legacy extractor promptset and prescan tooling.

`dopemux extractor` is not the canonical operator path for repo-truth runs.
Operators should use `dopemux extract truth-run`, which launches the canonical
`services/repo-truth-extractor/run_extraction_v5.py` runtime.
"""

import json
import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console
from ..ui.theme import styled_panel, styled_table, error_panel, Glyphs, StatusChip


@click.group()
@click.pass_context
def extractor(ctx):
    """🧪 Legacy promptset/prescan cockpit for repo-truth extraction support workflows.

    This group remains available for promptset generation, prescan, and validation
    chores. It is not the canonical operator path for running extraction. Use
    `dopemux extract truth-run` for canonical v5 execution.
    """
    if ctx.invoked_subcommand:
        click.echo(
            "`dopemux extractor` is legacy promptset tooling. "
            "Use `dopemux extract truth-run` for canonical v5 execution."
        )


# ---- Prescan command ----


@extractor.command()
@click.option(
    "--repo",
    "-r",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="📂 Target repository path for the intelligence audit (defaults to the current cockpit directory).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False),
    default=None,
    help="📂 Target directory for storing the generated prescan intelligence and metadata (default: extraction/prescan).",
)
@click.option(
    "--passes",
    type=str,
    default=None,
    help="📊 Specific grok passes to engage during the audit (e.g., dedup, discover, feasibility, optimize).",
)
@click.option(
    "--code/--no-code",
    default=True,
    help="🧪 Toggle high-fidelity code-focused sensor analysis for the prescan ritual.",
)
@click.option(
    "--git/--no-git",
    default=True,
    help="📈 Enrich the intelligence payload with git metadata and historical telemetry.",
)
@click.option(
    "--incremental",
    is_flag=True,
    help="⏯️  Perform an incremental prescan ritual by analyzing changes since the last git synchronization.",
)
@click.option(
    "--cost-estimate",
    is_flag=True,
    help="💰 Print a detailed cost-to-fidelity estimate for the extraction ritual and exit.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="⚡ Enable high-fidelity telemetry for detailed diagnostic output during the scan.",
)
def prescan(
    repo: str,
    output: Optional[str],
    passes: Optional[str],
    code: bool,
    git: bool,
    incremental: bool,
    cost_estimate: bool,
    verbose: bool,
):
    """📊 Flight-Deck: Execute a pre-extraction intelligence audit.

    Activate the cockpit sensors to perform deep-tissue codebase analysis. This command
    calibrates the extraction sensors through multiple grok passes—identifying
    redundancy, discovering hidden features, and assessing ritual feasibility.
    It provides a comprehensive diagnostic report and a detailed cost-to-fidelity
    estimate for the upcoming extraction sessions.
    """
    repo_path = Path(repo).resolve()
    extractor_root = _resolve_extractor_root(repo_path)

    if extractor_root is None:
        raise click.ClickException(
            "Cannot find repo-truth-extractor. "
            "Make sure you're in a dopemux workspace or pass --repo."
        )

    console.print(styled_panel(
        f"[mint]Running prescan for[/mint] {repo_path.name}",
        title="[bold]DØPEMÜX Extractor Prescan[/bold]",
        border_style="info",
    ))

    # Import prescan engine
    lib_path = extractor_root / "services" / "repo-truth-extractor"
    sys.path.insert(0, str(lib_path))
    from lib.prescan.engine import PrescanEngine
    from lib.prescan.models import PrescanConfig

    config = PrescanConfig(
        repo_root=repo_path,
        output_dir=Path(output) if output else repo_path / "extraction" / "prescan",
        enable_code_prescan=code,
        enable_git_enrichment=git,
        incremental=incremental,
        verbose=verbose,
    )

    engine = PrescanEngine(config)
    
    pass_list = [p.strip() for p in passes.split(",")] if passes else None

    with branded_progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running prescan engine...", total=None)
        result = engine.run(passes=pass_list, incremental=incremental)
        progress.update(task, completed=True)

    if result.success:
        # Load intelligence to show cost estimate if requested
        import json
        with open(result.intelligence_path) as f:
            intelligence = json.load(f)
        
        if cost_estimate:
            cost = intelligence.get("cost_estimate", {})
            net = cost.get("net_estimates", {})
            savings = cost.get("estimated_savings", {})
            
            console.print("\n[bold]Extraction Cost Estimate[/bold]")
            console.print(f"  Gross Tokens: {cost.get('corpus_stats', {}).get('total_tokens_gross', 0):,}")
            console.print(f"  Total Savings: {savings.get('total_savings_tokens', 0):,} tokens ({savings.get('savings_pct', 0)}%)")
            console.print(f"  Net Tokens:    {net.get('input_tokens', 0):,} input / {net.get('output_tokens', 0):,} output")
            console.print(f"  [success]Total Est Cost: ${net.get('total_cost_usd', 0)} USD[/success]")
            return

        console.print(f"\n[success]✓ Prescan completed successfully[/success]")
        console.print(f"  Intelligence: {result.intelligence_path}")
        console.print(f"  Manifest: {result.manifest_path}")
        console.print(f"  Files scanned: {result.file_count}")
        console.print(f"  Included: {result.included_count}")
        
        cost = intelligence.get("cost_estimate", {})
        net = cost.get("net_estimates", {})
        console.print(f"  Est. Cost: ${net.get('total_cost_usd', 0)} USD")
        console.print(f"  Duration: {result.duration_seconds}s")
    else:
        console.print(f"\n[error]✗ Prescan failed[/error]")
        for err in result.errors:
            console.print(f"  [error]• {err}[/error]")
        raise SystemExit(1)


# ---- Init command ----


@extractor.command()
@click.option(
    "--repo",
    "-r",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="📂 Target repository path for the initialization ritual.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False),
    default=None,
    help="📂 Target directory for the synthesized promptset and generated artifacts.",
)
@click.option(
    "--prescan",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="📂 Path to the existing prescan intelligence directory to accelerate initialization.",
)
@click.option(
    "--interactive/--no-interactive",
    "-i",
    default=True,
    help="🧠 Engage the interactive feature discovery module for manual sensor calibration.",
)
@click.option(
    "--enrich",
    is_flag=True,
    default=False,
    help="⚡ Enable an optional LLM enrichment pass to synthesize higher-fidelity feature descriptions.",
)
@click.option(
    "--feature-map",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="🗺️  Inject a pre-authored FEATURE_MAP.json to skip the interactive discovery phase.",
)
@click.option(
    "--force-include",
    multiple=True,
    help="🔥 Force-include specific ritual phases (e.g., --force-include H --force-include T) into the synthesized promptset.",
)
@click.option(
    "--force-skip",
    multiple=True,
    help="🛡️  Force-skip specific ritual phases (e.g., --force-skip B --force-skip W) to optimize the extraction sequence.",
)
def init(
    repo: str,
    output: Optional[str],
    prescan: Optional[str],
    interactive: bool,
    enrich: bool,
    feature_map: Optional[str],
    force_include: tuple,
    force_skip: tuple,
):
    """🧪 Ritual Daemon: Initialize the extraction cockpit — Fingerprint, discover, and synthesize.

    Execute the complete initialization sequence for your repository. This ritual
    synchronizes fingerprinting, engages in interactive feature discovery,
    and synthesizes the final promptset. It prepares the flight-deck for live
    extraction rituals by calibrating the model-map, artifacts, and routing-policies
    required for high-fidelity truth extraction.
    """
    repo_path = Path(repo).resolve()
    extractor_root = _resolve_extractor_root(repo_path)

    if extractor_root is None:
        raise click.ClickException(
            "Cannot find repo-truth-extractor. "
            "Make sure you're in a dopemux workspace or pass --repo."
        )

    console.print(styled_panel(
        f"[mint]Initializing extractor for[/mint] {repo_path.name}",
        title="[bold]DØPEMÜX Extractor Init[/bold]",
        border_style="info",
    ))

    # Import sync engine
    sys.path.insert(0, str(extractor_root / "services" / "repo-truth-extractor"))
    from lib.promptgen.sync_engine import run_sync

    output_path = Path(output) if output else None
    feature_map_path = Path(feature_map) if feature_map else None
    prescan_path = Path(prescan) if prescan else None

    with branded_progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running sync pipeline...", total=None)

        result = run_sync(
            repo_root=repo_path,
            output_root=output_path,
            feature_map_path=feature_map_path,
            prescan_dir=prescan_path,
            interactive=interactive,
            enrich=enrich,
            force_include=list(force_include),
            force_skip=list(force_skip),
        )

        progress.update(task, completed=True)

    # Display results
    if result.success:
        console.print(f"\n[success]✓ Sync completed successfully[/success]")
        console.print(f"  Output: {result.output_dir}")
        console.print(f"  Stages: {len(result.stages_completed)}")
        if result.summary:
            console.print(
                f"  Phases: {result.summary.get('phases', '?')} | "
                f"Steps: {result.summary.get('steps', '?')} | "
                f"Artifacts: {result.summary.get('artifacts', '?')}"
            )
    else:
        console.print(f"\n[error]✗ Sync failed[/error]")
        for err in result.errors:
            console.print(f"  [error]• [{err['stage']}] {err['message']}[/error]")

    if result.warnings:
        console.print(f"\n[warning]Warnings ({len(result.warnings)}):[/warning]")
        for w in result.warnings[:5]:
            console.print(f"  [warning]• {w['message']}[/warning]")

    if not result.success:
        raise SystemExit(1)


# ---- Run command ----


@extractor.command()
@click.option(
    "--promptset-root",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="📂 Path to the synthesized promptset directory (generated from `extractor init`) for the extraction ritual.",
)
@click.option(
    "--prescan",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="📂 Path to the prescan intelligence directory used to calibrate the runner sensors.",
)
@click.option(
    "--pipeline",
    "-p",
    type=click.Choice(["v3", "v4", "v5"]),
    default="v5",
    help="📊 Specify the pipeline engine version (v3, v4, or v5) to ignite for the ritual.",
)
@click.argument("runner_args", nargs=-1, type=click.UNPROCESSED)
def run(
    promptset_root: Optional[str], prescan: Optional[str], pipeline: str, runner_args: tuple
):
    """🚀 Legacy compatibility entrypoint for promptset-oriented extractor runs.

    This command is retained for legacy promptset workflows only. Canonical operator
    execution should use `dopemux extract truth-run`, which launches the v5 runtime.
    """
    console.print(
        styled_panel(
            f"[mint]Running extraction pipeline {pipeline}[/mint]",
            title="[bold]DØPEMÜX Extractor Run[/bold]",
            border_style="info",
        )
    )

    # SAFETY: Never execute extraction scripts — warn and exit
    console.print(
        "[error]⚠ SAFETY NOTICE:[/error] `dopemux extractor run` is a legacy surface and "
        "direct execution is disabled to prevent accidental provider costs.\n"
        "Use `dopemux extract truth-run` for the canonical operator path."
    )
    console.print(f"\nWould run: pipeline={pipeline}")
    if promptset_root:
        console.print(f"  --promptset-root {promptset_root}")
    if prescan:
        console.print(f"  --prescan {prescan}")
    if runner_args:
        console.print(f"  Extra args: {' '.join(runner_args)}")


# ---- Status command ----


@extractor.command()
@click.option(
    "--output-dir", "-o",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="🔬 Archive Coordinate: Path to a generated promptset directory.",
)
@click.option(
    "--pipeline-version",
    type=click.Choice(["v3", "v4", "v5"]),
    default=None,
    help="📊 Legacy alias mode: forward runtime status to a specific extractor pipeline version.",
)
@click.option(
    "--run-id",
    default=None,
    help="🆔 Legacy alias mode: runtime extraction run identifier to query.",
)
@click.option(
    "--json",
    "status_json",
    is_flag=True,
    help="📊 Legacy alias mode: emit runtime status as machine-readable JSON.",
)
def status(
    output_dir: Optional[str],
    pipeline_version: Optional[str],
    run_id: Optional[str],
    status_json: bool,
):
    """
    📊 Promptset Status: Show status of a generated promptset

    Retrieves synchronization state for generated promptset artifacts only.
    This is not the canonical runtime run-status surface. When a pipeline version
    or run identifier is supplied, this command acts as an explicit legacy alias
    to the extractor runtime status command while continuing to point operators
    at `dopemux extract truth-run` as the canonical path.
    """
    if pipeline_version is not None or run_id is not None or status_json:
        console.print(
            "[warning]`dopemux extractor status` is a legacy alias.[/warning] "
            "Use `dopemux extract truth-run` for the canonical operator path."
        )
        args: List[str] = ["--status-json" if status_json else "--status"]
        if run_id:
            args.extend(["--run-id", run_id])
        _run_extractor_runner(
            pipeline_version=pipeline_version or "v5",
            args=args,
        )
        return

    if output_dir is None:
        console.print("[warning]No --output-dir specified. Looking for latest...[/warning]")
        # Try to find the most recent generated promptset
        extractor_root = _resolve_extractor_root(Path.cwd())
        if extractor_root:
            gen_dir = extractor_root / "services" / "repo-truth-extractor" / "promptsets" / "generated"
            if gen_dir.exists():
                dirs = sorted(gen_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
                if dirs:
                    output_dir = str(dirs[0])
                    console.print(f"  Found: {output_dir}")

    if output_dir is None:
        raise click.ClickException("No generated promptset found. Run `dopemux extractor init` first.")

    output_path = Path(output_dir)

    # Read and display manifest
    manifest_path = output_path / "SYNC_MANIFEST.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

        table = styled_table(
            "Sync Manifest",
            ("Field", {"style": "bold"}),
            "Value",
        )

        table.add_row("Success", "✓" if manifest.get("success") else "✗")
        table.add_row("Run ID", manifest.get("run_id", "?"))
        table.add_row("Stages", str(len(manifest.get("stages_completed", []))))
        table.add_row("Errors", str(len(manifest.get("errors", []))))
        table.add_row("Warnings", str(len(manifest.get("warnings", []))))

        summary = manifest.get("summary", {})
        if summary:
            table.add_row("Phases", str(summary.get("phases", "?")))
            table.add_row("Steps", str(summary.get("steps", "?")))
            table.add_row("Artifacts", str(summary.get("artifacts", "?")))

        console.print(table)
    else:
        console.print(f"[warning]No SYNC_MANIFEST.json in {output_dir}[/warning]")

    # List files
    files = sorted(output_path.glob("*"))
    console.print(f"\n[bold]Files ({len(files)}):[/bold]")
    for f in files:
        size = f.stat().st_size
        console.print(f"  {'📁' if f.is_dir() else '📄'} {f.name} ({size:,} bytes)")


# ---- Validate command ----


@extractor.command()
@click.option(
    "--output-dir", "-o",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="🔬 Archive Coordinate: Path to the generated promptset directory to validate.",
)
def validate(output_dir: str):
    """
    ✅ Verify Integrity: Validate a generated promptset for referential integrity

    Performs a strict structural audit of promptset artifacts to ensure 
    schema compliance and system compatibility.
    """
    output_path = Path(output_dir)

    required_files = ["promptset.yaml", "artifacts.yaml", "model_map.yaml"]
    missing = [f for f in required_files if not (output_path / f).exists()]
    if missing:
        raise click.ClickException(f"Missing required files: {', '.join(missing)}")

    extractor_root = _resolve_extractor_root(Path.cwd())
    if extractor_root:
        sys.path.insert(0, str(extractor_root / "services" / "repo-truth-extractor"))

    from lib.promptgen.integrity_validator import validate_from_files

    console.print(styled_panel(
        f"[mint]Validating[/mint] {output_path}",
        title="[bold]DØPEMÜX Extractor Validate[/bold]",
        border_style="info",
    ))

    result = validate_from_files(
        promptset_path=output_path / "promptset.yaml",
        artifacts_path=output_path / "artifacts.yaml",
        model_map_path=output_path / "model_map.yaml",
    )

    if result["passed"]:
        console.print("[success]✓ All integrity checks passed[/success]")
    else:
        console.print(f"[error]✗ {result['error_count']} errors found[/error]")
        for err in result["errors"]:
            console.print(f"  [error]• [{err['check']}] {err['message']}[/error]")

    if result["warning_count"] > 0:
        console.print(f"\n[warning]{result['warning_count']} warnings:[/warning]")
        for w in result["warnings"]:
            console.print(f"  [warning]• {w['message']}[/warning]")

    console.print(f"\nSummary: {result['summary']}")

    if not result["passed"]:
        raise SystemExit(1)


# ---- Helpers ----


def _resolve_extractor_root(start: Path) -> Optional[Path]:
    """Find the dopemux repo root that contains services/repo-truth-extractor."""
    for candidate in [start, *start.parents]:
        if (candidate / "services" / "repo-truth-extractor").is_dir():
            return candidate
    return None


def _extractor_runner_path(repo_root: Path, pipeline_version: str) -> Path:
    base = repo_root / "services" / "repo-truth-extractor"
    if pipeline_version == "v5":
        return base / "run_extraction_v5.py"
    if pipeline_version == "v4":
        return base / "run_extraction_v4.py"
    return base / "run_extraction_v3.py"


def _run_extractor_runner(
    *,
    pipeline_version: str,
    args: List[str],
    repo_root: Optional[Path] = None,
) -> None:
    resolved_root = _resolve_extractor_root(repo_root or Path.cwd())
    if resolved_root is None:
        raise click.ClickException(
            "Cannot find repo-truth-extractor. "
            "Make sure you're in a dopemux workspace or pass --repo."
        )

    runner = _extractor_runner_path(resolved_root, pipeline_version)
    if not runner.exists():
        raise click.ClickException(f"Runner not found: {runner}")

    proc = subprocess.run([sys.executable, str(runner), *args], cwd=resolved_root)
    if proc.returncode != 0:
        raise click.ClickException(
            f"Repo Truth Extractor {pipeline_version} runner failed with exit code {proc.returncode}"
        )


def _run_repscan_runner(
    *,
    args: List[str],
    repo_root: Optional[Path] = None,
) -> None:
    resolved_root = _resolve_extractor_root(repo_root or Path.cwd())
    if resolved_root is None:
        raise click.ClickException(
            "Cannot find repo-truth-extractor. "
            "Make sure you're in a dopemux workspace or pass --repo."
        )

    runner = resolved_root / "services" / "repo-truth-extractor" / "run_repscan.py"
    if not runner.exists():
        raise click.ClickException(f"RepoScan runner not found: {runner}")

    proc = subprocess.run([sys.executable, str(runner), *args], cwd=resolved_root)
    if proc.returncode != 0:
        raise click.ClickException(f"RepoScan runner failed with exit code {proc.returncode}")
