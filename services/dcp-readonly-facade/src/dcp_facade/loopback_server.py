"""Pinned loopback Streamable HTTP server lifecycle (TP-DCP-MCP-RO-0014).

Only loopback hosts are accepted. Public binds (0.0.0.0, ::, LAN IPs) fail closed.
"""

from __future__ import annotations

import os
import socket
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import uvicorn

from .auth_context import MappingSecretResolver, SecretResolver
from .connector_policy import ConnectorPolicyStore, load_connector_policy_path
from .ingress import AuthIngressMiddleware, ASGIApp, build_protected_mcp_placeholder_app
from .ingress_audit import IngressAuditLog
from .rate_limit import ConnectorRateLimiter

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
ENV_HOST = "DCP_FACADE_INGRESS_HOST"
ENV_PORT = "DCP_FACADE_INGRESS_PORT"
ENV_POLICY = "DCP_FACADE_CONNECTOR_POLICY"


class NonLoopbackBindError(ValueError):
    """Raised when a non-loopback bind is requested."""


def assert_loopback_host(host: str) -> str:
    normalized = (host or "").strip().lower()
    if normalized not in LOOPBACK_HOSTS:
        raise NonLoopbackBindError(
            f"refusing non-loopback ingress bind host={host!r}; allowed={sorted(LOOPBACK_HOSTS)}"
        )
    # Prefer IPv4 loopback for deterministic tests and socket proof.
    if normalized == "localhost":
        return "127.0.0.1"
    return "127.0.0.1" if normalized == "127.0.0.1" else normalized


@dataclass
class IngressHealth:
    running: bool
    host: Optional[str]
    port: Optional[int]
    bind: Optional[str]
    auth_required: bool = True
    transport: str = "streamable-http-loopback"


class LoopbackIngressServer:
    """Deterministic start/stop/health for the authenticated loopback ingress."""

    def __init__(
        self,
        *,
        app: Optional[ASGIApp] = None,
        policy_store: Optional[ConnectorPolicyStore] = None,
        secret_resolver: Optional[SecretResolver] = None,
        audit_log: Optional[IngressAuditLog] = None,
        rate_limiter: Optional[ConnectorRateLimiter] = None,
        host: str = DEFAULT_HOST,
        port: int = 0,
    ) -> None:
        self.host = assert_loopback_host(host)
        self.port = int(port)
        self.audit_log = audit_log or IngressAuditLog()
        self.rate_limiter = rate_limiter or ConnectorRateLimiter()
        self.policy_store = policy_store or ConnectorPolicyStore()
        self.secret_resolver = secret_resolver or MappingSecretResolver({})
        inner = app or build_protected_mcp_placeholder_app()
        self.app = AuthIngressMiddleware(
            inner,
            policy_store=self.policy_store,
            secret_resolver=self.secret_resolver,
            audit_log=self.audit_log,
            rate_limiter=self.rate_limiter,
        )
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None
        self._bound_host: Optional[str] = None
        self._bound_port: Optional[int] = None

    @property
    def bound_url(self) -> Optional[str]:
        if self._bound_host is None or self._bound_port is None:
            return None
        return f"http://{self._bound_host}:{self._bound_port}"

    def health(self) -> IngressHealth:
        running = bool(self._server is not None and self._thread is not None and self._thread.is_alive())
        return IngressHealth(
            running=running,
            host=self._bound_host,
            port=self._bound_port,
            bind=f"{self._bound_host}:{self._bound_port}" if running else None,
        )

    def start(self, *, timeout_seconds: float = 5.0) -> IngressHealth:
        if self.health().running:
            return self.health()

        host = assert_loopback_host(self.host)
        config = uvicorn.Config(
            self.app,
            host=host,
            port=self.port,
            log_level="warning",
            access_log=False,
            lifespan="off",
        )
        server = uvicorn.Server(config)
        # Prevent uvicorn installing signal handlers in a thread.
        server.install_signal_handlers = lambda: None  # type: ignore[method-assign]

        thread = threading.Thread(target=server.run, name="dcp-loopback-ingress", daemon=True)
        self._server = server
        self._thread = thread
        thread.start()

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            # uvicorn sets server.servers after bind
            servers = getattr(server, "servers", None) or []
            for srv in servers:
                sockets = getattr(srv, "sockets", None) or []
                for sock in sockets:
                    try:
                        name = sock.getsockname()
                    except OSError:
                        continue
                    bound_host, bound_port = name[0], int(name[1])
                    # Force loopback proof even if platform returns expanded form.
                    if bound_host not in LOOPBACK_HOSTS and not str(bound_host).startswith("127."):
                        self.stop()
                        raise NonLoopbackBindError(f"bound non-loopback address: {bound_host}")
                    self._bound_host = "127.0.0.1" if bound_host in {"127.0.0.1", "localhost"} else bound_host
                    self._bound_port = bound_port
                    return self.health()
            if server.started:
                # Port may be available via config if already started.
                if self.port and self.port > 0:
                    self._bound_host = host
                    self._bound_port = self.port
                    return self.health()
            time.sleep(0.02)

        self.stop()
        raise TimeoutError("loopback ingress failed to bind in time")

    def stop(self, *, timeout_seconds: float = 5.0) -> IngressHealth:
        server = self._server
        thread = self._thread
        if server is not None:
            server.should_exit = True
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout_seconds)
        self._server = None
        self._thread = None
        self._bound_host = None
        self._bound_port = None
        return self.health()


def resolve_inner_mcp_app() -> ASGIApp:
    """Prefer FastMCP HTTP app when installed; otherwise authenticated placeholder."""
    try:
        from mcp.server import mcp  # type: ignore

        for attr in ("http_app", "streamable_http_app", "sse_app"):
            factory = getattr(mcp, attr, None)
            if callable(factory):
                app = factory()
                if app is not None:
                    return app
    except Exception:
        pass
    return build_protected_mcp_placeholder_app()


def build_server_from_env(
    *,
    secret_resolver: Optional[SecretResolver] = None,
    policy_store: Optional[ConnectorPolicyStore] = None,
) -> LoopbackIngressServer:
    host = assert_loopback_host(os.getenv(ENV_HOST, DEFAULT_HOST))
    port = int(os.getenv(ENV_PORT, str(DEFAULT_PORT)))
    store = policy_store
    if store is None:
        policy_path = os.getenv(ENV_POLICY)
        if policy_path:
            store = load_connector_policy_path(Path(policy_path).expanduser())
        else:
            store = ConnectorPolicyStore()
            store.warnings.append("no connector policy configured; all MCP auth will fail closed")
    return LoopbackIngressServer(
        app=resolve_inner_mcp_app(),
        policy_store=store,
        secret_resolver=secret_resolver,
        host=host,
        port=port,
    )


def run_loopback_ingress_forever() -> None:
    """CLI entry used by server.main for streamable-http transport."""
    server = build_server_from_env()
    health = server.start()
    print(
        f"dcp-readonly-facade loopback ingress listening on {health.bind} "
        f"(auth required for /mcp; health on /health)",
        flush=True,
    )
    try:
        while server.health().running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


def probe_loopback_bind(host: str = "127.0.0.1", port: int = 0) -> tuple[str, int]:
    """Pure socket proof helper: bind loopback and return actual host/port."""
    host = assert_loopback_host(host)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        bound_host, bound_port = sock.getsockname()[:2]
        return bound_host, int(bound_port)
