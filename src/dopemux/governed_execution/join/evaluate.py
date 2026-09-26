"""Join-type evaluation, partial-block semantics and macro_status derivation.

The evaluator never transfers authority between workstreams: a blocked
child can never be made green by a sibling's PASS (MACRO I03, I14, I16,
I18). All join semantics below are fixed by the W05 task packet invariants
and must not be redefined.
"""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .types import ConditionError, JoinDecl, JoinResult, JoinType, WorkstreamResult

_PASS = "PASS"

# Mirrors schemas/governed_execution/enums.v1.schema.json#/definitions/macro_status.
# Values and order are asserted equal to that schema definition by
# test_partial_block.py::test_macro_status_matches_enums_schema, so this
# module performs no filesystem read.
_MACRO_STATUS_VALUES: tuple[str, ...] = (
    "PASS_IMPLEMENTATION_PROGRAM_COMPLETE",
    "PARTIAL_BLOCKED",
    "BLOCKED",
    "BLOCKED_TEAM_LEAD_ROUTE_UNPROVEN",
    "NO_LEGAL_EXECUTION_ROUTE",
    "GLOBAL_AUTHORITY_CONFLICT",
    "ARCHITECTURE_INVARIANT_BROKEN",
    "NO_VALID_ROLLBACK_FOR_REQUIRED_MUTATION",
    "OPERATOR_GATE_REQUIRED_FOR_ALL_REMAINING_WORK",
)

_CONDITION_TERM = re.compile(r"^([A-Za-z0-9_]+)==([A-Za-z0-9_]+)$")


def _split_by_status(
    members: Sequence[str], results_by_id: Mapping[str, WorkstreamResult]
) -> tuple[list[str], list[str]]:
    """Generic affected/unaffected split: PASS is unaffected, everything else
    (including UNKNOWN, which never counts as PASS) is affected."""
    affected: list[str] = []
    unaffected: list[str] = []
    for member in members:
        if results_by_id[member].status == _PASS:
            unaffected.append(member)
        else:
            affected.append(member)
    return sorted(affected), sorted(unaffected)


def _evaluate_ordered(
    decl: JoinDecl, results_by_id: Mapping[str, WorkstreamResult]
) -> JoinResult:
    affected: list[str] = []
    unaffected: list[str] = []
    blocked = False
    for member in decl.requires:
        if blocked:
            # An earlier required id was non-PASS: every later id is "not
            # evaluated" and is reported as affected regardless of its own
            # recorded status.
            affected.append(member)
            continue
        if results_by_id[member].status == _PASS:
            unaffected.append(member)
        else:
            affected.append(member)
            blocked = True
    return JoinResult(
        join_id=decl.join_id,
        join_type=decl.join_type,
        satisfied=not blocked,
        affected_workstreams=tuple(sorted(affected)),
        unaffected_workstreams=tuple(sorted(unaffected)),
    )


def _validate_quorum(decl: JoinDecl) -> int:
    quorum = decl.quorum
    if quorum is None or not (1 <= quorum <= len(decl.requires)):
        raise ValueError(
            f"join {decl.join_id!r}: quorum must satisfy 1 <= quorum <= "
            f"len(requires) ({len(decl.requires)}); got {quorum!r}"
        )
    return quorum


def _parse_optional(condition: str | None) -> frozenset[str]:
    if condition is None:
        return frozenset()
    prefix = "optional:"
    if not condition.startswith(prefix):
        raise ConditionError(
            f"OPTIONAL_SIBLING condition must start with {prefix!r}: {condition!r}"
        )
    raw_ids = condition[len(prefix) :].split(",")
    ids = [raw.strip() for raw in raw_ids]
    if not all(ids):
        raise ConditionError(f"OPTIONAL_SIBLING condition has an empty id: {condition!r}")
    return frozenset(ids)


def _parse_condition_terms(
    condition: str, known_ids: Mapping[str, WorkstreamResult]
) -> tuple[str, list[tuple[str, str]]]:
    """Parse a flat CONDITIONAL grammar string into (operator, terms).

    operator is 'and', 'or', or '' for a single term. No nesting, no
    parentheses, no mixing of 'and' and 'or' in one condition, and every
    id must be a known workstream id. Never evaluates Python.
    """
    if "(" in condition or ")" in condition:
        raise ConditionError(f"CONDITIONAL condition may not nest: {condition!r}")

    has_and = " and " in condition
    has_or = " or " in condition
    if has_and and has_or:
        raise ConditionError(
            f"CONDITIONAL condition may not mix 'and' and 'or': {condition!r}"
        )

    if has_and:
        operator = "and"
        raw_terms = condition.split(" and ")
    elif has_or:
        operator = "or"
        raw_terms = condition.split(" or ")
    else:
        operator = ""
        raw_terms = [condition]

    terms: list[tuple[str, str]] = []
    for raw_term in raw_terms:
        match = _CONDITION_TERM.match(raw_term.strip())
        if match is None:
            raise ConditionError(f"CONDITIONAL term is malformed: {raw_term!r}")
        workstream_id, status = match.group(1), match.group(2)
        if workstream_id not in known_ids:
            raise ConditionError(f"CONDITIONAL condition names an unknown id: {workstream_id!r}")
        terms.append((workstream_id, status))
    return operator, terms


