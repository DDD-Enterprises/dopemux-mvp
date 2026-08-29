from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any

from dopemux_pr_steward import proof_successor


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


def collect_from_github(
    repo: str, pr_number: int, *, proof_path: Path | None = None
) -> dict[str, Any]:
    errors: list[str] = []
    proof_state, initial_proof_errors = _proof_state(
        proof_path=proof_path,
        pr_head_sha=None,
        expected_pr=pr_number,
        expected_repo=repo,
    )
    auth = _run(["gh", "auth", "status"])
    if auth.returncode != 0:
        return _incomplete_harvest(
            repo=repo,
            pr_number=pr_number,
            errors=initial_proof_errors + ["gh auth status failed for github.com"],
            proof_state=proof_state,
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
            errors=initial_proof_errors
            + [f"gh pr view failed: {view.stderr.strip()}"],
            proof_state=proof_state,
        )

    try:
        pr_payload = json.loads(view.stdout)
    except json.JSONDecodeError as exc:
        return _incomplete_harvest(
            repo=repo,
            pr_number=pr_number,
            errors=initial_proof_errors
            + [f"gh pr view returned invalid JSON: {exc}"],
            proof_state=proof_state,
        )

    proof_state, proof_errors = _proof_state(
        proof_path=proof_path,
        pr_head_sha=str(pr_payload.get("headRefOid") or ""),
        expected_pr=pr_number,
        expected_repo=repo,
    )
    errors.extend(proof_errors)
    threads, thread_errors = _fetch_review_threads(repo=repo, pr_number=pr_number)
    errors.extend(thread_errors)
    reviews_raw, review_errors = _fetch_reviews_with_commit(repo=repo, pr_number=pr_number)
    errors.extend(review_errors)
    changed_files, changed_files_rest_errors = _fetch_changed_files_rest(
        repo=repo, pr_number=pr_number
    )
    errors.extend(changed_files_rest_errors)
    rest_changed_file_paths = [item["path"] for item in changed_files]
    _changed_files_check, changed_files_errors = _fetch_changed_files_with_pagination_check(
        repo=repo, pr_number=pr_number, rest_paths=rest_changed_file_paths
    )
    errors.extend(changed_files_errors)
    security_release_approval = _select_security_release_approval(
        reviews_raw, repo=repo, pr_number=pr_number
    )
    return normalize_gh_payload(
        pr_payload,
        review_threads=threads,
        harvest_errors=errors,
        proof_state=proof_state,
        security_release_approval=security_release_approval,
        changed_files=changed_files,
    )


