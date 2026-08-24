"""Freshness, receipt-reuse eligibility and idempotency tests."""

from __future__ import annotations

import pytest

from dopemux.governed_delivery import models as m
from dopemux.governed_delivery.receipts import (
    REUSE_CONDITIONS,
    assess_freshness,
    check_idempotency_batch,
    evaluate_receipt_reuse,
)

IDENTITY = m.Identity(project_id="dopemux-mvp", repository_id="DDD-Enterprises/dopemux-mvp")
NOW = "2026-08-24T00:00:00Z"
LATER = "2026-08-25T00:00:00Z"
EARLIER = "2026-08-23T00:00:00Z"


def reference(**overrides):
    kwargs = dict(
        evidence_id="ev-1",
        evidence_class="VALIDATION_RECEIPT",
        owner_system="PROOF_TOOLING",
        producer_identity="deterministic-tool",
        canonical_location="proof/TP-X/VALIDATION.json",
        digest_or_signature="sha256:abc",
        identity=IDENTITY,
        observed_at=EARLIER,
        freshness_state=m.FreshnessState.CURRENT,
        subject=m.Subject(content_digest="sha256:subject"),
        policy_version="policy-1",
        schema_version_used="schema-1",
        tool_version="tool-1",
        environment_digest="env-1",
    )
    kwargs.update(overrides)
    return m.EvidenceReference(**kwargs)


def reuse(**overrides):
    kwargs = dict(
        candidate=reference(),
        required_subject_digest="sha256:subject",
        as_of=NOW,
        required_policy_version="policy-1",
        required_schema_version="schema-1",
        required_tool_version="tool-1",
        trusted_producers=["deterministic-tool"],
    )
    kwargs.update(overrides)
    return evaluate_receipt_reuse(**kwargs)


class TestFreshness:
    def test_current_reference_is_current(self):
        assert assess_freshness(reference(), as_of=NOW).state is m.FreshnessState.CURRENT

    def test_tombstone_takes_precedence(self):
        assessment = assess_freshness(reference(tombstone=True), as_of=NOW)
        assert assessment.state is m.FreshnessState.TOMBSTONED

    def test_supersession_detected(self):
        assessment = assess_freshness(reference(), as_of=NOW, superseded_ids=["ev-1"])
        assert assessment.state is m.FreshnessState.SUPERSEDED

    def test_expired_when_valid_until_has_passed(self):
        assessment = assess_freshness(reference(valid_until=EARLIER), as_of=NOW)
        assert assessment.state is m.FreshnessState.EXPIRED

    def test_not_expired_before_valid_until(self):
        assessment = assess_freshness(reference(valid_until=LATER), as_of=NOW)
        assert assessment.state is m.FreshnessState.CURRENT

    def test_unknown_state_stays_unknown(self):
        assessment = assess_freshness(
            reference(freshness_state=m.FreshnessState.UNKNOWN), as_of=NOW
        )
        assert assessment.state is m.FreshnessState.UNKNOWN

    def test_producer_declared_stale_is_preserved(self):
        assessment = assess_freshness(reference(freshness_state=m.FreshnessState.STALE), as_of=NOW)
        assert assessment.state is m.FreshnessState.STALE

    def test_every_assessment_carries_a_reason(self):
        assert assess_freshness(reference(), as_of=NOW).reason

    def test_unparseable_as_of_denied(self):
        with pytest.raises(m.Denial):
            assess_freshness(reference(), as_of="whenever")

    def test_freshness_is_deterministic(self):
        first = assess_freshness(reference(), as_of=NOW).as_dict()
        second = assess_freshness(reference(), as_of=NOW).as_dict()
        assert first == second


