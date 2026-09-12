"""Isolation invariants: cross-project, cross-worktree and unknown identity.

Every one of these must fail closed. Cross-project reuse is forbidden outright;
cross-worktree reuse is forbidden absent an explicit deterministic equivalence.
"""

from __future__ import annotations

import pytest

from dopemux.governed_delivery import models as m
from dopemux.governed_delivery import snapshot as s
from dopemux.governed_delivery.receipts import require_identity_match

NOW = "2026-08-24T00:00:00Z"

HOME = m.Identity(
    project_id="dopemux-mvp",
    repository_id="DDD-Enterprises/dopemux-mvp",
    workspace_id="ws-1",
    worktree_id="wt-1",
    instance_id="inst-1",
    packet_id="TP-A",
)
CORE = m.Identity(
    project_id=HOME.project_id,
    repository_id=HOME.repository_id,
    worktree_id=HOME.worktree_id,
    packet_id=HOME.packet_id,
)


def reference(identity: m.Identity, evidence_id: str = "ev-1"):
    return m.EvidenceReference(
        evidence_id=evidence_id,
        evidence_class="VALIDATION_RECEIPT",
        owner_system="PROOF_TOOLING",
        producer_identity="tool",
        canonical_location="proof/TP-A/VALIDATION.json",
        digest_or_signature="sha256:abc",
        identity=identity,
        observed_at=NOW,
        freshness_state=m.FreshnessState.CURRENT,
    )


def replace(identity: m.Identity, **changes) -> m.Identity:
    fields = identity.as_dict()
    fields.update(changes)
    return m.Identity(**fields)


class TestIdentityConflictDetection:
    def test_identical_identity_is_compatible(self):
        assert HOME.conflicts_with(HOME) is None

    @pytest.mark.parametrize(
        "dimension,value",
        [
            ("project_id", "other-project"),
            ("repository_id", "someone/other-repo"),
            ("workspace_id", "ws-2"),
            ("worktree_id", "wt-2"),
            ("instance_id", "inst-2"),
            ("packet_id", "TP-B"),
        ],
    )
    def test_each_dimension_mismatch_is_detected(self, dimension, value):
        other = replace(HOME, **{dimension: value})
        assert HOME.conflicts_with(other) == dimension

    def test_absent_dimension_is_not_a_value_conflict(self):
        """Optional workspace/instance absence is not a mismatch."""
        assert HOME.conflicts_with(CORE) is None


class TestRequiredIdentityDimensions:
    """GOV-AUD-004 R2: fixed core profile, optional dimensions compare when present."""

    @pytest.mark.parametrize(
        "dimension", ["project_id", "repository_id", "worktree_id", "packet_id"]
    )
    def test_required_dimension_cannot_be_unbound(self, dimension):
        values = CORE.as_dict()
        values[dimension] = None
        with pytest.raises(m.Denial):
            m.Identity(**values)

    def test_applicable_dimensions_track_what_the_identity_binds(self):
        assert m.applicable_dimensions(CORE) == m.G0_REQUIRED_IDENTITY_DIMENSIONS
        assert m.applicable_dimensions(HOME) == m.G0_REQUIRED_IDENTITY_DIMENSIONS

    def test_both_sides_bound_and_equal_is_accepted(self):
        HOME.require_compatible(
            HOME, context="test", required_dimensions=m.applicable_dimensions(HOME)
        )

    def test_unknown_dimension_name_is_denied(self):
        with pytest.raises(m.Denial):
            HOME.missing_dimensions(HOME, ["not_a_dimension"])

    def test_optional_identity_absence_is_accepted(self):
        require_identity_match(reference(CORE), HOME, context="reuse")

    def test_envelope_accepts_evidence_without_optional_dimensions(self):
        envelope = m.GovernedDeliveryEnvelope(
            envelope_id="env-core",
            kind=m.EnvelopeKind.FACT,
            event_type="ProofBundleRef",
            identity=HOME,
            producer="tool",
            consumer="tool",
            created_at=NOW,
            subject_ref="abc",
            idempotency_key="k1",
            payload_schema="schema",
            payload={},
            evidence_refs=[reference(CORE)],
        )
        assert envelope.evidence_refs

    def test_snapshot_requires_the_packet_dimension_when_packet_scoped(self):
        source = s.SnapshotInput(
            identity=HOME,
            work_item_id="TP-A",
            as_of=NOW,
            packet_ref="TP-A",
            evidence_refs=[reference(CORE)],
        )
        assert source.identity_dimensions_required() == m.G0_REQUIRED_IDENTITY_DIMENSIONS
        assert s.build_projection(source).work_item_id == "TP-A"


