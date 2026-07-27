"""Solo-owner exact-head security-release authorization (ADR-DMX-PRSTEWARD-SOLOOWNER-001).

This path exists only for repositories whose trusted security-release roster on
the trusted main ref contains exactly one human approver who is also the PR
author/owner, and who cannot post a GitHub APPROVED review on their own PR.

It never:
- counts as an ordinary GitHub APPROVED review;
- enables auto-merge;
- waives CI, proof, audit, review-thread, reviewer-classification, or harvest gates;
- activates when any eligible non-author trusted approver exists.

Activation requires an exact operator phrase harvested from PR issue comments:

  AUTHORIZE SOLO-OWNER SECURITY RELEASE FOR PR #<N> AT HEAD <40-char-sha>
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

# Exact phrase format (case-sensitive). Full 40-char lowercase or mixed hex SHA.
SOLO_OWNER_PHRASE_RE = re.compile(
    r"AUTHORIZE SOLO-OWNER SECURITY RELEASE FOR PR #(\d+) AT HEAD ([0-9a-fA-F]{40})\b"
)

RECEIPT_CODE = "SOLO_OWNER_SECURITY_RELEASE_OVERRIDE_USED"
AUTHORIZATION_SCOPE = "security_release_only"

# Associations that prove owner/operator authority for the solo path.
_OWNER_ASSOCIATIONS = frozenset({"OWNER"})

# Audit statuses that may accompany a solo-owner override.
_PASSING_AUDITS = frozenset({"PASS", "PASS_WITH_RISKS"})

@dataclass(frozen=True)
class SoloOwnerEvaluation:
    """Result of attempting the solo-owner security-release path."""

    activated: bool
    receipt: dict[str, Any] | None
    diagnostic_errors: tuple[str, ...]


def build_solo_owner_phrase(*, pr_number: int, head_sha: str) -> str:
    """Return the exact operator phrase for a PR head."""
    return (
        f"AUTHORIZE SOLO-OWNER SECURITY RELEASE FOR PR #{int(pr_number)} "
        f"AT HEAD {head_sha}"
    )


def parse_solo_owner_phrase(body: str) -> tuple[int, str] | None:
    """Parse the first exact solo-owner phrase in *body*, if any."""
    if not isinstance(body, str) or not body:
        return None
    match = SOLO_OWNER_PHRASE_RE.search(body)
    if not match:
        return None
    return int(match.group(1)), match.group(2).lower()


def solo_owner_roster_eligible(
    trusted_approvers: Sequence[str],
    *,
    pr_author: str,
) -> bool:
    """True when the roster is exactly one human and that human is the PR author.

    A non-author trusted approver makes the ordinary multi-reviewer path
    mandatory; the solo path must not activate.
    """
    cleaned = [str(a).strip() for a in trusted_approvers if str(a).strip()]
    if len(cleaned) != 1:
        return False
    return cleaned[0].lower() == str(pr_author or "").strip().lower()


def _comment_login(comment: Mapping[str, Any]) -> str | None:
    author = comment.get("author") or comment.get("user")
    if isinstance(author, dict):
        login = author.get("login")
        return str(login) if login else None
    if isinstance(author, str) and author:
        return author
    return None


def _comment_association(comment: Mapping[str, Any]) -> str | None:
    raw = comment.get("authorAssociation") or comment.get("author_association")
    if raw is None and isinstance(comment.get("author"), dict):
        raw = comment["author"].get("authorAssociation") or comment["author"].get(
            "association"
        )
    if raw is None:
        return None
    return str(raw).upper()


def _comment_timestamp(comment: Mapping[str, Any]) -> str | None:
    for key in ("createdAt", "created_at", "updatedAt", "updated_at", "submittedAt"):
        value = comment.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _comment_ref(comment: Mapping[str, Any]) -> str:
    for key in ("id", "databaseId", "url", "node_id"):
        value = comment.get(key)
        if value is not None and str(value):
            return str(value)
    return "issue-comment-unknown"


def harvest_solo_owner_authorization(
    issue_comments: Sequence[Any],
    *,
    expected_pr: int,
    expected_head_sha: str,
    expected_operator: str,
) -> dict[str, Any] | None:
    """Return the newest exact-head solo-owner authorization from issue comments.

    Comments from non-operators or with mismatched PR/head are ignored.
    """
    expected_head = str(expected_head_sha or "").lower()
    expected_op = str(expected_operator or "").lower()
    candidates: list[tuple[str, dict[str, Any]]] = []

    for raw in issue_comments:
        if not isinstance(raw, Mapping):
            continue
        body = raw.get("body")
        if not isinstance(body, str):
            continue
        parsed = parse_solo_owner_phrase(body)
        if parsed is None:
            continue
        phrase_pr, phrase_head = parsed
        if phrase_pr != int(expected_pr):
            continue
        if phrase_head != expected_head:
            continue
        login = _comment_login(raw)
        if not login or login.lower() != expected_op:
            continue
        ts = _comment_timestamp(raw) or ""
        candidates.append(
            (
                ts,
                {
                    "operator_login": login,
                    "operator_association": _comment_association(raw),
                    "authorized_at": ts or None,
                    "authorization_ref": _comment_ref(raw),
                    "authorization_phrase": build_solo_owner_phrase(
                        pr_number=phrase_pr, head_sha=phrase_head
                    ),
                    "pr_number": phrase_pr,
                    "head_sha": phrase_head,
                },
            )
        )

    if not candidates:
        return None
    # Newest by timestamp string (RFC3339 sorts lexicographically when present).
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def _has_non_waivable_blockers(blockers: Sequence[str]) -> list[str]:
    """Return non-security blockers that prevent solo-owner activation.

    Any blocker other than ``SECURITY_RELEASE_*`` is non-waivable: the solo path
    only substitutes for the missing non-author APPROVED review.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for blocker in blockers:
        text = str(blocker)
        if text.startswith("SECURITY_RELEASE_"):
            continue
        if text not in seen:
            seen.add(text)
            ordered.append(text)
    return ordered


