"""Partial-block semantics and macro_status derivation tests (W05).

Covers the named MACRO W05 behavioural fixture as exact literals, the
all-PASS and all-non-PASS macro_status boundaries, a global stop override,
and authority non-transfer (a PASS sibling can never change a BLOCKED
member's recorded status).
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from dopemux.governed_execution.join.evaluate import (
    _MACRO_STATUS_VALUES,
    derive_macro_status,
    evaluate_all,
    next_legal_action,
)
from dopemux.governed_execution.join.types import JoinDecl, JoinResult, ReturnRef, WorkstreamResult

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ENUMS_SCHEMA = _REPO_ROOT / "schemas" / "governed_execution" / "enums.v1.schema.json"


def _ws(workstream_id: str, status: str) -> WorkstreamResult:
    return WorkstreamResult(
        workstream_id=workstream_id,
        status=status,
        subject_sha="NONE",
        return_ref=ReturnRef(path=f"artifacts/{workstream_id}.json", sha256="0" * 64),
    )


def test_macro_status_matches_enums_schema() -> None:
    schema = json.loads(_ENUMS_SCHEMA.read_text(encoding="ascii"))
    expected = schema["definitions"]["macro_status"]["enum"]
    # derive_macro_status only ever returns a value from this closed set
    # (or a caller-validated global_stop override drawn from the same set).
    assert list(_MACRO_STATUS_VALUES) == expected


def test_named_macro_w05_fixture_exact_literals() -> None:
    """MACRO W05: W01=PASS, W02=BLOCKED, W03=PASS, W04=PASS.

    joins J_A=ALL_REQUIRED[W01], J_PARALLEL=ALL_REQUIRED[W02,W03,W04].
    Asserted as the exact literals from the task packet invariants.
    """
    results = (_ws("W01", "PASS"), _ws("W02", "BLOCKED"), _ws("W03", "PASS"), _ws("W04", "PASS"))
    decls = (
        JoinDecl(join_id="J_A", join_type="ALL_REQUIRED", requires=("W01",)),
        JoinDecl(join_id="J_PARALLEL", join_type="ALL_REQUIRED", requires=("W02", "W03", "W04")),
    )

    join_results = evaluate_all(decls, results)

    assert join_results == (
        JoinResult(
            join_id="J_A",
            join_type="ALL_REQUIRED",
            satisfied=True,
            affected_workstreams=(),
            unaffected_workstreams=("W01",),
        ),
        JoinResult(
            join_id="J_PARALLEL",
            join_type="ALL_REQUIRED",
            satisfied=False,
            affected_workstreams=("W02",),
            unaffected_workstreams=("W03", "W04"),
        ),
    )

    macro_status = derive_macro_status(results, join_results)
    assert macro_status == "PARTIAL_BLOCKED"

    action = next_legal_action(results, macro_status)
    assert action == "RESOLVE_W02"


def test_all_pass_and_all_joins_satisfied_yields_complete() -> None:
    results = (_ws("W01", "PASS"), _ws("W02", "PASS"))
    decls = (JoinDecl(join_id="J", join_type="ALL_REQUIRED", requires=("W01", "W02")),)
    join_results = evaluate_all(decls, results)
    macro_status = derive_macro_status(results, join_results)
    assert macro_status == "PASS_IMPLEMENTATION_PROGRAM_COMPLETE"
    assert next_legal_action(results, macro_status) == "RETURN_TO_TEAM_LEAD"


def test_all_non_pass_yields_blocked() -> None:
    results = (_ws("W01", "BLOCKED"), _ws("W02", "FAIL"))
    decls = (JoinDecl(join_id="J", join_type="ALL_REQUIRED", requires=("W01", "W02")),)
    join_results = evaluate_all(decls, results)
    macro_status = derive_macro_status(results, join_results)
    assert macro_status == "BLOCKED"


def test_global_stop_override() -> None:
    results = (_ws("W01", "PASS"), _ws("W02", "PASS"))
    join_results: tuple[JoinResult, ...] = ()
    macro_status = derive_macro_status(results, join_results, global_stop="ARCHITECTURE_INVARIANT_BROKEN")
    assert macro_status == "ARCHITECTURE_INVARIANT_BROKEN"


def test_global_stop_invalid_value_raises() -> None:
    results = (_ws("W01", "PASS"),)
    join_results: tuple[JoinResult, ...] = ()
    with pytest.raises(ValueError):
        derive_macro_status(results, join_results, global_stop="NOT_A_MACRO_STATUS")


def test_pass_sibling_never_changes_blocked_members_status() -> None:
    """Authority non-transfer: a PASS sibling can never make a BLOCKED
    member's recorded status green, and the evaluator cannot even attempt
    to mutate the caller's input (WorkstreamResult is a frozen dataclass)."""
    w02 = _ws("W02", "BLOCKED")
    results = (_ws("W01", "PASS"), w02, _ws("W03", "PASS"))
    decls = (
        JoinDecl(join_id="J_A", join_type="ALL_REQUIRED", requires=("W01",)),
        JoinDecl(join_id="J_PARALLEL", join_type="ALL_REQUIRED", requires=("W02", "W03")),
    )

    evaluate_all(decls, results)

    # The input tuple and its members are unchanged after evaluation.
    assert w02.status == "BLOCKED"
    assert results[1] is w02

    with pytest.raises(dataclasses.FrozenInstanceError):
        w02.status = "PASS"  # type: ignore[misc]
