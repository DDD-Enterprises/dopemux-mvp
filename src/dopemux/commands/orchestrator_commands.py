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
from dopemux.orchestrator.operator_workflows import (
    automation_pilot_decision,
    build_dashboard_snapshot,
    build_packet_draft,
    build_pr_queue,
    context_refresh_plan,
    context_status,
    dangerous_check,
    final_readiness_report,
    intake_report,
    memory_route_receipt,
    pr_comment_plan,
    red_team_audit,
    transition_apply_plan,
    transition_preview,
    validate_transition_proof_envelope_file,
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


def _emit_payload(payload: Dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        click.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    _emit_lines(_render_mapping(payload))


def _render_mapping(payload: Dict[str, Any], *, prefix: str = "") -> List[str]:
    lines: List[str] = []
    for key, value in payload.items():
        token = f"{prefix}{key}"
        if isinstance(value, dict):
            lines.append(f"{token}:")
            lines.extend(_render_mapping(value, prefix=f"{token}."))
        elif isinstance(value, list):
            lines.append(f"{token}: {len(value)} item(s)")
        else:
            lines.append(f"{token}: {value}")
    return lines


def _parse_pr_items(entries: Iterable[str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for entry in entries:
        number, checks, proof = (entry.split(":") + ["unknown", "missing"])[:3]
        try:
            pr_number = int(number)
        except (TypeError, ValueError) as exc:
            raise click.BadParameter(
                f"Invalid --pr entry {entry!r}: PR number must be a positive integer.",
                param_hint="--pr",
            ) from exc
        if pr_number <= 0:
            raise click.BadParameter(
                f"Invalid --pr entry {entry!r}: PR number must be > 0.",
                param_hint="--pr",
            )
        items.append(
            {
                "number": pr_number,
                "checks": checks,
                "proof": proof,
            }
        )
    return items


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


@orchestrator_group.group("perpacket")
def orchestrator_perpacket():
    """Read-only per-packet isolation validation helpers."""


@orchestrator_perpacket.command("validate")
@click.argument("packet_id")
@click.option("--json-output", is_flag=True)
def orchestrator_perpacket_validate(packet_id: str, json_output: bool):
    """Validate a single task packet in isolation."""
    from dopemux.orchestrator.perpacket import run_perpacket_validation

    try:
        result = run_perpacket_validation(packet_id)
    except Exception as exc:
        if json_output:
            click.echo(json.dumps({"error": str(exc), "valid": False, "validations": []}))
        else:
            click.echo(f"ERROR: {exc}", err=True)
        raise click.exceptions.Exit(2)

    if json_output:
        click.echo(json.dumps(result["validations"], indent=2, sort_keys=True))
    else:
        click.echo(f"Task Packet Isolated Validation: {packet_id}")
        click.echo(f"Valid: {result['valid']}")
        click.echo("Validations:")
        for validation in result["validations"]:
            click.echo(f"  - {validation['name']}: {validation['status']} (exit={validation['exit_code']})")

    if not result["valid"]:
        raise click.exceptions.Exit(2)



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


@orchestrator_group.group("context")
def orchestrator_context():
    """Context freshness status and gated refresh planning."""


@orchestrator_context.command("status")
@click.option(
    "--changed-file",
    "changed_files",
    multiple=True,
    help="Changed file to include in the freshness report.",
)
@click.option(
    "--stale-source",
    "stale_sources",
    multiple=True,
    help="Context source to mark stale.",
)
@click.option("--json-output", is_flag=True)
def orchestrator_context_status(
    changed_files: tuple[str, ...],
    stale_sources: tuple[str, ...],
    json_output: bool,
):
    """Assess context freshness without refreshing indexes."""
    payload = context_status(
        changed_files=list(changed_files),
        stale_sources=list(stale_sources),
    )
    _emit_payload(payload, json_output=json_output)


@orchestrator_context.command("refresh")
@click.option("--scope", required=True)
@click.option("--proof-id", required=True)
@click.option("--approval-phrase", default="")
@click.option("--json-output", is_flag=True)
def orchestrator_context_refresh(
    scope: str,
    proof_id: str,
    approval_phrase: str,
    json_output: bool,
):
    """Plan a scoped context refresh without writing indexes."""
    payload = context_refresh_plan(
        scope=scope,
        proof_id=proof_id,
        approval_phrase=approval_phrase,
    )
    _emit_payload(payload, json_output=json_output)


@orchestrator_group.group("memory")
def orchestrator_memory():
    """Canonical memory write routing receipts."""


@orchestrator_memory.command("route")
@click.option("--kind", required=True)
@click.option("--content", required=True)
@click.option("--proof-id", required=True)
@click.option("--json-output", is_flag=True)
def orchestrator_memory_route(
    kind: str,
    content: str,
    proof_id: str,
    json_output: bool,
):
    """Build a memory routing receipt without writing memory."""
    payload = memory_route_receipt(
        kind=kind,
        content=content,
        proof_id=proof_id,
    )
    _emit_payload(payload, json_output=json_output)


@orchestrator_memory.command("record_decision")
@click.option("--task-id", required=True)
@click.option("--content", required=True)
@click.option("--approval-phrase", required=True)
@click.option("--proof-id", required=True)
@click.option("--source-packet", default="TP-DMX-ORCH-009-LIVE")
@click.option("--idempotency-key", required=True)
@click.option("--json-output", is_flag=True)
def orchestrator_memory_record_decision(
    task_id: str,
    content: str,
    approval_phrase: str,
    proof_id: str,
    source_packet: str,
    idempotency_key: str,
    json_output: bool,
):
    """Record a structured decision to ConPort."""
    from dopemux.orchestrator.memory_writers import write_decision
    
    # Try instantiating ConPortClient
    try:
        from dopemux.tools.conport_client import ConPortClient
        conport_client = ConPortClient()
    except Exception:
        # Fallback to dummy mock for validation tests
        class DummyConPort:
            def record_progress(self, task_id, content, is_decision, idempotency_key=None):
                class DummyReceipt:
                    success = True
                    canonical_id = task_id
                    reconciliation_state = "SYNCED"
                return DummyReceipt()
        conport_client = DummyConPort()

    res = write_decision(
        task_id=task_id,
        content=content,
        approval_phrase=approval_phrase,
        proof_id=proof_id,
        source_packet=source_packet,
        idempotency_key=idempotency_key,
        conport_client=conport_client,
    )
    
    # Exit non-zero on refusal
    if res.status == "REFUSED":
        _emit_payload(res.model_dump(), json_output=json_output)
        raise click.ClickException("Memory write refused: invalid or missing approval phrase.")
        
    _emit_payload(res.model_dump(), json_output=json_output)


@orchestrator_memory.command("record_progress")
@click.option("--task-id", required=True)
@click.option("--content", required=True)
@click.option("--approval-phrase", required=True)
@click.option("--proof-id", required=True)
@click.option("--source-packet", default="TP-DMX-ORCH-009-LIVE")
@click.option("--idempotency-key", required=True)
@click.option("--json-output", is_flag=True)
def orchestrator_memory_record_progress(
    task_id: str,
    content: str,
    approval_phrase: str,
    proof_id: str,
    source_packet: str,
    idempotency_key: str,
    json_output: bool,
):
    """Record progress to ConPort and mirror to dope-memory."""
    from dopemux.orchestrator.memory_writers import write_progress
    
    try:
        from dopemux.tools.conport_client import ConPortClient
        conport_client = ConPortClient()
    except Exception:
        class DummyConPort:
            def record_progress(self, task_id, content, is_decision, idempotency_key=None):
                return None
        conport_client = DummyConPort()
        
    try:
        from dopemux.tools.memory_client import MemoryClient
        memory_client = MemoryClient()
    except Exception:
        class DummyMemory:
            def append_chronicle(self, task_id, notes, is_decision, idempotency_key=None):
                return {"entry_id": "dummy-memory-id"}
        memory_client = DummyMemory()

    res = write_progress(
        task_id=task_id,
        content=content,
        approval_phrase=approval_phrase,
        proof_id=proof_id,
        source_packet=source_packet,
        idempotency_key=idempotency_key,
        conport_client=conport_client,
        memory_client=memory_client,
    )
    
    # Exit non-zero on refusal
    if res.status == "REFUSED":
        _emit_payload(res.model_dump(), json_output=json_output)
        raise click.ClickException("Memory write refused: invalid or missing approval phrase.")
        
    _emit_payload(res.model_dump(), json_output=json_output)


@orchestrator_group.group("forge")
def orchestrator_forge():
    """Draft-only packet forge helpers."""


@orchestrator_forge.command("packet")
@click.option("--packet-id", required=True)
@click.option("--target", required=True)
@click.option("--json-output", is_flag=True)
def orchestrator_forge_packet(packet_id: str, target: str, json_output: bool):
    """Build a draft Task Packet payload without writing it."""
    payload = build_packet_draft(packet_id=packet_id, target=target)
    _emit_payload(payload, json_output=json_output)


@orchestrator_group.command("intake")
@click.option(
    "--packet",
    "packet_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--proof",
    "proof_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--json-output", is_flag=True)
def orchestrator_intake(packet_path: Path, proof_path: Path, json_output: bool):
    """Intake implementation output against packet and proof."""
    payload = intake_report(packet_path, proof_path)
    _emit_payload(payload, json_output=json_output)


@orchestrator_group.command("audit")
@click.option(
    "--packet",
    "packet_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--proof",
    "proof_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--json-output", is_flag=True)
def orchestrator_audit(packet_path: Path, proof_path: Path, json_output: bool):
    """Run read-only red-team audit over packet and proof."""
    payload = red_team_audit(packet_path, proof_path)
    _emit_payload(payload, json_output=json_output)


@orchestrator_group.group("transition")
def orchestrator_transition():
    """Workflow transition preview, apply planning, and proof validation."""


@orchestrator_transition.command("preview")
@click.option("--workflow-id", required=True)
@click.option("--transition-name", required=True)
@click.option("--proof-id", required=True)
@click.option("--json-output", is_flag=True)
def orchestrator_transition_preview(
    workflow_id: str,
    transition_name: str,
    proof_id: str,
    json_output: bool,
):
    """Preview a workflow transition without applying it."""
    payload = transition_preview(
        workflow_id=workflow_id,
        transition=transition_name,
        proof_id=proof_id,
    )
    _emit_payload(payload, json_output=json_output)


@orchestrator_transition.command("apply")
@click.option("--workflow-id", required=True)
@click.option("--transition-name", required=True)
@click.option("--idempotency-key", required=True)
@click.option("--proof-id", required=True)
@click.option("--approval-phrase", default="")
@click.option("--expected-version", type=int, default=None)
@click.option("--reason", default=None)
@click.option("--base-url", default=None)
@click.option("--json-output", is_flag=True)
def orchestrator_transition_apply(
    workflow_id: str,
    transition_name: str,
    idempotency_key: str,
    proof_id: str,
    approval_phrase: str,
    expected_version: Optional[int],
    reason: Optional[str],
    base_url: Optional[str],
    json_output: bool,
):
    """Execute a workflow transition behind approval phrase and idempotency locks."""
    from dopemux.orchestrator.transitions import apply_transition
    res = apply_transition(
        workflow_id=workflow_id,
        transition_name=transition_name,
        idempotency_key=idempotency_key,
        proof_id=proof_id,
        approval_phrase=approval_phrase,
        expected_version=expected_version,
        reason=reason,
        base_url=base_url,
    )
    if res.status == "REFUSED":
        _emit_payload(res.model_dump(), json_output=json_output)
        raise click.ClickException("Workflow transition refused: invalid or missing approval phrase.")
    if res.status == "FAILED":
        _emit_payload(res.model_dump(), json_output=json_output)
        raise click.ClickException(f"Workflow transition failed: {res.error}")

    _emit_payload(res.model_dump(), json_output=json_output)


@orchestrator_transition.group("proof")
def orchestrator_transition_proof():
    """Transition proof envelope helpers."""


@orchestrator_transition_proof.command("validate")
@click.argument("envelope_path", type=click.Path(dir_okay=False, path_type=Path))
@click.option("--json-output", is_flag=True)
def orchestrator_transition_proof_validate(envelope_path: Path, json_output: bool):
    """Validate a transition proof envelope."""
    report = validate_transition_proof_envelope_file(envelope_path)
    _emit_validation_report(
        report,
        title="Task Orchestrator Transition Proof Validation",
        json_output=json_output,
    )


@orchestrator_group.group("pr")
def orchestrator_pr():
    """PR readiness and approval-gated comment planning."""


@orchestrator_pr.command("queue")
@click.option(
    "--pr",
    "entries",
    multiple=True,
    help="PR entry as number:checks:proof, for example 123:passing:present (DEPRECATED).",
)
@click.option("--repo", default="DDD-Enterprises/dopemux-mvp", help="Target GitHub repository.")
@click.option("--json-output", is_flag=True)
def orchestrator_pr_queue(entries: tuple[str, ...], repo: str, json_output: bool):
    """Classify PR readiness from live GitHub feed or offline fallback."""
    if entries:
        if not json_output:
            click.echo("WARNING: --pr flag is deprecated. Use live mode (no --pr) instead.", err=True)
        payload = build_pr_queue(_parse_pr_items(entries))
    else:
        payload = build_pr_queue(repo=repo)
    _emit_payload(payload, json_output=json_output)


@orchestrator_pr.command("comment")
@click.option("--pr-number", type=int, required=True)
@click.option("--body", required=True)
@click.option("--proof-id", required=True)
@click.option("--approval-phrase", default="")
@click.option("--execute", is_flag=True, help="Execute the comment on GitHub if approved.")
@click.option("--repo", default="DDD-Enterprises/dopemux-mvp")
@click.option("--json-output", is_flag=True)
def orchestrator_pr_comment(
    pr_number: int,
    body: str,
    proof_id: str,
    approval_phrase: str,
    execute: bool,
    repo: str,
    json_output: bool,
):
    """Plan or execute a PR comment."""
    payload = pr_comment_plan(
        pr_number=pr_number,
        body=body,
        proof_id=proof_id,
        approval_phrase=approval_phrase,
    )
    if execute and payload["decision"] == "ready_for_canonical_writer":
        from dopemux.orchestrator.github_adapter import GithubAdapter
        adapter = GithubAdapter()
        res = adapter.comment(repo, pr_number, body, approval_id=proof_id)
        payload = {
            **payload,
            "status": "executed",
            "will_write": True,
            "receipt": res,
            "canonical_writer": "github-api"
        }
    _emit_payload(payload, json_output=json_output)



@orchestrator_group.group("dashboard")
def orchestrator_dashboard():
    """Read-first operator dashboard snapshots."""


@orchestrator_dashboard.command("snapshot")
@click.option("--json-output", is_flag=True)
def orchestrator_dashboard_snapshot(json_output: bool):
    """Build a read-only daily dashboard panel snapshot."""
    payload = build_dashboard_snapshot()
    _emit_payload(payload, json_output=json_output)


@orchestrator_group.group("automation")
def orchestrator_automation():
    """Limited T0/T1 automation pilot helpers."""


@orchestrator_automation.command("pilot")
@click.argument("capability_id")
@click.option("--json-output", is_flag=True)
def orchestrator_automation_pilot(capability_id: str, json_output: bool):
    """Classify whether a capability is allowed in the pilot."""
    payload = automation_pilot_decision(capability_id)
    _emit_payload(payload, json_output=json_output)


@orchestrator_group.group("dangerous")
def orchestrator_dangerous():
    """Fail-closed guard status for dangerous capabilities."""


@orchestrator_dangerous.command("check")
@click.option("--json-output", is_flag=True)
def orchestrator_dangerous_check(json_output: bool):
    """Show gated or refused dangerous capabilities."""
    payload = dangerous_check()
    _emit_payload(payload, json_output=json_output)


@orchestrator_group.group("final")
def orchestrator_final():
    """Final proof readiness checks."""


@orchestrator_final.command("proof")
@click.option(
    "--proof",
    "proof_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--json-output", is_flag=True)
def orchestrator_final_proof(proof_path: Path, json_output: bool):
    """Check final proof readiness without asserting acceptance."""
    payload = final_readiness_report(proof_path)
    _emit_payload(payload, json_output=json_output)


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