class TestCrossProjectDenial:
    def test_wrong_project_denied(self):
        foreign = reference(replace(HOME, project_id="other-project"))
        with pytest.raises(m.Denial) as excinfo:
            require_identity_match(foreign, HOME, context="test")
        assert excinfo.value.normalized_class is m.NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION

    def test_wrong_repository_denied(self):
        foreign = reference(replace(HOME, repository_id="someone/other-repo"))
        with pytest.raises(m.Denial):
            require_identity_match(foreign, HOME, context="test")

    def test_wrong_worktree_denied(self):
        foreign = reference(replace(HOME, worktree_id="wt-2"))
        with pytest.raises(m.Denial):
            require_identity_match(foreign, HOME, context="test")

    def test_wrong_workspace_denied(self):
        foreign = reference(replace(HOME, workspace_id="ws-2"))
        with pytest.raises(m.Denial):
            require_identity_match(foreign, HOME, context="test")

    def test_wrong_packet_denied(self):
        foreign = reference(replace(HOME, packet_id="TP-B"))
        with pytest.raises(m.Denial):
            require_identity_match(foreign, HOME, context="test")

    def test_matching_identity_accepted(self):
        require_identity_match(reference(HOME), HOME, context="test")


class TestUnknownIdentityFailsClosed:
    def test_blank_project_denied(self):
        with pytest.raises(m.Denial):
            m.Identity(project_id="", repository_id="repo")

    def test_blank_repository_denied(self):
        with pytest.raises(m.Denial):
            m.Identity(project_id="project", repository_id="")

    def test_literal_unknown_project_denied(self):
        with pytest.raises(m.Denial):
            m.Identity(project_id="UNKNOWN", repository_id="repo")

    def test_literal_unknown_repository_denied(self):
        with pytest.raises(m.Denial):
            m.Identity(project_id="project", repository_id="unknown")

    def test_whitespace_only_denied(self):
        with pytest.raises(m.Denial):
            m.Identity(project_id="   ", repository_id="repo")


class TestEnvelopeCrossProjectDenial:
    def test_envelope_rejects_foreign_evidence(self):
        with pytest.raises(m.Denial):
            m.GovernedDeliveryEnvelope(
                envelope_id="env-1",
                kind=m.EnvelopeKind.RECEIPT,
                event_type="ValidationResult",
                identity=HOME,
                producer="tool",
                consumer="governed-delivery",
                created_at=NOW,
                subject_ref="head:abc",
                idempotency_key="k",
                payload_schema="p.v1",
                payload={},
                evidence_refs=[reference(replace(HOME, project_id="other-project"))],
            )

    def test_envelope_accepts_matching_evidence(self):
        envelope = m.GovernedDeliveryEnvelope(
            envelope_id="env-1",
            kind=m.EnvelopeKind.RECEIPT,
            event_type="ValidationResult",
            identity=HOME,
            producer="tool",
            consumer="governed-delivery",
            created_at=NOW,
            subject_ref="head:abc",
            idempotency_key="k",
            payload_schema="p.v1",
            payload={},
            evidence_refs=[reference(HOME)],
        )
        assert len(envelope.evidence_refs) == 1


class TestSnapshotCrossProjectDenial:
    def test_snapshot_denies_foreign_evidence(self):
        with pytest.raises(m.Denial):
            s.build_projection(
                s.SnapshotInput(
                    identity=HOME,
                    work_item_id="TP-A",
                    as_of=NOW,
                    packet_ref="TP-A",
                    evidence_refs=[reference(replace(HOME, project_id="other-project"))],
                )
            )

    def test_snapshot_denies_foreign_worktree_evidence(self):
        with pytest.raises(m.Denial):
            s.build_projection(
                s.SnapshotInput(
                    identity=HOME,
                    work_item_id="TP-A",
                    as_of=NOW,
                    packet_ref="TP-A",
                    evidence_refs=[reference(replace(HOME, worktree_id="wt-2"))],
                )
            )

    def test_snapshot_accepts_own_evidence(self):
        projection = s.build_projection(
            s.SnapshotInput(
                identity=HOME,
                work_item_id="TP-A",
                as_of=NOW,
                packet_ref="TP-A",
                evidence_refs=[reference(HOME)],
            )
        )
        assert projection.work_item_id == "TP-A"
