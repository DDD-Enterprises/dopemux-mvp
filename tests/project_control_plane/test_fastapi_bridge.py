"""
Tests for the Packet 11 FastAPI live-write bridge (dopemux.pcp.bridge.fastapi_bridge).

Proves the bridge is fail-closed: a writer is invoked ONLY behind a schema-valid,
consistent, unexpired READY gate that is bound (operation_ref + target_surface +
payload_digest) to the exact operation, with execute is True, a registered
canonical writer matching the gate's name, and a first-time assertion_id.

Groups:
  A. check_live_write_gate (pure, incl. TTL)
  B. route_mutation decision branches (pure)
  C. gate-operation + payload-digest binding
  D. canonical-writer registry / substitution
  E. idempotency dedup
  F. FastAPI TestClient (thin HTTP layer)
  G. structural no-write proofs (Red Line #15) + invariants
"""

from __future__ import annotations

import hashlib
import inspect
import json
import pathlib
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dopemux.pcp.bridge import fastapi_bridge as bridge
from dopemux.pcp.bridge.authority_binding import binding_from_entries
from dopemux.pcp.bridge.fastapi_bridge import (
    InProcessDedupStore,
    RedisDedupStore,
    check_live_write_gate,
    create_bridge_router,
    route_mutation,
)

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# A fixed "now" so TTL tests are deterministic. The default gate valid_until is
# far in the future relative to this.
_NOW = datetime(2026, 6, 22, 12, 0, 0, tzinfo=timezone.utc)
_FAR_FUTURE = "2999-01-01T00:00:00Z"
_PAST = "2020-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _operation(operation_ref: str = "op-merge-pr-42", target_surface: str = "github.pr.merge", **extra) -> dict:
    op = {"operation_ref": operation_ref, "target_surface": target_surface}
    op.update(extra)
    return op


