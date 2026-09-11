"""Tests for dopemux.governed_execution.review_economy.decide."""
from __future__ import annotations

import builtins
import subprocess

import pytest

from dopemux.governed_execution.review_economy.decide import (
    TRIGGERS,
    ReviewDecision,
    ReviewPolicy,
    ReviewRequest,
    decide_review,
)
from dopemux.governed_execution.review_economy.keys import (
    MODEL_REVIEWER_CLASSES,
    REVIEWER_CLASSES,
    ReceiptRef,
    ReviewReceiptKey,
    ReviewReceiptRecord,
)

HEAD_A = "a" * 40
HEAD_B = "b" * 40
POLICY_DIGEST_A = "1" * 64
POLICY_DIGEST_B = "2" * 64
RECEIPT_DIGEST_A = "3" * 64
RECEIPT_DIGEST_B = "4" * 64

NOW = "2026-06-01T00:00:00Z"
PAST = "2026-01-01T00:00:00Z"
FUTURE = "2026-12-01T00:00:00Z"

QUALIFYING_VERDICTS = frozenset({"PASS", "PASS_WITH_RISKS"})


def make_key(
    review_type: str = "CODE_REVIEW",
    head_sha: str = HEAD_A,
    policy_digest: str = POLICY_DIGEST_A,
    reviewer_class: str = "MODEL_STANDARD",
) -> ReviewReceiptKey:
    return ReviewReceiptKey(
        review_type=review_type,
        head_sha=head_sha,
        policy_digest=policy_digest,
        reviewer_class=reviewer_class,
    )


def make_record(
    key: ReviewReceiptKey,
    verdict: str = "PASS",
    issued_at: str = PAST,
    expires_at: str = FUTURE,
    invalidated: bool = False,
    subject_head: str | None = None,
    receipt_digest: str = RECEIPT_DIGEST_A,
) -> ReviewReceiptRecord:
    return ReviewReceiptRecord(
        key=key,
        verdict=verdict,
        issued_at=issued_at,
        expires_at=expires_at,
        invalidated=invalidated,
        subject_head=subject_head if subject_head is not None else key.head_sha,
        receipt_ref=ReceiptRef(path="proof/w06/receipt.json", sha256=receipt_digest),
    )


def make_policy(
    qualifying_verdicts: frozenset[str] = QUALIFYING_VERDICTS,
    premium_classes: frozenset[str] = frozenset({"MODEL_PREMIUM"}),
    policy_digest: str = POLICY_DIGEST_A,
) -> ReviewPolicy:
    return ReviewPolicy(
        policy_digest=policy_digest,
        qualifying_verdicts=qualifying_verdicts,
        premium_classes=premium_classes,
    )


# -- ReviewRequest: trigger closed set, the excluded GitHub-draft trigger ----


@pytest.mark.parametrize("trigger", sorted(TRIGGERS))
def test_every_trigger_accepted(trigger: str):
    ReviewRequest(key=make_key(), trigger=trigger, explicit_rerun_authorized=False)


def test_unknown_trigger_string_rejected():
    with pytest.raises(ValueError):
        ReviewRequest(key=make_key(), trigger="NOT_A_TRIGGER", explicit_rerun_authorized=False)


def test_github_draft_derived_trigger_is_not_a_member_of_triggers():
    assert "DRAFT_TO_READY" not in TRIGGERS


def test_constructing_request_with_excluded_trigger_raises():
    with pytest.raises(ValueError):
        ReviewRequest(
            key=make_key(),
            trigger="DRAFT_TO_READY",
            explicit_rerun_authorized=False,
        )


def test_explicit_rerun_authorized_must_be_bool():
    with pytest.raises(ValueError):
        ReviewRequest(key=make_key(), trigger="HEAD_MOVED", explicit_rerun_authorized="yes")  # type: ignore[arg-type]


# -- ReviewPolicy --------------------------------------------------------------


def test_policy_accepts_well_formed():
    make_policy()


def test_policy_rejects_bad_policy_digest():
    with pytest.raises(ValueError):
        make_policy(policy_digest="not-hex")


