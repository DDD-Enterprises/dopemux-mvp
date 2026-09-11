"""Tests for dopemux.governed_execution.freeze.finality."""

from __future__ import annotations

import pytest

from dopemux.governed_execution.freeze.finality import (
    AuditReceiptRef,
    SubjectMismatch,
    author_finality_receipt,
)
from dopemux.governed_execution.freeze.lifecycle import AuditBeforeFreeze, FreezeLifecycle, Unfreeze
from dopemux.governed_execution.freeze.receipt import (
    FreezeSubject,
    RepoIdentity,
    author_freeze_receipt,
)
from dopemux.governed_execution.receipts.store import EvidenceRef
from dopemux.governed_execution.receipts.validate import Provenance

_PROVENANCE = Provenance(
    verified_by="tests/unit/governed_execution/freeze/test_finality_subject_binding.py",
    verified_at="2026-09-11T00:00:00Z",
    schema_set_digest="0" * 64,
)
_REPO_IDENTITY = RepoIdentity(
    origin_url="https://github.com/DDD-Enterprises/dopemux-mvp.git",
    toplevel="/Users/hue/code/dopemux-mvp/.worktrees/gec-v2-w04",
)
_HEAD_SHA = "b" * 40
_FREEZE_REF = EvidenceRef(path="proof/W04/freeze_receipt.json", sha256="e" * 64)


def _frozen_lifecycle() -> FreezeLifecycle:
    subject = FreezeSubject(
        repo_identity=_REPO_IDENTITY,
        base_sha="a" * 40,
        head_sha=_HEAD_SHA,
        tree_sha="c" * 40,
        blobs={"a.txt": b"aaa"},
    )
    receipt = author_freeze_receipt(
        subject,
        validation_refs=[EvidenceRef(path="proof/W04/verify.log", sha256="1" * 64)],
        review_refs=[],
        frozen_at="2026-09-11T12:00:00Z",
        packet_id="TP-X",
        macro_id="MACRO-X",
        provenance=_PROVENANCE,
    )
    return FreezeLifecycle.start(receipt)


def _audit_ref(audited_head: str = _HEAD_SHA, verdict: str = "PASS_WITH_RISKS") -> AuditReceiptRef:
    return AuditReceiptRef(
        path="proof/W04/audit_receipt.json",
        sha256="f" * 64,
        audited_head=audited_head,
        verdict=verdict,
    )


def test_audited_head_equals_finality_head_validates() -> None:
    lifecycle = _frozen_lifecycle()
    receipt = author_finality_receipt(
        lifecycle,
        _FREEZE_REF,
        _audit_ref(),
        finality_head=_HEAD_SHA,
        pr_ref="NOT_RUN",
        steward_snapshot="NOT_RUN",
        recorded_at="2026-09-11T15:00:00Z",
        packet_id="TP-X",
        macro_id="MACRO-X",
        provenance=_PROVENANCE,
    )
    assert receipt["audited_head"] == receipt["finality_head"] == _HEAD_SHA
    assert receipt["exact_head_equality"] is True
    assert receipt["audit_verdict"] == "PASS_WITH_RISKS"


def test_audited_head_ne_finality_head_raises_subject_mismatch() -> None:
    lifecycle = _frozen_lifecycle()
    with pytest.raises(SubjectMismatch):
        author_finality_receipt(
            lifecycle,
            _FREEZE_REF,
            _audit_ref(),
            finality_head="f" * 40,
            pr_ref="NOT_RUN",
            steward_snapshot=None,
            recorded_at="2026-09-11T15:00:00Z",
            packet_id="TP-X",
            macro_id="MACRO-X",
            provenance=_PROVENANCE,
        )


def test_audited_head_ne_freeze_head_raises_audit_before_freeze() -> None:
    lifecycle = _frozen_lifecycle()
    mismatched_ref = _audit_ref(audited_head="d" * 40)
    with pytest.raises(AuditBeforeFreeze):
        author_finality_receipt(
            lifecycle,
            _FREEZE_REF,
            mismatched_ref,
            finality_head="d" * 40,
            pr_ref="NOT_RUN",
            steward_snapshot=None,
            recorded_at="2026-09-11T15:00:00Z",
            packet_id="TP-X",
            macro_id="MACRO-X",
            provenance=_PROVENANCE,
        )


def test_authoring_from_unfrozen_subject_raises_audit_before_freeze() -> None:
    lifecycle = _frozen_lifecycle().apply(Unfreeze(reason="defect found"))
    with pytest.raises(AuditBeforeFreeze):
        author_finality_receipt(
            lifecycle,
            _FREEZE_REF,
            _audit_ref(),
            finality_head=_HEAD_SHA,
            pr_ref="NOT_RUN",
            steward_snapshot=None,
            recorded_at="2026-09-11T15:00:00Z",
            packet_id="TP-X",
            macro_id="MACRO-X",
            provenance=_PROVENANCE,
        )


def test_authored_receipt_always_has_merge_and_activation_authorized_false() -> None:
    lifecycle = _frozen_lifecycle()
    receipt = author_finality_receipt(
        lifecycle,
        _FREEZE_REF,
        _audit_ref(verdict="PASS"),
        finality_head=_HEAD_SHA,
        pr_ref="https://github.com/DDD-Enterprises/dopemux-mvp/pull/1",
        steward_snapshot="READY",
        recorded_at="2026-09-11T15:00:00Z",
        packet_id="TP-X",
        macro_id="MACRO-X",
        provenance=_PROVENANCE,
    )
    assert receipt["merge_authorized"] is False
    assert receipt["activation_authorized"] is False
    assert receipt["authority"] == "NONE"
    assert receipt["steward_readiness"] == "READY"


def test_steward_readiness_none_becomes_unknown() -> None:
    lifecycle = _frozen_lifecycle()
    receipt = author_finality_receipt(
        lifecycle,
        _FREEZE_REF,
        _audit_ref(),
        finality_head=_HEAD_SHA,
        pr_ref="NOT_RUN",
        steward_snapshot=None,
        recorded_at="2026-09-11T15:00:00Z",
        packet_id="TP-X",
        macro_id="MACRO-X",
        provenance=_PROVENANCE,
    )
    assert receipt["steward_readiness"] == "UNKNOWN"
