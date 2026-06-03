from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from .conflict import (
    apply_suggestion_to_file,
    comment_prefers_conflict_side,
)
from .github_api import (
    BOT_AUTHORS,
)
from .runtime import (
    CommandResult,
    append_command_log,
    run_command,
    contains_marker,
)
from .schema import (
    ReviewThread,
    ThreadComment,
    ThreadDisposition,
)

__all__ = [
    "latest_comment",
    "contains_marker",
    "has_newer_objection",
    "has_resolution_signal",
    "is_implementable_comment",
    "decide_thread_disposition",
    "graphql_escape",
    "graph_reply_to_thread",
    "graph_resolve_thread",
    "_graphql_mutation_ok",
    "_is_rate_limited",
    "_execute_thread_graphql",
    "apply_thread_dispositions",
]


def latest_comment(thread: ReviewThread) -> Optional[ThreadComment]:
    if not thread.comments:
        return None
    return sorted(thread.comments, key=lambda comment: comment.created_at or "")[-1]


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
    for comment in sorted(
        thread.comments, key=lambda comment: comment.created_at or ""
    ):
        if contains_marker(comment.body, markers):
            return True
    return False


def is_implementable_comment(
    comment: Optional[ThreadComment], policy: Dict[str, Any]
) -> bool:
    if comment is None:
        return False
    body = comment.body
    if comment_prefers_conflict_side(body) is not None:
        return True
    patterns = [
        str(item).lower()
        for item in policy.get("thread_rules", {}).get("implementable_patterns", [])
    ]
    lowered = body.lower()
    if any(pattern in lowered for pattern in patterns):
        return True
    if re.search(
        r"change\s+<code>.*?</code>\s+to\s+<code>.*?</code>",
        body,
        re.IGNORECASE | re.DOTALL,
    ):
        return True
    if re.search(
        r"(?:delete|remove)\s+(?:the\s+)?(?:line\s+)?<code>.*?</code>",
        body,
        re.IGNORECASE | re.DOTALL,
    ):
        return True
    return False


def is_actionable_comment(
    comment: Optional[ThreadComment], policy: Dict[str, Any]
) -> bool:
    if comment is None:
        return False
    thread_rules = policy.get("thread_rules", {})
    if not bool(thread_rules.get("enable_agentic_fix", False)):
        return False
    if comment.author in BOT_AUTHORS:
        return False
    body = comment.body.strip()
    if len(body) < 10:
        return False
    return True