def _digest(operation: dict) -> str:
    canonical = json.dumps(operation, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _ready_gate_for(operation: dict, **overrides) -> dict:
    """A schema-valid READY assertion bound to *operation* (ref/surface/digest),
    far-future expiry. Callers may override individual keys."""
    gate = {
        "schema_version": "pcp.live_write_ready.v0",
        "assertion_id": "assert-001",
        "operation_ref": operation["operation_ref"],
        "target_surface": operation["target_surface"],
        "canonical_writer": "dopemux.test_writer",
        "allowlist": {"paths": ["src/x.py"], "diff_within_allowlist": True},
        "approval": {"approved": True, "approver": "op", "approval_ref": "ref"},
        "idempotency": {"idempotent": True, "key": "k1"},
        "rollback": {"available": True, "plan": "revert the change"},
        "dry_run_proof": {"performed": True, "proof_ref": "dr"},
        "independent_audit": {
            "performed": True,
            "independent": True,
            "status": "PASS",
            "auditor": "auditor",
        },
        "post_write_verification": {"planned": True, "performed": False, "verification_ref": "v"},
        "status": "READY",
        "blocked_reasons": [],
        "live_write_performed": False,
        "created_at": "2026-06-22T00:00:00Z",
        "valid_until": _FAR_FUTURE,
        "payload_digest": _digest(operation),
    }
    gate.update(overrides)
    return gate


class _PassVerifier:
    def verify(self, assertion: dict, *, operation: dict) -> tuple[bool, list[str]]:
        _ = (assertion, operation)
        return (True, [])


def _authority_entry(
    *,
    domain: str = "github.pr.merge",
    canonical_writer: str = "dopemux.test_writer",
) -> dict:
    return {
        "domain": domain,
        "action": "mutate",
        "canonical_authority_owner": "test-owner",
        "canonical_writer": canonical_writer,
        "surface_class": "SOURCE",
        "reader_or_projection_surface": domain,
        "source_truth_refs": ["test-fixture"],
        "proof_required": True,
        "live_write_allowed": True,
        "approval_required": True,
        "rollback_required": True,
        "unknown_behavior": "BLOCK_OR_ESCALATE",
    }


def _activation_kwargs(
    writer_name: str = "dopemux.test_writer",
    *,
    domain: str = "github.pr.merge",
) -> dict:
    return {
        "assertion_verifier": _PassVerifier(),
        "authority_binding": binding_from_entries(
            [_authority_entry(domain=domain, canonical_writer=writer_name)]
        ),
    }


class _SpyWriter:
    """A fake canonical writer that records calls. Never performs a real write."""

    def __init__(self, result=None, raises: Exception | None = None):
        self.calls: list = []
        self._result = result if result is not None else {"ok": True}
        self._raises = raises

    def __call__(self, operation: dict):
        self.calls.append(operation)
        if self._raises is not None:
            raise self._raises
        return self._result


# ===========================================================================
# A. check_live_write_gate — pure, fail-closed
# ===========================================================================

class TestGate:
    def test_none_denied(self):
        permitted, reasons = check_live_write_gate(None)
        assert permitted is False and "GATE_ABSENT" in reasons

    @pytest.mark.parametrize("bad", ["READY", [], 123, 0, True])
    def test_non_dict_denied(self, bad):
        permitted, _ = check_live_write_gate(bad)  # type: ignore[arg-type]
        assert permitted is False

    def test_clean_ready_permitted(self):
        op = _operation()
        permitted, reasons = check_live_write_gate(_ready_gate_for(op), now=_NOW)
        assert permitted is True and reasons == []

    def test_schema_invalid_denied(self):
        op = _operation()
        # live_write_performed must be const false -> schema invalid
        gate = _ready_gate_for(op, live_write_performed=True)
        permitted, reasons = check_live_write_gate(gate, now=_NOW)
        assert permitted is False and "GATE_SCHEMA_INVALID" in reasons

    @pytest.mark.parametrize(
        "override",
        [
            {"canonical_writer": None},
            {"approval": {"approved": False, "approver": None, "approval_ref": None}},
            {"idempotency": {"idempotent": False, "key": None}},
            {"rollback": {"available": False, "plan": None}},
            {"dry_run_proof": {"performed": False, "proof_ref": None}},
            {"independent_audit": {"performed": True, "independent": False, "status": "PASS", "auditor": "x"}},
            {"independent_audit": {"performed": True, "independent": True, "status": "FAIL", "auditor": "x"}},
            {"post_write_verification": {"planned": False, "performed": False, "verification_ref": None}},
            {"allowlist": {"paths": [], "diff_within_allowlist": True}},
        ],
    )
    def test_each_missing_precondition_denied(self, override):
        op = _operation()
        gate = _ready_gate_for(op, status="READY", **override)
        permitted, _ = check_live_write_gate(gate, now=_NOW)
        assert permitted is False

    def test_blocked_status_denied_surfaces_reasons(self):
        op = _operation()
        gate = _ready_gate_for(op, status="BLOCKED", blocked_reasons=["MISSING_APPROVAL"])
        permitted, reasons = check_live_write_gate(gate, now=_NOW)
        assert permitted is False and "MISSING_APPROVAL" in reasons

    def test_needs_supervisor_denied(self):
        op = _operation()
        gate = _ready_gate_for(op, status="NEEDS_SUPERVISOR", blocked_reasons=["UNKNOWN"])
        permitted, _ = check_live_write_gate(gate, now=_NOW)
        assert permitted is False

    def test_expired_gate_denied(self):
        op = _operation()
        gate = _ready_gate_for(op, valid_until=_PAST)
        permitted, reasons = check_live_write_gate(gate, now=_NOW)
        assert permitted is False and "GATE_EXPIRED" in reasons

    def test_future_gate_permitted(self):
        op = _operation()
        gate = _ready_gate_for(op, valid_until=_FAR_FUTURE)
        permitted, _ = check_live_write_gate(gate, now=_NOW)
        assert permitted is True


# ===========================================================================
# B. route_mutation — decision branches (pure)
# ===========================================================================

class TestRoute:
    def _writer_reg(self, spy: _SpyWriter) -> dict:
        return {"dopemux.test_writer": spy}

    def test_no_gate_rejected_no_write(self):
        spy = _SpyWriter()
        op = _operation()
        r = route_mutation(op, live_write_ready=None, execute=True,
                           writer_registry=self._writer_reg(spy), now=_NOW)
        assert r["mode"] == "REJECTED" and r["executed"] is False and spy.calls == []

    def test_blocked_gate_rejected_no_write(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op, status="BLOCKED", blocked_reasons=["MISSING_APPROVAL"])
        r = route_mutation(op, live_write_ready=gate, execute=True,
                           writer_registry=self._writer_reg(spy), now=_NOW)
        assert r["mode"] == "REJECTED" and spy.calls == []

    def test_ready_no_execute_is_dry_run_no_write(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        r = route_mutation(op, live_write_ready=gate, execute=False,
                           writer_registry=self._writer_reg(spy), now=_NOW)
        assert r["mode"] == "DRY_RUN" and r["permitted"] is True and r["executed"] is False
        assert spy.calls == []

    def test_ready_execute_no_registry_rejected(self):
        op = _operation()
        gate = _ready_gate_for(op)
        r = route_mutation(op, live_write_ready=gate, execute=True,
                           writer_registry=None, now=_NOW)
        assert r["mode"] == "REJECTED" and "CANONICAL_WRITER_NOT_REGISTERED" in r["reasons"]
        assert r["executed"] is False

    def test_ready_execute_with_registered_writer_is_live(self):
        spy = _SpyWriter(result={"merged": True})
        op = _operation()
        gate = _ready_gate_for(op)
        r = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=self._writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            now=_NOW,
            **_activation_kwargs(),
        )
        assert r["mode"] == "LIVE" and r["executed"] is True
        assert r["writer_result"] == {"merged": True}
        assert len(spy.calls) == 1 and spy.calls[0] == op

    @pytest.mark.parametrize("execute_val", [1, "yes", "true", [1], object()])
    def test_execute_non_bool_truthy_is_dry_run(self, execute_val):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        r = route_mutation(op, live_write_ready=gate, execute=execute_val,  # type: ignore[arg-type]
                           writer_registry=self._writer_reg(spy), now=_NOW)
        assert r["mode"] == "DRY_RUN" and spy.calls == []

    def test_writer_raises_is_rejected_not_live(self):
        spy = _SpyWriter(raises=RuntimeError("boom"))
        op = _operation()
        gate = _ready_gate_for(op)
        r = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=self._writer_reg(spy),
            dedup_store=InProcessDedupStore(),
            now=_NOW,
            **_activation_kwargs(),
        )
        assert r["mode"] == "REJECTED" and r["executed"] is False
        assert any(reason.startswith("WRITER_RAISED") for reason in r["reasons"])

    @pytest.mark.parametrize("bad_op", [None, "x", 123, [], {}, {"operation_ref": "x"}, {"target_surface": "y"},
                                        {"operation_ref": "", "target_surface": "y"}])
    def test_malformed_operation_rejected(self, bad_op):
        spy = _SpyWriter()
        gate = _ready_gate_for(_operation())
        r = route_mutation(bad_op, live_write_ready=gate, execute=True,  # type: ignore[arg-type]
                           writer_registry=self._writer_reg(spy), now=_NOW)
        assert r["mode"] == "REJECTED" and spy.calls == []


