"""Request identity for dope-memory HTTP writes (Wave 2A R2, W01).

What this module does
- ``AuthGate`` verifies a bearer token on a write: SHA-256 of the token string,
  compared with ``hmac.compare_digest`` against a hash file, yielding a
  principal such as ``runner:codex`` or the literal ``unverified``.
- Three modes from one env setting, ``DOPE_MEMORY_AUTH_MODE`` (default ``log``):
  ``off``      never verify; every write is recorded ``unverified``;
  ``log``      verify; accept everything; record the verified principal or
               ``unverified`` and count unverified calls per caller;
  ``enforce``  as ``log`` but reject an unverified write with 401.
- ``validate_write_ids`` fills an omitted ``workspace_id`` from the container's
  binding (``DOPE_MEMORY_WORKSPACE_ID``) and an omitted ``instance_id`` from the
  server's default instance, rejects a supplied ``workspace_id`` that differs
  from the binding, and rejects every write when there is no binding
  (Amendment 04).
- ``WriteAuthMiddleware`` answers a real HTTP 401 for an unverified MCP
  ``tools/call`` of a mutating tool in ``enforce`` mode.

Hash file (written by the ``dopemux auth`` helper, read-only here)
- ``$DOPE_MEMORY_AUTH_DIR/memory-token-hashes.json``: a JSON object mapping the
  lowercase hex SHA-256 of a token to its principal, for example
  ``{"<64 hex>": "runner:codex"}``. Principals match
  ``(runner|internal):<name>``. Malformed entries are skipped; an unreadable or
  non-object file verifies nothing (fail closed). The file is re-read when its
  mtime or size changes, so rotation needs no restart.

Never logged: the Authorization header, a token, or a hash. Only principal
names and caller labels appear in logs and in the health counters.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, Optional

logger = logging.getLogger(__name__)

AUTH_MODES = ("off", "log", "enforce")
DEFAULT_AUTH_MODE = "log"
ENV_AUTH_MODE = "DOPE_MEMORY_AUTH_MODE"
ENV_AUTH_DIR = "DOPE_MEMORY_AUTH_DIR"
HASH_FILE_NAME = "memory-token-hashes.json"
UNVERIFIED_PRINCIPAL = "unverified"

# Every mutating tool. memory_mark_issue writes nothing today but is mutating
# by name (W00 Q6), so it is gated like the rest.
WRITE_TOOLS = frozenset(
    {
        "memory_store",
        "memory_correct",
        "memory_link_resolution",
        "memory_generate_reflection",
        "memory_mark_issue",
    }
)

MAX_TRACKED_CALLERS = 100
MAX_TOKEN_CHARS = 512
MAX_CALLER_LABEL_CHARS = 64
MAX_BODY_BYTES = 4 * 1024 * 1024

# `\Z`, not `$`: `$` also matches before a trailing newline.
_PRINCIPAL_RE = re.compile(r"^(runner|internal):[a-z0-9][a-z0-9_.-]{0,63}\Z")
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}\Z")
_NON_PRINTABLE_RE = re.compile(r"[^\x20-\x7e]")


class Unauthorized(Exception):
    """An unverified write was refused in ``enforce`` mode."""


class WriteIdentityError(ValueError):
    """A write names a workspace that is not this server's, or the server has none."""


@dataclass(frozen=True)
class Identity:
    principal: str
    verified: bool


UNVERIFIED = Identity(principal=UNVERIFIED_PRINCIPAL, verified=False)


def load_auth_mode(env: Optional[Mapping[str, str]] = None) -> str:
    """Return the auth mode from the environment; unknown values are an error."""
    source = os.environ if env is None else env
    raw = (source.get(ENV_AUTH_MODE) or "").strip().lower()
    if not raw:
        return DEFAULT_AUTH_MODE
    if raw not in AUTH_MODES:
        raise ValueError(
            f"{ENV_AUTH_MODE}={raw!r} is not one of {', '.join(AUTH_MODES)}"
        )
    return raw


def caller_label(user_agent: Optional[str], client_host: Optional[str]) -> str:
    """A short, log-safe label for an unverified caller (never a credential)."""
    label = _NON_PRINTABLE_RE.sub("", user_agent or "").strip()[:MAX_CALLER_LABEL_CHARS]
    return label or (client_host or "").strip()[:MAX_CALLER_LABEL_CHARS] or "unknown"