class TestReceiptReuse:
    def test_all_ten_conditions_declared(self):
        assert len(REUSE_CONDITIONS) == 10

    def test_eligible_when_every_condition_holds(self):
        decision = reuse()
        assert decision.eligible, decision.failed_conditions

    def test_decision_enumerates_all_conditions(self):
        assert set(reuse().conditions) == set(REUSE_CONDITIONS)

    def test_changed_subject_digest_blocks_reuse(self):
        decision = reuse(required_subject_digest="sha256:different")
        assert not decision.eligible
        assert "same_subject_digest" in decision.failed_conditions

    def test_changed_policy_blocks_reuse(self):
        decision = reuse(required_policy_version="policy-2")
        assert not decision.eligible
        assert "same_policy_digest" in decision.failed_conditions

    def test_changed_schema_blocks_reuse(self):
        decision = reuse(required_schema_version="schema-2")
        assert not decision.eligible

    def test_changed_tool_version_blocks_reuse(self):
        decision = reuse(required_tool_version="tool-2")
        assert not decision.eligible

    def test_untrusted_producer_blocks_reuse(self):
        decision = reuse(trusted_producers=["someone-else"])
        assert not decision.eligible
        assert "producer_identity_still_trusted" in decision.failed_conditions

    def test_environment_mismatch_blocks_reuse_when_environment_matters(self):
        decision = reuse(environment_matters=True, required_environment_digest="env-2")
        assert not decision.eligible

    def test_environment_ignored_when_it_does_not_matter(self):
        assert reuse(environment_matters=False).eligible

    def test_expired_evidence_blocks_reuse(self):
        decision = reuse(candidate=reference(valid_until=EARLIER))
        assert not decision.eligible
        assert "not_expired_when_freshness_is_semantic" in decision.failed_conditions

    def test_superseded_evidence_blocks_reuse(self):
        decision = reuse(superseded_ids=["ev-1"])
        assert not decision.eligible
        assert "not_superseded_or_tombstoned" in decision.failed_conditions

    def test_tombstoned_evidence_blocks_reuse(self):
        decision = reuse(candidate=reference(tombstone=True))
        assert not decision.eligible

    def test_distinct_consumer_authority_blocks_reuse(self):
        decision = reuse(consumer_adds_distinct_authority=True)
        assert not decision.eligible
        assert "consumer_adds_no_distinct_authority_or_live_state_check" in decision.failed_conditions

    def test_changed_input_digests_block_reuse(self):
        decision = reuse(required_input_digests=["a"], candidate_input_digests=["b"])
        assert not decision.eligible

    def test_matching_path_alone_is_not_sufficient(self):
        """Same canonical_location, different subject: reuse must still fail."""
        decision = reuse(
            candidate=reference(subject=m.Subject(content_digest="sha256:moved-on")),
        )
        assert not decision.eligible

    def test_reuse_decision_is_deterministic(self):
        assert reuse().as_dict() == reuse().as_dict()


class TestIdempotency:
    @staticmethod
    def envelope(key: str, payload: dict):
        return m.GovernedDeliveryEnvelope(
            envelope_id=f"env-{key}",
            kind=m.EnvelopeKind.RECEIPT,
            event_type="ValidationResult",
            identity=IDENTITY,
            producer="tool",
            consumer="governed-delivery",
            created_at=NOW,
            subject_ref="head:abc",
            idempotency_key=key,
            payload_schema="payload.v1",
            payload=payload,
        )

    def test_duplicate_key_with_identical_payload_accepted(self):
        batch = [self.envelope("k1", {"a": 1}), self.envelope("k1", {"a": 1})]
        assert len(check_idempotency_batch(batch)) == 1

    def test_duplicate_key_with_different_payload_denied(self):
        batch = [self.envelope("k1", {"a": 1}), self.envelope("k1", {"a": 2})]
        with pytest.raises(m.Denial):
            check_idempotency_batch(batch)

    def test_distinct_keys_accepted(self):
        batch = [self.envelope("k1", {"a": 1}), self.envelope("k2", {"a": 2})]
        assert len(check_idempotency_batch(batch)) == 2

    def test_empty_batch_is_fine(self):
        assert check_idempotency_batch([]) == {}
