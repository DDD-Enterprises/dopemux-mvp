from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


PASSING_AUDIT_STATUSES = {"PASS", "PASS_WITH_RISKS"}
READINESS_BY_CLASS = {
    "REMEDIATION": {"NEEDS_IMPLEMENTER"},
    "FINALIZATION": {"READY"},
}


@dataclass(frozen=True)
class StewardGateResult:
    allowed: bool
    reason_code: str
    required_class: str
    evidence: Mapping[str, Any]


def steward_gate(
    *,
    head_sha: str,
    required_class: str,
    merge_readiness_path: str | Path,
    audit_proof_path: str | Path,
    now: datetime | None = None,
    ttl_seconds: int = 3600,
) -> StewardGateResult:
    """Pure fail-closed guard over local PR Steward and embedded-audit artifacts."""

    normalized_class = required_class.upper()
    if normalized_class not in READINESS_BY_CLASS:
        return _deny(normalized_class, "DENY_UNSUPPORTED_CLASS")
    if not head_sha:
        return _deny(normalized_class, "DENY_MISSING_HEAD_SHA")

    try:
        readiness = _load_json(Path(merge_readiness_path))
        audit_proof = _load_json(Path(audit_proof_path))
    except (OSError, ValueError, TypeError) as exc:
        return _deny(
            normalized_class,
            "DENY_ARTIFACT_UNREADABLE",
            error=type(exc).__name__,
        )

    evidence = _evidence(readiness, audit_proof)
    sha_values = {
        "requested_head_sha": head_sha,
        "merge_readiness_pr_head_sha": evidence["merge_pr_head_sha"],
        "merge_readiness_proof_head_sha": evidence["merge_proof_head_sha"],
        "audit_proof_head_sha": evidence["audit_proof_head_sha"],
    }
    if any(not value for value in sha_values.values()) or len(set(sha_values.values())) != 1:
        return _deny(normalized_class, "DENY_SHA_MISMATCH", **evidence, sha_values=sha_values)

    if evidence["merge_readiness"] not in READINESS_BY_CLASS[normalized_class]:
        return _deny(normalized_class, "DENY_READINESS_CLASS_MISMATCH", **evidence)

    if (
        evidence["merge_embedded_audit_status"] not in PASSING_AUDIT_STATUSES
        or evidence["proof_embedded_audit_status"] not in PASSING_AUDIT_STATUSES
    ):
        return _deny(normalized_class, "DENY_AUDIT_NOT_PASSING", **evidence)

    if _is_stale(evidence["merge_generated_at"], now=now, ttl_seconds=ttl_seconds) or _is_stale(
        evidence["proof_generated_at"], now=now, ttl_seconds=ttl_seconds
    ):
        return _deny(normalized_class, "DENY_STALE_ARTIFACT", **evidence)

    return StewardGateResult(
        allowed=True,
        reason_code=f"ALLOW_{normalized_class}",
        required_class=normalized_class,
        evidence=evidence,
    )


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _evidence(readiness: Mapping[str, Any], audit_proof: Mapping[str, Any]) -> dict[str, Any]:
    pr = _mapping(readiness.get("pr"))
    readiness_proof = _mapping(readiness.get("proof"))
    readiness_audit = _mapping(readiness.get("embedded_audit"))
    proof_audit = _mapping(audit_proof.get("embedded_audit"))
    return {
        "merge_readiness": str(readiness.get("readiness") or ""),
        "merge_generated_at": str(readiness.get("generated_at") or ""),
        "proof_generated_at": str(audit_proof.get("generated_at") or ""),
        "merge_pr_head_sha": str(pr.get("head_sha") or ""),
        "merge_proof_head_sha": str(readiness_proof.get("proof_head_sha") or ""),
        "audit_proof_head_sha": str(audit_proof.get("head_sha") or ""),
        "merge_embedded_audit_status": str(readiness_audit.get("status") or "").upper(),
        "proof_embedded_audit_status": str(proof_audit.get("status") or "").upper(),
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _deny(required_class: str, reason_code: str, **evidence: Any) -> StewardGateResult:
    return StewardGateResult(
        allowed=False,
        reason_code=reason_code,
        required_class=required_class,
        evidence=evidence,
    )


def _is_stale(value: str, *, now: datetime | None, ttl_seconds: int) -> bool:
    if ttl_seconds <= 0 or not value:
        return True
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    try:
        generated_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    age = reference.astimezone(timezone.utc) - generated_at.astimezone(timezone.utc)
    return age.total_seconds() < 0 or age.total_seconds() > ttl_seconds
