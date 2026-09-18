"""Purity and enum-fidelity tests for the W02 derived DispatchQualification join.

qualify() must never touch the filesystem or a subprocess, must be
deterministic (same input -> same output), must never claim execution
authority, and its three output values must equal the schema's
dispatch_qualification enum exactly.
"""
from __future__ import annotations

import builtins
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from dopemux.governed_execution.dispatch import (
    DISPATCH_QUALIFICATION_VALUES,
    JoinInput,
    Provenance,
    qualify,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
ENUMS_SCHEMA_PATH = REPO_ROOT / "schemas" / "governed_execution" / "enums.v1.schema.json"


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


def test_qualify_is_pure_same_input_yields_equal_output() -> None:
    inp = JoinInput(receipts=_full_receipts(), provenance=_provenance())
    first = qualify(inp)
    second = qualify(inp)
    assert first == second
    assert first.reasons == second.reasons


def test_qualify_is_pure_across_fresh_equal_inputs() -> None:
    first = qualify(JoinInput(receipts=_full_receipts(), provenance=_provenance()))
    second = qualify(JoinInput(receipts=_full_receipts(), provenance=_provenance()))
    assert first == second


def test_reasons_are_sorted_by_rule_then_receipt_and_deterministic() -> None:
    receipts = _full_receipts()
    receipts["ScopeAuthority"] = None
    receipts["PolicyEligibility"] = {"dcp_status": "BLOCKED"}
    receipts["DriftOverlap"] = {"drift_class": "UNKNOWN"}
    inp = JoinInput(receipts=receipts, provenance=_provenance())

    first = qualify(inp)
    second = qualify(inp)
    assert first == second

    assert [(r.rule, r.receipt) for r in first.reasons] == [
        (1, "ScopeAuthority"),
        (3, "PolicyEligibility"),
        (9, "DriftOverlap"),
    ]
    assert first.result == "BLOCKED"


def test_qualify_never_opens_a_file_or_spawns_a_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_open(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("qualify() must never open a file")

    def _raise_run(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("qualify() must never spawn a subprocess")

    monkeypatch.setattr(builtins, "open", _raise_open)
    monkeypatch.setattr(subprocess, "run", _raise_run)

    inp = JoinInput(receipts=_full_receipts(), provenance=_provenance())
    result = qualify(inp)
    assert result.result == "DISPATCHABLE"


def test_dispatch_qualification_enum_matches_schema_exactly() -> None:
    schema = json.loads(ENUMS_SCHEMA_PATH.read_text(encoding="ascii"))
    schema_enum = schema["definitions"]["dispatch_qualification"]["enum"]
    assert list(DISPATCH_QUALIFICATION_VALUES) == schema_enum
    assert len(DISPATCH_QUALIFICATION_VALUES) == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"PolicyEligibility": {"dcp_status": "BLOCKED"}},
        {"PolicyEligibility": {"dcp_status": "UNKNOWN"}},
        {"ExecutionBinding": None},
        {"ExecutionBinding": {"authority": "GRANTED", "selection": {"runner_availability": "PROVEN"}}},
        {"OperatorGate": {"required": True, "receipt_ref": "ref", "granted": False}},
        {"CanonicalWriter": {"custody_state": "AMBIGUOUS"}},
        {"DriftOverlap": {"drift_class": "CONFLICTING"}},
        {"DriftOverlap": {"drift_class": "SUPERSET"}},
        {"ScopeAuthority": "not-a-dict"},
    ],
)
def test_result_never_claims_execution_authority(overrides: dict[str, object]) -> None:
    receipts = _full_receipts()
    receipts.update(overrides)
    result = qualify(JoinInput(receipts=receipts, provenance=_provenance()))
    assert result.authority == "NONE"
    assert result.is_execution_authority is False
    assert result.result in DISPATCH_QUALIFICATION_VALUES
