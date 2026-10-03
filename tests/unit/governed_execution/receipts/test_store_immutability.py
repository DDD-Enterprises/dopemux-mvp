"""Tests for dopemux.governed_execution.receipts.store."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import dopemux.governed_execution.receipts.store as store_module
from dopemux.governed_execution.receipts.store import (
    EvidenceRef,
    EvidenceStore,
    ImmutabilityViolation,
    ValidationRef,
)


def test_put_get_round_trip(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    address = store.put(b"evidence-bytes")
    assert address == hashlib.sha256(b"evidence-bytes").hexdigest()
    assert store.get(address) == b"evidence-bytes"


def test_identical_reput_is_a_no_op(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    first = store.put(b"same-bytes")
    second = store.put(b"same-bytes")
    assert first == second
    assert store.get(first) == b"same-bytes"


def test_forged_collision_raises_immutability_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = EvidenceStore(tmp_path)
    store.put(b"first-bytes")
    forced_address = hashlib.sha256(b"first-bytes").hexdigest()

    class _ForcedCollisionDigest:
        def __init__(self, _data: bytes) -> None:
            pass

        def hexdigest(self) -> str:
            return forced_address

    monkeypatch.setattr(store_module.hashlib, "sha256", _ForcedCollisionDigest)
    with pytest.raises(ImmutabilityViolation) as excinfo:
        store.put(b"second-different-bytes")
    assert forced_address in str(excinfo.value)


def test_no_delete_or_update_api() -> None:
    assert not hasattr(EvidenceStore, "delete")
    assert not hasattr(EvidenceStore, "update")
    assert "delete" not in dir(EvidenceStore)
    assert "update" not in dir(EvidenceStore)


def test_ref_sha256_equals_address(tmp_path: Path) -> None:
    store = EvidenceStore(tmp_path)
    address = store.put(b"ref-me")
    ref = store.ref(address)
    assert ref.sha256 == address
    assert ref.path == f"{address[:2]}/{address}"


def test_validation_ref_projects_to_evidence_ref() -> None:
    validation_ref = ValidationRef(
        kind="slice_validation",
        path="proof/W04/slice_validation.json",
        sha256="a" * 64,
        status="PASS",
    )
    projected = validation_ref.as_evidence_ref()
    assert projected == EvidenceRef(path=validation_ref.path, sha256=validation_ref.sha256)
