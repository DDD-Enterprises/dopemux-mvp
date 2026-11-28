"""Read-only qualification and process-bound custody for authenticated bridges."""

from __future__ import annotations

import http.client
import json
import os
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator

from . import docker_inspect as di
from . import launcher
from .envrc import safe_port_int
from .lifecycle import runtime_dir_for
from .locks import instance_lock
from .reap import ATTACHED_DIR, attach, detach
from .runtime_state import ENVRC_FILENAME, resolve_identity_view
from .stdio_proxy import BackendSpec

API_ONLY_POLICY = "DOPEMUX_MCP_BRIDGE_REQUIRE_API_ONLY"
HEALTH_LIMIT = 1 << 16
HEALTH_TIMEOUT = 3.0


class BridgeRuntimeError(RuntimeError):
    """A sanitized, terminal refusal before credentials can be dispatched."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_HEALTH_OPENER = urllib.request.build_opener(
    urllib.request.ProxyHandler({}), _NoRedirect()
)


def _health(port: int, server: str) -> None:
    """Bounded credential-free health capability check, with no proxies/redirects."""
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/health", headers={"Accept": "application/json"}
    )
    try:
        with _HEALTH_OPENER.open(request, timeout=HEALTH_TIMEOUT) as response:
            if response.status != 200:
                raise ValueError("health status")
            raw = response.read(HEALTH_LIMIT + 1)
        if len(raw) > HEALTH_LIMIT:
            raise ValueError("health size")
        body = json.loads(raw.decode("utf-8"))
        if (
            not isinstance(body, dict)
            or body.get("auth_mode") not in ("log", "enforce")
            or body.get("identity_required_writes") is not True
            or body.get("auth_hash_file") != "ok"
            or (server == "conport" and body.get("auth_principal_column") != "ok")
        ):
            raise ValueError("health capability")
    except (OSError, UnicodeError, ValueError, http.client.HTTPException):
        raise BridgeRuntimeError(
            "BRIDGE_HEALTH_UNQUALIFIED: target identity/auth health cannot be proven"
        ) from None


def _policy() -> bool:
    raw = os.environ.get(API_ONLY_POLICY)
    if raw is None:
        return False
    if raw not in {"true", "false"}:
        raise BridgeRuntimeError(
            f"BRIDGE_POLICY_INVALID: {API_ONLY_POLICY} must be literal true or false"
        )
    return raw == "true"


def _health_port(discovery: Any) -> int:
    # Lazy import avoids a bridge/runtime import cycle; retain selected-key-only parsing.
    from .http_stdio_bridge import _read_selected_keys

    if discovery.server == "dope-memory":
        return discovery.port
    port = safe_port_int(
        _read_selected_keys(discovery.envrc_path, frozenset({"CONPORT_HTTP_PORT"})),
        "CONPORT_HTTP_PORT",
    )
    if port is None:
        raise BridgeRuntimeError(
            "BRIDGE_HEALTH_PORT_UNKNOWN: target has no valid ConPort REST port"
        )
    return port


def _binding(discovery: Any) -> tuple:
    # `python -m` creates __main__.Discovery. Compare pinned values, not the
    # dataclass's module-specific identity or its mutable ids mapping.
    return (
        discovery.server,
        discovery.envrc_path.resolve(),
        discovery.port,
        tuple(sorted(discovery.ids.items())),
    )


@contextmanager
def runtime_session(discovery: Any) -> Iterator[Callable[[], None]]:
    """Hold a real current-process attachment across token lookup, HTTP and stdin.

    The instance lock protects only attach/detach. No stdin or HTTP operation
    runs under it; no service is started and no reaper policy is changed.
    """
    from .http_stdio_bridge import BridgeStartupError, discover_profile

    identity = resolve_identity_view(discovery.envrc_path.parent, trust_env=False)
    if (
        not identity.project_id
        or not identity.worktree_root
        or identity.identity_confidence == "UNKNOWN"
    ):
        raise BridgeRuntimeError(
            "BRIDGE_IDENTITY_UNKNOWN: target Git identity cannot be proven"
        )
    root = Path(identity.worktree_root).resolve()
    if discovery.envrc_path.resolve() != root / ENVRC_FILENAME:
        raise BridgeRuntimeError(
            "BRIDGE_CONFIG_UNBOUND: target envrc must belong to the Git worktree root"
        )
    target = launcher.LaunchTarget(
        root, identity, discovery.server, {}, runtime_dir_for(identity), ""
    )
    backend = BackendSpec(f"{discovery.base_url}/mcp", "http", discovery.server)
    initial_binding = _binding(discovery)
    require_api_only = _policy() and discovery.server == "dope-memory"
    try:
        initial_intent = launcher._memory_eventbus_intent(target)
        health_port = _health_port(discovery)
    except (launcher.LaunchError, BridgeStartupError) as exc:
        raise BridgeRuntimeError(str(exc)) from None

    def qualify() -> None:
        try:
            if (
                _binding(discover_profile(discovery.server, root)) != initial_binding
                or _health_port(discovery) != health_port
            ):
                raise BridgeRuntimeError(
                    "BRIDGE_CONFIG_CHANGED: target ports or identity changed; reconnect explicitly"
                )
            intent = launcher._memory_eventbus_intent(target)
            if intent is not initial_intent:
                raise BridgeRuntimeError(
                    "BRIDGE_CONFIG_CHANGED: target ingestion intent changed; reconnect explicitly"
                )
            if require_api_only and intent is True:
                raise BridgeRuntimeError(
                    "BRIDGE_POLICY_CONFLICT: target requests ingestion while API-only is required"
                )
            state = di.inspect_running_containers(
                timeout=launcher.GUARD_DOCKER_TIMEOUT_S
            )
            owners = (
                [c for c in state.containers if discovery.port in c.published_ports]
                if state.available
                else []
            )
            if len(owners) != 1 or not owners[0].id:
                raise BridgeRuntimeError(
                    "BRIDGE_OWNER_UNKNOWN: target container ownership cannot be proven"
                )
            launcher._check_sidecar_owner(
                target, discovery.port, state, lambda _: False
            )
            health_owners = [
                c for c in state.containers if health_port in c.published_ports
            ]
            if len(health_owners) != 1 or health_owners[0].id != owners[0].id:
                raise BridgeRuntimeError(
                    "BRIDGE_HEALTH_OWNER_UNKNOWN: health port is not owned by the target container"
                )
            launcher._verify_memory_eventbus(
                target, backend, False if require_api_only else intent, state=state
            )
            _health(health_port, discovery.server)
        except (launcher.LaunchError, BridgeStartupError) as exc:
            raise BridgeRuntimeError(str(exc)) from None

    # Precompute the canonical path before attach: finally also cleans up when a
    # signal interrupts attach after writing but before its return/yield.
    record = target.runtime_dir / ATTACHED_DIR / str(os.getpid())
    with launcher._signals_exit_through_finally():
        try:
            with instance_lock(target.runtime_dir):
                attach(target.runtime_dir)
            qualify()  # strictly before the caller can request a token
            yield qualify
        finally:
            with instance_lock(target.runtime_dir):
                detach(record)