def normalize_gh_payload(
    pr_payload: dict[str, Any],
    *,
    review_threads: list[dict[str, Any]],
    harvest_errors: list[str],
    proof_state: dict[str, Any] | None = None,
    security_release_approval: dict[str, Any] | None = None,
    changed_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    review_comments = []
    for thread in review_threads:
        review_comments.extend(thread.get("comments") or [])

    proof = proof_state or _missing_proof_state(None)
    return {
        "harvest_complete": not harvest_errors,
        "harvest_errors": harvest_errors,
        "pr": pr_payload,
        "changed_files": changed_files if changed_files is not None else (pr_payload.get("files") or []),
        "commits": pr_payload.get("commits") or [],
        "reviews": pr_payload.get("reviews") or [],
        "review_comments": review_comments,
        "review_threads": review_threads,
        "issue_comments": pr_payload.get("comments") or [],
        "checks": pr_payload.get("statusCheckRollup") or [],
        "embedded_audit": proof["embedded_audit"],
        "proof": proof["proof"],
        "security_release_approval": security_release_approval,
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


def _fetch_reviews_with_commit(
    *, repo: str, pr_number: int
) -> tuple[list[dict[str, Any]], list[str]]:
    owner, name = repo.split("/", 1)
    query = textwrap.dedent(
        """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              reviews(first: 100) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id
                  state
                  submittedAt
                  author { login }
                  authorAssociation
                  commit { oid }
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
        return [], [f"gh api graphql reviews failed: {result.stderr.strip()}"]
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return [], [f"gh api graphql reviews returned invalid JSON: {exc}"]
    page = (
        payload.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviews", {})
    )
    errors: list[str] = []
    if page.get("pageInfo", {}).get("hasNextPage"):
        errors.append("reviews harvest exceeded first 100 reviews")
    return page.get("nodes") or [], errors


def _fetch_changed_files_rest(
    *, repo: str, pr_number: int
) -> tuple[list[dict[str, Any]], list[str]]:
    """Canonical changed-file source: paginated REST pull-files endpoint.

    Unlike ``gh pr view --json files`` (path/additions/deletions only), the
    REST ``pulls/{n}/files`` endpoint reports ``status`` and, for renamed
    entries, ``previous_filename`` — the only way to know a protected path
    (a workflow, CODEOWNERS, or this gate's own tools/pr_steward/** trust
    root) was renamed OUT from under the classifier rather than edited in
    place. ``--paginate`` follows Link headers itself, so there is no
    separate hasNextPage check on this source the way there is for GraphQL.
    """
    owner, name = repo.split("/", 1)
    result = _run(
        [
            "gh",
            "api",
            f"repos/{owner}/{name}/pulls/{pr_number}/files",
            "--paginate",
            "-q",
            ".",
        ]
    )
    if result.returncode != 0:
        return [], [f"gh api pulls/files failed: {result.stderr.strip()}"]
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            page = json.loads(line)
            if not isinstance(page, list):
                errors.append("gh api pulls/files returned a non-list page")
                continue
            items.extend(page)
    except json.JSONDecodeError as exc:
        return [], [f"gh api pulls/files returned invalid JSON: {exc}"]

    changed_files: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"pulls/files entry at index {index} is not a mapping")
            continue
        path = item.get("filename")
        if not isinstance(path, str) or not path:
            errors.append(f"pulls/files entry at index {index} has no filename")
            continue
        status = item.get("status")
        previous_path = item.get("previous_filename")
        if status == "renamed" and (
            not isinstance(previous_path, str) or not previous_path
        ):
            errors.append(
                f"pulls/files entry {path!r} is renamed but previous_filename is "
                "missing or malformed"
            )
            continue
        changed_files.append(
            {
                "path": path,
                "additions": int(item.get("additions") or 0),
                "deletions": int(item.get("deletions") or 0),
                "status": status,
                "previous_path": previous_path if status == "renamed" else None,
            }
        )
    return changed_files, errors


def _fetch_changed_files_with_pagination_check(
    *, repo: str, pr_number: int, rest_paths: list[str] | None = None
) -> tuple[list[str], list[str]]:
    """Independently verify the REST-shaped `gh pr view --json files` list is complete.

    `gh pr view --json files` has a history of silently truncating large file
    lists with no indication of truncation in its REST-shaped JSON output. A
    truncated file list could hide a security-sensitive path (e.g. a workflow
    file) from `classify_security_release_paths`, causing the gate to be
    incorrectly marked not-required. This GraphQL query with an explicit
    `pageInfo.hasNextPage` check, paginated via `after: $cursor` until
    exhausted, is the completeness signal for that list; the REST list
    remains the source of truth for `changed_files` in the harvested
    payload, while this function returns the GraphQL path list only for verification/reconciliation.

    The GraphQL connection's non-negative `totalCount` is pinned across pages.
    Pagination continues without an arbitrary size ceiling while each page
    makes verifiable progress through a new non-empty cursor and at least one
    new path. Any malformed shape, GraphQL error, count drift, duplicate path,
    or cursor anomaly fails closed before reconciliation.

    When `rest_paths` is provided, this also reconciles the exact REST path set
    against the complete GraphQL path set. Reconciliation is skipped after any
    GraphQL failure because the GraphQL side is then untrustworthy.
    """
    owner, name = repo.split("/", 1)
    query = textwrap.dedent(
        """
        query($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              files(first: 100, after: $cursor) {
                totalCount
                pageInfo { hasNextPage endCursor }
                nodes {
                  path
                }
              }
            }
          }
        }
        """
    ).strip()
    paths: list[str] = []
    cursor: str | None = None
    seen_cursors: set[str] = set()
    seen_paths: set[str] = set()
    pinned_total_count: int | None = None
    while True:
        args = [
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
        if cursor is not None:
            args.extend(["-f", f"cursor={cursor}"])
        result = _run(args)
        if result.returncode != 0:
            return [], [f"gh api graphql changedFiles failed: {result.stderr.strip()}"]
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            return [], [f"gh api graphql changedFiles returned invalid JSON: {exc}"]
        if not isinstance(payload, dict):
            return paths, [
                "changedFiles GraphQL response is malformed: expected an object"
            ]

        graphql_errors = payload.get("errors")
        if graphql_errors is not None:
            if not isinstance(graphql_errors, list):
                return paths, [
                    "changedFiles GraphQL response is malformed: errors is not a list"
                ]
            if graphql_errors:
                return paths, ["changedFiles GraphQL response reported GraphQL errors"]

        data = payload.get("data")
        if not isinstance(data, dict):
            return paths, [
                "changedFiles GraphQL response is malformed: data is not an object"
            ]
        repository = data.get("repository")
        if not isinstance(repository, dict):
            return paths, [
                "changedFiles GraphQL response is malformed: repository is not an object"
            ]
        pull_request = repository.get("pullRequest")
        if not isinstance(pull_request, dict):
            return paths, [
                "changedFiles GraphQL response is malformed: pullRequest is not an object"
            ]
        page = pull_request.get("files")
        if not isinstance(page, dict):
            return paths, [
                "changedFiles GraphQL response is malformed: files is not an object"
            ]

        total_count = page.get("totalCount")
        if (
            not isinstance(total_count, int)
            or isinstance(total_count, bool)
            or total_count < 0
        ):
            return paths, [
                "changedFiles GraphQL totalCount must be a non-negative integer"
            ]
        if pinned_total_count is None:
            pinned_total_count = total_count
        elif total_count != pinned_total_count:
            return paths, [
                "changedFiles GraphQL totalCount changed during pagination: "
                f"expected {pinned_total_count}, got {total_count}"
            ]

        page_info = page.get("pageInfo")
        if not isinstance(page_info, dict):
            return paths, [
                "changedFiles GraphQL response is malformed: pageInfo is not an object"
            ]
        if "hasNextPage" not in page_info or "endCursor" not in page_info:
            return paths, [
                "changedFiles GraphQL response is malformed: pageInfo fields are missing"
            ]
        has_next_page = page_info["hasNextPage"]
        if not isinstance(has_next_page, bool):
            return paths, [
                "changedFiles GraphQL response is malformed: hasNextPage is not a boolean"
            ]
        end_cursor = page_info["endCursor"]
        if end_cursor is not None and not isinstance(end_cursor, str):
            return paths, [
                "changedFiles GraphQL response is malformed: endCursor is not a string or null"
            ]

        nodes = page.get("nodes")
        if not isinstance(nodes, list):
            return paths, [
                "changedFiles GraphQL response is malformed: nodes is not a list"
            ]
        page_path_count = 0
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                return paths, [
                    f"changedFiles GraphQL node at index {index} is malformed"
                ]
            path = node.get("path")
            if not isinstance(path, str) or not path:
                return paths, [
                    f"changedFiles GraphQL node at index {index} has a malformed path"
                ]
            if path in seen_paths:
                return paths, [f"changedFiles GraphQL returned duplicate path {path!r}"]
            seen_paths.add(path)
            paths.append(path)
            page_path_count += 1

        if len(paths) > pinned_total_count:
            return paths, [
                "changedFiles GraphQL collected count exceeded totalCount: "
                f"collected {len(paths)}, totalCount {pinned_total_count}"
            ]

        if has_next_page:
            if page_path_count == 0:
                return paths, [
                    "changedFiles GraphQL page reported hasNextPage but added no paths"
                ]
            if len(paths) >= pinned_total_count:
                return paths, [
                    "changedFiles GraphQL reported hasNextPage after collecting "
                    f"totalCount {pinned_total_count}"
                ]
            if not isinstance(end_cursor, str) or not end_cursor.strip():
                return paths, [
                    "changedFiles GraphQL page reported hasNextPage without a "
                    "non-empty cursor"
                ]
            if end_cursor == cursor or end_cursor in seen_cursors:
                return paths, [
                    "changedFiles GraphQL cursor repeated or did not advance"
                ]
            seen_cursors.add(end_cursor)
            cursor = end_cursor
            continue

        if len(paths) != pinned_total_count:
            return paths, [
                "changedFiles GraphQL final collected count differed from totalCount: "
                f"collected {len(paths)}, totalCount {pinned_total_count}"
            ]
        break

    errors: list[str] = []
    if rest_paths is not None:
        rest_set = set(rest_paths)
        graphql_set = set(paths)
        if rest_set != graphql_set:
            only_in_rest = sorted(rest_set - graphql_set)
            only_in_graphql = sorted(graphql_set - rest_set)
            detail_parts = []
            if only_in_rest:
                detail_parts.append(
                    f"{len(only_in_rest)} only in REST (e.g. {only_in_rest[:5]})"
                )
            if only_in_graphql:
                detail_parts.append(
                    f"{len(only_in_graphql)} only in GraphQL (e.g. {only_in_graphql[:5]})"
                )
            errors.append(
                "changed_files harvest content mismatch: "
                f"REST reported {len(rest_paths)} paths, GraphQL reported {len(paths)} "
                f"paths, sets differ ({'; '.join(detail_parts)})"
            )
    return paths, errors


def _select_security_release_approval(
    reviews: list[dict[str, Any]], *, repo: str, pr_number: int
) -> dict[str, Any] | None:
    """Return the most recent APPROVED review with a bound commit, or None.

    Chronological order matters: a later CHANGES_REQUESTED from anyone must
    not be shadowed by an earlier APPROVED — GitHub's own reviewDecision
    semantics treat the latest state per-author as authoritative, but for
    this fail-closed gate we take the single most-recent APPROVED review
    with commit binding, full stop. If a subsequent review (any state, any
    author) is more recent than the latest APPROVED review, treat approval
    as absent — a fresh review event means the approval is not necessarily
    still current from the maintainers' perspective.
    """
    dated = [r for r in reviews if isinstance(r, dict) and r.get("submittedAt")]
    if not dated:
        return None
    dated.sort(key=lambda r: r["submittedAt"])
    most_recent = dated[-1]
    if most_recent.get("state") != "APPROVED":
        return None
    commit = most_recent.get("commit")
    if not isinstance(commit, dict) or not commit.get("oid"):
        return None
    author = most_recent.get("author") or {}
    login = author.get("login") if isinstance(author, dict) else None
    if not login:
        return None
    association = most_recent.get("authorAssociation")
    return {
        "state": "APPROVED",
        "repository": repo,
        "pr_number": pr_number,
        "head_sha": str(commit["oid"]),
        "approver": str(login),
        "approver_association": str(association) if association else None,
        "approval_ref": str(most_recent.get("id") or ""),
        "approved_at": str(most_recent.get("submittedAt") or ""),
    }


def _incomplete_harvest(
    *,
    repo: str,
    pr_number: int,
    errors: list[str],
    proof_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proof = proof_state or _missing_proof_state(None)
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
        "embedded_audit": proof["embedded_audit"],
        "proof": proof["proof"],
        "security_release_approval": None,
    }


def _proof_state(
    *,
    proof_path: Path | None,
    pr_head_sha: str | None,
    expected_pr: int | None = None,
    expected_repo: str | None = None,
) -> tuple[dict[str, Any], list[str]]:
    if proof_path is None:
        return _missing_proof_state(None), ["proof_missing: --proof-path not provided"]
    try:
        payload = json.loads(proof_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return _missing_proof_state(proof_path), [f"proof_unreadable: {exc}"]
    except json.JSONDecodeError as exc:
        return _missing_proof_state(proof_path), [f"proof_unparseable: {exc}"]
    if not isinstance(payload, dict):
        return _missing_proof_state(proof_path), ["proof_unparseable: root is not an object"]

    errors: list[str] = []
    embedded = payload.get("embedded_audit") or {}
    if not isinstance(embedded, dict):
        embedded = {}
    audit_status = str(embedded.get("status") or "SKIPPED")
    independent_errors = _independent_audit_errors(
        payload,
        expected_pr=expected_pr,
        expected_head_sha=pr_head_sha,
        expected_repo=expected_repo,
    )
    if independent_errors:
        audit_status = "NEEDS_SUPERVISOR"
        errors.extend(independent_errors)
    proof_head_sha = _proof_head_sha(payload)
    proof_freshness = _proof_freshness(payload, proof_head_sha, pr_head_sha)
    return {
        "embedded_audit": {
            "status": audit_status,
            "report_path": str(
                embedded.get("report_path")
                or f"{proof_path.parent.as_posix()}/AUDITOR_REPORT.md"
            ),
        },
        "proof": {
            "proof_path": proof_path.as_posix(),
            "proof_head_sha": proof_head_sha,
            "matches_pr_head": bool(
                proof_head_sha and pr_head_sha and proof_head_sha == pr_head_sha
            ),
            "proof_freshness": proof_freshness,
        },
    }, errors


def _independent_audit_errors(
    payload: dict[str, Any],
    *,
    expected_pr: int | None = None,
    expected_head_sha: str | None = None,
    expected_repo: str | None = None,
) -> list[str]:
    """Delegate to the shared independent-audit proof validator.

    Parity with the embedded-audit workflow hard gate is intentional: both
    surfaces must accept and reject the same proof shapes. When known, pass
    expected PR/repo/head so a proof from another PR cannot produce READY.
    """
    # Local import keeps collector importable when scripts/ is unavailable in
    # tightly packaged test contexts, while remaining the single contract path.
    from scripts.audit.run_embedded_audit import independent_audit_errors

    return independent_audit_errors(
        payload,
        expected_pr=expected_pr,
        expected_head_sha=expected_head_sha or None,
        expected_repo=expected_repo,
    )


def _missing_proof_state(proof_path: Path | None) -> dict[str, Any]:
    return {
        "embedded_audit": {
            "status": "SKIPPED",
            "report_path": "proof/TP-DMX-PR-STEWARD-001/AUDITOR_REPORT.md",
        },
        "proof": {
            "proof_path": proof_path.as_posix() if proof_path else "",
            "proof_head_sha": None,
            "matches_pr_head": False,
            "proof_freshness": {
                "status": "MISSING",
                "matches_pr_head": False,
                "reason": "Proof file was not provided.",
                "proof_recorded_sha": None,
                "pr_head_sha": None,
                "self_reference_exception": None,
            },
        },
    }


def _proof_freshness(
    payload: dict[str, Any], proof_head_sha: str | None, pr_head_sha: str | None
) -> dict[str, Any]:
    raw = payload.get("proof_freshness")
    if isinstance(raw, dict):
        exception = raw.get("self_reference_exception")
        return {
            "status": str(raw.get("status") or "UNKNOWN"),
            "matches_pr_head": bool(
                raw.get("matches_pr_head", bool(proof_head_sha and pr_head_sha and proof_head_sha == pr_head_sha))
            ),
            "reason": str(raw.get("reason") or ""),
            "proof_recorded_sha": str(raw.get("proof_recorded_sha") or proof_head_sha)
            if proof_head_sha
            else None,
            "pr_head_sha": str(raw.get("pr_head_sha") or pr_head_sha)
            if (raw.get("pr_head_sha") or pr_head_sha)
            else None,
            "self_reference_exception": exception
            if isinstance(exception, dict)
            else None,
        }

    if not proof_head_sha:
        return {
            "status": "MISSING",
            "matches_pr_head": False,
            "reason": "Proof head SHA missing.",
            "proof_recorded_sha": None,
            "pr_head_sha": pr_head_sha,
            "self_reference_exception": None,
        }
    if pr_head_sha and proof_head_sha == pr_head_sha:
        return {
            "status": "CURRENT",
            "matches_pr_head": True,
            "reason": "Proof head SHA matches PR head SHA.",
            "proof_recorded_sha": proof_head_sha,
            "pr_head_sha": pr_head_sha,
            "self_reference_exception": None,
        }
    if pr_head_sha:
        ok, reasons = proof_successor.verify_proof_successor(
            Path("."),
            live_head_sha=pr_head_sha,
            audited_head_sha=proof_head_sha,
            proof_payload=payload,
        )
        if ok:
            return {
                "status": "VERIFIED_SUCCESSOR",
                "matches_pr_head": False,
                "reason": (
                    "Proof head SHA is a verified ancestor of PR head SHA "
                    "with a proof-only successor delta."
                ),
                "proof_recorded_sha": proof_head_sha,
                "pr_head_sha": pr_head_sha,
                "self_reference_exception": None,
            }
    return {
        "status": "STALE",
        "matches_pr_head": False,
        "reason": "Proof head SHA does not match PR head SHA.",
        "proof_recorded_sha": proof_head_sha,
        "pr_head_sha": pr_head_sha,
        "self_reference_exception": None,
    }


def _proof_head_sha(payload: dict[str, Any]) -> str | None:
    for key in (
        "head_sha",
        "commit",
        "commit_sha",
        "implementation_commit_sha",
    ):
        value = payload.get(key)
        if value:
            return str(value)
    for parent_key in ("pr", "target"):
        nested = payload.get(parent_key)
        if isinstance(nested, dict) and nested.get("head_sha"):
            return str(nested["head_sha"])
    return None


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        capture_output=True,
        check=False,
    )
