from __future__ import annotations

import pytest

from dopemux_pr_merge_specialist import engine
from dopemux_pr_merge_specialist.plan_builder import findings_from_pr_state
from dopemux_pr_merge_specialist.schema import CheckSummary, Finding, FindingSeverity, PRState, PullRequestState, ValidationStatus


def _state(
    pr_id: int,
    *,
    base: str,
    head: str,
    pr_class: str,
    risk: float,
    diff: int,
    labels: list[str] | None = None,
    mergeable: str = "MERGEABLE",
    merge_state_status: str = "CLEAN",
) -> PullRequestState:
    return PullRequestState(
        pr_id=pr_id,
        title=f"PR {pr_id}",
        author="tester",
        state="OPEN",
        base_ref=base,
        head_ref=head,
        ci_status="SUCCESS",
        mergeable=mergeable,
        merge_state_status=merge_state_status,
        review_decision="APPROVED",
        updated_at="2026-03-12T00:00:00Z",
        additions=diff,
        deletions=0,
        changed_files=1,
        unresolved_threads=0,
        active_unresolved_threads=0,
        outdated_unresolved_threads=0,
        pr_class=pr_class,  # type: ignore[arg-type]
        risk_score=risk,
        lifecycle_state=PRState.DISCOVERED,
        head_sha=f"head-{pr_id}",
        base_sha="base-main",
        labels=labels or [],
    )

def test_risk_score_penalizes_active_threads_and_failures():
    low = engine.risk_score(
        pr_class="READY",
        additions=10,
        deletions=0,
        changed_files=1,
        active_threads=0,
        outdated_threads=0,
        ci_state="SUCCESS",
        merge_state_status="CLEAN",
    )
    high = engine.risk_score(
        pr_class="MIXED",
        additions=10,
        deletions=0,
        changed_files=1,
        active_threads=2,
        outdated_threads=0,
        ci_state="FAILURE",
        merge_state_status="BEHIND",
    )
    assert high > low


def test_invalid_transition_raises():
    with pytest.raises(RuntimeError):
        engine.ensure_transition(PRState.DISCOVERED, PRState.MERGED)


def test_lifecycle_for_findings_blocks_on_blockers():
    findings = [
        Finding(
            kind=FindingSeverity.BLOCKER,
            finding_type="required_check_pending",
            message="blocked",
            source="github_protection_review",
        )
    ]
    assert engine.lifecycle_for_findings(findings, validation_status=ValidationStatus.NOT_EXECUTED) == PRState.APPLY_BLOCKED


def test_findings_from_pr_state_keeps_required_check_failures_blocking_after_local_pass() -> None:
    pr = _state(
        401,
        base="main",
        head="feature/failing-checks",
        pr_class="CI_ONLY",
        risk=5.0,
        diff=10,
    )
    findings = findings_from_pr_state(
        pr,
        check_payload={
            "summary": CheckSummary(required_failure=1, total=1, failure=1),
            "review_decision": "APPROVED",
            "approval_required": False,
            "blocker_types": ["required_check_failed"],
            "warning_types": [],
        },
        active_threads=0,
        validation_status=ValidationStatus.PASSED,
        local_validation_required=True,
        policy={},
    )

    blocker_types = {finding.finding_type for finding in findings if finding.kind == FindingSeverity.BLOCKER}

    assert "required_check_failed" in blocker_types
