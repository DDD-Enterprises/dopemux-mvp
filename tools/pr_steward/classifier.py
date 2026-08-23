from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.pr_steward.security_release_gate import classify_security_release_paths
from tools.pr_steward.security_release_approval import (
    compute_app_gate_ok,
    evaluate_security_release_approval,
    load_trusted_security_apps,
)
from tools.pr_steward.solo_owner_security_release import (
    evaluate_solo_owner_security_release,
)


SCHEMA_VERSION = "1.1.0"
PASSING_AUDITS = {"PASS", "PASS_WITH_RISKS"}
BLOCKING_AUDITS = {"FAIL", "NEEDS_SUPERVISOR", "SKIPPED"}
FAILED_CHECK_CONCLUSIONS = {
    "failure",
    "cancelled",
    "timed_out",
    "action_required",
    "stale",
    "startup_failure",
}
PENDING_CHECK_STATUSES = {"queued", "in_progress", "requested", "waiting", "pending"}
CURRENT_PROOF_STATUSES = {"CURRENT", "CURRENT_WITH_SELF_REFERENCE_EXCEPTION", "FRESH"}
STALE_PROOF_STATUSES = {"STALE"}
MISSING_PROOF_STATUSES = {"MISSING"}
# Exact context published by .github/workflows/pr-steward.yml against the
# candidate PR head. Must be excluded from readiness evaluation so a prior
# failed self-status cannot sticky-red the next Steward run on the same head.
# Raw harvest still retains the entry for evidence.
STEWARD_SELF_STATUS_CONTEXT = "PR Steward / final readiness"

# Sources that make up the review item ledger's conservation guarantee: every
# raw harvest entry from these four inputs must yield exactly one ledger item.
REVIEW_LEDGER_SOURCES = {"review", "review_comment", "issue_comment", "review_thread"}
# Every disposition a well-formed item can receive. Anything outside this set
# (currently only the malformed-shape sentinel below) counts as unclassified.
RECOGNIZED_REVIEW_DISPOSITIONS = {
    "MUST_FIX",
    "NEEDS_SUPERVISOR",
    "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION",
    "OUT_OF_SCOPE_FOLLOWUP",
    "REJECTED_WITH_REASON",
    "OPTIONAL_DEFERRED",
    "AUTO_APPLIED",
}
UNCLASSIFIED_ITEM_DISPOSITION = "UNCLASSIFIED_ITEM_SHAPE"


