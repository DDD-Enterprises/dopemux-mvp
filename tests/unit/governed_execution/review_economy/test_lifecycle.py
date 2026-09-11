"""Tests for dopemux.governed_execution.review_economy.lifecycle."""
from __future__ import annotations

import itertools

import pytest

from dopemux.governed_execution.review_economy.lifecycle import (
    EVENTS,
    FinalAuditAlreadyConsumed,
    IllegalStage,
    LifecycleStage,
    advance,
)

LEGAL_EDGES: dict[tuple[LifecycleStage, str], LifecycleStage] = {
    (LifecycleStage.IMPLEMENT, "VALIDATION_STARTED"): LifecycleStage.VALIDATE,
    (LifecycleStage.VALIDATE, "PR_OPENED"): LifecycleStage.PR,
    (LifecycleStage.PR, "CI_REVIEWS_STARTED"): LifecycleStage.CI_REVIEWS,
    (LifecycleStage.CI_REVIEWS, "REPAIR_NEEDED"): LifecycleStage.REPAIR,
    (LifecycleStage.CI_REVIEWS, "SETTLEMENT_REACHED"): LifecycleStage.REVIEW_SETTLED,
    (LifecycleStage.REPAIR, "REPAIR_COMPLETE"): LifecycleStage.VALIDATE,
    (LifecycleStage.REVIEW_SETTLED, "FREEZE_REACHED"): LifecycleStage.FREEZE,
    (LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED"): LifecycleStage.FINAL_AUDIT,
    (LifecycleStage.FINAL_AUDIT, "FINAL_AUDIT_PASSED"): LifecycleStage.FINALITY,
    (LifecycleStage.FINAL_AUDIT, "FINAL_AUDIT_FAILED"): LifecycleStage.REPAIR,
}

FREEZE_REF_1 = "freeze-0001"
FREEZE_REF_2 = "freeze-0002"


def test_lifecycle_stage_fixed_order():
    assert [stage.value for stage in LifecycleStage] == [
        "IMPLEMENT",
        "VALIDATE",
        "PR",
        "CI_REVIEWS",
        "REPAIR",
        "REVIEW_SETTLED",
        "FREEZE",
        "FINAL_AUDIT",
        "FINALITY",
    ]


# -- every legal transition -------------------------------------------------------


@pytest.mark.parametrize("edge", sorted(LEGAL_EDGES.items(), key=lambda item: (item[0][0].value, item[0][1])))
def test_every_legal_transition(edge: tuple[tuple[LifecycleStage, str], LifecycleStage]):
    (stage, event), expected = edge
    freeze_ref = FREEZE_REF_1 if expected is LifecycleStage.FINAL_AUDIT else FREEZE_REF_1
    new_stage, new_seen = advance(stage, event, freeze_ref, frozenset())
    assert new_stage is expected


def test_final_audit_entry_records_freeze_ref_in_seen():
    new_stage, new_seen = advance(
        LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", FREEZE_REF_1, frozenset()
    )
    assert new_stage is LifecycleStage.FINAL_AUDIT
    assert new_seen == frozenset({FREEZE_REF_1})


def test_non_final_audit_transitions_leave_seen_unchanged():
    seen = frozenset({FREEZE_REF_1})
    new_stage, new_seen = advance(
        LifecycleStage.IMPLEMENT, "VALIDATION_STARTED", FREEZE_REF_2, seen
    )
    assert new_stage is LifecycleStage.VALIDATE
    assert new_seen == seen


# -- every illegal pair raises (exhaustive over the enum product) -----------------


def test_every_illegal_stage_event_pair_raises():
    checked = 0
    for stage, event in itertools.product(list(LifecycleStage), sorted(EVENTS)):
        if (stage, event) in LEGAL_EDGES:
            continue
        with pytest.raises(IllegalStage):
            advance(stage, event, FREEZE_REF_1, frozenset())
        checked += 1
    # 9 stages * 10 events = 90 pairs, 10 of which are legal.
    assert checked == 9 * 10 - 10


def test_unknown_event_string_raises_illegal_stage():
    with pytest.raises(IllegalStage):
        advance(LifecycleStage.IMPLEMENT, "NOT_AN_EVENT", FREEZE_REF_1, frozenset())


def test_unknown_stage_string_raises_illegal_stage():
    with pytest.raises(IllegalStage):
        advance("NOT_A_STAGE", "VALIDATION_STARTED", FREEZE_REF_1, frozenset())


def test_stage_as_string_value_is_accepted():
    new_stage, _ = advance("IMPLEMENT", "VALIDATION_STARTED", FREEZE_REF_1, frozenset())
    assert new_stage is LifecycleStage.VALIDATE


def test_malformed_seen_final_audits_raises_illegal_stage():
    with pytest.raises(IllegalStage):
        advance(
            LifecycleStage.IMPLEMENT,
            "VALIDATION_STARTED",
            FREEZE_REF_1,
            {"not", "a", "frozenset"},  # plain set, not frozenset
        )


def test_final_audit_entry_with_non_string_freeze_ref_raises_illegal_stage():
    with pytest.raises(IllegalStage):
        advance(LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", None, frozenset())


def test_final_audit_entry_with_empty_freeze_ref_raises_illegal_stage():
    with pytest.raises(IllegalStage):
        advance(LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", "", frozenset())


# -- FINAL_AUDIT at most once per freeze -------------------------------------------


def test_final_audit_twice_for_one_freeze_ref_raises():
    _, seen = advance(LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", FREEZE_REF_1, frozenset())
    with pytest.raises(FinalAuditAlreadyConsumed):
        advance(LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", FREEZE_REF_1, seen)


def test_final_audit_allowed_for_a_different_freeze_ref():
    _, seen = advance(LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", FREEZE_REF_1, frozenset())
    new_stage, new_seen = advance(
        LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", FREEZE_REF_2, seen
    )
    assert new_stage is LifecycleStage.FINAL_AUDIT
    assert new_seen == frozenset({FREEZE_REF_1, FREEZE_REF_2})


# -- REPAIR after FINAL_AUDIT allowed once, then requires a new freeze_ref --------


def test_repair_after_final_audit_allowed_once_then_requires_new_freeze_ref():
    # Enter FINAL_AUDIT for freeze 1.
    stage, seen = advance(LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", FREEZE_REF_1, frozenset())
    assert stage is LifecycleStage.FINAL_AUDIT

    # Audit fails: FINAL_AUDIT -> REPAIR, allowed once.
    stage, seen = advance(stage, "FINAL_AUDIT_FAILED", FREEZE_REF_1, seen)
    assert stage is LifecycleStage.REPAIR

    # Repair completes, revalidate, re-settle, re-freeze under the SAME
    # freeze_ref: re-entering FINAL_AUDIT for that freeze_ref is refused.
    stage, seen = advance(stage, "REPAIR_COMPLETE", FREEZE_REF_1, seen)
    assert stage is LifecycleStage.VALIDATE
    stage, seen = advance(stage, "PR_OPENED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "CI_REVIEWS_STARTED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "SETTLEMENT_REACHED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "FREEZE_REACHED", FREEZE_REF_1, seen)
    assert stage is LifecycleStage.FREEZE
    with pytest.raises(FinalAuditAlreadyConsumed):
        advance(stage, "FINAL_AUDIT_STARTED", FREEZE_REF_1, seen)

    # A fresh freeze_ref (a new FreezeReceipt) legally enters FINAL_AUDIT.
    stage, seen = advance(stage, "FINAL_AUDIT_STARTED", FREEZE_REF_2, seen)
    assert stage is LifecycleStage.FINAL_AUDIT
    assert seen == frozenset({FREEZE_REF_1, FREEZE_REF_2})


def test_final_audit_passed_reaches_finality():
    stage, seen = advance(LifecycleStage.FREEZE, "FINAL_AUDIT_STARTED", FREEZE_REF_1, frozenset())
    stage, seen = advance(stage, "FINAL_AUDIT_PASSED", FREEZE_REF_1, seen)
    assert stage is LifecycleStage.FINALITY


def test_finality_is_terminal_no_legal_outgoing_edge():
    for event in sorted(EVENTS):
        with pytest.raises(IllegalStage):
            advance(LifecycleStage.FINALITY, event, FREEZE_REF_1, frozenset())


def test_full_happy_path_implement_to_finality():
    stage: LifecycleStage | str = LifecycleStage.IMPLEMENT
    seen: frozenset[str] = frozenset()
    stage, seen = advance(stage, "VALIDATION_STARTED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "PR_OPENED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "CI_REVIEWS_STARTED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "SETTLEMENT_REACHED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "FREEZE_REACHED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "FINAL_AUDIT_STARTED", FREEZE_REF_1, seen)
    stage, seen = advance(stage, "FINAL_AUDIT_PASSED", FREEZE_REF_1, seen)
    assert stage is LifecycleStage.FINALITY
