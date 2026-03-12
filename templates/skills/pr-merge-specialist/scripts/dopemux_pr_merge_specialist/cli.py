from __future__ import annotations

import argparse
import html
import json
import os
import re
import shlex
import subprocess
import sys
import textwrap
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .schema import (
    CheckSummary,
    MergeDecision,
    PRClass,
    PRMergeReport,
    PRState,
    QueueOrderingLayer,
    ReviewThread,
    ThreadComment,
    ThreadDisposition,
    ValidationReport,
    ValidationStepResult,
)


CLASS_PRIORITY: Dict[PRClass, int] = {
    "READY": 1,
    "CI_ONLY": 2,
    "CONFLICTS_ONLY": 3,
    "COMMENTS_ONLY": 4,
    "MIXED": 5,
    "BLOCKED": 6,
}

BOT_AUTHORS = {
    "github-code-quality",
    "copilot-pull-request-reviewer",
    "codecov-commenter",
}

CHECK_SUCCESS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
CHECK_FAILURE = {
    "FAILURE",
    "TIMED_OUT",
    "CANCELLED",
    "ACTION_REQUIRED",
    "STARTUP_FAILURE",
    "STALE",
}


@dataclass(frozen=True)
class CommandResult:
    command: List[str]
    returncode: int
    stdout: str
    stderr: str


def _run_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _shell_join(cmd: Sequence[str]) -> str:
    return " ".join(shlex.quote(x) for x in cmd)