class ProofFreshness(dict):
    """Dict proof state with legacy string comparisons for older callers."""

    _LEGACY_EQUIVALENTS = {
        "CURRENT": {"CURRENT", "FRESH"},
        "CURRENT_WITH_SELF_REFERENCE_EXCEPTION": {
            "CURRENT_WITH_SELF_REFERENCE_EXCEPTION",
            "FRESH",
        },
        "STALE": {"STALE"},
        "MISSING": {"MISSING"},
    }

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            status = str(self.get("status") or "")
            return other in self._LEGACY_EQUIVALENTS.get(status, {status})
        return super().__eq__(other)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_known_reviewers(path: Path) -> tuple[set[str], set[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    reviewers = {str(item) for item in payload.get("known_reviewers", [])}
    associations = {
        str(item).upper() for item in payload.get("trusted_author_associations", [])
    }
    return reviewers, associations


def load_trusted_security_approvers(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [str(item) for item in payload.get("trusted_security_release_approvers", [])]


def load_trusted_security_release_apps(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return load_trusted_security_apps(payload)


def build_artifacts(
    harvest: dict[str, Any],
    *,
    repo: str,
    pr_number: int,
    strict: bool,
    allow_closed: bool,
    generated_at: str | None = None,
    known_reviewers_path: Path | None = None,
) -> dict[str, dict[str, Any] | str]:
    generated = generated_at or utc_now()
    known_path = known_reviewers_path or Path(__file__).with_name("known_reviewers.json")
    known_reviewers, trusted_associations = load_known_reviewers(known_path)

    pr = _pr_payload(harvest, pr_number=pr_number)
    pr_raw = harvest.get("pr") or {}
    review_items: list[dict[str, Any]] = []
    thread_dispositions: list[dict[str, Any]] = []
    blockers: list[str] = []
    unknowns: list[str] = []
    reviews_in = _ensure_list(
        harvest.get("reviews"), label="reviews", blockers=blockers, unknowns=unknowns
    )
    review_comments_in = _ensure_list(
        harvest.get("review_comments"),
        label="review_comments",
        blockers=blockers,
        unknowns=unknowns,
    )
    issue_comments_in = _ensure_list(
        harvest.get("issue_comments"),
        label="issue_comments",
        blockers=blockers,
        unknowns=unknowns,
    )
    review_threads_in = _ensure_list(
        harvest.get("review_threads"),
        label="review_threads",
        blockers=blockers,
        unknowns=unknowns,
    )
    checks = _classify_checks(
        harvest.get("checks") or [],
        pr_head_sha=pr["head_sha"],
        strict=strict,
    )

    _extend_once(blockers, checks["blockers"])
    _extend_once(unknowns, checks["unknowns"])

    if not harvest.get("harvest_complete", False):
        _append_once(blockers, "HARVEST_INCOMPLETE")
        for error in harvest.get("harvest_errors") or []:
            _append_once(unknowns, str(error))

    pr_assoc = _association(pr_raw)
    if pr_assoc is None and isinstance(pr_raw.get("author"), dict):
        pr_assoc = _association(pr_raw["author"])
    if not _known_author(pr["author"], pr_assoc, known_reviewers, trusted_associations):
        _append_once(blockers, "UNKNOWN_PR_AUTHOR")
        _append_once(unknowns, f"Unknown PR author: {pr['author']}")

    if pr["draft"]:
        _append_once(blockers, "PR_IS_DRAFT")
    if pr["state"].upper() != "OPEN" and not allow_closed:
        _append_once(blockers, "PR_CLOSED")

    review_items.extend(
        _classify_reviews(
            reviews_in,
            known_reviewers=known_reviewers,
            trusted_associations=trusted_associations,
            blockers=blockers,
            unknowns=unknowns,
        )
    )
    resolved_review_comment_dispositions = _resolved_review_comment_dispositions(
        review_threads_in
    )

    review_items.extend(
        _classify_comments(
            review_comments_in,
            source="review_comment",
            known_reviewers=known_reviewers,
            trusted_associations=trusted_associations,
            blockers=blockers,
            unknowns=unknowns,
            resolved_review_comment_dispositions=resolved_review_comment_dispositions,
        )
    )
    review_items.extend(
        _classify_comments(
            issue_comments_in,
            source="issue_comment",
            known_reviewers=known_reviewers,
            trusted_associations=trusted_associations,
            blockers=blockers,
            unknowns=unknowns,
        )
    )

    thread_result = _classify_threads(
        review_threads_in,
        known_reviewers=known_reviewers,
        trusted_associations=trusted_associations,
        blockers=blockers,
        unknowns=unknowns,
    )
    review_items.extend(thread_result["items"])
    thread_dispositions.extend(thread_result["threads"])

    review_items.extend(checks["review_items"])

    expected_review_item_count = _review_source_item_count(
        reviews=reviews_in,
        issue_comments=issue_comments_in,
        review_comments=review_comments_in,
        review_threads=review_threads_in,
    )
    review_ledger_items = [
        item for item in review_items if item["source"] in REVIEW_LEDGER_SOURCES
    ]
    if len(review_ledger_items) != expected_review_item_count:
        _append_once(blockers, "HARVEST_INCOMPLETE")
        _append_once(
            unknowns,
            "Review item ledger conservation check failed: expected "
            f"{expected_review_item_count} items, got {len(review_ledger_items)}.",
        )
    unclassified_count = sum(
        1
        for item in review_ledger_items
        if item["disposition"] not in RECOGNIZED_REVIEW_DISPOSITIONS
    )

    if _detect_mixed_sha_checks(harvest.get("checks") or [], pr_head_sha=pr["head_sha"]):
        _append_once(blockers, "MIXED_SHA_ARTIFACT_SET")

    embedded_audit = _embedded_audit(harvest)
    raw_status = embedded_audit.pop("_raw_status", "")
    audit_status = embedded_audit["status"]
    if audit_status in BLOCKING_AUDITS:
        _append_once(blockers, f"EMBEDDED_AUDIT_{audit_status}")
    if raw_status:
        _append_once(blockers, "EMBEDDED_AUDIT_UNKNOWN")
        _append_once(unknowns, f"Unknown embedded audit status: {raw_status}")

    snapshot_changed_files = _changed_files(harvest.get("changed_files") or [])
    changed_paths = [item["path"] for item in snapshot_changed_files if item.get("path")]
    # A rename moves a path OUT of a protected location as surely as an edit
    # moves content into one — classify the pre-rename path too, or a rename
    # of e.g. tools/pr_steward/known_reviewers.json to an unprotected
    # location would silently evade the trust-root/CI/CODEOWNERS gate.
    renamed_from_paths = [
        item["previous_path"]
        for item in snapshot_changed_files
        if item.get("status") == "renamed" and item.get("previous_path")
    ]
    security_classification = classify_security_release_paths(
        changed_paths + renamed_from_paths
    )
    trusted_security_approvers = load_trusted_security_approvers(known_path)
    trusted_security_apps = load_trusted_security_release_apps(known_path)
    # Human approvals evaluate fully here. App approvals require non-security
    # gates first, so app_gate_ok=False until proof/audit/thread state is known.
    security_release_errors = evaluate_security_release_approval(
        harvest.get("security_release_approval"),
        required=security_classification.required,
        expected_repo=repo,
        expected_pr=pr_number,
        expected_head_sha=pr["head_sha"],
        trusted_approvers=trusted_security_approvers,
        trusted_apps=trusted_security_apps,
        app_gate_ok=False,
    )
    for err in security_release_errors:
        _append_once(blockers, err)
    security_release = {
        "required": security_classification.required,
        "approved": security_classification.required and not security_release_errors,
        "categories": list(security_classification.categories),
        "approval": harvest.get("security_release_approval"),
        "solo_owner_override": None,
        "approval_kind": None,
        "trusted_apps": [
            {"login": a.get("login"), "owner": a.get("owner")}
            for a in trusted_security_apps
        ],
    }
    proof = _proof(harvest, pr_head_sha=pr["head_sha"])
    proof_status = _proof_status(proof)
    if proof_status in STALE_PROOF_STATUSES:
        _append_once(blockers, "PROOF_STALE")
    elif proof_status in MISSING_PROOF_STATUSES:
        _append_once(blockers, "PROOF_MISSING")
    elif (
        proof_status == "CURRENT_WITH_SELF_REFERENCE_EXCEPTION"
        and not _valid_self_reference_exception(
            proof,
            changed_files=snapshot_changed_files,
            embedded_audit_status=audit_status,
        )
    ):
        _append_once(blockers, "PROOF_STALE_OR_MISSING")
    if not proof["proof_head_sha"]:
        _append_once(unknowns, "Proof head SHA missing")

    proof_status_str = str(
        proof_status.get("status") if isinstance(proof_status, dict) else proof_status
        or ""
    )

    # Org-owned GitHub App path: re-evaluate with full gate context.
    if security_classification.required and any(
        str(b).startswith("SECURITY_RELEASE_") for b in blockers
    ):
        app_gate_ok = compute_app_gate_ok(
            audit_status=str(audit_status or ""),
            proof_status=proof_status_str,
            blockers=blockers,
            unclassified_review_item_count=unclassified_count,
        )
        app_errors = evaluate_security_release_approval(
            harvest.get("security_release_approval"),
            required=True,
            expected_repo=repo,
            expected_pr=pr_number,
            expected_head_sha=pr["head_sha"],
            trusted_approvers=trusted_security_approvers,
            trusted_apps=trusted_security_apps,
            app_gate_ok=app_gate_ok,
        )
        if not app_errors:
            blockers[:] = [
                b for b in blockers if not str(b).startswith("SECURITY_RELEASE_")
            ]
            security_release_errors = []
            security_release["approved"] = True
            security_release["approval_kind"] = "github_app"
            security_release["approval"] = harvest.get("security_release_approval")
        else:
            # Replace prior security blockers with latest evaluation (may include
            # APP_GATES_NOT_MET / APP_UNKNOWN while preserving REQUIRED).
            blockers[:] = [
                b for b in blockers if not str(b).startswith("SECURITY_RELEASE_")
            ]
            for err in app_errors:
                _append_once(blockers, err)
            security_release_errors = list(app_errors)

    # Solo-owner path (ADR-DMX-PRSTEWARD-SOLOOWNER-001): only after ordinary
    # human/app approval failed, and only when every non-security gate is clean.
    if security_classification.required and any(
        str(b).startswith("SECURITY_RELEASE_") for b in blockers
    ):
        raw_audit = harvest.get("embedded_audit") or {}
        audit_meta = {
            "auditor_tool": raw_audit.get("auditor_tool"),
            "auditor_model": raw_audit.get("auditor_model"),
            "auditor_provider": raw_audit.get("auditor_provider"),
            "auditor_runner": raw_audit.get("auditor_runner"),
            "auditor_session": raw_audit.get("auditor_session"),
            "invocation": raw_audit.get("invocation"),
            "report_path": raw_audit.get("report_path")
            or embedded_audit.get("report_path"),
        }
        solo = evaluate_solo_owner_security_release(
            required=True,
            trusted_approvers=trusted_security_approvers,
            pr_author=str(pr["author"] or ""),
            pr_author_association=pr_assoc,
            expected_repo=repo,
            expected_pr=pr_number,
            expected_head_sha=str(pr["head_sha"] or ""),
            issue_comments=issue_comments_in,
            blockers=blockers,
            unclassified_review_item_count=unclassified_count,
            audit_status=str(audit_status or ""),
            audit_meta=audit_meta,
            proof_status=proof_status_str,
        )
        if solo.activated and solo.receipt is not None:
            blockers[:] = [
                b for b in blockers if not str(b).startswith("SECURITY_RELEASE_")
            ]
            security_release_errors = []
            security_release["approved"] = True
            security_release["solo_owner_override"] = solo.receipt
            # Never fabricate a GitHub APPROVED review object.
            security_release["approval"] = None
            security_release["approval_kind"] = "solo_owner_phrase"
            security_release["override_receipt_code"] = solo.receipt["receipt_code"]
        elif solo.diagnostic_errors:
            # Preserve ordinary SECURITY_RELEASE_* blockers; attach diagnostics as unknowns.
            for diag in solo.diagnostic_errors:
                if not str(diag).startswith("SECURITY_RELEASE_"):
                    _append_once(unknowns, f"solo_owner:{diag}")

    if security_release["approved"] and security_release.get("approval_kind") is None:
        security_release["approval_kind"] = "human_review"

    readiness = _readiness(blockers)
    tier = _risk_tier(readiness)
    review_item_ledger = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated,
        "pr_number": pr_number,
        "items": review_items,
        "unclassified_count": unclassified_count,
        "mutation_performed": False,
    }
    thread_payload = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated,
        "pr_number": pr_number,
        "threads": thread_dispositions,
        "unresolved_blocking_count": sum(
            1 for thread in thread_dispositions if thread["blocking"]
        ),
        "mutation_performed": False,
    }
    ci_triage = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated,
        "pr_number": pr_number,
        "head_sha": pr["head_sha"],
        "checks": checks["checks"],
        "required_check_count": checks["required_check_count"],
        "failed_required_count": checks["failed_required_count"],
        "pending_required_count": checks["pending_required_count"],
        "unknown_required_count": checks["unknown_required_count"],
        "mutation_performed": False,
    }
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated,
        "repo": repo,
        "pr_number": pr_number,
        "harvest_complete": bool(harvest.get("harvest_complete", False)),
        "harvest_errors": [str(item) for item in harvest.get("harvest_errors") or []],
        "mutation_performed": False,
        "pr": pr,
        "changed_files": snapshot_changed_files,
        "commits": _commits(harvest.get("commits") or []),
        "reviews": _raw_list(harvest.get("reviews") or []),
        "review_comments": _raw_list(harvest.get("review_comments") or []),
        "review_threads": _raw_list(harvest.get("review_threads") or []),
        "issue_comments": _raw_list(harvest.get("issue_comments") or []),
        "checks": checks["checks"],
        "embedded_audit": embedded_audit,
        "proof": proof,
        "blockers": blockers,
    }
    merge_readiness = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated,
        "pr": {
            "number": pr["number"],
            "url": pr["url"],
            "base_ref": pr["base_ref"],
            "head_ref": pr["head_ref"],
            "head_sha": pr["head_sha"],
            "changed_files": [item["path"] for item in snapshot["changed_files"]],
            "commits": [item["sha"] for item in snapshot["commits"]],
        },
        "readiness": readiness,
        "risk_tier": tier,
        "review_item_ledger_path": "REVIEW_ITEM_LEDGER.json",
        "thread_dispositions_path": "THREAD_DISPOSITIONS.json",
        "ci_triage_path": "CI_TRIAGE.json",
        "embedded_audit": embedded_audit,
        "proof": proof,
        "security_release": security_release,
        "blockers": blockers,
        "unknowns": unknowns,
        "mutation_performed": False,
    }
    summary = _summary(merge_readiness)
    return {
        "PR_STATE_SNAPSHOT.json": snapshot,
        "REVIEW_ITEM_LEDGER.json": review_item_ledger,
        "THREAD_DISPOSITIONS.json": thread_payload,
        "CI_TRIAGE.json": ci_triage,
        "MERGE_READINESS.json": merge_readiness,
        "PR_STEWARD_SUMMARY.md": summary,
    }


