"""
TaskX Kernel Lifecycle Commands

Delegates kernel lifecycle commands to the scripts/taskx wrapper.
"""

import sys
import subprocess
from pathlib import Path
from typing import Sequence

import click

from ..console import console


def _run_taskx_kernel(base_args: Sequence[str], taskx_args: Sequence[str]) -> None:
    """Delegate kernel lifecycle commands to scripts/taskx."""
    repo_root = Path(__file__).resolve().parents[3]
    wrapper = repo_root / "scripts" / "taskx"
    if not wrapper.exists():
        console.logger.error(f"[red]TaskX wrapper missing: {wrapper}[/red]")
        sys.exit(1)

    cmd = [str(wrapper), *base_args, *taskx_args]
    result = subprocess.run(cmd, cwd=repo_root, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


@click.group("kernel")
def kernel() -> None:
    """TaskX kernel lifecycle commands delegated through scripts/taskx."""


@kernel.command("doctor", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_doctor(taskx_args: Sequence[str]) -> None:
    """Run TaskX doctor."""
    _run_taskx_kernel(["doctor"], taskx_args)


@kernel.command("compile", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_compile(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux compile lifecycle step."""
    _run_taskx_kernel(["dopemux", "compile"], taskx_args)


@kernel.command("run", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_run(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux run lifecycle step."""
    _run_taskx_kernel(["dopemux", "run"], taskx_args)


@kernel.command("collect", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_collect(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux collect lifecycle step."""
    _run_taskx_kernel(["dopemux", "collect"], taskx_args)


@kernel.command("gate", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_gate(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux gate lifecycle step."""
    _run_taskx_kernel(["dopemux", "gate"], taskx_args)


@kernel.command("promote", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_promote(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux promote lifecycle step."""
    _run_taskx_kernel(["dopemux", "promote"], taskx_args)


@kernel.command("feedback", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_feedback(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux feedback lifecycle step."""
    _run_taskx_kernel(["dopemux", "feedback"], taskx_args)


@kernel.command("loop", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_loop(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux loop lifecycle step."""
    _run_taskx_kernel(["dopemux", "loop"], taskx_args)