def decide_thread_disposition(
    thread: ReviewThread, *, validation_green: bool, policy: Dict[str, Any]
) -> ThreadDisposition:
    comment = latest_comment(thread)
    path = comment.path if comment and comment.path else thread.path
    thread_rules = policy.get("thread_rules", {})
    if (
        validation_green
        and thread_rules.get("auto_resolve_outdated", True)
        and not has_newer_objection(thread, policy)
        and (
            thread.is_outdated
            or (
                thread_rules.get("auto_resolve_resolution_signals", True)
                and has_resolution_signal(thread, policy)
            )
        )
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
    if is_actionable_comment(comment, policy):
        return ThreadDisposition(
            thread_id=thread.id,
            disposition="agentic_fix",
            reason="Thread contains human feedback actionable by AI remediation agent.",
            path=path,
        )
    return ThreadDisposition(
        thread_id=thread.id,
        disposition="decline_with_rationale",
        reason="Suggestion is not safely auto-applicable; posting rationale and resolving.",
        path=path,
    )


def graphql_escape(value: str) -> str:
    return json.dumps(value)[1:-1]


def graph_reply_to_thread(
    thread_id: str, body: str, *, repo_root: Path, timeout_seconds: int
) -> CommandResult:
    query = (
        "mutation { addPullRequestReviewThreadReply(input: "
        f'{{pullRequestReviewThreadId: "{graphql_escape(thread_id)}", body: "{graphql_escape(body)}"}}) '
        "{ comment { id } } }"
    )
    return run_command(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        cwd=repo_root,
        timeout_seconds=timeout_seconds,
    )


def graph_resolve_thread(
    thread_id: str, *, repo_root: Path, timeout_seconds: int
) -> CommandResult:
    query = (
        "mutation { resolveReviewThread(input: "
        f'{{threadId: "{graphql_escape(thread_id)}"}}) {{ thread {{ id isResolved }} }} }}'
    )
    return run_command(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        cwd=repo_root,
        timeout_seconds=timeout_seconds,
    )


def _graphql_mutation_ok(result: CommandResult) -> bool:
    if result.returncode != 0:
        return False
    try:
        data = json.loads(result.stdout)
        return not data.get("errors")
    except json.JSONDecodeError:
        return False


def _is_rate_limited(result: CommandResult) -> bool:
    stderr = (result.stderr or "").lower()
    return "rate limit" in stderr or "too many requests" in stderr


def _execute_thread_graphql(
    func, *args, max_retries: int = 3, initial_backoff: float = 2.0, **kwargs
) -> CommandResult:
    retries = 0
    while retries < max_retries:
        result = func(*args, **kwargs)
        if _graphql_mutation_ok(result):
            return result
        if not _is_rate_limited(result):
            return result

        retries += 1
        if retries < max_retries:
            time.sleep(initial_backoff * (2 ** (retries - 1)))

    return result


def apply_thread_dispositions(
    *,
    dispositions: List[ThreadDisposition],
    threads_by_id: Dict[str, ReviewThread],
    worktree_path: Path,
    base_ref: str,
    execute: bool,
    commands_log: Path,
    repo_root: Path,
    policy: Dict[str, Any],
) -> List[ThreadDisposition]:
    applied: List[ThreadDisposition] = []
    timeout_seconds = int(policy.get("timeouts", {}).get("gh_seconds", 120) or 120)
    strict_conflicts = bool(policy.get("conflict_rules", {}).get("strict", True))
    for disposition in dispositions:
        thread = threads_by_id[disposition.thread_id]
        comment = latest_comment(thread)
        if disposition.disposition == "implement":
            if comment is None:
                applied.append(
                    ThreadDisposition(
                        thread_id=disposition.thread_id,
                        disposition="escalate",
                        reason="No comment payload found for implement disposition.",
                        path=disposition.path,
                        escalation_needed=True,
                    )
                )
                continue
            ok, reason = apply_suggestion_to_file(
                worktree_path=worktree_path,
                thread=thread,
                comment=comment,
                base_ref=base_ref,
                policy=policy,
            )[:2]
            if not ok:
                applied.append(
                    ThreadDisposition(
                        thread_id=disposition.thread_id,
                        disposition=(
                            "escalate" if strict_conflicts else "decline_with_rationale"
                        ),
                        reason=f"Auto-implement failed: {reason}",
                        path=disposition.path,
                        escalation_needed=strict_conflicts,
                    )
                )
                continue
            if execute:
                append_command_log(
                    commands_log,
                    _execute_thread_graphql(
                        graph_reply_to_thread,
                        disposition.thread_id,
                        "Automated queue-drain applied a minimal fix and will run verification before resolving this thread.",
                        repo_root=repo_root,
                        timeout_seconds=timeout_seconds,
                    ),
                )
                # DEFERRED: graph_resolve_thread is no longer called here.
                # It must be called after verification passes.
            applied.append(
                ThreadDisposition(
                    thread_id=disposition.thread_id,
                    disposition="implement",
                    reason=reason,
                    path=disposition.path,
                    applied=True,
                )
            )
            continue
        if disposition.disposition == "decline_with_rationale":
            if execute:
                append_command_log(
                    commands_log,
                    _execute_thread_graphql(
                        graph_reply_to_thread,
                        disposition.thread_id,
                        "Automated queue-drain could not safely auto-apply this suggestion. Keeping behavior deterministic and deferring to a targeted follow-up fix.",
                        repo_root=repo_root,
                        timeout_seconds=timeout_seconds,
                    ),
                )
                # DEFERRED: Resolution moved to resolve_verified_threads
            applied.append(
                ThreadDisposition(
                    thread_id=disposition.thread_id,
                    disposition="decline_with_rationale",
                    reason=disposition.reason,
                    path=disposition.path,
                    applied=True,
                )
            )
            continue
        if disposition.disposition == "auto_resolve_outdated":
            if execute:
                append_command_log(
                    commands_log,
                    _execute_thread_graphql(
                        graph_reply_to_thread,
                        disposition.thread_id,
                        "Outdated thread candidate for auto-resolution; pending verification.",
                        repo_root=repo_root,
                        timeout_seconds=timeout_seconds,
                    ),
                )
                # DEFERRED: Resolution moved to resolve_verified_threads
            applied.append(
                ThreadDisposition(
                    thread_id=disposition.thread_id,
                    disposition="auto_resolve_outdated",
                    reason=disposition.reason,
                    path=disposition.path,
                    applied=True,
                )
            )
            continue
        if disposition.disposition == "agentic_fix":
            # Agentic fixes are heavy and require isolation/verification cycles.
            # We mark them as NOT applied here; they must be handled by the
            # caller (e.g. pr_apply in queue_drain.py) using remediate_review_thread.
            applied.append(
                ThreadDisposition(
                    thread_id=disposition.thread_id,
                    disposition="agentic_fix",
                    reason="Thread marked for agentic remediation; pending execution slice.",
                    path=disposition.path,
                    applied=False,  # Must be set to True by the orchestrator after successful agent run
                )
            )
            continue
        applied.append(disposition)
    return applied


def resolve_verified_threads(
    *,
    dispositions: List[ThreadDisposition],
    execute: bool,
    commands_log: Path,
    repo_root: Path,
    policy: Dict[str, Any],
) -> bool:
    """Resolve threads that were previously applied or marked for resolution, now that verification has passed."""
    if not execute:
        return False

    timeout_seconds = int(policy.get("timeouts", {}).get("gh_seconds", 120) or 120)
    attempted = False
    all_succeeded = True
    for disposition in dispositions:
        if not disposition.applied:
            continue

        if disposition.disposition in {
            "implement",
            "agentic_fix",
            "auto_resolve_outdated",
        }:
            attempted = True
            # Post evidence-backed reply first
            reply_body = f"✅ Automated verification passed for this {disposition.disposition}."
            if disposition.disposition == "agentic_fix":
                reply_body = (
                    "🤖 Agentic remediation complete. A minimal surgical fix was applied "
                    "and local validation suites passed. Resolving thread."
                )
            elif disposition.disposition == "implement":
                reply_body = "✅ Machine-applicable suggestion applied and verified locally. Resolving thread."

            reply_result = _execute_thread_graphql(
                graph_reply_to_thread,
                disposition.thread_id,
                reply_body,
                repo_root=repo_root,
                timeout_seconds=timeout_seconds,
            )
            append_command_log(commands_log, reply_result)
            if not _graphql_mutation_ok(reply_result):
                all_succeeded = False

            # Then resolve
            resolve_result = _execute_thread_graphql(
                graph_resolve_thread,
                disposition.thread_id,
                repo_root=repo_root,
                timeout_seconds=timeout_seconds,
            )
            append_command_log(commands_log, resolve_result)
            if not _graphql_mutation_ok(resolve_result):
                all_succeeded = False
    return attempted and all_succeeded
