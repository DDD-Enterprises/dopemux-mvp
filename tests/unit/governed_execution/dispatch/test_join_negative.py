"""Negative-path tests for the W02 derived DispatchQualification join.

One test per MACRO proof obligation: a missing receipt fails closed to
BLOCKED, a denial cannot be widened by any other receipt, a Task
Orchestrator illegality cannot be overridden, an operator-gated action
cannot self-authorize, an ExecutionBinding is never authorization by
itself, and genuine uncertainty (never a denial) maps to
NEEDS_SUPERVISOR rather than DISPATCHABLE.
"""
from __future__ import annotations

import pytest

from dopemux.governed_execution.dispatch import (
    RECEIPT_NAMES,
    DispatchQualification,
    JoinInput,
    Provenance,
    ReceiptName,
    qualify,
)


def _full_receipts() -> dict[str, dict[str, object] | None]:
    """A complete, all-clear set of seven receipt payloads."""
    return {
        "ScopeAuthority": {"scope_status": "PASS", "allowlist_digest": "a" * 64},
        "WorkflowLegality": {"transition_legal": True, "blockers": []},
        "PolicyEligibility": {"dcp_status": "PASS"},
        "CanonicalWriter": {"custody_state": "HELD"},
        "ExecutionBinding": {
            "authority": "NONE",
            "selection": {"runner_availability": "PROVEN"},
        },
        "OperatorGate": {"required": False, "receipt_ref": None, "granted": None},
        "DriftOverlap": {"drift_class": "IDENTICAL"},
    }


def _provenance() -> Provenance:
    return Provenance(
        verified_by="w02-test",
        verified_at="2026-09-11T00:00:00Z",
        schema_set_digest="0" * 64,
    )


def _assert_never_authority(result: DispatchQualification) -> None:
    assert result.authority == "NONE"
    assert result.is_execution_authority is False


# --- Rule 1: any mandatory receipt absent -> BLOCKED -----------------------


@pytest.mark.parametrize("missing", list(RECEIPT_NAMES))
def test_missing_mandatory_receipt_fails_closed(missing: ReceiptName) -> None:
    receipts = _full_receipts()
    receipts[missing] = None
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(r.rule == 1 and r.receipt == missing for r in result.reasons)
    _assert_never_authority(result)


@pytest.mark.parametrize("malformed_receipt", list(RECEIPT_NAMES))
def test_malformed_non_mapping_payload_blocks_without_raising(
    malformed_receipt: ReceiptName,
) -> None:
    receipts = _full_receipts()
    receipts[malformed_receipt] = "not-a-dict"  # type: ignore[assignment]
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(r.rule == 1 and r.receipt == malformed_receipt for r in result.reasons)
    _assert_never_authority(result)


# --- Rule 2: ExecutionBinding is factual input, never authorization --------


def test_execution_binding_claiming_authority_blocks() -> None:
    receipts = _full_receipts()
    receipts["ExecutionBinding"] = {
        "authority": "GRANTED",
        "selection": {"runner_availability": "PROVEN"},
    }
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(
        r.rule == 2 and r.receipt == "ExecutionBinding" and r.field == "authority"
        for r in result.reasons
    )
    _assert_never_authority(result)


# --- Rule 3: a DCP denial cannot be widened to DISPATCHABLE ----------------


def test_dcp_denial_blocks_with_every_other_receipt_perfect() -> None:
    receipts = _full_receipts()
    receipts["PolicyEligibility"] = {"dcp_status": "BLOCKED"}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(r.rule == 3 and r.receipt == "PolicyEligibility" for r in result.reasons)
    _assert_never_authority(result)


# --- Rule 4: a Task Orchestrator illegality cannot be overridden -----------


def test_workflow_illegality_blocks_with_every_other_receipt_perfect() -> None:
    receipts = _full_receipts()
    receipts["WorkflowLegality"] = {"transition_legal": False, "blockers": ["conflict"]}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(r.rule == 4 and r.receipt == "WorkflowLegality" for r in result.reasons)
    _assert_never_authority(result)


# --- Rule 5: an operator-gated action cannot self-authorize ----------------


@pytest.mark.parametrize("granted", [None, False])
def test_operator_gate_required_and_not_granted_cannot_self_authorize(
    granted: bool | None,
) -> None:
    receipts = _full_receipts()
    receipts["OperatorGate"] = {
        "required": True,
        "receipt_ref": "operator-gate-receipt-123",
        "granted": granted,
    }
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(r.rule == 5 and r.receipt == "OperatorGate" for r in result.reasons)
    _assert_never_authority(result)


