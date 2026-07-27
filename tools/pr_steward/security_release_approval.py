"""Exact-head-bound security/release approval contract validator.

Mirrors the (repo, PR, head_sha) binding pattern already established by
``scripts.audit.run_embedded_audit.independent_audit_errors`` — the shared
validator used by both the embedded-audit workflow hard gate and the PR
Steward collector's proof check. This module applies the same binding
discipline to a *reviewer approval* rather than an audit proof.

Two accepted channels (SOLO_MAINTAINER_ORG_APP_APPROVAL):

1. **Human** — exact-head APPROVED review from a login in
   ``trusted_security_release_approvers`` with association OWNER/MEMBER/
   COLLABORATOR. The PR author cannot satisfy their own gate.
2. **GitHub App** — exact-head APPROVED review from a login registered in
   ``trusted_security_release_apps`` for the expected repository, owned by
   the configured org. Generic ``github-actions[bot]`` is never accepted.

Approval never overrides another blocker; callers add these errors as
additional ``SECURITY_RELEASE_APPROVAL_*`` blockers alongside all existing
ones. Broader gates (independent audit, CI, proof freshness, threads)
remain separate steward blockers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

_TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
# GitHub App installation reviews commonly surface NONE; some surfaces use BOT.
_TRUSTED_APP_ASSOCIATIONS = {"NONE", "BOT", "OWNER", "MEMBER", "COLLABORATOR"}
_FORBIDDEN_APP_LOGINS = frozenset(
    {
        "github-actions",
        "github-actions[bot]",
        "dependabot",
        "dependabot[bot]",
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
    pr_author: str | None = None,
) -> list[str]:
    """Return fail-closed blocker codes for a security/release approval claim.

    Returns an empty list only when *required* is falsy, or *approval* is a
    well-formed, current, exact-head-bound APPROVED review from either:

    * a human login in *trusted_approvers* with a trusted association, and
      not equal to *pr_author*; or
    * a GitHub App login registered in *trusted_apps* for *expected_repo*.
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

    # Structural errors above already fail closed; identity checks only when
    # the claim is otherwise coherent enough to classify.
    if errors:
        return _dedupe(errors)

    approver = approval.get("approver")
    if not isinstance(approver, str) or not approver.strip():
        return ["SECURITY_RELEASE_APPROVAL_INVALID"]

    human_errors = _evaluate_human_channel(
        approval,
        approver=approver,
        trusted_approvers=trusted_approvers,
        pr_author=pr_author,
    )
    if human_errors is None:
        return []

    app_errors = _evaluate_app_channel(
        approval,
        approver=approver,
        trusted_apps=list(trusted_apps or ()),
        expected_repo=expected_repo,
    )
    if app_errors is None:
        return []

    # Prefer the more specific human self-approval code when both fail.
    if "SECURITY_RELEASE_APPROVAL_SELF" in human_errors:
        return _dedupe(human_errors)
    # If the login looks like a bot / registered app, surface app errors.
    if _looks_like_bot_login(approver) or _find_trusted_app(approver, trusted_apps or ()):
        return _dedupe(app_errors)
    return _dedupe(human_errors)


def _evaluate_human_channel(
    approval: Mapping[str, Any],
    *,
    approver: str,
    trusted_approvers: list[str],
    pr_author: str | None,
) -> list[str] | None:
    """Return None on success, else error codes for the human channel."""
    if _looks_like_bot_login(approver):
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    if not trusted_approvers or approver not in trusted_approvers:
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    association = str(approval.get("approver_association") or "").upper()
    if association not in _TRUSTED_ASSOCIATIONS:
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    if pr_author and _normalize_login(approver) == _normalize_login(pr_author):
        return ["SECURITY_RELEASE_APPROVAL_SELF"]

    return None


def _evaluate_app_channel(
    approval: Mapping[str, Any],
    *,
    approver: str,
    trusted_apps: Sequence[Mapping[str, Any]],
    expected_repo: str,
) -> list[str] | None:
    """Return None on success, else error codes for the GitHub App channel."""
    if _normalize_login(approver) in {_normalize_login(x) for x in _FORBIDDEN_APP_LOGINS}:
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    app = _find_trusted_app(approver, trusted_apps)
    if app is None:
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    owner = str(app.get("owner") or "").strip()
    scope = str(app.get("installation_scope") or "").strip()
    if not owner or not scope:
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    # Installation must bind this repository.
    if scope != expected_repo:
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    # Owner must match the org that owns the repo (and the configured owner).
    repo_owner = expected_repo.split("/", 1)[0] if "/" in expected_repo else ""
    if owner != repo_owner:
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    association = str(approval.get("approver_association") or "NONE").upper()
    if association not in _TRUSTED_APP_ASSOCIATIONS:
        return ["SECURITY_RELEASE_APPROVER_UNKNOWN"]

    return None


def _find_trusted_app(
    approver: str, trusted_apps: Sequence[Mapping[str, Any]]
) -> Mapping[str, Any] | None:
    target = _normalize_login(approver)
    for app in trusted_apps:
        if not isinstance(app, Mapping):
            continue
        login = app.get("login")
        if not isinstance(login, str) or not login.strip():
            continue
        if _normalize_login(login) == target:
            return app
    return None


def _looks_like_bot_login(login: str) -> bool:
    normalized = _normalize_login(login)
    return normalized.endswith("[bot]") or normalized in {
        _normalize_login(x) for x in _FORBIDDEN_APP_LOGINS
    }


def _normalize_login(login: str) -> str:
    return login.strip().lower()


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
