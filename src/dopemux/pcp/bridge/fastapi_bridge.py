"""dopemux.pcp.bridge.fastapi_bridge — fail-closed live-write adapter.

This module is the Packet 11 live-write bridge. It routes a mutation to a
canonical writer ONLY when every fail-closed precondition holds:

  1. the operation is a well-formed dict carrying operation_ref + target_surface;
  2. a LIVE_WRITE_READY assertion validates against
     schemas/project_control_plane/live_write_ready.schema.json, has status
     "READY", is internally consistent, and is NOT expired (valid_until);
  3. the gate is bound to THIS operation (operation_ref + target_surface equal,
     and payload_digest == sha256(canonical(operation)));
  4. ``execute is True`` (identity, not truthiness — the strict direction);
  5. the gate's named canonical_writer resolves to a registered writer callable
     (there is NO default writer — a deployed app cannot live-write); and
  6. the assertion_id has not already been executed (idempotency dedup).

The bridge is an ADAPTER, never a canonical authority: every result carries
``is_authority: False`` and ``executed`` is True iff a live write actually ran.
The module performs no I/O of its own and contains no forbidden live-write
wiring (AIR Red Line #15).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from fastapi import APIRouter, FastAPI
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from jsonschema import Draft202012Validator
from pydantic import BaseModel, StrictBool

from .._schemas import load_schema
from .assertion_auth import (
    NoTrustedIssuerVerifier,
    ReadyAssertionVerifier,
    requires_assertion_verification,
)
from .authority_binding import (
    AuthorityMapBinding,
    FailClosedAuthorityBinding,
    requires_authority_binding,
)

# ---------------------------------------------------------------------------
# Schema — loaded from bundled package data (dopemux.pcp._schemas) so the
# validator is available both from the source tree and from an installed wheel.
# No repo-root-relative path is assumed.
# ---------------------------------------------------------------------------
_SCHEMA: dict = load_schema("live_write_ready.schema.json")

_VALIDATOR = Draft202012Validator(_SCHEMA)

_MODE_REJECTED = "REJECTED"
_MODE_DRY_RUN = "DRY_RUN"
_MODE_LIVE = "LIVE"
_RESULT_SCHEMA_VERSION = "pcp.bridge_result.v0"

Writer = Callable[[dict], Any]


# ---------------------------------------------------------------------------
# Idempotency dedup store — pluggable contract.
# ---------------------------------------------------------------------------

class DedupStore(Protocol):
    """Contract for an idempotency dedup store.

    ``check_and_record(key)`` must be atomic:
      - Returns ``False`` when ``key`` is first-seen (and records it).
      - Returns ``True`` when ``key`` was already recorded (duplicate).
    """

    def check_and_record(self, key: str) -> bool: ...


class InProcessDedupStore:
    """In-process dedup store backed by a Python ``set``.

    Atomic within a single synchronous call. Suitable for single-process /
    single-worker deployments and for testing.
    """

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def check_and_record(self, key: str) -> bool:
        if key in self._seen:
            return True  # duplicate
        self._seen.add(key)
        return False  # first-seen


class RedisDedupStore:
    """Redis-backed dedup store using SET NX semantics.

    The Redis client is injected (duck-typed) — no top-level ``redis`` import
    so this module remains importable without redis installed.

    ``client.set(name, value, nx=True, ex=ttl_seconds)`` semantics:
      - Returns ``True`` when the key was newly set (first-seen) → return ``False``.
      - Returns ``None`` when the key already existed (duplicate) → return ``True``.
    """

    def __init__(
        self,
        client: Any,
        *,
        ttl_seconds: int = 86400,
        key_prefix: str = "pcp:live_write_ready:",
    ) -> None:
        self._client = client
        self._ttl = ttl_seconds
        self._prefix = key_prefix

    def check_and_record(self, key: str) -> bool:
        result = self._client.set(
            self._prefix + key, "1", nx=True, ex=self._ttl
        )
        # True → newly set (first-seen) → not a duplicate.
        # None → key already existed → duplicate.
        return result is not True


# ---------------------------------------------------------------------------
# Time helpers (now is injectable for deterministic tests).
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso8601(value: Any) -> datetime | None:
    """Parse an ISO 8601 timestamp (accepting a trailing 'Z'); None on failure."""
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


# ---------------------------------------------------------------------------
# Gate evaluation (pure, fail-closed).
# ---------------------------------------------------------------------------

def check_live_write_gate(
    assertion: dict | None, *, now: datetime | None = None
) -> tuple[bool, list[str]]:
    """Fail-closed evaluation of a LIVE_WRITE_READY assertion.

    Returns ``(permitted, reasons)``. ``permitted`` is True ONLY when the
    assertion is a dict, validates against the LIVE_WRITE_READY schema with zero
    errors, has ``status == "READY"``, is internally consistent
    (``live_write_performed is False`` and ``blocked_reasons == []``), and is not
    expired (``now <= valid_until``). Every other condition denies.
    """
    if not isinstance(assertion, dict):
        return (False, ["GATE_ABSENT"])
    if list(_VALIDATOR.iter_errors(assertion)):
        return (False, ["GATE_SCHEMA_INVALID"])
    if assertion.get("status") != "READY":
        reasons = list(assertion.get("blocked_reasons") or [])
        return (False, reasons or ["GATE_NOT_READY"])
    # Defense-in-depth: the schema already guarantees these under READY, but an
    # authorization gate must not single-source-of-truth on a sibling contract.
    if assertion.get("live_write_performed") is not False:
        return (False, ["GATE_INCONSISTENT"])
    if assertion.get("blocked_reasons") != []:
        return (False, ["GATE_INCONSISTENT"])
    # TTL: an expired (or unparseable/absent valid_until) assertion is denied.
    valid_until = _parse_iso8601(assertion.get("valid_until"))
    if valid_until is None:
        return (False, ["GATE_EXPIRED"])
    current = now or _utcnow()
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    if current > valid_until:
        return (False, ["GATE_EXPIRED"])
    return (True, [])


# ---------------------------------------------------------------------------
# Payload digest + result construction.
# ---------------------------------------------------------------------------

def _canonical_digest(operation: dict) -> str:
    """Lowercase SHA-256 hex of the canonical JSON encoding of *operation*."""
    canonical = json.dumps(operation, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _result(
    *,
    mode: str,
    permitted: bool,
    executed: bool,
    reasons: list[str],
    operation_ref: str | None,
    target_surface: str | None,
    writer_result: dict | None = None,
) -> dict:
    return {
        "schema_version": _RESULT_SCHEMA_VERSION,
        "mode": mode,
        "permitted": permitted,
        "executed": executed,
        "reasons": reasons,
        "operation_ref": operation_ref,
        "target_surface": target_surface,
        "is_authority": False,
        "writer_result": writer_result,
    }


# ---------------------------------------------------------------------------
# Mutation routing (the only write path).
# ---------------------------------------------------------------------------

def route_mutation(
    operation: dict,
    *,
    live_write_ready: dict | None = None,
    execute: bool = False,
    writer_registry: dict[str, Writer] | None = None,
    dedup_store: "DedupStore | None" = None,
    assertion_verifier: ReadyAssertionVerifier | None = None,
    authority_binding: AuthorityMapBinding | None = None,
    now: datetime | None = None,
) -> dict:
    """Route a single mutation through the fail-closed live-write gate.

    A writer is invoked ONLY at the final branch, reachable only when ALL of the
    following hold: a well-formed operation; a schema-valid, consistent,
    unexpired READY gate; operation_ref + target_surface + payload_digest binding
    to THIS operation; ``execute is True``; the gate's ``canonical_writer`` name
    resolves in ``writer_registry``; and the assertion_id is first-seen in
    ``dedup_store``. Every other branch returns without invoking any writer.

    ``dedup_store`` is a pluggable idempotency store (any object implementing
    ``check_and_record(key) -> bool``). When None, a throwaway
    ``InProcessDedupStore`` is used (no cross-call dedup).
    """
    # 1. Operation shape (fail-closed).
    if not isinstance(operation, dict):
        return _result(
            mode=_MODE_REJECTED, permitted=False, executed=False,
            reasons=["MALFORMED_OPERATION"], operation_ref=None, target_surface=None,
        )
    op_ref = operation.get("operation_ref")
    op_surface = operation.get("target_surface")
    if not (isinstance(op_ref, str) and op_ref and isinstance(op_surface, str) and op_surface):
        return _result(
            mode=_MODE_REJECTED, permitted=False, executed=False,
            reasons=["MALFORMED_OPERATION"],
            operation_ref=op_ref if isinstance(op_ref, str) else None,
            target_surface=op_surface if isinstance(op_surface, str) else None,
        )

    # 2. Gate (schema-valid + READY + consistent + unexpired).
    permitted, reasons = check_live_write_gate(live_write_ready, now=now)
    if not permitted:
        return _result(
            mode=_MODE_REJECTED, permitted=False, executed=False,
            reasons=reasons, operation_ref=op_ref, target_surface=op_surface,
        )
    gate: dict = live_write_ready  # type: ignore[assignment]  # known dict + READY

    # 3. Operation binding on operation_ref + target_surface.
    if gate.get("operation_ref") != op_ref or gate.get("target_surface") != op_surface:
        return _result(
            mode=_MODE_REJECTED, permitted=True, executed=False,
            reasons=["GATE_OPERATION_MISMATCH"], operation_ref=op_ref, target_surface=op_surface,
        )

    # 4. Payload-digest binding (exact operation payload).
    if _canonical_digest(operation) != gate.get("payload_digest"):
        return _result(
            mode=_MODE_REJECTED, permitted=True, executed=False,
            reasons=["PAYLOAD_DIGEST_MISMATCH"], operation_ref=op_ref, target_surface=op_surface,
        )

    # 5. Dry-run default — a live write requires ``execute is True`` exactly.
    if execute is not True:
        return _result(
            mode=_MODE_DRY_RUN, permitted=True, executed=False,
            reasons=[], operation_ref=op_ref, target_surface=op_surface,
        )

    # 6. Canonical-writer registry resolve (no default writer).
    registry = writer_registry or {}
    canonical_writer_name = gate.get("canonical_writer")
    writer = (
        registry.get(canonical_writer_name)
        if isinstance(canonical_writer_name, str)
        else None
    )
    if writer is None:
        return _result(
            mode=_MODE_REJECTED, permitted=True, executed=False,
            reasons=["CANONICAL_WRITER_NOT_REGISTERED"], operation_ref=op_ref, target_surface=op_surface,
        )

    # 6b. Assertion authentication — required when a writer registry is active.
    if requires_assertion_verification(execute=execute, writer_registry=registry):
        verifier = assertion_verifier or NoTrustedIssuerVerifier()
        try:
            auth_ok, auth_reasons = verifier.verify(gate, operation=operation)
        except Exception as exc:  # noqa: BLE001 — fail-closed on verifier failure.
            return _result(
                mode=_MODE_REJECTED, permitted=True, executed=False,
                reasons=["ASSERTION_VERIFY_FAILED:" + type(exc).__name__],
                operation_ref=op_ref, target_surface=op_surface,
            )
        if not auth_ok:
            return _result(
                mode=_MODE_REJECTED, permitted=True, executed=False,
                reasons=auth_reasons or ["ASSERTION_UNAUTHENTICATED"],
                operation_ref=op_ref, target_surface=op_surface,
            )

    # 6c. Authority-map binding — required when a writer registry is active.
    if requires_authority_binding(execute=execute, writer_registry=registry):
        binding = authority_binding or FailClosedAuthorityBinding()
        writer_name = canonical_writer_name if isinstance(canonical_writer_name, str) else ""
        try:
            bind_ok, bind_reasons = binding.authorize(
                target_surface=op_surface,
                canonical_writer=writer_name,
                operation=operation,
            )
        except Exception as exc:  # noqa: BLE001 — fail-closed on binding failure.
            return _result(
                mode=_MODE_REJECTED, permitted=True, executed=False,
                reasons=["AUTHORITY_BINDING_FAILED:" + type(exc).__name__],
                operation_ref=op_ref, target_surface=op_surface,
            )
        if not bind_ok:
            return _result(
                mode=_MODE_REJECTED, permitted=True, executed=False,
                reasons=bind_reasons or ["AUTHORITY_BINDING_DENIED"],
                operation_ref=op_ref, target_surface=op_surface,
            )

    # 7. Idempotency dedup on assertion_id (record BEFORE the call).
    key = gate.get("assertion_id")
    if not isinstance(key, str) or not key:
        # Unreachable for a schema-valid gate (assertion_id is required, minLength 1);
        # guarded defensively so a non-str key can never reach a dedup store.
        return _result(
            mode=_MODE_REJECTED, permitted=True, executed=False,
            reasons=["GATE_INCONSISTENT"], operation_ref=op_ref, target_surface=op_surface,
        )
    store = dedup_store if dedup_store is not None else InProcessDedupStore()
    if store.check_and_record(key):
        return _result(
            mode=_MODE_REJECTED, permitted=True, executed=False,
            reasons=["DUPLICATE_SUPPRESSED"], operation_ref=op_ref, target_surface=op_surface,
        )

    # 8. Delegate to the canonical writer — the ONLY write path.
    try:
        produced = writer(operation)
    except Exception as exc:  # noqa: BLE001 — fail-closed reporting on writer failure.
        return _result(
            mode=_MODE_REJECTED, permitted=True, executed=False,
            reasons=["WRITER_RAISED:" + type(exc).__name__],
            operation_ref=op_ref, target_surface=op_surface,
        )
    writer_result = produced if isinstance(produced, dict) else {"result": produced}
    return _result(
        mode=_MODE_LIVE, permitted=True, executed=True, reasons=[],
        operation_ref=op_ref, target_surface=op_surface, writer_result=writer_result,
    )


# ---------------------------------------------------------------------------
# FastAPI surface (thin — all logic lives in route_mutation).
# ---------------------------------------------------------------------------

class MutateRequest(BaseModel):
    """Request body for POST /bridge/mutate.

    ``execute`` is a ``StrictBool``: a non-boolean JSON value (e.g. ``1`` or
    ``"yes"``) is rejected with HTTP 422 rather than coerced to ``True``. This
    preserves the ``execute is True`` strictness of ``route_mutation`` at the
    HTTP boundary — a client cannot accidentally trigger a live write by sending
    a truthy non-boolean.
    """

    operation: dict
    live_write_ready: dict | None = None
    execute: StrictBool = False


def create_bridge_router(
    *,
    writer_registry: dict[str, Writer] | None = None,
    dedup_store: "DedupStore | None" = None,
    assertion_verifier: ReadyAssertionVerifier | None = None,
    authority_binding: AuthorityMapBinding | None = None,
) -> APIRouter:
    """Build the bridge ``APIRouter``.

    ``writer_registry`` defaults to None, so a deployed app can NEVER perform a
    live write (every execute attempt resolves no writer and is rejected).
    Registering a real writer is an explicit, deliberate caller action. The
    router keeps a private idempotency store so replayed assertion_ids are
    suppressed across requests.

    ``dedup_store`` defaults to None, in which case a private
    ``InProcessDedupStore`` is created for this router instance. Pass an
    external store (e.g. ``RedisDedupStore``) for cross-worker dedup.
    """
    router = APIRouter(tags=["PCP Bridge"])
    _dedup_store: DedupStore = dedup_store if dedup_store is not None else InProcessDedupStore()

    @router.post("/bridge/mutate")
    async def mutate(req: MutateRequest) -> JSONResponse:
        result = route_mutation(
            req.operation,
            live_write_ready=req.live_write_ready,
            execute=req.execute,
            writer_registry=writer_registry,
            dedup_store=_dedup_store,
            assertion_verifier=assertion_verifier,
            authority_binding=authority_binding,
        )
        code = (
            http_status.HTTP_403_FORBIDDEN
            if result["mode"] == _MODE_REJECTED
            else http_status.HTTP_200_OK
        )
        return JSONResponse(status_code=code, content=result)

    return router


def create_bridge_app(
    *,
    writer_registry: dict[str, Writer] | None = None,
    dedup_store: "DedupStore | None" = None,
    assertion_verifier: ReadyAssertionVerifier | None = None,
    authority_binding: AuthorityMapBinding | None = None,
) -> FastAPI:
    """Build a standalone FastAPI app mounting the bridge router.

    Defaults to no writer registry — dry-run / reject only.
    ``dedup_store`` is forwarded to the bridge router.
    """
    app = FastAPI(title="PCP Live-Write Bridge", version="0.1.0")
    app.include_router(
        create_bridge_router(
            writer_registry=writer_registry,
            dedup_store=dedup_store,
            assertion_verifier=assertion_verifier,
            authority_binding=authority_binding,
        )
    )
    return app