# --- Rule 6: writer custody must be held, not ambiguous or released --------


@pytest.mark.parametrize("custody_state", ["AMBIGUOUS", "RELEASED"])
def test_writer_custody_not_held_blocks(custody_state: str) -> None:
    receipts = _full_receipts()
    receipts["CanonicalWriter"] = {"custody_state": custody_state}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(r.rule == 6 and r.receipt == "CanonicalWriter" for r in result.reasons)
    _assert_never_authority(result)


# --- Rule 7: conflicting drift blocks ---------------------------------------


def test_conflicting_drift_blocks() -> None:
    receipts = _full_receipts()
    receipts["DriftOverlap"] = {"drift_class": "CONFLICTING"}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(r.rule == 7 and r.receipt == "DriftOverlap" for r in result.reasons)
    _assert_never_authority(result)


# --- Rule 8: scope denial blocks --------------------------------------------


def test_scope_denial_blocks() -> None:
    receipts = _full_receipts()
    receipts["ScopeAuthority"] = {"scope_status": "BLOCKED", "allowlist_digest": "b" * 64}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    assert any(r.rule == 8 and r.receipt == "ScopeAuthority" for r in result.reasons)
    _assert_never_authority(result)


# --- Rule 9: uncertainty (never a denial) maps to NEEDS_SUPERVISOR ---------


def test_dcp_unknown_needs_supervisor() -> None:
    receipts = _full_receipts()
    receipts["PolicyEligibility"] = {"dcp_status": "UNKNOWN"}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(r.rule == 9 and r.receipt == "PolicyEligibility" for r in result.reasons)
    _assert_never_authority(result)


def test_dcp_not_run_needs_supervisor() -> None:
    receipts = _full_receipts()
    receipts["PolicyEligibility"] = {"dcp_status": "NOT_RUN"}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(r.rule == 9 and r.receipt == "PolicyEligibility" for r in result.reasons)
    _assert_never_authority(result)


def test_runner_availability_proposed_needs_supervisor() -> None:
    receipts = _full_receipts()
    receipts["ExecutionBinding"] = {
        "authority": "NONE",
        "selection": {"runner_availability": "PROPOSED"},
    }
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(
        r.rule == 9 and r.receipt == "ExecutionBinding" and r.field == "runner_availability"
        for r in result.reasons
    )
    _assert_never_authority(result)


def test_drift_superset_needs_supervisor() -> None:
    receipts = _full_receipts()
    receipts["DriftOverlap"] = {"drift_class": "SUPERSET"}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(r.rule == 9 and r.receipt == "DriftOverlap" for r in result.reasons)
    _assert_never_authority(result)


def test_scope_unknown_needs_supervisor() -> None:
    receipts = _full_receipts()
    receipts["ScopeAuthority"] = {"scope_status": "UNKNOWN"}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(r.rule == 9 and r.receipt == "ScopeAuthority" for r in result.reasons)
    _assert_never_authority(result)


def test_workflow_legality_unresolved_needs_supervisor() -> None:
    receipts = _full_receipts()
    receipts["WorkflowLegality"] = {"transition_legal": None, "blockers": []}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(r.rule == 9 and r.receipt == "WorkflowLegality" for r in result.reasons)
    _assert_never_authority(result)


def test_operator_gate_required_unspecified_needs_supervisor() -> None:
    receipts = _full_receipts()
    receipts["OperatorGate"] = {"required": None, "receipt_ref": None, "granted": None}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "NEEDS_SUPERVISOR"
    assert any(r.rule == 9 and r.receipt == "OperatorGate" for r in result.reasons)
    _assert_never_authority(result)


# --- Multiple simultaneous denials still resolve to BLOCKED, never lifted --


def test_multiple_denials_and_uncertainty_stay_blocked() -> None:
    receipts = _full_receipts()
    receipts["PolicyEligibility"] = {"dcp_status": "BLOCKED"}
    receipts["DriftOverlap"] = {"drift_class": "UNKNOWN"}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "BLOCKED"
    rules = {r.rule for r in result.reasons}
    assert 3 in rules
    assert 9 in rules
    _assert_never_authority(result)