def _classify_reviews(
    reviews: list[Any],
    *,
    known_reviewers: set[str],
    trusted_associations: set[str],
    blockers: list[str],
    unknowns: list[str],
) -> list[dict[str, Any]]:
    items = []
    for index, review in enumerate(reviews):
        if not isinstance(review, dict):
            item_id = f"review-{index}"
            _append_once(blockers, "HARVEST_INCOMPLETE")
            _append_once(
                unknowns, f"Malformed review entry at index {index} (not a mapping)."
            )
            items.append(
                _review_item(
                    item_id=item_id,
                    source="review",
                    author="unknown",
                    association=None,
                    body="",
                    disposition=UNCLASSIFIED_ITEM_DISPOSITION,
                    blocking=True,
                    blockers=["HARVEST_INCOMPLETE"],
                    rationale="Review entry is not a mapping.",
                )
            )
            continue
        author = _author_login(review)
        association = _association(review)
        body = str(review.get("body") or "")
        review_id = str(review.get("id") or f"review-{index}")
        item_blockers: list[str] = []
        if not _known_author(author, association, known_reviewers, trusted_associations):
            disposition = "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"
            blocking = True
            rationale = "Reviewer is not in known reviewer config."
            item_blockers.append("UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION")
            _append_once(blockers, "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION")
            _append_once(unknowns, f"Unknown reviewer: {author}")
        elif str(review.get("state") or "").upper() in {
            "CHANGES_REQUESTED",
            "REQUEST_CHANGES",
        }:
            disposition = "MUST_FIX"
            blocking = True
            rationale = "Review requested changes."
            item_blockers.append("REQUEST_CHANGES")
            _append_once(blockers, "REQUEST_CHANGES")
        else:
            disposition, blocking, rationale = _body_disposition(body)
            if blocking:
                if disposition == "NEEDS_SUPERVISOR":
                    item_blockers.append("REVIEW_ITEM_NEEDS_SUPERVISOR")
                elif disposition == "MUST_FIX":
                    item_blockers.append("REVIEW_ITEM_MUST_FIX")
                _append_disposition_blocker(blockers, disposition)
        items.append(
            _review_item(
                item_id=review_id,
                source="review",
                author=author,
                association=association,
                body=body,
                disposition=disposition,
                blocking=blocking,
                blockers=item_blockers,
                rationale=rationale,
            )
        )
    return items


