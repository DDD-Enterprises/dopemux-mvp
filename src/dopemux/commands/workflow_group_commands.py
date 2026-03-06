"""
Workflow Group Commands
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
from .capture_group_commands import _workflow_request

@click.group("workflow")
def workflow_group():
    """Workflow planning commands."""
    pass


@workflow_group.group("ideas")
def workflow_ideas_group():
    """Workflow idea management."""
    pass


@workflow_ideas_group.command("add", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("tokens", nargs=-1, type=click.UNPROCESSED)
def workflow_ideas_add(tokens: Sequence[str]):
    title: Optional[str] = None
    description: Optional[str] = None
    source = "manual"
    creator = "cli"
    tags: List[str] = []

    i = 0
    while i < len(tokens):
        arg = tokens[i]
        if arg == "--title":
            i += 1
            title = tokens[i] if i < len(tokens) else None
        elif arg == "--description":
            i += 1
            description = tokens[i] if i < len(tokens) else None
        elif arg == "--source":
            i += 1
            source = tokens[i] if i < len(tokens) else source
        elif arg == "--creator":
            i += 1
            creator = tokens[i] if i < len(tokens) else creator
        elif arg == "--tag":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--tag requires a value")
            tags.append(tokens[i])
        else:
            raise click.ClickException(f"Unknown option: {arg}")
        i += 1

    if not title:
        raise click.ClickException("--title is required")
    if not description:
        raise click.ClickException("--description is required")

    payload = {
        "title": title,
        "description": description,
        "source": source,
        "creator": creator,
        "tags": tags,
    }
    _workflow_request("POST", "/api/workflow/ideas", json_payload=payload)


@workflow_ideas_group.command("promote", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("idea_id")
@click.argument("tokens", nargs=-1, type=click.UNPROCESSED)
def workflow_ideas_promote(
    idea_id: str,
    tokens: Sequence[str],
):
    sync_leantime = True
    priority: Optional[str] = None
    business_value: Optional[str] = None
    criteria: List[str] = []
    tags: List[str] = []

    i = 0
    while i < len(tokens):
        arg = tokens[i]
        if arg == "--sync-leantime":
            sync_leantime = True
        elif arg == "--no-sync-leantime":
            sync_leantime = False
        elif arg == "--priority":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--priority requires a value")
            priority = tokens[i]
        elif arg == "--business-value":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--business-value requires a value")
            business_value = tokens[i]
        elif arg == "--criterion":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--criterion requires a value")
            criteria.append(tokens[i])
        elif arg == "--tag":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--tag requires a value")
            tags.append(tokens[i])
        else:
            raise click.ClickException(f"Unknown option: {arg}")
        i += 1

    payload = {
        "sync_to_leantime": sync_leantime,
        "acceptance_criteria": criteria,
        "tags": tags,
    }
    if priority:
        payload["priority"] = priority
    if business_value:
        payload["business_value"] = business_value

    _workflow_request("POST", f"/api/workflow/ideas/{idea_id}/promote", json_payload=payload)


@workflow_group.group("epics")
def workflow_epics_group():
    """Workflow epic management."""
    pass


@workflow_epics_group.command("list")
@click.option("--status", default=None, help="Filter by status")
@click.option("--priority", default=None, help="Filter by priority")
@click.option("--tag", default=None, help="Filter by single tag")
@click.option("--limit", type=int, default=20, show_default=True)
def workflow_epics_list(status: Optional[str], priority: Optional[str], tag: Optional[str], limit: int):
    params = {"limit": limit}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    if tag:
        params["tag"] = tag

    _workflow_request("GET", "/api/workflow/epics", params=params)
