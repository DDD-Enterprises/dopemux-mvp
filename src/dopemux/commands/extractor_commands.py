"""
Extractor Commands
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console

@click.group()
@click.pass_context
def extractor(ctx):
    """Legacy alias for `dopemux upgrades`."""
    if ctx.invoked_subcommand:
        console.logger.info("[yellow]⚠ `dopemux extractor` is legacy. Use `dopemux upgrades`.[/yellow]")


def _resolve_extractor_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "services" / "repo-truth-extractor").is_dir():
            return candidate
    return start


def _extractor_runner_path(repo_root: Path, pipeline_version: str) -> Path:
    base = repo_root / "services" / "repo-truth-extractor"
    if pipeline_version == "v4":
        return base / "run_extraction_v4.py"
    return base / "run_extraction_v3.py"


def _run_extractor_runner(
    *,
    pipeline_version: str,
    args: List[str],
    repo_root: Optional[Path] = None,
) -> None:
    resolved_root = _resolve_extractor_repo_root(repo_root or Path.cwd())
    runner = _extractor_runner_path(resolved_root, pipeline_version)
    if not runner.exists():
        raise click.ClickException(f"Runner not found: {runner}")
    cmd = [sys.executable, str(runner), *args]
    proc = subprocess.run(cmd, cwd=resolved_root)
    if proc.returncode != 0:
        raise click.ClickException(
            f"Repo Truth Extractor {pipeline_version} runner failed with exit code {proc.returncode}"
        )


def _repscan_runner_path(repo_root: Path) -> Path:
    return repo_root / "services" / "repo-truth-extractor" / "run_repscan.py"


def _run_repscan_runner(
    *,
    args: List[str],
    repo_root: Optional[Path] = None,
) -> None:
    resolved_root = _resolve_extractor_repo_root(repo_root or Path.cwd())
    runner = _repscan_runner_path(resolved_root)
    if not runner.exists():
        raise click.ClickException(f"RepoScan runner not found: {runner}")
    cmd = [sys.executable, str(runner), *args]
    proc = subprocess.run(cmd, cwd=resolved_root)
    if proc.returncode != 0:
        raise click.ClickException(f"RepoScan runner failed with exit code {proc.returncode}")