def _classify_comments(
    comments: list[Any],
    *,
    source: str,
    known_reviewers: set[str],
    trusted_associations: set[str],
    blockers: list[str],
    unknowns: list[str],
    resolved_review_comment_dispositions: dict[str, dict[str, str | bool]] | None = None,
) -> list[dict[str, Any]]:
    items = []
    resolved_review_comment_dispositions = resolved_review_comment_dispositions or {}
    for index, comment in enumerate(comments):
        if not isinstance(comment, dict):
            item_id = f"{source}-{index}"
            _append_once(blockers, "HARVEST_INCOMPLETE")
            _append_once(
                unknowns, f"Malformed {source} entry at index {index} (not a mapping)."
            )
            items.append(
                _review_item(
                    item_id=item_id,
                    source=source,
                    author="unknown",
                    association=None,
                    body="",
                    disposition=UNCLASSIFIED_ITEM_DISPOSITION,
                    blocking=True,
                    blockers=["HARVEST_INCOMPLETE"],
                    rationale=f"{source} entry is not a mapping.",
                )
            )
            continue
        author = _author_login(comment)
        association = _association(comment)
        body = str(comment.get("body") or "")
        item_id = str(comment.get("id") or f"{source}-{index}")
        item_blockers: list[str] = []
        linked_resolution = resolved_review_comment_dispositions.get(item_id)
        if linked_resolution is not None:
            disposition = str(linked_resolution["disposition"])
            blocking = bool(linked_resolution["blocking"])
            rationale = str(linked_resolution["rationale"])
        elif not _known_author(author, association, known_reviewers, trusted_associations):
            disposition = "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"
            blocking = True
            rationale = "Comment author is not in known reviewer config."
            item_blockers.append("UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION")
            _append_once(blockers, "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION")
            _append_once(unknowns, f"Unknown {source} author: {author}")
        else:
            disposition, blocking, rationale = _body_disposition(body)
            if blocking:
                if disposition == "NEEDS_SUPERVISOR":
                    item_blockers.append("REVIEW_ITEM_NEEDS_SUPERVISOR")
                elif disposition == "MUST_FIX":
                    item_blockers.append("REVIEW_ITEM_MUST_FIX")
                _append_disposition_blocker(blockers, disposition)
        items.append(
            _review_item(
                item_id=item_id,
                source=source,
                author=author,
                association=association,
                body=body,
                disposition=disposition,
                blocking=blocking,
                blockers=item_blockers,
                rationale=rationale,
            )
        )
    return items


