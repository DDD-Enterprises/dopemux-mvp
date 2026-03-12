from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
from collections import defaultdict, deque
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .github_api import (
    BOT_AUTHORS,
    GitHubClient,
    ci_status,
    summarize_checks,
    thread_counters,
)
from .policy import PolicyError, load_effective_policy, policy_artifact_payload, policy_fingerprint
from .runtime import (
    CommandResult,
    append_command_log,
    execute_or_dry_run,
    fingerprint_payload,
    pid_is_running,
    run_command,
    run_id,
    shell_join,
    snapshot_environment,
    utc_now,
    write_json,
    write_text,
)
from .schema import (
    ARTIFACT_VERSION,
    ArtifactMeta,
    BlockerType,
    FallbackReason,
    Finding,
    FindingSeverity,
    Fingerprint,
    MergeDecision,
    MergeActionType,
    OverrideRecord,
    PhaseRecord,
    PRResult,
    PRState,
    PRStateData,
    POLICY_SCHEMA_VERSION,
    PreflightCheck,
    PreflightResult,
    PullRequestState,
    QueueOrderingLayer,
    ReviewThread,
    RunManifest,
    ThreadComment,
    ThreadDisposition,
    ThreadDispositionType,
    TruthSource,
    ValidationReport,
    ValidationStatus,
    TOOL_VERSION,
)
from .validation import run_validation, validation_report_md

CLASS_PRIORITY: Dict[str, int] = {
    "READY": 1,
    "CI_ONLY": 2,
    "COMMENTS_ONLY": 3,
    "CONFLICTS_ONLY": 4,
    "MIXED": 5,
    "BLOCKED": 6,
}
TRUTH_PRECEDENCE = [
    "effective_policy",
    "github_protection_review",
    "local_validation",
    "local_rebase_simulation",
    "heuristics",
]
VALID_TRANSITIONS: Dict[PRState, set[PRState]] = {
    PRState.DISCOVERED: {PRState.SCANNED, PRState.ABORTED},
    PRState.SCANNED: {PRState.PLANNED, PRState.ABORTED},
    PRState.PLANNED: {PRState.APPLY_BLOCKED, PRState.APPLY_READY, PRState.ABORTED},
    PRState.APPLY_BLOCKED: {PRState.PLANNED, PRState.ABORTED, PRState.ESCALATED},
    PRState.APPLY_READY: {PRState.APPLIED, PRState.ABORTED},
    PRState.APPLIED: {PRState.MERGE_BLOCKED, PRState.MERGE_READY, PRState.ABORTED},
    PRState.MERGE_BLOCKED: {PRState.PLANNED, PRState.APPLIED, PRState.ABORTED, PRState.ESCALATED},
    PRState.MERGE_READY: {PRState.MERGED, PRState.ABORTED},
    PRState.MERGED: set(),
    PRState.ESCALATED: {PRState.PLANNED, PRState.ABORTED},
    PRState.ABORTED: set(),
}
QUEUE_LOCK_PATH = Path("tmp") / "pr_merge_specialist_queue.lock"


def _status_value(status: Any) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _severity_value(kind: Any) -> str:
    return kind.value if hasattr(kind, "value") else str(kind)


def _state_value(state: Any) -> str:
    return state.value if hasattr(state, "value") else str(state)


def decision_basis_payload(*, winning_reason: str, winning_sources: Sequence[str], suppressed_sources: Optional[Sequence[Dict[str, str]]] = None) -> Dict[str, Any]:
    return {
        "truth_precedence": ["policy", "github_protection", "local_validation", "local_apply_state", "heuristics"],
        "winning_sources": list(winning_sources),
        "winning_reason": winning_reason,
        "suppressed_sources": list(suppressed_sources or [{"source": "heuristics", "reason": "lower_precedence"}]),
    }


def ensure_transition(current: PRState, target: PRState) -> None:
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise RuntimeError(f"Invalid lifecycle transition: {current} -> {target}")


def parse_pr_id_args(values: Sequence[str]) -> List[int]:
    parsed: List[int] = []
    for raw in values:
        for part in raw.split(","):
            token = part.strip()
            if token:
                parsed.append(int(token))
    ordered: List[int] = []
    seen = set()
    for pr_id in parsed:
        if pr_id in seen:
            continue
        seen.add(pr_id)
        ordered.append(pr_id)
    return ordered


def require_clean_worktree(repo_root: Path) -> Tuple[bool, str]:
    result = run_command(["git", "status", "--porcelain"], cwd=repo_root)
    if result.returncode != 0:
        return False, result.stderr.strip() or "Unable to evaluate git status"
    if result.stdout.strip():
        return False, result.stdout.strip()
    return True, ""


