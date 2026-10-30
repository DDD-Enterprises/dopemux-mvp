"""
ADHD engine commands.

``dopemux adhd status`` is a read-only probe of the ADHD engine over HTTP.
It uses ``GET /api/v1/state`` and ``GET /health``, neither of which needs an
API key, and never changes engine state.
"""

import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional, Tuple
from urllib.parse import urlparse

import click
import requests

# Task 4 pins this value to services/registry.yaml.
DEFAULT_ADHD_ENGINE_PORT: int = 3025

EXIT_CODES = {"ok": 0, "unreachable": 1, "malformed": 1, "degraded": 3}

_BASE_URL_VAR = "DOPEMUX_ADHD_ENGINE_BASE_URL"
_PORT_VARS = ("DOPEMUX_ADHD_ENGINE_PORT", "ADHD_ENGINE_PORT")
_MAX_ENGINE_STRING = 200


@dataclass
class StatusResult:
    status: str  # ok | degraded | unreachable | malformed
    url: str
    url_source: str
    engine_mode: str  # normal | fallback | unknown
    energy: Optional[str]
    attention: Optional[str]
    session_minutes: Optional[int]
    detail: str
    # Raw engine startup error, kept for the one-line human output only; the
    # JSON output already carries it inside ``detail`` and omits this field.
    startup_error: str = ""


def _valid_port(raw: str) -> Optional[int]:
    try:
        port = int(raw)
    except ValueError:
        return None
    return port if 1 <= port <= 65535 else None


def normalize_base_url(raw: str) -> str:
    """Return ``scheme://host[:port]`` for ``raw``, or ``""`` when invalid.

    Same rules as ``_base_from_url`` in ``dopemux.ui.service_endpoints``: a
    missing scheme defaults to ``http://``, any path, query or credentials are
    dropped, and a malformed port is invalid. Kept local because importing that
    module pulls in aiohttp and pydantic. Only http and https are accepted,
    since ``requests`` cannot fetch other schemes.
    """
    candidate = raw.strip()
    if not candidate:
        return ""
    if "://" not in candidate:
        candidate = f"http://{candidate}"
    try:
        parsed = urlparse(candidate)
        port = parsed.port
    except ValueError:
        return ""
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return ""
    if port is not None and not 1 <= port <= 65535:
        return ""
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    return f"{parsed.scheme}://{host}" + (f":{port}" if port is not None else "")


def resolve_engine_url(
    cli_url: Optional[str], env: Mapping[str, str]
) -> Tuple[str, str]:
    """Return ``(base_url, source)`` for the engine.

    Order: --url, DOPEMUX_ADHD_ENGINE_BASE_URL, DOPEMUX_ADHD_ENGINE_PORT,
    ADHD_ENGINE_PORT, then the registry default port on 127.0.0.1. URLs are
    normalized by ``normalize_base_url``. An invalid --url is a usage error; an
    invalid base-URL variable is skipped with a warning.
    """
    if cli_url is not None:
        normalized = normalize_base_url(cli_url)
        if not normalized:
            raise click.BadParameter(
                f"{cli_url!r} is not a valid http(s) URL", param_hint="--url"
            )
        return normalized, "--url"
    base = env.get(_BASE_URL_VAR)
    if base:
        normalized = normalize_base_url(base)
        if normalized:
            return normalized, _BASE_URL_VAR
        click.echo(
            f"warning: ignoring {_BASE_URL_VAR}={base!r}: not a valid http(s) URL",
            err=True,
        )
    for name in _PORT_VARS:
        raw = env.get(name)
        if raw is None:
            continue
        port = _valid_port(raw)
        if port is None:
            click.echo(
                f"warning: ignoring {name}={raw!r}: " "not an integer from 1 to 65535",
                err=True,
            )
            continue
        return f"http://127.0.0.1:{port}", name
    return f"http://127.0.0.1:{DEFAULT_ADHD_ENGINE_PORT}", "registry-default"


def _first_str(body: Mapping[str, Any], *keys: str) -> Optional[str]:
    """First key whose value is a non-empty string; earlier keys win."""
    for key in keys:
        value = body.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _engine_mode(base: str, timeout: float) -> Tuple[str, str]:
    """Classify ``/health``; returns ``(mode, startup_error_or_empty)``."""
    try:
        response = requests.get(f"{base}/health", timeout=timeout)
        if not 200 <= response.status_code < 300:
            return "unknown", ""
        body = response.json()
    except (requests.RequestException, ValueError):
        return "unknown", ""
    if not isinstance(body, dict):
        return "unknown", ""
    if body.get("mode") == "fallback":
        return "fallback", str(body.get("startup_error") or "")
    if "error" in body:
        return "unknown", ""
    return "normal", ""