def _classify_threads(
    threads: list[Any],
    *,
    known_reviewers: set[str],
    trusted_associations: set[str],
    blockers: list[str],
    unknowns: list[str],
) -> dict[str, list[dict[str, Any]]]:
    items: list[dict[str, Any]] = []
    dispositions: list[dict[str, Any]] = []
    for thread_index, thread in enumerate(threads):
        if not isinstance(thread, dict):
            thread_id = f"thread-{thread_index}"
            _append_once(blockers, "HARVEST_INCOMPLETE")
            _append_once(
                unknowns,
                f"Malformed review_thread entry at index {thread_index} (not a mapping).",
            )
            items.append(
                _review_item(
                    item_id=thread_id,
                    source="review_thread",
                    author="unknown",
                    association=None,
                    body="",
                    disposition=UNCLASSIFIED_ITEM_DISPOSITION,
                    blocking=True,
                    blockers=["HARVEST_INCOMPLETE"],
                    rationale="Thread entry is not a mapping.",
                )
            )
            dispositions.append(
                {
                    "thread_id": thread_id,
                    "is_resolved": False,
                    "review_item_ids": [thread_id],
                    "disposition": UNCLASSIFIED_ITEM_DISPOSITION,
                    "blocking": True,
                    "rationale": "Thread entry is not a mapping.",
                }
            )
            continue
        thread_id = str(thread.get("id") or f"thread-{thread_index}")
        is_resolved = bool(thread.get("isResolved", False))
        is_outdated = bool(thread.get("isOutdated", False))
        raw_comments = thread.get("comments")
        if not isinstance(raw_comments, list):
            item_id = f"{thread_id}-comments-malformed"
            _append_once(blockers, "HARVEST_INCOMPLETE")
            _append_once(
                unknowns,
                f"Malformed review_thread.comments for {thread_id} (not a list).",
            )
            items.append(
                _review_item(
                    item_id=item_id,
                    source="review_thread",
                    author="unknown",
                    association=None,
                    body="",
                    disposition=UNCLASSIFIED_ITEM_DISPOSITION,
                    blocking=True,
                    blockers=["HARVEST_INCOMPLETE"],
                    rationale="Thread comments container is not a list.",
                )
            )
            dispositions.append(
                {
                    "thread_id": thread_id,
                    "is_resolved": is_resolved,
                    "review_item_ids": [item_id],
                    "disposition": UNCLASSIFIED_ITEM_DISPOSITION,
                    "blocking": True,
                    "rationale": "Thread comments container is not a list.",
                }
            )
            continue
        comments = raw_comments
        review_item_ids: list[str] = []
        unknown_author = False
        has_malformed_comment = False
        for comment_index, comment in enumerate(comments):
            if not isinstance(comment, dict):
                item_id = f"{thread_id}-comment-{comment_index}"
                review_item_ids.append(item_id)
                has_malformed_comment = True
                _append_once(blockers, "HARVEST_INCOMPLETE")
                _append_once(
                    unknowns,
                    f"Malformed review_thread comment at {thread_id}[{comment_index}] "
                    "(not a mapping).",
                )
                items.append(
                    _review_item(
                        item_id=item_id,
                        source="review_thread",
                        author="unknown",
                        association=None,
                        body="",
                        disposition=UNCLASSIFIED_ITEM_DISPOSITION,
                        blocking=True,
                        blockers=["HARVEST_INCOMPLETE"],
                        rationale="Thread comment is not a mapping.",
                    )
                )
                continue
            item_id = str(comment.get("id") or f"{thread_id}-comment-{comment_index}")
            review_item_ids.append(item_id)
            author = _author_login(comment)
            association = _association(comment)
            body = str(comment.get("body") or "")
            if not _known_author(
                author, association, known_reviewers, trusted_associations
            ):
                unknown_author = True
                disposition = "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"
                blocking = True
                rationale = "Thread author is not in known reviewer config."
                _append_once(blockers, "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION")
                _append_once(unknowns, f"Unknown review_thread author: {author}")
            elif not is_resolved:
                disposition = "MUST_FIX"
                blocking = True
                rationale = "Active unresolved review thread blocks readiness."
                _append_once(blockers, "UNRESOLVED_REVIEW_THREAD")
            elif is_outdated:
                disposition = "AUTO_APPLIED"
                blocking = False
                rationale = "Resolved outdated thread is historical evidence only."
            else:
                disposition = "OPTIONAL_DEFERRED"
                blocking = False
                rationale = "Resolved thread has no active blocker."
            items.append(
                _review_item(
                    item_id=item_id,
                    source="review_thread",
                    author=author,
                    association=association,
                    body=body,
                    disposition=disposition,
                    blocking=blocking,
                    rationale=rationale,
                )
            )
        if has_malformed_comment:
            thread_disposition = UNCLASSIFIED_ITEM_DISPOSITION
            thread_blocking = True
            thread_rationale = "Thread contains a malformed comment entry."
        elif unknown_author:
            thread_disposition = "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"
            thread_blocking = True
            thread_rationale = "Thread contains an unknown author."
        elif not is_resolved:
            thread_disposition = "MUST_FIX"
            thread_blocking = True
            thread_rationale = "Unresolved review thread blocks readiness."
        elif is_outdated:
            thread_disposition = "AUTO_APPLIED"
            thread_blocking = False
            thread_rationale = "Resolved outdated thread is nonblocking evidence."
        else:
            thread_disposition = "OPTIONAL_DEFERRED"
            thread_blocking = False
            thread_rationale = "Resolved review thread is nonblocking."
        dispositions.append(
            {
                "thread_id": thread_id,
                "is_resolved": is_resolved,
                "review_item_ids": review_item_ids,
                "disposition": thread_disposition,
                "blocking": thread_blocking,
                "rationale": thread_rationale,
            }
        )
    return {"items": items, "threads": dispositions}


def _resolved_review_comment_dispositions(
    threads: list[Any],
) -> dict[str, dict[str, str | bool]]:
    dispositions: dict[str, dict[str, str | bool]] = {}
    for thread in threads:
        if not isinstance(thread, dict) or not bool(thread.get("isResolved", False)):
            continue
        raw_comments = thread.get("comments")
        if not isinstance(raw_comments, list):
            continue
        for comment in raw_comments:
            if not isinstance(comment, dict):
                continue
            comment_id = str(comment.get("id") or "")
            if not comment_id:
                continue
            dispositions[comment_id] = {
                "disposition": "AUTO_APPLIED",
                "blocking": False,
                "rationale": "Linked review thread is resolved.",
            }
    return dispositions


def _is_steward_self_status(check: dict[str, Any] | Any) -> bool:
    """True only for the exact Steward self-status context name."""
    if not isinstance(check, dict):
        return False
    name = str(check.get("name") or check.get("context") or "")
    return name == STEWARD_SELF_STATUS_CONTEXT


