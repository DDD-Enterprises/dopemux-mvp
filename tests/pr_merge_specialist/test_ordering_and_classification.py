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


def test_classify_pr_states():
    assert engine.classify_pr(ci_state="SUCCESS", conflicts=False, active_unresolved_threads=0, is_draft=False) == "READY"
    assert engine.classify_pr(ci_state="FAILURE", conflicts=False, active_unresolved_threads=0, is_draft=False) == "CI_ONLY"
    assert engine.classify_pr(ci_state="SUCCESS", conflicts=True, active_unresolved_threads=0, is_draft=False) == "CONFLICTS_ONLY"
    assert engine.classify_pr(ci_state="SUCCESS", conflicts=False, active_unresolved_threads=2, is_draft=False) == "COMMENTS_ONLY"


def test_hybrid_ordering_respects_dependency_edges():
    p1 = _state(101, base="main", head="feature/a", pr_class="READY", risk=5.0, diff=10)
    p2 = _state(102, base="feature/a", head="feature/b", pr_class="READY", risk=1.0, diff=10)
    p3 = _state(103, base="main", head="feature/c", pr_class="READY", risk=3.0, diff=10)
    p4 = _state(104, base="main", head="feature/d", pr_class="READY", risk=2.0, diff=10)

    ordered, layers, edges, cycle = engine.sort_states([p1, p2, p3, p4], strategy="hybrid")

    assert cycle is False
    assert edges[101] == [102]
    ordered_ids = [item.pr_id for item in ordered]
    assert ordered_ids.index(101) < ordered_ids.index(102)
    assert layers


def test_simple_ordering_for_small_queues():
    p1 = _state(201, base="main", head="h1", pr_class="MIXED", risk=20.0, diff=100)
    p2 = _state(202, base="main", head="h2", pr_class="READY", risk=1.0, diff=5)
    p3 = _state(203, base="main", head="h3", pr_class="CI_ONLY", risk=5.0, diff=10)

    ordered, layers, edges, cycle = engine.sort_states([p1, p2, p3], strategy="hybrid")

    assert [item.pr_id for item in ordered] == [202, 203, 201]
    assert len(layers) == 1
    assert edges == {}
    assert cycle is False


def test_sort_states_prioritizes_eligible_conflicts_over_manual_conflict_blocks():
    eligible = _state(
        301,
        base="main",
        head="feature/eligible",
        pr_class="CONFLICTS_ONLY",
        risk=10.0,
        diff=15,
        labels=["conflict:mechanical"],
        mergeable="CONFLICTING",
        merge_state_status="DIRTY",
    )
    blocked = _state(
        302,
        base="main",
        head="feature/blocked",
        pr_class="CONFLICTS_ONLY",
        risk=1.0,
        diff=5,
        mergeable="CONFLICTING",
        merge_state_status="DIRTY",
    )

    ordered, _layers, _edges, _cycle = engine.sort_states(
        [blocked, eligible], strategy="simple"
    )

    assert [item.pr_id for item in ordered] == [301, 302]


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
