"""Tests for dopemux.governed_execution.freeze.receipt."""

from __future__ import annotations

import hashlib

from dopemux.governed_execution.freeze.receipt import (
    FreezeSubject,
    RepoIdentity,
    author_freeze_receipt,
    candidate_digest,
    substantive_path_digest,
)
from dopemux.governed_execution.receipts.store import EvidenceRef
from dopemux.governed_execution.receipts.validate import Provenance

_PROVENANCE = Provenance(
    verified_by="tests/unit/governed_execution/freeze/test_freeze_receipt.py",
    verified_at="2026-09-11T00:00:00Z",
    schema_set_digest="0" * 64,
)

_REPO_IDENTITY = RepoIdentity(
    origin_url="https://github.com/DDD-Enterprises/dopemux-mvp.git",
    toplevel="/Users/hue/code/dopemux-mvp/.worktrees/gec-v2-w04",
)

_VALIDATION_REF = EvidenceRef(path="proof/W04/verify.log", sha256="1" * 64)


def _subject(blobs: dict[str, bytes]) -> FreezeSubject:
    return FreezeSubject(
        repo_identity=_REPO_IDENTITY,
        base_sha="a" * 40,
        head_sha="b" * 40,
        tree_sha="c" * 40,
        blobs=blobs,
    )


def _manual_substantive_path_digest(paths: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(paths)).encode("utf-8")).hexdigest()


def _manual_candidate_digest(blobs: dict[str, bytes]) -> str:
    parts = "".join(
        f"{hashlib.sha256(blobs[path]).hexdigest()}\n" for path in sorted(blobs)
    )
    return hashlib.sha256(parts.encode("ascii")).hexdigest()


def test_authored_receipt_validates() -> None:
    blobs = {"src/a.py": b"a-bytes", "src/b.py": b"b-bytes"}
    receipt = author_freeze_receipt(
        _subject(blobs),
        validation_refs=[_VALIDATION_REF],
        review_refs=[],
        frozen_at="2026-09-11T12:00:00Z",
        packet_id="TP-DMX-GEC-V2-W04-EVIDENCE-SPINE-001",
        macro_id="MACRO-DMX-GOVERNED-EXECUTION-CONTRACT-V2-001",
        provenance=_PROVENANCE,
    )
    assert receipt["schema_version"] == "dopemux.governed_execution.freeze_receipt.v1"
    assert receipt["freeze_state"] == "FROZEN"
    assert receipt["no_audit_before_freeze"] is True
    assert receipt["authority"] == "NONE"
    assert receipt["substantive_paths"] == ["src/a.py", "src/b.py"]
    assert receipt["validation_refs"] == [{"path": "proof/W04/verify.log", "sha256": "1" * 64}]
    assert receipt["review_refs"] == []


def test_digests_match_independent_recomputation() -> None:
    blobs = {"z.txt": b"zzz", "a.txt": b"aaa", "m.txt": b"mmm"}
    receipt = author_freeze_receipt(
        _subject(blobs),
        validation_refs=[_VALIDATION_REF],
        review_refs=[],
        frozen_at="2026-09-11T12:00:00Z",
        packet_id="TP-X",
        macro_id="MACRO-X",
        provenance=_PROVENANCE,
    )
    sorted_paths = sorted(blobs)
    assert receipt["substantive_path_digest"] == _manual_substantive_path_digest(sorted_paths)
    assert receipt["substantive_path_digest"] == substantive_path_digest(sorted_paths)
    assert receipt["candidate_digest"] == _manual_candidate_digest(blobs)
    assert receipt["candidate_digest"] == candidate_digest(blobs)


def test_digests_are_path_order_independent() -> None:
    blobs_in_order = {"a.txt": b"aaa", "b.txt": b"bbb", "c.txt": b"ccc"}
    blobs_reversed = {"c.txt": b"ccc", "a.txt": b"aaa", "b.txt": b"bbb"}

    receipt_a = author_freeze_receipt(
        _subject(blobs_in_order),
        validation_refs=[_VALIDATION_REF],
        review_refs=[],
        frozen_at="2026-09-11T12:00:00Z",
        packet_id="TP-X",
        macro_id="MACRO-X",
        provenance=_PROVENANCE,
    )
    receipt_b = author_freeze_receipt(
        _subject(blobs_reversed),
        validation_refs=[_VALIDATION_REF],
        review_refs=[],
        frozen_at="2026-09-11T12:00:00Z",
        packet_id="TP-X",
        macro_id="MACRO-X",
        provenance=_PROVENANCE,
    )
    assert receipt_a["substantive_path_digest"] == receipt_b["substantive_path_digest"]
    assert receipt_a["candidate_digest"] == receipt_b["candidate_digest"]
    assert receipt_a["substantive_paths"] == receipt_b["substantive_paths"]


def test_supersedes_freeze_ref_is_embedded_when_given() -> None:
    blobs = {"a.txt": b"aaa"}
    old_ref = EvidenceRef(path="proof/old_freeze.json", sha256="9" * 64)
    receipt = author_freeze_receipt(
        _subject(blobs),
        validation_refs=[_VALIDATION_REF],
        review_refs=[],
        frozen_at="2026-09-11T12:00:00Z",
        packet_id="TP-X",
        macro_id="MACRO-X",
        provenance=_PROVENANCE,
        supersedes_freeze_ref=old_ref,
    )
    assert receipt["supersedes_freeze_ref"] == {"path": old_ref.path, "sha256": old_ref.sha256}