def test_policy_accepts_empty_qualifying_verdicts_at_construction():
    # Empty qualifying_verdicts is well-formed; decide_review, not the
    # constructor, is what fails closed to BLOCKED on it.
    make_policy(qualifying_verdicts=frozenset())


def test_policy_rejects_premium_classes_outside_closed_set():
    with pytest.raises(ValueError):
        make_policy(premium_classes=frozenset({"NOT_A_CLASS"}))


# -- REUSE happy path ------------------------------------------------------------


def test_reuse_happy_path_model_premium_avoids_one_call():
    key = make_key(reviewer_class="MODEL_PREMIUM")
    record = make_record(key)
    request = ReviewRequest(key=key, trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [record], NOW, make_policy())
    assert decision.decision == "REUSE"
    assert decision.model_calls_avoided == 1
    assert decision.reused_receipt_ref == record.receipt_ref
    assert decision.authority == "NONE"
    assert decision.is_execution_authority is False


def test_reuse_happy_path_deterministic_avoids_zero_calls():
    key = make_key(reviewer_class="DETERMINISTIC")
    record = make_record(key)
    request = ReviewRequest(key=key, trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [record], NOW, make_policy())
    assert decision.decision == "REUSE"
    assert decision.model_calls_avoided == 0


def test_model_calls_avoided_by_fixtures_sums_to_expected_total():
    # Four REUSE fixtures, one per reviewer class: MODEL_PREMIUM and
    # MODEL_STANDARD each avoid one call, DETERMINISTIC and HUMAN avoid zero.
    total = 0
    for reviewer_class in sorted(REVIEWER_CLASSES):
        key = make_key(reviewer_class=reviewer_class)
        record = make_record(key)
        request = ReviewRequest(
            key=key, trigger="HEAD_MOVED", explicit_rerun_authorized=False
        )
        decision = decide_review(request, [record], NOW, make_policy())
        assert decision.decision == "REUSE"
        total += decision.model_calls_avoided
    assert total == 2
    assert total == len(MODEL_REVIEWER_CLASSES)


# -- NEW_CALL: the five invalidation reasons -------------------------------------


def test_new_call_reason_head_moved():
    prior = make_record(make_key(head_sha=HEAD_A))
    request = ReviewRequest(
        key=make_key(head_sha=HEAD_B), trigger="HEAD_MOVED", explicit_rerun_authorized=False
    )
    decision = decide_review(request, [prior], NOW, make_policy())
    assert decision.decision == "NEW_CALL"
    assert decision.reasons == ("HEAD_MOVED",)
    assert decision.model_calls_avoided == 0


def test_new_call_reason_policy_changed():
    prior = make_record(make_key(policy_digest=POLICY_DIGEST_A))
    request = ReviewRequest(
        key=make_key(policy_digest=POLICY_DIGEST_B),
        trigger="POLICY_CHANGED",
        explicit_rerun_authorized=False,
    )
    policy = make_policy(policy_digest=POLICY_DIGEST_B)
    decision = decide_review(request, [prior], NOW, policy)
    assert decision.decision == "NEW_CALL"
    assert decision.reasons == ("POLICY_CHANGED",)


def test_new_call_reason_receipt_expired():
    key = make_key()
    prior = make_record(key, expires_at="2026-01-02T00:00:00Z")
    request = ReviewRequest(key=key, trigger="RECEIPT_EXPIRED", explicit_rerun_authorized=False)
    decision = decide_review(request, [prior], NOW, make_policy())
    assert decision.decision == "NEW_CALL"
    assert decision.reasons == ("RECEIPT_EXPIRED",)


def test_new_call_reason_reviewer_invalidated():
    key = make_key()
    prior = make_record(key, invalidated=True)
    request = ReviewRequest(
        key=key, trigger="REVIEWER_INVALIDATED", explicit_rerun_authorized=False
    )
    decision = decide_review(request, [prior], NOW, make_policy())
    assert decision.decision == "NEW_CALL"
    assert decision.reasons == ("REVIEWER_INVALIDATED",)


