"""
Trigger Group Commands
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
from ..memory.capture_client import CaptureError, emit_capture_event

@click.group("trigger")
def trigger_group():
    """Internal hook triggers."""
    pass

@trigger_group.command("command-done")
@click.option("--async", "_async", is_flag=True, help="No-op")
@click.option("--quiet", is_flag=True, help="Suppress output")
def trigger_command_done(_async: bool, quiet: bool):
    if _async and not quiet:
        quiet = True
    try:
        emit_capture_event(
            {"event_type": "command.done", "payload": {}},
            mode="auto",
            emit_event_bus=False,
        )
    except CaptureError:
        sys.exit(1)
    if not quiet:
        console.print("[dim]command-done trigger received[/dim]")
    return 0

@trigger_group.command("shell-command")
@click.option("--context", type=str, help="JSON context", default="")
@click.option("--async", "_async", is_flag=True, help="No-op")
@click.option("--quiet", is_flag=True, help="Suppress output")
def trigger_shell_command(context: str, _async: bool, quiet: bool):
    import json

    if _async and not quiet:
        quiet = True
    payload: dict = {}
    if context:
        try:
            parsed_context = json.loads(context)
            payload = parsed_context if isinstance(parsed_context, dict) else {"context": parsed_context}
        except json.JSONDecodeError:
            payload = {"raw_context": context}
    try:
        emit_capture_event(
            {"event_type": "shell.command", "payload": payload},
            mode="auto",
            emit_event_bus=False,
        )
    except CaptureError:
        sys.exit(1)
    if not quiet:
        console.print("[dim]shell-command trigger received[/dim]")
    return 0