def fetch_status(base_url: str, url_source: str, timeout: float = 2.0) -> StatusResult:
    """Probe ``/api/v1/state`` then ``/health`` and classify the outcome."""
    base = base_url.rstrip("/")

    def fail(status: str, detail: str) -> StatusResult:
        return StatusResult(
            status, base_url, url_source, "unknown", None, None, None, detail
        )

    try:
        response = requests.get(f"{base}/api/v1/state", timeout=timeout)
    except requests.Timeout:
        return fail("unreachable", f"timed out after {timeout:g}s")
    except requests.RequestException as exc:
        return fail("unreachable", f"{type(exc).__name__}: no response")
    if not 200 <= response.status_code < 300:
        return fail(
            "unreachable",
            f"GET /api/v1/state returned HTTP {response.status_code}",
        )

    try:
        body = response.json()
    except ValueError:
        return fail("malformed", "GET /api/v1/state did not return JSON")
    if not isinstance(body, dict):
        return fail("malformed", "GET /api/v1/state did not return a JSON object")

    # The *_level / *_state aliases win over the original keys.
    energy = _first_str(body, "energy_level", "energy")
    attention = _first_str(body, "attention_state", "attention")
    if energy is None:
        return fail("malformed", "GET /api/v1/state has no energy value")

    minutes = body.get("session_minutes")
    session_minutes = (
        minutes if isinstance(minutes, int) and not isinstance(minutes, bool) else None
    )

    mode, startup_error = _engine_mode(base, timeout)
    if mode == "fallback":
        detail = "engine running on its fallback class"
        if startup_error:
            detail += f" (startup error: {startup_error})"
        status = "degraded"
    else:
        detail = ""
        status = "ok"
        startup_error = ""
    return StatusResult(
        status,
        base_url,
        url_source,
        mode,
        energy,
        attention,
        session_minutes,
        detail,
        startup_error,
    )


def _one_line(value: str) -> str:
    """Collapse whitespace runs and cap an engine string at 200 characters."""
    text = " ".join(value.split())
    if len(text) > _MAX_ENGINE_STRING:
        text = text[: _MAX_ENGINE_STRING - 1] + "\u2026"
    return text


def _human_line(result: StatusResult) -> str:
    """One line of text; engine-supplied strings are collapsed and capped."""
    head = f"ADHD engine {result.status} ({result.url}, {result.url_source})"
    if result.energy is None:
        return f"{head}: {result.detail}"
    parts = [f"energy {_one_line(result.energy)}"]
    if result.attention is not None:
        parts.append(f"attention {_one_line(result.attention)}")
    if result.session_minutes is not None and result.session_minutes > 0:
        parts.append(f"session {result.session_minutes} min")
    line = f"{head}: {', '.join(parts)}"
    if result.status == "degraded":
        detail = "engine running on its fallback class"
        if result.startup_error:
            detail += f" (startup error: {_one_line(result.startup_error)})"
        line += f"; degraded: {detail}"
    return line


def _json_payload(result: StatusResult) -> Dict[str, Any]:
    data = asdict(result)
    del data["startup_error"]
    return data


@click.group()
def adhd() -> None:
    """ADHD engine commands."""


@adhd.command()
@click.option("--json", "as_json", is_flag=True, help="Print machine-readable JSON.")
@click.option(
    "--url",
    default=None,
    help="Engine base URL (overrides environment). A missing scheme defaults "
    "to http and any path is dropped.",
)
def status(as_json: bool, url: Optional[str]) -> None:
    """Show ADHD engine status (read-only).

    Exit codes: 0 ok, 1 unreachable or malformed, 3 degraded (fallback engine).
    """
    base_url, source = resolve_engine_url(url, os.environ)
    result = fetch_status(base_url, source)
    if as_json:
        click.echo(json.dumps(_json_payload(result), ensure_ascii=False))
    else:
        click.echo(_human_line(result))
    sys.exit(EXIT_CODES[result.status])