def evaluate_solo_owner_security_release(
    *,
    required: bool,
    trusted_approvers: Sequence[str],
    pr_author: str,
    pr_author_association: str | None,
    expected_repo: str,
    expected_pr: int,
    expected_head_sha: str,
    issue_comments: Sequence[Any],
    blockers: Sequence[str],
    unclassified_review_item_count: int,
    audit_status: str,
    audit_meta: Mapping[str, Any] | None,
    proof_status: str,
) -> SoloOwnerEvaluation:
    """Evaluate whether a solo-owner security-release override may activate.

    Returns ``activated=True`` only when every activation condition holds and an
    exact-head operator phrase is harvested from issue comments.
    """
    diagnostics: list[str] = []

    if not required:
        return SoloOwnerEvaluation(False, None, ("SOLO_OWNER_NOT_REQUIRED",))

    if not solo_owner_roster_eligible(trusted_approvers, pr_author=pr_author):
        return SoloOwnerEvaluation(
            False,
            None,
            ("SOLO_OWNER_INELIGIBLE_ROSTER",),
        )

    assoc = str(pr_author_association or "").upper()
    # If association is present and not OWNER, refuse. Missing association is
    # allowed only when the authorizing issue comment itself carries OWNER.
    if assoc and assoc not in _OWNER_ASSOCIATIONS:
        diagnostics.append("SOLO_OWNER_AUTHOR_NOT_OWNER")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))

    if unclassified_review_item_count:
        diagnostics.append("SOLO_OWNER_UNCLASSIFIED_REVIEW_ITEMS")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))

    audit = str(audit_status or "").upper()
    if audit not in _PASSING_AUDITS:
        diagnostics.append("SOLO_OWNER_AUDIT_NOT_PASSING")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))

    proof = str(proof_status or "").upper()
    if proof not in {"CURRENT", "CURRENT_WITH_SELF_REFERENCE_EXCEPTION", "FRESH"}:
        diagnostics.append("SOLO_OWNER_PROOF_NOT_CURRENT")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))

    non_waivable = _has_non_waivable_blockers(blockers)
    if non_waivable:
        diagnostics.append("SOLO_OWNER_OTHER_GATES_BLOCKING")
        return SoloOwnerEvaluation(
            False,
            None,
            tuple(diagnostics + non_waivable[:8]),
        )

    auth = harvest_solo_owner_authorization(
        issue_comments,
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha,
        expected_operator=pr_author,
    )
    if auth is None:
        diagnostics.append("SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))

    # Operator association on the phrase comment must be OWNER (fail-closed when
    # both PR author association and comment association are missing/untrusted).
    comment_assoc = str(auth.get("operator_association") or "").upper()
    if comment_assoc not in _OWNER_ASSOCIATIONS and assoc not in _OWNER_ASSOCIATIONS:
        diagnostics.append("SOLO_OWNER_PHRASE_OPERATOR_NOT_OWNER")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))
    if comment_assoc and comment_assoc not in _OWNER_ASSOCIATIONS:
        diagnostics.append("SOLO_OWNER_PHRASE_OPERATOR_NOT_OWNER")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))

    meta = dict(audit_meta or {})
    receipt = {
        "receipt_code": RECEIPT_CODE,
        "kind": "SOLO_OWNER_SECURITY_RELEASE_OVERRIDE",
        "repository": expected_repo,
        "pr_number": int(expected_pr),
        "head_sha": str(expected_head_sha).lower(),
        "operator_login": auth["operator_login"],
        "operator_association": comment_assoc or assoc,
        "authorized_at": auth.get("authorized_at")
        or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authorization_ref": auth["authorization_ref"],
        "authorization_phrase": auth["authorization_phrase"],
        "authorization_scope": AUTHORIZATION_SCOPE,
        "does_not_count_as_github_approved_review": True,
        "auto_merge_enabled": False,
        "trusted_roster_snapshot": [str(a) for a in trusted_approvers],
        "audit": {
            "status": audit,
            "auditor_tool": meta.get("auditor_tool"),
            "auditor_model": meta.get("auditor_model"),
            "auditor_provider": meta.get("auditor_provider"),
            "auditor_runner": meta.get("auditor_runner"),
            "auditor_session": meta.get("auditor_session"),
            "invocation": meta.get("invocation"),
            "report_path": meta.get("report_path"),
        },
        "proof_status": proof,
    }
    return SoloOwnerEvaluation(True, receipt, ())