def _classify_checks(
    checks: list[Any], *, pr_head_sha: str, strict: bool
) -> dict[str, Any]:
    items = []
    payload_checks = []
    blockers: list[str] = []
    unknowns: list[str] = []
    required_count = 0
    failed_count = 0
    pending_count = 0
    unknown_count = 0

    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            continue
        name = str(check.get("name") or check.get("context") or f"check-{index}")
        required = bool(check.get("isRequired") is True or check.get("required") is True)
        status = _normalize_status(check.get("status") or check.get("state"))
        conclusion = _normalize_conclusion(check.get("conclusion"))
        if conclusion is None and check.get("state") == "FAILURE":
            conclusion = "failure"
        url = check.get("detailsUrl") or check.get("targetUrl") or check.get("url")
        head_sha = str(check.get("headSha") or check.get("head_sha") or pr_head_sha)

        # Preserve self-status in triage payload, but never let it block readiness.
        # Otherwise a failed prior publish sticky-reds the next Steward run.
        if _is_steward_self_status(check):
            payload_checks.append(
                {
                    "name": name,
                    "required": required,
                    "status": status,
                    "conclusion": conclusion,
                    "url": url,
                    "head_sha": head_sha,
                    "blocking": False,
                    "blockers": [],
                    "rationale": (
                        "Steward self-status "
                        f"{STEWARD_SELF_STATUS_CONTEXT!r} retained as harvest "
                        "evidence but excluded from readiness evaluation."
                    ),
                }
            )
            continue

        if required:
            required_count += 1

        blocking = False
        rationale = "Check is nonblocking or successful."
        check_blockers: list[str] = []
        if required and conclusion in FAILED_CHECK_CONCLUSIONS:
            blocking = True
            failed_count += 1
            rationale = "Required check did not succeed."
            check_blockers.append("FAILED_CHECK")
            _append_once(blockers, "FAILED_CHECK")
        elif required and strict and status in PENDING_CHECK_STATUSES:
            blocking = True
            pending_count += 1
            rationale = "Strict mode requires final check state."
            check_blockers.append("PENDING_CHECK")
            _append_once(blockers, "PENDING_CHECK")
        elif required and status == "unknown":
            blocking = True
            unknown_count += 1
            rationale = "Check status is unknown."
            check_blockers.append("UNKNOWN_CHECK")
            _append_once(blockers, "UNKNOWN_CHECK")
            _append_once(unknowns, f"Unknown check status: {name}")

        payload_checks.append(
            {
                "name": name,
                "required": required,
                "status": status,
                "conclusion": conclusion,
                "url": url,
                "head_sha": head_sha,
                "blocking": blocking,
                "blockers": check_blockers,
                "rationale": rationale,
            }
        )
        if blocking:
            items.append(
                _review_item(
                    item_id=f"ci-{index}-{_slug(name)}",
                    source="ci_annotation",
                    author="github-actions[bot]",
                    association=None,
                    body=f"{name}: {status}/{conclusion}",
                    disposition="MUST_FIX",
                    blocking=True,
                    blockers=check_blockers,
                    rationale=rationale,
                )
            )
    return {
        "checks": payload_checks,
        "review_items": items,
        "required_check_count": required_count,
        "failed_required_count": failed_count,
        "pending_required_count": pending_count,
        "unknown_required_count": unknown_count,
        "blockers": blockers,
        "unknowns": unknowns,
    }


_READINESS_TO_RISK: dict[str, str] = {
    "BLOCKED": "CRITICAL",
    "NEEDS_SUPERVISOR": "HIGH",
    "NEEDS_IMPLEMENTER": "MEDIUM",
    "NOT_READY": "LOW",
    "READY": "CLEAR",
}


def _readiness(blockers: list[str]) -> str:
    blocker_set = set(blockers)
    if blocker_set & {"HARVEST_INCOMPLETE", "PR_IS_DRAFT", "PR_CLOSED", "MIXED_SHA_ARTIFACT_SET"}:
        return "BLOCKED"
    if any(
        item.startswith("EMBEDDED_AUDIT_") or item.startswith("SECURITY_RELEASE_")
        for item in blocker_set
    ) or blocker_set & {
        "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION",
        "PROOF_STALE",
        "PROOF_MISSING",
        "PROOF_STALE_OR_MISSING",
        "UNKNOWN_PR_AUTHOR",
        "UNKNOWN_CHECK",
        "REVIEW_ITEM_NEEDS_SUPERVISOR",
    }:
        return "NEEDS_SUPERVISOR"
    if blocker_set & {
        "UNRESOLVED_REVIEW_THREAD",
        "FAILED_CHECK",
        "REQUEST_CHANGES",
        "REVIEW_ITEM_MUST_FIX",
    }:
        return "NEEDS_IMPLEMENTER"
    if blocker_set & {"PENDING_CHECK"}:
        return "NOT_READY"
    return "READY"


def _risk_tier(readiness: str) -> str:
    return _READINESS_TO_RISK.get(readiness, "CRITICAL")


def _pr_payload(harvest: dict[str, Any], *, pr_number: int) -> dict[str, Any]:
    raw = harvest.get("pr") or {}
    return {
        "number": int(raw.get("number") or pr_number),
        "url": str(raw.get("url") or ""),
        "state": str(raw.get("state") or "UNKNOWN"),
        "draft": bool(raw.get("isDraft", raw.get("draft", False))),
        "mergeable": raw.get("mergeable"),
        "merge_state_status": raw.get("mergeStateStatus"),
        "review_decision": raw.get("reviewDecision"),
        "base_ref": str(raw.get("baseRefName") or ""),
        "base_sha": str(raw.get("baseRefOid") or ""),
        "head_ref": str(raw.get("headRefName") or ""),
        "head_sha": str(raw.get("headRefOid") or ""),
        "author": _author_login(raw),
        "created_at": raw.get("createdAt"),
        "updated_at": raw.get("updatedAt"),
    }


def _changed_files(files: list[Any]) -> list[dict[str, Any]]:
    payload = []
    for item in files:
        payload.append(
            {
                "path": str(item.get("path") or item.get("filename") or ""),
                "additions": int(item.get("additions") or 0),
                "deletions": int(item.get("deletions") or 0),
                "status": item.get("status"),
                "previous_path": item.get("previous_path"),
            }
        )
    return payload


def _commits(commits: list[Any]) -> list[dict[str, Any]]:
    payload = []
    for item in commits:
        commit = item.get("commit") or item
        payload.append(
            {
                "sha": str(
                    commit.get("oid")
                    or commit.get("sha")
                    or item.get("oid")
                    or item.get("sha")
                    or ""
                ),
                "message": str(
                    commit.get("messageHeadline")
                    or commit.get("message")
                    or item.get("messageHeadline")
                    or ""
                ),
            }
        )
    return payload


def _embedded_audit(harvest: dict[str, Any]) -> dict[str, str]:
    raw = harvest.get("embedded_audit") or {}
    raw_status = str(raw.get("status") or "").upper()
    if raw_status in PASSING_AUDITS | BLOCKING_AUDITS:
        normalized = raw_status
        was_unknown = False
    else:
        normalized = "SKIPPED"
        was_unknown = bool(raw_status)  # only "unknown" if upstream supplied a non-empty bad value
    return {
        "status": normalized,
        "report_path": str(raw.get("report_path") or ""),
        # `_raw_status` is internal; the caller uses it to add the
        # EMBEDDED_AUDIT_UNKNOWN blocker, then strips it before serializing.
        "_raw_status": raw_status if was_unknown else "",
    }


