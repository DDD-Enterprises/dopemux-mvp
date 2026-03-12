from __future__ import annotations

import pytest

from dopemux_pr_merge_specialist import engine
from dopemux_pr_merge_specialist.schema import Finding, FindingSeverity, PRState, PullRequestState, ValidationStatus


def _state(pr_id: int, *, base: str, head: str, pr_class: str, risk: float, diff: int) -> PullRequestState:
    return PullRequestState(
        pr_id=pr_id,
        title=f"PR {pr_id}",
        author="tester",
        state="OPEN",
        base_ref=base,
        head_ref=head,
        ci_status="SUCCESS",
        mergeable="MERGEABLE",
        merge_state_status="CLEAN",
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