def validate_write_ids(
    workspace_id: Optional[str],
    instance_id: Optional[str],
    bound_workspace_id: Optional[str],
    default_instance_id: str = "A",
) -> tuple[str, str]:
    """Resolve a write's ids against this server's binding (Amendment 04).

    Returns ``(workspace_id, instance_id)``. An omitted, empty or blank
    ``workspace_id`` becomes ``bound_workspace_id``; an omitted, empty or blank
    ``instance_id`` becomes ``default_instance_id``. A supplied value is never
    replaced. Raises ``WriteIdentityError`` when the server has no binding
    (every write is rejected) or when a supplied ``workspace_id`` differs from it.
    """
    if not bound_workspace_id:
        raise WriteIdentityError(
            "this dope-memory server has no workspace binding "
            "(DOPE_MEMORY_WORKSPACE_ID is unset); writes are rejected"
        )
    if workspace_id is None or not str(workspace_id).strip():
        workspace_id = bound_workspace_id
    elif workspace_id != bound_workspace_id:
        raise WriteIdentityError(
            f"workspace_id {str(workspace_id)[:128]!r} does not match this "
            f"server's bound workspace {bound_workspace_id!r}; write rejected"
        )
    if instance_id is None or not str(instance_id).strip():
        instance_id = default_instance_id
    return workspace_id, instance_id


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    if not token or len(token) > MAX_TOKEN_CHARS:
        return None
    return token


class AuthGate:
    """Verifies bearer tokens and counts unverified callers."""

    def __init__(self, mode: str, auth_dir: Optional[Path | str] = None):
        if mode not in AUTH_MODES:
            raise ValueError(f"invalid auth mode {mode!r}; use one of {', '.join(AUTH_MODES)}")
        self.mode = mode
        self._hash_path = Path(auth_dir) / HASH_FILE_NAME if auth_dir else None
        self._lock = threading.Lock()
        self._stamp: Optional[tuple[int, int]] = None
        self._hashes: dict[str, str] = {}
        self._status = "unconfigured" if self._hash_path is None else "missing"
        self._unverified: dict[str, int] = {}

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None) -> "AuthGate":
        source = os.environ if env is None else env
        return cls(load_auth_mode(source), (source.get(ENV_AUTH_DIR) or "").strip() or None)

    # -- hash file ---------------------------------------------------------

    def _refresh(self) -> tuple[dict[str, str], str]:
        if self._hash_path is None:
            return {}, "unconfigured"
        with self._lock:
            try:
                stat = self._hash_path.stat()
            except OSError:
                self._stamp, self._hashes, self._status = None, {}, "missing"
                return self._hashes, self._status
            stamp = (stat.st_mtime_ns, stat.st_size)
            if stamp != self._stamp:
                self._stamp = stamp
                self._hashes, self._status = self._read_hash_file()
            return self._hashes, self._status

    def _read_hash_file(self) -> tuple[dict[str, str], str]:
        assert self._hash_path is not None
        try:
            data = json.loads(self._hash_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.error("dope-memory auth hash file is unreadable or not JSON")
            return {}, "invalid"
        if not isinstance(data, dict):
            logger.error("dope-memory auth hash file is not a JSON object")
            return {}, "invalid"
        hashes: dict[str, str] = {}
        skipped = 0
        for digest, principal in data.items():
            if (
                isinstance(digest, str)
                and isinstance(principal, str)
                and _SHA256_HEX_RE.match(digest)
                and _PRINCIPAL_RE.match(principal)
            ):
                hashes[digest] = principal
            else:
                skipped += 1
        if skipped:
            logger.warning("dope-memory auth hash file: skipped %d malformed entries", skipped)
        return hashes, "ok"

    # -- verification ----------------------------------------------------------

    def authenticate(self, authorization: Optional[str]) -> Identity:
        """Return the verified principal for a header value, else ``unverified``."""
        token = _extract_bearer(authorization)
        if token is None:
            return UNVERIFIED
        hashes, _ = self._refresh()
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        matched: Optional[str] = None
        for stored, principal in hashes.items():
            # No early exit: every stored hash is compared.
            if hmac.compare_digest(digest, stored):
                matched = principal
        return Identity(matched, True) if matched else UNVERIFIED

    def record_unverified(self, caller: str) -> None:
        with self._lock:
            if caller in self._unverified:
                self._unverified[caller] += 1
                return
            if len(self._unverified) < MAX_TRACKED_CALLERS:
                self._unverified[caller] = 1
                logger.warning("unverified dope-memory write from caller=%s", caller)
            else:
                self._unverified["other"] = self._unverified.get("other", 0) + 1

    def authorize_write(self, authorization: Optional[str], caller: str) -> Identity:
        """Apply the mode to a write; return the identity to store with it."""
        if self.mode == "off":
            return UNVERIFIED
        identity = self.authenticate(authorization)
        if identity.verified:
            return identity
        self.record_unverified(caller)
        if self.mode == "enforce":
            raise Unauthorized(
                "unauthorized (401): a valid bearer token is required for writes "
                "while the auth mode is 'enforce'"
            )
        return identity

    def health_fields(self) -> dict[str, Any]:
        """Fields the health route reports (read by the generator gate and doctor)."""
        _, status = self._refresh()
        with self._lock:
            counts = dict(self._unverified)
        # identity_required_writes stays True: it means writes are bound to this
        # server's workspace (a mismatched workspace is rejected), not that the
        # caller must send the ids (omitted ids are filled from the binding).
        return {
            "auth_mode": self.mode,
            "identity_required_writes": True,
            "auth_hash_file": status,
            "auth_unverified_calls": counts,
        }


# --------------------------------------------------------------------------- ASGI

_Scope = dict
_Message = dict
_Receive = Callable[[], Awaitable[_Message]]
_Send = Callable[[_Message], Awaitable[None]]


def _scope_header(scope: _Scope, name: bytes) -> Optional[str]:
    for key, value in scope.get("headers") or []:
        if key.lower() == name:
            return value.decode("latin-1")
    return None


def _count_write_calls(payload: Any) -> int:
    items = payload if isinstance(payload, list) else [payload]
    count = 0
    for item in items:
        if isinstance(item, dict) and item.get("method") == "tools/call":
            params = item.get("params")
            if isinstance(params, dict) and params.get("name") in WRITE_TOOLS:
                count += 1
    return count


async def _respond(send: _Send, status: int, payload: dict, extra: Optional[list] = None) -> None:
    body = json.dumps(payload).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("ascii")),
    ]
    headers.extend(extra or [])
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


