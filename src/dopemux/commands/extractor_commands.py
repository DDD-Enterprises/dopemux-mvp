"""
Extractor Commands — Universal Repo-Truth-Extractor CLI.

Provides the `dopemux extractor` command group with subcommands:
  init    — Fingerprint + interactive feature discovery + prompt generation
  run     — Execute extraction using generated (or v4) promptset
  status  — Show extraction run status
  validate — Validate a generated promptset for referential integrity
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
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console


@click.group()
@click.pass_context
def extractor(ctx):
    """Universal Repo-Truth-Extractor — analyze any codebase."""
    if ctx.invoked_subcommand:
        click.echo("`dopemux extractor` is legacy. Use `dopemux upgrades`.")


# ---- Prescan command ----


@extractor.command()
@click.option(
    "--repo", "-r",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Path to the target repository (default: current directory).",
)
@click.option(
    "--output", "-o",
    type=click.Path(file_okay=False),
    default=None,
    help="Output directory for prescan intelligence (default: extraction/prescan).",
)
@click.option(
    "--passes",
    type=str,
    default=None,
    help="Grok passes to run (comma-separated: dedup,discover,feasibility,optimize).",
)
@click.option(
    "--code/--no-code",
    default=True,
    help="Enable code-focused prescan (default: True).",
)
@click.option(
    "--git/--no-git",
    default=True,
    help="Enable git metadata enrichment (default: True).",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Verbose output.",
)
def prescan(
    repo: str,
    output: Optional[str],
    passes: Optional[str],
    code: bool,
    git: bool,
    verbose: bool,
):
    """Run pre-extraction intelligence audit."""
    repo_path = Path(repo).resolve()
    extractor_root = _resolve_extractor_root(repo_path)

    if extractor_root is None:
        raise click.ClickException(
            "Cannot find repo-truth-extractor. "
            "Make sure you're in a dopemux workspace or pass --repo."
        )

    console.print(Panel(
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
        verbose=verbose,
    )

    engine = PrescanEngine(config)
    
    pass_list = [p.strip() for p in passes.split(",")] if passes else None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running prescan engine...", total=None)
        result = engine.run(passes=pass_list)
        progress.update(task, completed=True)

    if result.success:
        console.print(f"\n[success]✓ Prescan completed successfully[/success]")
        console.print(f"  Intelligence: {result.intelligence_path}")
        console.print(f"  Manifest: {result.manifest_path}")
        console.print(f"  Files scanned: {result.file_count}")
        console.print(f"  Included: {result.included_count}")
        console.print(f"  Duration: {result.duration_seconds}s")
    else:
        console.print(f"\n[error]✗ Prescan failed[/error]")
        for err in result.errors:
            console.print(f"  [error]• {err}[/error]")
        raise SystemExit(1)


# ---- Init command ----


@extractor.command()
@click.option(
    "--repo", "-r",
    type=click.Path(exists=True, file_okay=False),
    default=".",
    help="Path to the target repository (default: current directory).",
)
@click.option(
    "--output", "-o",
    type=click.Path(file_okay=False),
    default=None,
    help="Output directory for generated promptset.",
)
@click.option(
    "--prescan",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="Path to prescan output directory.",
)
@click.option(
    "--interactive/--no-interactive", "-i",
    default=True,
    help="Run interactive feature discovery (default: True).",
)
@click.option(
    "--enrich",
    is_flag=True,
    default=False,
    help="Enable optional LLM enrichment pass.",
)
@click.option(
    "--feature-map",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Pre-authored FEATURE_MAP.json (skips interactive discovery).",
)
@click.option(
    "--force-include",
    multiple=True,
    help="Force-include phases (e.g., --force-include H --force-include T).",
)
@click.option(
    "--force-skip",
    multiple=True,
    help="Force-skip phases (e.g., --force-skip B --force-skip W).",
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
    """Initialize extraction — fingerprint, discover features, generate prompts."""
    repo_path = Path(repo).resolve()
    extractor_root = _resolve_extractor_root(repo_path)

    if extractor_root is None:
        raise click.ClickException(
            "Cannot find repo-truth-extractor. "
            "Make sure you're in a dopemux workspace or pass --repo."
        )

    console.print(Panel(
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

    with Progress(
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
    help="Path to a generated promptset directory (from `extractor init`).",
)
@click.option(
    "--prescan",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="Path to prescan output directory.",
)
@click.option(
    "--pipeline", "-p",
    type=click.Choice(["v3", "v4", "v5"]),
    default="v5",
    help="Pipeline version to use (default: v5).",
)
@click.argument("runner_args", nargs=-1, type=click.UNPROCESSED)
def run(promptset_root: Optional[str], prescan: Optional[str], pipeline: str, runner_args: tuple):
    """Run the extraction pipeline with a generated or default promptset."""
    console.print(Panel(
        f"[mint]Running extraction pipeline {pipeline}[/mint]",
        title="[bold]DØPEMÜX Extractor Run[/bold]",
        border_style="info",
    ))

    # SAFETY: Never execute extraction scripts — warn and exit
    console.print(
        "[error]⚠ SAFETY NOTICE:[/error] Direct execution of extraction runners "
        "is disabled in the CLI to prevent accidental provider costs.\n"
        "Use the v5 runner directly with appropriate flags if you understand the costs."
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
    help="Path to a generated promptset directory.",
)
def status(output_dir: Optional[str]):
    """Show status of a generated promptset."""
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

        table = Table(title="Sync Manifest", border_style="info")
        table.add_column("Field", style="bold")
        table.add_column("Value")

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
    help="Path to the generated promptset directory to validate.",
)
def validate(output_dir: str):
    """Validate a generated promptset for referential integrity."""
    output_path = Path(output_dir)

    required_files = ["promptset.yaml", "artifacts.yaml", "model_map.yaml"]
    missing = [f for f in required_files if not (output_path / f).exists()]
    if missing:
        raise click.ClickException(f"Missing required files: {', '.join(missing)}")

    extractor_root = _resolve_extractor_root(Path.cwd())
    if extractor_root:
        sys.path.insert(0, str(extractor_root / "services" / "repo-truth-extractor"))

    from lib.promptgen.integrity_validator import validate_from_files

    console.print(Panel(
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
