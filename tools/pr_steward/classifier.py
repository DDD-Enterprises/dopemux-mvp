from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_known_reviewers(path: Path) -> tuple[set[str], set[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    reviewers = {str(item) for item in payload.get("known_reviewers", [])}
    associations = {
        str(item).upper() for item in payload.get("trusted_author_associations", [])
    }
    return reviewers, associations


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
    checks = _classify_checks(
        harvest.get("checks") or [],
        pr_head_sha=pr["head_sha"],
        strict=strict,
    )

    blockers: list[str] = []
    unknowns: list[str] = []
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
            harvest.get("reviews") or [],
            known_reviewers=known_reviewers,
            trusted_associations=trusted_associations,
            blockers=blockers,
            unknowns=unknowns,
        )
    )
    review_items.extend(
        _classify_comments(
            harvest.get("review_comments") or [],
            source="review_comment",
            known_reviewers=known_reviewers,
            trusted_associations=trusted_associations,
            blockers=blockers,
            unknowns=unknowns,
        )
    )
    review_items.extend(
        _classify_comments(
            harvest.get("issue_comments") or [],
            source="issue_comment",
            known_reviewers=known_reviewers,
            trusted_associations=trusted_associations,
            blockers=blockers,
            unknowns=unknowns,
        )
    )

    thread_result = _classify_threads(
        harvest.get("review_threads") or [],
        known_reviewers=known_reviewers,
        trusted_associations=trusted_associations,
        blockers=blockers,
        unknowns=unknowns,
    )
    review_items.extend(thread_result["items"])
    thread_dispositions.extend(thread_result["threads"])

    review_items.extend(checks["review_items"])

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

    proof = _proof(harvest)
    if proof["proof_freshness"] == "STALE":
        _append_once(blockers, "PROOF_STALE")
    elif proof["proof_freshness"] == "MISSING":
        _append_once(blockers, "PROOF_MISSING")
    if not proof["proof_head_sha"]:
        _append_once(unknowns, "Proof head SHA missing")

    readiness = _readiness(blockers)
    tier = _risk_tier(readiness)
    review_item_ledger = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated,
        "pr_number": pr_number,
        "items": review_items,
        "unclassified_count": 0,
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
        "changed_files": _changed_files(harvest.get("changed_files") or []),
        "commits": _commits(harvest.get("commits") or []),
        "reviews": _raw_list(harvest.get("reviews") or []),
        "review_comments": _raw_list(harvest.get("review_comments") or []),
        "review_threads": _raw_list(harvest.get("review_threads") or []),
        "issue_comments": _raw_list(harvest.get("issue_comments") or []),
        "checks": checks["checks"],
        "embedded_audit": embedded_audit,
        "proof": proof,
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
        author = _author_login(review)
        association = _association(review)
        body = str(review.get("body") or "")
        review_id = str(review.get("id") or f"review-{index}")
        if not _known_author(author, association, known_reviewers, trusted_associations):
            disposition = "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"
            blocking = True
            rationale = "Reviewer is not in known reviewer config."
            _append_once(blockers, "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION")
            _append_once(unknowns, f"Unknown reviewer: {author}")
        elif str(review.get("state") or "").upper() in {
            "CHANGES_REQUESTED",
            "REQUEST_CHANGES",
        }:
            disposition = "MUST_FIX"
            blocking = True
            rationale = "Review requested changes."
            _append_once(blockers, "REQUEST_CHANGES")
        else:
            disposition, blocking, rationale = _body_disposition(body)
            if blocking:
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
) -> list[dict[str, Any]]:
    items = []
    for index, comment in enumerate(comments):
        author = _author_login(comment)
        association = _association(comment)
        body = str(comment.get("body") or "")
        item_id = str(comment.get("id") or f"{source}-{index}")
        if not _known_author(author, association, known_reviewers, trusted_associations):
            disposition = "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"
            blocking = True
            rationale = "Comment author is not in known reviewer config."
            _append_once(blockers, "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION")
            _append_once(unknowns, f"Unknown {source} author: {author}")
        else:
            disposition, blocking, rationale = _body_disposition(body)
            if blocking:
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
        thread_id = str(thread.get("id") or f"thread-{thread_index}")
        is_resolved = bool(thread.get("isResolved", False))
        is_outdated = bool(thread.get("isOutdated", False))
        comments = thread.get("comments") or []
        review_item_ids: list[str] = []
        unknown_author = False
        for comment_index, comment in enumerate(comments):
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
        if unknown_author:
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
        name = str(check.get("name") or check.get("context") or f"check-{index}")
        required = bool(check.get("isRequired") is True or check.get("required") is True)
        if required:
            required_count += 1
        status = _normalize_status(check.get("status") or check.get("state"))
        conclusion = _normalize_conclusion(check.get("conclusion"))
        url = check.get("detailsUrl") or check.get("targetUrl") or check.get("url")
        head_sha = str(check.get("headSha") or check.get("head_sha") or pr_head_sha)

        blocking = False
        rationale = "Check is nonblocking or successful."
        if required and conclusion in FAILED_CHECK_CONCLUSIONS:
            blocking = True
            failed_count += 1
            rationale = "Required check did not succeed."
            _append_once(blockers, "FAILED_CHECK")
        elif required and strict and status in PENDING_CHECK_STATUSES:
            blocking = True
            pending_count += 1
            rationale = "Strict mode requires final check state."
            _append_once(blockers, "PENDING_CHECK")
        elif required and status == "unknown":
            blocking = True
            unknown_count += 1
            rationale = "Check status is unknown."
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
        item.startswith("EMBEDDED_AUDIT_")
        for item in blocker_set
    ) or blocker_set & {
        "UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION",
        "PROOF_STALE",
        "PROOF_MISSING",
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
        raw_sha = check.get("headSha") or check.get("head_sha")
        sha = (raw_sha or "").strip() if isinstance(raw_sha, str) else ""
        if sha and sha != pr_head_sha:
            return True
    return False


def _proof(harvest: dict[str, Any]) -> dict[str, Any]:
    raw = harvest.get("proof") or {}
    proof_head_sha = raw.get("proof_head_sha")
    proof_path = str(raw.get("proof_path") or "")
    matches = bool(raw.get("matches_pr_head", False))
    if not proof_head_sha and not proof_path:
        freshness = "MISSING"
    elif not proof_head_sha:
        # proof_path present but no verifiable SHA — cannot confirm freshness, treat as MISSING.
        freshness = "MISSING"
    elif proof_head_sha and matches:
        freshness = "FRESH"
    else:
        freshness = "STALE"
    return {
        "proof_path": proof_path,
        "proof_head_sha": proof_head_sha,
        "matches_pr_head": matches,
        "proof_freshness": freshness,
    }


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
) -> dict[str, Any]:
    return {
        "id": item_id,
        "source": source,
        "author": author,
        "author_association": association,
        "body_excerpt": _excerpt(body),
        "disposition": disposition,
        "blocking": blocking,
        "rationale": rationale,
    }


def _known_author(
    author: str,
    association: str | None,
    known_reviewers: set[str],
    trusted_associations: set[str],
) -> bool:
    return author in known_reviewers or str(association or "").upper() in trusted_associations


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