def acquire_queue_lock(repo_root: Path, active_run_id: str) -> Tuple[bool, Path, str]:
    lock_path = repo_root / QUEUE_LOCK_PATH
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"pid": os.getpid(), "run_id": active_run_id, "started_at": utc_now()}
    if lock_path.exists():
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
        existing_pid = int(existing.get("pid", 0) or 0)
        if existing_pid and pid_is_running(existing_pid):
            return (
                False,
                lock_path,
                f"queue-drain lock is already held by pid {existing_pid} (run {existing.get('run_id', 'unknown')})",
            )
        lock_path.unlink()
    fd = os.open(str(lock_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return True, lock_path, ""


def release_queue_lock(lock_path: Optional[Path]) -> None:
    if lock_path and lock_path.exists():
        lock_path.unlink()


def build_run_paths(out_dir: str, active_run_id: str) -> Tuple[Path, Path, Path]:
    run_dir = Path(out_dir) / f"run_{active_run_id}"
    queue_dir = run_dir / "queue"
    pr_root = run_dir / "pr"
    queue_dir.mkdir(parents=True, exist_ok=True)
    pr_root.mkdir(parents=True, exist_ok=True)
    return run_dir, queue_dir, pr_root


def pr_dir_for(pr_root: Path, pr_id: int) -> Path:
    path = pr_root / str(pr_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_meta(
    *,
    repo_root: Path,
    repo_slug: str,
    run_identifier: str,
    pr_head_sha: str = "",
    base_sha: str = "",
    applied_tree_sha: str = "",
) -> ArtifactMeta:
    remote = run_command(["git", "remote", "get-url", "origin"], cwd=repo_root, timeout_seconds=30)
    current_branch = run_command(["git", "branch", "--show-current"], cwd=repo_root, timeout_seconds=30)
    default_branch = run_command(["git", "remote", "show", "origin"], cwd=repo_root, timeout_seconds=30)
    default_branch_name = ""
    if default_branch.returncode == 0:
        for line in default_branch.stdout.splitlines():
            if "HEAD branch:" in line:
                default_branch_name = line.split("HEAD branch:", 1)[1].strip()
                break
    return ArtifactMeta(
        generated_at=utc_now(),
        run_id=run_identifier,
        repo_root=str(repo_root),
        git_remote_origin_url=remote.stdout.strip() if remote.returncode == 0 else "",
        git_repo_name=repo_slug,
        current_branch=current_branch.stdout.strip() if current_branch.returncode == 0 else "",
        default_branch=default_branch_name,
        pr_head_sha=pr_head_sha,
        base_sha=base_sha,
        applied_tree_sha=applied_tree_sha,
    )


def lifecycle_for_findings(findings: Sequence[Finding], *, validation_status: ValidationStatus) -> PRState:
    blockers = [item for item in findings if _severity_value(item.kind) == FindingSeverity.BLOCKER.value]
    if blockers:
        return PRState.APPLY_BLOCKED
    if _status_value(validation_status) == ValidationStatus.PASSED.value:
        return PRState.MERGE_READY
    if _status_value(validation_status) == ValidationStatus.NOT_EXECUTED.value:
        return PRState.APPLY_READY
    return PRState.MERGE_BLOCKED


def has_conflicts(mergeable: str, merge_state_status: str) -> bool:
    mergeable_u = str(mergeable or "").upper()
    state_u = str(merge_state_status or "").upper()
    return mergeable_u == "CONFLICTING" or state_u in {"DIRTY", "HAS_HOOKS"}


def classify_pr(*, ci_state: str, conflicts: bool, active_unresolved_threads: int, is_draft: bool) -> str:
    if is_draft:
        return "BLOCKED"
    ci_fail = ci_state == "FAILURE"
    has_comments = active_unresolved_threads > 0
    blockers = int(ci_fail) + int(conflicts) + int(has_comments)
    if blockers == 0:
        return "READY"
    if blockers > 1:
        return "MIXED"
    if ci_fail:
        return "CI_ONLY"
    if conflicts:
        return "CONFLICTS_ONLY"
    if has_comments:
        return "COMMENTS_ONLY"
    return "BLOCKED"


def risk_score(
    *,
    pr_class: str,
    additions: int,
    deletions: int,
    changed_files: int,
    active_threads: int,
    outdated_threads: int,
    ci_state: str,
    merge_state_status: str,
) -> float:
    diff_size = additions + deletions
    score = float(diff_size) + (changed_files * 10.0)
    score += active_threads * 80.0
    score += outdated_threads * 20.0
    if ci_state == "FAILURE":
        score += 250.0
    elif ci_state == "PENDING":
        score += 90.0
    if merge_state_status.upper() == "BEHIND":
        score += 20.0
    if pr_class == "CONFLICTS_ONLY":
        score += 300.0
    if pr_class == "MIXED":
        score += 200.0
    if pr_class == "BLOCKED":
        score += 500.0
    return score


def build_pr_state(raw: Dict[str, Any], unresolved_total: int, active_unresolved: int, outdated_unresolved: int) -> PullRequestState:
    checks = raw.get("statusCheckRollup", []) or []
    ci_state = ci_status(checks)
    merge_state_status = raw.get("mergeStateStatus") or ""
    conflicts = has_conflicts(raw.get("mergeable") or "", merge_state_status)
    pr_class = classify_pr(
        ci_state=ci_state,
        conflicts=conflicts,
        active_unresolved_threads=active_unresolved,
        is_draft=bool(raw.get("isDraft", False)),
    )
    return PullRequestState(
        pr_id=int(raw["number"]),
        title=raw.get("title", ""),
        author=(raw.get("author") or {}).get("login", "unknown"),
        state=raw.get("state", "OPEN"),
        base_ref=raw.get("baseRefName", ""),
        head_ref=raw.get("headRefName", ""),
        ci_status=ci_state,  # type: ignore[arg-type]
        mergeable=raw.get("mergeable", "UNKNOWN"),
        merge_state_status=merge_state_status,
        review_decision=raw.get("reviewDecision") or "",
        labels=[item.get("name", "") for item in raw.get("labels", []) if isinstance(item, dict)],
        updated_at=raw.get("updatedAt", ""),
        is_draft=bool(raw.get("isDraft", False)),
        additions=int(raw.get("additions", 0) or 0),
        deletions=int(raw.get("deletions", 0) or 0),
        changed_files=int(raw.get("changedFiles", 0) or 0),
        unresolved_threads=unresolved_total,
        active_unresolved_threads=active_unresolved,
        outdated_unresolved_threads=outdated_unresolved,
        pr_class=pr_class,  # type: ignore[arg-type]
        risk_score=risk_score(
            pr_class=pr_class,
            additions=int(raw.get("additions", 0) or 0),
            deletions=int(raw.get("deletions", 0) or 0),
            changed_files=int(raw.get("changedFiles", 0) or 0),
            active_threads=active_unresolved,
            outdated_threads=outdated_unresolved,
            ci_state=ci_state,
            merge_state_status=merge_state_status,
        ),
        check_summary=summarize_checks(checks),
        lifecycle_state=PRState.DISCOVERED,
        head_sha=str(raw.get("headRefOid") or ""),
        base_sha=str(raw.get("baseRefOid") or ""),
    )


def priority_key(pr: PullRequestState) -> Tuple[int, float, int, str, int]:
    return (
        CLASS_PRIORITY.get(pr.pr_class, 99),
        pr.risk_score,
        pr.diff_size,
        pr.updated_at,
        pr.pr_id,
    )


def build_dependency_edges(states: List[PullRequestState]) -> Dict[int, List[int]]:
    edges: Dict[int, List[int]] = defaultdict(list)
    by_head = {pr.head_ref: pr.pr_id for pr in states if pr.head_ref}
    for pr in states:
        depends_on = by_head.get(pr.base_ref)
        if depends_on and depends_on != pr.pr_id:
            edges[depends_on].append(pr.pr_id)
    return {key: sorted(set(value)) for key, value in edges.items()}


def sort_states(states: List[PullRequestState], strategy: str) -> Tuple[List[PullRequestState], List[QueueOrderingLayer], Dict[int, List[int]], bool]:
    if len(states) <= 3 or strategy == "simple":
        ordered = sorted(states, key=priority_key)
        return ordered, [QueueOrderingLayer(layer=0, pr_ids=[item.pr_id for item in ordered])], {}, False
    edges = build_dependency_edges(states)
    if not edges:
        ordered = sorted(states, key=priority_key)
        return ordered, [QueueOrderingLayer(layer=0, pr_ids=[item.pr_id for item in ordered])], {}, False
    by_id = {item.pr_id: item for item in states}
    indegree: Dict[int, int] = {item.pr_id: 0 for item in states}
    for targets in edges.values():
        for target in targets:
            indegree[target] = indegree.get(target, 0) + 1
    queue: deque[int] = deque(sorted([pid for pid, count in indegree.items() if count == 0], key=lambda pid: priority_key(by_id[pid])))
    ordered_ids: List[int] = []
    layers: List[QueueOrderingLayer] = []
    visited: set[int] = set()
    layer_index = 0
    while queue:
        layer_items = sorted(list(queue), key=lambda pid: priority_key(by_id[pid]))
        queue.clear()
        layers.append(QueueOrderingLayer(layer=layer_index, pr_ids=layer_items))
        layer_index += 1
        for pid in layer_items:
            if pid in visited:
                continue
            visited.add(pid)
            ordered_ids.append(pid)
            for child in edges.get(pid, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
    cycle = len(visited) != len(states)
    if cycle:
        remaining = sorted([item.pr_id for item in states if item.pr_id not in visited], key=lambda pid: priority_key(by_id[pid]))
        layers.append(QueueOrderingLayer(layer=layer_index, pr_ids=remaining))
        ordered_ids.extend(remaining)
    return [by_id[pid] for pid in ordered_ids], layers, edges, cycle


def apply_priority_preferences(states: List[PullRequestState], *, only_ids: Sequence[int], prioritize_ids: Sequence[int]) -> List[PullRequestState]:
    filtered = states
    if only_ids:
        allowed = set(only_ids)
        filtered = [pr for pr in filtered if pr.pr_id in allowed]
    if not prioritize_ids:
        return filtered
    priority_rank = {pr_id: index for index, pr_id in enumerate(prioritize_ids)}
    prioritized = [pr for pr in filtered if pr.pr_id in priority_rank]
    remainder = [pr for pr in filtered if pr.pr_id not in priority_rank]
    prioritized.sort(key=lambda pr: priority_rank[pr.pr_id])
    return prioritized + remainder


def latest_comment(thread: ReviewThread) -> Optional[ThreadComment]:
    if not thread.comments:
        return None
    return sorted(thread.comments, key=lambda comment: comment.created_at or "")[-1]


def contains_marker(text: str, markers: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def has_newer_objection(thread: ReviewThread, policy: Dict[str, Any]) -> bool:
    ordered = sorted(thread.comments, key=lambda comment: comment.created_at or "")
    markers = policy.get("thread_rules", {}).get("objection_markers", [])
    for comment in reversed(ordered):
        if comment.author in BOT_AUTHORS:
            continue
        return contains_marker(comment.body, markers)
    return False


def has_resolution_signal(thread: ReviewThread, policy: Dict[str, Any]) -> bool:
    markers = policy.get("thread_rules", {}).get("resolution_markers", [])
    for comment in sorted(thread.comments, key=lambda comment: comment.created_at or ""):
        if contains_marker(comment.body, markers):
            return True
    return False


def comment_prefers_conflict_side(body: str) -> Optional[str]:
    lowered = html.unescape(body).lower()
    if "<<<<<<< head" not in lowered and "conflict marker" not in lowered:
        return None
    head_markers = [
        "keep the head side",
        "from the <code>head</code> side",
        "keep the current main version",
        "keep the current version",
        "keep the wrapper implementation already in head",
        "between <code><<<<<<< head</code> and <code>=======</code>",
        "under <code><<<<<<< head</code>",
    ]
    if any(marker in lowered for marker in head_markers):
        return "head"
    if "after <code>=======</code>" in lowered or "keep the other side" in lowered:
        return "theirs"
    return None


def is_implementable_comment(comment: Optional[ThreadComment], policy: Dict[str, Any]) -> bool:
    if comment is None:
        return False
    body = comment.body
    if comment_prefers_conflict_side(body) is not None:
        return True
    patterns = [str(item).lower() for item in policy.get("thread_rules", {}).get("implementable_patterns", [])]
    lowered = body.lower()
    if any(pattern in lowered for pattern in patterns):
        return True
    if re.search(r"change\s+<code>.*?</code>\s+to\s+<code>.*?</code>", body, re.IGNORECASE | re.DOTALL):
        return True
    if re.search(r"(?:delete|remove)\s+(?:the\s+)?(?:line\s+)?<code>.*?</code>", body, re.IGNORECASE | re.DOTALL):
        return True
    return False


def decide_thread_disposition(thread: ReviewThread, *, validation_green: bool, policy: Dict[str, Any]) -> ThreadDisposition:
    comment = latest_comment(thread)
    path = comment.path if comment and comment.path else thread.path
    thread_rules = policy.get("thread_rules", {})
    if (
        validation_green
        and thread_rules.get("auto_resolve_outdated", True)
        and not has_newer_objection(thread, policy)
        and (thread.is_outdated or (thread_rules.get("auto_resolve_resolution_signals", True) and has_resolution_signal(thread, policy)))
    ):
        return ThreadDisposition(
            thread_id=thread.id,
            disposition="auto_resolve_outdated",
            reason="Thread is safe to resolve after green verification and no newer objection.",
            path=path,
        )
    if is_implementable_comment(comment, policy):
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


def extract_suggestion_block(body: str) -> Optional[str]:
    match = re.search(r"```suggestion\s*(.*?)```", body, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip("\n")


def graphql_escape(value: str) -> str:
    return json.dumps(value)[1:-1]


def read_file_at_ref(worktree_path: Path, ref: str, rel_path: str) -> Optional[str]:
    result = run_command(["git", "show", f"{ref}:{rel_path}"], cwd=worktree_path)
    if result.returncode != 0:
        return None
    return result.stdout


def maybe_sync_canonical_file(
    *,
    worktree_path: Path,
    base_ref: str,
    rel_path: str,
    original: str,
    resolved: str,
    prefer: str,
    comment_body: str,
    policy: Dict[str, Any],
) -> Tuple[str, str]:
    if prefer != "head":
        return resolved, ""
    canonical_markers = policy.get("conflict_rules", {}).get("canonical_head_markers", [])
    if not contains_marker(comment_body, canonical_markers):
        return resolved, ""
    canonical = read_file_at_ref(worktree_path, f"origin/{base_ref}", rel_path)
    if canonical is None:
        return resolved, ""
    if any(marker in canonical for marker in ("<<<<<<<", "=======", ">>>>>>>")):
        return resolved, ""
    if canonical.rstrip("\n") == resolved.rstrip("\n") or canonical.rstrip("\n") in original.rstrip("\n"):
        return canonical, " using canonical base file content"
    return resolved, ""


def resolve_conflict_markers(text: str, *, prefer: str) -> Tuple[bool, str]:
    if "<<<<<<<" not in text:
        return False, "File does not contain Git conflict markers."
    lines = text.splitlines()
    output: List[str] = []
    index = 0
    changed = False
    while index < len(lines):
        line = lines[index]
        if not line.startswith("<<<<<<<"):
            output.append(line)
            index += 1
            continue
        changed = True
        index += 1
        head_lines: List[str] = []
        while index < len(lines) and not lines[index].startswith("======="):
            head_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            return False, "Malformed conflict block: missing ======= marker."
        index += 1
        other_lines: List[str] = []
        while index < len(lines) and not lines[index].startswith(">>>>>>>"):
            other_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            return False, "Malformed conflict block: missing >>>>>>> marker."
        output.extend(head_lines if prefer == "head" else other_lines)
        index += 1
    resolved = "\n".join(output)
    if text.endswith("\n"):
        resolved += "\n"
    return changed, resolved


def apply_suggestion_to_file(*, worktree_path: Path, thread: ReviewThread, comment: ThreadComment, base_ref: str, policy: Dict[str, Any]) -> Tuple[bool, str]:
    target = comment.path or thread.path
    if not target:
        return False, "No path on thread/comment."
    file_path = worktree_path / target
    if not file_path.exists() or not file_path.is_file():
        return False, f"Target file missing: {target}"
    original = file_path.read_text(encoding="utf-8")
    text = original
    preferred_conflict_side = comment_prefers_conflict_side(comment.body)
    if preferred_conflict_side is not None:
        changed, resolved = resolve_conflict_markers(text, prefer=preferred_conflict_side)
        if not changed:
            return False, resolved
        resolved, canonical_note = maybe_sync_canonical_file(
            worktree_path=worktree_path,
            base_ref=base_ref,
            rel_path=target,
            original=original,
            resolved=resolved,
            prefer=preferred_conflict_side,
            comment_body=comment.body,
            policy=policy,
        )
        if resolved == original:
            return False, "Conflict-marker resolution produced no file changes."
        file_path.write_text(resolved, encoding="utf-8")
        return True, f"Resolved conflict markers in {target} using {preferred_conflict_side} side{canonical_note}."
    suggestion = extract_suggestion_block(comment.body)
    if suggestion is not None:
        start = thread.original_start_line or thread.original_line or thread.line
        end = thread.original_line or thread.line or start
        if start is None or end is None:
            return False, "Suggestion block missing line anchors."
        lines = text.splitlines()
        start_idx = max(start - 1, 0)
        end_idx = max(end, start_idx + 1)
        replacement = suggestion.splitlines()
        text = "\n".join(lines[:start_idx] + replacement + lines[end_idx:]) + ("\n" if original.endswith("\n") else "")
    else:
        replace_match = re.search(r"change\s+<code>(.*?)</code>\s+to\s+<code>(.*?)</code>", comment.body, re.IGNORECASE | re.DOTALL)
        if replace_match:
            old = html.unescape(replace_match.group(1)).strip()
            new = html.unescape(replace_match.group(2)).strip()
            if old not in text:
                return False, "Could not locate replacement source fragment in file."
            text = text.replace(old, new, 1)
        else:
            delete_match = re.search(r"(?:delete|remove)\s+(?:the\s+)?(?:line\s+)?<code>(.*?)</code>", comment.body, re.IGNORECASE | re.DOTALL)
            if not delete_match:
                return False, "No known machine-applicable suggestion pattern."
            snippet = html.unescape(delete_match.group(1)).strip()
            removed = False
            new_lines: List[str] = []
            for line in text.splitlines():
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


def graph_reply_to_thread(thread_id: str, body: str, *, repo_root: Path, timeout_seconds: int) -> CommandResult:
    query = (
        "mutation { addPullRequestReviewThreadReply(input: "
        f'{{pullRequestReviewThreadId: "{graphql_escape(thread_id)}", body: "{graphql_escape(body)}"}}) '
        "{ comment { id } } }"
    )
    return run_command(["gh", "api", "graphql", "-f", f"query={query}"], cwd=repo_root, timeout_seconds=timeout_seconds)


def graph_resolve_thread(thread_id: str, *, repo_root: Path, timeout_seconds: int) -> CommandResult:
    query = (
        "mutation { resolveReviewThread(input: "
        f'{{threadId: "{graphql_escape(thread_id)}"}}) {{ thread {{ id isResolved }} }} }}'
    )
    return run_command(["gh", "api", "graphql", "-f", f"query={query}"], cwd=repo_root, timeout_seconds=timeout_seconds)


def prepare_worktree(repo_root: Path, pr_id: int, active_run_id: str, commands_log: Path, policy: Dict[str, Any]) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
    branch = f"prmerge/{active_run_id}-{pr_id}"
    path = Path("/tmp") / f"dopemux-pr-merge-{pr_id}-{active_run_id}"
    fetch = run_command(["git", "fetch", "origin", f"pull/{pr_id}/head:{branch}"], cwd=repo_root, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return None, None, fetch.stderr.strip() or "git fetch failed"
    add = run_command(["git", "worktree", "add", str(path), branch], cwd=repo_root, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    append_command_log(commands_log, add)
    if add.returncode != 0:
        return None, None, add.stderr.strip() or "git worktree add failed"
    return path, branch, None


def cleanup_worktree(repo_root: Path, worktree_path: Path, branch: str, commands_log: Path, policy: Dict[str, Any]) -> None:
    remove = run_command(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=repo_root, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    append_command_log(commands_log, remove)
    run_command(["git", "branch", "-D", branch], cwd=repo_root, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))


def ensure_worktree_matches_pr_head(*, worktree_path: Path, pr_id: int, head_ref: str, client: GitHubClient, commands_log: Path, policy: Dict[str, Any]) -> Tuple[bool, str]:
    expected_oid, err = client.fetch_pr_head_oid(pr_id)
    if err:
        return False, err
    local_head = run_command(["git", "rev-parse", "HEAD"], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    append_command_log(commands_log, local_head)
    if local_head.returncode != 0:
        return False, local_head.stderr.strip() or "Unable to read local worktree HEAD"
    if local_head.stdout.strip() == expected_oid:
        return True, "worktree already matched live PR head"
    fetch = run_command(["git", "fetch", "origin", head_ref], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return False, fetch.stderr.strip() or "Unable to fetch live PR head"
    reset = run_command(["git", "reset", "--hard", expected_oid], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    append_command_log(commands_log, reset)
    if reset.returncode != 0:
        return False, reset.stderr.strip() or "Unable to refresh worktree to live PR head"
    return True, f"refreshed stale worktree to live PR head {expected_oid}"


def attempt_rebase(*, pr_id: int, worktree_path: Path, base_ref: str, head_ref: str, commands_log: Path, execute: bool, repo: Optional[str], policy: Dict[str, Any]) -> Tuple[bool, bool, str]:
    command = ["gh", "pr", "update-branch", str(pr_id), "--rebase"]
    if repo:
        command.extend(["--repo", repo])
    update = execute_or_dry_run(command, execute=execute, cwd=worktree_path, commands_log=commands_log, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    if execute and update.returncode != 0:
        if "conflict" in update.stderr.lower():
            fetch_base = run_command(["git", "fetch", "origin", base_ref], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
            append_command_log(commands_log, fetch_base)
            local_rebase = run_command(["git", "rebase", f"origin/{base_ref}"], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
            append_command_log(commands_log, local_rebase)
            detail = local_rebase.stderr.strip() or local_rebase.stdout.strip()
            return False, True, update.stderr.strip() + (f"\n\nLocal conflict reproduction:\n{detail}" if detail else "")
        return False, False, update.stderr.strip() or "gh pr update-branch failed"
    if not execute:
        return True, False, "dry-run"
    fetch = run_command(["git", "fetch", "origin", head_ref], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return False, False, fetch.stderr.strip() or "git fetch for head failed"
    reset = run_command(["git", "reset", "--hard", f"origin/{head_ref}"], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    append_command_log(commands_log, reset)
    if reset.returncode != 0:
        return False, False, reset.stderr.strip() or "git reset to rebased head failed"
    return True, False, "rebase updated and worktree refreshed"


def conflict_files(worktree_path: Path, policy: Dict[str, Any]) -> List[str]:
    status = run_command(["git", "status", "--porcelain"], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    if status.returncode != 0:
        return []
    return [line[3:].strip() for line in status.stdout.splitlines() if line.startswith(("UU ", "AA ", "DD "))]


def pr_changed_files(worktree_path: Path, base_ref: str, commands_log: Optional[Path], policy: Dict[str, Any]) -> List[str]:
    fetch = run_command(["git", "fetch", "origin", base_ref], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    if commands_log:
        append_command_log(commands_log, fetch)
    if fetch.returncode != 0:
        return []
    diff = run_command(["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    if commands_log:
        append_command_log(commands_log, diff)
    if diff.returncode != 0:
        return []
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]


def scan_files_for_conflict_markers(worktree_path: Path, rel_paths: Sequence[str]) -> List[str]:
    hits: List[str] = []
    conflict_pattern = re.compile(r"^<<<<<<< .*\n(?:.*\n)*?^=======\n(?:.*\n)*?^>>>>>>> .*$", re.MULTILINE)
    for rel_path in rel_paths:
        file_path = worktree_path / rel_path
        if not file_path.exists() or not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if conflict_pattern.search(text):
            hits.append(rel_path)
    return sorted(set(hits))


def conflict_excerpt(worktree_path: Path, rel_path: str, *, context_lines: int = 3) -> str:
    file_path = worktree_path / rel_path
    if not file_path.exists() or not file_path.is_file():
        return "File unavailable for conflict excerpt."
    lines = file_path.read_text(encoding="utf-8").splitlines()
    excerpts: List[str] = []
    index = 0
    while index < len(lines):
        if not lines[index].startswith("<<<<<<<"):
            index += 1
            continue
        start = max(index - context_lines, 0)
        end = min(index + 1, len(lines))
        while end < len(lines) and not lines[end].startswith(">>>>>>>"):
            end += 1
        if end < len(lines):
            end += 1
        end = min(end + context_lines, len(lines))
        excerpts.append("\n".join(f"{line_no + 1:>4}: {content}" for line_no, content in enumerate(lines[start:end], start=start)))
        index = end
        if len(excerpts) >= 2:
            break
    return "\n\n".join(excerpts) if excerpts else "No conflict markers found in working tree file."


def recent_file_history(worktree_path: Path, rel_path: str, *, limit: int, policy: Dict[str, Any]) -> List[str]:
    result = run_command(["git", "log", "--oneline", f"-n{limit}", "--", rel_path], cwd=worktree_path, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    if result.returncode != 0 or not result.stdout.strip():
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def build_conflict_analysis(*, pr: PullRequestState, worktree_path: Optional[Path], rebase_error: str, policy: Dict[str, Any]) -> str:
    strict = bool(policy.get("conflict_rules", {}).get("strict", True))
    lines = [
        f"# Conflict Analysis for PR #{pr.pr_id}",
        "",
        "## Classification",
        "- conflict_type: semantic_or_unknown",
        f"- strict_conflicts: {strict}",
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
        files = conflict_files(worktree_path, policy)
        lines.extend(["## Conflicting Files", *([f"- {item}" for item in files] if files else ["- none detected"]), ""])
        if files:
            lines.append("## Conflict Hunks")
            for rel_path in files:
                lines.extend([f"### {rel_path}", "```text", conflict_excerpt(worktree_path, rel_path), "```", ""])
            lines.append("## Recent File History")
            for rel_path in files:
                history = recent_file_history(worktree_path, rel_path, limit=5, policy=policy)
                lines.append(f"### {rel_path}")
                lines.extend([f"- {entry}" for entry in history] if history else ["- no recent history available"])
                lines.append("")
    lines.extend(["## Resolution Decision", "- status: escalated", "- reason: strict conflict mode requires explicit semantic resolution evidence."])
    return "\n".join(lines) + "\n"


def checks_green(check_payload: Dict[str, Any]) -> bool:
    summary = check_payload["summary"]
    return summary.required_failure == 0 and summary.required_pending == 0


def wait_for_green_checks(*, pr_id: int, client: GitHubClient, execute: bool, policy: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    payload = client.query_checks(pr_id)
    green = checks_green(payload)
    history: List[Dict[str, Any]] = [{"attempt": 1, "green": green, **serialize_check_payload(payload)}]
    wait_seconds = int(policy.get("check_rules", {}).get("wait_seconds", 900) or 900)
    poll_seconds = int(policy.get("check_rules", {}).get("poll_seconds", 30) or 30)
    summary = payload["summary"]
    review_decision = str(payload.get("review_decision") or "")
    if review_decision and review_decision != "APPROVED":
        final_status = "approval_missing" if review_decision != "CHANGES_REQUESTED" else "changes_requested"
        return green, payload, {"wait_used": False, "wait_reason": final_status, "iterations": 1, "final_status": final_status, "timed_out": False, "history": history}
    if not execute or green or wait_seconds <= 0 or summary.required_pending == 0 or summary.required_failure > 0:
        final_status = "green" if green else "required_failed" if summary.required_failure > 0 else "required_pending" if summary.required_pending > 0 else "not_waited"
        return green, payload, {"wait_used": False, "wait_reason": "execute_disabled" if not execute else "no_wait_needed", "iterations": 1, "final_status": final_status, "timed_out": False, "history": history}
    deadline = time.time() + wait_seconds
    waited = False
    while time.time() < deadline:
        time.sleep(max(poll_seconds, 1))
        waited = True
        client.invalidate(f"pr:{pr_id}")
        payload = client.query_checks(pr_id)
        green = checks_green(payload)
        history.append({"attempt": len(history) + 1, "green": green, **serialize_check_payload(payload)})
        summary = payload["summary"]
        if green or summary.required_pending == 0 or summary.required_failure > 0:
            break
    summary = payload["summary"]
    return green, payload, {
        "wait_used": waited,
        "wait_reason": "healthy_required_pending",
        "iterations": len(history),
        "final_status": "green" if green else "required_failed" if summary.required_failure > 0 else "required_pending",
        "timed_out": waited and not green and summary.required_pending > 0,
        "history": history,
    }


def checks_blocker_reason(check_payload: Dict[str, Any], check_wait_payload: Dict[str, Any]) -> str:
    summary = check_payload["summary"]
    if summary.required_failure > 0:
        return "Required checks are failing."
    if summary.required_pending > 0:
        if check_wait_payload.get("timed_out"):
            return "Required checks are still pending after the wait window."
        return "Required checks are still pending but currently healthy."
    if check_payload.get("review_decision") == "CHANGES_REQUESTED":
        return "Changes have been requested."
    if check_payload.get("review_decision") != "APPROVED":
        return "Required approval is still missing."
    return "Required checks are not fully green."


def decide_merge_action(*, pr: PullRequestState, findings: Sequence[Finding], validation_report: ValidationReport) -> MergeDecision:
    blockers = [item for item in findings if _severity_value(item.kind) == FindingSeverity.BLOCKER.value]
    if blockers:
        return MergeDecision(
            action=MergeActionType.BLOCKED,
            command=[],
            reason="; ".join(item.message for item in blockers),
            reason_code=blockers[0].finding_type,
        )
    if _status_value(validation_report.status) != ValidationStatus.PASSED.value:
        return MergeDecision(
            action=MergeActionType.BLOCKED,
            command=[],
            reason="Local validation has not produced a passing result for this SHA.",
            reason_code="validation_missing_or_failed",
        )
    return MergeDecision(
        action=MergeActionType.REBASE_MERGE,
        command=["gh", "pr", "merge", str(pr.pr_id), "--rebase", "--delete-branch"],
        reason="All gates are green; rebase merge selected by default.",
        reason_code="rebase_merge_ready",
    )


def run_merge_with_fallback(*, decision: MergeDecision, pr_id: int, execute: bool, repo: Optional[str], commands_log: Path, repo_root: Path, policy: Dict[str, Any], client: GitHubClient) -> MergeDecision:
    if _state_value(decision.action) == MergeActionType.BLOCKED.value:
        return decision
    command = list(decision.command)
    if repo:
        command.extend(["--repo", repo])
    result = execute_or_dry_run(command, execute=execute, cwd=repo_root, commands_log=commands_log, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    if not execute:
        return decision
    if result.returncode == 0:
        client.invalidate(f"pr:{pr_id}")
        return decision
    stderr = (result.stderr or "").lower()
    if "already merged" in stderr:
        payload = client.fetch_pr(pr_id)
        if str(payload.get("state", "")).upper() == "MERGED":
            return MergeDecision(
                action=MergeActionType.REBASE_MERGE,
                command=command,
                reason="PR was already merged; local branch cleanup failure treated as non-blocking.",
                reason_code="already_merged_cleanup_failure",
            )
    if "merge queue required" in stderr or ("merge queue" in stderr and "required" in stderr):
        fallback_reason = FallbackReason.MERGE_QUEUE_REQUIRED.value
    elif "auto-merge is required" in stderr or ("auto-merge" in stderr and "required" in stderr):
        fallback_reason = FallbackReason.AUTO_MERGE_REQUIRED_BY_PROTECTION.value
    elif "rebase merge is not allowed" in stderr or "rebase commits are not allowed" in stderr:
        fallback_reason = FallbackReason.DIRECT_MERGE_DISALLOWED_BY_POLICY.value
    else:
        return MergeDecision(action=MergeActionType.BLOCKED, command=command, reason=f"Rebase merge failed: {result.stderr.strip()}", reason_code="rebase_merge_failed")
    allowed_reasons = {
        str(item)
        for item in policy.get("merge", {}).get(
            "allow_auto_fallback_only_for",
            [FallbackReason.MERGE_QUEUE_REQUIRED.value],
        )
    }
    if fallback_reason not in allowed_reasons:
        return MergeDecision(
            action=MergeActionType.BLOCKED,
            command=command,
            reason=f"Fallback reason {fallback_reason} is not permitted by policy.",
            reason_code="auto_fallback_not_permitted",
        )
    fallback_command = ["gh", "pr", "merge", str(pr_id), "--auto", "--delete-branch"]
    if repo:
        fallback_command.extend(["--repo", repo])
    fallback = execute_or_dry_run(fallback_command, execute=execute, cwd=repo_root, commands_log=commands_log, timeout_seconds=int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600))
    if fallback.returncode == 0:
        client.invalidate(f"pr:{pr_id}")
        return MergeDecision(action=MergeActionType.AUTO_MERGE_FALLBACK, command=fallback_command, reason="Rebase merge blocked by explicit policy; auto-merge fallback succeeded.", reason_code=fallback_reason)
    return MergeDecision(action=MergeActionType.BLOCKED, command=fallback_command, reason=f"Fallback auto-merge failed: {fallback.stderr.strip()}", reason_code="auto_merge_fallback_failed")


def apply_thread_dispositions(*, dispositions: List[ThreadDisposition], threads_by_id: Dict[str, ReviewThread], worktree_path: Path, base_ref: str, execute: bool, commands_log: Path, repo_root: Path, policy: Dict[str, Any]) -> List[ThreadDisposition]:
    applied: List[ThreadDisposition] = []
    timeout_seconds = int(policy.get("timeouts", {}).get("gh_seconds", 120) or 120)
    strict_conflicts = bool(policy.get("conflict_rules", {}).get("strict", True))
    for disposition in dispositions:
        thread = threads_by_id[disposition.thread_id]
        comment = latest_comment(thread)
        if disposition.disposition == "implement":
            if comment is None:
                applied.append(ThreadDisposition(thread_id=disposition.thread_id, disposition="escalate", reason="No comment payload found for implement disposition.", path=disposition.path, escalation_needed=True))
                continue
            ok, reason = apply_suggestion_to_file(worktree_path=worktree_path, thread=thread, comment=comment, base_ref=base_ref, policy=policy)
            if not ok:
                applied.append(ThreadDisposition(thread_id=disposition.thread_id, disposition="escalate" if strict_conflicts else "decline_with_rationale", reason=f"Auto-implement failed: {reason}", path=disposition.path, escalation_needed=strict_conflicts))
                continue
            if execute:
                append_command_log(commands_log, graph_reply_to_thread(disposition.thread_id, "Automated queue-drain applied a minimal fix and will run verification before merge.", repo_root=repo_root, timeout_seconds=timeout_seconds))
                append_command_log(commands_log, graph_resolve_thread(disposition.thread_id, repo_root=repo_root, timeout_seconds=timeout_seconds))
            applied.append(ThreadDisposition(thread_id=disposition.thread_id, disposition="implement", reason=reason, path=disposition.path, applied=True))
            continue
        if disposition.disposition == "decline_with_rationale":
            if execute:
                append_command_log(commands_log, graph_reply_to_thread(disposition.thread_id, "Automated queue-drain could not safely auto-apply this suggestion. Keeping behavior deterministic and deferring to a targeted follow-up fix.", repo_root=repo_root, timeout_seconds=timeout_seconds))
                append_command_log(commands_log, graph_resolve_thread(disposition.thread_id, repo_root=repo_root, timeout_seconds=timeout_seconds))
            applied.append(ThreadDisposition(thread_id=disposition.thread_id, disposition="decline_with_rationale", reason=disposition.reason, path=disposition.path, applied=True))
            continue
        if disposition.disposition == "auto_resolve_outdated":
            if execute:
                append_command_log(commands_log, graph_reply_to_thread(disposition.thread_id, "Outdated thread auto-resolved after re-validation with no newer objections.", repo_root=repo_root, timeout_seconds=timeout_seconds))
                append_command_log(commands_log, graph_resolve_thread(disposition.thread_id, repo_root=repo_root, timeout_seconds=timeout_seconds))
            applied.append(ThreadDisposition(thread_id=disposition.thread_id, disposition="auto_resolve_outdated", reason=disposition.reason, path=disposition.path, applied=True))
            continue
        applied.append(disposition)
    return applied


def stage_and_push_if_needed(*, worktree_path: Path, head_ref: str, active_run_id: str, pr_id: int, execute: bool, commands_log: Path, policy: Dict[str, Any]) -> bool:
    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)
    status = execute_or_dry_run(["git", "status", "--porcelain"], execute=execute, cwd=worktree_path, commands_log=commands_log, timeout_seconds=timeout_seconds)
    if not execute:
        return bool(status.stdout.strip())
    if status.returncode != 0 or not status.stdout.strip():
        return False
    add = run_command(["git", "add", "-A"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    append_command_log(commands_log, add)
    if add.returncode != 0:
        return False
    commit = run_command(["git", "commit", "-m", f"review-response: address thread suggestions (pr-merge/{active_run_id}/PR-{pr_id})"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    append_command_log(commands_log, commit)
    if commit.returncode != 0:
        return False
    push = run_command(["git", "push", "origin", f"HEAD:{head_ref}", "--force-with-lease"], cwd=worktree_path, timeout_seconds=timeout_seconds)
    append_command_log(commands_log, push)
    return push.returncode == 0


def update_remaining_pr_bases(*, remaining: Iterable[int], execute: bool, repo: Optional[str], commands_log: Path, repo_root: Path, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    updates: List[Dict[str, Any]] = []
    timeout_seconds = int(policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600)
    for pr_id in remaining:
        command = ["gh", "pr", "update-branch", str(pr_id), "--rebase"]
        if repo:
            command.extend(["--repo", repo])
        result = execute_or_dry_run(command, execute=execute, cwd=repo_root, commands_log=commands_log, timeout_seconds=timeout_seconds)
        updates.append({"pr_id": pr_id, "command": command, "returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    return updates


def snapshot_payload(states: List[PullRequestState]) -> List[Dict[str, Any]]:
    return [state.to_dict() for state in states]


def serialize_check_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    summary = payload["summary"]
    return {
        "checks_total": summary.total,
        "checks_success": summary.success,
        "checks_failure": summary.failure,
        "checks_pending": summary.pending,
        "required_checks_pending": summary.required_pending,
        "required_checks_failed": summary.required_failure,
        "optional_checks_pending": summary.optional_pending,
        "optional_checks_failed": summary.optional_failure,
        "review_decision": payload.get("review_decision", ""),
        "mergeable": payload.get("mergeable", ""),
        "merge_state_status": payload.get("merge_state_status", ""),
        "blocker_types": payload.get("blocker_types", []),
        "warning_types": payload.get("warning_types", []),
    }


def plan_fingerprint(pr: PullRequestState, *, policy_fp: str, review_state: Dict[str, Any]) -> Fingerprint:
    digest = fingerprint_payload({
        "pr_id": pr.pr_id,
        "head_sha": pr.head_sha,
        "base_sha": pr.base_sha,
        "review_state": review_state,
        "policy_fingerprint": policy_fp,
    })
    return Fingerprint(
        input_fingerprint=digest,
        valid_for_sha=pr.head_sha,
        stale_if=[
            "PR head SHA changes",
            "base SHA changes beyond allowed tolerance",
            "review state changes",
            "active thread set changes",
            "required check set changes",
            "effective policy fingerprint changes",
        ],
        created_from_state=pr.lifecycle_state,
    )


def findings_from_pr_state(pr: PullRequestState, *, check_payload: Dict[str, Any], active_threads: int, validation_status: ValidationStatus, local_validation_required: bool) -> List[Finding]:
    findings: List[Finding] = []
    if pr.is_draft:
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="draft_pr", message="Draft pull requests are blocked from merge.", source="github_protection_review"))
    if active_threads > 0:
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type=BlockerType.ACTIVE_THREAD.value, message=f"{active_threads} active unresolved review threads remain.", details={"active_threads": active_threads}, source="github_protection_review"))
    summary = check_payload["summary"]
    if summary.required_failure > 0:
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type=BlockerType.REQUIRED_CHECK_FAILED.value, message="Required checks are failing.", details=serialize_check_payload(check_payload), source="github_protection_review"))
    elif summary.required_pending > 0:
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type=BlockerType.REQUIRED_CHECK_PENDING.value, message="Required checks are still pending.", details=serialize_check_payload(check_payload), source="github_protection_review"))
    if check_payload.get("review_decision") == "CHANGES_REQUESTED":
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type=BlockerType.CHANGES_REQUESTED.value, message="Review state is CHANGES_REQUESTED.", source="github_protection_review"))
    elif check_payload.get("review_decision") != "APPROVED":
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type=BlockerType.APPROVAL_MISSING.value, message="Required approval is missing.", source="github_protection_review"))
    if summary.optional_failure > 0:
        findings.append(Finding(kind=FindingSeverity.WARNING, finding_type="optional_check_failed", message="Optional checks are failing.", details=serialize_check_payload(check_payload), source="github_protection_review"))
    if summary.optional_pending > 0:
        findings.append(Finding(kind=FindingSeverity.WARNING, finding_type=BlockerType.OPTIONAL_CHECK_PENDING.value, message="Optional checks are still pending.", details=serialize_check_payload(check_payload), source="github_protection_review"))
    if pr.diff_size > 1000:
        findings.append(Finding(kind=FindingSeverity.WARNING, finding_type="large_diff", message="Large diff size may increase merge risk.", details={"diff_size": pr.diff_size}, source="heuristics"))
    if pr.risk_score > 500:
        findings.append(Finding(kind=FindingSeverity.OBSERVATION, finding_type="high_risk_score", message="PR has elevated risk score relative to queue.", details={"risk_score": pr.risk_score}, source="heuristics"))
    if local_validation_required and _status_value(validation_status) != ValidationStatus.PASSED.value:
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="validation_not_executed" if _status_value(validation_status) == ValidationStatus.NOT_EXECUTED.value else BlockerType.VALIDATION_FAILED.value, message="Local validation is required before merge readiness can be declared.", details={"validation_status": _status_value(validation_status)}, source="local_validation"))
    return findings


def truth_sources_for(check_payload: Dict[str, Any], validation_report: ValidationReport, policy: Dict[str, Any], *, rebase_status: str = "not_run") -> List[TruthSource]:
    return [
        TruthSource(name="effective_policy", status="loaded", details={"policy_fingerprint": policy_fingerprint(policy)}),
        TruthSource(name="github_protection_review", status="observed", details=serialize_check_payload(check_payload)),
        TruthSource(name="local_validation", status=_status_value(validation_report.status), details=validation_report.to_dict()),
        TruthSource(name="local_rebase_simulation", status=rebase_status, details={}),
        TruthSource(name="heuristics", status="computed", details={"precedence": TRUTH_PRECEDENCE}),
    ]


def summarize_findings(findings: Sequence[Finding]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    blockers = [finding.to_dict() for finding in findings if _severity_value(finding.kind) == FindingSeverity.BLOCKER.value]
    warnings = [finding.to_dict() for finding in findings if _severity_value(finding.kind) == FindingSeverity.WARNING.value]
    observations = [finding.to_dict() for finding in findings if _severity_value(finding.kind) == FindingSeverity.OBSERVATION.value]
    return blockers, warnings, observations


def explain_findings(findings: Sequence[Finding], *, previous: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    blockers, warnings, observations = summarize_findings(findings)
    next_action = "merge" if not blockers else "clear blockers"
    changed_since_prior: List[str] = []
    if previous:
        previous_blockers = {item.get("finding_type") or item.get("type") for item in previous.get("blockers", [])}
        current_blockers = {item.get("finding_type") or item.get("type") for item in blockers}
        previous_blockers.discard(None)
        current_blockers.discard(None)
        added = sorted(current_blockers - previous_blockers)
        removed = sorted(previous_blockers - current_blockers)
        if added:
            changed_since_prior.append("added blockers: " + ", ".join(added))
        if removed:
            changed_since_prior.append("cleared blockers: " + ", ".join(removed))
    return {
        "why_blocked": [item.get("message") or item.get("name") or "" for item in blockers],
        "evidence": blockers + warnings,
        "next_action": next_action,
        "changed_since_prior_scan": changed_since_prior,
        "warnings": warnings,
        "observations": observations,
    }


def build_plan_result(*, active_run_id: str, pr: PullRequestState, threads: List[ReviewThread], check_payload: Dict[str, Any], validation_report: ValidationReport, policy: Dict[str, Any], previous_result: Optional[Dict[str, Any]] = None) -> PRResult:
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    review_state = {
        "unresolved_total": unresolved_total,
        "active_threads": active_threads,
        "outdated_threads": outdated_threads,
        "review_decision": check_payload.get("review_decision", ""),
        "required_checks_pending": check_payload["summary"].required_pending,
        "required_checks_failed": check_payload["summary"].required_failure,
    }
    planned_threads = [
        decide_thread_disposition(
            thread,
            validation_green=_status_value(validation_report.status) == ValidationStatus.PASSED.value,
            policy=policy,
        )
        for thread in threads
        if not thread.is_resolved
    ]
    findings = findings_from_pr_state(
        pr,
        check_payload=check_payload,
        active_threads=active_threads,
        validation_status=validation_report.status,
        local_validation_required=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
    )
    fingerprint = plan_fingerprint(pr, policy_fp=policy_fingerprint(policy), review_state=review_state)
    truth = truth_sources_for(check_payload, validation_report, policy)
    decision = decide_merge_action(pr=pr, findings=findings, validation_report=validation_report)
    explain = explain_findings(findings, previous=previous_result)
    lifecycle_state = lifecycle_for_findings(findings, validation_status=validation_report.status)
    return PRResult(
        run_id=active_run_id,
        pr_state=replace(pr, lifecycle_state=lifecycle_state),
        lifecycle_state=lifecycle_state,
        apply_actions=[f"rebase {pr.head_ref} onto {pr.base_ref}", "resolve review threads", "run validation"],
        merge_decision=decision,
        findings=findings,
        truth_sources=truth,
        precedence_order=TRUTH_PRECEDENCE,
        decision_basis=decision_basis_payload(
            winning_reason="merge_readiness",
            winning_sources=["policy", "github_protection", "local_validation"],
        ),
        validation_report=validation_report,
        thread_dispositions=planned_threads,
        fingerprint=fingerprint,
        artifacts={"explain": json.dumps(explain)},
    )


def render_operator_summary(results: Sequence[PRResult]) -> str:
    lines = ["# Queue Summary", "", "| PR | State | Confidence | Blockers | Warnings | Next action |", "| --- | --- | --- | --- | --- | --- |"]
    for result in results:
        blockers, warnings, _ = summarize_findings(result.findings)
        confidence = "high" if not blockers and result.validation_report and _status_value(result.validation_report.status) == ValidationStatus.PASSED.value else "medium" if not blockers else "blocked"
        next_action = "merge" if not blockers else "clear blockers"
        lines.append(
            f"| #{result.pr_state.pr_id} | {result.lifecycle_state} | {confidence} | {len(blockers)} | {len(warnings)} | {next_action} |"
        )
    return "\n".join(lines) + "\n"


def manifest_for_run(*, active_run_id: str, mode: str, repo_root: Path, repo_slug: str, policy: Dict[str, Any]) -> RunManifest:
    return RunManifest(
        run_id=active_run_id,
        mode=mode,
        repo_root=str(repo_root),
        repo_slug=repo_slug,
        policy_fingerprint=policy_fingerprint(policy),
        artifact_schema_versions={
            "artifact_version": ARTIFACT_VERSION,
            "tool_version": TOOL_VERSION,
            "policy_schema_version": str(POLICY_SCHEMA_VERSION),
        },
        completed_phases=[],
        resumable_phases=["queue-scan", "pr-plan", "pr-apply", "pr-merge", "queue-drain"],
        invalidation_conditions=[
            "policy fingerprint changes",
            "planned PR head SHA changes",
            "planned PR base SHA changes",
            "review state changes",
        ],
        pr_states={},
        artifact_pointers={},
    )


def write_manifest(run_dir: Path, manifest: RunManifest) -> None:
    write_json(run_dir / "RUN_MANIFEST.json", manifest.to_dict())


def preflight(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, _ = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    binaries = ["git", "gh", "python", "pre-commit"]
    checks: List[PreflightCheck] = []
    overrides: List[OverrideRecord] = []
    for binary in binaries:
        result = run_command(["which", binary], cwd=repo_root, timeout_seconds=30)
        checks.append(
            PreflightCheck(
                name=f"binary:{binary}",
                status="passed" if result.returncode == 0 else "failed",
                required=True,
                details=result.stdout.strip() or result.stderr.strip(),
                remediation=f"Install `{binary}` and ensure it is on PATH.",
            )
        )
    auth = run_command(["gh", "auth", "status"], cwd=repo_root, timeout_seconds=60)
    checks.append(
        PreflightCheck(
            name="gh_auth",
            status="passed" if auth.returncode == 0 else "failed",
            required=True,
            details=auth.stdout.strip() or auth.stderr.strip(),
            remediation="Run `gh auth login` for the target repository.",
        )
    )
    remote = run_command(["git", "remote", "get-url", "origin"], cwd=repo_root, timeout_seconds=30)
    checks.append(
        PreflightCheck(
            name="git_remote",
            status="passed" if remote.returncode == 0 else "failed",
            required=True,
            details=remote.stdout.strip() or remote.stderr.strip(),
            remediation="Configure the `origin` remote.",
        )
    )
    worktree = run_command(["git", "worktree", "list"], cwd=repo_root, timeout_seconds=60)
    checks.append(
        PreflightCheck(
            name="git_worktree",
            status="passed" if worktree.returncode == 0 else "failed",
            required=True,
            details=worktree.stdout.strip() or worktree.stderr.strip(),
            remediation="Use a git version with worktree support.",
        )
    )
    clean_ok, clean_detail = require_clean_worktree(repo_root)
    if getattr(args, "allow_dirty", False):
        overrides.append(
            OverrideRecord(
                override_type="allow_dirty",
                actor="cli",
                reason="User explicitly allowed dirty worktree execution.",
                scope="preflight.clean_worktree",
                source="--allow-dirty",
            )
        )
        checks.append(
            PreflightCheck(
                name="clean_worktree",
                status="warning" if not clean_ok else "passed",
                required=True,
                details=clean_detail,
                remediation="Clean the repo root or keep using `--allow-dirty` deliberately.",
            )
        )
    else:
        checks.append(
            PreflightCheck(
                name="clean_worktree",
                status="passed" if clean_ok else "failed",
                required=True,
                details=clean_detail,
                remediation="Commit or stash tracked changes before execute-mode runs.",
            )
        )
    for step in policy.get("validation", {}).get("steps", []):
        command = step.get("command", [])
        if command and len(command) > 1 and command[1].startswith("scripts/"):
            script_path = repo_root / command[1]
            checks.append(
                PreflightCheck(
                    name=f"script:{command[1]}",
                    status="passed" if script_path.exists() else "failed",
                    required=True,
                    details=str(script_path),
                    remediation=f"Restore or update `{command[1]}` in policy.",
                )
            )
    rate_limit = client.rate_limit_snapshot()
    precheck = PreflightResult(
        ok=all(item.status in {"passed", "warning"} for item in checks),
        checks=checks,
        policy_resolution=policy_artifact_payload(policy).get("policy_resolution"),  # placeholder, replaced below
        override_records=overrides,
    )
    precheck_payload = precheck.to_dict()
    precheck_payload["meta"] = artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict()
    precheck_payload["policy_resolution"] = {
        "source": policy_artifact_payload(policy).get("policy_source", ""),
        "path": policy_artifact_payload(policy).get("policy_path", ""),
        "fingerprint": policy_artifact_payload(policy).get("policy_fingerprint", ""),
        "policy_schema_version": POLICY_SCHEMA_VERSION,
        "overrides": [item.to_dict() for item in overrides],
    }
    write_json(run_dir / "PRECHECK.json", precheck_payload)
    environment = snapshot_environment(repo_root)
    environment.update({"repo_slug": repo_slug, "rate_limit": rate_limit})
    write_json(run_dir / "ENVIRONMENT.json", environment)
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    print(f"Preflight artifacts: {run_dir}")
    return 0 if precheck.ok else 2


def queue_scan(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, queue_dir, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    manifest = manifest_for_run(active_run_id=active_run_id, mode="queue-scan", repo_root=repo_root, repo_slug=repo_slug, policy=policy)
    raws = client.fetch_open_prs(int(args.limit))
    states: List[PullRequestState] = []
    results: List[PRResult] = []
    for raw in raws:
        threads = client.fetch_review_threads(int(raw["number"]))
        unresolved_total, active_threads, outdated_threads = thread_counters(threads)
        pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
        check_payload = client.query_checks(pr.pr_id)
        validation = ValidationReport(
            status=ValidationStatus.NOT_EXECUTED,
            required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
            steps=[],
            attempts=0,
            remediation_applied=False,
        )
        results.append(build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation, policy=policy))
        states.append(pr)
    ordered, layers, edges, cycle = sort_states(apply_priority_preferences(states, only_ids=parse_pr_id_args(getattr(args, "only", []) or []), prioritize_ids=parse_pr_id_args(getattr(args, "prioritize", []) or [])), args.strategy)
    ordered_ids = [state.pr_id for state in ordered]
    write_json(queue_dir / "QUEUE_SNAPSHOT.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(), "states": snapshot_payload(states), "cache": client.cache_summary()})
    write_json(queue_dir / "ORDERING_PLAN.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(), "strategy": args.strategy, "cycle_detected": cycle, "layers": [layer.to_dict() for layer in layers], "edges": edges, "ordered_pr_ids": ordered_ids})
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    manifest.completed_phases.append("queue-scan")
    manifest.artifact_pointers.update({"queue_snapshot": str(queue_dir / "QUEUE_SNAPSHOT.json"), "ordering_plan": str(queue_dir / "ORDERING_PLAN.json")})
    write_manifest(run_dir, manifest)
    write_text(run_dir / "RUN_SUMMARY.md", render_operator_summary(results))
    print(f"Open PRs: {len(states)}")
    print(f"Artifacts: {run_dir}")
    return 0


def write_pr_state_artifact(pr_dir: Path, result: PRResult) -> None:
    write_json(pr_dir / "STATE.json", result.to_dict())


def pr_plan(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    raw = client.fetch_pr(int(args.id))
    threads = client.fetch_review_threads(int(args.id))
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    check_payload = client.query_checks(pr.pr_id)
    validation = ValidationReport(
        status=ValidationStatus.NOT_EXECUTED,
        required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
        steps=[],
        attempts=0,
        remediation_applied=False,
    )
    result = build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation, policy=policy)
    explain = json.loads(result.artifacts["explain"])
    write_json(pr_dir / "INTAKE.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id, pr_head_sha=pr.head_sha, base_sha=pr.base_sha).to_dict(), "pr": pr.to_dict()})
    write_json(pr_dir / "REVIEW_THREADS.json", {"threads": [thread.to_dict() for thread in threads]})
    write_json(pr_dir / "PLAN.json", result.to_dict())
    write_json(pr_dir / "EXPLAIN.json", explain)
    write_pr_state_artifact(pr_dir, result)
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    print(f"Plan artifacts: {pr_dir}")
    return 0


def pr_apply(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    raw = client.fetch_pr(int(args.id))
    threads = client.fetch_review_threads(int(args.id))
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    commands_log = pr_dir / "COMMANDS_RUN.txt"
    write_json(pr_dir / "INTAKE.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id, pr_head_sha=pr.head_sha, base_sha=pr.base_sha).to_dict(), "pr": pr.to_dict()})
    worktree_path: Optional[Path] = None
    branch: Optional[str] = None
    blockers: List[Finding] = []
    thread_dispositions = [decide_thread_disposition(thread, validation_green=pr.ci_status == "SUCCESS", policy=policy) for thread in threads if not thread.is_resolved]
    if args.execute:
        worktree_path, branch, err = prepare_worktree(repo_root, pr.pr_id, active_run_id, commands_log, policy)
        if err or worktree_path is None or branch is None:
            blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="worktree_setup_failed", message=f"worktree setup failed: {err}", source="local_rebase_simulation"))
        else:
            fresh, fresh_reason = ensure_worktree_matches_pr_head(worktree_path=worktree_path, pr_id=pr.pr_id, head_ref=pr.head_ref, client=client, commands_log=commands_log, policy=policy)
            if not fresh:
                blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="stale_worktree_refresh_failed", message=f"worktree freshness check failed: {fresh_reason}", source="local_rebase_simulation"))
            else:
                ok, conflict, message = attempt_rebase(pr_id=pr.pr_id, worktree_path=worktree_path, base_ref=pr.base_ref, head_ref=pr.head_ref, commands_log=commands_log, execute=True, repo=getattr(args, "repo", None), policy=policy)
                if not ok and conflict:
                    write_text(pr_dir / "CONFLICT_ANALYSIS.md", build_conflict_analysis(pr=pr, worktree_path=worktree_path, rebase_error=message, policy=policy))
                    blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type=BlockerType.CONFLICT_DETECTED.value, message="Rebase conflict encountered.", details={"detail": message}, source="local_rebase_simulation"))
                elif not ok:
                    blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="rebase_update_failed", message=f"rebase update failed: {message}", source="local_rebase_simulation"))
                else:
                    applied = apply_thread_dispositions(dispositions=thread_dispositions, threads_by_id={thread.id: thread for thread in threads}, worktree_path=worktree_path, base_ref=pr.base_ref, execute=True, commands_log=commands_log, repo_root=repo_root, policy=policy)
                    thread_dispositions = applied
                    stage_and_push_if_needed(worktree_path=worktree_path, head_ref=pr.head_ref, active_run_id=active_run_id, pr_id=pr.pr_id, execute=True, commands_log=commands_log, policy=policy)
    validation = run_validation(repo_root=repo_root, worktree_path=worktree_path, policy=policy, execute=bool(args.execute), commands_log=commands_log, pr_id=pr.pr_id, head_sha=pr.head_sha, base_sha=pr.base_sha, policy_fingerprint=policy_fingerprint(policy), lifecycle_state="applied" if args.execute else "planned")
    write_text(pr_dir / "VALIDATION.json", json.dumps(validation.to_dict(), indent=2) + "\n")
    write_text(pr_dir / "VALIDATION_REPORT.md", validation_report_md(validation))
    changed_paths: List[str] = []
    if worktree_path and policy.get("conflict_rules", {}).get("scan_changed_files_for_markers", True):
        changed_paths = pr_changed_files(worktree_path, pr.base_ref, commands_log, policy)
    conflict_markers = scan_files_for_conflict_markers(worktree_path, changed_paths) if worktree_path else []
    if conflict_markers:
        blockers.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="conflict_markers_present", message="Conflict markers remain in changed PR files.", details={"paths": conflict_markers}, source="local_rebase_simulation"))
    write_json(pr_dir / "CONFLICT_MARKER_SCAN.json", {"paths": conflict_markers})
    check_payload = client.query_checks(pr.pr_id)
    findings = blockers + findings_from_pr_state(pr, check_payload=check_payload, active_threads=thread_counters(client.fetch_review_threads(pr.pr_id))[1], validation_status=validation.status, local_validation_required=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)))
    result = PRResult(
        run_id=active_run_id,
        pr_state=replace(pr, lifecycle_state=lifecycle_for_findings(findings, validation_status=validation.status)),
        lifecycle_state=lifecycle_for_findings(findings, validation_status=validation.status),
        apply_actions=["prepare worktree", "rebase branch", "apply review thread fixes", "run validation"],
        merge_decision=decide_merge_action(pr=pr, findings=findings, validation_report=validation),
        findings=findings,
        truth_sources=truth_sources_for(check_payload, validation, policy, rebase_status="passed" if not blockers else "failed"),
        precedence_order=TRUTH_PRECEDENCE,
        decision_basis=decision_basis_payload(
            winning_reason="apply_phase_gates",
            winning_sources=["policy", "github_protection", "local_validation", "local_apply_state"],
        ),
        validation_report=validation,
        thread_dispositions=thread_dispositions,
        fingerprint=plan_fingerprint(pr, policy_fp=policy_fingerprint(policy), review_state=serialize_check_payload(check_payload)),
        artifacts={"commands": str(commands_log)},
    )
    write_json(pr_dir / "THREAD_DISPOSITIONS.json", {"applied": [item.to_dict() for item in thread_dispositions]})
    write_json(pr_dir / "APPLY.json", result.to_dict())
    write_pr_state_artifact(pr_dir, result)
    if worktree_path is not None and branch is not None:
        cleanup_worktree(repo_root, worktree_path, branch, commands_log, policy)
    print(f"Apply artifacts: {pr_dir}")
    return 0


def pr_merge(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, _, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    raw = client.fetch_pr(int(args.id))
    threads = client.fetch_review_threads(int(args.id))
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
    pr_dir = pr_dir_for(pr_root, pr.pr_id)
    commands_log = pr_dir / "COMMANDS_RUN.txt"
    apply_result_path = pr_dir / "APPLY.json"
    validation = run_validation(repo_root=repo_root, worktree_path=None, policy=policy, execute=False, commands_log=commands_log, pr_id=pr.pr_id, head_sha=pr.head_sha, base_sha=pr.base_sha, policy_fingerprint=policy_fingerprint(policy), lifecycle_state=PRState.MERGE_READY.value)
    if apply_result_path.exists():
        apply_payload = json.loads(apply_result_path.read_text(encoding="utf-8"))
        validation_payload = apply_payload.get("validation_report")
        if isinstance(validation_payload, dict):
            from .schema import Fingerprint as SchemaFingerprint, ValidationStepResult

            fingerprint_payload_data = validation_payload.get("input_fingerprint")
            validation = ValidationReport(
                status=validation_payload["status"],
                required_for_merge_ready=validation_payload.get("required_for_merge_ready", True),
                steps=[
                    ValidationStepResult(**step)
                    for step in validation_payload.get("steps", [])
                ],
                attempts=validation_payload.get("attempts", 0),
                remediation_applied=validation_payload.get("remediation_applied", False),
                fingerprint=SchemaFingerprint(**fingerprint_payload_data)
                if fingerprint_payload_data
                else None,
            )
    check_green, check_payload, wait_payload = wait_for_green_checks(pr_id=pr.pr_id, client=client, execute=bool(args.execute), policy=policy)
    findings = findings_from_pr_state(pr, check_payload=check_payload, active_threads=active_threads, validation_status=validation.status, local_validation_required=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)))
    if validation.fingerprint is not None and validation.fingerprint.valid_for_sha != pr.head_sha:
        findings.append(
            Finding(
                kind=FindingSeverity.BLOCKER,
                finding_type="stale_validation",
                message="Prior validation artifact is stale for the current PR head SHA.",
                details={
                    "validated_sha": validation.fingerprint.valid_for_sha,
                    "current_sha": pr.head_sha,
                },
                source="local_validation",
            )
        )
    if not check_green:
        findings.append(Finding(kind=FindingSeverity.BLOCKER, finding_type="merge_gate", message=checks_blocker_reason(check_payload, wait_payload), source="github_protection_review"))
    decision = decide_merge_action(pr=pr, findings=findings, validation_report=validation)
    merged = run_merge_with_fallback(decision=decision, pr_id=pr.pr_id, execute=bool(args.execute), repo=getattr(args, "repo", None), commands_log=commands_log, repo_root=repo_root, policy=policy, client=client)
    merge_succeeded = _state_value(merged.action) in {MergeActionType.REBASE_MERGE.value, MergeActionType.AUTO_MERGE_FALLBACK.value} and args.execute
    result = PRResult(
        run_id=active_run_id,
        pr_state=replace(pr, lifecycle_state=PRState.MERGED if merge_succeeded else PRState.MERGE_BLOCKED),
        lifecycle_state=PRState.MERGED.value if merge_succeeded else PRState.MERGE_BLOCKED.value,
        apply_actions=[],
        merge_decision=merged,
        findings=findings,
        truth_sources=truth_sources_for(check_payload, validation, policy),
        precedence_order=TRUTH_PRECEDENCE,
        decision_basis=decision_basis_payload(
            winning_reason="remote_merge_gate",
            winning_sources=["policy", "github_protection", "local_validation"],
        ),
        validation_report=validation,
        thread_dispositions=[],
        fingerprint=plan_fingerprint(pr, policy_fp=policy_fingerprint(policy), review_state=serialize_check_payload(check_payload)),
        artifacts={"commands": str(commands_log)},
    )
    write_json(pr_dir / "MERGE.json", {"decision": merged.to_dict(), "checks": serialize_check_payload(check_payload), "check_wait": wait_payload})
    write_json(pr_dir / "RESULT.json", result.to_dict())
    write_pr_state_artifact(pr_dir, result)
    write_json(run_dir / "CHECK_WAIT_REPORT.json", wait_payload)
    print(f"Merge artifacts: {pr_dir}")
    return 0


def queue_drain(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    active_run_id = getattr(args, "run_id", None) or run_id()
    run_dir, queue_dir, pr_root = build_run_paths(args.out_dir, active_run_id)
    policy = load_effective_policy(repo_root, explicit_path=getattr(args, "policy", None))
    client = GitHubClient(repo=getattr(args, "repo", None), repo_root=repo_root, policy=policy)
    repo_slug = client.resolve_repo_slug()
    manifest = manifest_for_run(active_run_id=active_run_id, mode="queue-drain", repo_root=repo_root, repo_slug=repo_slug, policy=policy)
    write_json(run_dir / "POLICY_EFFECTIVE.json", policy_artifact_payload(policy))
    lock_path: Optional[Path] = None
    if args.execute:
        if policy.get("gates", {}).get("require_clean_worktree", True) and not getattr(args, "allow_dirty", False):
            clean_ok, clean_detail = require_clean_worktree(repo_root)
            if not clean_ok:
                write_json(run_dir / "PRECHECK.json", {"ok": False, "reason": clean_detail})
                return 2
        acquired, lock_path, reason = acquire_queue_lock(repo_root, active_run_id)
        if not acquired:
            write_json(run_dir / "QUEUE_REPORT.json", {"run_id": active_run_id, "execute": True, "processed": 0, "merged": 0, "blocked": 0, "lock": {"acquired": False, "path": str(lock_path), "reason": reason}})
            print(f"Blocked by active queue worker: {reason}")
            return 2
    results: List[PRResult] = []
    pass_reports: List[Dict[str, Any]] = []
    base_rebase_updates: List[Dict[str, Any]] = []
    merged_ids: List[int] = []
    processed_ids: set[int] = set()
    prioritize_ids = parse_pr_id_args(getattr(args, "prioritize", []) or [])
    only_ids = parse_pr_id_args(getattr(args, "only", []) or [])
    try:
        max_passes = max(int(getattr(args, "max_passes", 1) or 1), 1)
        for pass_index in range(1, max_passes + 1):
            raws = client.fetch_open_prs(int(args.limit))
            states = []
            thread_map: Dict[int, List[ReviewThread]] = {}
            for raw in raws:
                threads = client.fetch_review_threads(int(raw["number"]))
                unresolved_total, active_threads, outdated_threads = thread_counters(threads)
                pr = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
                states.append(pr)
                thread_map[pr.pr_id] = threads
            states = apply_priority_preferences(states, only_ids=only_ids, prioritize_ids=prioritize_ids)
            ordered, layers, edges, cycle = sort_states(states, args.strategy)
            if args.max_prs and int(args.max_prs) > 0:
                ordered = ordered[: int(args.max_prs)]
            write_json(queue_dir / "QUEUE_SNAPSHOT.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(), "states": snapshot_payload(states), "cache": client.cache_summary()})
            write_json(queue_dir / "ORDERING_PLAN.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(), "strategy": args.strategy, "cycle_detected": cycle, "layers": [layer.to_dict() for layer in layers], "edges": edges, "ordered_pr_ids": [pr.pr_id for pr in ordered], "prioritize_ids": prioritize_ids, "only_ids": only_ids})
            if not ordered:
                pass_reports.append({"pass_index": pass_index, "queue_size": 0, "processed": 0, "merged": 0, "healthy_pending_pr_ids": []})
                break
            merged_this_pass = 0
            healthy_pending_ids: List[int] = []
            for index, pr in enumerate(ordered):
                processed_ids.add(pr.pr_id)
                pr_dir = pr_dir_for(pr_root, pr.pr_id)
                write_json(pr_dir / "INTAKE.json", {"meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id, pr_head_sha=pr.head_sha, base_sha=pr.base_sha).to_dict(), "pr": pr.to_dict()})
                threads = thread_map[pr.pr_id]
                write_json(pr_dir / "REVIEW_THREADS.json", {"threads": [thread.to_dict() for thread in threads]})
                check_payload = client.query_checks(pr.pr_id)
                validation_dry = ValidationReport(
                    status=ValidationStatus.NOT_EXECUTED,
                    required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
                    steps=[],
                    attempts=0,
                    remediation_applied=False,
                )
                plan_result = build_plan_result(active_run_id=active_run_id, pr=pr, threads=threads, check_payload=check_payload, validation_report=validation_dry, policy=policy, previous_result=results[-1].to_dict() if results else None)
                write_json(pr_dir / "PLAN.json", plan_result.to_dict())
                write_pr_state_artifact(pr_dir, plan_result)
                apply_ns = argparse.Namespace(**{**vars(args), "id": pr.pr_id, "run_id": active_run_id})
                pr_apply(apply_ns)
                client.invalidate(f"pr:{pr.pr_id}")
                client.invalidate(f"threads:{pr.pr_id}")
                merge_ns = argparse.Namespace(**{**vars(args), "id": pr.pr_id, "run_id": active_run_id})
                pr_merge(merge_ns)
                result_path = pr_dir / "RESULT.json"
                if result_path.exists():
                    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
                    merged = result_payload.get("lifecycle_state") == "merged"
                    if merged:
                        merged_ids.append(pr.pr_id)
                        merged_this_pass += 1
                        remaining_ids = [item.pr_id for item in ordered[index + 1 :]]
                        updates = update_remaining_pr_bases(remaining=remaining_ids, execute=bool(args.execute), repo=getattr(args, "repo", None), commands_log=run_dir / "COMMANDS_RUN.txt", repo_root=repo_root, policy=policy)
                        base_rebase_updates.extend([{"trigger_pr": pr.pr_id, "pass_index": pass_index, **item} for item in updates])
                        client.invalidate("open_prs:")
                        break
                    checks = json.loads((pr_dir / "MERGE.json").read_text(encoding="utf-8")) if (pr_dir / "MERGE.json").exists() else {}
                    if checks:
                        pending = int(checks.get("checks", {}).get("required_checks_pending", 0) or 0)
                        failures = int(checks.get("checks", {}).get("required_checks_failed", 0) or 0)
                        if pending > 0 and failures == 0:
                            healthy_pending_ids.append(pr.pr_id)
                if result_path.exists():
                    results.append(PRResult(**_inflate_pr_result(json.loads(result_path.read_text(encoding="utf-8")))))
            pass_reports.append({"pass_index": pass_index, "queue_size": len(ordered), "processed": len(ordered), "merged": merged_this_pass, "healthy_pending_pr_ids": healthy_pending_ids})
            if merged_this_pass == 0 and not healthy_pending_ids:
                break
            client.invalidate("open_prs:")
        manifest.completed_phases.extend(["queue-scan", "pr-plan", "pr-apply", "pr-merge", "queue-drain"])
        manifest.pr_states.update({str(result.pr_state.pr_id): result.lifecycle_state for result in results})
        manifest.artifact_pointers.update({"queue_snapshot": str(queue_dir / "QUEUE_SNAPSHOT.json"), "ordering_plan": str(queue_dir / "ORDERING_PLAN.json"), "base_rebase_updates": str(run_dir / "BASE_REBASE_UPDATES.json")})
        write_manifest(run_dir, manifest)
        write_json(run_dir / "BASE_REBASE_UPDATES.json", base_rebase_updates)
        write_json(
            run_dir / "CHECK_WAIT_REPORT.json",
            {
                "wait_used": any(item.get("healthy_pending_pr_ids") for item in pass_reports),
                "wait_reason": "healthy_required_pending" if any(item.get("healthy_pending_pr_ids") for item in pass_reports) else "no_wait_needed",
                "iterations": len(pass_reports),
                "final_status": "healthy_pending" if any(item.get("healthy_pending_pr_ids") for item in pass_reports) else "stable",
                "passes": pass_reports,
            },
        )
        write_text(run_dir / "RUN_SUMMARY.md", render_operator_summary(results))
        queue_report = {
            "meta": artifact_meta(repo_root=repo_root, repo_slug=repo_slug, run_identifier=active_run_id).to_dict(),
            "run_id": active_run_id,
            "execute": bool(args.execute),
            "strategy": args.strategy,
            "prioritize_ids": prioritize_ids,
            "only_ids": only_ids,
            "processed": len(processed_ids),
            "merged": len(merged_ids),
            "blocked": len([result for result in results if result.lifecycle_state != "merged"]),
            "merged_ids": merged_ids,
            "passes": pass_reports,
            "summaries": [result.to_dict() for result in results],
            "cache": client.cache_summary(),
        }
        write_json(run_dir / "QUEUE_REPORT.json", queue_report)
        print(f"Run ID: {active_run_id}")
        print(f"Processed PRs: {len(processed_ids)}")
        print(f"Merged: {len(merged_ids)}")
        print(f"Artifacts: {run_dir}")
        return 0
    finally:
        release_queue_lock(lock_path)


def _inflate_pr_result(payload: Dict[str, Any]) -> Dict[str, Any]:
    pr_state_payload = payload.get("pr_state", {})
    check_summary_payload = pr_state_payload.get("check_summary")
    if check_summary_payload is not None:
        from .schema import CheckSummary
        pr_state_payload["check_summary"] = CheckSummary(**check_summary_payload)
    payload["pr_state"] = PullRequestState(**pr_state_payload)
    merge_payload = payload.get("merge_decision")
    if merge_payload is not None:
        payload["merge_decision"] = MergeDecision(**merge_payload)
    combined_findings = []
    for item in payload.get("blockers", []):
        combined_findings.append(
            Finding(
                kind=FindingSeverity.BLOCKER,
                finding_type=item.get("type", ""),
                message=item.get("name") or item.get("details") or "",
                details=item.get("metadata", {}),
                source=item.get("source", ""),
            )
        )
    for item in payload.get("warnings", []):
        combined_findings.append(
            Finding(
                kind=FindingSeverity.WARNING,
                finding_type=item.get("finding_type", ""),
                message=item.get("message", ""),
                details=item.get("details", {}),
                source=item.get("source", ""),
            )
        )
    for item in payload.get("observations", []):
        combined_findings.append(
            Finding(
                kind=FindingSeverity.OBSERVATION,
                finding_type=item.get("finding_type", ""),
                message=item.get("message", ""),
                details=item.get("details", {}),
                source=item.get("source", ""),
            )
        )
    payload["findings"] = combined_findings
    payload["truth_sources"] = [TruthSource(**item) for item in payload.get("truth_sources", [])]
    validation_payload = payload.get("validation_report")
    if validation_payload is not None:
        from .schema import ValidationStepResult, Fingerprint as SchemaFingerprint
        fp = validation_payload.get("input_fingerprint")
        payload["validation_report"] = ValidationReport(
            status=validation_payload["status"],
            required_for_merge_ready=validation_payload.get("required_for_merge_ready", True),
            steps=[ValidationStepResult(**step) for step in validation_payload.get("steps", [])],
            attempts=validation_payload.get("attempts", 0),
            remediation_applied=validation_payload.get("remediation_applied", False),
            fingerprint=SchemaFingerprint(**fp) if fp else None,
        )
    payload["thread_dispositions"] = [ThreadDisposition(**item) for item in payload.get("thread_dispositions", [])]
    fp_payload = payload.get("fingerprint")
    if fp_payload is not None:
        payload["fingerprint"] = Fingerprint(**fp_payload)
    payload.pop("blockers", None)
    payload.pop("warnings", None)
    payload.pop("observations", None)
    return payload
