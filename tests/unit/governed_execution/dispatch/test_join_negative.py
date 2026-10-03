"""Fail-closed receipt admission and existing dispatch denial precedence."""
from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import pytest

from dopemux.governed_execution.dispatch import (
    RECEIPT_NAMES,
    DispatchQualification,
    JoinInput,
    ReceiptName,
    qualify,
)
from dopemux.governed_execution.receipts.validate import ReceiptInvalid, validate_receipt
from tests.unit.governed_execution.dispatch.test_join_positive import (
    MACRO_ID,
    PACKET_ID,
    _full_receipts,
    _join_input,
    _provenance,
    _validated_receipt,
)

_UPSTREAM_NAMES = (
    "ScopeAuthority", "WorkflowLegality", "PolicyEligibility", "OperatorGate", "DriftOverlap"
)


def _assert_never_authority(result: DispatchQualification) -> None:
    assert result.authority == "NONE"
    assert result.is_execution_authority is False


def _assert_contract_blocked(receipts: Any, name: str) -> None:
    result = qualify(_join_input(receipts))
    assert result.result == "BLOCKED"
    assert any(r.rule == 1 and r.receipt == name for r in result.reasons)
    _assert_never_authority(result)


def test_all_seven_free_dict_receipts_are_rejected() -> None:
    receipts = {name: dict(receipt.payload) for name, receipt in _full_receipts().items()}
    result = qualify(_join_input(receipts))
    assert result.result == "BLOCKED"
    assert {r.receipt for r in result.reasons if r.rule == 1} == set(RECEIPT_NAMES)
    _assert_never_authority(result)


@pytest.mark.parametrize("name", RECEIPT_NAMES)
def test_each_free_dict_is_rejected_among_six_validated_receipts(name: ReceiptName) -> None:
    receipts = _full_receipts()
    receipts[name] = dict(receipts[name].payload)
    _assert_contract_blocked(receipts, name)


def test_free_canonical_writer_held_cannot_pass() -> None:
    receipts = _full_receipts()
    receipts["CanonicalWriter"] = {"custody_state": "HELD"}
    _assert_contract_blocked(receipts, "CanonicalWriter")


@pytest.mark.parametrize("name", RECEIPT_NAMES)
@pytest.mark.parametrize("field", ["macro_id", "packet_id"])
def test_cross_subject_receipt_is_rejected(name: ReceiptName, field: str) -> None:
    receipts = _full_receipts()
    receipts[name] = _validated_receipt(name, **{field: "another-subject"})
    _assert_contract_blocked(receipts, name)


@pytest.mark.parametrize("field", ["macro_id", "packet_id"])
def test_agreeing_receipts_cannot_replace_expected_subject(field: str) -> None:
    receipts = {
        name: _validated_receipt(name, **{field: "another-subject"})
        for name in RECEIPT_NAMES
    }
    result = qualify(_join_input(receipts))
    assert result.result == "BLOCKED"
    assert {r.receipt for r in result.reasons if r.rule == 1} == set(RECEIPT_NAMES)


@pytest.mark.parametrize("field", ["macro_id", "packet_id"])
@pytest.mark.parametrize("value", [None, "", " ", 7, [], {}])
def test_expected_subject_must_be_nonempty_identifier(field: str, value: Any) -> None:
    inp = replace(_join_input(_full_receipts()), **{field: value})
    result = qualify(inp)
    assert result.result == "BLOCKED"
    _assert_never_authority(result)


@pytest.mark.parametrize("missing", ["macro_id", "packet_id"])
def test_expected_subject_arguments_are_required(missing: str) -> None:
    kwargs = dict(
        receipts=_full_receipts(), provenance=_provenance(),
        macro_id=MACRO_ID, packet_id=PACKET_ID,
    )
    del kwargs[missing]
    with pytest.raises(TypeError):
        JoinInput(**kwargs)


@pytest.mark.parametrize("name", RECEIPT_NAMES)
@pytest.mark.parametrize("field", ["macro_id", "packet_id"])
@pytest.mark.parametrize("value", [None, "", " ", 7])
def test_corrupted_receipt_subject_cannot_pass(
    name: ReceiptName, field: str, value: Any
) -> None:
    receipts = _full_receipts()
    receipt = receipts[name]
    # Defensive guard: ValidatedReceipt's payload is currently a mutable mapping.
    payload = dict(receipt.payload)
    payload[field] = value
    receipts[name] = replace(receipt, payload=payload)
    _assert_contract_blocked(receipts, name)


