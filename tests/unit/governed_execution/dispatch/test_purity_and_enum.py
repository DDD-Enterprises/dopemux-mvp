"""Dispatch remains pure, deterministic, advisory, and faithful to its enum."""
from __future__ import annotations

import builtins
import hashlib
import json
import os
import socket
import subprocess
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator

from dopemux.governed_execution.dispatch import DISPATCH_QUALIFICATION_VALUES, qualify
from tests.unit.governed_execution.dispatch.test_join_positive import (
    _full_receipts,
    _join_input,
    _validated_receipt,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
ENUMS_SCHEMA_PATH = REPO_ROOT / "schemas/governed_execution/enums.v1.schema.json"


def test_qualify_is_pure_same_input_yields_equal_output() -> None:
    inp = _join_input(_full_receipts())
    before = deepcopy(inp)
    first = qualify(inp)
    second = qualify(inp)
    assert first == second
    assert first.result == "DISPATCHABLE"
    assert inp == before


def test_qualify_is_pure_across_fresh_equal_inputs() -> None:
    first = qualify(_join_input(_full_receipts()))
    second = qualify(_join_input(_full_receipts()))
    assert first == second


def test_reasons_are_sorted_by_rule_then_receipt_and_deterministic() -> None:
    receipts = _full_receipts()
    receipts["ScopeAuthority"] = None
    receipts["PolicyEligibility"] = _validated_receipt("PolicyEligibility", dcp_status="BLOCKED")
    receipts["DriftOverlap"] = _validated_receipt("DriftOverlap", drift_class="UNKNOWN")
    inp = _join_input(receipts)

    first = qualify(inp)
    second = qualify(inp)
    reversed_input = _join_input(dict(reversed(list(receipts.items()))))
    assert first == second == qualify(reversed_input)
    assert [(r.rule, r.receipt) for r in first.reasons] == [
        (1, "ScopeAuthority"),
        (3, "PolicyEligibility"),
        (9, "DriftOverlap"),
    ]
    assert first.result == "BLOCKED"


@pytest.mark.parametrize("invalid", [False, True], ids=["dispatchable", "blocked"])
def test_qualify_has_no_io_clock_digest_or_schema_validation(
    monkeypatch: pytest.MonkeyPatch, invalid: bool
) -> None:
    # Upstream validation performs I/O. Finish it before guarding the pure join.
    receipts = _full_receipts()
    if invalid:
        receipts["ScopeAuthority"] = dict(receipts["ScopeAuthority"].payload)
    inp = _join_input(receipts)

    def forbidden(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("qualify() must only read its supplied receipt values")

    with monkeypatch.context() as patch:
        for target, attr in (
            (builtins, "open"),
            (Path, "open"),
            (Path, "read_bytes"),
            (Path, "read_text"),
            (os, "open"),
            (subprocess, "run"),
            (subprocess, "Popen"),
            (socket, "socket"),
            (time, "time"),
            (time, "monotonic"),
            (hashlib, "sha256"),
            (Draft7Validator, "iter_errors"),
        ):
            patch.setattr(target, attr, forbidden)
        result = qualify(inp)
    assert result.result == ("BLOCKED" if invalid else "DISPATCHABLE")
    assert result.authority == "NONE"


def test_dispatch_qualification_enum_matches_schema_exactly() -> None:
    schema = json.loads(ENUMS_SCHEMA_PATH.read_text(encoding="ascii"))
    schema_enum = schema["definitions"]["dispatch_qualification"]["enum"]
    assert list(DISPATCH_QUALIFICATION_VALUES) == schema_enum
    assert len(DISPATCH_QUALIFICATION_VALUES) == 3


@pytest.mark.parametrize(
    ("name", "changes"),
    [
        ("PolicyEligibility", {"dcp_status": "PASS"}),
        ("PolicyEligibility", {"dcp_status": "BLOCKED"}),
        ("PolicyEligibility", {"dcp_status": "UNKNOWN"}),
        ("OperatorGate", {"required": True, "granted": False, "receipt_ref": "operator:ref"}),
        ("CanonicalWriter", {"custody_state": "AMBIGUOUS"}),
        ("DriftOverlap", {"drift_class": "CONFLICTING"}),
        ("DriftOverlap", {"drift_class": "SUPERSET"}),
    ],
)
def test_result_never_claims_execution_authority(name: str, changes: dict[str, Any]) -> None:
    receipts = _full_receipts()
    receipts[name] = _validated_receipt(name, **changes)
    result = qualify(_join_input(receipts))
    assert result.authority == "NONE"
    assert result.is_execution_authority is False
    assert result.result in DISPATCH_QUALIFICATION_VALUES
