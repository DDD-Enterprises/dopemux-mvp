"""Schema-validated, same-subject inputs to the derived dispatch join."""
from __future__ import annotations

import json
from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import Any

import pytest

from dopemux.governed_execution.dispatch import (
    RECEIPT_NAMES,
    JoinInput,
    Provenance,
    ReceiptName,
    qualify,
)
from dopemux.governed_execution.receipts.validate import (
    Provenance as ReceiptProvenance,
    ValidatedReceipt,
    validate_receipt,
)

MACRO_ID = "MACRO-W02B-TEST"
PACKET_ID = "TP-W02B-TEST"
_VALID_DIR = (
    Path(__file__).resolve().parents[4]
    / "tests/governance/governed_execution/fixtures/valid"
)
_FIXTURES = {
    "ScopeAuthority": "dispatch_input_receipt.v1__scope_authority",
    "WorkflowLegality": "dispatch_input_receipt.v1__workflow_legality",
    "PolicyEligibility": "dispatch_input_receipt.v1__policy_eligibility",
    "CanonicalWriter": "writer_custody_receipt.v1",
    "ExecutionBinding": "execution_binding.v2",
    "OperatorGate": "dispatch_input_receipt.v1__operator_gate",
    "DriftOverlap": "dispatch_input_receipt.v1__drift_overlap",
}
_RECEIPT_PROVENANCE = ReceiptProvenance(
    verified_by="w02b-test",
    verified_at="2026-09-20T00:00:00Z",
    schema_set_digest="0" * 64,
)


@cache
def _base_receipt(name: ReceiptName) -> ValidatedReceipt:
    """Validate read-only governance fixtures through the runtime boundary."""
    fixture = _FIXTURES[name]
    payload = json.loads((_VALID_DIR / f"{fixture}.json").read_bytes())
    payload.update(macro_id=MACRO_ID, packet_id=PACKET_ID)
    return validate_receipt(
        fixture.split("__", 1)[0], json.dumps(payload).encode(), _RECEIPT_PROVENANCE
    )


def _validated_receipt(name: ReceiptName, **changes: Any) -> ValidatedReceipt:
    receipt = _base_receipt(name)
    payload = deepcopy(dict(receipt.payload))
    payload.update(changes)
    return validate_receipt(receipt.kind, json.dumps(payload).encode(), _RECEIPT_PROVENANCE)


def _full_receipts() -> dict[ReceiptName, ValidatedReceipt]:
    return {name: deepcopy(_base_receipt(name)) for name in RECEIPT_NAMES}


def _provenance() -> Provenance:
    return Provenance(
        verified_by="w02b-test",
        verified_at="2026-09-20T00:00:00Z",
        schema_set_digest="0" * 64,
    )


def _join_input(receipts: Any) -> JoinInput:
    return JoinInput(
        receipts=receipts,
        provenance=_provenance(),
        macro_id=MACRO_ID,
        packet_id=PACKET_ID,
    )


def test_full_seven_receipt_fixture_is_dispatchable() -> None:
    receipts = _full_receipts()
    assert all(isinstance(receipt, ValidatedReceipt) for receipt in receipts.values())
    result = qualify(_join_input(receipts))
    assert result.result == "DISPATCHABLE"
    assert result.reasons == ()
    assert result.provenance == _provenance()
    assert result.authority == "NONE"
    assert result.is_execution_authority is False


@pytest.mark.parametrize("drift_class", ["IDENTICAL", "SUBSET", "COMPATIBLE"])
def test_compatible_drift_classes_remain_dispatchable(drift_class: str) -> None:
    receipts = _full_receipts()
    receipts["DriftOverlap"] = _validated_receipt("DriftOverlap", drift_class=drift_class)
    result = qualify(_join_input(receipts))
    assert result.result == "DISPATCHABLE"
    assert result.reasons == ()
    assert result.authority == "NONE"
    assert result.is_execution_authority is False


def test_required_operator_gate_with_grant_and_receipt_is_dispatchable() -> None:
    receipts = _full_receipts()
    receipts["OperatorGate"] = _validated_receipt(
        "OperatorGate", required=True, granted=True, receipt_ref="operator:grant"
    )
    result = qualify(_join_input(receipts))
    assert result.result == "DISPATCHABLE"
    assert result.reasons == ()
