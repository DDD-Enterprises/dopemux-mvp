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
    "_status_value",
    "_severity_value",
    "_state_value",
    "ensure_transition",
    "classify_pr",
    "risk_score",
    "build_pr_state",
    "lifecycle_for_findings",
    "has_conflicts",
    "CLASS_PRIORITY",
    "VALID_TRANSITIONS",
    "TRUTH_PRECEDENCE",
]

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
    PRState.MERGE_BLOCKED: {
        PRState.PLANNED,
        PRState.APPLIED,
        PRState.ABORTED,
        PRState.ESCALATED,
    },
    PRState.MERGE_READY: {PRState.QUEUED_FOR_MERGE, PRState.MERGED, PRState.ABORTED},
    PRState.QUEUED_FOR_MERGE: {PRState.MERGED, PRState.ABORTED},
    PRState.MERGED: set(),
    PRState.ESCALATED: {PRState.PLANNED, PRState.ABORTED},
    PRState.ABORTED: set(),
}


def _status_value(status: Any) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _severity_value(kind: Any) -> str:
    return kind.value if hasattr(kind, "value") else str(kind)


def _state_value(state: Any) -> str:
    return state.value if hasattr(state, "value") else str(state)


def ensure_transition(current: PRState, target: PRState) -> None:
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise RuntimeError(f"Invalid lifecycle transition: {current} -> {target}")


def lifecycle_for_findings(
    findings: Sequence[Finding], *, validation_status: ValidationStatus
) -> PRState:
    blockers = [
        item
        for item in findings
        if _severity_value(item.kind) == FindingSeverity.BLOCKER.value
    ]
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


def classify_pr(
    *, ci_state: str, conflicts: bool, active_unresolved_threads: int, is_draft: bool
) -> str:
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


def build_pr_state(
    raw: Dict[str, Any],
    unresolved_total: int,
    active_unresolved: int,
    outdated_unresolved: int,
) -> PullRequestState:
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
        labels=[
            item.get("name", "")
            for item in raw.get("labels", [])
            if isinstance(item, dict)
        ],
        updated_at=raw.get("updatedAt", ""),
        is_draft=bool(raw.get("isDraft", False)),
        auto_merge_enabled=bool(raw.get("autoMergeRequest")),
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
