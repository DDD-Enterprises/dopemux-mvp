===== tools/pr_steward/solo_owner_security_release.py (full file) =====
"""Solo-owner exact-head security-release authorization (ADR-DMX-PRSTEWARD-SOLOOWNER-001).

This path exists only for repositories whose trusted security-release roster on
the trusted main ref contains exactly one human approver who is also the PR
author, holds solo-operator association OWNER (user-owned) or MEMBER
(organization-owned), and who cannot post a GitHub APPROVED review on their
own PR.

It never:
- counts as an ordinary GitHub APPROVED review;
- enables auto-merge;
- waives CI, proof, audit, review-thread, reviewer-classification, or harvest gates;
- activates when any eligible non-author trusted approver exists;
- activates for COLLABORATOR or other non-solo-operator associations.

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

# Associations that prove solo-operator authority for the solo path.
# OWNER  — user-owned repositories
# MEMBER — organization-owned repositories (org maintainer association)
# COLLABORATOR and all other associations do NOT activate this path.
# Do not generalize to trusted_author_associations (that set includes
# COLLABORATOR and is broader than this release-authority contract).
_SOLO_OPERATOR_ASSOCIATIONS = frozenset({"OWNER", "MEMBER"})

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
    # If association is present and not OWNER/MEMBER, refuse. Missing association
    # is allowed only when the authorizing issue comment itself carries a
    # solo-operator association (OWNER or MEMBER). Public diagnostic codes
    # preserve the historical SOLO_OWNER_* names for consumers.
    if assoc and assoc not in _SOLO_OPERATOR_ASSOCIATIONS:
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

    # Operator association on the phrase comment must be OWNER or MEMBER.
    # Fail-closed when both PR author association and comment association are
    # missing/untrusted. When both are present and differ, refuse (mismatch).
    comment_assoc = str(auth.get("operator_association") or "").upper()
    if assoc and comment_assoc and assoc != comment_assoc:
        diagnostics.append("SOLO_OWNER_ASSOCIATION_MISMATCH")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))
    if (
        comment_assoc not in _SOLO_OPERATOR_ASSOCIATIONS
        and assoc not in _SOLO_OPERATOR_ASSOCIATIONS
    ):
        diagnostics.append("SOLO_OWNER_PHRASE_OPERATOR_NOT_OWNER")
        return SoloOwnerEvaluation(False, None, tuple(diagnostics))
    if comment_assoc and comment_assoc not in _SOLO_OPERATOR_ASSOCIATIONS:
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

===== DIFF (allowlisted) =====
diff --git a/docs/90-adr/adr-dmx-prsteward-soloowner-001.md b/docs/90-adr/adr-dmx-prsteward-soloowner-001.md
index d9399b36dc..7b497f235f 100644
--- a/docs/90-adr/adr-dmx-prsteward-soloowner-001.md
+++ b/docs/90-adr/adr-dmx-prsteward-soloowner-001.md
@@ -5,10 +5,10 @@ type: adr
 owner: '@hu3mann'
 author: 'Grok Build, for operator decision'
 date: '2026-07-27'
-last_review: '2026-07-27'
-next_review: '2026-10-25'
+last_review: '2026-07-26'
+next_review: '2026-10-24'
 status: accepted
-prelude: Resolves solo-owner PR Steward security-release deadlock without inventing a second reviewer or weakening multi-reviewer enforcement.
+prelude: Resolves solo-owner PR Steward security-release deadlock without inventing a second reviewer or weakening multi-reviewer enforcement. Org maintainers use MEMBER association.
 graph_metadata:
   node_type: ADR
   impact: high
@@ -66,16 +66,22 @@ Provide a narrowly scoped override that activates **only** when all of the
 following hold:
 
 1. trusted security-release roster on trusted main contains exactly one human;
-2. that identity is the repository owner and PR author;
-3. no eligible non-author trusted approver exists;
-4. independent embedded audit is current to the exact PR head with
+2. that identity is the PR author and the sole trusted security-release approver;
+3. the PR author / authorizing-comment association is exactly `OWNER` (user-owned
+   repositories) or `MEMBER` (organization-owned repositories); `COLLABORATOR`,
+   `CONTRIBUTOR`, `FIRST_TIMER`, `FIRST_TIME_CONTRIBUTOR`, `NONE`, missing on both
+   sides, and unknown values do **not** activate;
+4. when both PR association and comment association are present, they must match
+   (mismatch → `SOLO_OWNER_ASSOCIATION_MISMATCH`);
+5. no eligible non-author trusted approver exists;
+6. independent embedded audit is current to the exact PR head with
    `PASS` or non-blocking `PASS_WITH_RISKS`, and auditor tool/model/provider/
    runner/session fields are recorded when present;
-5. all required CI checks are current and green (no failed/pending required);
-6. proof is current to the exact PR head;
-7. no unknown reviewers, unclassified review items, unresolved blocking threads,
+7. all required CI checks are current and green (no failed/pending required);
+8. proof is current to the exact PR head;
+9. no unknown reviewers, unclassified review items, unresolved blocking threads,
    harvest incompleteness, draft/closed PR, or mixed-SHA artifact sets remain;
-8. the operator posts an exact phrase as a PR issue comment:
+10. the operator posts an exact phrase as a PR issue comment:
 
 ```text
 AUTHORIZE SOLO-OWNER SECURITY RELEASE FOR PR #<PR_NUMBER> AT HEAD <FULL_SHA>
@@ -124,6 +130,24 @@ remains mandatory whenever a non-author trusted approver exists.
 5. Head binding is exact (full SHA); partial SHAs and wrong PR numbers fail closed.
 6. Phrase author must be the solo trusted identity; foreign logins are ignored.
 7. Receipt is evidence, not a second catalog of authority.
+8. Solo-operator associations are exactly `{OWNER, MEMBER}` — not the broader
+   `trusted_author_associations` set (which includes `COLLABORATOR`).
+9. Association acceptance never replaces the exact single-person trusted roster
+   check; a second trusted human disables the solo path regardless of association.
+
+## Amendment — org MEMBER association (TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001)
+
+**Problem:** The initial implementation required GitHub `authorAssociation=OWNER`.
+On organization-owned repositories such as `DDD-Enterprises/dopemux-mvp`, GitHub
+reports the sole human maintainer as `MEMBER`, so a legitimate exact-head solo
+authorization was rejected before remaining gates ran.
+
+**Repair:** Accept `_SOLO_OPERATOR_ASSOCIATIONS = {OWNER, MEMBER}` for PR author
+and authorization-comment association validation (and receipt generation). All
+other security, proof, audit, review, CI, exact-head, and multi-approver gates
+remain independently blocking. Auto-merge remains disabled. The solo-owner
+receipt never becomes a fabricated GitHub review. The organization-owned GitHub
+App approval path (PR #1133 / ADR companion) is unchanged.
 
 ## Consequences
 
diff --git a/tests/pr_steward/test_classifier_solo_owner.py b/tests/pr_steward/test_classifier_solo_owner.py
index 793d7d7523..88044ce599 100644
--- a/tests/pr_steward/test_classifier_solo_owner.py
+++ b/tests/pr_steward/test_classifier_solo_owner.py
@@ -228,3 +228,61 @@ def test_stale_head_phrase_does_not_approve(tmp_path: Path):
     readiness = _readiness(harvest, known)
     assert readiness["security_release"]["approved"] is False
     assert "SECURITY_RELEASE_APPROVAL_REQUIRED" in readiness["blockers"]
+
+
+def test_org_member_solo_owner_exact_head_ready(tmp_path: Path):
+    """Organization-owned repo: sole trusted maintainer reported as MEMBER.
+
+    Reproduces DDD-Enterprises/dopemux-mvp + hu3mann + MEMBER association
+    with exact phrase, single trusted roster, and all other gates passing.
+    """
+    known = _known_reviewers(tmp_path, ["hu3mann"])
+    phrase = build_solo_owner_phrase(pr_number=PR, head_sha=HEAD_SHA)
+    harvest = _harvest(
+        issue_comments=[
+            {
+                "id": "ic-auth-member",
+                "body": phrase,
+                "author": {"login": "hu3mann"},
+                "authorAssociation": "MEMBER",
+                "createdAt": "2026-07-27T12:00:00Z",
+            }
+        ],
+        author_association="MEMBER",
+    )
+    readiness = _readiness(harvest, known)
+    assert readiness["security_release"]["required"] is True
+    assert readiness["security_release"]["approved"] is True
+    override = readiness["security_release"]["solo_owner_override"]
+    assert override is not None
+    assert override["receipt_code"] == RECEIPT_CODE
+    assert override["operator_login"] == "hu3mann"
+    assert override["operator_association"] == "MEMBER"
+    assert override["does_not_count_as_github_approved_review"] is True
+    assert override["auto_merge_enabled"] is False
+    assert readiness["security_release"]["approval"] is None
+    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" not in readiness["blockers"]
+    assert readiness["readiness"] == "READY"
+
+
+def test_org_member_collaborator_does_not_activate(tmp_path: Path):
+    """COLLABORATOR association must not clear the security-release gate."""
+    known = _known_reviewers(tmp_path, ["hu3mann"])
+    phrase = build_solo_owner_phrase(pr_number=PR, head_sha=HEAD_SHA)
+    harvest = _harvest(
+        issue_comments=[
+            {
+                "id": "ic-auth",
+                "body": phrase,
+                "author": {"login": "hu3mann"},
+                "authorAssociation": "COLLABORATOR",
+                "createdAt": "2026-07-27T12:00:00Z",
+            }
+        ],
+        author_association="COLLABORATOR",
+    )
+    readiness = _readiness(harvest, known)
+    assert readiness["security_release"]["approved"] is False
+    assert readiness["security_release"]["solo_owner_override"] is None
+    assert "SECURITY_RELEASE_APPROVAL_REQUIRED" in readiness["blockers"]
+    assert readiness["readiness"] != "READY"
diff --git a/tests/pr_steward/test_solo_owner_security_release.py b/tests/pr_steward/test_solo_owner_security_release.py
index 07e2a29efe..c344f4c4d1 100644
--- a/tests/pr_steward/test_solo_owner_security_release.py
+++ b/tests/pr_steward/test_solo_owner_security_release.py
@@ -93,6 +93,158 @@ def test_activate_happy_path():
     assert result.receipt["auto_merge_enabled"] is False
     assert result.receipt["head_sha"] == HEAD
     assert result.receipt["pr_number"] == PR
+    assert result.receipt["operator_association"] == "OWNER"
+
+
+def test_activate_owner_owner():
+    """PR OWNER + comment OWNER + single trusted roster → activated."""
+    result = _eval(
+        pr_author_association="OWNER",
+        issue_comments=[_comment(_phrase(), association="OWNER")],
+    )
+    assert result.activated is True
+    assert result.receipt is not None
+    assert result.receipt["operator_association"] == "OWNER"
+
+
+def test_activate_member_member():
+    """PR MEMBER + comment MEMBER + single trusted roster → activated (org case)."""
+    result = _eval(
+        pr_author_association="MEMBER",
+        issue_comments=[_comment(_phrase(), association="MEMBER")],
+    )
+    assert result.activated is True
+    assert result.receipt is not None
+    assert result.receipt["receipt_code"] == RECEIPT_CODE
+    assert result.receipt["operator_association"] == "MEMBER"
+    assert result.receipt["operator_login"] == AUTHOR
+
+
+def test_activate_missing_pr_association_member_comment():
+    """Missing PR association + comment MEMBER → activated via comment."""
+    result = _eval(
+        pr_author_association=None,
+        issue_comments=[_comment(_phrase(), association="MEMBER")],
+    )
+    assert result.activated is True
+    assert result.receipt is not None
+    assert result.receipt["operator_association"] == "MEMBER"
+
+
+def test_reject_collaborator_collaborator():
+    """COLLABORATOR does not activate the solo-owner path."""
+    result = _eval(
+        pr_author_association="COLLABORATOR",
+        issue_comments=[_comment(_phrase(), association="COLLABORATOR")],
+    )
+    assert result.activated is False
+    assert "SOLO_OWNER_AUTHOR_NOT_OWNER" in result.diagnostic_errors
+
+
+def test_reject_member_pr_collaborator_comment():
+    """PR MEMBER + comment COLLABORATOR → rejected (mismatch / untrusted comment)."""
+    result = _eval(
+        pr_author_association="MEMBER",
+        issue_comments=[_comment(_phrase(), association="COLLABORATOR")],
+    )
+    assert result.activated is False
+    assert "SOLO_OWNER_ASSOCIATION_MISMATCH" in result.diagnostic_errors
+
+
+def test_reject_owner_member_association_mismatch():
+    """PR OWNER + comment MEMBER → rejected due association mismatch."""
+    result = _eval(
+        pr_author_association="OWNER",
+        issue_comments=[_comment(_phrase(), association="MEMBER")],
+    )
+    assert result.activated is False
+    assert "SOLO_OWNER_ASSOCIATION_MISMATCH" in result.diagnostic_errors
+
+
+def test_reject_member_with_second_trusted_human():
+    """Trusted roster [author, second-human] + MEMBER → rejected."""
+    result = _eval(
+        trusted_approvers=[AUTHOR, "second-human"],
+        pr_author_association="MEMBER",
+        issue_comments=[_comment(_phrase(), association="MEMBER")],
+    )
+    assert result.activated is False
+    assert "SOLO_OWNER_INELIGIBLE_ROSTER" in result.diagnostic_errors
+
+
+def test_reject_member_foreign_comment_author():
+    """comment author != PR author + MEMBER → rejected."""
+    result = _eval(
+        pr_author_association="MEMBER",
+        issue_comments=[
+            _comment(_phrase(), login="not-the-author", association="MEMBER")
+        ],
+    )
+    assert result.activated is False
+    assert "SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH" in result.diagnostic_errors
+
+
+def test_reject_member_wrong_pr_or_stale_head():
+    """Wrong PR number or stale head + MEMBER → rejected."""
+    wrong_pr = _eval(
+        pr_author_association="MEMBER",
+        issue_comments=[_comment(_phrase(pr=9999), association="MEMBER")],
+    )
+    assert wrong_pr.activated is False
+    assert "SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH" in wrong_pr.diagnostic_errors
+
+    stale_head = _eval(
+        pr_author_association="MEMBER",
+        issue_comments=[_comment(_phrase(head="a" * 40), association="MEMBER")],
+    )
+    assert stale_head.activated is False
+    assert "SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH" in stale_head.diagnostic_errors
+
+
+def test_reject_member_when_other_gates_fail():
+    """MEMBER cannot waive audit/proof/CI/thread/reviewer/unclassified gates."""
+    for kwargs, diagnostic in (
+        ({"audit_status": "FAIL"}, "SOLO_OWNER_AUDIT_NOT_PASSING"),
+        ({"proof_status": "STALE"}, "SOLO_OWNER_PROOF_NOT_CURRENT"),
+        (
+            {
+                "blockers": [
+                    "SECURITY_RELEASE_APPROVAL_REQUIRED",
+                    "FAILED_CHECK",
+                ]
+            },
+            "SOLO_OWNER_OTHER_GATES_BLOCKING",
+        ),
+        (
+            {
+                "blockers": [
+                    "SECURITY_RELEASE_APPROVAL_REQUIRED",
+                    "UNRESOLVED_REVIEW_THREAD",
+                ]
+            },
+            "SOLO_OWNER_OTHER_GATES_BLOCKING",
+        ),
+        (
+            {
+                "blockers": [
+                    "SECURITY_RELEASE_APPROVAL_REQUIRED",
+                    "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION",
+                ]
+            },
+            "SOLO_OWNER_OTHER_GATES_BLOCKING",
+        ),
+        (
+            {"unclassified_review_item_count": 1},
+            "SOLO_OWNER_UNCLASSIFIED_REVIEW_ITEMS",
+        ),
+    ):
+        result = _eval(
+            pr_author_association="MEMBER",
+            issue_comments=[_comment(_phrase(), association="MEMBER")],
+            **kwargs,
+        )
+        assert result.activated is False, kwargs
+        assert diagnostic in result.diagnostic_errors, (kwargs, result.diagnostic_errors)
 
 
 def test_cannot_activate_when_non_author_trusted_approver_exists():
diff --git a/tools/pr_steward/solo_owner_security_release.py b/tools/pr_steward/solo_owner_security_release.py
index 375d8feec0..e3a4c0205a 100644
--- a/tools/pr_steward/solo_owner_security_release.py
+++ b/tools/pr_steward/solo_owner_security_release.py
@@ -2,13 +2,16 @@
 
 This path exists only for repositories whose trusted security-release roster on
 the trusted main ref contains exactly one human approver who is also the PR
-author/owner, and who cannot post a GitHub APPROVED review on their own PR.
+author, holds solo-operator association OWNER (user-owned) or MEMBER
+(organization-owned), and who cannot post a GitHub APPROVED review on their
+own PR.
 
 It never:
 - counts as an ordinary GitHub APPROVED review;
 - enables auto-merge;
 - waives CI, proof, audit, review-thread, reviewer-classification, or harvest gates;
-- activates when any eligible non-author trusted approver exists.
+- activates when any eligible non-author trusted approver exists;
+- activates for COLLABORATOR or other non-solo-operator associations.
 
 Activation requires an exact operator phrase harvested from PR issue comments:
 
@@ -30,8 +33,13 @@ SOLO_OWNER_PHRASE_RE = re.compile(
 RECEIPT_CODE = "SOLO_OWNER_SECURITY_RELEASE_OVERRIDE_USED"
 AUTHORIZATION_SCOPE = "security_release_only"
 
-# Associations that prove owner/operator authority for the solo path.
-_OWNER_ASSOCIATIONS = frozenset({"OWNER"})
+# Associations that prove solo-operator authority for the solo path.
+# OWNER  — user-owned repositories
+# MEMBER — organization-owned repositories (org maintainer association)
+# COLLABORATOR and all other associations do NOT activate this path.
+# Do not generalize to trusted_author_associations (that set includes
+# COLLABORATOR and is broader than this release-authority contract).
+_SOLO_OPERATOR_ASSOCIATIONS = frozenset({"OWNER", "MEMBER"})
 
 # Audit statuses that may accompany a solo-owner override.
 _PASSING_AUDITS = frozenset({"PASS", "PASS_WITH_RISKS"})
@@ -225,9 +233,11 @@ def evaluate_solo_owner_security_release(
         )
 
     assoc = str(pr_author_association or "").upper()
-    # If association is present and not OWNER, refuse. Missing association is
-    # allowed only when the authorizing issue comment itself carries OWNER.
-    if assoc and assoc not in _OWNER_ASSOCIATIONS:
+    # If association is present and not OWNER/MEMBER, refuse. Missing association
+    # is allowed only when the authorizing issue comment itself carries a
+    # solo-operator association (OWNER or MEMBER). Public diagnostic codes
+    # preserve the historical SOLO_OWNER_* names for consumers.
+    if assoc and assoc not in _SOLO_OPERATOR_ASSOCIATIONS:
         diagnostics.append("SOLO_OWNER_AUTHOR_NOT_OWNER")
         return SoloOwnerEvaluation(False, None, tuple(diagnostics))
 
@@ -264,13 +274,20 @@ def evaluate_solo_owner_security_release(
         diagnostics.append("SOLO_OWNER_PHRASE_MISSING_OR_MISMATCH")
         return SoloOwnerEvaluation(False, None, tuple(diagnostics))
 
-    # Operator association on the phrase comment must be OWNER (fail-closed when
-    # both PR author association and comment association are missing/untrusted).
+    # Operator association on the phrase comment must be OWNER or MEMBER.
+    # Fail-closed when both PR author association and comment association are
+    # missing/untrusted. When both are present and differ, refuse (mismatch).
     comment_assoc = str(auth.get("operator_association") or "").upper()
-    if comment_assoc not in _OWNER_ASSOCIATIONS and assoc not in _OWNER_ASSOCIATIONS:
+    if assoc and comment_assoc and assoc != comment_assoc:
+        diagnostics.append("SOLO_OWNER_ASSOCIATION_MISMATCH")
+        return SoloOwnerEvaluation(False, None, tuple(diagnostics))
+    if (
+        comment_assoc not in _SOLO_OPERATOR_ASSOCIATIONS
+        and assoc not in _SOLO_OPERATOR_ASSOCIATIONS
+    ):
         diagnostics.append("SOLO_OWNER_PHRASE_OPERATOR_NOT_OWNER")
         return SoloOwnerEvaluation(False, None, tuple(diagnostics))
-    if comment_assoc and comment_assoc not in _OWNER_ASSOCIATIONS:
+    if comment_assoc and comment_assoc not in _SOLO_OPERATOR_ASSOCIATIONS:
         diagnostics.append("SOLO_OWNER_PHRASE_OPERATOR_NOT_OWNER")
         return SoloOwnerEvaluation(False, None, tuple(diagnostics))
 

===== TASK PACKET SUMMARY =====
---
id: TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001
project: dopemux-mvp
target: tools/pr_steward/solo_owner_security_release.py
series: pr-steward
risk: HIGH
status: implementing
parent_policy: ADR-DMX-PRSTEWARD-SOLOOWNER-001
parent_pr: 1131
related_product_pr: 1126
---

# TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001

## Objective

Repair PR Steward solo-owner security-release policy so the sole trusted
maintainer of an organization-owned repository may authorize an exact-head
red-lane PR when GitHub reports their repository association as `MEMBER`.

Preserve every other security, proof, audit, review, CI, exact-head, and
multi-approver gate.

## Root cause

`tools/pr_steward/solo_owner_security_release.py` defined:

```python
_OWNER_ASSOCIATIONS = frozenset({"OWNER"})
```

For organization-owned repositories, human org maintainers are reported as
`MEMBER`, so legitimate exact-head solo-owner authorization was rejected early.

## Required policy

Solo-operator associations: exactly `{OWNER, MEMBER}`.

- `OWNER` — user-owned repositories
- `MEMBER` — organization-owned repositories
- `COLLABORATOR` and all other values do not activate
- Association acceptance never replaces exact single-person trusted roster
- Non-author trusted security approver disables solo-owner route
- Authorization comment must be authored by PR author and sole trusted approver
- Comment must match exact PR number and full 40-char head SHA
- Audit, proof, CI, review-thread, reviewer-classification, harvest, mixed-SHA
  gates remain independently blocking
- Auto-merge remains disabled
- Solo-owner receipt never becomes a fabricated GitHub review
- When both PR and comment associations are present and differ →
  `SOLO_OWNER_ASSOCIATION_MISMATCH`

## Scope IN

- `tools/pr_steward/solo_owner_security_release.py`
- `tests/pr_steward/test_solo_owner_security_release.py`
- `tests/pr_steward/test_classifier_solo_owner.py`
- `docs/90-adr/adr-dmx-prsteward-soloowner-001.md`
- `task-packets/pr-steward/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001.md`
- `proof/TP-PRSTEWARD-SOLO-OWNER-ORG-MEMBER-001/**`

## Scope OUT

- `known_reviewers.json`, ordinary security-release approval/app paths
- schemas, `.github/**`, services/dope-context/**
- PR #1126 branch, PR #1133 policy, red-lane classifications
- opportunistic cleanup

## Stop conditions

Stop if allowlist escape, COLLABORATOR accepted, roster condition weakened,
multi-reviewer enforcement changes, app approval semantics change, non-security
blocker waived, tests fail, independent audit FAIL/NEEDS_SUPERVISOR, secrets
appear, or PR #1126 modified before this policy lands.
