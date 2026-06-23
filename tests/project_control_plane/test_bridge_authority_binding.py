"""Authority-map binding tests for live-write activation."""

from __future__ import annotations

from dopemux.pcp.bridge.authority_binding import (
    FailClosedAuthorityBinding,
    binding_from_entries,
)
from dopemux.pcp.bridge.fastapi_bridge import InProcessDedupStore, route_mutation
from tests.project_control_plane.test_fastapi_bridge import (
    _NOW,
    _PassVerifier,
    _SpyWriter,
    _activation_kwargs,
    _authority_entry,
    _operation,
    _ready_gate_for,
)


def _writer_reg(spy: _SpyWriter, name: str = "dopemux.test_writer") -> dict:
    return {name: spy}


class TestAuthorityBinding:
    def test_no_authority_map_with_writer_rejected(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            assertion_verifier=_PassVerifier(),
            authority_binding=FailClosedAuthorityBinding(),
            now=_NOW,
        )
        assert result["mode"] == "REJECTED"
        assert "AUTHORITY_MAP_ABSENT" in result["reasons"]
        assert spy.calls == []

    def test_adapter_entry_rejected(self):
        spy = _SpyWriter()
        op = _operation(target_surface="memory.decisions")
        gate = _ready_gate_for(op)
        entry = _authority_entry(domain="memory.decisions")
        entry["surface_class"] = "ADAPTER"
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            assertion_verifier=_PassVerifier(),
            authority_binding=binding_from_entries([entry]),
            now=_NOW,
        )
        assert result["mode"] == "REJECTED"
        assert "AUTHORITY_SURFACE_NOT_WRITABLE" in result["reasons"]

    def test_writer_mismatch_rejected(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op, canonical_writer="dopemux.test_writer")
        entry = _authority_entry(canonical_writer="dopemux.other_writer")
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            assertion_verifier=_PassVerifier(),
            authority_binding=binding_from_entries([entry]),
            now=_NOW,
        )
        assert result["mode"] == "REJECTED"
        assert "AUTHORITY_WRITER_MISMATCH" in result["reasons"]

    def test_live_write_not_allowed_rejected(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        entry = _authority_entry()
        entry["live_write_allowed"] = False
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            assertion_verifier=_PassVerifier(),
            authority_binding=binding_from_entries([entry]),
            now=_NOW,
        )
        assert result["mode"] == "REJECTED"
        assert "AUTHORITY_LIVE_WRITE_FORBIDDEN" in result["reasons"]

    def test_valid_source_entry_allows_writer(self):
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

    def test_unknown_target_surface_rejected(self):
        spy = _SpyWriter()
        op = _operation(target_surface="unknown.surface")
        gate = _ready_gate_for(op)
        result = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=_writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            assertion_verifier=_PassVerifier(),
            authority_binding=binding_from_entries([_authority_entry()]),
            now=_NOW,
        )
        assert result["mode"] == "REJECTED"
        assert "AUTHORITY_ENTRY_NOT_FOUND" in result["reasons"]