# ===========================================================================
# C. Binding — ref/surface + payload digest
# ===========================================================================

class TestBinding:
    def test_operation_ref_mismatch_rejected(self):
        spy = _SpyWriter()
        op = _operation(operation_ref="op-A")
        # gate authored for a DIFFERENT operation_ref
        other = _operation(operation_ref="op-B")
        gate = _ready_gate_for(other)
        r = route_mutation(op, live_write_ready=gate, execute=True,
                           writer_registry={"dopemux.test_writer": spy}, now=_NOW)
        assert r["mode"] == "REJECTED" and "GATE_OPERATION_MISMATCH" in r["reasons"]
        assert spy.calls == []

    def test_target_surface_mismatch_rejected(self):
        spy = _SpyWriter()
        op = _operation(target_surface="github.pr.merge")
        other = _operation(target_surface="conport.progress_entry")
        gate = _ready_gate_for(other)
        # align refs so only surface differs; re-point gate ref to op's ref
        gate["operation_ref"] = op["operation_ref"]
        r = route_mutation(op, live_write_ready=gate, execute=True,
                           writer_registry={"dopemux.test_writer": spy}, now=_NOW)
        assert r["mode"] == "REJECTED" and "GATE_OPERATION_MISMATCH" in r["reasons"]
        assert spy.calls == []

    def test_payload_digest_mismatch_rejected(self):
        spy = _SpyWriter()
        op = _operation(pr_id=42)
        gate = _ready_gate_for(op)  # digest bound to pr_id=42
        tampered = _operation(pr_id=9999)  # same ref+surface, different payload
        r = route_mutation(tampered, live_write_ready=gate, execute=True,
                           writer_registry={"dopemux.test_writer": spy}, now=_NOW)
        assert r["mode"] == "REJECTED" and "PAYLOAD_DIGEST_MISMATCH" in r["reasons"]
        assert spy.calls == []

    def test_matching_digest_allows_live(self):
        spy = _SpyWriter()
        op = _operation(pr_id=42, head_sha="abc123")
        gate = _ready_gate_for(op)
        r = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry={"dopemux.test_writer": spy},
            dedup_store=InProcessDedupStore(),
            now=_NOW,
            **_activation_kwargs(),
        )
        assert r["mode"] == "LIVE" and len(spy.calls) == 1


