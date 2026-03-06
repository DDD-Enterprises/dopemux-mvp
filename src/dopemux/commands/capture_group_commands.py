"""
Capture Group Commands
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

@click.group("capture")
def capture_group():
    """Capture events into Chronicle."""
    pass


@capture_group.command("emit")
@click.option("--event", type=str, required=True, help="Event JSON object")
@click.option(
    "--mode",
    type=click.Choice(["plugin", "cli", "mcp", "auto"]),
    default="auto",
    help="Capture mode",
)
@click.option("--repo-root", type=click.Path(exists=True, path_type=Path), default=None)
def capture_emit(event: str, mode: str, repo_root: Optional[Path]):
    import json

    try:
        event_data = json.loads(event)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON: {exc}")

    if not isinstance(event_data, dict):
        raise click.ClickException("event must decode to an object")

    emit_capture_event(
        event_data,
        mode=mode,
        repo_root=repo_root,
        emit_event_bus=False,
    )


@capture_group.command("note", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("tokens", nargs=-1, type=click.UNPROCESSED)
def capture_note(tokens: Sequence[str]):
    if not tokens:
        raise click.ClickException("summary is required")

    summary = tokens[0]
    mode = "auto"
    tags: List[str] = []
    session_id: Optional[str] = None
    source = "cli"

    i = 1
    while i < len(tokens):
        arg = tokens[i]
        if arg == "--mode":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--mode requires a value")
            mode = tokens[i]
        elif arg == "--tag":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--tag requires a value")
            tags.append(tokens[i])
        elif arg == "--session-id":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--session-id requires a value")
            session_id = tokens[i]
        elif arg == "--source":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--source requires a value")
            source = tokens[i]
        else:
            raise click.ClickException(f"Unknown option: {arg}")
        i += 1

    event = {
        "event_type": "manual.note",
        "source": source,
        "payload": {
            "summary": summary,
            "tags": tags,
        },
    }
    if session_id:
        event["session_id"] = session_id

    emit_capture_event(
        event,
        mode=mode,
        emit_event_bus=False,
    )


def _workflow_api_base_url() -> str:
    return os.getenv("DOPEMUX_WORKFLOW_API_URL", "http://localhost:8000").rstrip("/")


def _workflow_request(method: str, path: str, *, json_payload=None, params=None):
    import requests

    url = f"{_workflow_api_base_url()}{path}"
    response = requests.request(method, url, json=json_payload, params=params, timeout=30)
    if response.status_code >= 400:
        raise click.ClickException(f"Workflow API error {response.status_code}: {response.text}")
    return response


