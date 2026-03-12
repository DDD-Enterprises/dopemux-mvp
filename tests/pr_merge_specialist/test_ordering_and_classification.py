from __future__ import annotations

from dopemux_pr_merge_specialist import cli
from dopemux_pr_merge_specialist.schema import PRState


def _state(
    pr_id: int,
    *,
    base: str,
    head: str,
    pr_class: str,
    risk: float,
    diff: int,
) -> PRState:
    return PRState(
        pr_id=pr_id,
        title=f"PR {pr_id}",
        author="tester",
        state="OPEN",
        base_ref=base,
        head_ref=head,
        ci_status="SUCCESS",
        mergeable="MERGEABLE",
        merge_state_status="CLEAN",
        review_decision="",
        updated_at="2026-03-12T00:00:00Z",
        additions=diff,
        deletions=0,
        changed_files=1,
        unresolved_threads=0,
        active_unresolved_threads=0,
        outdated_unresolved_threads=0,
        pr_class=pr_class,  # type: ignore[arg-type]
        risk_score=risk,
    )


def test_classify_pr_states():
    assert cli._classify_pr(
        ci_status="SUCCESS",
        has_conflicts=False,
        active_unresolved_threads=0,
        is_draft=False,
    ) == "READY"
    assert cli._classify_pr(
        ci_status="FAILURE",
        has_conflicts=False,
        active_unresolved_threads=0,
        is_draft=False,
    ) == "CI_ONLY"
    assert cli._classify_pr(
        ci_status="SUCCESS",
        has_conflicts=True,
        active_unresolved_threads=0,
        is_draft=False,
    ) == "CONFLICTS_ONLY"
    assert cli._classify_pr(
        ci_status="SUCCESS",
        has_conflicts=False,
        active_unresolved_threads=2,
        is_draft=False,
    ) == "COMMENTS_ONLY"


def test_hybrid_ordering_respects_dependency_edges():
    p1 = _state(101, base="main", head="feature/a", pr_class="READY", risk=5.0, diff=10)
    p2 = _state(102, base="feature/a", head="feature/b", pr_class="READY", risk=1.0, diff=10)
    p3 = _state(103, base="main", head="feature/c", pr_class="READY", risk=3.0, diff=10)
    p4 = _state(104, base="main", head="feature/d", pr_class="READY", risk=2.0, diff=10)

    ordered, layers, edges, cycle = cli._sort_states([p1, p2, p3, p4], strategy="hybrid")

    assert cycle is False
    assert edges[101] == [102]
    order_ids = [x.pr_id for x in ordered]
    assert order_ids.index(101) < order_ids.index(102)
    assert layers


def test_simple_ordering_for_small_queues():
    p1 = _state(201, base="main", head="h1", pr_class="MIXED", risk=20.0, diff=100)
    p2 = _state(202, base="main", head="h2", pr_class="READY", risk=1.0, diff=5)
    p3 = _state(203, base="main", head="h3", pr_class="CI_ONLY", risk=5.0, diff=10)

    ordered, layers, edges, cycle = cli._sort_states([p1, p2, p3], strategy="hybrid")

    assert [x.pr_id for x in ordered] == [202, 203, 201]
    assert len(layers) == 1
    assert edges == {}
    assert cycle is False


def test_risk_score_penalizes_active_threads_and_failures():
    low = cli._risk_score(
        pr_class="READY",
        additions=10,
        deletions=0,
        changed_files=1,
        active_threads=0,
        outdated_threads=0,
        ci_status="SUCCESS",
        merge_state_status="CLEAN",
    )
    high = cli._risk_score(
        pr_class="MIXED",
        additions=10,
        deletions=0,
        changed_files=1,
        active_threads=2,
        outdated_threads=0,
        ci_status="FAILURE",
        merge_state_status="BEHIND",
    )
    assert high > low