# ===========================================================================
# D. Canonical-writer registry / substitution
# ===========================================================================

class TestRegistry:
    def test_writer_name_not_in_registry_rejected(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op, canonical_writer="dopemux.real_writer")
        # registry only has a DIFFERENT name
        r = route_mutation(op, live_write_ready=gate, execute=True,
                           writer_registry={"dopemux.other_writer": spy}, dedup_store=InProcessDedupStore(), now=_NOW)
        assert r["mode"] == "REJECTED" and "CANONICAL_WRITER_NOT_REGISTERED" in r["reasons"]
        assert spy.calls == []

    def test_registered_name_match_is_live(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op, canonical_writer="dopemux.real_writer")
        r = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry={"dopemux.real_writer": spy},
            dedup_store=InProcessDedupStore(),
            now=_NOW,
            **_activation_kwargs(writer_name="dopemux.real_writer"),
        )
        assert r["mode"] == "LIVE" and len(spy.calls) == 1


# ===========================================================================
# E. Idempotency dedup
# ===========================================================================

class TestDedup:
    def test_same_assertion_id_executes_once(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op, assertion_id="assert-dedup-1")
        store = InProcessDedupStore()
        reg = {"dopemux.test_writer": spy}
        activation = _activation_kwargs()
        first = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=reg,
            dedup_store=store,
            now=_NOW,
            **activation,
        )
        second = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=reg,
            dedup_store=store,
            now=_NOW,
            **activation,
        )
        assert first["mode"] == "LIVE"
        assert second["mode"] == "REJECTED" and "DUPLICATE_SUPPRESSED" in second["reasons"]
        assert len(spy.calls) == 1  # writer called exactly once total

    def test_in_process_dedup_store_first_call_returns_false(self):
        store = InProcessDedupStore()
        assert store.check_and_record("key-1") is False  # first-seen

    def test_in_process_dedup_store_second_call_returns_true(self):
        store = InProcessDedupStore()
        store.check_and_record("key-1")
        assert store.check_and_record("key-1") is True  # duplicate

    def test_in_process_dedup_store_different_keys_independent(self):
        store = InProcessDedupStore()
        assert store.check_and_record("key-A") is False
        assert store.check_and_record("key-B") is False  # different key, first-seen
        assert store.check_and_record("key-A") is True   # key-A is now duplicate


class _FakeRedisClient:
    """Minimal fake redis client implementing SET NX semantics for testing."""

    def __init__(self) -> None:
        self._store: dict = {}
        self.set_calls: list = []

    def set(self, name: str, value: str, *, nx: bool = False, ex: int | None = None):
        self.set_calls.append({"name": name, "value": value, "nx": nx, "ex": ex})
        if nx:
            if name in self._store:
                return None  # key already exists — duplicate
            self._store[name] = value
            return True  # newly set — first-seen
        self._store[name] = value
        return True


