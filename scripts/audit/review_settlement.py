#!/usr/bin/env python3
"""Fetch and evaluate exact-head PR review settlement deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
FINAL_READINESS_CONTEXT = "PR Steward / final readiness"
INVALIDATION_WRITER_NAME = "PR readiness invalidation writer"
INVALIDATION_WRITER_PATH = ".github/workflows/pr-readiness-invalidation-writer.yml"


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _review_time(review: dict[str, Any]) -> datetime | None:
    for field in ("updated_at", "submitted_at"):
        value = review.get(field)
        if value:
            return _parse_time(str(value))
    return None


def _canonical_facts(snapshot: dict[str, Any]) -> dict[str, Any]:
    latest_by_author: dict[str, dict[str, Any]] = {}
    for index, review in enumerate(snapshot.get("reviews") or []):
        author = str(review.get("author") or "")
        when = _review_time(review)
        if not author or when is None:
            continue
        candidate = {
            "author": author,
            "state": review.get("state"),
            "submitted_at": review.get("submitted_at"),
            "updated_at": review.get("updated_at"),
            "sort_key": (when.isoformat(), index),
        }
        previous = latest_by_author.get(author)
        if previous is None or candidate["sort_key"] >= previous["sort_key"]:
            latest_by_author[author] = candidate

    latest_reviews = []
    for author in sorted(latest_by_author):
        review = dict(latest_by_author[author])
        review.pop("sort_key")
        latest_reviews.append(review)

    threads = []
    for thread in snapshot.get("threads") or []:
        comments = [
            {
                "id": comment.get("id"),
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at"),
            }
            for comment in thread.get("comments") or []
        ]
        comments.sort(
            key=lambda item: (
                str(item.get("created_at") or ""),
                str(item.get("updated_at") or ""),
                str(item.get("id") or ""),
            )
        )
        threads.append(
            {
                "id": thread.get("id"),
                "is_resolved": thread.get("is_resolved"),
                "comments": comments,
            }
        )
    threads.sort(key=lambda item: str(item.get("id") or ""))

    source = snapshot.get("latest_trusted_invalidation_source")
    trusted_source = None
    if isinstance(source, dict):
        trusted_source = {
            "repository": source.get("repository"),
            "workflow_run_id": source.get("workflow_run_id"),
            "workflow_name": source.get("workflow_name"),
            "workflow_path": source.get("workflow_path"),
            "status_context": source.get("status_context"),
            "status_state": source.get("status_state"),
        }

    return {
        "repository": snapshot.get("repository"),
        "pr_number": snapshot.get("pr_number"),
        "state": snapshot.get("state"),
        "is_draft": snapshot.get("is_draft"),
        "merged": snapshot.get("merged"),
        "created_at": snapshot.get("created_at"),
        "head_sha": snapshot.get("head_sha"),
        "review_decision": snapshot.get("review_decision"),
        "ready_events_complete": snapshot.get("ready_events_complete"),
        "review_events_complete": snapshot.get("review_events_complete"),
        "thread_events_complete": snapshot.get("thread_events_complete"),
        "review_comment_events_complete": snapshot.get(
            "review_comment_events_complete"
        ),
        "ready_events": sorted(
            str(value) for value in snapshot.get("ready_events") or []
        ),
        "latest_trusted_invalidation_at": snapshot.get(
            "latest_trusted_invalidation_at"
        ),
        "latest_trusted_invalidation_source": trusted_source,
        "trusted_invalidation_time_unknown": bool(
            snapshot.get("trusted_invalidation_time_unknown")
        ),
        "latest_reviews": latest_reviews,
        "threads": threads,
    }


def _trusted_invalidation_source_valid(
    facts: dict[str, Any],
    *,
    expected_repo: str,
) -> bool:
    source = facts.get("latest_trusted_invalidation_source")
    if not isinstance(source, dict):
        return False
    return (
        source.get("repository") == expected_repo
        and isinstance(source.get("workflow_run_id"), int)
        and not isinstance(source.get("workflow_run_id"), bool)
        and source.get("workflow_run_id") > 0
        and source.get("workflow_name") == INVALIDATION_WRITER_NAME
        and source.get("workflow_path") == INVALIDATION_WRITER_PATH
        and source.get("status_context") == FINAL_READINESS_CONTEXT
        and source.get("status_state") == "pending"
    )


def evaluate_snapshot(
    snapshot: dict[str, Any],
    *,
    expected_repo: str,
    expected_pr: int,
    expected_head: str,
    now: datetime,
    min_ready_age_seconds: int,
    min_activity_quiet_seconds: int,
) -> dict[str, Any]:
    """Return settlement verdict and stable identity/review-state fingerprint."""
    reasons: list[str] = []
    facts = _canonical_facts(snapshot)

    if facts["repository"] != expected_repo:
        reasons.append("repository_mismatch")
    if facts["pr_number"] != expected_pr:
        reasons.append("pr_number_mismatch")
    if facts["head_sha"] != expected_head:
        reasons.append("head_sha_mismatch")
    if facts["state"] != "OPEN":
        reasons.append("pr_not_open")
    if facts["is_draft"] is not False:
        reasons.append("pr_is_draft_or_unknown")
    if facts["merged"] is not False:
        reasons.append("pr_merged_or_unknown")

    completeness = {
        "ready_events_complete": "ready_events_pagination_unknown",
        "review_events_complete": "reviews_pagination_unknown",
        "thread_events_complete": "review_threads_pagination_unknown",
        "review_comment_events_complete": "review_comments_pagination_unknown",
    }
    for field, reason in completeness.items():
        if facts[field] is not True:
            reasons.append(reason)

    ready_times = []
    for value in facts["ready_events"]:
        try:
            ready_times.append(_parse_time(value))
        except (TypeError, ValueError):
            reasons.append("ready_event_timestamp_invalid")
    if not ready_times:
        created_at = facts.get("created_at")
        if not created_at:
            reasons.append("ready_for_review_event_missing")
        else:
            try:
                ready_times.append(_parse_time(str(created_at)))
            except (TypeError, ValueError):
                reasons.append("created_at_timestamp_invalid")

    ready_age = None
    if ready_times:
        ready_age = int((now - max(ready_times)).total_seconds())
        if ready_age < min_ready_age_seconds:
            reasons.append("ready_for_review_too_recent")

    latest_reviews = facts["latest_reviews"]
    if facts["review_decision"] == "CHANGES_REQUESTED" or any(
        review.get("state") == "CHANGES_REQUESTED" for review in latest_reviews
    ):
        reasons.append("active_change_request_reviews")

    unresolved = sum(
        1 for thread in facts["threads"] if thread.get("is_resolved") is not True
    )
    if unresolved:
        reasons.append("unresolved_review_threads")

    activity_times = []
    for review in snapshot.get("reviews") or []:
        for field in ("submitted_at", "updated_at"):
            value = review.get(field)
            if value:
                try:
                    activity_times.append(_parse_time(str(value)))
                except (TypeError, ValueError):
                    reasons.append("review_timestamp_invalid")
    for thread in snapshot.get("threads") or []:
        for comment in thread.get("comments") or []:
            for field in ("created_at", "updated_at"):
                value = comment.get(field)
                if value:
                    try:
                        activity_times.append(_parse_time(str(value)))
                    except (TypeError, ValueError):
                        reasons.append("review_comment_timestamp_invalid")

    invalidation_at = facts.get("latest_trusted_invalidation_at")
    invalidation_source = facts.get("latest_trusted_invalidation_source")
    if facts["trusted_invalidation_time_unknown"]:
        reasons.append("trusted_invalidation_time_unknown")
    if invalidation_at or invalidation_source:
        if not (
            invalidation_at
            and _trusted_invalidation_source_valid(facts, expected_repo=expected_repo)
        ):
            reasons.append("trusted_invalidation_time_unknown")
        else:
            try:
                activity_times.append(_parse_time(str(invalidation_at)))
            except (TypeError, ValueError):
                reasons.append("trusted_invalidation_timestamp_invalid")

    activity_age = None
    if activity_times:
        activity_age = int((now - max(activity_times)).total_seconds())
        if activity_age < min_activity_quiet_seconds:
            reasons.append("review_activity_too_recent")

    canonical = json.dumps(facts, sort_keys=True, separators=(",", ":"))
    return {
        "marker": "REVIEW_SETTLEMENT",
        "status": "SETTLED" if not reasons else "BLOCKED",
        "repository": expected_repo,
        "pr_number": expected_pr,
        "expected_head_sha": expected_head,
        "live_head_sha": facts.get("head_sha"),
        "ready_age_seconds": ready_age,
        "review_activity_age_seconds": activity_age,
        "unresolved_review_threads": unresolved,
        "fingerprint": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "facts": facts,
        "reasons": sorted(set(reasons)),
    }


def _graphql(query: str, **variables: object) -> dict[str, Any]:
    command = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is not None:
            command.extend(["-F", f"{key}={value}"])
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"graphql_request_failed: {completed.stderr.strip()}")
    payload = json.loads(completed.stdout)
    if payload.get("errors"):
        raise RuntimeError(
            "graphql_errors: " + json.dumps(payload["errors"], sort_keys=True)
        )
    return payload


def _gh_api_json(*args: str) -> Any:
    completed = subprocess.run(
        ["gh", "api", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"gh_api_failed: {completed.stderr.strip()}")
    return json.loads(completed.stdout)


def _status_history(repo: str, head_sha: str) -> list[dict[str, Any]]:
    statuses: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = _gh_api_json(
            f"repos/{repo}/commits/{head_sha}/statuses",
            "--method",
            "GET",
            "-f",
            "per_page=100",
            "-f",
            f"page={page}",
        )
        if not isinstance(payload, list):
            raise RuntimeError("trusted_invalidation_status_payload_invalid")
        statuses.extend(item for item in payload if isinstance(item, dict))
        if len(payload) < 100:
            return statuses
        page += 1
        if page > 20:
            raise RuntimeError("trusted_invalidation_status_pagination_unknown")


def _actions_run_id_from_target_url(repo: str, target_url: object) -> int | None:
    if not isinstance(target_url, str):
        return None
    match = re.fullmatch(
        rf"https://github\.com/{re.escape(repo)}/actions/runs/([1-9][0-9]*)",
        target_url,
    )
    if not match:
        return None
    return int(match.group(1))


def _validated_invalidation_source(
    *,
    repo: str,
    run_id: int,
    status: dict[str, Any],
) -> dict[str, Any]:
    run = _gh_api_json(f"repos/{repo}/actions/runs/{run_id}")
    errors = []
    if int(run.get("id") or 0) != run_id:
        errors.append("invalidation_run_id_mismatch")
    if (run.get("repository") or {}).get("full_name") != repo:
        errors.append("invalidation_run_repository_mismatch")
    if run.get("name") != INVALIDATION_WRITER_NAME:
        errors.append("invalidation_workflow_name_mismatch")
    if run.get("path") != INVALIDATION_WRITER_PATH:
        errors.append("invalidation_workflow_path_mismatch")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        errors.append("invalidation_run_not_successfully_completed")
    if run.get("event") != "workflow_run":
        errors.append("invalidation_run_event_mismatch")
    if errors:
        raise RuntimeError("TRUSTED_INVALIDATION_TIME_UNKNOWN: " + ",".join(errors))

    return {
        "repository": repo,
        "workflow_run_id": run_id,
        "workflow_name": run.get("name"),
        "workflow_path": run.get("path"),
        "status_context": status.get("context"),
        "status_state": status.get("state"),
    }


def fetch_latest_trusted_invalidation(
    repo: str,
    head_sha: str,
) -> tuple[str | None, dict[str, Any] | None]:
    pending_statuses = [
        status
        for status in _status_history(repo, head_sha)
        if status.get("context") == FINAL_READINESS_CONTEXT
        and status.get("state") == "pending"
    ]
    if not pending_statuses:
        return None, None

    pending_statuses.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    latest = pending_statuses[0]
    created_at = latest.get("created_at")
    if not created_at:
        raise RuntimeError("TRUSTED_INVALIDATION_TIME_UNKNOWN: status_created_at_missing")
    try:
        _parse_time(str(created_at))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "TRUSTED_INVALIDATION_TIME_UNKNOWN: status_created_at_invalid"
        ) from exc
    run_id = _actions_run_id_from_target_url(repo, latest.get("target_url"))
    if run_id is None:
        raise RuntimeError("TRUSTED_INVALIDATION_TIME_UNKNOWN: status_target_url_unbound")
    source = _validated_invalidation_source(repo=repo, run_id=run_id, status=latest)
    return str(created_at), source


def _collect_connection(
    fetch_page: Callable[[str | None], dict[str, Any]],
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    cursor = None
    seen_cursors: set[str] = set()
    while True:
        connection = fetch_page(cursor)
        page_info = connection.get("pageInfo") or {}
        page_nodes = connection.get("nodes")
        if not isinstance(page_nodes, list):
            raise RuntimeError("graphql_connection_nodes_missing")
        nodes.extend(page_nodes)
        if page_info.get("hasNextPage") is False:
            return nodes
        cursor = page_info.get("endCursor")
        if not isinstance(cursor, str) or not cursor or cursor in seen_cursors:
            raise RuntimeError("graphql_pagination_incomplete")
        seen_cursors.add(cursor)


def fetch_snapshot(repo: str, pr_number: int) -> dict[str, Any]:
    """Fetch complete review facts using trusted GitHub CLI authentication."""
    owner, name = repo.split("/", 1)
    common = {"owner": owner, "name": name, "number": pr_number}
    metadata_query = """
    query($owner:String!,$name:String!,$number:Int!){
      repository(owner:$owner,name:$name){nameWithOwner pullRequest(number:$number){
        number state isDraft merged createdAt headRefOid reviewDecision
      }}
    }
    """
    metadata_payload = _graphql(metadata_query, **common)
    repository = (metadata_payload.get("data") or {}).get("repository")
    pr = (repository or {}).get("pullRequest")
    if not isinstance(repository, dict) or not isinstance(pr, dict):
        raise RuntimeError("pull_request_missing")

    ready_query = """
    query($owner:String!,$name:String!,$number:Int!,$cursor:String){
      repository(owner:$owner,name:$name){pullRequest(number:$number){
        items:timelineItems(first:100,after:$cursor,itemTypes:[READY_FOR_REVIEW_EVENT]){
          pageInfo{hasNextPage endCursor} nodes{... on ReadyForReviewEvent{createdAt}}
        }
      }}
    }
    """
    ready_nodes = _collect_connection(
        lambda cursor: (
            (
                (_graphql(ready_query, cursor=cursor, **common).get("data") or {}).get(
                    "repository"
                )
                or {}
            ).get("pullRequest")
            or {}
        ).get("items")
        or {}
    )

    reviews_query = """
    query($owner:String!,$name:String!,$number:Int!,$cursor:String){
      repository(owner:$owner,name:$name){pullRequest(number:$number){
        items:reviews(first:100,after:$cursor){pageInfo{hasNextPage endCursor}
          nodes{author{login}submittedAt updatedAt state}}
      }}
    }
    """
    review_nodes = _collect_connection(
        lambda cursor: (
            (
                (
                    _graphql(reviews_query, cursor=cursor, **common).get("data") or {}
                ).get("repository")
                or {}
            ).get("pullRequest")
            or {}
        ).get("items")
        or {}
    )

    threads_query = """
    query($owner:String!,$name:String!,$number:Int!,$cursor:String){
      repository(owner:$owner,name:$name){pullRequest(number:$number){
        items:reviewThreads(first:100,after:$cursor){pageInfo{hasNextPage endCursor}
          nodes{id isResolved}}
      }}
    }
    """
    thread_nodes = _collect_connection(
        lambda cursor: (
            (
                (
                    _graphql(threads_query, cursor=cursor, **common).get("data") or {}
                ).get("repository")
                or {}
            ).get("pullRequest")
            or {}
        ).get("items")
        or {}
    )

    comments_query = """
    query($threadId:ID!,$cursor:String){node(id:$threadId){
      ... on PullRequestReviewThread{items:comments(first:100,after:$cursor){
        pageInfo{hasNextPage endCursor} nodes{id createdAt updatedAt}
      }}
    }}
    """
    threads = []
    for thread in thread_nodes:
        thread_id = thread.get("id")
        if not isinstance(thread_id, str) or not thread_id:
            raise RuntimeError("review_thread_id_missing")
        comments = _collect_connection(
            lambda cursor, thread_id=thread_id: (
                (
                    _graphql(comments_query, threadId=thread_id, cursor=cursor).get(
                        "data"
                    )
                    or {}
                ).get("node")
                or {}
            ).get("items")
            or {}
        )
        threads.append(
            {
                "id": thread_id,
                "is_resolved": thread.get("isResolved"),
                "comments": [
                    {
                        "id": comment.get("id"),
                        "created_at": comment.get("createdAt"),
                        "updated_at": comment.get("updatedAt"),
                    }
                    for comment in comments
                ],
            }
        )

    trusted_invalidation_at, trusted_invalidation_source = (
        fetch_latest_trusted_invalidation(repo, str(pr.get("headRefOid") or ""))
    )

    return {
        "repository": repository.get("nameWithOwner"),
        "pr_number": pr.get("number"),
        "state": pr.get("state"),
        "is_draft": pr.get("isDraft"),
        "merged": pr.get("merged"),
        "created_at": pr.get("createdAt"),
        "head_sha": pr.get("headRefOid"),
        "review_decision": pr.get("reviewDecision"),
        "ready_events_complete": True,
        "review_events_complete": True,
        "thread_events_complete": True,
        "review_comment_events_complete": True,
        "ready_events": [node.get("createdAt") for node in ready_nodes],
        "latest_trusted_invalidation_at": trusted_invalidation_at,
        "latest_trusted_invalidation_source": trusted_invalidation_source,
        "trusted_invalidation_time_unknown": False,
        "reviews": [
            {
                "author": (node.get("author") or {}).get("login"),
                "state": node.get("state"),
                "submitted_at": node.get("submittedAt"),
                "updated_at": node.get("updatedAt"),
            }
            for node in review_nodes
        ],
        "threads": threads,
    }


def _write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _fetch_command(args: argparse.Namespace) -> int:
    if args.repo.count("/") != 1:
        raise SystemExit("repo must be OWNER/NAME")
    if args.pr <= 0:
        raise SystemExit("pr must be positive")
    if not SHA_RE.fullmatch(args.head):
        raise SystemExit("head must be a lowercase 40-hex SHA")
    snapshot = fetch_snapshot(args.repo, args.pr)
    now = (
        datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        if args.now
        else datetime.now(timezone.utc)
    )
    result = evaluate_snapshot(
        snapshot,
        expected_repo=args.repo,
        expected_pr=args.pr,
        expected_head=args.head,
        now=now,
        min_ready_age_seconds=args.min_ready_age_seconds,
        min_activity_quiet_seconds=args.min_activity_quiet_seconds,
    )
    _write_result(args.output, result)
    safe_result = {
        "marker": result.get("marker"),
        "status": result.get("status"),
        "repository": result.get("repository"),
        "pr_number": result.get("pr_number"),
        "expected_head_sha": result.get("expected_head_sha"),
        "live_head_sha": result.get("live_head_sha"),
        "fingerprint": result.get("fingerprint"),
        "reasons": result.get("reasons"),
    }
    print(json.dumps(safe_result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "SETTLED" else 1


def _compare_command(args: argparse.Namespace) -> int:
    before = json.loads(args.before.read_text(encoding="utf-8"))
    after = json.loads(args.after.read_text(encoding="utf-8"))
    matches = (
        before.get("status") == "SETTLED"
        and after.get("status") == "SETTLED"
        and before.get("fingerprint") == after.get("fingerprint")
        and before.get("repository") == after.get("repository")
        and before.get("pr_number") == after.get("pr_number")
        and before.get("live_head_sha") == after.get("live_head_sha")
    )
    print(
        json.dumps(
            {
                "marker": "REVIEW_SETTLEMENT_COMPARE",
                "status": "MATCH" if matches else "DRIFT",
                "before_fingerprint": before.get("fingerprint"),
                "after_fingerprint": after.get("fingerprint"),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if matches else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    fetch = subparsers.add_parser("fetch")
    fetch.add_argument("--repo", required=True)
    fetch.add_argument("--pr", required=True, type=int)
    fetch.add_argument("--head", required=True)
    fetch.add_argument("--output", required=True, type=Path)
    fetch.add_argument("--min-ready-age-seconds", type=int, default=300)
    fetch.add_argument("--min-activity-quiet-seconds", type=int, default=120)
    fetch.add_argument("--now")
    fetch.set_defaults(handler=_fetch_command)

    compare = subparsers.add_parser("compare")
    compare.add_argument("--before", required=True, type=Path)
    compare.add_argument("--after", required=True, type=Path)
    compare.set_defaults(handler=_compare_command)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        return int(args.handler(args))
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"review settlement failed closed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
