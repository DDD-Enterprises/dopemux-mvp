"""Read-only HTTP client for backend adapters.

Exposes ONLY ``get()`` and ``post_read()`` — there is **no** put/patch/delete
and **no** generic ``request(method, ...)``, so mutating HTTP methods are
structurally unreachable. ``post_read`` additionally rejects any path that is
not in an explicit read-path allowlist (the two side-effect-free dope-memory
read routes). The underlying transport asserts method ∈ {GET, POST}.

Security posture:
- ``base_url`` and ``workspace_id`` are registry-owned (the resolver supplies
  them); a caller never provides a URL/host/port/path.
- ``base_url`` host MUST be loopback (SSRF guard) — a misconfigured/compromised
  registry cannot redirect the facade off-host.
- All calls time out and fail closed (`ReadOnlyHttpError`); the facade maps that
  to a `PARTIAL`/`BLOCKED` envelope, never fabricated data.

``httpx`` is imported lazily (only when a real call runs), so the package
imports/compiles without it. Tests inject a fake transport and make no live
network calls.
"""

from __future__ import annotations

import ipaddress
import json as _json
from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import urlparse

DEFAULT_TIMEOUT = 10.0

# Hard cap on a backend response body (DoS guard); a larger response fails closed.
MAX_RESPONSE_BYTES = 2_000_000


class ReadOnlyHttpError(Exception):
    """Raised for any refused or failed read-only backend call (fail closed)."""


@dataclass(frozen=True)
class HttpResponse:
    status: int
    json: Any
    ok: bool


# Transport signature: (method, url, params, json, timeout) -> HttpResponse
Transport = Callable[..., HttpResponse]


def _is_loopback(host: str) -> bool:
    """True only for loopback. IP literals use ipaddress.is_loopback (so
    127.0.0.0/8 and ::1 pass; 0.0.0.0, ::ffff:127.0.0.1, and routable IPs fail);
    the only allowed hostname is ``localhost`` (trailing dot normalized)."""
    h = (host or "").strip().rstrip(".").lower()
    if not h:
        return False
    if h == "localhost":
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def _validate_base_url(base_url: str) -> None:
    u = urlparse(base_url)
    if u.scheme not in ("http", "https"):
        raise ReadOnlyHttpError(f"base_url scheme not allowed: {u.scheme!r}")
    if not _is_loopback(u.hostname or ""):
        raise ReadOnlyHttpError("base_url host is not loopback")


def _join(base_url: str, path: str) -> str:
    if not path.startswith("/"):
        raise ReadOnlyHttpError("path must be absolute (start with '/')")
    if "?" in path or "#" in path:
        raise ReadOnlyHttpError("path must not include a query or fragment")
    return base_url.rstrip("/") + path


def _default_transport(
    *, method: str, url: str, params: Any, json: Any, timeout: float
) -> HttpResponse:
    if method not in ("GET", "POST"):  # belt-and-suspenders: never a mutating verb
        raise ReadOnlyHttpError(f"method not allowed: {method}")
    import httpx  # lazy import — only needed for real calls

    # Stream the body so an oversized response fails closed before it is fully
    # buffered (DoS guard). JSON is parsed only for a 2xx response.
    with httpx.Client(timeout=timeout) as client:
        with client.stream(method, url, params=params, json=json) as resp:
            status = resp.status_code
            ok = resp.is_success
            total = 0
            chunks: list[bytes] = []
            for chunk in resp.iter_bytes():
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    raise ReadOnlyHttpError("backend response too large")
                chunks.append(chunk)
    body: Any = None
    if ok and chunks:
        try:
            body = _json.loads(b"".join(chunks).decode("utf-8", errors="replace"))
        except ValueError:
            body = None
    return HttpResponse(status=status, json=body, ok=ok)


class ReadOnlyHttpClient:
    """A read-only HTTP client. Only GET and explicit POST-reads are possible."""

    def __init__(self, transport: Optional[Transport] = None, timeout: float = DEFAULT_TIMEOUT):
        self._transport = transport or _default_transport
        self._timeout = timeout

    def get(self, base_url: str, path: str, params: Optional[dict] = None) -> HttpResponse:
        _validate_base_url(base_url)
        return self._call("GET", _join(base_url, path), params, None)

    def post_read(
        self,
        base_url: str,
        path: str,
        json_body: dict,
        allowed_read_paths: frozenset,
    ) -> HttpResponse:
        if path not in allowed_read_paths:
            raise ReadOnlyHttpError(f"POST path not in read allowlist: {path}")
        _validate_base_url(base_url)
        return self._call("POST", _join(base_url, path), None, json_body)

    def _call(self, method: str, url: str, params: Any, json_body: Any) -> HttpResponse:
        try:
            return self._transport(
                method=method, url=url, params=params, json=json_body, timeout=self._timeout
            )
        except ReadOnlyHttpError:
            raise
        except Exception as exc:  # timeout, connection error, etc. → fail closed
            raise ReadOnlyHttpError(f"backend call failed: {exc}") from exc
