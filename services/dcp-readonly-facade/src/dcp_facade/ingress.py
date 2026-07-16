"""Provider-neutral authenticated ASGI ingress for loopback MCP (TP-0014).

Auth runs before any MCP discovery/dispatch path. This module does not open
sockets; see ``loopback_server`` for pinned loopback binding.
"""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Iterable, Mapping, MutableMapping, Optional

from .auth_context import (
    GENERIC_AUTH_FAILURE,
    ConnectorAuthContext,
    MappingSecretResolver,
    SecretResolver,
    authenticate_bearer,
    strip_untrusted_connector_headers,
    verify_context_seal,
)
from .connector_policy import ConnectorPolicyStore
from .ingress_audit import IngressAuditEvent, IngressAuditLog, now_ts
from .rate_limit import ConnectorRateLimiter, RateLimitConfig

ASGIApp = Callable[[dict, Callable, Callable], Awaitable[None]]

# Paths that never disclose tools and may be unauthenticated.
HEALTH_PATHS = frozenset({"/health", "/healthz"})
# MCP/discovery/dispatch paths require authentication.
PROTECTED_PREFIXES = ("/mcp", "/sse", "/messages", "/message")


def _headers_map(scope_headers: Iterable[tuple[bytes, bytes]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in scope_headers:
        out[key.decode("latin-1")] = value.decode("latin-1")
    return out


def _header_get(headers: Mapping[str, str], name: str) -> Optional[str]:
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def _client_host(scope: Mapping[str, Any]) -> Optional[str]:
    client = scope.get("client")
    if isinstance(client, (list, tuple)) and client:
        return str(client[0])
    return None


def _json_response(status: int, body: dict[str, Any]) -> tuple[int, list[tuple[bytes, bytes]], bytes]:
    payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(payload)).encode("ascii")),
        (b"cache-control", b"no-store"),
    ]
    return status, headers, payload


async def _send_raw(send: Callable, status: int, headers: list[tuple[bytes, bytes]], body: bytes) -> None:
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body, "more_body": False})


def is_protected_path(path: str) -> bool:
    if path in HEALTH_PATHS:
        return False
    return any(path == prefix or path.startswith(prefix + "/") for prefix in PROTECTED_PREFIXES)


