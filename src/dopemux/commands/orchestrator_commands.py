"""Read-only Task Orchestrator operator commands."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Iterable, List, Optional

import click


DEFAULT_PROJECT_ID = "dopemux-mvp"


async def pm_get_priority_queue(project_id: str):
    from dopemux.pm.reads import pm_get_priority_queue as read_priority_queue

    return await read_priority_queue(project_id)


async def pm_get_blockers(project_id: str):
    from dopemux.pm.reads import pm_get_blockers as read_blockers

    return await read_blockers(project_id)


async def pm_get_workflow_state(project_id: str):
    from dopemux.pm.reads import pm_get_workflow_state as read_workflow_state

    return await read_workflow_state(project_id)


def _to_mapping(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    return {}


def _error_text(payload: Dict[str, Any]) -> Optional[str]:
    error = payload.get("error")
    return str(error) if error else None


def _authority(payload: Dict[str, Any]) -> str:
    provenance = payload.get("provenance") or {}
    if isinstance(provenance, dict):
        return str(provenance.get("source") or payload.get("canonical_backend") or "UNKNOWN")
    return str(payload.get("canonical_backend") or "UNKNOWN")


def _item_token(item: Dict[str, Any]) -> str:
    for key in ("id", "packet_id", "task_id", "workflow_id", "ticket_id"):
        value = item.get(key)
        if value:
            return str(value)
    return "-"


def _item_title(item: Dict[str, Any]) -> str:
    for key in ("title", "name", "summary", "description"):
        value = item.get(key)
        if value:
            return str(value)
    return ""


def _render_top_items(items: Iterable[Dict[str, Any]]) -> List[str]:
    rows: List[str] = []
    for index, item in enumerate(list(items)[:3], start=1):
        token = _item_token(item)
        title = _item_title(item)
        rows.append(f"{index}. {token} {title}".rstrip())
    return rows


def _next_token(payload: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    next_action = payload.get("next_action") or {}
    if isinstance(next_action, dict):
        token = _item_token(next_action)
        if token != "-":
            return token
    if items:
        return _item_token(items[0])
    return "none"


def _emit_lines(lines: Iterable[str]) -> None:
    for line in lines:
        click.echo(line)


def _run(awaitable):
    return asyncio.run(awaitable)


@click.group("orchestrator")
def orchestrator_group():
    """Read-only Task Orchestrator status and daily planning views."""


@orchestrator_group.command("queue")
@click.option("--project-id", default=DEFAULT_PROJECT_ID, show_default=True)
@click.option("--json-output", is_flag=True)
def orchestrator_queue(project_id: str, json_output: bool):
    """Show the read-only workflow priority queue."""
    payload = _to_mapping(_run(pm_get_priority_queue(project_id)))
    if json_output:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    items = list(payload.get("queue_items") or [])
    error = _error_text(payload)
    lines = [
        "Task Orchestrator Queue",
        f"project: {project_id}",
        f"authority: {_authority(payload)}",
        f"legality_result: {payload.get('legality_result', 'unavailable')}",
    ]
    if error:
        lines.append(f"error: {error}")
    if items:
        lines.extend(_render_top_items(items))
    else:
        lines.append("queue: empty")
    lines.append(f"more_count: {max(len(items) - 3, 0)}")
    lines.append(f"next_token: {_next_token(payload, items)}")
    _emit_lines(lines)


@orchestrator_group.command("blockers")
@click.option("--project-id", default=DEFAULT_PROJECT_ID, show_default=True)
@click.option("--json-output", is_flag=True)
def orchestrator_blockers(project_id: str, json_output: bool):
    """Show read-only workflow blockers."""
    payload = _to_mapping(_run(pm_get_blockers(project_id)))
    if json_output:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    blockers = list(payload.get("active_blockers") or [])
    error = _error_text(payload)
    lines = [
        "Task Orchestrator Blockers",
        f"project: {project_id}",
        f"authority: {_authority(payload)}",
        f"legality_result: {payload.get('legality_result', 'unavailable')}",
    ]
    if error:
        lines.append(f"error: {error}")
    if blockers:
        lines.extend(_render_top_items(blockers))
    else:
        lines.append("blockers: empty")
    lines.append(f"more_count: {max(len(blockers) - 3, 0)}")
    lines.append(f"next_token: {_next_token(payload, blockers)}")
    _emit_lines(lines)


@orchestrator_group.command("status")
@click.option("--project-id", default=DEFAULT_PROJECT_ID, show_default=True)
@click.option("--json-output", is_flag=True)
def orchestrator_status(project_id: str, json_output: bool):
    """Show read-only workflow state."""
    payload = _to_mapping(_run(pm_get_workflow_state(project_id)))
    if json_output:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    state = payload.get("state") or {}
    allowed = payload.get("allowed_transitions") or []
    error = _error_text(payload)
    lines = [
        "Task Orchestrator Status",
        f"project: {project_id}",
        f"authority: {_authority(payload)}",
        f"legality_result: {payload.get('legality_result', 'unavailable')}",
    ]
    if error:
        lines.append(f"error: {error}")
    if state:
        for key, value in state.items():
            lines.append(f"{key}: {value}")
    else:
        lines.append("state: empty")
    lines.append(f"allowed_transitions: {', '.join(allowed) if allowed else 'none'}")
    _emit_lines(lines)


@orchestrator_group.command("daily")
@click.option("--project-id", default=DEFAULT_PROJECT_ID, show_default=True)
@click.option("--json-output", is_flag=True)
def orchestrator_daily(project_id: str, json_output: bool):
    """Show the read-only daily operator workflow summary."""
    queue_payload = _to_mapping(_run(pm_get_priority_queue(project_id)))
    blockers_payload = _to_mapping(_run(pm_get_blockers(project_id)))
    workflow_payload = _to_mapping(_run(pm_get_workflow_state(project_id)))
    payloads = {
        "queue": queue_payload,
        "blockers": blockers_payload,
        "workflow_state": workflow_payload,
    }
    if json_output:
        click.echo(json.dumps(payloads, indent=2, sort_keys=True))
        return

    failures = {
        name: _error_text(payload)
        for name, payload in payloads.items()
        if _error_text(payload)
    }
    queue_items = list(queue_payload.get("queue_items") or [])
    blocker_items = list(blockers_payload.get("active_blockers") or [])
    workflow_state = workflow_payload.get("state") or {}
    lines = [
        "Task Orchestrator Daily",
        f"project: {project_id}",
        f"authority: {_authority(queue_payload)}",
    ]
    for name, payload in payloads.items():
        error = _error_text(payload)
        if error:
            lines.append(f"{name}: ERROR {error}")
        else:
            lines.append(f"{name}: {payload.get('legality_result', 'available')}")
    lines.append(f"partial_failures: {len(failures)}")
    lines.append("queue_top:")
    lines.extend(_render_top_items(queue_items) or ["queue: empty"])
    lines.append(f"queue_more_count: {max(len(queue_items) - 3, 0)}")
    lines.append(f"queue_next_token: {_next_token(queue_payload, queue_items)}")
    lines.append("blockers_top:")
    lines.extend(_render_top_items(blocker_items) or ["blockers: empty"])
    if workflow_state:
        for key, value in workflow_state.items():
            lines.append(f"{key}: {value}")
    else:
        lines.append("state: empty")
    _emit_lines(lines)