class WriteAuthMiddleware:
    """HTTP 401 for an unverified mutating MCP ``tools/call`` in ``enforce`` mode.

    Only ``POST /mcp`` is inspected. The body is buffered (up to
    ``max_body_bytes``), parsed as JSON-RPC (single or batch), and replayed
    unchanged to the wrapped app. Unparseable bodies and non-write traffic pass
    through untouched; the tool itself re-checks authorization, so this layer
    only adds the early HTTP status.
    """

    def __init__(
        self,
        app: Any,
        get_gate: Callable[[], AuthGate],
        max_body_bytes: int = MAX_BODY_BYTES,
    ):
        self.app = app
        self.get_gate = get_gate
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: _Scope, receive: _Receive, send: _Send) -> None:
        if (
            scope.get("type") != "http"
            or scope.get("method") != "POST"
            or scope.get("path") != "/mcp"
        ):
            await self.app(scope, receive, send)
            return

        messages: list[_Message] = []
        body = bytearray()
        while True:
            message = await receive()
            messages.append(message)
            if message.get("type") != "http.request":
                break
            body.extend(message.get("body", b""))
            if len(body) > self.max_body_bytes:
                await _respond(send, 413, {"error": "request body too large"})
                return
            if not message.get("more_body", False):
                break

        pending = list(messages)

        async def replay() -> _Message:
            if pending:
                return pending.pop(0)
            return await receive()

        gate = self.get_gate()
        if gate.mode == "enforce":
            try:
                writes = _count_write_calls(json.loads(bytes(body)))
            except (ValueError, RecursionError):
                writes = 0
            if writes:
                identity = gate.authenticate(_scope_header(scope, b"authorization"))
                if not identity.verified:
                    client = scope.get("client")
                    caller = caller_label(
                        _scope_header(scope, b"user-agent"), client[0] if client else None
                    )
                    for _ in range(writes):
                        gate.record_unverified(caller)
                    await _respond(
                        send,
                        401,
                        {
                            "error": "unauthorized",
                            "detail": "a valid bearer token is required for writes",
                        },
                        [(b"www-authenticate", b"Bearer")],
                    )
                    return

        await self.app(scope, replay, send)
