"""Immutable logical-request identity tests."""

from __future__ import annotations

import dataclasses

import pytest

from dopemux.uag import LogicalRequest, RequestedOutputContract, WorkspaceBinding
from dopemux.uag.enums import OutputContractClass


def _make_request() -> LogicalRequest:
    return LogicalRequest(
        logical_request_id="req-1",
        binding=WorkspaceBinding(
            project_id="dopemux-mvp",
            workspace_ref="/w",
            request_id="req-1",
        ),
        requested_output_contract=RequestedOutputContract(
            output_class=OutputContractClass.PUBLIC_TEXT
        ),
    )


def test_request_is_frozen_and_hashable():
    req = _make_request()
    assert hash(req) is not None
    assert dataclasses.is_dataclass(req)


def test_mutation_of_identity_fails():
    req = _make_request()
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.logical_request_id = "req-2"
    with pytest.raises(dataclasses.FrozenInstanceError):
        req.binding = WorkspaceBinding("x", "/y", "z")


def test_identity_digest_is_deterministic():
    a = _make_request()
    b = _make_request()
    assert a.identity_digest == b.identity_digest
    assert a.identity_digest == a.identity_digest


def test_identity_digest_varies_with_binding():
    a = _make_request()
    b = LogicalRequest(
        logical_request_id="req-1",
        binding=WorkspaceBinding("other-project", "/w", "req-1"),
        requested_output_contract=RequestedOutputContract(
            output_class=OutputContractClass.PUBLIC_TEXT
        ),
    )
    assert a.identity_digest != b.identity_digest


def test_empty_request_id_rejected():
    with pytest.raises(ValueError):
        LogicalRequest(
            logical_request_id="",
            binding=WorkspaceBinding("p", "/w", "r"),
            requested_output_contract=RequestedOutputContract(
                output_class=OutputContractClass.PUBLIC_TEXT
            ),
        )