def test_new_call_reason_explicit_rerun():
    key = make_key()
    prior = make_record(key)
    request = ReviewRequest(key=key, trigger="EXPLICIT_RERUN", explicit_rerun_authorized=True)
    decision = decide_review(request, [prior], NOW, make_policy())
    assert decision.decision == "NEW_CALL"
    assert decision.reasons == ("EXPLICIT_RERUN",)
    assert decision.model_calls_avoided == 0


def test_new_call_reason_no_prior_receipt():
    request = ReviewRequest(key=make_key(), trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [], NOW, make_policy())
    assert decision.decision == "NEW_CALL"
    assert decision.reasons == ("NO_PRIOR_RECEIPT",)


def test_new_call_reason_verdict_not_qualifying():
    key = make_key()
    prior = make_record(key, verdict="FAIL")
    request = ReviewRequest(key=key, trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [prior], NOW, make_policy())
    assert decision.decision == "NEW_CALL"
    assert decision.reasons == ("VERDICT_NOT_QUALIFYING",)


# -- BLOCKED: missing key / malformed record / empty qualifying set -------------


def test_blocked_missing_key():
    request = ReviewRequest(key=None, trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [], NOW, make_policy())
    assert decision.decision == "BLOCKED"
    assert decision.reasons == ("MISSING_KEY",)
    assert decision.reused_receipt_ref is None
    assert decision.model_calls_avoided == 0


def test_blocked_malformed_record():
    request = ReviewRequest(key=make_key(), trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, ["not-a-record"], NOW, make_policy())  # type: ignore[list-item]
    assert decision.decision == "BLOCKED"
    assert decision.reasons == ("MALFORMED_RECORD",)


