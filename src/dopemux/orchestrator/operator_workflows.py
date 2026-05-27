"""Fail-closed operator workflow helpers for orchestrator integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

from dopemux.orchestrator.policy import classify_capability
from dopemux.orchestrator.validation.packets import validate_packet_file
from dopemux.orchestrator.validation.proof import validate_proof_file
from dopemux.orchestrator.validation.report import (
    ValidationIssue,
    ValidationReport,
    issue,
    path_text,
    sort_issues,
)
from dopemux.orchestrator.validation.json_io import load_json_object


AUTHORITY = "docs/03-reference/systems/task-orchestrator/operator-integration-authority.md"
DASHBOARD_PANELS = [
    "today",
    "authority",
    "packets",
    "proof",
    "risks",
    "pr_queue",
    "context",
    "do_not_touch",
]
DEFAULT_CONTEXT_SOURCES = ("dope-context", "ConPort", "dope-memory")
TRANSITION_PROOF_AUTHORITY = "task-orchestrator-transition-proof-envelope"
SUPPORTED_TRANSITION_PROOF_SCHEMA_VERSION = "1"


def approve_phrase(
    *,
    operation: str,
    resource: str,
    writer: str,
    proof_id: str,
) -> str:
    """Return the exact typed approval phrase required by authority docs."""
    return (
        f"I AUTHORIZE {operation} ON {resource} "
        f"USING {writer} WITH PROOF {proof_id}"
    )


def context_status(
    *,
    changed_files: Sequence[str] | None = None,
    stale_sources: Sequence[str] | None = None,
) -> Dict[str, Any]:
    stale = set(stale_sources or [])
    changed = list(changed_files or [])
    sources = {
        source: {
            "fresh": source not in stale,
            "authority_role": _context_source_role(source),
        }
        for source in DEFAULT_CONTEXT_SOURCES
    }
    status = "STALE" if stale or changed else "FRESH"
    return {
        "kind": "context_status",
        "authority": AUTHORITY,
        "read_only": True,
        "will_write": False,
        "tier": "T0/T1",
        "status": status,
        "changed_file_count": len(changed),
        "changed_files": changed,
        "sources": sources,
    }


def context_refresh_plan(
    *,
    scope: str,
    proof_id: str,
    approval_phrase: str = "",
    resource: str = "dopemux-mvp",
) -> Dict[str, Any]:
    operation = f"context refresh {scope}"
    required = approve_phrase(
        operation=operation,
        resource=resource,
        writer="dope-context",
        proof_id=proof_id,
    )
    approved = bool(approval_phrase) and approval_phrase == required
    return {
        "kind": "context_refresh_plan",
        "authority": AUTHORITY,
        "scope": scope,
        "tier": "T4",
        "canonical_writer": "dope-context",
        "decision": "ready_for_canonical_writer" if approved else "blocked",
        "approval_required": True,
        "receipt_required": True,
        "required_phrase": required,
        "approval_matched": approved,
        "will_write": False,
        "write_boundary": "external_canonical_writer_required",
    }


def memory_route_receipt(
    *,
    kind: str,
    content: str,
    proof_id: str,
) -> Dict[str, Any]:
    normalized = kind.strip().lower()
    mirror_writer = "dope-memory" if normalized == "progress" else ""
    return {
        "kind": "memory_route_receipt",
        "record_kind": normalized,
        "content_preview": content[:120],
        "proof_id": proof_id,
        "tier": "T4",
        "canonical_writer": "ConPort",
        "mirror_writer": mirror_writer,
        "task_orchestrator_role": "observe_route_only",
        "decision": "route_only",
        "approval_required": True,
        "receipt_required": True,
        "will_write": False,
    }


def build_packet_draft(*, packet_id: str, target: str) -> Dict[str, Any]:
    packet = {
        "id": packet_id,
        "project": "dopemux-mvp",
        "target": target,
        "repo_binding": {
            "project_id": "DDD-Enterprises/dopemux-mvp",
            "repo_marker": ".dopetaskroot",
            "require_identity_match": True,
        },
        "series": {
            "id": "DMX-ORCH-INTEGRATION",
            "base_branch": "main",
            "parent_tp_id": "UNKNOWN_UNTIL_REVIEW",
            "final_packet": False,
        },
        "commit": {
            "message": "UNKNOWN_UNTIL_REVIEW",
            "allowlist": ["UNKNOWN_UNTIL_REVIEW"],
        },
        "pr": {
            "title": target,
            "body": "Draft-only packet. Review authority before use.",
            "base": "main",
        },
        "steps": [
            {
                "id": "inspect",
                "task": "Inspect authority before implementation.",
                "validation": ["Authority and allowlist are reviewed."],
            }
        ],
    }
    return {
        "kind": "packet_forge_draft",
        "status": "DRAFT_ONLY",
        "tier": "T2",
        "will_write": False,
        "packet": packet,
    }


def intake_report(packet_path: str | Path, proof_path: str | Path) -> Dict[str, Any]:
    packet_report = validate_packet_file(packet_path)
    proof_report = validate_proof_file(proof_path)
    verdict = "PASS" if packet_report.valid and proof_report.valid else "FAIL"
    return {
        "kind": "implementation_intake",
        "authority": AUTHORITY,
        "tier": "T1",
        "verdict": verdict,
        "will_accept": False,
        "will_write": False,
        "packet": packet_report.to_dict(),
        "proof": proof_report.to_dict(),
    }


def red_team_audit(packet_path: str | Path, proof_path: str | Path) -> Dict[str, Any]:
    report = intake_report(packet_path, proof_path)
    findings: list[Dict[str, str]] = []
    if report["verdict"] != "PASS":
        findings.append(
            {
                "severity": "blocker",
                "code": "PACKET_OR_PROOF_INVALID",
                "message": "Packet or proof validation failed.",
            }
        )
    return {
        "kind": "red_team_audit",
        "authority": AUTHORITY,
        "tier": "T1",
        "verdict": "PASS" if not findings else "FAIL",
        "will_write": False,
        "findings": findings,
        "intake": report,
    }


def transition_preview(
    *,
    workflow_id: str,
    transition: str,
    proof_id: str,
) -> Dict[str, Any]:
    return {
        "kind": "workflow_transition_preview",
        "authority": AUTHORITY,
        "workflow_id": workflow_id,
        "transition": transition,
        "proof_id": proof_id,
        "tier": "T1",
        "canonical_writer": "task-orchestrator",
        "read_only": True,
        "will_write": False,
        "apply_requires": [
            "idempotency_key",
            "exact_typed_approval",
            "canonical_writer_receipt",
        ],
    }


def transition_apply_plan(
    *,
    workflow_id: str,
    transition: str,
    idempotency_key: str,
    proof_id: str,
    approval_phrase: str = "",
    resource: str = "dopemux-mvp",
) -> Dict[str, Any]:
    operation = f"workflow transition {transition}"
    required = approve_phrase(
        operation=operation,
        resource=resource,
        writer="task-orchestrator",
        proof_id=proof_id,
    )
    errors = []
    if not idempotency_key:
        errors.append("idempotency_key_required")
    if not proof_id:
        errors.append("proof_id_required")
    approved = bool(approval_phrase) and approval_phrase == required and not errors
    return {
        "kind": "workflow_transition_apply_plan",
        "authority": AUTHORITY,
        "workflow_id": workflow_id,
        "transition": transition,
        "idempotency_key": idempotency_key,
        "proof_id": proof_id,
        "tier": "T4",
        "canonical_writer": "task-orchestrator",
        "decision": "ready_for_canonical_writer" if approved else "blocked",
        "approval_required": True,
        "receipt_required": True,
        "required_phrase": required,
        "approval_matched": approved,
        "will_write": False,
        "write_boundary": "external_canonical_writer_required",
        "errors": errors,
    }


def validate_transition_proof_envelope_file(
    envelope_path: str | Path,
) -> ValidationReport:
    path = Path(envelope_path)
    payload, load_errors = load_json_object(path)
    errors: list[ValidationIssue] = [*load_errors]
    if payload is not None:
        errors.extend(_validate_transition_proof_envelope(payload))
    sorted_errors = sort_issues(errors)
    status = "PASS" if not sorted_errors else "FAIL"
    return ValidationReport(
        kind="transition_proof_envelope",
        path=path_text(path),
        authority=TRANSITION_PROOF_AUTHORITY,
        status=status,
        valid=status == "PASS",
        errors=sorted_errors,
        details={
            "authority_boundary": "read_only_transition_proof_validation_only",
            "canonical_writer": "task-orchestrator",
        },
        exit_code=0 if status == "PASS" else 4,
    )


def build_pr_queue(items: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    rows = []
    for item in items:
        checks = str(item.get("checks") or "unknown")
        proof = str(item.get("proof") or "missing")
        if checks == "passing" and proof == "present":
            readiness = "merge_candidate"
        elif checks == "failing" or proof != "present":
            readiness = "blocked"
        else:
            readiness = "needs_review"
        rows.append(
            {
                "number": int(item.get("number", 0)),
                "checks": checks,
                "proof": proof,
                "readiness": readiness,
            }
        )
    return {
        "kind": "pr_queue",
        "authority": AUTHORITY,
        "tier": "T1",
        "read_only": True,
        "will_write": False,
        "items": rows,
    }


def pr_comment_plan(
    *,
    pr_number: int,
    body: str,
    proof_id: str,
    approval_phrase: str = "",
    resource: str = "dopemux-mvp",
) -> Dict[str, Any]:
    operation = f"github pr comment {pr_number}"
    required = approve_phrase(
        operation=operation,
        resource=resource,
        writer="GitHub",
        proof_id=proof_id,
    )
    approved = bool(approval_phrase) and approval_phrase == required
    return {
        "kind": "pr_comment_plan",
        "authority": AUTHORITY,
        "pr_number": pr_number,
        "body_preview": body[:120],
        "proof_id": proof_id,
        "tier": "T5",
        "canonical_writer": "GitHub",
        "decision": "ready_for_canonical_writer" if approved else "blocked",
        "approval_required": True,
        "receipt_required": True,
        "required_phrase": required,
        "approval_matched": approved,
        "will_write": False,
        "write_boundary": "external_canonical_writer_required",
    }


def build_dashboard_snapshot() -> Dict[str, Any]:
    panels = [
        {
            "id": panel_id,
            "tier": "T1" if panel_id in {"packets", "proof", "pr_queue"} else "T0",
            "read_only": True,
        }
        for panel_id in DASHBOARD_PANELS
    ]
    return {
        "kind": "dashboard_snapshot",
        "authority": AUTHORITY,
        "read_only": True,
        "will_write": False,
        "panels": panels,
    }


def automation_pilot_decision(capability_id: str) -> Dict[str, Any]:
    decision = classify_capability(capability_id)
    return {
        "kind": "automation_pilot_decision",
        "authority": AUTHORITY,
        "capability_id": capability_id,
        "tier": decision.tier,
        "policy_decision": decision.decision,
        "decision": "allow" if decision.allowed else "blocked",
        "automatic_allowed": decision.automatic_allowed,
        "approval_required": decision.approval_required,
        "receipt_required": decision.receipt_required,
        "will_write": False,
        "reason": decision.reason,
    }


def dangerous_check() -> Dict[str, Any]:
    refused = [
        classify_capability("orchestrator.route.pm").to_dict(),
        classify_capability("orchestrator.destructive.clear_index").to_dict(),
    ]
    return {
        "kind": "dangerous_check",
        "authority": AUTHORITY,
        "tier": "T1",
        "read_only": True,
        "will_write": False,
        "refused_or_gated_capabilities": refused,
    }


def final_readiness_report(proof_path: str | Path) -> Dict[str, Any]:
    proof = validate_proof_file(proof_path)
    return {
        "kind": "final_readiness_report",
        "authority": AUTHORITY,
        "proof": {
            "path": proof.path,
            "status": proof.status,
            "valid": proof.valid,
        },
        "acceptance": {
            "status": "UNKNOWN",
            "reason": "Acceptance authority is external to this local proof check.",
        },
        "ready_for_merge": False,
        "will_write": False,
    }


def _context_source_role(source: str) -> str:
    if source == "dope-context":
        return "retrieval_index"
    if source == "ConPort":
        return "decision_progress_context"
    if source == "dope-memory":
        return "chronicle_recap"
    return "unknown"


def _validate_transition_proof_envelope(
    payload: Mapping[str, Any],
) -> list[ValidationIssue]:
    errors: list[ValidationIssue] = []
    required_strings = [
        "schema_version",
        "workflow_id",
        "transition",
        "idempotency_key",
        "actor",
        "canonical_writer",
    ]
    for key in required_strings:
        if not _non_empty_string(payload.get(key)):
            errors.append(
                issue(
                    f"TRANSITION_PROOF_{key.upper()}_MISSING",
                    f"Transition proof envelope must include {key}.",
                    path=f"/{key}",
                )
            )
    schema_version = payload.get("schema_version")
    if (
        _non_empty_string(schema_version)
        and schema_version not in {"1", "1.0"}
    ):
        errors.append(
            issue(
                "TRANSITION_PROOF_SCHEMA_VERSION_UNSUPPORTED",
                (
                    f"Transition proof schema_version must be "
                    f"one of {{'1', '1.0'}}; "
                    f"got {schema_version!r}."
                ),
                path="/schema_version",
            )
        )
    if payload.get("canonical_writer") not in {None, "task-orchestrator"}:
        errors.append(
            issue(
                "TRANSITION_PROOF_CANONICAL_WRITER_INVALID",
                "Transition proof canonical_writer must be task-orchestrator.",
                path="/canonical_writer",
            )
        )
    receipt = payload.get("receipt")
    if not isinstance(receipt, Mapping):
        errors.append(
            issue(
                "TRANSITION_PROOF_RECEIPT_MISSING",
                "Transition proof envelope must include a receipt object.",
                path="/receipt",
            )
        )
        return errors
    for key in ("proof_id", "operation", "status"):
        if not _non_empty_string(receipt.get(key)):
            errors.append(
                issue(
                    f"TRANSITION_PROOF_RECEIPT_{key.upper()}_MISSING",
                    f"Transition proof receipt must include {key}.",
                    path=f"/receipt/{key}",
                )
            )
    return errors


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
