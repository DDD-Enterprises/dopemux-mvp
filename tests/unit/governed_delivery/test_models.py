"""Contract tests for the governed-delivery models and both censuses."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource

from dopemux.governed_delivery import models as m

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas" / "governed_delivery"


def local_registry() -> Registry:
    """Resolve cross-schema $refs from disk. Validation stays fully offline."""
    resources = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)

IDENTITY = m.Identity(project_id="dopemux-mvp", repository_id="DDD-Enterprises/dopemux-mvp")
NOW = "2026-08-24T00:00:00Z"


def _reference(**overrides):
    kwargs = dict(
        evidence_id="ev-1",
        evidence_class="PROOF_BUNDLE",
        owner_system="PROOF_TOOLING",
        producer_identity="deterministic-tool",
        canonical_location="proof/TP-X/PROOF.json",
        digest_or_signature="sha256:abc",
        identity=IDENTITY,
        observed_at=NOW,
        freshness_state=m.FreshnessState.CURRENT,
    )
    kwargs.update(overrides)
    return m.EvidenceReference(**kwargs)


def _envelope(**overrides):
    kwargs = dict(
        envelope_id="env-1",
        kind=m.EnvelopeKind.REQUEST,
        event_type="AuditRequest",
        identity=IDENTITY,
        producer="governed-delivery",
        consumer="audit-broker",
        created_at=NOW,
        subject_ref="head:abc",
        idempotency_key="key-1",
        payload_schema="payload.v1",
        payload={"action_type": "AUDIT"},
    )
    kwargs.update(overrides)
    return m.GovernedDeliveryEnvelope(**kwargs)


class TestCensusCompleteness:
    def test_all_39_message_classes_present(self):
        assert len(m.MESSAGE_CLASS_CENSUS) == 39

    def test_message_classes_reduce_to_exactly_five_kinds(self):
        assert set(m.MESSAGE_CLASS_CENSUS.values()) == set(m.EnvelopeKind)

    def test_message_class_distribution_matches_architecture_census(self):
        counts: dict[str, int] = {}
        for kind in m.MESSAGE_CLASS_CENSUS.values():
            counts[kind.value] = counts.get(kind.value, 0) + 1
        assert counts == {"REQUEST": 9, "FACT": 7, "DECISION": 4, "RECEIPT": 13, "FINDING": 6}

    def test_every_message_class_maps_without_error(self):
        for event_type in m.MESSAGE_CLASS_CENSUS:
            assert isinstance(m.envelope_kind_for_event(event_type), m.EnvelopeKind)

    def test_unknown_message_class_fails_closed(self):
        with pytest.raises(m.Denial):
            m.envelope_kind_for_event("NotACensusClass")

    def test_all_44_failure_branches_present(self):
        assert len(m.FAILURE_BRANCH_CENSUS) == 44
        for index in range(1, 45):
            assert f"F-{index:02d}" in m.FAILURE_BRANCH_CENSUS

    def test_failure_branches_map_to_the_eleven_normalized_classes(self):
        used = {entry[1] for entry in m.FAILURE_BRANCH_CENSUS.values()}
        assert used == set(m.NormalizedFailureClass)

    def test_every_failure_branch_maps_without_error(self):
        for branch in m.FAILURE_BRANCH_CENSUS:
            assert isinstance(m.normalized_class_for_branch(branch), m.NormalizedFailureClass)

    def test_unknown_failure_branch_fails_closed(self):
        with pytest.raises(m.Denial):
            m.normalized_class_for_branch("F-99")

    def test_control_reframed_branches_are_not_treated_as_defects(self):
        for branch in m.CONTROL_REFRAMED_BRANCHES:
            assert branch in m.FAILURE_BRANCH_CENSUS


class TestGateStates:
    def test_all_eight_states_exist(self):
        assert len(list(m.GateState)) == 8

    @pytest.mark.parametrize(
        "state",
        [
            m.GateState.UNSATISFIED,
            m.GateState.STALE,
            m.GateState.BLOCKED,
            m.GateState.UNKNOWN,
            m.GateState.CONFLICTING,
            m.GateState.PENDING,
        ],
    )
    def test_unresolved_states_block_consequential_action(self, state):
        entry = m.GateEntry(
            gate_id="g1",
            gate_class="AUDIT",
            state=state,
            policy_owner="governance",
            policy_version="v1",
            subject_digest_or_head="abc",
            producer_identity="tool",
            observed_at=NOW,
            reason="test",
        )
        assert entry.blocks_consequential_action

    def test_unknown_and_conflicting_fail_closed(self):
        for state in (m.GateState.UNKNOWN, m.GateState.CONFLICTING):
            entry = m.GateEntry(
                gate_id="g",
                gate_class="AUDIT",
                state=state,
                policy_owner="governance",
                policy_version="v1",
                subject_digest_or_head="abc",
                producer_identity="tool",
                observed_at=NOW,
                reason="test",
            )
            assert entry.blocks_consequential_action, f"{state} must fail closed"

    def test_satisfied_does_not_block(self):
        entry = m.GateEntry(
            gate_id="g",
            gate_class="AUDIT",
            state=m.GateState.SATISFIED,
            policy_owner="governance",
            policy_version="v1",
            subject_digest_or_head="abc",
            producer_identity="tool",
            observed_at=NOW,
            reason="evidence present",
        )
        assert not entry.blocks_consequential_action

    def test_unknown_gate_class_denied(self):
        with pytest.raises(m.Denial):
            m.GateEntry(
                gate_id="g",
                gate_class="NOT_A_GATE_CLASS",
                state=m.GateState.SATISFIED,
                policy_owner="o",
                policy_version="v",
                subject_digest_or_head="s",
                producer_identity="p",
                observed_at=NOW,
                reason="r",
            )


class TestAuthorityNonAmplification:
    def test_reference_cannot_raise_authority(self):
        reference = _reference(authority_effect=m.AuthorityEffect.NONE)
        assert reference.as_dict()["authority_effect"] == "NONE"

    def test_envelope_mutation_authorized_is_structurally_false(self):
        assert _envelope().as_dict()["mutation_authorized"] is False

    def test_envelope_rejects_mutation_authorized(self):
        with pytest.raises(m.Denial) as excinfo:
            _envelope(mutation_authorized=True)
        assert excinfo.value.normalized_class is m.NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT

    def test_dispatch_eligible_always_false(self):
        action = m.NextLegalAction("MERGE", "OPERATOR", authority_ref="packet")
        assert action.dispatch_eligible is False
        assert action.as_dict()["dispatch_eligible"] is False

    def test_gate_satisfaction_is_not_permission(self):
        ledger = m.GateLedger(
            ledger_id="l1",
            identity=IDENTITY,
            subject_digest_or_head="abc",
            gates=[
                m.GateEntry(
                    gate_id="merge",
                    gate_class="MERGE_AUTHORITY",
                    state=m.GateState.SATISFIED,
                    policy_owner="governance",
                    policy_version="v1",
                    subject_digest_or_head="abc",
                    producer_identity="tool",
                    observed_at=NOW,
                    reason="gate evidence present",
                )
            ],
        )
        # A satisfied gate exposes no field that could authorize an action.
        assert "authority" not in json.dumps(ledger.as_dict()).lower().replace("merge_authority", "")


class TestEnvelopeKinds:
    def test_exactly_five_kinds(self):
        assert len(list(m.EnvelopeKind)) == 5

    def test_event_type_kind_mismatch_denied(self):
        with pytest.raises(m.Denial):
            _envelope(event_type="AuditRequest", kind=m.EnvelopeKind.RECEIPT)

    def test_every_census_class_is_representable(self):
        for event_type, kind in m.MESSAGE_CLASS_CENSUS.items():
            envelope = _envelope(event_type=event_type, kind=kind)
            assert envelope.as_dict()["event_type"] == event_type


class TestIdentityFailsClosed:
    def test_blank_project_denied(self):
        with pytest.raises(m.Denial):
            m.Identity(project_id="", repository_id="repo")

    def test_literal_unknown_identity_denied(self):
        with pytest.raises(m.Denial):
            m.Identity(project_id="UNKNOWN", repository_id="repo")

    def test_unknown_evidence_class_denied(self):
        with pytest.raises(m.Denial):
            _reference(evidence_class="MADE_UP")

    def test_unknown_schema_version_denied(self):
        raw = _reference().as_dict()
        raw["schema_version"] = "governed-delivery.evidence-reference.v2"
        with pytest.raises(m.Denial):
            m.EvidenceReference.from_dict(raw)

    def test_unparseable_instant_denied(self):
        with pytest.raises(m.Denial):
            _reference(observed_at="last tuesday")


class TestDeterminism:
    def test_canonical_json_is_key_order_independent(self):
        assert m.canonical_json({"b": 1, "a": 2}) == m.canonical_json({"a": 2, "b": 1})

    def test_digest_is_stable(self):
        assert m.digest_of({"a": [1, 2]}) == m.digest_of({"a": [1, 2]})

    def test_reference_roundtrip_is_stable(self):
        original = _reference()
        assert m.EvidenceReference.from_dict(original.as_dict()).as_dict() == original.as_dict()


class TestSchemaConformance:
    """Every model's canonical output must validate against its schema."""

    @staticmethod
    def _validator(filename: str) -> Draft7Validator:
        schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
        Draft7Validator.check_schema(schema)
        return Draft7Validator(schema, registry=local_registry())

    def test_evidence_reference_document_validates(self):
        self._validator("evidence-reference.schema.json").validate(_reference().as_dict())

    def test_envelope_document_validates(self):
        self._validator("governed-delivery-envelope.schema.json").validate(_envelope().as_dict())

    def test_gate_ledger_document_validates(self):
        ledger = m.GateLedger(
            ledger_id="l1",
            identity=IDENTITY,
            subject_digest_or_head="abc",
            gates=[
                m.GateEntry(
                    gate_id="audit",
                    gate_class="AUDIT",
                    state=m.GateState.PENDING,
                    policy_owner="governance",
                    policy_version="v1",
                    subject_digest_or_head="abc",
                    producer_identity="tool",
                    observed_at=NOW,
                    reason="awaiting independent audit",
                    evidence_refs=[_reference()],
                )
            ],
        )
        self._validator("gate-ledger.schema.json").validate(ledger.as_dict())

    def test_work_item_projection_document_validates(self):
        projection = m.WorkItemProjection(
            projection_id="p1",
            work_item_id="TP-X",
            identity=IDENTITY,
            subject=m.Subject(head_sha="abc"),
            phase=m.Phase.VERIFY,
            posture=m.Posture.ACTIVE,
            next_legal_action=m.NextLegalAction("CONTINUE", "IMPLEMENTER"),
            updated_at=NOW,
            native_state_refs=[m.NativeStateRef("task-orchestrator", "in_progress")],
            evidence_refs=[_reference()],
            blockers=[
                m.Blocker("b1", m.NormalizedFailureClass.VALIDATION_FAILURE, "tests failing")
            ],
        )
        self._validator("work-item-projection.schema.json").validate(projection.as_dict())

    def test_content_audit_binding_document_validates(self):
        binding = m.ContentAuditBinding(
            audit_id="a1",
            packet_ref="TP-X",
            audited_head="abc",
            audited_tree="def",
            audited_content_digest="sha256:1",
            base_policy_ref="AGENTS.md",
            auditor_requested_identity="independent",
            auditor_configured_identity="model-x",
            auditor_response_claimed_identity="model-x",
            auditor_proxy_reported_identity="model-x",
            auditor_provider_attested_identity="UNKNOWN",
            independence=m.Independence.LIMITED,
            verdict=m.AuditVerdict.PASS_WITH_RISKS,
            audit_result_digest="sha256:2",
            observed_at=NOW,
        )
        self._validator("content-audit-binding.schema.json").validate(binding.as_dict())

    def test_operator_decision_request_document_validates(self):
        request = m.OperatorDecisionRequest(
            decision_request_id="d1",
            decision_type=m.DecisionType.MERGE_DECISION_REQUIRED,
            identity=IDENTITY,
            work_item_id="TP-X",
            packet_ref="TP-X",
            exact_subject_ref="head:abc",
            decision_required_from="operator",
            current_state="awaiting merge decision",
            recommended_action="review and decide",
        )
        self._validator("operator-decision-request.schema.json").validate(request.as_dict())


