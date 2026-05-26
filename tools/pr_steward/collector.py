from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any


PR_VIEW_FIELDS = ",".join(
    [
        "number",
        "url",
        "state",
        "isDraft",
        "mergeable",
        "mergeStateStatus",
        "reviewDecision",
        "baseRefName",
        "baseRefOid",
        "headRefName",
        "headRefOid",
        "author",
        "createdAt",
        "updatedAt",
        "files",
        "commits",
        "reviews",
        "comments",
        "statusCheckRollup",
    ]
)


def load_fixture(fixture_dir: Path) -> dict[str, Any]:
    path = fixture_dir / "harvest.json"
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"fixture payload must be an object: {path}")
    return payload


def collect_from_github(repo: str, pr_number: int) -> dict[str, Any]:
    errors: list[str] = []
    auth = _run(["gh", "auth", "status"])
    if auth.returncode != 0:
        return _incomplete_harvest(
            repo=repo,
            pr_number=pr_number,
            errors=["gh auth status failed for github.com"],
        )

    view = _run(
        [
            "gh",
            "pr",
            "view",
            str(pr_number),
            "--repo",
            repo,
            "--json",
            PR_VIEW_FIELDS,
        ]
    )
    if view.returncode != 0:
        return _incomplete_harvest(
            repo=repo,
            pr_number=pr_number,
            errors=[f"gh pr view failed: {view.stderr.strip()}"],
        )

    try:
        pr_payload = json.loads(view.stdout)
    except json.JSONDecodeError as exc:
        return _incomplete_harvest(
            repo=repo,
            pr_number=pr_number,
            errors=[f"gh pr view returned invalid JSON: {exc}"],
        )

    threads, thread_errors = _fetch_review_threads(repo=repo, pr_number=pr_number)
    errors.extend(thread_errors)
    return normalize_gh_payload(
        pr_payload,
        review_threads=threads,
        harvest_errors=errors,
    )


def normalize_gh_payload(
    pr_payload: dict[str, Any],
    *,
    review_threads: list[dict[str, Any]],
    harvest_errors: list[str],
) -> dict[str, Any]:
    review_comments = []
    for thread in review_threads:
        review_comments.extend(thread.get("comments") or [])

    return {
        "harvest_complete": not harvest_errors,
        "harvest_errors": harvest_errors,
        "pr": pr_payload,
        "changed_files": pr_payload.get("files") or [],
        "commits": pr_payload.get("commits") or [],
        "reviews": pr_payload.get("reviews") or [],
        "review_comments": review_comments,
        "review_threads": review_threads,
        "issue_comments": pr_payload.get("comments") or [],
        "checks": pr_payload.get("statusCheckRollup") or [],
        "embedded_audit": {
            "status": "SKIPPED",
            "report_path": "proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md",
        },
        "proof": {
            "proof_path": "proof/TP-DMX-PR-STEWARD-001/PROOF.json",
            "proof_head_sha": None,
            "matches_pr_head": False,
        },
    }


def _fetch_review_threads(
    *, repo: str, pr_number: int
) -> tuple[list[dict[str, Any]], list[str]]:
    owner, name = repo.split("/", 1)
    query = textwrap.dedent(
        """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              reviewThreads(first: 100) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id
                  isResolved
                  isOutdated
                  path
                  line
                  startLine
                  comments(first: 50) {
                    pageInfo { hasNextPage endCursor }
                    nodes {
                      id
                      body
                      path
                      line
                      createdAt
                      updatedAt
                      author { login }
                      authorAssociation
                    }
                  }
                }
              }
            }
          }
        }
        """
    ).strip()
    result = _run(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"owner={owner}",
            "-f",
            f"repo={name}",
            "-F",
            f"number={pr_number}",
            "-f",
            f"query={query}",
        ]
    )
    if result.returncode != 0:
        return [], [f"gh api graphql reviewThreads failed: {result.stderr.strip()}"]

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return [], [f"gh api graphql reviewThreads returned invalid JSON: {exc}"]

    page = (
        payload.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviewThreads", {})
    )
    errors: list[str] = []
    if page.get("pageInfo", {}).get("hasNextPage"):
        errors.append("reviewThreads harvest exceeded first 100 threads")

    threads = page.get("nodes") or []
    for thread in threads:
        comments_page = thread.get("comments") or {}
        if comments_page.get("pageInfo", {}).get("hasNextPage"):
            errors.append(f"reviewThread {thread.get('id')} exceeded first 50 comments")
        thread["comments"] = comments_page.get("nodes") or []
    return threads, errors


def _incomplete_harvest(
    *, repo: str, pr_number: int, errors: list[str]
) -> dict[str, Any]:
    return {
        "harvest_complete": False,
        "harvest_errors": errors,
        "pr": {
            "number": pr_number,
            "url": f"https://github.com/{repo}/pull/{pr_number}",
            "state": "UNKNOWN",
            "isDraft": False,
            "mergeable": "UNKNOWN",
            "mergeStateStatus": "UNKNOWN",
            "reviewDecision": None,
            "baseRefName": "",
            "baseRefOid": "",
            "headRefName": "",
            "headRefOid": "",
            "author": {"login": "unknown"},
            "createdAt": None,
            "updatedAt": None,
        },
        "changed_files": [],
        "commits": [],
        "reviews": [],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "checks": [],
        "embedded_audit": {
            "status": "SKIPPED",
            "report_path": "proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md",
        },
        "proof": {
            "proof_path": "proof/TP-DMX-PR-STEWARD-001/PROOF.json",
            "proof_head_sha": None,
            "matches_pr_head": False,
        },
    }


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        capture_output=True,
        check=False,
    )
