from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
import time
from collections import defaultdict, deque
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .classification import _severity_value, _state_value, _status_value
from .github_api import (
    BOT_AUTHORS,
    GitHubClient,
    ci_status,
    summarize_checks,
    thread_counters,
)
from .policy import (
    PolicyError,
    load_effective_policy,
    policy_artifact_payload,
    policy_fingerprint,
)
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
    POLICY_SCHEMA_VERSION,
    TOOL_VERSION,
    ArtifactMeta,
    BlockerType,
    FallbackReason,
    Finding,
    FindingSeverity,
    Fingerprint,
    MergeActionType,
    MergeDecision,
    OverrideRecord,
    PhaseRecord,
    PreflightCheck,
    PreflightResult,
    PRResult,
    PRState,
    PRStateData,
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
)
from .strategy_library import STRATEGY_LIBRARY
from .validation import run_validation, validation_report_md

__all__ = [
    "checks_green",
    "wait_for_green_checks",
    "checks_blocker_reason",
    "decide_merge_action",
    "run_merge_with_fallback",
    "serialize_check_payload",
]


def checks_green(check_payload: Dict[str, Any]) -> bool:
    summary = check_payload["summary"]
    return summary.required_failure == 0 and summary.required_pending == 0


def wait_for_green_checks(
    *, pr_id: int, client: GitHubClient, execute: bool, policy: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
    payload = client.query_checks(pr_id)
    green = checks_green(payload)
    history: List[Dict[str, Any]] = [
        {"attempt": 1, "green": green, **serialize_check_payload(payload)}
    ]
    wait_seconds = int(policy.get("check_rules", {}).get("wait_seconds", 900) or 900)
    poll_seconds = int(policy.get("check_rules", {}).get("poll_seconds", 30) or 30)
    summary = payload["summary"]
    review_decision = str(payload.get("review_decision") or "")
    approval_required = bool(payload.get("approval_required", False))
    if approval_required and review_decision and review_decision != "APPROVED":
        final_status = (
            "approval_missing"
            if review_decision != "CHANGES_REQUESTED"
            else "changes_requested"
        )
        return (
            green,
            payload,
            {
                "wait_used": False,
                "wait_reason": final_status,
                "iterations": 1,
                "final_status": final_status,
                "timed_out": False,
                "history": history,
            },
        )
    if (
        not execute
        or green
        or wait_seconds <= 0
        or summary.required_pending == 0
        or summary.required_failure > 0
    ):
        final_status = (
            "green"
            if green
            else (
                "required_failed"
                if summary.required_failure > 0
                else (
                    "required_pending" if summary.required_pending > 0 else "not_waited"
                )
            )
        )
        return (
            green,
            payload,
            {
                "wait_used": False,
                "wait_reason": "execute_disabled" if not execute else "no_wait_needed",
                "iterations": 1,
                "final_status": final_status,
                "timed_out": False,
                "history": history,
            },
        )
    deadline = time.time() + wait_seconds
    waited = False
    while time.time() < deadline:
        time.sleep(max(poll_seconds, 1))
        waited = True
        client.invalidate(f"pr:{pr_id}")
        payload = client.query_checks(pr_id)
        green = checks_green(payload)
        history.append(
            {
                "attempt": len(history) + 1,
                "green": green,
                **serialize_check_payload(payload),
            }
        )
        summary = payload["summary"]
        if green or summary.required_pending == 0 or summary.required_failure > 0:
            break
    summary = payload["summary"]
    return (
        green,
        payload,
        {
            "wait_used": waited,
            "wait_reason": "healthy_required_pending",
            "iterations": len(history),
            "final_status": (
                "green"
                if green
                else (
                    "required_failed"
                    if summary.required_failure > 0
                    else "required_pending"
                )
            ),
            "timed_out": waited and not green and summary.required_pending > 0,
            "history": history,
        },
    )


def checks_blocker_reason(
    check_payload: Dict[str, Any], check_wait_payload: Dict[str, Any]
) -> str:
    summary = check_payload["summary"]
    if summary.required_failure > 0:
        return "Required checks are failing."
    if summary.required_pending > 0:
        if check_wait_payload.get("timed_out"):
            return "Required checks are still pending after the wait window."
        return "Required checks are still pending but currently healthy."
    if bool(check_payload.get("approval_required", False)) and check_payload.get(
        "review_decision"
    ) == "CHANGES_REQUESTED":
        return "Changes have been requested."
    if bool(check_payload.get("approval_required", False)) and check_payload.get(
        "review_decision"
    ) != "APPROVED":
        return "Required approval is still missing."
    return "Required checks are not fully green."


def decide_merge_action(
    *,
    pr: PullRequestState,
    findings: Sequence[Finding],
    validation_report: ValidationReport,
) -> MergeDecision:
    blockers = [
        item
        for item in findings
        if _severity_value(item.kind) == FindingSeverity.BLOCKER.value
    ]
    
    # Check if the only blockers are pending checks
    non_check_blockers = [
        b
        for b in blockers
        if b.finding_type != BlockerType.REQUIRED_CHECK_PENDING.value
    ]
    pending_checks = [
        b
        for b in blockers
        if b.finding_type == BlockerType.REQUIRED_CHECK_PENDING.value
    ]

    if non_check_blockers:
        return MergeDecision(
            action=MergeActionType.BLOCKED,
            command=[],
            reason="; ".join(item.message for item in non_check_blockers),
            reason_code=non_check_blockers[0].finding_type,
        )
        
    if _status_value(validation_report.status) != ValidationStatus.PASSED.value:
        return MergeDecision(
            action=MergeActionType.BLOCKED,
            command=[],
            reason="Local validation has not produced a passing result for this SHA.",
            reason_code="validation_missing_or_failed",
        )

    if pending_checks:
        return MergeDecision(
            action=MergeActionType.AUTO_MERGE_FALLBACK,
            command=["gh", "pr", "merge", str(pr.pr_id), "--auto", "--rebase", "--delete-branch"],
            reason="All structural gates green; enabling auto-merge for pending checks.",
            reason_code="auto_merge_pending_checks",
        )

    return MergeDecision(
        action=MergeActionType.REBASE_MERGE,
        command=["gh", "pr", "merge", str(pr.pr_id), "--rebase", "--delete-branch"],
        reason="All gates are green; rebase merge selected by default.",
        reason_code="rebase_merge_ready",
    )


def run_merge_with_fallback(
    *,
    decision: MergeDecision,
    pr_id: int,
    execute: bool,
    repo: Optional[str],
    commands_log: Path,
    repo_root: Path,
    policy: Dict[str, Any],
    client: GitHubClient,
) -> MergeDecision:
    if _state_value(decision.action) == MergeActionType.BLOCKED.value:
        return decision
    command = list(decision.command)
    if repo:
        command.extend(["--repo", repo])
    result = execute_or_dry_run(
        command,
        execute=execute,
        cwd=repo_root,
        commands_log=commands_log,
        timeout_seconds=int(
            policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
        ),
    )
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
    if (
        "merge queue required" in stderr
        or ("merge queue" in stderr and "required" in stderr)
        or ("merge queue enabled" in stderr and "--delete-branch" in stderr)
        or ("merge queue enabled" in stderr and "-d" in stderr)
    ):
        fallback_reason = FallbackReason.MERGE_QUEUE_REQUIRED.value
    elif "auto-merge is required" in stderr or (
        "auto-merge" in stderr and "required" in stderr
    ):
        fallback_reason = FallbackReason.AUTO_MERGE_REQUIRED_BY_PROTECTION.value
    elif (
        "rebase merge is not allowed" in stderr
        or "rebase commits are not allowed" in stderr
    ):
        fallback_reason = FallbackReason.DIRECT_MERGE_DISALLOWED_BY_POLICY.value
    else:
        return MergeDecision(
            action=MergeActionType.BLOCKED,
            command=command,
            reason=f"Rebase merge failed: {result.stderr.strip()}",
            reason_code="rebase_merge_failed",
        )
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
    fallback_command = ["gh", "pr", "merge", str(pr_id), "--auto"]
    if repo:
        fallback_command.extend(["--repo", repo])
    fallback = execute_or_dry_run(
        fallback_command,
        execute=execute,
        cwd=repo_root,
        commands_log=commands_log,
        timeout_seconds=int(
            policy.get("timeouts", {}).get("subprocess_seconds", 600) or 600
        ),
    )
    if fallback.returncode == 0:
        client.invalidate(f"pr:{pr_id}")
        return MergeDecision(
            action=MergeActionType.AUTO_MERGE_FALLBACK,
            command=fallback_command,
            reason="Rebase merge blocked by explicit policy; auto-merge fallback succeeded.",
            reason_code=fallback_reason,
        )
    return MergeDecision(
        action=MergeActionType.BLOCKED,
        command=fallback_command,
        reason=f"Fallback auto-merge failed: {fallback.stderr.strip()}",
        reason_code="auto_merge_fallback_failed",
    )


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
        "approval_required": bool(payload.get("approval_required", False)),
        "mergeable": payload.get("mergeable", ""),
        "merge_state_status": payload.get("merge_state_status", ""),
        "protection": payload.get("protection", {}),
        "blocker_types": payload.get("blocker_types", []),
        "warning_types": payload.get("warning_types", []),
    }