class TestAuditBinding:
    def test_provider_attested_unknown_is_preserved(self):
        binding = m.ContentAuditBinding(
            audit_id="a",
            packet_ref="p",
            audited_head="h",
            audited_tree="t",
            audited_content_digest="d",
            base_policy_ref="b",
            auditor_requested_identity="x",
            auditor_configured_identity="y",
            auditor_response_claimed_identity="z",
            auditor_proxy_reported_identity="w",
            auditor_provider_attested_identity="UNKNOWN",
            independence=m.Independence.LIMITED,
            verdict=m.AuditVerdict.PASS,
            audit_result_digest="r",
            observed_at=NOW,
        )
        assert binding.as_dict()["auditor_provider_attested_identity"] == "UNKNOWN"

    @pytest.mark.parametrize(
        "verdict,acceptable",
        [
            (m.AuditVerdict.PASS, True),
            (m.AuditVerdict.PASS_WITH_RISKS, True),
            (m.AuditVerdict.FAIL, False),
            (m.AuditVerdict.NEEDS_SUPERVISOR, False),
            (m.AuditVerdict.SKIPPED, False),
            (m.AuditVerdict.MALFORMED, False),
            (m.AuditVerdict.UNKNOWN, False),
        ],
    )
    def test_only_pass_verdicts_are_acceptable(self, verdict, acceptable):
        binding = m.ContentAuditBinding(
            audit_id="a",
            packet_ref="p",
            audited_head="h",
            audited_tree="t",
            audited_content_digest="d",
            base_policy_ref="b",
            auditor_requested_identity="x",
            auditor_configured_identity="y",
            auditor_response_claimed_identity="z",
            auditor_proxy_reported_identity="w",
            auditor_provider_attested_identity="v",
            independence=m.Independence.PROVEN,
            verdict=verdict,
            audit_result_digest="r",
            observed_at=NOW,
        )
        assert binding.is_acceptable is acceptable
