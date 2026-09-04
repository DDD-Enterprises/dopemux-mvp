"""Three-lane IR separation tests."""

from __future__ import annotations

import dataclasses

import pytest

from dopemux.uag import (
    DigestRef,
    FamilyEnvelope,
    PrivateStateCapsuleRef,
    PublicCore,
    RequestedOutputContract,
)
from dopemux.uag.enums import OutputContractClass


def test_public_core_canonicalizes_deterministically():
    core = PublicCore(public_text="hello", public_values=(("b", 2), ("a", 1)))
    canonical = core.canonical()
    assert canonical["public_text"] == "hello"
    # public_values sorted by key for deterministic serialization.
    assert canonical["public_values"] == [("a", 1), ("b", 2)]


def test_family_envelope_is_opaque_to_core():
    opaque = object()
    envelope = FamilyEnvelope(family_id="openai", payload=opaque)
    assert envelope.payload is opaque


def test_private_state_capsule_is_digest_only():
    ref = DigestRef(id="ps-1", sha256="1" * 64)
    capsule = PrivateStateCapsuleRef(ref=ref)
    # The core exposes only the reference, never the underlying bytes.
    assert capsule.ref is ref
    assert not hasattr(capsule, "bytes")
    assert not hasattr(capsule, "payload")


def test_ir_types_are_frozen():
    for obj in (
        PublicCore(),
        FamilyEnvelope("f", object()),
        PrivateStateCapsuleRef(DigestRef("ps-1", "1" * 64)),
        RequestedOutputContract(OutputContractClass.PUBLIC_TEXT),
    ):
        assert dataclasses.is_dataclass(obj)


def test_digest_ref_rejects_invalid_sha():
    with pytest.raises(ValueError):
        DigestRef(id="bad", sha256="not-a-hash")
