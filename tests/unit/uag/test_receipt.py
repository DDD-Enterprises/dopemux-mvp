"""Deterministic receipt tests."""

from __future__ import annotations

from dopemux.uag import Receipt, deterministic_receipt
from dopemux.uag.enums import AttemptSemanticState, ExecutionAuthority


def test_receipt_digest_is_deterministic():
    payload = {"result": "hello"}
    r1 = deterministic_receipt(
        "r-1", "a1", AttemptSemanticState.COMPLETED, payload
    )
    r2 = deterministic_receipt(
        "r-1", "a1", AttemptSemanticState.COMPLETED, payload
    )
    assert r1.digest == r2.digest


def test_receipt_digest_varies_with_payload():
    r1 = deterministic_receipt("r-1", "a1", AttemptSemanticState.COMPLETED, {"x": 1})
    r2 = deterministic_receipt("r-1", "a1", AttemptSemanticState.COMPLETED, {"x": 2})
    assert r1.digest != r2.digest


def test_receipt_never_claims_exactly_once():
    r = deterministic_receipt("r-1", "a1", AttemptSemanticState.COMPLETED, {})
    assert r.exactly_once_claim == "FORBIDDEN"


def test_receipt_execution_authority_is_none():
    r = deterministic_receipt("r-1", "a1", AttemptSemanticState.COMPLETED, {})
    assert r.execution_authority is ExecutionAuthority.NONE


def test_receipt_is_frozen():
    r = Receipt(
        receipt_id="r-1",
        digest="0" * 64,
        subject_ref="a1",
        semantic_state=AttemptSemanticState.COMPLETED,
    )
    assert r.exactly_once_claim == "FORBIDDEN"