class AuthIngressMiddleware:
    """ASGI middleware: strip forgeable headers, authenticate, rate-limit, audit."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        policy_store: ConnectorPolicyStore,
        secret_resolver: Optional[SecretResolver] = None,
        audit_log: Optional[IngressAuditLog] = None,
        rate_limiter: Optional[ConnectorRateLimiter] = None,
        require_auth_for_all_non_health: bool = True,
    ) -> None:
        self.app = app
        self.policy_store = policy_store
        self.secret_resolver = secret_resolver or MappingSecretResolver({})
        self.audit_log = audit_log or IngressAuditLog()
        self.rate_limiter = rate_limiter or ConnectorRateLimiter()
        self.require_auth_for_all_non_health = require_auth_for_all_non_health

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or "/"
        method = (scope.get("method") or "GET").upper()
        raw_headers = _headers_map(scope.get("headers") or [])
        cleaned_headers, redactions = strip_untrusted_connector_headers(raw_headers)
        client_host = _client_host(scope)

        # Rebuild scope headers without forgeable connector claims; redact bearer
        # is only for outbound audit copies — the app still needs Authorization
        # for auth, so keep original Authorization in a private auth view.
        auth_header = _header_get(raw_headers, "authorization")
        scope_headers = []
        for key, value in cleaned_headers.items():
            if key.lower() == "authorization":
                # Do not forward raw Authorization to the inner app.
                continue
            scope_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
        scope = dict(scope)
        scope["headers"] = scope_headers
        state: MutableMapping[str, Any] = scope.setdefault("state", {})  # type: ignore[assignment]

        if path in HEALTH_PATHS:
            status, headers, body = _json_response(
                200,
                {
                    "status": "ok",
                    "service": "dcp-readonly-facade-ingress",
                    "auth_required_for_mcp": True,
                },
            )
            self.audit_log.record(
                IngressAuditEvent(
                    ts=now_ts(),
                    decision="allow_health",
                    path=path,
                    method=method,
                    status_code=status,
                    reason="health",
                    client_host=client_host,
                    redactions=redactions,
                )
            )
            await _send_raw(send, status, headers, body)
            return

        needs_auth = is_protected_path(path) or self.require_auth_for_all_non_health
        if not needs_auth:
            await self.app(scope, receive, send)
            return

        context, decision = authenticate_bearer(
            self.policy_store,
            authorization_header=auth_header,
            secret_resolver=self.secret_resolver,
        )
        if not decision.allowed or context is None or not verify_context_seal(context):
            status, headers, body = _json_response(
                401,
                {"error": GENERIC_AUTH_FAILURE, "status": "BLOCKED"},
            )
            self.audit_log.record(
                IngressAuditEvent(
                    ts=now_ts(),
                    decision="deny_auth",
                    path=path,
                    method=method,
                    status_code=status,
                    reason=GENERIC_AUTH_FAILURE,
                    client_host=client_host,
                    redactions=redactions + ["secrets"],
                )
            )
            await _send_raw(send, status, headers, body)
            return

        rate_cfg = RateLimitConfig(
            requests_per_minute=context.rate_limit_rpm,
            burst=context.rate_limit_burst,
            max_concurrent=context.rate_limit_max_concurrent,
        )
        rate = self.rate_limiter.allow(context.connector_id, rate_cfg)
        if not rate.allowed:
            status, headers, body = _json_response(
                429,
                {"error": "rate limit exceeded", "status": "BLOCKED"},
            )
            headers.append((b"retry-after", str(int(rate.retry_after_seconds or 1)).encode("ascii")))
            self.audit_log.record(
                IngressAuditEvent(
                    ts=now_ts(),
                    decision="deny_rate",
                    path=path,
                    method=method,
                    connector_id=context.connector_id,
                    credential_fingerprint=context.credential_fingerprint,
                    audit_label=context.audit_label,
                    status_code=status,
                    reason=rate.reason,
                    client_host=client_host,
                    redactions=redactions,
                )
            )
            await _send_raw(send, status, headers, body)
            return

        state["connector_auth_context"] = context
        state["connector_id"] = context.connector_id

        status_box = {"code": 200}

        async def send_wrapper(message: dict) -> None:
            if message.get("type") == "http.response.start":
                status_box["code"] = int(message.get("status") or 200)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            self.audit_log.record(
                IngressAuditEvent(
                    ts=now_ts(),
                    decision="allow",
                    path=path,
                    method=method,
                    connector_id=context.connector_id,
                    credential_fingerprint=context.credential_fingerprint,
                    audit_label=context.audit_label,
                    status_code=status_box["code"],
                    reason="authenticated",
                    client_host=client_host,
                    redactions=redactions,
                )
            )
        finally:
            self.rate_limiter.release(context.connector_id)


def build_protected_mcp_placeholder_app(
    *,
    tool_names: Optional[list[str]] = None,
) -> ASGIApp:
    """Minimal authenticated MCP-like app used when FastMCP HTTP app is unavailable.

    Only reachable after AuthIngressMiddleware allows the request.
    """

    tools = tool_names or [
        "list_targets",
        "get_target_capabilities",
        "get_target_repo_state_snapshot",
        "list_target_proof_bundles",
        "fetch_target_proof_bundle",
        "get_target_runtime_receipt",
    ]

    async def app(scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            return
        path = scope.get("path") or "/"
        method = (scope.get("method") or "GET").upper()
        state = scope.get("state") or {}
        context = state.get("connector_auth_context")
        if not isinstance(context, ConnectorAuthContext) or not verify_context_seal(context):
            status, headers, body = _json_response(401, {"error": GENERIC_AUTH_FAILURE})
            await _send_raw(send, status, headers, body)
            return

        if path.startswith("/mcp") and method in {"GET", "POST"}:
            # Discovery payload only after auth.
            allowed = [name for name in tools if name in context.allowed_tools and name not in context.denied_tools]
            status, headers, body = _json_response(
                200,
                {
                    "status": "OK",
                    "authenticated_connector": context.connector_id,
                    "tools": [{"name": name} for name in allowed],
                    "transport": "streamable-http-loopback",
                },
            )
            await _send_raw(send, status, headers, body)
            return

        status, headers, body = _json_response(404, {"error": "not found"})
        await _send_raw(send, status, headers, body)

    return app