def _run_cmd(cmd: Sequence[str], *, cwd: Optional[Path] = None) -> CommandResult:
    cp = subprocess.run(
        list(cmd),
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(
        command=list(cmd),
        returncode=cp.returncode,
        stdout=cp.stdout,
        stderr=cp.stderr,
    )


def _json_loads_or_empty(raw: str) -> Any:
    if not raw.strip():
        return {}
    return json.loads(raw)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _append_command_log(path: Path, result: CommandResult, *, dry_run: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if path.exists() else "w"
    with path.open(mode, encoding="utf-8") as f:
        f.write(f"$ {_shell_join(result.command)}\n")
        f.write(f"exit={result.returncode}")
        if dry_run:
            f.write(" (dry-run)")
        f.write("\n")
        if result.stdout:
            f.write("--- stdout ---\n")
            f.write(result.stdout.rstrip() + "\n")
        if result.stderr:
            f.write("--- stderr ---\n")
            f.write(result.stderr.rstrip() + "\n")
        f.write("\n")


def _dry_run_result(cmd: Sequence[str]) -> CommandResult:
    return CommandResult(command=list(cmd), returncode=0, stdout="", stderr="")


def _execute_or_dry_run(
    cmd: Sequence[str],
    *,
    execute: bool,
    cwd: Optional[Path],
    commands_log: Path,
) -> CommandResult:
    if execute:
        result = _run_cmd(cmd, cwd=cwd)
        _append_command_log(commands_log, result, dry_run=False)
        return result
    result = _dry_run_result(cmd)
    _append_command_log(commands_log, result, dry_run=True)
    return result


def _require_clean_worktree(repo_root: Path) -> Tuple[bool, str]:
    result = _run_cmd(["git", "status", "--porcelain"], cwd=repo_root)
    if result.returncode != 0:
        return False, result.stderr.strip() or "Unable to evaluate git status"
    if result.stdout.strip():
        return False, result.stdout.strip()
    return True, ""


def _resolve_repo_slug(repo: Optional[str]) -> str:
    if repo:
        return repo
    result = _run_cmd(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
    if result.returncode != 0:
        raise RuntimeError(f"Unable to resolve repo slug: {result.stderr.strip()}")
    slug = result.stdout.strip()
    if not slug or "/" not in slug:
        raise RuntimeError(f"Invalid repo slug response: {slug!r}")
    return slug


def _ci_status(checks: List[Dict[str, Any]]) -> str:
    has_pending = False
    for check in checks:
        status = (check.get("status") or "").upper()
        conclusion = (check.get("conclusion") or "").upper()
        if status and status != "COMPLETED":
            has_pending = True
            continue
        if conclusion in CHECK_FAILURE:
            return "FAILURE"
        if not conclusion and status != "COMPLETED":
            has_pending = True
    return "PENDING" if has_pending else "SUCCESS"


def _check_summary(checks: List[Dict[str, Any]]) -> CheckSummary:
    success = 0
    failure = 0
    pending = 0
    for check in checks:
        status = (check.get("status") or "").upper()
        conclusion = (check.get("conclusion") or "").upper()
        if status and status != "COMPLETED":
            pending += 1
            continue
        if conclusion in CHECK_SUCCESS:
            success += 1
        elif conclusion in CHECK_FAILURE:
            failure += 1
        elif conclusion:
            pending += 1
        else:
            pending += 1
    return CheckSummary(total=len(checks), success=success, failure=failure, pending=pending)


def _has_conflicts(mergeable: str, merge_state_status: str) -> bool:
    mergeable_u = (mergeable or "").upper()
    state_u = (merge_state_status or "").upper()
    return mergeable_u == "CONFLICTING" or state_u in {"DIRTY", "HAS_HOOKS"}


def _classify_pr(
    *,
    ci_status: str,
    has_conflicts: bool,
    active_unresolved_threads: int,
    is_draft: bool,
) -> PRClass:
    if is_draft:
        return "BLOCKED"
    ci_fail = ci_status == "FAILURE"
    has_comments = active_unresolved_threads > 0
    blockers = int(ci_fail) + int(has_conflicts) + int(has_comments)
    if blockers == 0:
        return "READY"
    if blockers > 1:
        return "MIXED"
    if ci_fail:
        return "CI_ONLY"
    if has_conflicts:
        return "CONFLICTS_ONLY"
    if has_comments:
        return "COMMENTS_ONLY"
    return "BLOCKED"


def _risk_score(
    *,
    pr_class: PRClass,
    additions: int,
    deletions: int,
    changed_files: int,
    active_threads: int,
    outdated_threads: int,
    ci_status: str,
    merge_state_status: str,
) -> float:
    diff_size = additions + deletions
    score = float(diff_size) + (changed_files * 10.0)
    score += active_threads * 80.0
    score += outdated_threads * 20.0
    if ci_status == "FAILURE":
        score += 250.0
    elif ci_status == "PENDING":
        score += 90.0
    if merge_state_status.upper() in {"BEHIND"}:
        score += 20.0
    if pr_class == "CONFLICTS_ONLY":
        score += 300.0
    if pr_class == "MIXED":
        score += 200.0
    if pr_class == "BLOCKED":
        score += 500.0
    return score


def _build_pr_state(raw: Dict[str, Any], unresolved_total: int, active_unresolved: int, outdated_unresolved: int) -> PRState:
    checks = raw.get("statusCheckRollup", []) or []
    ci = _ci_status(checks)
    merge_state_status = raw.get("mergeStateStatus") or ""
    has_conflicts = _has_conflicts(raw.get("mergeable") or "", merge_state_status)
    pr_class = _classify_pr(
        ci_status=ci,
        has_conflicts=has_conflicts,
        active_unresolved_threads=active_unresolved,
        is_draft=bool(raw.get("isDraft", False)),
    )
    score = _risk_score(
        pr_class=pr_class,
        additions=int(raw.get("additions", 0) or 0),
        deletions=int(raw.get("deletions", 0) or 0),
        changed_files=int(raw.get("changedFiles", 0) or 0),
        active_threads=active_unresolved,
        outdated_threads=outdated_unresolved,
        ci_status=ci,
        merge_state_status=merge_state_status,
    )
    author = raw.get("author") or {}
    labels = [x.get("name", "") for x in raw.get("labels", []) if isinstance(x, dict)]
    return PRState(
        pr_id=int(raw["number"]),
        title=raw.get("title", ""),
        author=author.get("login", "unknown"),
        state=raw.get("state", "OPEN"),
        base_ref=raw.get("baseRefName", ""),
        head_ref=raw.get("headRefName", ""),
        ci_status=ci,  # type: ignore[arg-type]
        mergeable=raw.get("mergeable", "UNKNOWN"),
        merge_state_status=merge_state_status,
        review_decision=raw.get("reviewDecision") or "",
        labels=labels,
        updated_at=raw.get("updatedAt", ""),
        is_draft=bool(raw.get("isDraft", False)),
        additions=int(raw.get("additions", 0) or 0),
        deletions=int(raw.get("deletions", 0) or 0),
        changed_files=int(raw.get("changedFiles", 0) or 0),
        unresolved_threads=unresolved_total,
        active_unresolved_threads=active_unresolved,
        outdated_unresolved_threads=outdated_unresolved,
        pr_class=pr_class,
        risk_score=score,
        check_summary=_check_summary(checks),
    )


def _fetch_open_prs(limit: int, repo: Optional[str]) -> List[Dict[str, Any]]:
    cmd = [
        "gh",
        "pr",
        "list",
        "--state",
        "open",
        "--limit",
        str(limit),
        "--json",
        "number,title,author,state,statusCheckRollup,mergeable,mergeStateStatus,labels,reviewDecision,updatedAt,baseRefName,headRefName,isDraft,additions,deletions,changedFiles,url",
    ]
    if repo:
        cmd.extend(["--repo", repo])
    result = _run_cmd(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"Unable to fetch open PRs: {result.stderr.strip()}")
    data = _json_loads_or_empty(result.stdout)
    if not isinstance(data, list):
        raise RuntimeError("Unexpected gh pr list payload")
    return data


def _load_queue_states(limit: int, repo: Optional[str], repo_slug: str) -> List[PRState]:
    raws = _fetch_open_prs(limit=limit, repo=repo)
    states: List[PRState] = []
    for raw in raws:
        threads = _fetch_review_threads(repo_slug, int(raw["number"]))
        unresolved, active, outdated = _thread_counters(threads)
        states.append(_build_pr_state(raw, unresolved, active, outdated))
    return states


def _parse_review_threads(payload: Dict[str, Any]) -> List[ReviewThread]:
    nodes = (
        payload.get("data", {})
        .get("repository", {})
        .get("pullRequest", {})
        .get("reviewThreads", {})
        .get("nodes", [])
    )
    threads: List[ReviewThread] = []
    for node in nodes:
        comments_raw = node.get("comments", {}).get("nodes", []) or []
        comments: List[ThreadComment] = []
        for c in comments_raw:
            comments.append(
                ThreadComment(
                    id=str(c.get("id", "")),
                    author=(c.get("author") or {}).get("login", "unknown"),
                    body=c.get("body", ""),
                    created_at=c.get("createdAt", ""),
                    path=c.get("path") or "",
                    line=c.get("line"),
                    original_line=c.get("originalLine"),
                )
            )
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
    return threads


def _fetch_review_threads(repo_slug: str, pr_id: int) -> List[ReviewThread]:
    owner, name = repo_slug.split("/", 1)
    query = textwrap.dedent(
        f"""
        query {{
          repository(owner:"{owner}", name:"{name}") {{
            pullRequest(number:{pr_id}) {{
              reviewThreads(first:100) {{
                nodes {{
                  id
                  isResolved
                  isOutdated
                  viewerCanResolve
                  path
                  line
                  originalLine
                  originalStartLine
                  comments(first:30) {{
                    nodes {{
                      id
                      body
                      path
                      line
                      originalLine
                      createdAt
                      author {{
                        login
                      }}
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        """
    ).strip()
    result = _run_cmd(["gh", "api", "graphql", "-f", f"query={query}"])
    if result.returncode != 0:
        raise RuntimeError(
            f"Unable to fetch review threads for PR {pr_id}: {result.stderr.strip()}"
        )
    payload = _json_loads_or_empty(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("Unexpected GraphQL payload while reading review threads")
    return _parse_review_threads(payload)


def _thread_counters(threads: List[ReviewThread]) -> Tuple[int, int, int]:
    unresolved = [t for t in threads if not t.is_resolved]
    unresolved_total = len(unresolved)
    active = len([t for t in unresolved if not t.is_outdated])
    outdated = len([t for t in unresolved if t.is_outdated])
    return unresolved_total, active, outdated


def _priority_key(pr: PRState) -> Tuple[int, float, int, str, int]:
    return (
        CLASS_PRIORITY.get(pr.pr_class, 99),
        pr.risk_score,
        pr.diff_size,
        pr.updated_at,
        pr.pr_id,
    )


def _build_dependency_edges(states: List[PRState]) -> Dict[int, List[int]]:
    edges: Dict[int, List[int]] = defaultdict(list)
    by_head = {p.head_ref: p.pr_id for p in states if p.head_ref}
    for p in states:
        depends_on = by_head.get(p.base_ref)
        if depends_on and depends_on != p.pr_id:
            edges[depends_on].append(p.pr_id)
    for k in list(edges.keys()):
        edges[k] = sorted(set(edges[k]))
    return dict(edges)


def _sort_states(
    states: List[PRState], strategy: str
) -> Tuple[List[PRState], List[QueueOrderingLayer], Dict[int, List[int]], bool]:
    if len(states) <= 3 or strategy == "simple":
        ordered = sorted(states, key=_priority_key)
        layer = QueueOrderingLayer(layer=0, pr_ids=[x.pr_id for x in ordered])
        return ordered, [layer], {}, False

    edges = _build_dependency_edges(states)
    if not edges:
        ordered = sorted(states, key=_priority_key)
        layer = QueueOrderingLayer(layer=0, pr_ids=[x.pr_id for x in ordered])
        return ordered, [layer], {}, False

    by_id = {x.pr_id: x for x in states}
    indegree: Dict[int, int] = {x.pr_id: 0 for x in states}
    for src, targets in edges.items():
        for dst in targets:
            indegree[dst] = indegree.get(dst, 0) + 1
            indegree.setdefault(src, 0)

    zero = [pid for pid, d in indegree.items() if d == 0]
    queue: deque[int] = deque()
    for pid in sorted(zero, key=lambda p: _priority_key(by_id[p])):
        queue.append(pid)

    ordered_ids: List[int] = []
    layers: List[QueueOrderingLayer] = []
    visited = set()
    layer_idx = 0
    while queue:
        layer_items: List[int] = list(queue)
        queue.clear()
        layer_items = sorted(layer_items, key=lambda p: _priority_key(by_id[p]))
        layers.append(QueueOrderingLayer(layer=layer_idx, pr_ids=layer_items))
        layer_idx += 1
        for pid in layer_items:
            if pid in visited:
                continue
            visited.add(pid)
            ordered_ids.append(pid)
            for child in edges.get(pid, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

    cycle_detected = False
    if len(visited) != len(states):
        cycle_detected = True
        remaining = [p.pr_id for p in states if p.pr_id not in visited]
        remaining_sorted = sorted(remaining, key=lambda p: _priority_key(by_id[p]))
        layers.append(QueueOrderingLayer(layer=layer_idx, pr_ids=remaining_sorted))
        ordered_ids.extend(remaining_sorted)

    ordered = [by_id[x] for x in ordered_ids]
    return ordered, layers, edges, cycle_detected


def _latest_comment(thread: ReviewThread) -> Optional[ThreadComment]:
    if not thread.comments:
        return None
    ordered = sorted(thread.comments, key=lambda c: c.created_at or "")
    return ordered[-1]


def _contains_objection(text: str) -> bool:
    lowered = text.lower()
    markers = [
        "not fixed",
        "still",
        "needs changes",
        "please address",
        "didn't",
        "fails",
        "not resolved",
    ]
    return any(x in lowered for x in markers)


def _signals_resolution(text: str) -> bool:
    lowered = text.lower()
    markers = [
        "addressed",
        "fixed",
        "resolved",
        "done in latest push",
        "updated in latest push",
        "acknowledged",
        "landed in latest push",
    ]
    return any(x in lowered for x in markers)


def _has_newer_objection(thread: ReviewThread) -> bool:
    if not thread.comments:
        return False
    ordered = sorted(thread.comments, key=lambda c: c.created_at or "")
    for comment in reversed(ordered):
        if comment.author in BOT_AUTHORS:
            continue
        return _contains_objection(comment.body)
    return False


def _has_resolution_signal(thread: ReviewThread) -> bool:
    if not thread.comments:
        return False
    for comment in sorted(thread.comments, key=lambda c: c.created_at or "")[1:]:
        if _signals_resolution(comment.body):
            return True
    return False


def _is_implementable_comment(comment: Optional[ThreadComment]) -> bool:
    if comment is None:
        return False
    body = comment.body
    if "```suggestion" in body:
        return True
    if _comment_prefers_conflict_side(body) is not None:
        return True
    if re.search(r"change\s+<code>.*?</code>\s+to\s+<code>.*?</code>", body, re.IGNORECASE | re.DOTALL):
        return True
    if re.search(r"(delete|remove)\s+(the\s+)?(line\s+)?<code>.*?</code>", body, re.IGNORECASE | re.DOTALL):
        return True
    return False


def _comment_prefers_conflict_side(body: str) -> Optional[str]:
    lowered = html.unescape(body).lower()
    if "<<<<<<< head" not in lowered and "conflict marker" not in lowered:
        return None
    if "keep the head side" in lowered or "from the <code>head</code> side" in lowered:
        return "head"
    if "between <code><<<<<<< head</code> and <code>=======</code>" in lowered:
        return "head"
    if "under <code><<<<<<< head</code>" in lowered:
        return "head"
    if "from the <code>head</code> branch" in lowered:
        return "head"
    if "after <code>=======</code>" in lowered or "keep the other side" in lowered:
        return "theirs"
    return None


def _resolve_conflict_markers(text: str, *, prefer: str) -> Tuple[bool, str]:
    if "<<<<<<<" not in text:
        return False, "File does not contain Git conflict markers."

    lines = text.splitlines()
    output: List[str] = []
    i = 0
    changed = False
    while i < len(lines):
        line = lines[i]
        if not line.startswith("<<<<<<<"):
            output.append(line)
            i += 1
            continue

        changed = True
        i += 1
        head_lines: List[str] = []
        while i < len(lines) and not lines[i].startswith("======="):
            head_lines.append(lines[i])
            i += 1
        if i >= len(lines):
            return False, "Malformed conflict block: missing ======= marker."

        i += 1
        other_lines: List[str] = []
        while i < len(lines) and not lines[i].startswith(">>>>>>>"):
            other_lines.append(lines[i])
            i += 1
        if i >= len(lines):
            return False, "Malformed conflict block: missing >>>>>>> marker."

        chosen = head_lines if prefer == "head" else other_lines
        output.extend(chosen)
        i += 1

    resolved = "\n".join(output)
    if text.endswith("\n"):
        resolved += "\n"
    return changed, resolved


def _decide_thread_disposition(
    thread: ReviewThread, validation_green: bool
) -> ThreadDisposition:
    comment = _latest_comment(thread)
    path = comment.path if comment and comment.path else thread.path
    if validation_green and not _has_newer_objection(thread) and (
        thread.is_outdated or _has_resolution_signal(thread)
    ):
        return ThreadDisposition(
            thread_id=thread.id,
            disposition="auto_resolve_outdated",
            reason=(
                "Thread is safe to resolve after green verification and no newer objection."
            ),
            path=path,
        )
    if _is_implementable_comment(comment):
        return ThreadDisposition(
            thread_id=thread.id,
            disposition="implement",
            reason="Thread contains machine-applicable suggestion pattern.",
            path=path,
        )
    return ThreadDisposition(
        thread_id=thread.id,
        disposition="decline_with_rationale",
        reason="Suggestion is not safely auto-applicable; posting rationale and resolving.",
        path=path,
    )


def _extract_suggestion_block(body: str) -> Optional[str]:
    m = re.search(r"```suggestion\s*(.*?)```", body, re.DOTALL | re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip("\n")


def _graphql_escape(value: str) -> str:
    return json.dumps(value)[1:-1]


def _apply_suggestion_to_file(
    *,
    worktree_path: Path,
    thread: ReviewThread,
    comment: ThreadComment,
) -> Tuple[bool, str]:
    target = comment.path or thread.path
    if not target:
        return False, "No path on thread/comment."
    file_path = worktree_path / target
    if not file_path.exists() or not file_path.is_file():
        return False, f"Target file missing: {target}"
    text = file_path.read_text(encoding="utf-8")
    original = text

    preferred_conflict_side = _comment_prefers_conflict_side(comment.body)
    if preferred_conflict_side is not None:
        changed, resolved = _resolve_conflict_markers(text, prefer=preferred_conflict_side)
        if not changed:
            return False, resolved
        if resolved == original:
            return False, "Conflict-marker resolution produced no file changes."
        file_path.write_text(resolved, encoding="utf-8")
        return True, f"Resolved conflict markers in {target} using {preferred_conflict_side} side."

    suggestion = _extract_suggestion_block(comment.body)
    if suggestion is not None:
        start = thread.original_start_line or thread.original_line or thread.line
        end = thread.original_line or thread.line or start
        if start is None or end is None:
            return False, "Suggestion block missing line anchors."
        lines = text.splitlines()
        start_idx = max(start - 1, 0)
        end_idx = max(end, start_idx + 1)
        replacement = suggestion.splitlines()
        new_lines = lines[:start_idx] + replacement + lines[end_idx:]
        text = "\n".join(new_lines) + ("\n" if original.endswith("\n") else "")
    else:
        body = comment.body
        replace_match = re.search(
            r"change\s+<code>(.*?)</code>\s+to\s+<code>(.*?)</code>",
            body,
            re.IGNORECASE | re.DOTALL,
        )
        if replace_match:
            old = html.unescape(replace_match.group(1)).strip()
            new = html.unescape(replace_match.group(2)).strip()
            if old in text:
                text = text.replace(old, new, 1)
            else:
                return False, "Could not locate replacement source fragment in file."
        else:
            delete_match = re.search(
                r"(?:delete|remove)\s+(?:the\s+)?(?:line\s+)?<code>(.*?)</code>",
                body,
                re.IGNORECASE | re.DOTALL,
            )
            if not delete_match:
                return False, "No known machine-applicable suggestion pattern."
            snippet = html.unescape(delete_match.group(1)).strip()
            lines = text.splitlines()
            removed = False
            new_lines: List[str] = []
            for line in lines:
                if not removed and line.strip() == snippet:
                    removed = True
                    continue
                new_lines.append(line)
            if not removed:
                return False, "Could not find deletion snippet in file."
            text = "\n".join(new_lines) + ("\n" if original.endswith("\n") else "")

    if text == original:
        return False, "No file changes produced."
    file_path.write_text(text, encoding="utf-8")
    return True, f"Applied suggestion to {target}."


def _graph_reply_to_thread(thread_id: str, body: str) -> CommandResult:
    escaped_body = _graphql_escape(body)
    escaped_thread_id = _graphql_escape(thread_id)
    query = (
        "mutation { addPullRequestReviewThreadReply(input: "
        f'{{pullRequestReviewThreadId: "{escaped_thread_id}", body: "{escaped_body}"}}) '
        "{ comment { id } } }"
    )
    return _run_cmd(["gh", "api", "graphql", "-f", f"query={query}"])


def _graph_resolve_thread(thread_id: str) -> CommandResult:
    escaped_thread_id = _graphql_escape(thread_id)
    query = (
        "mutation { resolveReviewThread(input: "
        f'{{threadId: "{escaped_thread_id}"}}) {{ thread {{ id isResolved }} }} }}'
    )
    return _run_cmd(["gh", "api", "graphql", "-f", f"query={query}"])


def _prepare_worktree(repo_root: Path, pr_id: int, run_id: str, commands_log: Path) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    branch = f"prmerge/{run_id}-{pr_id}"
    path = Path("/tmp") / f"dopemux-pr-merge-{pr_id}-{run_id}"
    fetch_ref = f"pull/{pr_id}/head:{branch}"
    fetch = _run_cmd(["git", "fetch", "origin", fetch_ref], cwd=repo_root)
    _append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return None, None, fetch.stderr.strip() or "git fetch failed"
    add = _run_cmd(["git", "worktree", "add", str(path), branch], cwd=repo_root)
    _append_command_log(commands_log, add)
    if add.returncode != 0:
        return None, None, add.stderr.strip() or "git worktree add failed"
    return path, branch, None


def _cleanup_worktree(repo_root: Path, worktree_path: Path, branch: str, commands_log: Path) -> None:
    rm = _run_cmd(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=repo_root)
    _append_command_log(commands_log, rm)
    _run_cmd(["git", "branch", "-D", branch], cwd=repo_root)


def _attempt_rebase(
    *,
    pr_id: int,
    worktree_path: Path,
    base_ref: str,
    head_ref: str,
    commands_log: Path,
    execute: bool,
) -> Tuple[bool, bool, str]:
    cmd_update = ["gh", "pr", "update-branch", str(pr_id), "--rebase"]
    update_res = _execute_or_dry_run(
        cmd_update,
        execute=execute,
        cwd=worktree_path,
        commands_log=commands_log,
    )
    if execute and update_res.returncode != 0:
        if "conflict" in update_res.stderr.lower():
            fetch_base = _run_cmd(["git", "fetch", "origin", base_ref], cwd=worktree_path)
            _append_command_log(commands_log, fetch_base)
            if fetch_base.returncode != 0:
                return False, True, (
                    update_res.stderr.strip()
                    + "\n\n"
                    + (fetch_base.stderr.strip() or "Unable to fetch base ref for local conflict inspection.")
                )
            local_rebase = _run_cmd(["git", "rebase", f"origin/{base_ref}"], cwd=worktree_path)
            _append_command_log(commands_log, local_rebase)
            details = local_rebase.stderr.strip() or local_rebase.stdout.strip()
            if details:
                return False, True, update_res.stderr.strip() + "\n\nLocal conflict reproduction:\n" + details
            return False, True, update_res.stderr.strip()
    if not execute:
        return True, False, "dry-run"

    # `gh pr update-branch --rebase` already updates the remote PR branch. Refresh the
    # disposable worktree to that remote state instead of rebasing/pushing it again.
    fetch = _run_cmd(["git", "fetch", "origin", head_ref], cwd=worktree_path)
    _append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return False, False, fetch.stderr.strip() or "git fetch for head failed"
    reset = _run_cmd(["git", "reset", "--hard", f"origin/{head_ref}"], cwd=worktree_path)
    _append_command_log(commands_log, reset)
    if reset.returncode != 0:
        return False, False, reset.stderr.strip() or "git reset to rebased head failed"
    return True, False, "rebase updated and worktree refreshed"


def _conflict_files(worktree_path: Path) -> List[str]:
    status = _run_cmd(["git", "status", "--porcelain"], cwd=worktree_path)
    if status.returncode != 0:
        return []
    files: List[str] = []
    for line in status.stdout.splitlines():
        if line.startswith("UU ") or line.startswith("AA ") or line.startswith("DD "):
            files.append(line[3:].strip())
    return files


def _conflict_excerpt(worktree_path: Path, rel_path: str, *, context_lines: int = 3) -> str:
    file_path = worktree_path / rel_path
    if not file_path.exists() or not file_path.is_file():
        return "File unavailable for conflict excerpt."

    lines = file_path.read_text(encoding="utf-8").splitlines()
    excerpts: List[str] = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith("<<<<<<<"):
            i += 1
            continue
        start = max(i - context_lines, 0)
        end = min(i + 1, len(lines))
        while end < len(lines) and not lines[end].startswith(">>>>>>>"):
            end += 1
        if end < len(lines):
            end += 1
        end = min(end + context_lines, len(lines))
        block = "\n".join(
            f"{line_no + 1:>4}: {content}" for line_no, content in enumerate(lines[start:end], start=start)
        )
        excerpts.append(block)
        i = end
        if len(excerpts) >= 2:
            break
    if not excerpts:
        return "No conflict markers found in working tree file."
    return "\n\n".join(excerpts)


def _recent_file_history(worktree_path: Path, rel_path: str, *, limit: int = 5) -> List[str]:
    history = _run_cmd(["git", "log", "--oneline", f"-n{limit}", "--", rel_path], cwd=worktree_path)
    if history.returncode != 0 or not history.stdout.strip():
        return []
    return [line.strip() for line in history.stdout.splitlines() if line.strip()]


def _build_conflict_analysis(
    *,
    pr: PRState,
    worktree_path: Optional[Path],
    rebase_error: str,
    strict_conflicts: bool,
) -> str:
    lines = [
        f"# Conflict Analysis for PR #{pr.pr_id}",
        "",
        "## Classification",
        "- conflict_type: semantic_or_unknown",
        f"- strict_conflicts: {strict_conflicts}",
        "",
        "## PR Context",
        f"- title: {pr.title}",
        f"- base_ref: {pr.base_ref}",
        f"- head_ref: {pr.head_ref}",
        f"- merge_state_status: {pr.merge_state_status}",
        f"- ci_status: {pr.ci_status}",
        "",
        "## Rebase Failure Signal",
        "```text",
        rebase_error or "no error text available",
        "```",
        "",
        "## Deep Inspection Protocol",
        "1. Inspect conflict hunks (base/ours/theirs) and surrounding commit intent.",
        "2. Compare behavior impact, not text-only resolution convenience.",
        "3. Reject blanket `-X ours/-X theirs` strategies.",
        "4. Require scoped tests plus full validation when conflict touches shared primitives.",
        "5. Escalate if confidence is below release safety threshold.",
        "",
    ]
    if worktree_path:
        files = _conflict_files(worktree_path)
        file_lines = [f"- {x}" for x in files] if files else ["- none detected"]
        lines.extend(["## Conflicting Files", *file_lines])
        lines.append("")
        if files:
            lines.append("## Conflict Hunks")
            for rel_path in files:
                lines.extend(
                    [
                        f"### {rel_path}",
                        "```text",
                        _conflict_excerpt(worktree_path, rel_path),
                        "```",
                        "",
                    ]
                )
            lines.append("## Recent File History")
            for rel_path in files:
                history = _recent_file_history(worktree_path, rel_path)
                lines.append(f"### {rel_path}")
                if history:
                    lines.extend([f"- {entry}" for entry in history])
                else:
                    lines.append("- no recent history available")
                lines.append("")
    lines.extend(
        [
            "## Resolution Decision",
            "- status: escalated",
            "- reason: strict conflict mode requires explicit semantic resolution evidence.",
        ]
    )
    return "\n".join(lines) + "\n"


def _run_validation_steps(
    *,
    worktree_path: Path,
    commands_log: Path,
    execute: bool,
) -> ValidationReport:
    commands = [
        ("pre-commit", ["pre-commit", "run", "--all-files"]),
        ("docs-frontmatter-fix", ["python", "scripts/docs_frontmatter_guard.py", "--fix"]),
        ("docs-validator", ["python", "scripts/docs_validator.py"]),
        ("docs-hygiene", ["python", "scripts/check_docs_hygiene.py", "--check", "--all-files"]),
        (
            "docs-filename-hygiene",
            ["python", "scripts/check_docs_filename_hygiene.py", "--check", "--all-files"],
        ),
        ("root-hygiene", ["python", "scripts/check_root_hygiene.py"]),
    ]
    all_steps: List[ValidationStepResult] = []

    def run_once() -> bool:
        ok = True
        for step_name, cmd in commands:
            result = _execute_or_dry_run(
                cmd,
                execute=execute,
                cwd=worktree_path,
                commands_log=commands_log,
            )
            all_steps.append(
                ValidationStepResult(
                    name=step_name,
                    command=_shell_join(cmd),
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            )
            if result.returncode != 0:
                ok = False
        return ok

    passed_first = run_once()
    if passed_first:
        return ValidationReport(
            passed=True,
            steps=all_steps,
            attempts=1,
            remediation_applied=False,
        )

    remediation = _execute_or_dry_run(
        ["python", "scripts/docs_frontmatter_guard.py", "--fix"],
        execute=execute,
        cwd=worktree_path,
        commands_log=commands_log,
    )
    all_steps.append(
        ValidationStepResult(
            name="docs-frontmatter-remediation",
            command="python scripts/docs_frontmatter_guard.py --fix",
            returncode=remediation.returncode,
            stdout=remediation.stdout,
            stderr=remediation.stderr,
        )
    )
    passed_second = run_once()
    return ValidationReport(
        passed=passed_second,
        steps=all_steps,
        attempts=2,
        remediation_applied=True,
    )


def _validation_report_md(report: ValidationReport) -> str:
    lines = [
        "# Validation Report",
        "",
        f"- passed: {report.passed}",
        f"- attempts: {report.attempts}",
        f"- remediation_applied: {report.remediation_applied}",
        "",
        "## Steps",
    ]
    for step in report.steps:
        lines.extend(
            [
                f"### {step.name}",
                f"- command: `{step.command}`",
                f"- exit_code: {step.returncode}",
                "",
            ]
        )
        if step.stdout.strip():
            lines.extend(["```text", step.stdout.strip(), "```", ""])
        if step.stderr.strip():
            lines.extend(["```text", step.stderr.strip(), "```", ""])
    return "\n".join(lines).rstrip() + "\n"


def _checks_green(pr_id: int, repo: Optional[str]) -> Tuple[bool, Dict[str, Any]]:
    cmd = ["gh", "pr", "view", str(pr_id), "--json", "statusCheckRollup,mergeable,mergeStateStatus,reviewDecision"]
    if repo:
        cmd.extend(["--repo", repo])
    result = _run_cmd(cmd)
    if result.returncode != 0:
        return False, {"error": result.stderr.strip() or "Unable to query PR checks"}
    payload = _json_loads_or_empty(result.stdout)
    checks = payload.get("statusCheckRollup", []) or []
    pending = 0
    failures = 0
    successes = 0
    for c in checks:
        status = (c.get("status") or "").upper()
        conclusion = (c.get("conclusion") or "").upper()
        if status and status != "COMPLETED":
            pending += 1
            continue
        if conclusion in CHECK_FAILURE:
            failures += 1
        elif conclusion in CHECK_SUCCESS:
            successes += 1
        elif not conclusion:
            pending += 1
    green = failures == 0 and pending == 0
    return green, {
        "checks_total": len(checks),
        "checks_success": successes,
        "checks_failure": failures,
        "checks_pending": pending,
        "mergeable": payload.get("mergeable", ""),
        "merge_state_status": payload.get("mergeStateStatus", ""),
        "review_decision": payload.get("reviewDecision") or "",
    }


def _wait_for_green_checks(
    *,
    pr_id: int,
    repo: Optional[str],
    execute: bool,
    max_wait_seconds: int,
    poll_interval_seconds: int,
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    checks_green, payload = _checks_green(pr_id, repo)
    history: List[Dict[str, Any]] = [
        {
            "attempt": 1,
            "green": checks_green,
            **payload,
        }
    ]
    pending = int(payload.get("checks_pending", 0) or 0)
    failures = int(payload.get("checks_failure", 0) or 0)
    if (
        not execute
        or checks_green
        or max_wait_seconds <= 0
        or pending == 0
        or failures > 0
    ):
        return checks_green, payload, {
            "waited": False,
            "timed_out": False,
            "attempts": len(history),
            "history": history,
        }

    deadline = time.time() + max_wait_seconds
    interval = max(poll_interval_seconds, 1)
    waited = False
    while time.time() < deadline:
        time.sleep(interval)
        waited = True
        checks_green, payload = _checks_green(pr_id, repo)
        history.append(
            {
                "attempt": len(history) + 1,
                "green": checks_green,
                **payload,
            }
        )
        pending = int(payload.get("checks_pending", 0) or 0)
        failures = int(payload.get("checks_failure", 0) or 0)
        if checks_green or pending == 0 or failures > 0:
            break

    pending = int(payload.get("checks_pending", 0) or 0)
    return checks_green, payload, {
        "waited": waited,
        "timed_out": waited and not checks_green and pending > 0,
        "attempts": len(history),
        "history": history,
    }


def _decide_merge_action(
    *,
    pr: PRState,
    checks_green: bool,
    active_unresolved_threads: int,
) -> MergeDecision:
    if active_unresolved_threads > 0:
        return MergeDecision(
            action="blocked",
            command=[],
            reason=f"{active_unresolved_threads} active unresolved review threads remain.",
        )
    if not checks_green:
        return MergeDecision(
            action="blocked",
            command=[],
            reason="Required checks are not fully green.",
        )
    return MergeDecision(
        action="rebase_merge",
        command=["gh", "pr", "merge", str(pr.pr_id), "--rebase", "--delete-branch"],
        reason="All gates are green; rebase merge selected by default.",
    )


def _run_merge_with_fallback(
    *,
    decision: MergeDecision,
    pr_id: int,
    execute: bool,
    repo: Optional[str],
    commands_log: Path,
) -> MergeDecision:
    if decision.action == "blocked":
        return decision
    cmd = list(decision.command)
    if repo:
        cmd.extend(["--repo", repo])
    result = _execute_or_dry_run(
        cmd,
        execute=execute,
        cwd=None,
        commands_log=commands_log,
    )
    if not execute:
        return decision
    if result.returncode == 0:
        return decision
    stderr = (result.stderr or "").lower()
    if "already merged" in stderr:
        state_cmd = ["gh", "pr", "view", str(pr_id), "--json", "state", "--jq", ".state"]
        if repo:
            state_cmd.extend(["--repo", repo])
        state = _run_cmd(state_cmd)
        if state.returncode == 0 and state.stdout.strip().upper() == "MERGED":
            return MergeDecision(
                action="rebase_merge",
                command=cmd,
                reason="PR was already merged; local branch cleanup failure treated as non-blocking.",
            )
    if "merge queue" in stderr or "auto-merge" in stderr or "rebase" in stderr:
        fallback_cmd = ["gh", "pr", "merge", str(pr_id), "--auto", "--delete-branch"]
        if repo:
            fallback_cmd.extend(["--repo", repo])
        fallback = _execute_or_dry_run(
            fallback_cmd,
            execute=execute,
            cwd=None,
            commands_log=commands_log,
        )
        if fallback.returncode == 0:
            return MergeDecision(
                action="auto_merge_fallback",
                command=fallback_cmd,
                reason="Rebase merge blocked by policy/queue; auto-merge fallback succeeded.",
            )
        return MergeDecision(
            action="blocked",
            command=fallback_cmd,
            reason=f"Fallback auto-merge failed: {fallback.stderr.strip()}",
        )
    return MergeDecision(
        action="blocked",
        command=cmd,
        reason=f"Rebase merge failed: {result.stderr.strip()}",
    )


def _apply_thread_dispositions(
    *,
    dispositions: List[ThreadDisposition],
    threads_by_id: Dict[str, ReviewThread],
    worktree_path: Path,
    execute: bool,
    commands_log: Path,
    strict_conflicts: bool,
) -> List[ThreadDisposition]:
    applied: List[ThreadDisposition] = []
    for d in dispositions:
        thread = threads_by_id[d.thread_id]
        comment = _latest_comment(thread)
        if d.disposition == "implement":
            if comment is None:
                applied.append(
                    ThreadDisposition(
                        thread_id=d.thread_id,
                        disposition="escalate",
                        reason="No comment payload found for implement disposition.",
                        path=d.path,
                        escalation_needed=True,
                    )
                )
                continue
            ok, reason = _apply_suggestion_to_file(
                worktree_path=worktree_path,
                thread=thread,
                comment=comment,
            )
            if not ok:
                applied.append(
                    ThreadDisposition(
                        thread_id=d.thread_id,
                        disposition="escalate" if strict_conflicts else "decline_with_rationale",
                        reason=f"Auto-implement failed: {reason}",
                        path=d.path,
                        escalation_needed=strict_conflicts,
                    )
                )
                continue
            if execute:
                _append_command_log(
                    commands_log,
                    _graph_reply_to_thread(
                        d.thread_id,
                        "Automated queue-drain applied a minimal fix and will run verification before merge.",
                    ),
                )
                _append_command_log(commands_log, _graph_resolve_thread(d.thread_id))
            applied.append(
                ThreadDisposition(
                    thread_id=d.thread_id,
                    disposition="implement",
                    reason=reason,
                    path=d.path,
                    applied=True,
                    escalation_needed=False,
                )
            )
            continue

        if d.disposition == "decline_with_rationale":
            if execute:
                _append_command_log(
                    commands_log,
                    _graph_reply_to_thread(
                        d.thread_id,
                        "Automated queue-drain could not safely auto-apply this suggestion. Keeping behavior deterministic and deferring to a targeted follow-up fix.",
                    ),
                )
                _append_command_log(commands_log, _graph_resolve_thread(d.thread_id))
            applied.append(
                ThreadDisposition(
                    thread_id=d.thread_id,
                    disposition="decline_with_rationale",
                    reason=d.reason,
                    path=d.path,
                    applied=True,
                    escalation_needed=False,
                )
            )
            continue

        if d.disposition == "auto_resolve_outdated":
            if execute:
                _append_command_log(
                    commands_log,
                    _graph_reply_to_thread(
                        d.thread_id,
                        "Outdated thread auto-resolved after re-validation with no newer objections.",
                    ),
                )
                _append_command_log(commands_log, _graph_resolve_thread(d.thread_id))
            applied.append(
                ThreadDisposition(
                    thread_id=d.thread_id,
                    disposition="auto_resolve_outdated",
                    reason=d.reason,
                    path=d.path,
                    applied=True,
                    escalation_needed=False,
                )
            )
            continue

        applied.append(d)
    return applied


def _stage_and_push_if_needed(
    *,
    worktree_path: Path,
    head_ref: str,
    run_id: str,
    pr_id: int,
    execute: bool,
    commands_log: Path,
) -> bool:
    status = _execute_or_dry_run(
        ["git", "status", "--porcelain"],
        execute=execute,
        cwd=worktree_path,
        commands_log=commands_log,
    )
    if not execute:
        return bool(status.stdout.strip())
    if status.returncode != 0:
        return False
    if not status.stdout.strip():
        return False
    add = _run_cmd(["git", "add", "-A"], cwd=worktree_path)
    _append_command_log(commands_log, add)
    if add.returncode != 0:
        return False
    commit = _run_cmd(
        [
            "git",
            "commit",
            "-m",
            f"review-response: address thread suggestions (pr-merge/{run_id}/PR-{pr_id})",
        ],
        cwd=worktree_path,
    )
    _append_command_log(commands_log, commit)
    if commit.returncode != 0:
        return False
    push = _run_cmd(
        ["git", "push", "origin", f"HEAD:{head_ref}", "--force-with-lease"],
        cwd=worktree_path,
    )
    _append_command_log(commands_log, push)
    return push.returncode == 0


def _update_remaining_pr_bases(
    *,
    remaining: Iterable[int],
    execute: bool,
    repo: Optional[str],
    commands_log: Path,
) -> List[Dict[str, Any]]:
    updates: List[Dict[str, Any]] = []
    for pr_id in remaining:
        cmd = ["gh", "pr", "update-branch", str(pr_id), "--rebase"]
        if repo:
            cmd.extend(["--repo", repo])
        result = _execute_or_dry_run(
            cmd,
            execute=execute,
            cwd=None,
            commands_log=commands_log,
        )
        updates.append(
            {
                "pr_id": pr_id,
                "command": cmd,
                "returncode": result.returncode,
                "stderr": result.stderr.strip(),
                "stdout": result.stdout.strip(),
            }
        )
    return updates


def _snapshot_payload(states: List[PRState]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for pr in states:
        payload.append(
            {
                "pr_id": pr.pr_id,
                "title": pr.title,
                "author": pr.author,
                "base_ref": pr.base_ref,
                "head_ref": pr.head_ref,
                "ci_status": pr.ci_status,
                "mergeable": pr.mergeable,
                "merge_state_status": pr.merge_state_status,
                "review_decision": pr.review_decision,
                "unresolved_threads": pr.unresolved_threads,
                "active_unresolved_threads": pr.active_unresolved_threads,
                "outdated_unresolved_threads": pr.outdated_unresolved_threads,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "diff_size": pr.diff_size,
                "pr_class": pr.pr_class,
                "risk_score": pr.risk_score,
                "updated_at": pr.updated_at,
                "is_draft": pr.is_draft,
            }
        )
    return payload


def _queue_scan(args: argparse.Namespace) -> int:
    repo_slug = _resolve_repo_slug(args.repo)
    raws = _fetch_open_prs(limit=args.limit, repo=args.repo)
    states: List[PRState] = []
    for raw in raws:
        threads = _fetch_review_threads(repo_slug, int(raw["number"]))
        unresolved, active, outdated = _thread_counters(threads)
        states.append(_build_pr_state(raw, unresolved, active, outdated))
    ordered, layers, edges, cycle = _sort_states(states, args.strategy)

    print(f"Open PRs: {len(states)}")
    print(f"Ordering strategy: {args.strategy}")
    if cycle:
        print("Cycle detected in dependency graph; fallback ordering applied for remaining nodes.")
    print("")
    for idx, pr in enumerate(ordered, start=1):
        print(
            f"{idx:>2}. PR #{pr.pr_id:<4} class={pr.pr_class:<14} risk={pr.risk_score:>8.1f} "
            f"ci={pr.ci_status:<7} threads(active={pr.active_unresolved_threads}, outdated={pr.outdated_unresolved_threads}) "
            f"head={pr.head_ref} base={pr.base_ref}"
        )

    if args.out_dir:
        run_dir = Path(args.out_dir) / f"scan_{_run_id()}"
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_json(run_dir / "QUEUE_SNAPSHOT.json", _snapshot_payload(states))
        _write_json(
            run_dir / "ORDERING_PLAN.json",
            {
                "strategy": args.strategy,
                "cycle_detected": cycle,
                "layers": [{"layer": l.layer, "pr_ids": l.pr_ids} for l in layers],
                "edges": edges,
                "ordered_pr_ids": [x.pr_id for x in ordered],
            },
        )
        print(f"\nArtifacts written to: {run_dir}")
    return 0


def _queue_drain(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    run_id = _run_id()
    run_dir = Path(args.out_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    run_commands_log = run_dir / "COMMANDS_RUN.txt"

    repo_slug = _resolve_repo_slug(args.repo)
    max_passes = max(int(getattr(args, "max_passes", 1) or 1), 1)
    target_pr_ids: Optional[set[int]] = None
    summary_by_pr: Dict[int, Dict[str, Any]] = {}
    merged_ids: List[int] = []
    processed_ids: set[int] = set()
    global_base_updates: List[Dict[str, Any]] = []
    pass_reports: List[Dict[str, Any]] = []

    for pass_index in range(1, max_passes + 1):
        states = _load_queue_states(limit=args.limit, repo=args.repo, repo_slug=repo_slug)
        ordered, layers, edges, cycle = _sort_states(states, args.strategy)
        if target_pr_ids is None and args.max_prs > 0:
            target_pr_ids = {pr.pr_id for pr in ordered[: args.max_prs]}
        if target_pr_ids is not None:
            ordered = [pr for pr in ordered if pr.pr_id in target_pr_ids]
            states = [pr for pr in states if pr.pr_id in target_pr_ids]

        _write_json(run_dir / "QUEUE_SNAPSHOT.json", _snapshot_payload(states))
        _write_json(
            run_dir / "ORDERING_PLAN.json",
            {
                "strategy": args.strategy,
                "queue_size": len(states),
                "processed_count": len(ordered),
                "cycle_detected": cycle,
                "pass_index": pass_index,
                "layers": [{"layer": l.layer, "pr_ids": l.pr_ids} for l in layers],
                "edges": edges,
                "ordered_pr_ids": [x.pr_id for x in ordered],
            },
        )

        if not ordered:
            pass_reports.append(
                {
                    "pass_index": pass_index,
                    "queue_size": len(states),
                    "processed": 0,
                    "merged": 0,
                    "thread_actions_applied": 0,
                    "pending_checks_seen": 0,
                    "restarted_after_merge": False,
                }
            )
            break

        merged_this_pass = 0
        thread_actions_applied = 0
        pending_checks_seen = 0
        restart_after_merge = False

        for idx, pr in enumerate(ordered):
            processed_ids.add(pr.pr_id)
            pr_dir = run_dir / f"PR-{pr.pr_id}"
            pr_dir.mkdir(parents=True, exist_ok=True)
            pr_commands = pr_dir / "COMMANDS_RUN.txt"
            _write_json(pr_dir / "INTAKE.json", _snapshot_payload([pr])[0])

            worktree_path: Optional[Path] = None
            branch: Optional[str] = None
            blockers: List[str] = []

            if args.execute:
                worktree_path, branch, err = _prepare_worktree(
                    repo_root=repo_root,
                    pr_id=pr.pr_id,
                    run_id=run_id,
                    commands_log=pr_commands,
                )
                if err or worktree_path is None or branch is None:
                    blockers.append(f"worktree setup failed: {err}")

            if not blockers:
                if args.execute and worktree_path is not None:
                    ok, conflict, msg = _attempt_rebase(
                        pr_id=pr.pr_id,
                        worktree_path=worktree_path,
                        base_ref=pr.base_ref,
                        head_ref=pr.head_ref,
                        commands_log=pr_commands,
                        execute=args.execute,
                    )
                    if not ok and conflict:
                        analysis = _build_conflict_analysis(
                            pr=pr,
                            worktree_path=worktree_path,
                            rebase_error=msg,
                            strict_conflicts=args.strict_conflicts,
                        )
                        (pr_dir / "CONFLICT_ANALYSIS.md").write_text(analysis, encoding="utf-8")
                        blockers.append("rebase conflict encountered")
                    elif not ok:
                        blockers.append(f"rebase update failed: {msg}")
                else:
                    _execute_or_dry_run(
                        ["gh", "pr", "update-branch", str(pr.pr_id), "--rebase"],
                        execute=False,
                        cwd=None,
                        commands_log=pr_commands,
                    )

            threads = _fetch_review_threads(repo_slug, pr.pr_id)
            _write_json(
                pr_dir / "REVIEW_THREADS.json",
                {
                    "threads": [
                        {
                            "id": t.id,
                            "is_resolved": t.is_resolved,
                            "is_outdated": t.is_outdated,
                            "path": t.path,
                            "line": t.line,
                            "original_line": t.original_line,
                            "original_start_line": t.original_start_line,
                            "comments": [
                                {
                                    "id": c.id,
                                    "author": c.author,
                                    "created_at": c.created_at,
                                    "path": c.path,
                                    "line": c.line,
                                    "original_line": c.original_line,
                                    "body": c.body,
                                }
                                for c in t.comments
                            ],
                        }
                        for t in threads
                    ]
                },
            )

            validation_green_pre = pr.ci_status == "SUCCESS"
            unresolved_threads = [t for t in threads if not t.is_resolved]
            planned_dispositions = [
                _decide_thread_disposition(t, validation_green=validation_green_pre) for t in unresolved_threads
            ]

            applied_dispositions = planned_dispositions
            if args.execute and worktree_path is not None:
                applied_dispositions = _apply_thread_dispositions(
                    dispositions=planned_dispositions,
                    threads_by_id={t.id: t for t in threads},
                    worktree_path=worktree_path,
                    execute=args.execute,
                    commands_log=pr_commands,
                    strict_conflicts=args.strict_conflicts,
                )
                _stage_and_push_if_needed(
                    worktree_path=worktree_path,
                    head_ref=pr.head_ref,
                    run_id=run_id,
                    pr_id=pr.pr_id,
                    execute=args.execute,
                    commands_log=pr_commands,
                )

            thread_actions_applied += len([d for d in applied_dispositions if d.applied])
            _write_json(
                pr_dir / "THREAD_DISPOSITIONS.json",
                {
                    "planned": [
                        {
                            "thread_id": d.thread_id,
                            "disposition": d.disposition,
                            "reason": d.reason,
                            "path": d.path,
                        }
                        for d in planned_dispositions
                    ],
                    "applied": [
                        {
                            "thread_id": d.thread_id,
                            "disposition": d.disposition,
                            "reason": d.reason,
                            "path": d.path,
                            "applied": d.applied,
                            "escalation_needed": d.escalation_needed,
                        }
                        for d in applied_dispositions
                    ],
                },
            )

            if args.execute and worktree_path is not None:
                validation = _run_validation_steps(
                    worktree_path=worktree_path,
                    commands_log=pr_commands,
                    execute=args.execute,
                )
            else:
                validation = ValidationReport(passed=True, steps=[], attempts=1, remediation_applied=False)
            (pr_dir / "VALIDATION_REPORT.md").write_text(_validation_report_md(validation), encoding="utf-8")

            current_threads = _fetch_review_threads(repo_slug, pr.pr_id)
            unresolved_now, active_now, _ = _thread_counters(current_threads)
            if active_now > 0:
                blockers.append(f"{active_now} active unresolved review threads remain")
            if not validation.passed:
                blockers.append("validation pipeline failed")

            checks_green = False
            checks_payload: Dict[str, Any] = {}
            check_wait_payload: Dict[str, Any] = {
                "waited": False,
                "timed_out": False,
                "attempts": 0,
                "history": [],
            }
            if not blockers:
                checks_green, checks_payload, check_wait_payload = _wait_for_green_checks(
                    pr_id=pr.pr_id,
                    repo=args.repo,
                    execute=args.execute,
                    max_wait_seconds=getattr(args, "check_wait_seconds", 900),
                    poll_interval_seconds=getattr(args, "check_poll_seconds", 30),
                )
                pending_checks_seen += int(checks_payload.get("checks_pending", 0) or 0)
                current_threads = _fetch_review_threads(repo_slug, pr.pr_id)
                unresolved_now, active_now, _ = _thread_counters(current_threads)
                if active_now > 0:
                    blockers.append(f"{active_now} active unresolved review threads remain")
            else:
                checks_green, checks_payload = _checks_green(pr.pr_id, args.repo)
                pending_checks_seen += int(checks_payload.get("checks_pending", 0) or 0)

            decision = _decide_merge_action(
                pr=pr,
                checks_green=checks_green,
                active_unresolved_threads=active_now,
            )
            if blockers:
                decision = MergeDecision(
                    action="blocked",
                    command=[],
                    reason="; ".join(blockers),
                )

            merge_result = _run_merge_with_fallback(
                decision=decision,
                pr_id=pr.pr_id,
                execute=args.execute,
                repo=args.repo,
                commands_log=pr_commands,
            )
            _write_json(
                pr_dir / "MERGE_DECISION.json",
                {
                    "decision": {
                        "action": merge_result.action,
                        "command": merge_result.command,
                        "reason": merge_result.reason,
                    },
                    "checks": checks_payload,
                    "check_wait": check_wait_payload,
                    "unresolved_threads_after_disposition": unresolved_now,
                    "active_unresolved_threads_after_disposition": active_now,
                    "pass_index": pass_index,
                },
            )

            status = "blocked"
            if merge_result.action in {"rebase_merge", "auto_merge_fallback"}:
                if args.execute:
                    status = "merged"
                    merged_ids.append(pr.pr_id)
                    merged_this_pass += 1

                    remaining_ids = [x.pr_id for x in ordered[idx + 1 :]]
                    updates = _update_remaining_pr_bases(
                        remaining=remaining_ids,
                        execute=args.execute,
                        repo=args.repo,
                        commands_log=run_commands_log,
                    )
                    global_base_updates.extend(
                        [{"trigger_pr": pr.pr_id, "pass_index": pass_index, **item} for item in updates]
                    )
                    restart_after_merge = True
                else:
                    status = "merge_ready"

            report = PRMergeReport(
                run_id=run_id,
                pr_id=pr.pr_id,
                status=status,  # type: ignore[arg-type]
                status_reason=merge_result.reason,
                pr_state=pr,
                merge_decision=merge_result,
                thread_dispositions=applied_dispositions,
                blockers=blockers,
                artifacts={
                    "intake": str(pr_dir / "INTAKE.json"),
                    "review_threads": str(pr_dir / "REVIEW_THREADS.json"),
                    "thread_dispositions": str(pr_dir / "THREAD_DISPOSITIONS.json"),
                    "validation_report": str(pr_dir / "VALIDATION_REPORT.md"),
                    "merge_decision": str(pr_dir / "MERGE_DECISION.json"),
                    "commands": str(pr_commands),
                },
            )
            _write_json(pr_dir / "RESULT.json", report.to_dict())
            summary_by_pr[pr.pr_id] = {
                "pr_id": pr.pr_id,
                "title": pr.title,
                "status": status,
                "status_reason": merge_result.reason,
                "merge_action": merge_result.action,
                "pass_index": pass_index,
            }

            if args.execute and worktree_path is not None and branch is not None:
                _cleanup_worktree(
                    repo_root=repo_root,
                    worktree_path=worktree_path,
                    branch=branch,
                    commands_log=pr_commands,
                )

            if restart_after_merge:
                break

        pass_reports.append(
            {
                "pass_index": pass_index,
                "queue_size": len(states),
                "processed": len(ordered),
                "merged": merged_this_pass,
                "thread_actions_applied": thread_actions_applied,
                "pending_checks_seen": pending_checks_seen,
                "restarted_after_merge": restart_after_merge,
            }
        )

        remaining_states = _load_queue_states(limit=args.limit, repo=args.repo, repo_slug=repo_slug)
        if target_pr_ids is not None:
            remaining_states = [pr for pr in remaining_states if pr.pr_id in target_pr_ids]

        should_continue = False
        if restart_after_merge:
            should_continue = True
        elif args.execute and remaining_states and (
            thread_actions_applied > 0 or pending_checks_seen > 0
        ):
            should_continue = True
        if not should_continue:
            break

    summaries = [summary_by_pr[pr_id] for pr_id in sorted(summary_by_pr)]
    _write_json(run_dir / "PASS_REPORTS.json", pass_reports)
    _write_json(run_dir / "BASE_REBASE_UPDATES.json", global_base_updates)
    _write_json(
        run_dir / "QUEUE_REPORT.json",
        {
            "run_id": run_id,
            "execute": args.execute,
            "strategy": args.strategy,
            "processed": len(processed_ids),
            "merged": len(merged_ids),
            "blocked": len([x for x in summaries if x["status"] == "blocked"]),
            "merged_ids": merged_ids,
            "passes": pass_reports,
            "summaries": summaries,
        },
    )

    print(f"Run ID: {run_id}")
    print(f"Processed PRs: {len(processed_ids)}")
    print(f"Merged: {len(merged_ids)}")
    print(f"Blocked: {len([x for x in summaries if x['status'] == 'blocked'])}")
    print(f"Artifacts: {run_dir}")
    return 0


def _pr_fix(args: argparse.Namespace) -> int:
    # Backward-compatible thin wrapper: process a single PR through queue-drain flow.
    ns = argparse.Namespace(
        execute=args.execute,
        max_prs=1,
        strategy=args.strategy,
        strict_conflicts=args.strict_conflicts,
        out_dir=args.out_dir,
        repo=args.repo,
        limit=max(10, args.limit),
        max_passes=max(1, getattr(args, "max_passes", 4)),
        check_wait_seconds=getattr(args, "check_wait_seconds", 900),
        check_poll_seconds=getattr(args, "check_poll_seconds", 30),
    )
    return _queue_drain(ns)


def main() -> None:
    p = argparse.ArgumentParser(prog="dopemux-pr-merge")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_scan = sub.add_parser("queue-scan", help="Scan the PR queue and compute deterministic ordering.")
    s_scan.add_argument("--repo", help="Optional OWNER/REPO override.")
    s_scan.add_argument("--limit", type=int, default=50, help="Max open PRs to inspect.")
    s_scan.add_argument(
        "--strategy",
        choices=["simple", "hybrid"],
        default="hybrid",
        help="Queue ordering strategy.",
    )
    s_scan.add_argument("--out-dir", default="proof/pr_merge", help="Artifact output directory.")
    s_scan.set_defaults(func=_queue_scan)

    s_drain = sub.add_parser("queue-drain", help="Drain queue with rebase-first and thread-resolution gates.")
    s_drain.add_argument("--repo", help="Optional OWNER/REPO override.")
    s_drain.add_argument("--execute", action="store_true", help="Run mutating actions. Default is dry-run.")
    s_drain.add_argument("--max-prs", type=int, default=0, help="Max PRs to process (0 means all).")
    s_drain.add_argument("--limit", type=int, default=100, help="Max open PRs to inspect.")
    s_drain.add_argument(
        "--max-passes",
        type=int,
        default=4,
        help="Max queue refresh passes after merges, thread actions, or pending checks.",
    )
    s_drain.add_argument(
        "--check-wait-seconds",
        type=int,
        default=900,
        help="Max seconds to wait for pending required checks before blocking a PR.",
    )
    s_drain.add_argument(
        "--check-poll-seconds",
        type=int,
        default=30,
        help="Seconds between required-check polls while waiting for green.",
    )
    s_drain.add_argument(
        "--strategy",
        choices=["simple", "hybrid"],
        default="hybrid",
        help="Queue ordering strategy.",
    )
    s_drain.add_argument(
        "--strict-conflicts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Escalate unresolved semantic conflicts instead of taking easy defaults.",
    )
    s_drain.add_argument("--out-dir", default="proof/pr_merge", help="Artifact output directory.")
    s_drain.set_defaults(func=_queue_drain)

    s_fix = sub.add_parser("pr-fix", help="Backward-compatible single-PR fix loop wrapper.")
    s_fix.add_argument("--id", required=False, help="Reserved for compatibility; currently ignored.")
    s_fix.add_argument("--repo", help="Optional OWNER/REPO override.")
    s_fix.add_argument("--execute", action="store_true", help="Run mutating actions. Default is dry-run.")
    s_fix.add_argument("--limit", type=int, default=50, help="Max open PRs to inspect.")
    s_fix.add_argument(
        "--max-passes",
        type=int,
        default=4,
        help="Max queue refresh passes after merges, thread actions, or pending checks.",
    )
    s_fix.add_argument(
        "--check-wait-seconds",
        type=int,
        default=900,
        help="Max seconds to wait for pending required checks before blocking a PR.",
    )
    s_fix.add_argument(
        "--check-poll-seconds",
        type=int,
        default=30,
        help="Seconds between required-check polls while waiting for green.",
    )
    s_fix.add_argument(
        "--strategy",
        choices=["simple", "hybrid"],
        default="hybrid",
        help="Queue ordering strategy.",
    )
    s_fix.add_argument(
        "--strict-conflicts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Escalate unresolved semantic conflicts instead of taking easy defaults.",
    )
    s_fix.add_argument("--out-dir", default="proof/pr_merge", help="Artifact output directory.")
    s_fix.set_defaults(func=_pr_fix)

    args = p.parse_args()
    try:
        rc = args.func(args)
        raise SystemExit(rc)
    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
