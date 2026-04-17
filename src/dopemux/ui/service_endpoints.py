"""Shared endpoint resolution for Dopemux operator dashboards."""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import ParseResult, urlparse

from dopemux.instance_state import resolve_conport_port


@dataclass(frozen=True)
class ResolvedEndpoint:
    """Resolved operator endpoint plus source metadata."""

    name: str
    base_url: str
    source: str

    def url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"


def _safe_int(value: str | None) -> int | None:
    try:
        return (
            int(str(value).strip())
            if value is not None and str(value).strip()
            else None
        )
    except (TypeError, ValueError):
        return None


def _base_from_url(url: str) -> str:
    """Return a normalized base URL or empty string for invalid values.

    Scheme-less host values default to ``http://`` for deterministic local
    dashboard endpoint behavior.
    """

    def _format_host(parsed_result: ParseResult) -> str:
        """Return ``hostname:port`` for valid parsed input, else empty.

        ``ParseResult.port`` raises ``ValueError`` for malformed ports
        (for example ``localhost:notaport``), which we treat as invalid input.
        """
        hostname = parsed_result.hostname
        if not hostname:
            return ""
        try:
            parsed_port = parsed_result.port
        except ValueError:
            # Invalid ports such as "localhost:notaport" should be rejected.
            return ""
        port = f":{parsed_port}" if parsed_port is not None else ""
        return f"{hostname}{port}"

    candidate = url.strip()
    parsed = urlparse(candidate)
    if parsed.scheme and parsed.hostname:
        host = _format_host(parsed)
        if host:
            return f"{parsed.scheme}://{host}"
        return ""

    if not parsed.scheme:
        # Accept host[:port][/path] forms like "localhost:8000/health".
        host_only = urlparse(f"//{candidate}")
        host = _format_host(host_only)
        if host:
            return f"http://{host}"

    return ""


def _port_is_listening(
    port: int, host: str = "127.0.0.1", timeout: float = 0.2
) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _select_port(candidates: list[tuple[int, str]]) -> tuple[int, str]:
    if not candidates:
        raise ValueError("port candidates must not be empty")
    for port, source in candidates:
        if _port_is_listening(port):
            return port, source
    return candidates[0]


def resolve_adhd_engine_endpoint() -> ResolvedEndpoint:
    explicit_base = os.getenv("DOPEMUX_ADHD_ENGINE_BASE_URL", "").strip()
    if explicit_base:
        parsed_base = _base_from_url(explicit_base)
        if parsed_base:
            return ResolvedEndpoint(
                name="ADHD Engine",
                base_url=parsed_base,
                source="DOPEMUX_ADHD_ENGINE_BASE_URL",
            )

    candidates: list[tuple[int, str]] = []
    env_port = _safe_int(os.getenv("DOPEMUX_ADHD_ENGINE_PORT"))
    if env_port is not None:
        candidates.append((env_port, "DOPEMUX_ADHD_ENGINE_PORT"))
    for port, source in ((5448, "default:5448"), (8095, "default:8095")):
        if port not in {candidate for candidate, _ in candidates}:
            candidates.append((port, source))
    port, source = _select_port(candidates)
    return ResolvedEndpoint("ADHD Engine", f"http://localhost:{port}", source)


def resolve_conport_endpoint() -> ResolvedEndpoint:
    explicit_url = os.getenv("CONPORT_URL", "").strip()
    if explicit_url:
        parsed_base = _base_from_url(explicit_url)
        if parsed_base:
            return ResolvedEndpoint("ConPort", parsed_base, "CONPORT_URL")

    port = resolve_conport_port()
    if os.getenv("DOPEMUX_CONPORT_PORT", "").strip():
        source = "DOPEMUX_CONPORT_PORT"
    elif os.getenv("CONPORT_PORT", "").strip():
        source = "CONPORT_PORT"
    elif os.getenv("DOPEMUX_PORT_BASE", "").strip():
        source = "DOPEMUX_PORT_BASE+7"
    else:
        source = "default"
    return ResolvedEndpoint("ConPort", f"http://localhost:{port}", source)


def resolve_serena_endpoint() -> ResolvedEndpoint:
    candidates: list[tuple[int, str]] = []
    for env_name in ("DOPEMUX_SERENA_PORT", "SERENA_PORT"):
        port = _safe_int(os.getenv(env_name))
        if port is not None:
            candidates.append((port, env_name))
            break
    base_port = _safe_int(os.getenv("DOPEMUX_PORT_BASE"))
    if base_port is not None:
        candidates.append((base_port + 6, "DOPEMUX_PORT_BASE+6"))
    candidates.append((8003, "legacy:8003"))
    port, source = _select_port(candidates)
    return ResolvedEndpoint("Serena", f"http://localhost:{port}", source)


def resolve_bridge_endpoint() -> ResolvedEndpoint:
    explicit_url = os.getenv("DOPECON_BRIDGE_URL", "").strip()
    if explicit_url:
        parsed_base = _base_from_url(explicit_url)
        if parsed_base:
            return ResolvedEndpoint("Dopecon Bridge", parsed_base, "DOPECON_BRIDGE_URL")

    candidates: list[tuple[int, str]] = []
    explicit_port = _safe_int(os.getenv("DOPECON_BRIDGE_PORT"))
    if explicit_port is not None:
        candidates.append((explicit_port, "DOPECON_BRIDGE_PORT"))
    port_base = _safe_int(os.getenv("PORT_BASE"))
    if port_base is not None:
        candidates.append((port_base + 16, "PORT_BASE+16"))
    candidates.append((3016, "default:3016"))
    port, source = _select_port(candidates)
    return ResolvedEndpoint("Dopecon Bridge", f"http://localhost:{port}", source)


def resolve_dashboard_endpoints() -> dict[str, ResolvedEndpoint]:
    return {
        "adhd": resolve_adhd_engine_endpoint(),
        "conport": resolve_conport_endpoint(),
        "serena": resolve_serena_endpoint(),
        "bridge": resolve_bridge_endpoint(),
    }


def refresh_age_label(sampled_at: datetime | None) -> str:
    if sampled_at is None:
        return "never"
    elapsed = max(0, int((datetime.now(timezone.utc) - sampled_at).total_seconds()))
    if elapsed < 5:
        return "just now"
    if elapsed < 60:
        return f"{elapsed}s ago"
    minutes, seconds = divmod(elapsed, 60)
    return f"{minutes}m {seconds}s ago"


__all__ = [
    "ResolvedEndpoint",
    "refresh_age_label",
    "resolve_adhd_engine_endpoint",
    "resolve_bridge_endpoint",
    "resolve_conport_endpoint",
    "resolve_dashboard_endpoints",
    "resolve_serena_endpoint",
]
