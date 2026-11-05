"""Seven-contract runtime/JSON-Schema conformance corpus for governed-delivery G0."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource

from dopemux.governed_delivery import equivalence as eq
from dopemux.governed_delivery import models as m
from dopemux.governed_delivery import snapshot as s

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "schemas" / "governed_delivery"
PACKET = "TP-DMX-GOV-DELIVERY-EVIDENCE-SPINE-001"
NOW = "2026-08-24T00:00:00Z"
HEAD = "a" * 40
TREE = "b" * 40
BASE = "c" * 40
CONTENT = "sha256:" + "1" * 64
PACKET_DIGEST = "sha256:" + "2" * 64
POLICY_DIGEST = "sha256:" + "3" * 64
AUDIT_DIGEST = "sha256:" + "4" * 64
IDENTITY = m.Identity(
    project_id="dopemux-mvp",
    repository_id="DDD-Enterprises/dopemux-mvp",
    worktree_id="wt-r2-conformance",
    packet_id=PACKET,
)


def registry() -> Registry:
    resources = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def validator(filename: str) -> Draft7Validator:
    schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema, registry=registry())


def evidence() -> m.EvidenceReference:
    return m.EvidenceReference(
        evidence_id="ev-r2",
        evidence_class="AUDIT_RESULT",
        owner_system="embedded-audit",
        producer_identity="independent-auditor",
        canonical_location="artifact://embedded-audit/PROOF.json",
        digest_or_signature=AUDIT_DIGEST,
        identity=IDENTITY,
        subject=m.Subject(head_sha=HEAD, tree_sha=TREE, content_digest=CONTENT),
        observed_at=NOW,
        freshness_state=m.FreshnessState.CURRENT,
    )


def binding() -> m.ContentAuditBinding:
    return m.ContentAuditBinding(
        audit_id="audit-r2",
        packet_ref=PACKET,
        packet_digest=PACKET_DIGEST,
        policy_digest=POLICY_DIGEST,
        audited_head=HEAD,
        audited_tree=TREE,
        audited_content_digest=CONTENT,
        included_paths_digest="sha256:" + "5" * 64,
        base_policy_ref="AGENTS.md",
        auditor_requested_identity="claude-code-cli/opus",
        auditor_configured_identity="claude-code-cli/opus",
        auditor_response_claimed_identity="claude-opus",
        auditor_proxy_reported_identity="direct-cli",
        auditor_provider_attested_identity="UNKNOWN",
        independence=m.Independence.LIMITED,
        verdict=m.AuditVerdict.PASS,
        audit_result_digest=AUDIT_DIGEST,
        observed_at=NOW,
    )


def gate(gate_class: str) -> m.GateEntry:
    return m.GateEntry(
        gate_id=gate_class.lower(),
        gate_class=gate_class,
        state=m.GateState.SATISFIED,
        policy_owner="governed-delivery-g0",
        policy_version="v1",
        subject_digest_or_head=HEAD,
        producer_identity="deterministic-gate-evaluator",
        observed_at=NOW,
        reason="conformance fixture",
    )


def ledger() -> m.GateLedger:
    return m.GateLedger(
        ledger_id="ledger-r2",
        identity=IDENTITY,
        subject_digest_or_head=HEAD,
        gates=[gate(name) for name in m.GATE_CLASSES],
        risk_lane="L2",
        policy_digest=POLICY_DIGEST,
    )


def projection_document() -> dict:
    projection = s.build_projection(
        s.SnapshotInput(
            identity=IDENTITY,
            work_item_id=PACKET,
            as_of=NOW,
            subject=m.Subject(
                base_sha=BASE,
                head_sha=HEAD,
                tree_sha=TREE,
                content_digest=CONTENT,
            ),
            gate_ledger=ledger(),
            audit_binding=binding(),
            packet_ref=PACKET,
            packet_digest=PACKET_DIGEST,
            policy_digest=POLICY_DIGEST,
        )
    )
    assert projection.posture is m.Posture.READY
    return projection.as_dict()


def equivalence_document() -> dict:
    facts = m.StructuralFacts.claimed(
        ancestry_established=True,
        actual_changed_paths=["proof/TP-X/SUMMARY.md"],
        raw_diff_digest="sha256:" + "6" * 64,
        content_tree_equivalent_under_exclusion=True,
        audited_packet_digest=PACKET_DIGEST,
        successor_packet_digest=PACKET_DIGEST,
        audited_policy_digest=POLICY_DIGEST,
        successor_policy_digest=POLICY_DIGEST,
        audited_audit_result_digest=AUDIT_DIGEST,
        successor_audit_result_digest=AUDIT_DIGEST,
    )
    return eq.evaluate_proof_only_equivalence(
        equivalence_id="eq-r2",
        audited_head=HEAD,
        successor_head="d" * 40,
        audited_bundle=eq.ProofOnlyBundle({"proof/TP-X/PROOF.json": {"audit_verdict": "PASS"}}),
        successor_bundle=eq.ProofOnlyBundle({"proof/TP-X/PROOF.json": {"audit_verdict": "PASS"}}),
        allowed_paths=["proof/**"],
        facts=facts,
    ).as_dict()


def valid_corpus():
    envelope = m.GovernedDeliveryEnvelope(
        envelope_id="env-r2",
        kind=m.EnvelopeKind.FINDING,
        event_type="AuditResult",
        identity=IDENTITY,
        producer="embedded-audit",
        consumer="pr-steward",
        created_at=NOW,
        subject_ref=f"head:{HEAD}",
        idempotency_key="audit-r2",
        payload_schema="audit-result.v1",
        payload={"verdict": "PASS"},
        evidence_refs=[evidence()],
    )
    request = m.OperatorDecisionRequest(
        decision_request_id="decision-r2",
        decision_type=m.DecisionType.MERGE_DECISION_REQUIRED,
        identity=IDENTITY,
        work_item_id=PACKET,
        packet_ref=PACKET,
        exact_subject_ref=f"head:{HEAD}",
        decision_required_from="operator",
        current_state="audit passed; merge forbidden pending operator",
        recommended_action="review exact-head evidence",
    )
    return {
        "evidence-reference.schema.json": (evidence().as_dict(), m.EvidenceReference.from_dict),
        "governed-delivery-envelope.schema.json": (
            envelope.as_dict(),
            m.GovernedDeliveryEnvelope.from_dict,
        ),
        "gate-ledger.schema.json": (ledger().as_dict(), m.GateLedger.from_dict),
        "work-item-projection.schema.json": (
            projection_document(),
            m.WorkItemProjection.from_dict,
        ),
        "content-audit-binding.schema.json": (
            binding().as_dict(),
            m.ContentAuditBinding.from_dict,
        ),
        "operator-decision-request.schema.json": (
            request.as_dict(),
            m.OperatorDecisionRequest.from_dict,
        ),
        "proof-only-successor-equivalence.schema.json": (
            equivalence_document(),
            eq.EquivalenceResult.from_dict,
        ),
    }


def test_valid_runtime_and_schema_conformance_corpus():
    corpus = valid_corpus()
    assert len(corpus) == 7
    for schema_name, (document, runtime_parser) in corpus.items():
        validator(schema_name).validate(document)
        runtime_parser(document)


def test_invalid_runtime_and_schema_conformance_corpus():
    corpus = valid_corpus()
    invalid = {}
    for schema_name, (document, runtime_parser) in corpus.items():
        invalid[schema_name] = [copy.deepcopy(document), runtime_parser]

    invalid["evidence-reference.schema.json"][0]["forbidden"] = "extra"
    invalid["governed-delivery-envelope.schema.json"][0]["schema_version"] = (
        "governed-delivery.envelope.v2"
    )
    invalid["gate-ledger.schema.json"][0]["policy"]["required_gate_set"] = []
    invalid["work-item-projection.schema.json"][0]["audit_binding_acceptable"] = False
    invalid["content-audit-binding.schema.json"][0]["audited_head"] = "abc123"
    invalid["operator-decision-request.schema.json"][0]["current_state"] = ""
    invalid["proof-only-successor-equivalence.schema.json"][0][
        "audit_reuse_authorized"
    ] = True

    assert len(invalid) == 7
    for schema_name, (document, runtime_parser) in invalid.items():
        with pytest.raises(Exception):
            validator(schema_name).validate(document)
        with pytest.raises(Exception):
            runtime_parser(document)


@pytest.mark.parametrize(
    "schema_name",
    [
        "evidence-reference.schema.json",
        "governed-delivery-envelope.schema.json",
        "gate-ledger.schema.json",
        "work-item-projection.schema.json",
        "operator-decision-request.schema.json",
    ],
)
def test_unknown_core_identity_is_invalid_in_runtime_and_schema(schema_name):
    document, runtime_parser = valid_corpus()[schema_name]
    document = copy.deepcopy(document)
    document["project_id"] = "UNKNOWN"
    with pytest.raises(Exception):
        validator(schema_name).validate(document)
    with pytest.raises(Exception):
        runtime_parser(document)
