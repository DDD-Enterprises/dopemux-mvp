"""Exact-head-bound security/release approval contract validator.

Mirrors the (repo, PR, head_sha) binding pattern already established by
``scripts.audit.run_embedded_audit.independent_audit_errors`` — the shared
validator used by both the embedded-audit workflow hard gate and the PR
Steward collector's proof check. This module applies the same binding
discipline to a *reviewer approval* rather than an audit proof.

Two approval authorities are recognized (ADR / SOLO_MAINTAINER_ORG_APP_APPROVAL):

1. **Human non-author path** — exact-head GitHub ``APPROVED`` review from a
   login in ``trusted_security_release_approvers`` with association
   OWNER/MEMBER/COLLABORATOR.

2. **Organization-owned GitHub App path** — exact-head ``APPROVED`` review from
   a login listed in ``trusted_security_release_apps``, with association
   suitable for apps (typically ``NONE``), never generic ``github-actions[bot]``,
   and only when non-security readiness gates are already green.

Approval never overrides another blocker; callers add these errors as
additional ``SECURITY_RELEASE_APPROVAL_*`` blockers alongside all existing
ones. The solo-owner phrase override remains a separate module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

_TRUSTED_HUMAN_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
# GitHub App PR reviews commonly report authorAssociation NONE.
_TRUSTED_APP_ASSOCIATIONS = {"NONE"}
_FORBIDDEN_APP_LOGINS = frozenset(
    {
        "github-actions[bot]",
        "github-actions",
        "dependabot[bot]",
        "dependabot",
    }
)


def evaluate_security_release_approval(
    approval: Mapping[str, Any] | None,
    *,
    required: bool,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    trusted_approvers: list[str],
    trusted_apps: Sequence[Mapping[str, Any]] | None = None,
    app_gate_ok: bool | None = None,
) -> list[str]:
    """Return fail-closed blocker codes for a security/release approval claim.

    Returns an empty list only when *required* is falsy, or *approval* is a
    well-formed, current, exact-head-bound APPROVED review from either:

    - a trusted human login (OWNER/MEMBER/COLLABORATOR), or
    - a trusted organization-owned GitHub App login with app-gate preconditions.
    """
    if not bool(required):
        return []

    if approval is None:
        return ["SECURITY_RELEASE_APPROVAL_REQUIRED"]

    if not isinstance(approval, Mapping):
        return ["SECURITY_RELEASE_APPROVAL_INVALID"]

    apps = list(trusted_apps or [])
    approver = str(approval.get("approver") or "")
    assoc = str(approval.get("approver_association") or "").upper()
    # Route bot/app-shaped approvals (login ends with [bot] or association NONE
    # when apps are configured) through the app evaluator so unknowns surface as
    # APP_* codes rather than human APPROVER_UNKNOWN.
    looks_like_app = approver.lower().endswith("[bot]") or (
        bool(apps) and assoc == "NONE" and approver not in (trusted_approvers or [])
    )
    if looks_like_app or _match_trusted_app(approver, apps, expected_repo=expected_repo):
        return _evaluate_app_approval(
            approval,
            expected_repo=expected_repo,
            expected_pr=expected_pr,
            expected_head_sha=expected_head_sha,
            trusted_apps=apps,
            app_gate_ok=app_gate_ok,
        )
    return _evaluate_human_approval(
        approval,
        expected_repo=expected_repo,
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
        trusted_approvers=trusted_approvers,
    )


def _evaluate_human_approval(
    approval: Mapping[str, Any],
    *,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    trusted_approvers: list[str],
) -> list[str]:
    errors: list[str] = []
    _append_common_shape_errors(
        approval,
        errors=errors,
        expected_repo=expected_repo,
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
    )

    approver = approval.get("approver")
    if not trusted_approvers or approver not in trusted_approvers:
        errors.append("SECURITY_RELEASE_APPROVER_UNKNOWN")

    approver_association = approval.get("approver_association")
    if str(approver_association or "").upper() not in _TRUSTED_HUMAN_ASSOCIATIONS:
        errors.append("SECURITY_RELEASE_APPROVER_UNKNOWN")

    return _dedupe(errors)


def _evaluate_app_approval(
    approval: Mapping[str, Any],
    *,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    trusted_apps: Sequence[Mapping[str, Any]],
    app_gate_ok: bool | None,
) -> list[str]:
    errors: list[str] = []
    _append_common_shape_errors(
        approval,
        errors=errors,
        expected_repo=expected_repo,
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
    )

    approver = str(approval.get("approver") or "")
    if _normalize_login(approver) in _FORBIDDEN_APP_LOGINS:
        errors.append("SECURITY_RELEASE_APP_FORBIDDEN")

    matched = _match_trusted_app(approver, trusted_apps, expected_repo=expected_repo)
    if matched is None:
        errors.append("SECURITY_RELEASE_APP_UNKNOWN")

    assoc = str(approval.get("approver_association") or "").upper()
    if assoc not in _TRUSTED_APP_ASSOCIATIONS:
        # Some installations may report MEMBER; still reject OWNER-style human
        # associations for apps to avoid human impersonation confusion.
        if assoc in _TRUSTED_HUMAN_ASSOCIATIONS:
            errors.append("SECURITY_RELEASE_APP_ASSOCIATION_INVALID")
        else:
            errors.append("SECURITY_RELEASE_APP_ASSOCIATION_INVALID")

    # App approvals only count when non-security gates are already satisfied.
    # app_gate_ok=None means "identity-only unit tests" / gate not yet evaluated.
    if app_gate_ok is False:
        errors.append("SECURITY_RELEASE_APP_GATES_NOT_MET")

    if matched is not None:
        # Surface installation_scope mismatch if configured.
        scope = str(matched.get("installation_scope") or "").strip()
        if scope and not _scope_covers_repo(scope, expected_repo):
            errors.append("SECURITY_RELEASE_APP_SCOPE_MISMATCH")
        owner = str(matched.get("owner") or "").strip()
        if owner and "/" in expected_repo:
            repo_owner = expected_repo.split("/", 1)[0]
            if owner != repo_owner:
                errors.append("SECURITY_RELEASE_APP_OWNER_MISMATCH")

    return _dedupe(errors)


def _append_common_shape_errors(
    approval: Mapping[str, Any],
    *,
    errors: list[str],
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
) -> None:
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


def load_trusted_security_apps(path_payload: Mapping[str, Any] | list[Any]) -> list[dict[str, str]]:
    """Normalize ``trusted_security_release_apps`` config entries."""
    if isinstance(path_payload, Mapping):
        raw = path_payload.get("trusted_security_release_apps") or []
    else:
        raw = path_payload
    if not isinstance(raw, list):
        return []
    apps: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        login = str(item.get("login") or "").strip()
        if not login:
            continue
        apps.append(
            {
                "login": login,
                "owner": str(item.get("owner") or "").strip(),
                "installation_scope": str(item.get("installation_scope") or "").strip(),
            }
        )
    return apps


def compute_app_gate_ok(
    *,
    audit_status: str,
    proof_status: str,
    blockers: Sequence[str],
    unclassified_review_item_count: int,
) -> bool:
    """True when non-security gates allow an org-app approval to count."""
    audit = str(audit_status or "").upper()
    if audit not in {"PASS", "PASS_WITH_RISKS"}:
        return False
    proof = str(proof_status or "").upper()
    if proof not in {"CURRENT", "CURRENT_WITH_SELF_REFERENCE_EXCEPTION", "FRESH"}:
        return False
    if unclassified_review_item_count:
        return False
    forbidden = {
        "FAILED_CHECK",
        "PENDING_CHECK",
        "UNRESOLVED_REVIEW_THREAD",
        "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION",
        "HARVEST_INCOMPLETE",
        "PR_IS_DRAFT",
        "PR_CLOSED",
        "MIXED_SHA_ARTIFACT_SET",
        "PROOF_STALE",
        "PROOF_MISSING",
        "PROOF_STALE_OR_MISSING",
        "REQUEST_CHANGES",
        "REVIEW_ITEM_MUST_FIX",
        "REVIEW_ITEM_NEEDS_SUPERVISOR",
    }
    for b in blockers:
        text = str(b)
        if text.startswith("SECURITY_RELEASE_"):
            continue
        if text.startswith("EMBEDDED_AUDIT_"):
            return False
        if text in forbidden or text.startswith("UNKNOWN_"):
            return False
    return True


def _match_trusted_app(
    login: str,
    trusted_apps: Sequence[Mapping[str, Any]],
    *,
    expected_repo: str,
) -> Mapping[str, Any] | None:
    want = _normalize_login(login)
    if not want:
        return None
    for app in trusted_apps:
        app_login = _normalize_login(str(app.get("login") or ""))
        if not app_login:
            continue
        if want == app_login or want == app_login.removesuffix("[bot]") + "[bot]":
            scope = str(app.get("installation_scope") or "").strip()
            if scope and not _scope_covers_repo(scope, expected_repo):
                continue
            return app
        # Allow config without [bot] suffix to match GitHub's bot login.
        if want.removesuffix("[bot]") == app_login.removesuffix("[bot]"):
            scope = str(app.get("installation_scope") or "").strip()
            if scope and not _scope_covers_repo(scope, expected_repo):
                continue
            return app
    return None


def _scope_covers_repo(scope: str, expected_repo: str) -> bool:
    if scope == expected_repo:
        return True
    # Org-wide install recorded as org login only.
    if "/" not in scope and "/" in expected_repo:
        return scope == expected_repo.split("/", 1)[0]
    return False


def _normalize_login(login: str) -> str:
    return str(login or "").strip().lower()


def _dedupe(errors: list[str]) -> list[str]:
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
