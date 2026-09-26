"""Tests for the six fixed join semantics (W05).

For each join_type: at least one satisfied case, and at least two
unsatisfied cases where one includes an UNKNOWN member (UNKNOWN never
counts as PASS). QUORUM additionally covers the == and < quorum boundary.
ORDERED additionally covers early-failure "not evaluated" propagation.
CONDITIONAL additionally covers grammar acceptance and ConditionError.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.governed_execution.join.evaluate import evaluate_join
from dopemux.governed_execution.join.types import ConditionError, JoinDecl, JoinType, ReturnRef, WorkstreamResult

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ENUMS_SCHEMA = _REPO_ROOT / "schemas" / "governed_execution" / "enums.v1.schema.json"


def _ws(workstream_id: str, status: str) -> WorkstreamResult:
    return WorkstreamResult(
        workstream_id=workstream_id,
        status=status,
        subject_sha="NONE",
        return_ref=ReturnRef(path=f"artifacts/{workstream_id}.json", sha256="0" * 64),
    )


def _by_id(*results: WorkstreamResult) -> dict[str, WorkstreamResult]:
    return {result.workstream_id: result for result in results}


def test_join_type_matches_enums_schema() -> None:
    schema = json.loads(_ENUMS_SCHEMA.read_text(encoding="ascii"))
    expected = schema["definitions"]["join_type"]["enum"]
    assert [member.value for member in JoinType] == expected


# --- ALL_REQUIRED ---------------------------------------------------------


def test_all_required_satisfied() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "PASS"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ALL_REQUIRED.value, requires=("A", "B"))
    result = evaluate_join(decl, results)
    assert result.satisfied is True
    assert result.affected_workstreams == ()
    assert result.unaffected_workstreams == ("A", "B")


def test_all_required_unsatisfied_one_blocked() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "BLOCKED"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ALL_REQUIRED.value, requires=("A", "B"))
    result = evaluate_join(decl, results)
    assert result.satisfied is False
    assert result.affected_workstreams == ("B",)


def test_all_required_unsatisfied_unknown_member() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "UNKNOWN"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ALL_REQUIRED.value, requires=("A", "B"))
    result = evaluate_join(decl, results)
    assert result.satisfied is False
    assert "B" in result.affected_workstreams


# --- ANY_ONE ---------------------------------------------------------------


def test_any_one_satisfied() -> None:
    results = _by_id(_ws("A", "BLOCKED"), _ws("B", "PASS"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ANY_ONE.value, requires=("A", "B"))
    result = evaluate_join(decl, results)
    assert result.satisfied is True
    assert result.unaffected_workstreams == ("B",)


def test_any_one_unsatisfied_none_pass() -> None:
    results = _by_id(_ws("A", "BLOCKED"), _ws("B", "FAIL"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ANY_ONE.value, requires=("A", "B"))
    result = evaluate_join(decl, results)
    assert result.satisfied is False


def test_any_one_unsatisfied_unknown_member() -> None:
    results = _by_id(_ws("A", "UNKNOWN"), _ws("B", "BLOCKED"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ANY_ONE.value, requires=("A", "B"))
    result = evaluate_join(decl, results)
    assert result.satisfied is False
    assert result.unaffected_workstreams == ()


# --- QUORUM ------------------------------------------------------------


def test_quorum_satisfied_at_boundary() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "PASS"), _ws("C", "BLOCKED"))
    decl = JoinDecl(join_id="J", join_type=JoinType.QUORUM.value, requires=("A", "B", "C"), quorum=2)
    result = evaluate_join(decl, results)
    assert result.satisfied is True


def test_quorum_unsatisfied_below_boundary() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "BLOCKED"), _ws("C", "BLOCKED"))
    decl = JoinDecl(join_id="J", join_type=JoinType.QUORUM.value, requires=("A", "B", "C"), quorum=2)
    result = evaluate_join(decl, results)
    assert result.satisfied is False


def test_quorum_unsatisfied_unknown_member() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "UNKNOWN"), _ws("C", "BLOCKED"))
    decl = JoinDecl(join_id="J", join_type=JoinType.QUORUM.value, requires=("A", "B", "C"), quorum=2)
    result = evaluate_join(decl, results)
    assert result.satisfied is False


def test_quorum_invalid_quorum_raises() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "PASS"))
    decl = JoinDecl(join_id="J", join_type=JoinType.QUORUM.value, requires=("A", "B"), quorum=None)
    with pytest.raises(ValueError):
        evaluate_join(decl, results)
    decl_zero = JoinDecl(join_id="J", join_type=JoinType.QUORUM.value, requires=("A", "B"), quorum=0)
    with pytest.raises(ValueError):
        evaluate_join(decl_zero, results)
    decl_too_high = JoinDecl(join_id="J", join_type=JoinType.QUORUM.value, requires=("A", "B"), quorum=3)
    with pytest.raises(ValueError):
        evaluate_join(decl_too_high, results)


# --- ORDERED -----------------------------------------------------------


def test_ordered_satisfied() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "PASS"), _ws("C", "PASS"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ORDERED.value, requires=("A", "B", "C"))
    result = evaluate_join(decl, results)
    assert result.satisfied is True
    assert result.unaffected_workstreams == ("A", "B", "C")
    assert result.affected_workstreams == ()


def test_ordered_early_failure_marks_later_not_evaluated() -> None:
    # B and C are actually PASS, but A fails first: both must be reported
    # as affected ("not evaluated"), never silently counted as unaffected.
    results = _by_id(_ws("A", "BLOCKED"), _ws("B", "PASS"), _ws("C", "PASS"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ORDERED.value, requires=("A", "B", "C"))
    result = evaluate_join(decl, results)
    assert result.satisfied is False
    assert result.affected_workstreams == ("A", "B", "C")
    assert result.unaffected_workstreams == ()


def test_ordered_unsatisfied_unknown_member_blocks_later() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "UNKNOWN"), _ws("C", "PASS"))
    decl = JoinDecl(join_id="J", join_type=JoinType.ORDERED.value, requires=("A", "B", "C"))
    result = evaluate_join(decl, results)
    assert result.satisfied is False
    assert result.unaffected_workstreams == ("A",)
    assert result.affected_workstreams == ("B", "C")


# --- OPTIONAL_SIBLING ----------------------------------------------------


def test_optional_sibling_satisfied_optional_member_blocked() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "BLOCKED"))
    decl = JoinDecl(
        join_id="J",
        join_type=JoinType.OPTIONAL_SIBLING.value,
        requires=("A", "B"),
        condition="optional:B",
    )
    result = evaluate_join(decl, results)
    assert result.satisfied is True
    # affected/unaffected are still status-based over every member.
    assert result.affected_workstreams == ("B",)
    assert result.unaffected_workstreams == ("A",)


def test_optional_sibling_unsatisfied_required_member_blocked() -> None:
    results = _by_id(_ws("A", "BLOCKED"), _ws("B", "PASS"))
    decl = JoinDecl(
        join_id="J",
        join_type=JoinType.OPTIONAL_SIBLING.value,
        requires=("A", "B"),
        condition="optional:B",
    )
    result = evaluate_join(decl, results)
    assert result.satisfied is False


def test_optional_sibling_unsatisfied_unknown_required_member() -> None:
    results = _by_id(_ws("A", "UNKNOWN"), _ws("B", "PASS"))
    decl = JoinDecl(
        join_id="J",
        join_type=JoinType.OPTIONAL_SIBLING.value,
        requires=("A", "B"),
        condition="optional:B",
    )
    result = evaluate_join(decl, results)
    assert result.satisfied is False


def test_optional_sibling_malformed_condition_raises() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "PASS"))
    decl = JoinDecl(
        join_id="J", join_type=JoinType.OPTIONAL_SIBLING.value, requires=("A", "B"), condition="B"
    )
    with pytest.raises(ConditionError):
        evaluate_join(decl, results)


# --- CONDITIONAL ---------------------------------------------------------


def test_conditional_satisfied_and_grammar() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "PASS"))
    decl = JoinDecl(
        join_id="J",
        join_type=JoinType.CONDITIONAL.value,
        requires=("A", "B"),
        condition="A==PASS and B==PASS",
    )
    result = evaluate_join(decl, results)
    assert result.satisfied is True


def test_conditional_unsatisfied_or_grammar() -> None:
    results = _by_id(_ws("A", "BLOCKED"), _ws("B", "BLOCKED"))
    decl = JoinDecl(
        join_id="J",
        join_type=JoinType.CONDITIONAL.value,
        requires=("A", "B"),
        condition="A==PASS or B==PASS",
    )
    result = evaluate_join(decl, results)
    assert result.satisfied is False


def test_conditional_unsatisfied_unknown_member_status() -> None:
    results = _by_id(_ws("A", "UNKNOWN"), _ws("B", "PASS"))
    decl = JoinDecl(
        join_id="J", join_type=JoinType.CONDITIONAL.value, requires=("A", "B"), condition="A==PASS"
    )
    result = evaluate_join(decl, results)
    assert result.satisfied is False


def test_conditional_rejects_nesting_parentheses() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "PASS"))
    decl = JoinDecl(
        join_id="J",
        join_type=JoinType.CONDITIONAL.value,
        requires=("A", "B"),
        condition="(A==PASS)",
    )
    with pytest.raises(ConditionError):
        evaluate_join(decl, results)


def test_conditional_rejects_mixed_and_or() -> None:
    results = _by_id(_ws("A", "PASS"), _ws("B", "PASS"), _ws("C", "PASS"))
    decl = JoinDecl(
        join_id="J",
        join_type=JoinType.CONDITIONAL.value,
        requires=("A", "B", "C"),
        condition="A==PASS and B==PASS or C==PASS",
    )
    with pytest.raises(ConditionError):
        evaluate_join(decl, results)


def test_conditional_rejects_unknown_id() -> None:
    results = _by_id(_ws("A", "PASS"))
    decl = JoinDecl(
        join_id="J", join_type=JoinType.CONDITIONAL.value, requires=("A",), condition="Z==PASS"
    )
    with pytest.raises(ConditionError):
        evaluate_join(decl, results)


def test_conditional_missing_condition_raises() -> None:
    results = _by_id(_ws("A", "PASS"))
    decl = JoinDecl(join_id="J", join_type=JoinType.CONDITIONAL.value, requires=("A",), condition=None)
    with pytest.raises(ConditionError):
        evaluate_join(decl, results)
