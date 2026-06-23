"""Authentication guard tests for LIVE_WRITE_READY activation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from dopemux.pcp.bridge.assertion_auth import NoTrustedIssuerVerifier
from dopemux.pcp.bridge.authority_binding import binding_from_entries
from dopemux.pcp.bridge.fastapi_bridge import InProcessDedupStore, route_mutation
from tests.project_control_plane.test_fastapi_bridge import (
    _FAR_FUTURE,
    _NOW,
    _PassVerifier,
    _SpyWriter,
    _activation_kwargs,
    _authority_entry,
    _operation,
    _ready_gate_for,
)


class _FailVerifier:
    def verify(self, assertion: dict, *, operation: dict) -> tuple[bool, list[str]]:
        _ = (assertion, operation)
        return (False, ["ASSERTION_SIGNATURE_INVALID"])


class _RaisingVerifier:
    def verify(self, assertion: dict, *, operation: dict) -> tuple[bool, list[str]]:
        _ = (assertion, operation)
        raise RuntimeError("verifier exploded")


def _writer_reg(spy: _SpyWriter) -> dict:
    return {"dopemux.test_writer": spy}


class TestAssertionAuth:
    def test_registered_writer_no_verifier_rejected(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            now=_NOW,
            authority_binding=binding_from_entries([_authority_entry()]),
        )
        assert result["mode"] == "REJECTED"
        assert "ASSERTION_ISSUER_UNTRUSTED" in result["reasons"]
        assert spy.calls == []

    def test_registered_writer_fail_verifier_rejected(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            assertion_verifier=_FailVerifier(),
            authority_binding=binding_from_entries([_authority_entry()]),
            now=_NOW,
        )
        assert result["mode"] == "REJECTED"
        assert "ASSERTION_SIGNATURE_INVALID" in result["reasons"]
        assert spy.calls == []

    def test_registered_writer_pass_verifier_reaches_writer(self):
        spy = _SpyWriter(result={"ok": True})
        op = _operation()
        gate = _ready_gate_for(op)
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            now=_NOW,
            **_activation_kwargs(),
        )
        assert result["mode"] == "LIVE"
        assert len(spy.calls) == 1

    def test_verifier_exception_rejected(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            assertion_verifier=_RaisingVerifier(),
            authority_binding=binding_from_entries([_authority_entry()]),
            now=_NOW,
        )
        assert result["mode"] == "REJECTED"
        assert any(r.startswith("ASSERTION_VERIFY_FAILED") for r in result["reasons"])
        assert spy.calls == []

    def test_unsigned_ready_with_future_valid_until_still_rejected(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op, valid_until=_FAR_FUTURE, authenticity={"required": True, "verified": True, "issuer": "self", "verification_ref": None})
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            assertion_verifier=NoTrustedIssuerVerifier(),
            authority_binding=binding_from_entries([_authority_entry()]),
            now=datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc),
        )
        assert result["mode"] == "REJECTED"
        assert spy.calls == []

    def test_dry_run_does_not_require_verifier(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=False,
            writer_registry=_writer_reg(spy),
            now=_NOW,
        )
        assert result["mode"] == "DRY_RUN"
        assert spy.calls == []

    @pytest.mark.parametrize("writer_registry", [None, {}])
    def test_no_registry_does_not_invoke_default_verifier_path(self, writer_registry):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=writer_registry,
            now=_NOW,
        )
        assert result["mode"] == "REJECTED"
        assert "CANONICAL_WRITER_NOT_REGISTERED" in result["reasons"]
        assert spy.calls == []