@pytest.mark.parametrize("name", RECEIPT_NAMES)
@pytest.mark.parametrize("field", ["macro_id", "packet_id"])
def test_missing_receipt_subject_cannot_be_inferred(name: ReceiptName, field: str) -> None:
    receipts = _full_receipts()
    receipt = receipts[name]
    payload = dict(receipt.payload)
    del payload[field]
    receipts[name] = replace(receipt, payload=payload)
    _assert_contract_blocked(receipts, name)


def test_schema_valid_coordinator_binding_cannot_fill_child_slot() -> None:
    receipts = _full_receipts()
    receipt = receipts["ExecutionBinding"]
    payload = dict(receipt.payload)
    del payload["packet_id"]  # Schema permits coordinator bindings; join requires a child.
    receipts["ExecutionBinding"] = validate_receipt(
        receipt.kind, json.dumps(payload).encode(), receipt.provenance
    )
    _assert_contract_blocked(receipts, "ExecutionBinding")


@pytest.mark.parametrize("name", RECEIPT_NAMES)
def test_wrong_validated_kind_is_rejected(name: ReceiptName) -> None:
    receipts = _full_receipts()
    other = "ScopeAuthority" if name in ("CanonicalWriter", "ExecutionBinding") else "CanonicalWriter"
    receipts[name] = receipts[other]
    _assert_contract_blocked(receipts, name)


@pytest.mark.parametrize("name", RECEIPT_NAMES)
@pytest.mark.parametrize("kind", ["execution_binding.v1", "unknown", None, []])
def test_wrong_kind_cannot_pass_even_with_expected_payload(name: ReceiptName, kind: Any) -> None:
    receipts = _full_receipts()
    receipts[name] = replace(receipts[name], kind=kind)
    _assert_contract_blocked(receipts, name)


@pytest.mark.parametrize(
    ("name", "other"),
    [(name, other) for name in _UPSTREAM_NAMES for other in _UPSTREAM_NAMES if name != other],
)
def test_wrong_validated_dispatch_receipt_type_is_rejected(
    name: ReceiptName, other: ReceiptName
) -> None:
    receipts = _full_receipts()
    receipts[name] = receipts[other]
    _assert_contract_blocked(receipts, name)


@pytest.mark.parametrize("name", RECEIPT_NAMES)
@pytest.mark.parametrize("missing", [False, True], ids=["null-slot", "absent-slot"])
def test_missing_mandatory_receipt_fails_closed(name: ReceiptName, missing: bool) -> None:
    receipts = _full_receipts()
    if missing:
        del receipts[name]
    else:
        receipts[name] = None
    _assert_contract_blocked(receipts, name)


@pytest.mark.parametrize("name", RECEIPT_NAMES)
def test_malformed_non_mapping_payload_blocks_without_raising(name: ReceiptName) -> None:
    receipts = _full_receipts()
    receipts[name] = "not-a-receipt"
    _assert_contract_blocked(receipts, name)


@pytest.mark.parametrize("name", RECEIPT_NAMES)
@pytest.mark.parametrize("payload", [None, "not-a-mapping", []])
def test_corrupted_validated_payload_blocks(name: ReceiptName, payload: Any) -> None:
    receipts = _full_receipts()
    receipts[name] = replace(receipts[name], payload=payload)
    _assert_contract_blocked(receipts, name)


@pytest.mark.parametrize("receipts", [None, "not-a-mapping", []])
def test_malformed_receipt_collection_blocks(receipts: Any) -> None:
    result = qualify(_join_input(receipts))
    assert result.result == "BLOCKED"
    _assert_never_authority(result)


