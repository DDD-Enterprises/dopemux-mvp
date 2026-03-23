"""
Trigger Group Commands
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console
from ..memory.capture_client import CaptureError, emit_capture_event

@click.group("trigger")
def trigger_group():
    """
    ⚡ Sensor Triggers: Internal hook telemetry signals

    Orchestrates the automated ingestion of internal sensor signals. 
    These triggers synchronize shell rituals and command execution 
    telemetry into the persistent ritual ledger.
    """
    pass

@trigger_group.command("command-done")
@click.option("--async", "_async", is_flag=True, help="⚡ Asynchronous Ritual: Process the trigger in the background.")
@click.option("--quiet", is_flag=True, help="🔇 Silence HUD: Suppress telemetry output for this trigger.")
def trigger_command_done(_async: bool, quiet: bool):
    """
    ⚡ Signal Completion: Emit command termination telemetry

    Writes a 'command.done' signal to the ritual ledger, marking the 
    successful completion of a cockpit ritual.
    """
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
@click.option("--context", type=str, help="📊 Signal Context: JSON-encoded telemetry payload.", default="")
@click.option("--async", "_async", is_flag=True, help="⚡ Asynchronous Ritual: Process the trigger in the background.")
@click.option("--quiet", is_flag=True, help="🔇 Silence HUD: Suppress telemetry output.")
def trigger_shell_command(context: str, _async: bool, quiet: bool):
    """
    🐚 Shell Telemetry: Emit interactive shell signal

    Writes a 'shell.command' signal to the ritual ledger, capturing 
    the active shell context and ritual coordinates.
    """
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
