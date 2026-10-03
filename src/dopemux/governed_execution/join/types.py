"""Frozen data shapes for join-type evaluation (W05).

Field names mirror schemas/governed_execution/aggregate_return_envelope.v1
exactly so that envelope.py can serialize these dataclasses without any
field-name translation layer. All dataclasses are frozen: an evaluator can
never mutate a caller-supplied result, which is the mechanical enforcement
of authority non-transfer (a PASS sibling cannot change a BLOCKED member's
recorded status).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class JoinType(str, Enum):
    """Mirrors schemas/governed_execution/enums.v1.schema.json#/definitions/join_type.

    The values and their order are asserted equal to that schema definition
    by test_join_types.py::test_join_type_matches_enums_schema, so this
    module itself performs no filesystem read.
    """

    ALL_REQUIRED = "ALL_REQUIRED"
    ANY_ONE = "ANY_ONE"
    QUORUM = "QUORUM"
    ORDERED = "ORDERED"
    OPTIONAL_SIBLING = "OPTIONAL_SIBLING"
    CONDITIONAL = "CONDITIONAL"


class ConditionError(ValueError):
    """Raised when a join declaration's condition string is malformed.

    Covers both the CONDITIONAL grammar (nesting, parentheses, unknown ids)
    and the OPTIONAL_SIBLING 'optional:<id>,<id>' condition string.
    """


@dataclass(frozen=True)
class ReturnRef:
    """Mirrors aggregate_return_envelope.v1#/properties/workstreams/items/return_ref."""

    path: str
    sha256: str


@dataclass(frozen=True)
class WorkstreamResult:
    """Mirrors aggregate_return_envelope.v1#/properties/workstreams/items.

    status is a workstream_status enum value (see enums.v1.schema.json);
    subject_sha is either a git_oid or the literal string 'NONE'.
    """

    workstream_id: str
    status: str
    subject_sha: str
    return_ref: ReturnRef


@dataclass(frozen=True)
class JoinDecl:
    """A join declaration: which workstream ids must be reconciled, and how.

    condition carries the CONDITIONAL grammar string for join_type
    CONDITIONAL, or the 'optional:<id>,<id>' marker string for join_type
    OPTIONAL_SIBLING; it is unused (and should be None) for every other
    join_type. quorum is required (and validated) only for join_type
    QUORUM.
    """

    join_id: str
    join_type: str
    requires: tuple[str, ...]
    condition: str | None = None
    quorum: int | None = None


@dataclass(frozen=True)
class JoinResult:
    """Mirrors aggregate_return_envelope.v1#/properties/join_results/items.

    affected_workstreams and unaffected_workstreams are always sorted.
    """

    join_id: str
    join_type: str
    satisfied: bool
    affected_workstreams: tuple[str, ...]
    unaffected_workstreams: tuple[str, ...]
