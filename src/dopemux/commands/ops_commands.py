"""
Ops Commands

Wrappers around subprocess-invoked developer rituals (`run-tests`,
`run-build`) that thread through the mobile-task notification system
and refresh the tmux HUD indicator on completion.
"""

import logging
import subprocess
import sys
from typing import Optional, Sequence

import click

from ..config import ConfigManager
from ..console import console
from ..mobile.hooks import mobile_task_notification
from ..mobile.runtime import update_tmux_mobile_indicator

logger = logging.getLogger(__name__)


@click.command("run-tests")
@click.argument("command", nargs=-1)
@click.option(
    "--cwd",
    type=click.Path(file_okay=False, dir_okay=True),
    help="🔬 Execution Coordinate: Working directory for the test ritual.",
)
@click.option(
    "--label",
    default="Test run",
    show_default=True,
    help="🏷️  Ritual Label: Notification identifier for this test run.",
)
@click.pass_context
def run_tests(ctx, command: Sequence[str], cwd: Optional[str], label: str):
    """
    🧪 Validation Ritual: Run automated tests and send satellite notifications

    Executes the prescribed test sequence while synchronizing cognitive
    telemetry. Automatically tracks focus state and transmits ritual results
    to the satellite HUD.
    """

    args = list(command) if command else ["pytest"]
    task_label = label or "Test run"

    with mobile_task_notification(
        ctx,
        task_label,
        success_message=f"✅ {task_label} complete",
        failure_message=f"❌ {task_label} failed",
    ):
        result = subprocess.run(args, cwd=cwd, check=False)
        cmd_display = " ".join(args)

        if result.returncode == 0:
            console.logger.info(f"[success]✅ Tests passed ({cmd_display})[/success]")
        else:
            console.logger.error(f"[error]❌ Tests failed ({cmd_display})[/error]")
            sys.exit(result.returncode)

    cfg_manager = ctx.obj.get("config_manager") if ctx.obj else ConfigManager()
    update_tmux_mobile_indicator(cfg_manager)


@click.command("run-build")
@click.argument("command", nargs=-1)
@click.option(
    "--cwd",
    type=click.Path(file_okay=False, dir_okay=True),
    help="🔬 Execution Coordinate: Working directory for the build ritual.",
)
@click.option(
    "--label",
    default="Build",
    show_default=True,
    help="🏷️  Ritual Label: Notification identifier for this build run.",
)
@click.pass_context
def run_build(ctx, command: Sequence[str], cwd: Optional[str], label: str):
    """
    🏗️  Materialization Ritual: Run a build command and send satellite notifications

    Engages the materialization engine to execute the specified build
    ritual while synchronizing cognitive telemetry.
    """

    args = list(command) if command else ["npm", "run", "build"]
    task_label = label or "Build"

    with mobile_task_notification(
        ctx,
        task_label,
        success_message=f"✅ {task_label} complete",
        failure_message=f"❌ {task_label} failed",
    ):
        result = subprocess.run(args, cwd=cwd, check=False)
        cmd_display = " ".join(args)

        if result.returncode == 0:
            console.logger.info(
                f"[success]✅ Build succeeded ({cmd_display})[/success]"
            )
        else:
            console.logger.error(f"[error]❌ Build failed ({cmd_display})[/error]")
            sys.exit(result.returncode)

    cfg_manager = ctx.obj.get("config_manager") if ctx.obj else ConfigManager()
    update_tmux_mobile_indicator(cfg_manager)
