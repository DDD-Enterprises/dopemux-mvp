from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .classification import (
    TRUTH_PRECEDENCE,
    _severity_value,
    _state_value,
    _status_value,
    has_conflicts,
    lifecycle_for_findings,
)
from .github_api import (
    thread_counters,
)
from .merge import decide_merge_action, serialize_check_payload
from .conflict import conflict_recovery_state
from .policy import (
    policy_fingerprint,
)
from .runtime import (
    fingerprint_payload,
    run_command,
    utc_now,
    write_json,
)
from .schema import (
    ArtifactMeta,
    BlockerType,
    Finding,
    FindingSeverity,
    Fingerprint,
    MergeDecision,
    PRResult,
    PRState,
    PullRequestState,
    ReviewThread,
    ThreadDisposition,
    TruthSource,
    ValidationReport,
    ValidationStatus,
)
from .thread_resolution import decide_thread_disposition

__all__ = [
    "artifact_meta",
    "decision_basis_payload",
    "plan_fingerprint",
    "findings_from_pr_state",
    "truth_sources_for",
    "summarize_findings",
    "explain_findings",
    "build_plan_result",
    "render_operator_summary",
    "write_pr_state_artifact",
    "_inflate_pr_result",
]


def decision_basis_payload(
    *,
    winning_reason: str,
    winning_sources: Sequence[str],
    suppressed_sources: Optional[Sequence[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    return {
        "truth_precedence": [
            "policy",
            "github_protection",
            "local_validation",
            "local_apply_state",
            "heuristics",
        ],
        "winning_sources": list(winning_sources),
        "winning_reason": winning_reason,
        "suppressed_sources": list(
            suppressed_sources
            or [{"source": "heuristics", "reason": "lower_precedence"}]
        ),
    }


def artifact_meta(
    *,
    repo_root: Path,
    repo_slug: str,
    run_identifier: str,
    pr_head_sha: str = "",
    base_sha: str = "",
    applied_tree_sha: str = "",
) -> ArtifactMeta:
    remote = run_command(
        ["git", "remote", "get-url", "origin"], cwd=repo_root, timeout_seconds=30
    )
    current_branch = run_command(
        ["git", "branch", "--show-current"], cwd=repo_root, timeout_seconds=30
    )
    default_branch = run_command(
        ["git", "remote", "show", "origin"], cwd=repo_root, timeout_seconds=30
    )
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
        current_branch=(
            current_branch.stdout.strip() if current_branch.returncode == 0 else ""
        ),
        default_branch=default_branch_name,
        pr_head_sha=pr_head_sha,
        base_sha=base_sha,
        applied_tree_sha=applied_tree_sha,
    )


def plan_fingerprint(
    pr: PullRequestState, *, policy_fp: str, plan_review_state: Dict[str, Any]
) -> Fingerprint:
    digest = fingerprint_payload(
        {
            "pr_id": pr.pr_id,
            "head_sha": pr.head_sha,
            "base_sha": pr.base_sha,
            "plan_review_state": plan_review_state,
            "policy_fingerprint": policy_fp,
        }
    )
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


def findings_from_pr_state(
    pr: PullRequestState,
    *,
    check_payload: Dict[str, Any],
    active_threads: int,
    validation_status: ValidationStatus,
    local_validation_required: bool,
    policy: Dict[str, Any],
    threads_resolved_locally: bool = False,
) -> List[Finding]:
    findings: List[Finding] = []
    if str(pr.state).upper() == "MERGED":
        return findings
    if has_conflicts(pr.mergeable, pr.merge_state_status):
        recovery_state = conflict_recovery_state(pr, policy)
        if recovery_state == "semantic_conflict_blocked":
            findings.append(
                Finding(
                    kind=FindingSeverity.BLOCKER,
                    finding_type="semantic_conflict_blocked",
                    message="Conflict automation is blocked by the PR's semantic-conflict label.",
                    details={"labels": pr.labels},
                    source="local_rebase_simulation",
                )
            )
        elif recovery_state == "manual_conflict_required":
            findings.append(
                Finding(
                    kind=FindingSeverity.BLOCKER,
                    finding_type="manual_conflict_required",
                    message="Dirty/conflicted PR is blocked until it opts into mechanical recovery.",
                    details={"labels": pr.labels},
                    source="local_rebase_simulation",
                )
            )
        else:
            findings.append(
                Finding(
                    kind=FindingSeverity.BLOCKER,
                    finding_type=BlockerType.CONFLICT_DETECTED.value,
                    message="Dirty/conflicted PR is eligible for automated mechanical recovery.",
                    details={
                        "labels": pr.labels,
                        "merge_state_status": pr.merge_state_status,
                    },
                    source="local_rebase_simulation",
                )
            )
    if pr.is_draft:
        findings.append(
            Finding(
                kind=FindingSeverity.BLOCKER,
                finding_type="draft_pr",
                message="Draft pull requests are blocked from merge.",
                source="github_protection_review",
            )
        )
    if active_threads > 0:
        if threads_resolved_locally and _status_value(validation_status) == ValidationStatus.PASSED.value:
             findings.append(
                Finding(
                    kind=FindingSeverity.WARNING,
                    finding_type="threads_resolved_locally",
                    message=f"GitHub shows {active_threads} active threads, but they were resolved locally and validation passed.",
                    details={"active_threads": active_threads},
                    source="local_validation",
                )
            )
        else:
            findings.append(
                Finding(
                    kind=FindingSeverity.BLOCKER,
                    finding_type=BlockerType.ACTIVE_THREAD.value,
                    message=f"{active_threads} active unresolved review threads remain.",
                    details={"active_threads": active_threads},
                    source="github_protection_review",
                )
            )
    summary = check_payload["summary"]
    if summary.required_failure > 0:
        # OPTIMISTIC OVERRIDE: If local validation just passed, we suppress the CI failure blocker
        # because we assume GitHub hasn't caught up to the new push yet.
        if _status_value(validation_status) == ValidationStatus.PASSED.value:
            findings.append(
                Finding(
                    kind=FindingSeverity.WARNING,
                    finding_type="ci_failing_but_local_passed",
                    message="GitHub CI is currently failing, but local validation passed. Assuming state transition in progress.",
                    details=serialize_check_payload(check_payload),
                    source="local_validation",
                )
            )
        else:
            findings.append(
                Finding(
                    kind=FindingSeverity.BLOCKER,
                    finding_type=BlockerType.REQUIRED_CHECK_FAILED.value,
                    message="Required checks are failing.",
                    details=serialize_check_payload(check_payload),
                    source="github_protection_review",
                )
            )
    elif summary.required_pending > 0:
        # OPTIMISTIC OVERRIDE: If local validation passed, we assume it will eventually turn green on GH.
        if _status_value(validation_status) == ValidationStatus.PASSED.value:
            findings.append(
                Finding(
                    kind=FindingSeverity.WARNING,
                    finding_type="ci_pending_but_local_passed",
                    message="GitHub CI is pending, but local validation passed.",
                    details=serialize_check_payload(check_payload),
                    source="local_validation",
                )
            )
        else:
            findings.append(
                Finding(
                    kind=FindingSeverity.BLOCKER,
                    finding_type=BlockerType.REQUIRED_CHECK_PENDING.value,
                    message="Required checks are still pending.",
                    details=serialize_check_payload(check_payload),
                    source="github_protection_review",
                )
            )
    approval_required = bool(check_payload.get("approval_required", False))
    if approval_required and check_payload.get("review_decision") == "CHANGES_REQUESTED":
        findings.append(
            Finding(
                kind=FindingSeverity.BLOCKER,
                finding_type=BlockerType.CHANGES_REQUESTED.value,
                message="Review state is CHANGES_REQUESTED.",
                source="github_protection_review",
            )
        )
    elif approval_required and check_payload.get("review_decision") != "APPROVED":
        findings.append(
            Finding(
                kind=FindingSeverity.BLOCKER,
                finding_type=BlockerType.APPROVAL_MISSING.value,
                message="Required approval is missing.",
                source="github_protection_review",
            )
        )
    elif check_payload.get("review_decision") == "CHANGES_REQUESTED":
        findings.append(
            Finding(
                kind=FindingSeverity.WARNING,
                finding_type=BlockerType.CHANGES_REQUESTED.value,
                message="Review state is CHANGES_REQUESTED, but branch protection does not currently require approvals.",
                source="github_protection_review",
            )
        )
    if summary.optional_failure > 0:
        findings.append(
            Finding(
                kind=FindingSeverity.WARNING,
                finding_type="optional_check_failed",
                message="Optional checks are failing.",
                details=serialize_check_payload(check_payload),
                source="github_protection_review",
            )
        )
    if summary.optional_pending > 0:
        findings.append(
            Finding(
                kind=FindingSeverity.WARNING,
                finding_type=BlockerType.OPTIONAL_CHECK_PENDING.value,
                message="Optional checks are still pending.",
                details=serialize_check_payload(check_payload),
                source="github_protection_review",
            )
        )
    if pr.diff_size > 1000:
        findings.append(
            Finding(
                kind=FindingSeverity.WARNING,
                finding_type="large_diff",
                message="Large diff size may increase merge risk.",
                details={"diff_size": pr.diff_size},
                source="heuristics",
            )
        )
    if pr.risk_score > 500:
        findings.append(
            Finding(
                kind=FindingSeverity.OBSERVATION,
                finding_type="high_risk_score",
                message="PR has elevated risk score relative to queue.",
                details={"risk_score": pr.risk_score},
                source="heuristics",
            )
        )
    if (
        local_validation_required
        and _status_value(validation_status) != ValidationStatus.PASSED.value
    ):
        findings.append(
            Finding(
                kind=FindingSeverity.BLOCKER,
                finding_type=(
                    "validation_not_executed"
                    if _status_value(validation_status)
                    == ValidationStatus.NOT_EXECUTED.value
                    else BlockerType.VALIDATION_FAILED.value
                ),
                message="Local validation is required before merge readiness can be declared.",
                details={"validation_status": _status_value(validation_status)},
                source="local_validation",
            )
        )
    return findings


def truth_sources_for(
    check_payload: Dict[str, Any],
    validation_report: ValidationReport,
    policy: Dict[str, Any],
    *,
    rebase_status: str = "not_run",
) -> List[TruthSource]:
    return [
        TruthSource(
            name="effective_policy",
            status="loaded",
            details={"policy_fingerprint": policy_fingerprint(policy)},
        ),
        TruthSource(
            name="github_protection_review",
            status="observed",
            details=serialize_check_payload(check_payload),
        ),
        TruthSource(
            name="local_validation",
            status=_status_value(validation_report.status),
            details=validation_report.to_dict(),
        ),
        TruthSource(name="local_rebase_simulation", status=rebase_status, details={}),
        TruthSource(
            name="heuristics",
            status="computed",
            details={"precedence": TRUTH_PRECEDENCE},
        ),
    ]


def summarize_findings(
    findings: Sequence[Finding],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    blockers = [
        finding.to_dict()
        for finding in findings
        if _severity_value(finding.kind) == FindingSeverity.BLOCKER.value
    ]
    warnings = [
        finding.to_dict()
        for finding in findings
        if _severity_value(finding.kind) == FindingSeverity.WARNING.value
    ]
    observations = [
        finding.to_dict()
        for finding in findings
        if _severity_value(finding.kind) == FindingSeverity.OBSERVATION.value
    ]
    return blockers, warnings, observations


def explain_findings(
    findings: Sequence[Finding], *, previous: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    blockers, warnings, observations = summarize_findings(findings)
    next_action = "merge" if not blockers else "clear blockers"
    changed_since_prior: List[str] = []
    if previous:
        previous_blockers = {
            item.get("finding_type") or item.get("type")
            for item in previous.get("blockers", [])
        }
        current_blockers = {
            item.get("finding_type") or item.get("type") for item in blockers
        }
        previous_blockers.discard(None)
        current_blockers.discard(None)
        added = sorted(current_blockers - previous_blockers)
        removed = sorted(previous_blockers - current_blockers)
        if added:
            changed_since_prior.append("added blockers: " + ", ".join(added))
        if removed:
            changed_since_prior.append("cleared blockers: " + ", ".join(removed))
    return {
        "why_blocked": [
            item.get("message") or item.get("name") or "" for item in blockers
        ],
        "evidence": blockers + warnings,
        "next_action": next_action,
        "changed_since_prior_scan": changed_since_prior,
        "warnings": warnings,
        "observations": observations,
    }


def build_plan_result(
    *,
    active_run_id: str,
    pr: PullRequestState,
    threads: List[ReviewThread],
    check_payload: Dict[str, Any],
    validation_report: ValidationReport,
    policy: Dict[str, Any],
    previous_result: Optional[Dict[str, Any]] = None,
    threads_resolved_locally: bool = False,
) -> PRResult:
    unresolved_total, active_threads, outdated_threads = thread_counters(threads)
    plan_review_state = {
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
            validation_green=_status_value(validation_report.status)
            == ValidationStatus.PASSED.value,
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
        local_validation_required=bool(
            policy.get("validation", {}).get(
                "require_local_validation_for_merge_ready", True
            )
        ),
        policy=policy,
        threads_resolved_locally=threads_resolved_locally,
    )
    fingerprint = plan_fingerprint(
        pr, policy_fp=policy_fingerprint(policy), plan_review_state=plan_review_state
    )
    truth = truth_sources_for(check_payload, validation_report, policy)
    decision = decide_merge_action(
        pr=pr, findings=findings, validation_report=validation_report
    )
    explain = explain_findings(findings, previous=previous_result)
    if str(pr.state).upper() == "MERGED":
        pr_lifecycle_state = PRState.MERGED
    elif (
        pr.auto_merge_enabled 
        and _status_value(validation_report.status) == ValidationStatus.PASSED.value
        and not any(
            finding.finding_type != BlockerType.REQUIRED_CHECK_PENDING.value
            for finding in findings
            if _severity_value(finding.kind) == FindingSeverity.BLOCKER.value
        )
    ):
        pr_lifecycle_state = PRState.QUEUED_FOR_MERGE
    else:
        pr_lifecycle_state = lifecycle_for_findings(
            findings, validation_status=validation_report.status
        )
    lifecycle_state = _state_value(pr_lifecycle_state)
    operator_state = (
        "queued_for_merge"
        if pr_lifecycle_state == PRState.QUEUED_FOR_MERGE
        else ""
    )
    return PRResult(
        run_id=active_run_id,
        pr_state=replace(pr, lifecycle_state=pr_lifecycle_state),
        lifecycle_state=lifecycle_state,
        apply_actions=[
            f"rebase {pr.head_ref} onto {pr.base_ref}",
            "resolve review threads",
            "run validation",
        ],
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
        artifacts={
            "explain": json.dumps(explain),
            "operator_state": operator_state,
        },
    )


def render_operator_summary(results: Sequence[PRResult]) -> str:
    lines = [
        "# Queue Summary",
        "",
        "| PR | State | Confidence | Blockers | Warnings | Next action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        blockers, warnings, _ = summarize_findings(result.findings)
        confidence = (
            "high"
            if not blockers
            and result.validation_report
            and _status_value(result.validation_report.status)
            == ValidationStatus.PASSED.value
            else "medium" if not blockers else "blocked"
        )
        next_action = "merge" if not blockers else "clear blockers"
        lines.append(
            f"| #{result.pr_state.pr_id} | {result.lifecycle_state} | {confidence} | {len(blockers)} | {len(warnings)} | {next_action} |"
        )
    return "\n".join(lines) + "\n"


def write_pr_state_artifact(pr_dir: Path, result: PRResult) -> None:
    write_json(pr_dir / "STATE.json", result.to_dict())


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
    payload["truth_sources"] = [
        TruthSource(**item) for item in payload.get("truth_sources", [])
    ]
    validation_payload = payload.get("validation_report")
    if validation_payload is not None:
        from .schema import Fingerprint as SchemaFingerprint
        from .schema import ValidationStepResult

        fp = validation_payload.get("input_fingerprint")
        payload["validation_report"] = ValidationReport(
            status=validation_payload["status"],
            required_for_merge_ready=validation_payload.get(
                "required_for_merge_ready", True
            ),
            steps=[
                ValidationStepResult(**step)
                for step in validation_payload.get("steps", [])
            ],
            attempts=validation_payload.get("attempts", 0),
            remediation_applied=validation_payload.get("remediation_applied", False),
            fingerprint=SchemaFingerprint(**fp) if fp else None,
        )
    payload["thread_dispositions"] = [
        ThreadDisposition(**item) for item in payload.get("thread_dispositions", [])
    ]
    fp_payload = payload.get("fingerprint")
    if fp_payload is not None:
        payload["fingerprint"] = Fingerprint(**fp_payload)
    payload.pop("blockers", None)
    payload.pop("warnings", None)
    payload.pop("observations", None)
    return payload
