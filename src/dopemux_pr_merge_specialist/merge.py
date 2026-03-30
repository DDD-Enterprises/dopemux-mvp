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
        # If the only non-check blocker is APPROVAL_MISSING, and checks are otherwise green,
        # we can consider an admin bypass squash merge.
        if (
            len(non_check_blockers) == 1 
            and non_check_blockers[0].finding_type == BlockerType.APPROVAL_MISSING.value
            and not pending_checks
            and _status_value(validation_report.status) == ValidationStatus.PASSED.value
        ):
            return MergeDecision(
                action=MergeActionType.ADMIN_BYPASS_SQUASH,
                command=[],
                reason="Only missing approvals remain; opting for admin-bypass squash merge.",
                reason_code="admin_bypass_ready",
            )

    if pending_checks and not non_check_blockers:
        return MergeDecision(
            action=MergeActionType.AUTO_MERGE_ENABLE,
            command=[],
            reason="All structural gates green; enabling auto-merge for pending checks.",
            reason_code="auto_merge_pending_checks",
        )

    return MergeDecision(
        action=MergeActionType.REBASE_MERGE,
        command=[],
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
    action = _state_value(decision.action)
    if action == MergeActionType.BLOCKED.value:
        return decision

    pr_payload = client.fetch_pr(pr_id)
    title = pr_payload.get("title", f"PR #{pr_id}")

    if not execute:
        return decision

    success = False
    if action == MergeActionType.ADMIN_BYPASS_SQUASH.value:
        success = client.merge_pr(
            pr_id, title=title, method="squash", admin_bypass=True
        )
    elif action == MergeActionType.REBASE_MERGE.value:
        success = client.merge_pr(
            pr_id, title=title, method="rebase", admin_bypass=False
        )
    elif action == MergeActionType.AUTO_MERGE_FALLBACK.value:
        # For auto-merge, we still use the 'gh pr merge --auto' command via shell for now
        # until client support is added, but REBASE is the preference.
        command = ["gh", "pr", "merge", str(pr_id), "--auto", "--rebase", "--delete-branch"]
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
        success = result.returncode == 0

    if success:
        client.invalidate(f"pr:{pr_id}")
        return decision

    return MergeDecision(
        action=MergeActionType.BLOCKED,
        command=[],
        reason="Merge command execution failed.",
        reason_code="merge_execution_failed",
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
        "failed_required_checks": payload.get("failed_required_checks", []),
        "failed_required_check_entries": payload.get(
            "failed_required_check_entries", []
        ),
        "pending_required_checks": payload.get("pending_required_checks", []),
        "blocker_types": payload.get("blocker_types", []),
        "warning_types": payload.get("warning_types", []),
    }
