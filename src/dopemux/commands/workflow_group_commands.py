"""
Workflow Group Commands
"""

import json
import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console
from .capture_group_commands import _workflow_request
from ..workflow import DEFAULT_COMPLETION_TOKEN, WorkflowKernel
from ..workflow.orchestration import WorkflowOrchestrator

@click.group("workflow")
def workflow_group():
    """
    📜 Mission Planning: Orchestrate ritual workflows and ideas

    Manages the lifecycle of cockpit missions, from initial pattern synthesis 
    to high-fidelity execution. Synchronizes across active workflows, ideas, 
    and epics to ensure cognitive alignment with mission objectives.
    """
    pass


def _print_workflow_summary(state) -> None:
    console.print(
        f"[success]Workflow[/success] [mint]{state.workflow_id}[/mint] "
        f"[text.dim]phase={state.phase.value} status={state.status.value}[/text.dim]"
    )
    console.print(f"[text.dim]workspace[/text.dim] {state.workspace_root}")
    if state.active_workspace and state.active_workspace != state.workspace_root:
        console.print(f"[text.dim]active workspace[/text.dim] {state.active_workspace}")
    if state.brief_path:
        console.print(f"[text.dim]brief[/text.dim] {state.brief_path}")
    console.print(
        f"[text.dim]pm authority[/text.dim] {state.pm_authority} "
        f"(reachable={state.pm_reachable})"
    )


@workflow_group.command("init")
@click.argument("prompt", required=False)
@click.option("--mode", type=click.Choice(["manager", "executor"]), default="manager", show_default=True, help="🧠 Cognitive Mode: Select manager for planning or executor for materialization.")
@click.option("--max-iterations", type=int, default=0, show_default=True, help="🚀 Scaling Threshold: Maximum ritual iterations (0 for infinite).")
@click.option("--max-minutes", type=int, default=0, show_default=True, help="⏳ Temporal Limit: Maximum duration in minutes for the ritual.")
@click.option("--completion-token", default=DEFAULT_COMPLETION_TOKEN, show_default=True, help="🏁 Signal Completion: Token identifier for ritual termination.")
@click.option("--force-new", is_flag=True, help="⚡ Force Ignition: Always materialize a new workflow, bypassing existing sessions.")
def workflow_init(
    prompt: Optional[str],
    mode: str,
    max_iterations: int,
    max_minutes: int,
    completion_token: str,
    force_new: bool,
):
    """
    🚀 Ignite Mission: Create or resume a local ritual workflow

    Initializes a new cockpit mission or synchronizes with an existing 
    temporal coordinate to continue an active workflow.
    """
    kernel = WorkflowKernel(Path.cwd())
    state = kernel.init_workflow(
        prompt=prompt or "",
        mode=mode,
        max_iterations=max_iterations,
        max_minutes=max_minutes,
        completion_token=completion_token,
        force_new=force_new,
    )
    _print_workflow_summary(state)


@workflow_group.command("status")
@click.option("--workflow-id", default=None, help="🆔 Ritual Session: Explicit identifier for the mission to query.")
@click.option("--json-output", "json_output", is_flag=True, help="📊 Emit JSON: Output mission telemetry as raw machine-readable data.")
def workflow_status(workflow_id: Optional[str], json_output: bool):
    """
    📊 Mission HUD: Show active workflow status and telemetry

    Retrieves current operational coordinates for the mission bound to 
    the active workspace, detailing phase progression and gate status.
    """
    kernel = WorkflowKernel(Path.cwd())
    state = kernel.resolve(workflow_id)
    if not state:
        raise click.ClickException("No workflow is bound to this workspace or instance.")

    inspection = kernel.inspection(state)
    if json_output:
        click.echo(json.dumps(inspection, indent=2, sort_keys=True))
        return

    _print_workflow_summary(state)
    if inspection["task_title"]:
        console.print(
            f"[text.dim]task[/text.dim] {inspection['task_title']} "
            f"[text.dim]({inspection['task_status']})[/text.dim]"
        )
    if inspection["gate_failures"]:
        console.print("[warning]Gate failures:[/warning]")
        for failure in inspection["gate_failures"]:
            console.print(f"  - {failure}")
    else:
        console.print("[success]No gate failures for the current phase.[/success]")


@workflow_group.command("resume")
@click.option("--workflow-id", default=None, help="🆔 Ritual Session: Explicit identifier for the mission to rebind.")
def workflow_resume(workflow_id: Optional[str]):
    """
    ▶️ Re-Engage Mission: Rebind workspace to an existing workflow

    Synchronizes the active cockpit coordinates with a previously 
    established mission session.
    """
    kernel = WorkflowKernel(Path.cwd())
    state = kernel.resume(workflow_id)
    if not state:
        raise click.ClickException("No workflow found to resume.")
    _print_workflow_summary(state)


