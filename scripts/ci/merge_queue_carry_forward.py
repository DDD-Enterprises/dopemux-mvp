"""Carry a passing pull-request audit onto a merge-queue commit.

GitHub runs required checks on a temporary merge commit, not on the pull
request head. Unit tests and CodeQL re-run on that commit. The independent
embedded audit and PR Steward status stay bound to the pull request head,
where Grok and AGY review the change. This script lets the queue commit
inherit those two results only when every parent of the queue commit, other
than the queue base, is the current head of an open pull request and that
head already has both results in success.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

AUDIT_CHECK = "independent embedded audit"
STEWARD_CONTEXT = "PR Steward / final readiness"
# GitHub encodes one entry as pr-1466-<sha> and a group as either
# pr-1466-1440-<sha> or pr-1466-pr-1440-<sha>. The suffix is the short sha.
_REF_RE = re.compile(
    r"gh-readonly-queue/[^/]+/(pr-(?:\d+-|pr-\d+-)+)([0-9a-fA-F]{7,40})$"
)


class CarryForwardError(RuntimeError):
    """The queue commit must not inherit pull-request audit results."""


class GitHubView(Protocol):
    def pulls_for_commit(self, sha: str) -> Sequence[Mapping[str, object]]:
        """Return pull requests that contain ``sha``."""

    def check_conclusion(self, sha: str, name: str) -> str | None:
        """Return the latest completed conclusion for a check name."""

    def status_state(self, sha: str, context: str) -> str | None:
        """Return the latest state for a commit-status context."""


ParentsOf = Callable[[str], Sequence[str]]


@dataclass(frozen=True)
class CarryForward:
    pull_requests: tuple[int, ...]
    pull_request_heads: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": True,
            "pull_requests": list(self.pull_requests),
            "pull_request_heads": list(self.pull_request_heads),
        }


def parse_queue_pr_numbers(head_ref: str) -> tuple[int, ...] | None:
    """Return PR numbers encoded in a merge-queue ref, or None if unnamed."""
    ref = head_ref.removeprefix("refs/heads/")
    match = _REF_RE.search(ref)
    if match is None:
        return None
    numbers = tuple(int(number) for number in re.findall(r"\d+", match.group(1)))
    return numbers or None


def merge_pr_heads(
    *,
    head_sha: str,
    base_sha: str,
    parents_of: ParentsOf,
) -> tuple[str, ...]:
    """Walk first parents from the queue head back to the queue base.

    Every merge's other parents are the pull-request heads being tested.
    """
    if head_sha == base_sha:
        raise CarryForwardError("queue head and base are the same commit")
    found: list[str] = []
    current = head_sha
    seen: set[str] = set()
    while current != base_sha:
        if current in seen:
            raise CarryForwardError(f"parent walk cycled at {current}")
        seen.add(current)
        if len(seen) > 25:
            raise CarryForwardError("merge group is deeper than 25 commits")
        parents = tuple(parents_of(current))
        if len(parents) < 2:
            raise CarryForwardError(f"{current} is not a merge commit")
        if parents[0] == current:
            raise CarryForwardError(f"{current} lists itself as a parent")
        found.extend(parents[1:])
        current = parents[0]
    if not found:
        raise CarryForwardError("merge group has no pull-request parents")
    return tuple(found)


def _branch_name(ref: str) -> str:
    """Return the branch name from a short name or a refs/heads full ref."""
    return ref.removeprefix("refs/heads/")


def _open_pr_number(
    pulls: Sequence[Mapping[str, object]],
    *,
    sha: str,
    base_ref: str,
) -> int:
    base_name = _branch_name(base_ref)
    matches: list[int] = []
    for pull in pulls:
        if pull.get("state") != "open":
            continue
        base = pull.get("base")
        head = pull.get("head")
        if not isinstance(base, Mapping) or not isinstance(head, Mapping):
            continue
        if base.get("ref") != base_name or head.get("sha") != sha:
            continue
        number = pull.get("number")
        if isinstance(number, int):
            matches.append(number)
    if len(matches) != 1:
        raise CarryForwardError(
            f"{sha} is not the head of exactly one open pull request "
            f"targeting {base_name}"
        )
    return matches[0]


def evaluate(
    *,
    head_sha: str,
    base_sha: str,
    head_ref: str,
    base_ref: str,
    parents_of: ParentsOf,
    github: GitHubView,
) -> CarryForward:
    pr_heads = merge_pr_heads(
        head_sha=head_sha, base_sha=base_sha, parents_of=parents_of
    )
    numbers: list[int] = []
    for sha in pr_heads:
        number = _open_pr_number(
            github.pulls_for_commit(sha), sha=sha, base_ref=base_ref
        )
        if github.check_conclusion(sha, AUDIT_CHECK) != "success":
            raise CarryForwardError(
                f"PR #{number} head {sha} does not have a successful "
                f"{AUDIT_CHECK} check"
            )
        if github.status_state(sha, STEWARD_CONTEXT) != "success":
            raise CarryForwardError(
                f"PR #{number} head {sha} does not have a successful "
                f"{STEWARD_CONTEXT} status"
            )
        numbers.append(number)
    named = parse_queue_pr_numbers(head_ref)
    # GitHub names the temporary branch for the newest pull request only
    # (`main/pr-2`) even when that commit also contains earlier queued
    # pull requests. Every discovered parent is still required to pass both
    # gates. A name that points at a pull request outside those parents fails.
    if named is not None:
        missing = [number for number in named if number not in numbers]
        if missing:
            raise CarryForwardError(
                "queue ref names PRs " f"{missing} that are not merge parents {numbers}"
            )
    return CarryForward(
        pull_requests=tuple(numbers),
        pull_request_heads=pr_heads,
    )


def git_parents(repo: Path, sha: str) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "rev-parse", f"{sha}^@"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CarryForwardError(f"cannot read parents of {sha}")
    return tuple(parent for parent in result.stdout.split() if parent)


def _check_run_order(run: Mapping[str, object]) -> tuple[int, str]:
    """Sort key: higher GitHub check-run id is newer."""
    raw_id = run.get("id")
    try:
        run_id = int(raw_id)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        run_id = -1
    stamp = str(run.get("started_at") or run.get("completed_at") or "")
    return (run_id, stamp)


class GhApi(GitHubView):
    def __init__(self, repo: str) -> None:
        self.repo = repo

    def _api(self, path: str) -> object:
        result = subprocess.run(
            ["gh", "api", f"repos/{self.repo}/{path}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise CarryForwardError(f"GitHub API failed for {path}")
        return json.loads(result.stdout)

    def pulls_for_commit(self, sha: str) -> Sequence[Mapping[str, object]]:
        payload = self._api(f"commits/{sha}/pulls")
        if not isinstance(payload, list):
            raise CarryForwardError(f"unexpected pulls payload for {sha}")
        return [item for item in payload if isinstance(item, Mapping)]

    def check_conclusion(self, sha: str, name: str) -> str | None:
        matches: list[Mapping[str, object]] = []
        for page in range(1, 11):
            payload = self._api(f"commits/{sha}/check-runs?per_page=100&page={page}")
            if not isinstance(payload, Mapping):
                return None
            runs = payload.get("check_runs")
            if not isinstance(runs, list):
                return None
            matches.extend(
                run
                for run in runs
                if isinstance(run, Mapping) and run.get("name") == name
            )
            if len(runs) < 100:
                break
        if not matches:
            return None
        # Check-run ids increase as GitHub creates runs. A queued rerun can
        # have null timestamps, which sort before an older success and would
        # otherwise hide the rerun. Only a completed success on the highest
        # id may be carried forward.
        matches.sort(key=_check_run_order)
        latest = matches[-1]
        if latest.get("status") != "completed":
            return None
        conclusion = latest.get("conclusion")
        return conclusion if isinstance(conclusion, str) else None

    def status_state(self, sha: str, context: str) -> str | None:
        payload = self._api(f"commits/{sha}/status")
        if not isinstance(payload, Mapping):
            return None
        statuses = payload.get("statuses")
        if not isinstance(statuses, list):
            return None
        for status in statuses:
            if isinstance(status, Mapping) and status.get("context") == context:
                state = status.get("state")
                return state if isinstance(state, str) else None
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--git-dir", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = evaluate(
            head_sha=args.head_sha,
            base_sha=args.base_sha,
            head_ref=args.head_ref,
            base_ref=args.base_ref,
            parents_of=lambda sha: git_parents(args.git_dir, sha),
            github=GhApi(args.repo),
        )
        payload: dict[str, object] = result.to_dict()
        code = 0
    except CarryForwardError as exc:
        payload = {"ok": False, "reason": str(exc)}
        code = 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload))
    return code


if __name__ == "__main__":
    sys.exit(main())
