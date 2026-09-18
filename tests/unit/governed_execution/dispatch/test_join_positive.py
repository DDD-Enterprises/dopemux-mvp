"""Positive-path tests for the W02 derived DispatchQualification join."""
from __future__ import annotations

import pytest

from dopemux.governed_execution.dispatch import JoinInput, Provenance, qualify


def _full_receipts() -> dict[str, dict[str, object]]:
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


def test_full_seven_receipt_fixture_is_dispatchable() -> None:
    result = qualify(JoinInput(receipts=_full_receipts(), provenance=_provenance()))
    assert result.result == "DISPATCHABLE"
    assert result.reasons == ()
    assert result.authority == "NONE"
    assert result.is_execution_authority is False


@pytest.mark.parametrize("drift_class", ["IDENTICAL", "SUBSET", "COMPATIBLE"])
def test_compatible_drift_classes_remain_dispatchable(drift_class: str) -> None:
    receipts = _full_receipts()
    receipts["DriftOverlap"] = {"drift_class": drift_class}
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.result == "DISPATCHABLE"
    assert result.reasons == ()
    assert result.authority == "NONE"
    assert result.is_execution_authority is False
