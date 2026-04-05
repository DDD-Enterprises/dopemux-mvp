from __future__ import annotations

import json
import re
import textwrap
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .runtime import CommandResult, json_loads_or_empty, run_command
from .schema import CheckSummary, ReviewThread, ThreadComment

CHECK_SUCCESS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
CHECK_FAILURE = {
    "FAILURE",
    "TIMED_OUT",
    "CANCELLED",
    "ACTION_REQUIRED",
    "STARTUP_FAILURE",
    "STALE",
}
BOT_AUTHORS = {
    "github-code-quality",
    "copilot-pull-request-reviewer",
    "codecov-commenter",
}
GITHUB_ACTIONS_DETAILS_URL_RE = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/actions/runs/(?P<run_id>\d+)(?:/job/(?P<job_id>\d+))?/?$"
)
GIT_REMOTE_SLUG_RE = re.compile(
    r"(?:github\.com[:/])(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?$"
)


@dataclass(frozen=True)
class RemoteCheckLogEvidence:
    check_name: str
    details_url: str
    run_id: Optional[str] = None
    job_id: Optional[str] = None
    log_text: str = ""
    fetch_status: str = "unsupported"
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def ok(self) -> bool:
        return self.fetch_status == "ok"


def _check_rollup_name(check: Dict[str, Any]) -> str:
    name = str(check.get("name") or check.get("context") or "").strip()
    return name


def _check_rollup_details_url(check: Dict[str, Any]) -> str:
    return str(check.get("detailsUrl") or check.get("targetUrl") or "").strip()


def _required_check_entries_by_state(
    checks: List[Dict[str, Any]],
    required_contexts: Sequence[str],
    *,
    failure_only: bool = False,
    pending_only: bool = False,
) -> List[Dict[str, Any]]:
    required = {str(item).strip() for item in required_contexts if str(item).strip()}
    entries: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()
    for check in checks:
        name = _check_rollup_name(check)
        if not name or name not in required:
            continue
        status = str(check.get("status") or check.get("state") or "").upper()
        conclusion = str(check.get("conclusion") or "").upper()
        is_pending = bool(status and status != "COMPLETED") or (
            not conclusion and status != "COMPLETED"
        )
        is_failure = conclusion in CHECK_FAILURE
        if failure_only and not is_failure:
            continue
        if pending_only and not is_pending:
            continue
        details_url = _check_rollup_details_url(check)
        dedupe_key = (name, details_url)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        entries.append(
            {
                "check_name": name,
                "details_url": details_url,
                "status": status,
                "conclusion": conclusion,
            }
        )
    return entries


def _required_check_names_by_state(
    checks: List[Dict[str, Any]],
    required_contexts: Sequence[str],
    *,
    failure_only: bool = False,
    pending_only: bool = False,
) -> List[str]:
    required = {str(item).strip() for item in required_contexts if str(item).strip()}
    names: List[str] = []
    for check in checks:
        name = _check_rollup_name(check)
        if not name or name not in required:
            continue
        status = str(check.get("status") or "").upper()
        conclusion = str(check.get("conclusion") or "").upper()
        is_pending = bool(status and status != "COMPLETED") or (
            not conclusion and status != "COMPLETED"
        )
        is_failure = conclusion in CHECK_FAILURE
        if failure_only and not is_failure:
            continue
        if pending_only and not is_pending:
            continue
        names.append(name)
    return sorted(dict.fromkeys(names))


