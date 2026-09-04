"""Append-only physical-attempt lineage tests."""

from __future__ import annotations

import dataclasses

import pytest

from dopemux.uag import AttemptLineage, AttemptRecord, DigestRef
from dopemux.uag.enums import AttemptSemanticState


def _record(attempt_id: str, state: AttemptSemanticState) -> AttemptRecord:
    return AttemptRecord(
        attempt_id=attempt_id,
        semantic_state=state,
        selected_route_profile_id="profile-1",
    )


def test_lineage_is_append_only_and_immutable():
    lineage = AttemptLineage()
    a = _record("a1", AttemptSemanticState.NOT_SENT)
    lineage2 = lineage.append(a)
    lineage3 = lineage2.append(_record("a2", AttemptSemanticState.COMPLETED))

    assert len(lineage) == 0
    assert len(lineage2) == 1
    assert len(lineage3) == 2
    assert lineage3.records[0] is a
    assert lineage3.latest().attempt_id == "a2"


def test_existing_records_cannot_be_rewritten():
    a1 = _record("a1", AttemptSemanticState.NOT_SENT)
    lineage = AttemptLineage(records=(a1,))
    lineage2 = lineage.append(_record("a1", AttemptSemanticState.COMPLETED))

    # Append does not rewrite the original record; both are preserved in order.
    assert lineage.records[0].semantic_state is AttemptSemanticState.NOT_SENT
    assert lineage2.records[0].semantic_state is AttemptSemanticState.NOT_SENT
    assert lineage2.records[1].semantic_state is AttemptSemanticState.COMPLETED


def test_attempt_record_is_frozen():
    a = _record("a1", AttemptSemanticState.NOT_SENT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.semantic_state = AttemptSemanticState.COMPLETED


def test_non_acceptance_requires_evidence_ref():
    with pytest.raises(ValueError):
        AttemptRecord(
            attempt_id="a1",
            semantic_state=AttemptSemanticState.NON_ACCEPTANCE_PROVEN,
            selected_route_profile_id="profile-1",
        )


def test_evidence_ref_only_for_non_acceptance():
    with pytest.raises(ValueError):
        AttemptRecord(
            attempt_id="a1",
            semantic_state=AttemptSemanticState.COMPLETED,
            selected_route_profile_id="profile-1",
            provider_non_acceptance_evidence_ref=DigestRef(
                id="ev-1", sha256="0" * 64
            ),
        )


def test_non_acceptance_with_evidence_ref_ok():
    record = AttemptRecord(
        attempt_id="a1",
        semantic_state=AttemptSemanticState.NON_ACCEPTANCE_PROVEN,
        selected_route_profile_id="profile-1",
        provider_non_acceptance_evidence_ref=DigestRef(id="ev-1", sha256="0" * 64),
    )
    assert record.provider_non_acceptance_evidence_ref.id == "ev-1"
