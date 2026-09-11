"""Tests for dopemux.governed_execution.freeze.lifecycle."""

from __future__ import annotations

import itertools

import pytest

from dopemux.governed_execution.freeze.lifecycle import (
    AuditBeforeFreeze,
    FreezeLifecycle,
    FreezeState,
    IllegalTransition,
    NewFreeze,
    RepairRecorded,
    Revalidated,
    ReviewSettled,
    Unfreeze,
    attach_audit_ref,
)
from dopemux.governed_execution.freeze.receipt import (
    FreezeSubject,
    RepoIdentity,
    author_freeze_receipt,
)
from dopemux.governed_execution.receipts.store import EvidenceRef
from dopemux.governed_execution.receipts.validate import Provenance

_PROVENANCE = Provenance(
    verified_by="tests/unit/governed_execution/freeze/test_lifecycle.py",
    verified_at="2026-09-11T00:00:00Z",
    schema_set_digest="0" * 64,
)
_REPO_IDENTITY = RepoIdentity(
    origin_url="https://github.com/DDD-Enterprises/dopemux-mvp.git",
    toplevel="/Users/hue/code/dopemux-mvp/.worktrees/gec-v2-w04",
)
_VALIDATION_REF = EvidenceRef(path="proof/W04/verify.log", sha256="1" * 64)


def _receipt(head_sha: str = "b" * 40, **overrides: object) -> dict:
    subject = FreezeSubject(
        repo_identity=_REPO_IDENTITY,
        base_sha="a" * 40,
        head_sha=head_sha,
        tree_sha="c" * 40,
        blobs={"a.txt": b"aaa"},
    )
    receipt = dict(
        author_freeze_receipt(
            subject,
            validation_refs=[_VALIDATION_REF],
            review_refs=[],
            frozen_at="2026-09-11T12:00:00Z",
            packet_id="TP-X",
            macro_id="MACRO-X",
            provenance=_PROVENANCE,
            **overrides,
        )
    )
    return receipt


def _lifecycle() -> FreezeLifecycle:
    return FreezeLifecycle.start(_receipt())


def test_frozen_to_unfrozen_via_unfreeze() -> None:
    lifecycle = _lifecycle()
    unfrozen = lifecycle.apply(Unfreeze(reason="defect found in review"))
    assert unfrozen.state is FreezeState.UNFROZEN
    assert lifecycle.state is FreezeState.FROZEN  # original is untouched


def test_unfrozen_self_loops_on_repair_revalidate_review_settle() -> None:
    unfrozen = _lifecycle().apply(Unfreeze(reason="defect"))
    after_repair = unfrozen.apply(RepairRecorded(EvidenceRef("proof/repair.json", "2" * 64)))
    assert after_repair.state is FreezeState.UNFROZEN
    after_revalidate = after_repair.apply(Revalidated((EvidenceRef("proof/revalidate.json", "3" * 64),)))
    assert after_revalidate.state is FreezeState.UNFROZEN
    after_review = after_revalidate.apply(ReviewSettled((EvidenceRef("proof/review.json", "4" * 64),)))
    assert after_review.state is FreezeState.UNFROZEN


def test_new_freeze_marks_old_receipt_superseded_with_supersedes_ref() -> None:
    original = _lifecycle()
    unfrozen = original.apply(Unfreeze(reason="defect"))
    old_ref = EvidenceRef(path="proof/old_freeze.json", sha256="5" * 64)
    new_receipt = _receipt(head_sha="d" * 40, supersedes_freeze_ref=old_ref)

    refrozen = unfrozen.apply(NewFreeze(new_receipt))

    assert refrozen.state is FreezeState.FROZEN
    assert refrozen.receipt["supersedes_freeze_ref"] == {"path": old_ref.path, "sha256": old_ref.sha256}
    assert refrozen.predecessor is not None
    assert refrozen.predecessor.state is FreezeState.SUPERSEDED
    assert refrozen.predecessor.receipt is original.receipt


def test_new_freeze_without_supersedes_ref_is_illegal() -> None:
    unfrozen = _lifecycle().apply(Unfreeze(reason="defect"))
    new_receipt = _receipt(head_sha="d" * 40)  # no supersedes_freeze_ref
    with pytest.raises(IllegalTransition):
        unfrozen.apply(NewFreeze(new_receipt))


_LEGAL_EVENTS_BY_STATE = {
    FreezeState.FROZEN: (Unfreeze,),
    FreezeState.UNFROZEN: (RepairRecorded, Revalidated, ReviewSettled, NewFreeze),
}

_ALL_EVENT_FACTORIES = {
    Unfreeze: lambda: Unfreeze(reason="x"),
    RepairRecorded: lambda: RepairRecorded(EvidenceRef("p", "6" * 64)),
    Revalidated: lambda: Revalidated((EvidenceRef("p", "7" * 64),)),
    ReviewSettled: lambda: ReviewSettled((EvidenceRef("p", "8" * 64),)),
    NewFreeze: lambda: NewFreeze(_receipt(supersedes_freeze_ref=EvidenceRef("p", "9" * 64))),
}


@pytest.mark.parametrize(
    "state,event_type",
    [
        (state, event_type)
        for state, event_type in itertools.product(
            (FreezeState.FROZEN, FreezeState.UNFROZEN), _ALL_EVENT_FACTORIES
        )
        if event_type not in _LEGAL_EVENTS_BY_STATE[state]
    ],
    ids=lambda value: getattr(value, "value", getattr(value, "__name__", str(value))),
)
def test_every_illegal_transition_raises(state: FreezeState, event_type: type) -> None:
    lifecycle = _lifecycle()
    if state is FreezeState.UNFROZEN:
        lifecycle = lifecycle.apply(Unfreeze(reason="x"))
    assert lifecycle.state is state
    with pytest.raises(IllegalTransition):
        lifecycle.apply(_ALL_EVENT_FACTORIES[event_type]())


def test_attach_audit_ref_happy_path() -> None:
    lifecycle = _lifecycle()
    audit_ref = EvidenceRef(path="proof/audit.json", sha256="a" * 64)
    result = attach_audit_ref(lifecycle, audit_ref, lifecycle.receipt["head_sha"])
    assert result is audit_ref


def test_attach_audit_ref_on_unfrozen_raises_audit_before_freeze() -> None:
    lifecycle = _lifecycle().apply(Unfreeze(reason="x"))
    audit_ref = EvidenceRef(path="proof/audit.json", sha256="a" * 64)
    with pytest.raises(AuditBeforeFreeze):
        attach_audit_ref(lifecycle, audit_ref, lifecycle.receipt["head_sha"])


def test_attach_audit_ref_with_different_audited_head_raises() -> None:
    lifecycle = _lifecycle()
    audit_ref = EvidenceRef(path="proof/audit.json", sha256="a" * 64)
    with pytest.raises(AuditBeforeFreeze):
        attach_audit_ref(lifecycle, audit_ref, "f" * 40)
