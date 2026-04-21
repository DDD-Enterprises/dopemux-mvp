"""
Bootstrap Commands

Project scaffolding and ConPort uplink wiring. ``init`` provisions the
local ``.dopemux/`` ritual chamber and installs the ConPort git hook.
``wire-conport`` re-runs the project-level ConPort wiring script.
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional

import click

from ..claude import ClaudeConfigurator
from ..claude_config import ClaudeConfigError
from ..console import console
from ..profile_models import ProfileValidationError
from ..project_init import init_project

logger = logging.getLogger(__name__)


@click.command("init")
@click.argument(
    "directory",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    required=False,
)
@click.option("--profile", "-p", help="Select a specific ritual profile (e.g., python, node, rust-mcp) to define the flight-deck capabilities.")
@click.option(
    "--force", "-f", is_flag=True, help="⚡ Overwrite existing .dopemux/ configurations. Useful for hard-resetting the cockpit state."
)
@click.option("--template", "-t", help="🔬 Select a Claude configuration template to align the ritual daemon's cognitive patterns.")
@click.pass_context
def init(
    ctx,
    directory: Optional[Path],
    profile: Optional[str],
    force: bool,
    template: Optional[str],
):
    """
    🚀 Synchronize Flight-Deck: Initialize DØPEMÜX Rituals

    Scaffolds the .dopemux/ ritual chamber within the target directory. This command
    provisions the local environment with profile-driven configurations,
    try:
        workspace_exists = workspace.exists()
        dopemux_exists = dopemux_dir.exists()
    except TypeError:
        pass

    Effects:
    - Generates .dopemux/ directory for state and instance persistence.
    - Provisions .claude/ workspace configuration for deep-linked automation.
    - Installs git hooks to automate ConPort wiring across worktrees.

    \b
    Examples:
        dopemux init                    # Auto-detect project type and launch setup wizard
        dopemux init -p python-ml       # Force use of the Python Machine Learning ritual
        dopemux init --force            # Reconstruct the ritual chamber (overwrites existing)
        dopemux init ../project-2       # Initialize a distant project coordinate
    """
    config_manager = ctx.obj["config_manager"]

    workspace = Path(directory or Path.cwd()).expanduser().resolve()
    dopemux_dir = workspace / ".dopemux"

    workspace_exists = False
    dopemux_exists = False
    try:
        workspace_exists = workspace.exists()
        dopemux_exists = Path.exists(dopemux_dir)
    except TypeError:
        console.logger.error("[error]Invalid workspace or dopemux path type[/error]")
        sys.exit(1)

    if directory and not workspace_exists and not dopemux_exists:
        console.logger.info(f"[error]Directory does not exist: {workspace}[/error]")
        sys.exit(1)

    if not force and dopemux_dir.is_dir():
        console.logger.info(
            f"[warning]⚠️  Project already initialized (.dopemux/ exists)[/warning]"
        )
        sys.exit(1)

    try:
        workspace.mkdir(parents=True, exist_ok=True)
    except (OSError, FileNotFoundError) as e:
        logger.error(f"Workspace directory creation failed: {e}")
    except Exception:
        logger.error("Unexpected error creating workspace directory", exc_info=True)
    success = init_project(workspace, profile, force)

    if not success:
        console.logger.info("[warning]Initialization cancelled.[/warning]")
        sys.exit(1)

    click.echo("Project Initialized")

    try:
        configurator = ClaudeConfigurator(config_manager)
        configurator.setup_project_config(workspace, template or "python", force=force)
    except (ClaudeConfigError, ProfileValidationError) as e:
        logger.error(f"Project configuration setup failed: {e}")
    except Exception:
        logger.error("Unexpected configurator error", exc_info=True)
    # Install git hook for automatic ConPort wiring
    try:
        hooks_dir = workspace / ".git" / "hooks"
        if hooks_dir.exists():
            src = (
                Path(__file__).resolve().parents[3]
                / "scripts"
                / "git_post_worktree_hook.sh"
            )
            dst = hooks_dir / "post-checkout"
            if not dst.exists():
                shutil.copy2(src, dst)
                dst.chmod(0o755)
                click.echo("🔗 Installed git post-checkout hook for ConPort wiring")
            else:
                click.echo("✅ Git post-checkout hook present")
    except (OSError, shutil.Error) as e:
        logger.error(f"Git hook installation failed: {e}")
    except Exception:
        logger.error("Unexpected git hook install error", exc_info=True)


@click.command("wire-conport")
@click.option("--instance", "-i", help="The specific instance identifier (e.g., A, B, C) or feature branch name to target for the uplink.")
@click.option("--project", "-p", help="The project root coordinate where the ConPort configuration should be wired.")
def wire_conport(instance: Optional[str], project: Optional[str]):
    """
    ⚡ Synchronize Uplink: Wire ConPort MCP Terminal

    Establishes the stdio uplink between the Claude cognitive engine and the
    ConPort ritual daemon. This command modifies .claude/claude_config.json to
    ensure that the cockpit can docker-exec into the correct instance container
    (mcp-conport[_<instance>]), bridging the gap between host and containerized state.
    """
    try:
        script = (
            Path(__file__).resolve().parents[3] / "scripts" / "wire_conport_project.py"
        )
        args = [sys.executable, str(script)]
        if instance:
            args.extend(["--instance", instance])
        if project:
            args.extend(["--project", project])
        subprocess.check_call(args)
        click.echo("✅ ConPort wired for this project/worktree")
    except CalledProcessError as e:
        click.echo(f"❌ Failed to wire ConPort: {e}", err=True)
        sys.exit(1)