@workflow_group.command("cancel")
@click.option("--workflow-id", default=None, help="🆔 Ritual Session: Explicit identifier for the mission to cancel.")
def workflow_cancel(workflow_id: Optional[str]):
    """
    ⏹️ Halt Mission: Deactivate current workflow sequence

    Suspends the active ritual sequence without purging mission artifacts 
    from the ritual ledger.
    """
    kernel = WorkflowKernel(Path.cwd())
    state = kernel.cancel(workflow_id)
    if not state:
        raise click.ClickException("No workflow found to cancel.")
    _print_workflow_summary(state)


@workflow_group.command("inspect")
@click.option("--workflow-id", default=None, help="🆔 Ritual Session: Explicit identifier for the mission to audit.")
@click.option("--json-output", "json_output", is_flag=True, help="📊 Deep Telemetry: Emit full structured mission state.")
def workflow_inspect(workflow_id: Optional[str], json_output: bool):
    """
    🔬 Deep Audit: Show mission details, checkpoints, and launch preview

    Performs a high-fidelity audit of the active mission, detailing 
    temporal checkpoints and materializing a preview of the next ritual step.
    """
    kernel = WorkflowKernel(Path.cwd())
    state = kernel.resolve(workflow_id)
    if not state:
        raise click.ClickException("No workflow found to inspect.")

    inspection = kernel.inspection(state)
    orchestrator = WorkflowOrchestrator(Path(state.workspace_root))
    launch_preview = None
    if state.current_task():
        try:
            spec = orchestrator.build_worker_launch_spec(state)
            launch_preview = {
                "task_id": spec.task_id,
                "instance_id": spec.instance_id,
                "branch_name": spec.branch_name,
                "worktree_path": str(spec.worktree_path),
                "session_name": spec.session_name,
                "window_name": spec.window_name,
                "command": spec.command,
            }
        except Exception as exc:
            launch_preview = {"error": str(exc)}

    payload = {
        "inspection": inspection,
        "state": state.to_dict(),
        "launch_preview": launch_preview,
    }
    if json_output:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    _print_workflow_summary(state)
    console.print(f"[text.dim]history entries[/text.dim] {len(state.history)}")
    console.print(f"[text.dim]checkpoints[/text.dim] {len(state.checkpoints)}")

    if state.checkpoints:
        console.print("[mint]Recent checkpoints:[/mint]")
        for checkpoint in state.checkpoints[-3:]:
            console.print(
                f"  - {checkpoint.phase.value}:{checkpoint.status.value} "
                f"{checkpoint.summary or checkpoint.task_id or ''}".rstrip()
            )

    if launch_preview:
        console.print("[gold]Executor launch preview:[/gold]")
        if "error" in launch_preview:
            console.print(f"  - {launch_preview['error']}")
        else:
            console.print(
                f"  - instance {launch_preview['instance_id']} -> {launch_preview['worktree_path']}"
            )
            console.print(f"  - {launch_preview['command']}")


@workflow_group.group("ideas")
def workflow_ideas_group():
    """
    💡 Cognitive Seeds: Manage mission ideas and ritual patterns

    Orchestrates the synthesis and cataloging of cockpit ideas. These 
    seeds can be promoted to active missions once ritual feasibility is 
    established.
    """
    pass


@workflow_ideas_group.command("add", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("tokens", nargs=-1, type=click.UNPROCESSED)
def workflow_ideas_add(tokens: Sequence[str]):
    """
    ✨ Seed Idea: Capture a new cockpit observation or pattern

    Writes a new idea signal to the mission ledger, detailing its 
    title, description, and ritual source.
    """
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
    """
    🚀 Promote Signal: Elevate an idea to an active mission

    Engages the promotion engine to transform a cognitive seed into 
    a high-fidelity ritual mission, synchronizing with PM authorities.
    """
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
    """
    📈 Grand Rituals: Manage cockpit epics and long-term missions

    Orchestrates high-level mission groups (epics). Synchronizes 
    across multiple ritual missions to track long-term cockpit objectives.
    """
    pass


@workflow_epics_group.command("list")
@click.option("--status", default=None, help="📊 Ritual State: Filter epics by operational status.")
@click.option("--priority", default=None, help="🎯 Mission Priority: Filter epics by calibration level.")
@click.option("--tag", default=None, help="🔬 Signal Filter: Filter epics by specific ritual tag.")
@click.option("--limit", type=int, default=20, show_default=True, help="📊 Telemetry Limit: Maximum epics to render in the HUD.")
def workflow_epics_list(status: Optional[str], priority: Optional[str], tag: Optional[str], limit: int):
    """
    📋 Catalog Epics: List all active grand rituals and missions

    Displays the full index of cockpit epics, detailing their 
    operational state and mission alignment.
    """
    params = {"limit": limit}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    if tag:
        params["tag"] = tag

    _workflow_request("GET", "/api/workflow/epics", params=params)