class TestRedisDedupStore:
    def test_first_key_returns_false(self):
        client = _FakeRedisClient()
        store = RedisDedupStore(client)
        assert store.check_and_record("key-1") is False  # first-seen

    def test_second_key_returns_true(self):
        client = _FakeRedisClient()
        store = RedisDedupStore(client)
        store.check_and_record("key-1")
        assert store.check_and_record("key-1") is True  # duplicate

    def test_set_called_with_nx_true_and_ex(self):
        client = _FakeRedisClient()
        store = RedisDedupStore(client, ttl_seconds=3600)
        store.check_and_record("key-x")
        assert len(client.set_calls) == 1
        call = client.set_calls[0]
        assert call["nx"] is True
        assert call["ex"] == 3600

    def test_key_prefix_applied(self):
        client = _FakeRedisClient()
        store = RedisDedupStore(client, key_prefix="test:prefix:")
        store.check_and_record("my-key")
        assert client.set_calls[0]["name"] == "test:prefix:my-key"

    def test_route_mutation_with_redis_store_deduplicates(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op, assertion_id="assert-redis-dedup")
        client = _FakeRedisClient()
        redis_store = RedisDedupStore(client)
        reg = {"dopemux.test_writer": spy}
        activation = _activation_kwargs()
        first = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=reg,
            dedup_store=redis_store,
            now=_NOW,
            **activation,
        )
        second = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=reg,
            dedup_store=redis_store,
            now=_NOW,
            **activation,
        )
        assert first["mode"] == "LIVE" and first["executed"] is True
        assert second["mode"] == "REJECTED" and "DUPLICATE_SUPPRESSED" in second["reasons"]
        assert len(spy.calls) == 1  # writer called exactly once


# ===========================================================================
# F. FastAPI TestClient — thin HTTP layer
# ===========================================================================

class TestHttp:
    def _client(self, writer_registry=None, **router_kwargs) -> TestClient:
        app = FastAPI()
        app.include_router(create_bridge_router(writer_registry=writer_registry, **router_kwargs))
        return TestClient(app)

    def test_no_gate_returns_403(self):
        client = self._client()
        op = _operation()
        resp = client.post("/bridge/mutate", json={"operation": op, "execute": True})
        assert resp.status_code == 403
        body = resp.json()
        assert body["mode"] == "REJECTED" and body["is_authority"] is False

    def test_dry_run_returns_200(self):
        op = _operation()
        gate = _ready_gate_for(op)
        client = self._client()
        resp = client.post("/bridge/mutate", json={"operation": op, "live_write_ready": gate, "execute": False})
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "DRY_RUN" and body["executed"] is False

    def test_default_app_cannot_live_write(self):
        # No writer registry -> execute=True with a valid READY gate is rejected.
        op = _operation()
        gate = _ready_gate_for(op)
        client = self._client()  # no registry
        resp = client.post("/bridge/mutate", json={"operation": op, "live_write_ready": gate, "execute": True})
        assert resp.status_code == 403
        assert "CANONICAL_WRITER_NOT_REGISTERED" in resp.json()["reasons"]

    def test_live_when_writer_registered(self):
        spy = _SpyWriter(result={"merged": True})
        op = _operation()
        gate = _ready_gate_for(op)
        client = self._client(
            writer_registry={"dopemux.test_writer": spy},
            **_activation_kwargs(),
        )
        resp = client.post("/bridge/mutate", json={"operation": op, "live_write_ready": gate, "execute": True})
        assert resp.status_code == 200
        body = resp.json()
        assert body["mode"] == "LIVE" and body["executed"] is True
        assert len(spy.calls) == 1

    def test_http_dedup_suppresses_replay(self):
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op, assertion_id="assert-http-dedup")
        client = self._client(
            writer_registry={"dopemux.test_writer": spy},
            **_activation_kwargs(),
        )
        payload = {"operation": op, "live_write_ready": gate, "execute": True}
        first = client.post("/bridge/mutate", json=payload)
        second = client.post("/bridge/mutate", json=payload)
        assert first.status_code == 200 and first.json()["mode"] == "LIVE"
        assert second.status_code == 403 and "DUPLICATE_SUPPRESSED" in second.json()["reasons"]
        assert len(spy.calls) == 1

    @pytest.mark.parametrize("bad_val", [1, "yes", "true"])
    def test_execute_truthy_non_bool_rejected_at_http(self, bad_val):
        """StrictBool: a truthy non-boolean execute value is rejected at the HTTP
        boundary (422), never coerced to True and never routed to a live write.

        This closes the Pydantic-coercion gap: without StrictBool, JSON 1/"yes"
        would coerce to True before route_mutation's `execute is True` check.
        """
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        client = self._client(writer_registry={"dopemux.test_writer": spy})
        resp = client.post(
            "/bridge/mutate",
            json={"operation": op, "live_write_ready": gate, "execute": bad_val},
        )
        assert resp.status_code == 422
        assert spy.calls == []

    def test_execute_real_bools_still_work(self):
        """A genuine JSON boolean still routes correctly under StrictBool."""
        spy = _SpyWriter()
        op = _operation()
        gate = _ready_gate_for(op)
        client = self._client(
            writer_registry={"dopemux.test_writer": spy},
            **_activation_kwargs(),
        )
        live = client.post("/bridge/mutate", json={"operation": op, "live_write_ready": gate, "execute": True})
        assert live.status_code == 200 and live.json()["mode"] == "LIVE"
        # a fresh gate (new assertion_id) for the dry-run path to avoid dedup
        gate2 = _ready_gate_for(op, assertion_id="assert-dry")
        dry = client.post("/bridge/mutate", json={"operation": op, "live_write_ready": gate2, "execute": False})
        assert dry.status_code == 200 and dry.json()["mode"] == "DRY_RUN"