def _detect_mixed_sha_checks(checks: list[Any], *, pr_head_sha: str) -> bool:
    for check in checks:
        if not isinstance(check, dict):
            continue
        # Self-status is Steward-published evidence, not foreign SHA noise.
        if _is_steward_self_status(check):
            continue
        raw_sha = check.get("headSha") or check.get("head_sha")
        sha = (raw_sha or "").strip() if isinstance(raw_sha, str) else ""
        if sha and sha != pr_head_sha:
            return True
    return False


def _proof(harvest: dict[str, Any], *, pr_head_sha: str | None = None) -> dict[str, Any]:
    raw = harvest.get("proof") or {}
    proof_head_sha = raw.get("proof_head_sha")
    proof_path = str(raw.get("proof_path") or "")
    matches = (
        bool(proof_head_sha and proof_head_sha == pr_head_sha)
        if pr_head_sha
        else bool(raw.get("matches_pr_head", False))
    )
    raw_freshness = raw.get("proof_freshness")
    self_reference_exception = (
        raw_freshness.get("self_reference_exception")
        if isinstance(raw_freshness, dict)
        and isinstance(raw_freshness.get("self_reference_exception"), dict)
        else None
    )
    if isinstance(raw_freshness, dict):
        raw_status = str(raw_freshness.get("status") or "UNKNOWN")
        if raw_status == "CURRENT_WITH_SELF_REFERENCE_EXCEPTION" and not matches:
            freshness = _proof_freshness_payload(
                status=raw_status,
                proof_head_sha=proof_head_sha,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof freshness requires self-reference exception validation.",
            )
            freshness["self_reference_exception"] = self_reference_exception
        elif not proof_head_sha and not proof_path:
            freshness = _proof_freshness_payload(
                status="MISSING",
                proof_head_sha=None,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof file was not provided.",
            )
        elif not proof_head_sha:
            freshness = _proof_freshness_payload(
                status="MISSING",
                proof_head_sha=None,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof head SHA missing.",
            )
        elif matches:
            freshness = _proof_freshness_payload(
                status="CURRENT",
                proof_head_sha=proof_head_sha,
                pr_head_sha=pr_head_sha,
                matches=True,
                reason="Proof head SHA matches PR head SHA.",
            )
        else:
            freshness = _proof_freshness_payload(
                status="STALE",
                proof_head_sha=proof_head_sha,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof head SHA does not match PR head SHA.",
            )
    elif isinstance(raw_freshness, str) and raw_freshness:
        if not proof_head_sha and not proof_path:
            freshness = _proof_freshness_payload(
                status="MISSING",
                proof_head_sha=None,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof file was not provided.",
            )
        elif not proof_head_sha:
            freshness = _proof_freshness_payload(
                status="MISSING",
                proof_head_sha=None,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof head SHA missing.",
            )
        elif matches:
            freshness = _proof_freshness_payload(
                status="CURRENT",
                proof_head_sha=proof_head_sha,
                pr_head_sha=pr_head_sha,
                matches=True,
                reason="Proof head SHA matches PR head SHA.",
            )
        else:
            freshness = _proof_freshness_payload(
                status="STALE",
                proof_head_sha=proof_head_sha,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof head SHA does not match PR head SHA.",
            )
    else:
        if not proof_head_sha and not proof_path:
            freshness = _proof_freshness_payload(
                status="MISSING",
                proof_head_sha=None,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof file was not provided.",
            )
        elif not proof_head_sha:
            # proof_path present but no verifiable SHA — cannot confirm freshness, treat as MISSING.
            freshness = _proof_freshness_payload(
                status="MISSING",
                proof_head_sha=None,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof head SHA missing.",
            )
        elif proof_head_sha and matches:
            freshness = _proof_freshness_payload(
                status="CURRENT",
                proof_head_sha=proof_head_sha,
                pr_head_sha=pr_head_sha,
                matches=True,
                reason="Proof head SHA matches PR head SHA.",
            )
        else:
            freshness = _proof_freshness_payload(
                status="STALE",
                proof_head_sha=proof_head_sha,
                pr_head_sha=pr_head_sha,
                matches=False,
                reason="Proof head SHA does not match PR head SHA.",
            )
    return {
        "proof_path": proof_path,
        "proof_head_sha": proof_head_sha,
        "matches_pr_head": matches,
        "proof_freshness": freshness,
    }


def _proof_freshness_payload(
    *,
    status: str,
    proof_head_sha: str | None,
    pr_head_sha: str | None,
    matches: bool,
    reason: str = "",
) -> ProofFreshness:
    normalized = "CURRENT" if status == "FRESH" else status
    return ProofFreshness(
        {
            "status": normalized,
            "matches_pr_head": matches,
            "reason": reason,
            "proof_recorded_sha": proof_head_sha,
            "pr_head_sha": pr_head_sha,
            "self_reference_exception": None,
        }
    )


def _proof_status(proof: dict[str, Any]) -> str:
    freshness = proof.get("proof_freshness")
    if isinstance(freshness, dict):
        return str(freshness.get("status") or "UNKNOWN")
    if freshness == "FRESH":
        return "CURRENT"
    return str(freshness or "UNKNOWN")


def _valid_self_reference_exception(
    proof: dict[str, Any],
    *,
    changed_files: list[dict[str, Any]],
    embedded_audit_status: str,
) -> bool:
    freshness = proof.get("proof_freshness")
    if not isinstance(freshness, dict):
        return False
    exception = freshness.get("self_reference_exception")
    if not isinstance(exception, dict):
        return False
    if exception.get("supervisor_accepted") is not True:
        return False
    if embedded_audit_status not in PASSING_AUDITS:
        return False
    changed_paths = sorted(
        {str(item.get("path") or "") for item in changed_files if item.get("path")}
    )
    exception_paths = sorted(
        {str(item) for item in exception.get("changed_files") or [] if item}
    )
    if not changed_paths or changed_paths != exception_paths:
        return False
    return all(path.startswith("proof/") for path in changed_paths)


