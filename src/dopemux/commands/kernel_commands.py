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
        console.logger.error(f"[error]TaskX wrapper missing: {wrapper}[/error]")
        sys.exit(1)

    cmd = [str(wrapper), *base_args, *taskx_args]
    result = subprocess.run(cmd, cwd=repo_root, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


@click.group("kernel")
def kernel() -> None:
    """
    🔬 TaskX Kernel Lifecycle: Orchestrate Ritual Steps

    Manages the primary execution kernel of the TaskX subsystem. These commands 
    delegate to the TaskX ritual wrapper (scripts/taskx), synchronizing the 
    core state and lifecycle of the active daemon.

    Capabilities:
    - Diagnostic Scans: Run the doctor ritual to verify kernel health.
    - Lifecycle Stages: Compile, Run, Collect, Gate, Promote, Feedback, and Loop.
    """


@kernel.command("doctor", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_doctor(taskx_args: Sequence[str]) -> None:
    """
    🔬 Run diagnostic scan on the active kernel (TaskX doctor).

    Verifies the integrity of the ritual chamber and daemon synchronization.
    """
    _run_taskx_kernel(["doctor"], taskx_args)


@kernel.command("compile", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_compile(taskx_args: Sequence[str]) -> None:
    """
    🧪 Synchronize and compile the TaskX ritual logic.

    Transforms raw intent into executable kernel patterns.
    """
    _run_taskx_kernel(["dopemux", "compile"], taskx_args)


@kernel.command("run", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_run(taskx_args: Sequence[str]) -> None:
    """
    ⚡ Execute the current TaskX ritual cycle.

    Launches the active kernel within the provisioned cockpit.
    """
    _run_taskx_kernel(["dopemux", "run"], taskx_args)


@kernel.command("collect", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_collect(taskx_args: Sequence[str]) -> None:
    """
    📊 Harvest ritual artifacts and state updates from the active kernel.

    Consolidates mission telemetry and stores it in the central archive.
    """
    _run_taskx_kernel(["dopemux", "collect"], taskx_args)


@kernel.command("gate", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_gate(taskx_args: Sequence[str]) -> None:
    """
    💧 Verify ritual exit conditions and quality gates.

    Ensures mission success criteria are satisfied before promotion.
    """
    _run_taskx_kernel(["dopemux", "gate"], taskx_args)


@kernel.command("promote", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_promote(taskx_args: Sequence[str]) -> None:
    """
    ⚡ Advance the ritual state to the next temporal coordinate.

    Commits verified artifacts to the shared repository.
    """
    _run_taskx_kernel(["dopemux", "promote"], taskx_args)


@kernel.command("feedback", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_feedback(taskx_args: Sequence[str]) -> None:
    """
    🧠 Process mission feedback and update ritual heuristics.

    Refines the daemon's cognitive patterns based on execution data.
    """
    _run_taskx_kernel(["dopemux", "feedback"], taskx_args)


@kernel.command("loop", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_loop(taskx_args: Sequence[str]) -> None:
    """
    ⚡ Initiate a persistent ritual loop.

    Automates sequential execution of the TaskX kernel lifecycle.
    """
    _run_taskx_kernel(["dopemux", "loop"], taskx_args)