# ===========================================================================
# G. Structural no-write proofs + invariants
# ===========================================================================

class TestStructural:
    def test_module_source_has_no_live_write_wiring(self):
        """The bridge module must contain no forbidden live-write wiring (Red Line #15)."""
        src = inspect.getsource(bridge)
        _eq = "="
        forbidden = [
            "subprocess",
            "gh" + " pr " + "merge",
            "gh" + " pr " + "ready",
            "git" + " push",
            "git" + " commit",
            "git" + " merge",
            "queue_drain",
            "batch_resolve_and_merge",
            "execute" + _eq + "True",
        ]
        for token in forbidden:
            assert token not in src, f"forbidden live-write token {token!r} in bridge source"

    def test_no_default_writer(self):
        for fn in (route_mutation, create_bridge_router, bridge.create_bridge_app):
            params = inspect.signature(fn).parameters
            if "writer_registry" in params:
                assert params["writer_registry"].default is None

    def test_is_authority_const_false_across_modes(self):
        op = _operation()
        gate = _ready_gate_for(op)
        spy = _SpyWriter()
        reg = {"dopemux.test_writer": spy}
        results = [
            route_mutation(op, live_write_ready=None, execute=True, writer_registry=reg, now=_NOW),  # REJECTED
            route_mutation(op, live_write_ready=gate, execute=False, writer_registry=reg, now=_NOW),  # DRY_RUN
            route_mutation(
                op,
                live_write_ready=gate,
                execute=True,
                writer_registry=reg,
                dedup_store=InProcessDedupStore(),
                now=_NOW,
                **_activation_kwargs(),
            ),  # LIVE
        ]
        assert {r["mode"] for r in results} == {"REJECTED", "DRY_RUN", "LIVE"}
        for r in results:
            assert r["is_authority"] is False

    def test_executed_iff_live(self):
        op = _operation()
        gate = _ready_gate_for(op)
        spy = _SpyWriter()
        reg = {"dopemux.test_writer": spy}
        rejected = route_mutation(op, live_write_ready=None, execute=True, writer_registry=reg, now=_NOW)
        dry = route_mutation(op, live_write_ready=gate, execute=False, writer_registry=reg, now=_NOW)
        live = route_mutation(
            op,
            live_write_ready=gate,
            execute=True,
            writer_registry=reg,
            dedup_store=InProcessDedupStore(),
            now=_NOW,
            **_activation_kwargs(),
        )
        for r in (rejected, dry, live):
            assert r["executed"] is (r["mode"] == "LIVE")

    def test_allowlist_files_only(self):
        bridge_dir = _REPO_ROOT / "src" / "dopemux" / "pcp" / "bridge"
        py_files = sorted(p.name for p in bridge_dir.glob("*.py"))
        assert py_files == [
            "__init__.py",
            "assertion_auth.py",
            "authority_binding.py",
            "fastapi_bridge.py",
        ]
