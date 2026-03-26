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
from ..workflow import WorkflowStore
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


def _resolve_instance_id(value: Optional[str]) -> str:
    return value or os.environ.get("DOPEMUX_INSTANCE_ID") or "main"


def _workflow_store_for_path(path: Optional[str]) -> WorkflowStore:
    return WorkflowStore.for_path(Path(path) if path else None)


def _load_workflow_state(
    *,
    path: Optional[str],
    workflow_id: Optional[str],
    instance_id: Optional[str],
) -> tuple[WorkflowStore, object]:
    store = _workflow_store_for_path(path)
    if workflow_id:
        state = store.load(workflow_id)
    else:
        resolved_instance_id = _resolve_instance_id(instance_id)
        state = store.resolve_active(resolved_instance_id)
        if state is None:
            raise click.ClickException(
                f"No active workflow found for instance '{resolved_instance_id}' in {store.workspace_root}"
            )
    return store, state


@workflow_group.command("init")
@click.option("--workflow-id", default=None, help="Explicit workflow identifier")
@click.option("--mode", default="internal", show_default=True)
@click.option("--instance-id", default=None, help="Workflow instance ID")
@click.option("--max-iterations", type=int, default=50, show_default=True)
@click.option("--max-minutes", type=int, default=120, show_default=True)
@click.option("--completion-token", default="WORKFLOW_COMPLETE", show_default=True)
@click.option("--path", "workspace_path", default=None, help="Workspace or child path")
def workflow_init(
    workflow_id: Optional[str],
    mode: str,
    instance_id: Optional[str],
    max_iterations: int,
    max_minutes: int,
    completion_token: str,
    workspace_path: Optional[str],
) -> None:
    """Create or resume the active local workflow for the current workspace."""
    store = _workflow_store_for_path(workspace_path)
    state = store.create_or_resume(
        workflow_id=workflow_id,
        instance_id=_resolve_instance_id(instance_id),
        mode=mode,
        max_iterations=max_iterations,
        max_minutes=max_minutes,
        completion_token=completion_token,
    )
    click.echo(
        yaml.safe_dump(
            {
                "workflow_id": state.workflow_id,
                "workspace_root": state.workspace_root,
                "instance_id": state.instance_id,
                "status": state.status.value,
                "phase": state.phase.value,
            },
            sort_keys=False,
        ).rstrip()
    )


@workflow_group.command("status")
@click.option("--workflow-id", default=None, help="Explicit workflow identifier")
@click.option("--instance-id", default=None, help="Workflow instance ID")
@click.option("--path", "workspace_path", default=None, help="Workspace or child path")
def workflow_status(
    workflow_id: Optional[str],
    instance_id: Optional[str],
    workspace_path: Optional[str],
) -> None:
    """Show concise local workflow status."""
    _, state = _load_workflow_state(
        path=workspace_path,
        workflow_id=workflow_id,
        instance_id=instance_id,
    )
    click.echo(
        yaml.safe_dump(
            {
                "workflow_id": state.workflow_id,
                "workspace_root": state.workspace_root,
                "instance_id": state.instance_id,
                "status": state.status.value,
                "phase": state.phase.value,
                "current_task_id": state.current_task_id,
                "iteration": state.iteration,
                "max_iterations": state.max_iterations,
                "max_minutes": state.max_minutes,
            },
            sort_keys=False,
        ).rstrip()
    )


@workflow_group.command("resume")
@click.option("--workflow-id", default=None, help="Explicit workflow identifier")
@click.option("--instance-id", default=None, help="Workflow instance ID")
@click.option("--path", "workspace_path", default=None, help="Workspace or child path")
def workflow_resume(
    workflow_id: Optional[str],
    instance_id: Optional[str],
    workspace_path: Optional[str],
) -> None:
    """Resolve a workflow by cwd ancestry or explicit ID and print its state."""
    _, state = _load_workflow_state(
        path=workspace_path,
        workflow_id=workflow_id,
        instance_id=instance_id,
    )
    click.echo(
        yaml.safe_dump(
            {
                "workflow_id": state.workflow_id,
                "workspace_root": state.workspace_root,
                "instance_id": state.instance_id,
                "status": state.status.value,
                "phase": state.phase.value,
                "current_task_id": state.current_task_id,
            },
            sort_keys=False,
        ).rstrip()
    )


@workflow_group.command("cancel")
@click.option("--workflow-id", default=None, help="Explicit workflow identifier")
@click.option("--instance-id", default=None, help="Workflow instance ID")
@click.option("--path", "workspace_path", default=None, help="Workspace or child path")
@click.option("--reason", default="Cancelled by operator", show_default=True)
def workflow_cancel(
    workflow_id: Optional[str],
    instance_id: Optional[str],
    workspace_path: Optional[str],
    reason: str,
) -> None:
    """Deactivate a workflow without deleting its state."""
    store, state = _load_workflow_state(
        path=workspace_path,
        workflow_id=workflow_id,
        instance_id=instance_id,
    )
    updated = store.cancel(state, reason)
    click.echo(
        yaml.safe_dump(
            {
                "workflow_id": updated.workflow_id,
                "status": updated.status.value,
                "phase": updated.phase.value,
                "reason": reason,
            },
            sort_keys=False,
        ).rstrip()
    )


@workflow_group.command("inspect")
@click.option("--workflow-id", default=None, help="Explicit workflow identifier")
@click.option("--instance-id", default=None, help="Workflow instance ID")
@click.option("--path", "workspace_path", default=None, help="Workspace or child path")
def workflow_inspect(
    workflow_id: Optional[str],
    instance_id: Optional[str],
    workspace_path: Optional[str],
) -> None:
    """Print detailed workflow checkpoints and validation status."""
    store, state = _load_workflow_state(
        path=workspace_path,
        workflow_id=workflow_id,
        instance_id=instance_id,
    )
    inspection = store.inspect(state)
    click.echo(yaml.safe_dump(inspection, sort_keys=False).rstrip())
