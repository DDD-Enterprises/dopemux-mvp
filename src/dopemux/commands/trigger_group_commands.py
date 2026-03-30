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

def _log(message: str, quiet: bool = False, level: str = "info"):
    if not quiet:
        if level == "error":
            console.logger.error(f"[error]❌ {message}[/error]")
        elif level == "success":
            console.logger.info(f"[success]✅ {message}[/success]")
        else:
            console.logger.info(f"[info]ℹ️  {message}[/info]")



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
    payload = {}
    if context:
        try:
            payload = json.loads(context)
            if not isinstance(payload, dict):
                payload = {"raw_context": context}
        except json.JSONDecodeError:
            payload = {"raw_context": context}

    event = {
        "event_type": "shell.command",
        "source": "cli",
        "payload": payload,
    }
    
    try:
        emit_capture_event(event, mode="auto")
        _log("Shell command signal emitted", quiet=quiet, level="success")
    except CaptureError as exc:
        _log(f"Capture failed: {exc}", quiet=quiet, level="error")
        sys.exit(1)
    except Exception as exc:
        _log(f"Unexpected error: {exc}", quiet=quiet, level="error")
        sys.exit(1)