def _evaluate_condition(
    condition: str | None, results_by_id: Mapping[str, WorkstreamResult]
) -> bool:
    if condition is None:
        raise ConditionError("CONDITIONAL join declaration requires a condition string")
    operator, terms = _parse_condition_terms(condition, results_by_id)
    checks = (results_by_id[wid].status == status for wid, status in terms)
    if operator == "and" or operator == "":
        return all(checks)
    return any(checks)


def evaluate_join(
    decl: JoinDecl, results_by_id: Mapping[str, WorkstreamResult]
) -> JoinResult:
    """Evaluate one join declaration against known workstream results.

    Join semantics are fixed by the W05 task packet invariants:
    ALL_REQUIRED satisfied iff every required id is PASS; ANY_ONE iff at
    least one PASS; QUORUM iff count(PASS) >= quorum; ORDERED iff every
    required id is PASS in declared order (a non-PASS id blocks every
    later id as "not evaluated"); OPTIONAL_SIBLING iff the non-optional
    members are PASS regardless of optional members; CONDITIONAL iff the
    flat grammar predicate over statuses is True. UNKNOWN never counts as
    PASS for any join type.
    """
    if decl.join_type == JoinType.ORDERED.value:
        return _evaluate_ordered(decl, results_by_id)

    affected, unaffected = _split_by_status(decl.requires, results_by_id)

    if decl.join_type == JoinType.ALL_REQUIRED.value:
        satisfied = not affected
    elif decl.join_type == JoinType.ANY_ONE.value:
        satisfied = bool(unaffected)
    elif decl.join_type == JoinType.QUORUM.value:
        quorum = _validate_quorum(decl)
        satisfied = len(unaffected) >= quorum
    elif decl.join_type == JoinType.OPTIONAL_SIBLING.value:
        optional_ids = _parse_optional(decl.condition)
        non_optional = [member for member in decl.requires if member not in optional_ids]
        satisfied = all(results_by_id[member].status == _PASS for member in non_optional)
    elif decl.join_type == JoinType.CONDITIONAL.value:
        satisfied = _evaluate_condition(decl.condition, results_by_id)
    else:
        raise ValueError(f"unknown join_type: {decl.join_type!r}")

    return JoinResult(
        join_id=decl.join_id,
        join_type=decl.join_type,
        satisfied=satisfied,
        affected_workstreams=tuple(affected),
        unaffected_workstreams=tuple(unaffected),
    )


def evaluate_all(
    decls: Sequence[JoinDecl], results: Sequence[WorkstreamResult]
) -> tuple[JoinResult, ...]:
    """Evaluate every join declaration, in declaration order."""
    results_by_id = {result.workstream_id: result for result in results}
    return tuple(evaluate_join(decl, results_by_id) for decl in decls)


def derive_macro_status(
    results: Sequence[WorkstreamResult],
    join_results: Sequence[JoinResult],
    global_stop: str | None = None,
) -> str:
    """Derive macro_status per the closed, fixed derivation rule.

    A caller-supplied global stop condition (a macro_status enum member)
    always overrides. Otherwise: all declared joins satisfied and every
    workstream PASS yields PASS_IMPLEMENTATION_PROGRAM_COMPLETE; every
    workstream non-PASS yields BLOCKED; any other mix (at least one PASS
    alongside at least one non-PASS workstream, or all-PASS workstreams
    with an unsatisfied join) yields PARTIAL_BLOCKED, which is the
    fixture's asserted case (a blocked child can never be made green by a
    sibling's PASS, and an unaffected sibling can never be falsely failed).
    No other value is produced.
    """
    if global_stop is not None:
        if global_stop not in _MACRO_STATUS_VALUES:
            raise ValueError(f"unknown global stop condition: {global_stop!r}")
        return global_stop

    statuses = [result.status for result in results]
    all_pass = all(status == _PASS for status in statuses)
    all_joins_satisfied = all(join_result.satisfied for join_result in join_results)
    if all_pass and all_joins_satisfied:
        return "PASS_IMPLEMENTATION_PROGRAM_COMPLETE"
    if all(status != _PASS for status in statuses):
        return "BLOCKED"
    return "PARTIAL_BLOCKED"


def next_legal_action(results: Sequence[WorkstreamResult], macro_status: str) -> str:
    """Derive the next legal action string for a macro_status.

    PARTIAL_BLOCKED and BLOCKED both resolve to
    'RESOLVE_<first affected id in sorted order>', where affected means
    status is not PASS. PASS_IMPLEMENTATION_PROGRAM_COMPLETE has nothing
    left to resolve and returns upward to the team lead. Any other
    (global-stop-overridden) macro_status requires operator attention.
    """
    if macro_status == "PASS_IMPLEMENTATION_PROGRAM_COMPLETE":
        return "RETURN_TO_TEAM_LEAD"
    if macro_status in ("PARTIAL_BLOCKED", "BLOCKED"):
        non_pass = sorted(result.workstream_id for result in results if result.status != _PASS)
        if non_pass:
            return f"RESOLVE_{non_pass[0]}"
        return "RETURN_TO_TEAM_LEAD"
    return "ESCALATE_TO_OPERATOR"