@pytest.mark.parametrize(
    ("name", "changes", "rule"),
    [
        ("PolicyEligibility", {"dcp_status": "BLOCKED"}, 3),
        ("WorkflowLegality", {"transition_legal": False, "blockers": ["conflict"]}, 4),
        ("WorkflowLegality", {"transition_legal": True, "blockers": ["conflict"]}, 4),
        ("WorkflowLegality", {"transition_legal": None, "blockers": ["conflict"]}, 4),
        ("OperatorGate", {"required": True, "granted": None, "receipt_ref": "operator:ref"}, 5),
        ("OperatorGate", {"required": True, "granted": False, "receipt_ref": "operator:ref"}, 5),
        ("OperatorGate", {"required": True, "granted": True, "receipt_ref": None}, 5),
        ("CanonicalWriter", {"custody_state": "AMBIGUOUS"}, 6),
        ("CanonicalWriter", {"custody_state": "RELEASED"}, 6),
        ("DriftOverlap", {"drift_class": "CONFLICTING"}, 7),
        ("ScopeAuthority", {"scope_status": "BLOCKED"}, 8),
    ],
)
def test_validated_denial_cannot_be_widened(
    name: ReceiptName, changes: dict[str, Any], rule: int
) -> None:
    receipts = _full_receipts()
    receipts[name] = _validated_receipt(name, **changes)
    result = qualify(_join_input(receipts))
    assert result.result == "BLOCKED"
    assert any(r.rule == rule and r.receipt == name for r in result.reasons)
    _assert_never_authority(result)


@pytest.mark.parametrize(
    ("name", "changes"),
    [
        ("PolicyEligibility", {"dcp_status": "UNKNOWN"}),
        ("PolicyEligibility", {"dcp_status": "NOT_RUN"}),
        ("DriftOverlap", {"drift_class": "SUPERSET"}),
        ("DriftOverlap", {"drift_class": "UNKNOWN"}),
        ("ScopeAuthority", {"scope_status": "UNKNOWN"}),
        ("WorkflowLegality", {"transition_legal": None}),
        ("OperatorGate", {"required": None}),
    ],
)
def test_validated_uncertainty_needs_supervisor(
    name: ReceiptName, changes: dict[str, Any]
) -> None:
    receipts = _full_receipts()
    receipts[name] = _validated_receipt(name, **changes)
    result = qualify(_join_input(receipts))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(r.rule == 9 and r.receipt == name for r in result.reasons)
    _assert_never_authority(result)


@pytest.mark.parametrize("availability", ["PROPOSED", "UNKNOWN"])
def test_runner_not_proven_needs_supervisor(availability: str) -> None:
    receipts = _full_receipts()
    selection = dict(receipts["ExecutionBinding"].payload["selection"])
    selection["runner_availability"] = availability
    receipts["ExecutionBinding"] = _validated_receipt("ExecutionBinding", selection=selection)
    result = qualify(_join_input(receipts))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(r.rule == 9 and r.field == "runner_availability" for r in result.reasons)
    _assert_never_authority(result)


@pytest.mark.parametrize("authority", ["GRANTED", None, True])
def test_execution_binding_claiming_authority_blocks(authority: Any) -> None:
    receipts = _full_receipts()
    receipt = receipts["ExecutionBinding"]
    receipts["ExecutionBinding"] = replace(
        receipt, payload={**receipt.payload, "authority": authority}
    )
    result = qualify(_join_input(receipts))
    assert result.result == "BLOCKED"
    assert any(r.rule == 2 and r.field == "authority" for r in result.reasons)
    _assert_never_authority(result)


@pytest.mark.parametrize(
    ("name", "field"),
    [
        ("ScopeAuthority", "allowlist_digest"),
        ("WorkflowLegality", "blockers"),
        ("CanonicalWriter", "custody_state"),
        ("ExecutionBinding", "selection"),
        ("ExecutionBinding", "qualification_receipt_ref"),
        ("OperatorGate", "receipt_ref"),
    ],
)
def test_required_evidence_cannot_enter_through_validation_boundary(
    name: ReceiptName, field: str
) -> None:
    receipt = _full_receipts()[name]
    payload = dict(receipt.payload)
    del payload[field]
    with pytest.raises(ReceiptInvalid):
        validate_receipt(receipt.kind, json.dumps(payload).encode(), receipt.provenance)


def test_multiple_denials_and_uncertainty_stay_blocked() -> None:
    receipts = _full_receipts()
    receipts["PolicyEligibility"] = _validated_receipt("PolicyEligibility", dcp_status="BLOCKED")
    receipts["DriftOverlap"] = _validated_receipt("DriftOverlap", drift_class="UNKNOWN")
    result = qualify(_join_input(receipts))
    assert result.result == "BLOCKED"
    assert {r.rule for r in result.reasons} == {3, 9}
    _assert_never_authority(result)
