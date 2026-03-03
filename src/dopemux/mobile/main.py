from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click

# Resolve the repo root relative to this file's location
REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts" / "mobile"


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    """📱 dopemux-mobile: ADHD-optimized mobile tmux environment.

    Provides a specialized tmux session for Blink Shell (iOS) with 
    Supervisor/Implementer splits and zero-chord navigation.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(launch)


@main.command()
def launch() -> None:
    """🚀 Launch or attach to the mobile tmux session."""
    script_path = SCRIPTS_DIR / "dopemux-mobile.sh"
    if not script_path.exists():
        click.echo(f"Error: Bootstrap script not found at {script_path}", err=True)
        sys.exit(1)

    # Hand over process to the shell script
    os.execvp(str(script_path), [str(script_path)])


@main.command()
def attach() -> None:
    """🧭 Alias for launch: Attach to the mobile session."""
    launch.callback() # Call launch callback directly


@main.command()
def setup() -> None:
    """🏥 Run the mobile setup verification script."""
    script_path = SCRIPTS_DIR / "verify-setup.sh"
    if not script_path.exists():
        click.echo(f"Error: Verification script not found at {script_path}", err=True)
        sys.exit(1)

    subprocess.run([str(script_path)], check=True)


@main.command()
def status() -> None:
    """📊 Show the mobile tmux session status."""
    socket_name = "dopemux-mobile"
    try:
        subprocess.run(["tmux", "-L", socket_name, "ls"], check=True)
    except subprocess.CalledProcessError:
        click.echo(f"No active dopemux-mobile session found on socket '{socket_name}'.")


if __name__ == "__main__":
    main()
