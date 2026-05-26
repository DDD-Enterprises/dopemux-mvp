"""Read-only Task Orchestrator operator commands."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import click

from dopemux.orchestrator.hooks import (
    audit_hook_registry_file,
    hook_registry_list_payload,
    validate_hook_registry_file,
)
from dopemux.orchestrator.policy import (
    classify_capability,
    load_approval_policy,
    validate_policy_file,
)
from dopemux.orchestrator.validation.packets import validate_packet_file
from dopemux.orchestrator.validation.proof import validate_proof_file
from dopemux.orchestrator.validation.report import ValidationReport
from dopemux.orchestrator.workflow_dsl import validate_workflow_dsl_file


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


def _emit_validation_report(report: ValidationReport, *, title: str, json_output: bool):
    if json_output:
        click.echo(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        lines = [
            title,
            f"path: {report.path}",
            f"authority: {report.authority}",
            f"status: {report.status}",
        ]
        for error in report.errors:
            suffix = f" {error['path']}" if error.get("path") else ""
            lines.append(f"{error['code']}{suffix}: {error['message']}")
        if not report.errors:
            lines.append("errors: none")
        _emit_lines(lines)

    if report.exit_code:
        raise click.exceptions.Exit(report.exit_code)


@click.group("orchestrator")
def orchestrator_group():
    """Read-only Task Orchestrator status and daily planning views."""


@orchestrator_group.group("packet")
def orchestrator_packet():
    """Read-only Task Packet validation helpers."""


@orchestrator_packet.command("validate")
@click.argument("packet_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--schema",
    "schema_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--json-output", is_flag=True)
def orchestrator_packet_validate(
    packet_path: Path,
    schema_path: Optional[Path],
    json_output: bool,
):
    """Validate a Task Packet against the canonical repo schema."""
    report = validate_packet_file(packet_path, schema_path=schema_path)
    _emit_validation_report(
        report,
        title="Task Orchestrator Packet Validation",
        json_output=json_output,
    )


@orchestrator_group.group("proof")
def orchestrator_proof():
    """Read-only proof bundle validation helpers."""


@orchestrator_proof.command("validate")
@click.argument("proof_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--json-output", is_flag=True)
def orchestrator_proof_validate(proof_path: Path, json_output: bool):
    """Validate proof bundle shape without writing proof artifacts."""
    report = validate_proof_file(proof_path)
    _emit_validation_report(
        report,
        title="Task Orchestrator Proof Validation",
        json_output=json_output,
    )


@orchestrator_group.group("workflow")
def orchestrator_workflow():
    """Read-only workflow DSL validation helpers."""


@orchestrator_workflow.command("validate")
@click.argument("workflow_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--json-output", is_flag=True)
def orchestrator_workflow_validate(workflow_path: Path, json_output: bool):
    """Validate a workflow DSL file without applying transitions."""
    report = validate_workflow_dsl_file(workflow_path)
    _emit_validation_report(
        report,
        title="Task Orchestrator Workflow DSL Validation",
        json_output=json_output,
    )


@orchestrator_group.group("hooks")
def orchestrator_hooks():
    """Read-only declarative hook registry helpers."""


@orchestrator_hooks.command("list")
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--json-output", is_flag=True)
def orchestrator_hooks_list(registry_path: Optional[Path], json_output: bool):
    """List declarative orchestrator hooks without executing them."""
    payload = hook_registry_list_payload(registry_path)
    if json_output:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return

    lines = [
        "Task Orchestrator Hooks",
        f"path: {payload['path']}",
        f"authority: {payload['authority']}",
        f"hook_count: {payload['hook_count']}",
    ]
    for hook in payload["hooks"]:
        lines.append(
            f"{hook['id']}: tier={hook['tier']} trigger={hook['trigger']}"
        )
    _emit_lines(lines)


@orchestrator_hooks.command("validate")
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--json-output", is_flag=True)
def orchestrator_hooks_validate(registry_path: Optional[Path], json_output: bool):
    """Validate the declarative hook registry without executing hooks."""
    report = validate_hook_registry_file(registry_path)
    _emit_validation_report(
        report,
        title="Task Orchestrator Hook Registry Validation",
        json_output=json_output,
    )


@orchestrator_group.group("plugins")
def orchestrator_plugins():
    """Read-only orchestrator plugin safety helpers."""


@orchestrator_plugins.command("doctor")
@click.option(
    "--registry",
    "registry_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--json-output", is_flag=True)
def orchestrator_plugins_doctor(registry_path: Optional[Path], json_output: bool):
    """Audit declarative plugin hook safety without loading plugins."""
    report = audit_hook_registry_file(registry_path)
    _emit_validation_report(
        report,
        title="Task Orchestrator Plugin Hook Doctor",
        json_output=json_output,
    )


@orchestrator_group.group("policy")
def orchestrator_policy():
    """Read-only approval policy registry helpers."""


@orchestrator_policy.command("validate")
@click.option(
    "--policy",
    "policy_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--json-output", is_flag=True)
def orchestrator_policy_validate(policy_path: Optional[Path], json_output: bool):
    """Validate the automation tier and approval policy registry."""
    report = validate_policy_file(policy_path)
    _emit_validation_report(
        report,
        title="Task Orchestrator Approval Policy Validation",
        json_output=json_output,
    )


@orchestrator_policy.command("tiers")
@click.option("--json-output", is_flag=True)
def orchestrator_policy_tiers(json_output: bool):
    """Show registered automation safety tiers."""
    policy = load_approval_policy()
    tiers = {key: tier.to_dict() for key, tier in policy.tiers.items()}
    if json_output:
        click.echo(json.dumps({"tiers": tiers}, indent=2, sort_keys=True))
        return

    lines = ["Task Orchestrator Automation Tiers", f"path: {policy.source_path}"]
    for tier_id, tier in policy.tiers.items():
        lines.append(
            (
                f"{tier_id}: auto={tier.automatic_allowed} "
                f"approval={tier.approval_required} "
                f"receipt={tier.receipt_required} decision={tier.decision}"
            )
        )
    _emit_lines(lines)


@orchestrator_policy.command("capabilities")
@click.option("--json-output", is_flag=True)
def orchestrator_policy_capabilities(json_output: bool):
    """Show registered orchestrator policy capabilities."""
    policy = load_approval_policy()
    capabilities = {
        key: capability.to_dict()
        for key, capability in policy.capabilities.items()
    }
    if json_output:
        click.echo(
            json.dumps(
                {"capabilities": capabilities},
                indent=2,
                sort_keys=True,
            )
        )
        return

    lines = [
        "Task Orchestrator Policy Capabilities",
        f"path: {policy.source_path}",
    ]
    for capability_id, capability in policy.capabilities.items():
        lines.append(
            (
                f"{capability_id}: tier={capability.tier} "
                f"mode={capability.mode} decision={capability.decision}"
            )
        )
    _emit_lines(lines)


@orchestrator_policy.command("classify")
@click.argument("capability_id")
@click.option("--json-output", is_flag=True)
def orchestrator_policy_classify(capability_id: str, json_output: bool):
    """Classify one capability against the approval policy registry."""
    decision = classify_capability(capability_id)
    if json_output:
        click.echo(json.dumps(decision.to_dict(), indent=2, sort_keys=True))
        return

    _emit_lines(
        [
            "Task Orchestrator Capability Classification",
            f"capability: {decision.capability_id}",
            f"tier: {decision.tier}",
            f"mode: {decision.mode}",
            f"allowed: {decision.allowed}",
            f"decision: {decision.decision}",
            f"approval_required: {decision.approval_required}",
            f"receipt_required: {decision.receipt_required}",
            f"reason: {decision.reason}",
        ]
    )


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
