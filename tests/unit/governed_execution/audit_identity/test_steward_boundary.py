"""Tests for the PR Steward boundary classifier."""
from __future__ import annotations

import pytest

from dopemux.governed_execution.audit_identity import steward_boundary
from dopemux.governed_execution.audit_identity.steward_boundary import (
    ALLOWED,
    ALLOWED_ACTIONS,
    CHECK_ONLY,
    FORBIDDEN,
    FORBIDDEN_ACTIONS,
    NO_APPROVAL,
    NO_AUDIT_AUTHORING,
    NO_FIX,
    NO_MERGE,
    NOT_READY,
    READY,
    classify_steward_action,
)

_FORBIDDEN_ATTRIBUTE_NAMES = frozenset({"merge", "approve", "push", "write"})


def test_boundary_constants_are_the_five_named_strings() -> None:
    assert CHECK_ONLY == "CHECK_ONLY"
    assert NO_FIX == "NO_FIX"
    assert NO_APPROVAL == "NO_APPROVAL"
    assert NO_MERGE == "NO_MERGE"
    assert NO_AUDIT_AUTHORING == "NO_AUDIT_AUTHORING"


@pytest.mark.parametrize("action", sorted(ALLOWED_ACTIONS))
def test_every_allowed_action_classifies_allowed(action: str) -> None:
    assert classify_steward_action(action) == ALLOWED


@pytest.mark.parametrize("action", sorted(FORBIDDEN_ACTIONS))
def test_every_forbidden_action_classifies_forbidden(action: str) -> None:
    assert classify_steward_action(action) == FORBIDDEN


def test_allowed_and_forbidden_vocabularies_are_disjoint() -> None:
    assert ALLOWED_ACTIONS.isdisjoint(FORBIDDEN_ACTIONS)


@pytest.mark.parametrize(
    "action",
    ["", "UNKNOWN_ACTION", "read_pr", "Merge", "DELETE_REPO", "EMIT_APPROVAL"],
)
def test_unknown_action_is_forbidden_fail_closed(action: str) -> None:
    assert classify_steward_action(action) == FORBIDDEN


def test_ready_and_not_ready_are_plain_string_constants() -> None:
    assert READY == "READY"
    assert NOT_READY == "NOT_READY"
    assert isinstance(READY, str)
    assert isinstance(NOT_READY, str)


def test_module_exposes_no_merge_approve_push_write_attribute() -> None:
    for name in dir(steward_boundary):
        if name.startswith("_"):
            continue
        assert name.lower() not in _FORBIDDEN_ATTRIBUTE_NAMES, (
            f"steward_boundary module must not expose an attribute named {name!r}"
        )


def test_module_exposes_no_callables_besides_the_classifier() -> None:
    callables = [
        name
        for name in dir(steward_boundary)
        if not name.startswith("_") and callable(getattr(steward_boundary, name))
    ]
    assert callables == ["classify_steward_action"]