class GitHubClient:
    def __init__(
        self,
        *,
        repo: Optional[str],
        repo_root: Path,
        policy: Dict[str, Any],
    ) -> None:
        self.repo = repo
        self.repo_root = repo_root
        self.policy = policy
        self.cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_invalidations = 0
        retry = policy.get("retry", {})
        timeouts = policy.get("timeouts", {})
        self.max_attempts = int(retry.get("max_attempts", 3) or 3)
        self.backoff_seconds = int(retry.get("backoff_seconds", 2) or 2)
        self.max_backoff_seconds = int(retry.get("max_backoff_seconds", 10) or 10)
        self.retryable_markers = [
            str(x).lower() for x in retry.get("retryable_gh_errors", [])
        ]
        self.timeout_seconds = int(timeouts.get("gh_seconds", 120) or 120)

    def cache_summary(self) -> Dict[str, Any]:
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "invalidations": self.cache_invalidations,
            "keys": sorted(self.cache.keys()),
        }

    def invalidate(self, prefix: str) -> None:
        doomed = [key for key in self.cache if key.startswith(prefix)]
        if not doomed:
            return
        for key in doomed:
            self.cache.pop(key, None)
        self.cache_invalidations += len(doomed)

    def _repo_args(self) -> List[str]:
        if not self.repo:
            return []
        return ["--repo", self.repo]

    def _run(self, cmd: Sequence[str]) -> CommandResult:
        last_result: Optional[CommandResult] = None
        for attempt in range(1, self.max_attempts + 1):
            result = run_command(
                cmd, cwd=self.repo_root, timeout_seconds=self.timeout_seconds
            )
            last_result = result
            if result.returncode == 0:
                return result
            stderr = (result.stderr or "").lower()
            if attempt >= self.max_attempts or not any(
                marker in stderr for marker in self.retryable_markers
            ):
                return result
            delay = min(
                self.backoff_seconds * (2 ** (attempt - 1)), self.max_backoff_seconds
            )
            time.sleep(delay)
        return last_result or CommandResult(
            list(cmd), 1, "", "unknown GitHub command failure"
        )

    def _cache_get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        self.cache_misses += 1
        return None

    def _resolve_repo_slug_from_git_remote(self) -> Optional[str]:
        result = run_command(
            ["git", "remote", "get-url", "origin"],
            cwd=self.repo_root,
            timeout_seconds=self.timeout_seconds,
        )
        if result.returncode != 0:
            return None
        remote_url = (result.stdout or "").strip()
        match = GIT_REMOTE_SLUG_RE.search(remote_url)
        if not match:
            return None
        owner = match.group("owner").strip()
        repo = match.group("repo").strip()
        if not owner or not repo:
            return None
        return f"{owner}/{repo}"

    def resolve_repo_slug(self) -> str:
        cached = self._cache_get("repo_slug")
        if cached is not None:
            return str(cached)
        if self.repo:
            self.cache["repo_slug"] = self.repo
            return self.repo
        result = self._run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]
        )
        if result.returncode == 0:
            slug = result.stdout.strip()
        else:
            slug = self._resolve_repo_slug_from_git_remote() or ""
        if not slug or "/" not in slug:
            if result.returncode != 0:
                raise RuntimeError(f"Unable to resolve repo slug: {result.stderr.strip()}")
            raise RuntimeError(f"Invalid repo slug response: {slug!r}")
        self.cache["repo_slug"] = slug
        return slug

    def fetch_open_prs(self, limit: int) -> List[Dict[str, Any]]:
        cache_key = f"open_prs:{limit}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return list(cached)
        # We want ALL non-closed PRs, including drafts
        cmd = [
            "gh",
            "pr",
            "list",
            "--limit",
            str(limit),
            "--json",
            ",".join(
                [
                    "number",
                    "title",
                    "author",
                    "state",
                    "statusCheckRollup",
                    "mergeable",
                    "mergeStateStatus",
                    "labels",
                    "reviewDecision",
                    "autoMergeRequest",
                    "updatedAt",
                    "baseRefName",
                    "headRefName",
                    "headRefOid",
                    "baseRefOid",
                    "isDraft",
                    "additions",
                    "deletions",
                    "changedFiles",
                    "url",
                ]
            ),
            *self._repo_args(),
        ]
        result = self._run(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Unable to fetch open PRs: {result.stderr.strip()}")
        payload = json_loads_or_empty(result.stdout)
        if not isinstance(payload, list):
            raise RuntimeError("Unexpected gh pr list payload")
        self.cache[cache_key] = payload
        return payload

    def ready_pr(self, pr_id: int) -> bool:
        """Convert a draft PR to ready for review."""
        cmd = ["gh", "pr", "ready", str(pr_id), *self._repo_args()]
        result = self._run(cmd)
        return result.returncode == 0

    def get_authenticated_user(self) -> str:
        """Get the login of the currently authenticated user."""
        cached = self._cache_get("auth_user")
        if cached:
            return str(cached)
        result = self._run(["gh", "api", "user", "--jq", ".login"])
        if result.returncode != 0:
            return ""
        user = result.stdout.strip()
        self.cache["auth_user"] = user
        return user

    def find_global_fix_prs(self) -> List[Dict[str, Any]]:
        """
        Finds pull requests that are global fixes for CI failures.
        These are identified by the 'global-ci-fix' label and authored by the bot.
        """
        command = [
            "gh",
            "pr",
            "list",
            "--label",
            "global-ci-fix",
            "--author",
            "@me",  # Ensure we only find PRs opened by the bot.
            "--state",
            "open",
            "--json",
            "number,title,author,body,headRefName",
        ]
        command.extend(self._repo_args())
        result = self._run(command)
        if result.returncode != 0:
            return []
        if not result.stdout.strip():
            return []
        return json.loads(result.stdout)

    def fetch_pr(self, pr_id: int) -> Dict[str, Any]:
        cache_key = f"pr:{pr_id}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return dict(cached)
        cmd = [
            "gh",
            "pr",
            "view",
            str(pr_id),
            "--json",
            ",".join(
                [
                    "number",
                    "title",
                    "author",
                    "state",
                    "statusCheckRollup",
                    "mergeable",
                    "mergeStateStatus",
                    "labels",
                    "reviewDecision",
                    "autoMergeRequest",
                    "updatedAt",
                    "baseRefName",
                    "headRefName",
                    "headRefOid",
                    "baseRefOid",
                    "isDraft",
                    "additions",
                    "deletions",
                    "changedFiles",
                    "url",
                ]
            ),
            *self._repo_args(),
        ]
        result = self._run(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Unable to fetch PR #{pr_id}: {result.stderr.strip()}")
        payload = json_loads_or_empty(result.stdout)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Unexpected gh pr view payload for PR #{pr_id}")
        self.cache[cache_key] = payload
        return payload

    def fetch_pr_head_oid(self, pr_id: int) -> Tuple[Optional[str], Optional[str]]:
        payload = self.fetch_pr(pr_id)
        oid = str(payload.get("headRefOid") or "").strip()
        if not oid:
            return None, "PR head SHA was empty"
        return oid, None

    def fetch_branch_protection(self, branch: str) -> Dict[str, Any]:
        branch_name = str(branch or "").strip()
        if not branch_name:
            return {
                "available": False,
                "protected": False,
                "branch": branch_name,
                "required_approving_review_count": 0,
                "approval_required": False,
            }
        cache_key = f"branch_protection:{branch_name}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return dict(cached)
        repo_slug = self.resolve_repo_slug()
        result = self._run(
            ["gh", "api", f"repos/{repo_slug}/branches/{branch_name}/protection"]
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").lower()
            if "404" in stderr or "not found" in stderr or "not protected" in stderr:
                payload = {
                    "available": True,
                    "protected": False,
                    "branch": branch_name,
                    "required_approving_review_count": 0,
                    "approval_required": False,
                    "require_code_owner_reviews": False,
                    "require_last_push_approval": False,
                    "required_conversation_resolution": False,
                    "required_status_checks": [],
                    "strict_status_checks": False,
                    "enforce_admins": False,
                    "required_linear_history": False,
                }
                self.cache[cache_key] = payload
                return payload
            raise RuntimeError(
                f"Unable to fetch protection for branch {branch_name}: {result.stderr.strip()}"
            )
        raw = json_loads_or_empty(result.stdout)
        if not isinstance(raw, dict):
            raise RuntimeError(
                f"Unexpected branch protection payload for {branch_name!r}"
            )
        review_cfg = raw.get("required_pull_request_reviews") or {}
        status_cfg = raw.get("required_status_checks") or {}
        count = int(review_cfg.get("required_approving_review_count", 0) or 0)
        require_code_owner_reviews = bool(
            review_cfg.get("require_code_owner_reviews", False)
        )
        require_last_push_approval = bool(
            review_cfg.get("require_last_push_approval", False)
        )
        payload = {
            "available": True,
            "protected": True,
            "branch": branch_name,
            "required_approving_review_count": count,
            "approval_required": bool(
                count > 0 or require_code_owner_reviews or require_last_push_approval
            ),
            "require_code_owner_reviews": require_code_owner_reviews,
            "require_last_push_approval": require_last_push_approval,
            "required_conversation_resolution": bool(
                (raw.get("required_conversation_resolution") or {}).get(
                    "enabled", False
                )
            ),
            "required_status_checks": list(status_cfg.get("contexts") or []),
            "strict_status_checks": bool(status_cfg.get("strict", False)),
            "enforce_admins": bool(
                (raw.get("enforce_admins") or {}).get("enabled", False)
            ),
            "required_linear_history": bool(
                (raw.get("required_linear_history") or {}).get("enabled", False)
            ),
        }
        self.cache[cache_key] = payload
        return payload

    def fetch_review_threads(self, pr_id: int) -> List[ReviewThread]:
        cache_key = f"threads:{pr_id}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return list(cached)
        repo_slug = self.resolve_repo_slug()
        owner, name = repo_slug.split("/", 1)
        threads: List[ReviewThread] = []
        cursor: Optional[str] = None
        while True:
            after_clause = "null" if cursor is None else f'"{cursor}"'
            query = textwrap.dedent(f"""
                query {{
                  repository(owner: \"{owner}\", name: \"{name}\") {{
                    pullRequest(number: {pr_id}) {{
                      reviewThreads(first: 50, after: {after_clause}) {{
                        nodes {{
                          id
                          isResolved
                          isOutdated
                          viewerCanResolve
                          path
                          line
                          originalLine
                          originalStartLine
                          comments(first: 50) {{
                            pageInfo {{ hasNextPage endCursor }}
                            nodes {{
                              id
                              body
                              path
                              line
                              originalLine
                              createdAt
                              author {{ login }}
                            }}
                          }}
                        }}
                        pageInfo {{ hasNextPage endCursor }}
                      }}
                    }}
                  }}
                }}
                """).strip()
            result = self._run(["gh", "api", "graphql", "-f", f"query={query}"])
            if result.returncode != 0:
                raise RuntimeError(
                    f"Unable to fetch review threads for PR {pr_id}: {result.stderr.strip()}"
                )
            payload = json_loads_or_empty(result.stdout)
            page = (
                payload.get("data", {})
                .get("repository", {})
                .get("pullRequest", {})
                .get("reviewThreads", {})
            )
            nodes = page.get("nodes", []) or []
            for node in nodes:
                comments_page = node.get("comments", {}) or {}
                comments = self._parse_comments(comments_page.get("nodes", []) or [])
                if comments_page.get("pageInfo", {}).get("hasNextPage"):
                    extra = self._fetch_thread_comments(
                        node.get("id", ""), comments_page["pageInfo"].get("endCursor")
                    )
                    comments.extend(extra)
                threads.append(
                    ReviewThread(
                        id=str(node.get("id", "")),
                        is_resolved=bool(node.get("isResolved", False)),
                        is_outdated=bool(node.get("isOutdated", False)),
                        viewer_can_resolve=bool(node.get("viewerCanResolve", False)),
                        path=node.get("path") or "",
                        line=node.get("line"),
                        original_line=node.get("originalLine"),
                        original_start_line=node.get("originalStartLine"),
                        comments=comments,
                    )
                )
            page_info = page.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            if not cursor:
                break
        self.cache[cache_key] = threads
        return threads

    def _fetch_thread_comments(
        self, thread_id: str, cursor: Optional[str]
    ) -> List[ThreadComment]:
        comments: List[ThreadComment] = []
        next_cursor = cursor
        while next_cursor:
            query = textwrap.dedent(f"""
                query {{
                  node(id: \"{thread_id}\") {{
                    ... on PullRequestReviewThread {{
                      comments(first: 50, after: \"{next_cursor}\") {{
                        pageInfo {{ hasNextPage endCursor }}
                        nodes {{
                          id
                          body
                          path
                          line
                          originalLine
                          createdAt
                          author {{ login }}
                        }}
                      }}
                    }}
                  }}
                }}
                """).strip()
            result = self._run(["gh", "api", "graphql", "-f", f"query={query}"])
            if result.returncode != 0:
                raise RuntimeError(
                    f"Unable to fetch paginated comments for thread {thread_id}"
                )
            payload = json_loads_or_empty(result.stdout)
            comments_page = payload.get("data", {}).get("node", {}).get("comments", {})
            comments.extend(self._parse_comments(comments_page.get("nodes", []) or []))
            page_info = comments_page.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            next_cursor = page_info.get("endCursor")
        return comments

    @staticmethod
    def _parse_comments(nodes: Iterable[Dict[str, Any]]) -> List[ThreadComment]:
        comments: List[ThreadComment] = []
        for item in nodes:
            comments.append(
                ThreadComment(
                    id=str(item.get("id", "")),
                    author=(item.get("author") or {}).get("login", "unknown"),
                    body=item.get("body", ""),
                    created_at=item.get("createdAt", ""),
                    path=item.get("path") or "",
                    line=item.get("line"),
                    original_line=item.get("originalLine"),
                )
            )
        return comments

    def query_checks(
        self, pr_id: int, *, pr_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        payload = dict(pr_payload) if pr_payload is not None else self.fetch_pr(pr_id)
        checks = payload.get("statusCheckRollup", []) or []
        summary = summarize_checks(checks)
        review_decision = str(payload.get("reviewDecision") or "")
        protection = self.fetch_branch_protection(str(payload.get("baseRefName") or ""))
        required_contexts = list(protection.get("required_status_checks") or [])
        approval_required = bool(protection.get("approval_required", False))
        blockers: List[str] = []
        warnings: List[str] = []
        failed_required_checks = _required_check_names_by_state(
            checks, required_contexts, failure_only=True
        )
        failed_required_check_entries = _required_check_entries_by_state(
            checks, required_contexts, failure_only=True
        )
        pending_required_checks = _required_check_names_by_state(
            checks, required_contexts, pending_only=True
        )
        if summary.required_failure > 0:
            blockers.append("required_check_failed")
        if summary.required_pending > 0:
            blockers.append("required_check_pending")
        if summary.optional_failure > 0:
            warnings.append("optional_check_failed")
        if summary.optional_pending > 0:
            warnings.append("optional_check_pending")
        if approval_required and review_decision == "CHANGES_REQUESTED":
            blockers.append("changes_requested")
        elif approval_required and review_decision != "APPROVED":
            blockers.append("approval_missing")
        elif review_decision == "CHANGES_REQUESTED":
            warnings.append("changes_requested_not_blocking")
        elif review_decision and review_decision != "APPROVED":
            warnings.append("approval_not_required")
        return {
            "summary": summary,
            "review_decision": review_decision,
            "mergeable": payload.get("mergeable", ""),
            "merge_state_status": payload.get("mergeStateStatus", ""),
            "protection": protection,
            "failed_required_checks": failed_required_checks,
            "failed_required_check_entries": failed_required_check_entries,
            "pending_required_checks": pending_required_checks,
            "approval_required": approval_required,
            "blocker_types": blockers,
            "warning_types": warnings,
        }

    def fetch_remote_check_log_evidence(
        self, check_entry: Dict[str, Any]
    ) -> RemoteCheckLogEvidence:
        check_name = str(check_entry.get("check_name") or "").strip()
        details_url = str(check_entry.get("details_url") or "").strip()
        if not details_url:
            return RemoteCheckLogEvidence(
                check_name=check_name,
                details_url=details_url,
                fetch_status="missing_details_url",
                error="Required check did not include a details URL.",
            )
        cache_key = f"remote_check_log:{check_name}:{details_url}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        match = GITHUB_ACTIONS_DETAILS_URL_RE.match(details_url)
        if not match:
            evidence = RemoteCheckLogEvidence(
                check_name=check_name,
                details_url=details_url,
                fetch_status="unsupported",
                error="Details URL is not a GitHub Actions run or job URL.",
            )
            self.cache[cache_key] = evidence
            return evidence

        run_id = match.group("run_id")
        job_id = match.group("job_id")
        cmd = ["gh", "run", "view", run_id]
        if job_id:
            cmd.extend(["--job", job_id])
        cmd.append("--log")
        if self.repo:
            cmd.extend(["--repo", self.repo])
        result = self._run(cmd)
        if result.returncode != 0:
            evidence = RemoteCheckLogEvidence(
                check_name=check_name,
                details_url=details_url,
                run_id=run_id,
                job_id=job_id,
                fetch_status="error",
                error=result.stderr.strip() or "Unable to fetch GitHub Actions log.",
            )
            self.cache[cache_key] = evidence
            return evidence
        evidence = RemoteCheckLogEvidence(
            check_name=check_name,
            details_url=details_url,
            run_id=run_id,
            job_id=job_id,
            log_text=result.stdout or "",
            fetch_status="ok",
        )
        self.cache[cache_key] = evidence
        return evidence

    def rate_limit_snapshot(self) -> Dict[str, Any]:
        result = self._run(["gh", "api", "rate_limit"])
        if result.returncode != 0:
            return {"available": False, "error": result.stderr.strip()}
        payload = json_loads_or_empty(result.stdout)
        if not isinstance(payload, dict):
            return {"available": False, "error": "unexpected rate_limit payload"}
        return {"available": True, "resources": payload.get("resources", {})}


def ci_status(checks: List[Dict[str, Any]]) -> str:
    has_pending = False
    for check in checks:
        status = str(check.get("status") or "").upper()
        conclusion = str(check.get("conclusion") or "").upper()
        if status and status != "COMPLETED":
            has_pending = True
            continue
        if conclusion in CHECK_FAILURE:
            return "FAILURE"
        if not conclusion and status != "COMPLETED":
            has_pending = True
    return "PENDING" if has_pending else "SUCCESS"


def summarize_checks(checks: List[Dict[str, Any]]) -> CheckSummary:
    buckets = defaultdict(int)
    for check in checks:
        status = str(check.get("status") or "").upper()
        conclusion = str(check.get("conclusion") or "").upper()
        required = bool(check.get("isRequired", True))
        if status and status != "COMPLETED":
            buckets["pending"] += 1
            buckets["required_pending" if required else "optional_pending"] += 1
            continue
        if conclusion in CHECK_FAILURE:
            buckets["failure"] += 1
            buckets["required_failure" if required else "optional_failure"] += 1
            continue
        if conclusion in CHECK_SUCCESS:
            buckets["success"] += 1
            continue
        buckets["pending"] += 1
        buckets["required_pending" if required else "optional_pending"] += 1
    return CheckSummary(
        total=len(checks),
        success=buckets["success"],
        failure=buckets["failure"],
        pending=buckets["pending"],
        required_pending=buckets["required_pending"],
        required_failure=buckets["required_failure"],
        optional_pending=buckets["optional_pending"],
        optional_failure=buckets["optional_failure"],
    )


def thread_counters(threads: List[ReviewThread]) -> Tuple[int, int, int]:
    unresolved = [thread for thread in threads if not thread.is_resolved]
    unresolved_total = len(unresolved)
    active = len([thread for thread in unresolved if not thread.is_outdated])
    outdated = len([thread for thread in unresolved if thread.is_outdated])
    return unresolved_total, active, outdated
