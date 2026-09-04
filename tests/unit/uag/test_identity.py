"""Identity-stage and UNKNOWN/CONFLICTING first-class tests."""

from __future__ import annotations

import pytest

from dopemux.uag import (
    ConflictItem,
    IdentityChain,
    IdentityStage,
    UnknownItem,
)
from dopemux.uag.enums import (
    AttestationClass,
    Confidence,
    EvidenceStatus,
    IdentityStageName,
)


def _stage(name: IdentityStageName, value: str | None = None) -> IdentityStage:
    return IdentityStage(
        stage=name,
        value=value,
        source="test",
        evidence_status=EvidenceStatus.OBSERVED,
        confidence=Confidence.HIGH,
    )


def test_stages_remain_distinct_and_chain_is_append_only():
    chain = IdentityChain()
    chain = chain.record(_stage(IdentityStageName.REQUESTED, "id-requested"))
    chain = chain.record(_stage(IdentityStageName.CONFIGURED, "id-configured"))

    assert chain.get(IdentityStageName.REQUESTED).value == "id-requested"
    assert chain.get(IdentityStageName.CONFIGURED).value == "id-configured"
    assert chain.get(IdentityStageName.PROVIDER_ATTESTED) is None


def test_duplicate_stage_is_refused_not_rewritten():
    chain = IdentityChain().record(_stage(IdentityStageName.REQUESTED, "first"))
    with pytest.raises(ValueError):
        chain.record(_stage(IdentityStageName.REQUESTED, "second"))
    assert chain.get(IdentityStageName.REQUESTED).value == "first"


def test_provider_attested_requires_attestation_class():
    with pytest.raises(ValueError):
        IdentityStage(
            stage=IdentityStageName.PROVIDER_ATTESTED,
            value="model-id",
            source="provider",
            evidence_status=EvidenceStatus.OBSERVED,
            confidence=Confidence.HIGH,
        )


def test_provider_attested_cannot_be_inferred_from_provider_reported():
    # provider_reported is a distinct stage with no attestation class.
    reported = _stage(IdentityStageName.PROVIDER_REPORTED, "model-id")
    assert reported.stage is not IdentityStageName.PROVIDER_ATTESTED
    # The resolved_identity must not treat provider_reported as attested.
    chain = IdentityChain().record(reported)
    assert chain.get(IdentityStageName.PROVIDER_ATTESTED) is None


def test_provider_attested_with_absent_class_ok():
    stage = IdentityStage(
        stage=IdentityStageName.PROVIDER_ATTESTED,
        value="model-id",
        source="provider",
        evidence_status=EvidenceStatus.OBSERVED,
        confidence=Confidence.HIGH,
        attestation_class=AttestationClass.ABSENT,
    )
    assert stage.attestation_class is AttestationClass.ABSENT


def test_unknown_and_conflicting_are_first_class():
    unknown = UnknownItem(code="U1", description="identity unresolved")
    conflict = ConflictItem(
        code="C1", left="model-a", right="model-b", description="two models reported"
    )
    assert unknown.evidence_status is EvidenceStatus.UNKNOWN
    assert conflict.left != conflict.right
    # Neither is silently coerced into a resolved identity.
    chain = IdentityChain()
    assert chain.resolved_identity is None


def test_resolved_identity_prefers_highest_fidelity_stage():
    chain = IdentityChain()
    chain = chain.record(_stage(IdentityStageName.REQUESTED, "r"))
    chain = chain.record(_stage(IdentityStageName.UAG_RESOLVED, "uag"))
    assert chain.resolved_identity == "uag"
