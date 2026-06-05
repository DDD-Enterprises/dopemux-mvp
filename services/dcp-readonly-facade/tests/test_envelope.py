"""Envelope: field completeness + status semantics."""

from __future__ import annotations

import pytest

from dcp_facade import envelope as E


def test_envelope_has_all_canonical_fields():
    env = E.build_envelope(
        project_id="p",
        status=E.OK,
        source_system=E.SOURCE_FACADE,
        authority_label=E.AUTHORITY_FACADE,
        data={"x": 1},
    )
    assert set(env.keys()) == set(E.ENVELOPE_FIELDS)
    # list fields are always present as lists
    for key in ("limitations", "warnings", "redactions", "blocked_reasons"):
        assert isinstance(env[key], list)


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        E.build_envelope(
            project_id="p",
            status="SUCCESS",  # not a valid token
            source_system=E.SOURCE_FACADE,
            authority_label=E.AUTHORITY_FACADE,
        )


def test_blocked_helper_shape():
    env = E.blocked("p", "unknown project")
    assert env["status"] == E.BLOCKED
    assert env["data"] is None
    assert env["blocked_reasons"] == ["unknown project"]
    assert env["project_id"] == "p"