def _body_disposition(body: str) -> tuple[str, bool, str]:
    lowered = body.lower()
    if re.search(r"\bp1\b", lowered):
        return "MUST_FIX", True, "P1 review item blocks readiness."
    if re.search(r"\bp2\b", lowered):
        return "MUST_FIX", True, "P2 review item blocks unless documented nonblocking."
    if "needs supervisor" in lowered:
        return "NEEDS_SUPERVISOR", True, "Comment requests supervisor review."
    if "out of scope" in lowered or "follow-up" in lowered:
        return (
            "OUT_OF_SCOPE_FOLLOWUP",
            False,
            "Comment is explicitly documented as follow-up.",
        )
    if "rejected" in lowered and "reason" in lowered:
        return "REJECTED_WITH_REASON", False, "Comment records a rejected item."
    return "OPTIONAL_DEFERRED", False, "Known author comment is classified nonblocking."


def _append_disposition_blocker(blockers: list[str], disposition: str) -> None:
    if disposition == "NEEDS_SUPERVISOR":
        _append_once(blockers, "REVIEW_ITEM_NEEDS_SUPERVISOR")
    elif disposition == "MUST_FIX":
        _append_once(blockers, "REVIEW_ITEM_MUST_FIX")


def _review_item(
    *,
    item_id: str,
    source: str,
    author: str,
    association: str | None,
    body: str,
    disposition: str,
    blocking: bool,
    rationale: str,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": item_id,
        "source": source,
        "author": author,
        "association": association,
        "body": body,
        "disposition": disposition,
        "blocking": blocking,
        "blockers": blockers or [],
        "rationale": rationale,
    }



def _normalize_bot_login(login: str) -> str:
    """Canonicalize a GitHub bot login by dropping app/ prefix for dependabot or [bot] suffix.

    GitHub renders the same bot identity inconsistently across APIs/UI
    (``app/dependabot`` vs ``dependabot`` vs ``dependabot[bot]``); comparing
    on the normalized form avoids needing a literal roster entry per variant.
    """
    if login in ("app/dependabot", "app/dependabot[bot]"):
        return "dependabot"
    return login[: -len("[bot]")] if login.endswith("[bot]") else login


def _known_author(
    author: str,
    association: str | None,
    known_reviewers: set[str],
    trusted_associations: set[str],
) -> bool:
    if str(association or "").upper() in trusted_associations:
        return True
    # Only the candidate login is normalized, never the roster: a roster entry
    # stored as "foo[bot]" must not also match a bare human login "foo" that
    # happens to reclaim the un-suffixed name.
    # API variants that omit "[bot]" (e.g. ddd-release-gate review author) must
    # be listed explicitly as bare logins in known_reviewers.json.
    return author in known_reviewers or _normalize_bot_login(author) in known_reviewers


def _author_login(payload: dict[str, Any]) -> str:
    author = payload.get("author")
    if isinstance(author, dict):
        return str(author.get("login") or "unknown")
    return str(payload.get("login") or "unknown")


def _association(payload: dict[str, Any]) -> str | None:
    value = payload.get("authorAssociation") or payload.get("author_association")
    if value is None:
        return None
    return str(value)


def _normalize_status(value: Any) -> str:
    status = str(value or "unknown").lower()
    return {
        "completed": "completed",
        "success": "completed",
        "failure": "completed",
        "queued": "queued",
        "in_progress": "in_progress",
        "requested": "requested",
        "waiting": "waiting",
        "pending": "pending",
    }.get(status, "unknown")


def _normalize_conclusion(value: Any) -> str | None:
    if value is None:
        return None
    conclusion = str(value).lower()
    if conclusion == "success":
        return "success"
    if conclusion == "failure":
        return "failure"
    return conclusion


def _excerpt(body: str) -> str:
    return re.sub(r"\s+", " ", body).strip()[:240]


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower() or "check"


def _ensure_list(
    value: Any, *, label: str, blockers: list[str], unknowns: list[str]
) -> list[Any]:
    """Normalize a harvest field to a list, blocking on a present-but-wrong type.

    A missing field (None) is normal harvest shape and yields an empty list
    silently; a field that is present but not a list is a malformed harvest
    and must block readiness rather than crash or silently drop data.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return value
    _append_once(blockers, "HARVEST_INCOMPLETE")
    _append_once(
        unknowns, f"Harvest field {label!r} is not a list (got {type(value).__name__})."
    )
    return []


def _review_source_item_count(
    *,
    reviews: list[Any],
    issue_comments: list[Any],
    review_comments: list[Any],
    review_threads: list[Any],
) -> int:
    """Expected review-ledger item count, mirroring the classify_* item yield.

    Each raw entry in reviews/issue_comments/review_comments yields exactly
    one ledger item. Each review_thread yields one item per comment (or a
    single unclassified item if the thread or its comments container is
    malformed) — this must stay in lockstep with `_classify_threads`.
    """
    count = len(reviews) + len(issue_comments) + len(review_comments)
    for thread in review_threads:
        if not isinstance(thread, dict):
            count += 1
            continue
        comments = thread.get("comments")
        count += len(comments) if isinstance(comments, list) else 1
    return count


def _append_once(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _extend_once(items: list[str], values: list[str]) -> None:
    for value in values:
        _append_once(items, value)


def _raw_list(items: list[Any]) -> list[dict[str, Any]]:
    return [item for item in items if isinstance(item, dict)]


def _summary(readiness: dict[str, Any]) -> str:
    blockers = readiness["blockers"] or ["none"]
    unknowns = readiness["unknowns"] or ["none"]
    blocker_lines = "\n".join(f"- {item}" for item in blockers)
    unknown_lines = "\n".join(f"- {item}" for item in unknowns)
    return (
        "# PR Steward Summary\n\n"
        f"- PR: {readiness['pr']['number']}\n"
        f"- readiness: {readiness['readiness']}\n"
        f"- risk_tier: {readiness['risk_tier']}\n"
        "- mutation_performed: false\n\n"
        "## Blockers\n\n"
        f"{blocker_lines}\n\n"
        "## UNKNOWN\n\n"
        f"{unknown_lines}\n"
    )