def test_blocked_empty_qualifying_verdicts():
    request = ReviewRequest(key=make_key(), trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    policy = make_policy(qualifying_verdicts=frozenset())
    decision = decide_review(request, [], NOW, policy)
    assert decision.decision == "BLOCKED"
    assert decision.reasons == ("EMPTY_QUALIFYING_VERDICTS",)


def test_blocked_malformed_now():
    request = ReviewRequest(key=make_key(), trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [], "not-a-time", make_policy())
    assert decision.decision == "BLOCKED"
    assert decision.reasons == ("MALFORMED_NOW",)


def test_blocked_malformed_policy():
    request = ReviewRequest(key=make_key(), trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [], NOW, "not-a-policy")  # type: ignore[arg-type]
    assert decision.decision == "BLOCKED"
    assert decision.reasons == ("MALFORMED_POLICY",)


def test_blocked_never_reuse_even_with_qualifying_record_present():
    key = make_key()
    record = make_record(key)
    request = ReviewRequest(key=None, trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [record], NOW, make_policy())
    assert decision.decision == "BLOCKED"


# -- determinism: same input -> equal output -------------------------------------


def test_decide_review_is_deterministic():
    key = make_key()
    record = make_record(key)
    request = ReviewRequest(key=key, trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    policy = make_policy()
    first = decide_review(request, [record], NOW, policy)
    second = decide_review(request, [record], NOW, policy)
    assert first == second


# -- purity: no filesystem or process access -------------------------------------


def test_decide_review_never_opens_a_file(monkeypatch: pytest.MonkeyPatch):
    def _forbidden_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("decide_review must never call open()")

    monkeypatch.setattr(builtins, "open", _forbidden_open)
    key = make_key()
    record = make_record(key)
    request = ReviewRequest(key=key, trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [record], NOW, make_policy())
    assert decision.decision == "REUSE"


def test_decide_review_never_spawns_a_process(monkeypatch: pytest.MonkeyPatch):
    def _forbidden_run(*args: object, **kwargs: object) -> None:
        raise AssertionError("decide_review must never call subprocess.run")

    monkeypatch.setattr(subprocess, "run", _forbidden_run)
    key = make_key()
    record = make_record(key)
    request = ReviewRequest(key=key, trigger="HEAD_MOVED", explicit_rerun_authorized=False)
    decision = decide_review(request, [record], NOW, make_policy())
    assert decision.decision == "REUSE"


# -- ReviewDecision construction guards -------------------------------------------


def test_review_decision_rejects_unknown_decision_value():
    with pytest.raises(ValueError):
        ReviewDecision(
            decision="MAYBE",
            reasons=("X",),
            reused_receipt_ref=None,
            model_calls_avoided=0,
        )


def test_review_decision_rejects_empty_reasons():
    with pytest.raises(ValueError):
        ReviewDecision(
            decision="NEW_CALL",
            reasons=(),
            reused_receipt_ref=None,
            model_calls_avoided=0,
        )


def test_review_decision_rejects_negative_model_calls_avoided():
    with pytest.raises(ValueError):
        ReviewDecision(
            decision="REUSE",
            reasons=("X",),
            reused_receipt_ref=None,
            model_calls_avoided=-1,
        )


def test_review_decision_authority_is_const_none_and_not_a_constructor_arg():
    decision = ReviewDecision(
        decision="NEW_CALL",
        reasons=("X",),
        reused_receipt_ref=None,
        model_calls_avoided=0,
    )
    assert decision.authority == "NONE"
    assert decision.is_execution_authority is False


# -- I20 property: an unexpired, non-invalidated, qualifying record with an ------
# equal key can never be answered NEW_CALL unless explicit_rerun_authorized. ----


def _noise_records(review_type: str, reviewer_class: str) -> list[ReviewReceiptRecord]:
    same_key_expired = make_record(
        make_key(review_type=review_type, reviewer_class=reviewer_class),
        expires_at="2026-01-02T00:00:00Z",
        receipt_digest=RECEIPT_DIGEST_B,
    )
    same_key_invalidated = make_record(
        make_key(review_type=review_type, reviewer_class=reviewer_class),
        invalidated=True,
        receipt_digest=RECEIPT_DIGEST_B,
    )
    other_head = make_record(
        make_key(review_type=review_type, reviewer_class=reviewer_class, head_sha=HEAD_B),
        receipt_digest=RECEIPT_DIGEST_B,
    )
    other_policy = make_record(
        make_key(
            review_type=review_type,
            reviewer_class=reviewer_class,
            policy_digest=POLICY_DIGEST_B,
        ),
        receipt_digest=RECEIPT_DIGEST_B,
    )
    non_qualifying_verdict = make_record(
        make_key(review_type=review_type, reviewer_class=reviewer_class),
        verdict="FAIL",
        receipt_digest=RECEIPT_DIGEST_B,
    )
    return [
        [],
        [same_key_expired],
        [same_key_invalidated],
        [other_head],
        [other_policy],
        [non_qualifying_verdict],
    ]


def test_i20_new_call_impossible_for_qualifying_unexpired_receipt_unless_rerun():
    policy = make_policy()
    for reviewer_class in sorted(REVIEWER_CLASSES):
        for verdict in sorted(QUALIFYING_VERDICTS):
            for review_type in ("CODE_REVIEW", "SECURITY_REVIEW"):
                key = make_key(review_type=review_type, reviewer_class=reviewer_class)
                qualifying = make_record(key, verdict=verdict, receipt_digest=RECEIPT_DIGEST_A)
                for noise in _noise_records(review_type, reviewer_class):
                    for position in ("front", "back"):
                        existing = (
                            [qualifying] + noise
                            if position == "front"
                            else noise + [qualifying]
                        )
                        for trigger in sorted(TRIGGERS):
                            for rerun in (False, True):
                                request = ReviewRequest(
                                    key=key,
                                    trigger=trigger,
                                    explicit_rerun_authorized=rerun,
                                )
                                decision = decide_review(request, existing, NOW, policy)
                                assert decision.decision != "BLOCKED", (
                                    reviewer_class,
                                    verdict,
                                    review_type,
                                    noise,
                                    position,
                                    trigger,
                                    rerun,
                                )
                                if rerun:
                                    assert decision.decision == "NEW_CALL"
                                    assert decision.reasons == ("EXPLICIT_RERUN",)
                                else:
                                    assert decision.decision == "REUSE", (
                                        reviewer_class,
                                        verdict,
                                        review_type,
                                        noise,
                                        position,
                                        trigger,
                                    )
                                    assert decision.reused_receipt_ref == qualifying.receipt_ref
                                    expected_avoided = (
                                        1 if reviewer_class in MODEL_REVIEWER_CLASSES else 0
                                    )
                                    assert decision.model_calls_avoided == expected_avoided
