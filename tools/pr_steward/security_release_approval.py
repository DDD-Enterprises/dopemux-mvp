"""Exact-head-bound security/release approval contract validator.

Mirrors the (repo, PR, head_sha) binding pattern already established by
``scripts.audit.run_embedded_audit.independent_audit_errors`` — the shared
validator used by both the embedded-audit workflow hard gate and the PR
Steward collector's proof check. This module applies the same binding
discipline to a *reviewer approval* rather than an audit proof.

Approval never overrides another blocker; callers add these errors as
additional ``SECURITY_RELEASE_APPROVAL_*`` blockers alongside all existing
ones.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

_TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}


def evaluate_security_release_approval(
    approval: Mapping[str, Any] | None,
    *,
    required: bool,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    trusted_approvers: list[str],
) -> list[str]:
    """Return fail-closed blocker codes for a security/release approval claim.

    Returns an empty list only when *required* is falsy, or *approval* is a
    well-formed, current, exact-head-bound APPROVED review from a login in
    *trusted_approvers*.
    """
    if not bool(required):
        return []

    if approval is None:
        return ["SECURITY_RELEASE_APPROVAL_REQUIRED"]

    if not isinstance(approval, Mapping):
        return ["SECURITY_RELEASE_APPROVAL_INVALID"]

    errors: list[str] = []

    state = approval.get("state")
    if state != "APPROVED":
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")

    approval_ref = approval.get("approval_ref")
    if not isinstance(approval_ref, str) or not approval_ref:
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")

    repository = approval.get("repository")
    pr_number = approval.get("pr_number")
    if repository != expected_repo or pr_number != expected_pr:
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")

    head_sha = approval.get("head_sha")
    if isinstance(head_sha, str) and repository == expected_repo and pr_number == expected_pr:
        if head_sha != expected_head_sha:
            errors.append("SECURITY_RELEASE_APPROVAL_HEAD_MISMATCH")
    elif not isinstance(head_sha, str):
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")

    approved_at = approval.get("approved_at")
    parsed_at = _parse_rfc3339(approved_at)
    if parsed_at is None:
        errors.append("SECURITY_RELEASE_APPROVAL_INVALID")
    elif parsed_at > datetime.now(timezone.utc):
        errors.append("SECURITY_RELEASE_APPROVAL_STALE")

    approver = approval.get("approver")
    if not trusted_approvers or approver not in trusted_approvers:
        errors.append("SECURITY_RELEASE_APPROVER_UNKNOWN")

    approver_association = approval.get("approver_association")
    if str(approver_association or "").upper() not in _TRUSTED_ASSOCIATIONS:
        errors.append("SECURITY_RELEASE_APPROVER_UNKNOWN")

    # De-duplicate while preserving first-seen order.
    seen: set[str] = set()
    ordered: list[str] = []
    for err in errors:
        if err not in seen:
            seen.add(err)
            ordered.append(err)
    return ordered


def _parse_rfc3339(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed
