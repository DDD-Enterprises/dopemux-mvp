"""Docker-down MCP tool-surface snapshot builder.

Captures every catalog server's live ``tools/list`` surface into a single,
diff-stable JSON artifact (``mcp_tool_surfaces.json``, repo root, sibling of
``mcp_catalog.yaml``). This snapshot is the cache the (future) tool-granular
drift gate and doc generators consume when the fleet isn't running.

Two independent sources feed the snapshot, reconciled by :func:`merge_snapshots`:

- :func:`snapshot_from_seed` ingests prior ``tools/list`` probe captures (e.g.
  ``proof/mcpint-p0/tools_list/*.json``) — useful when the fleet is down.
- :func:`snapshot_from_live` probes the fleet directly over two MCP transports:

  1. **Streamable HTTP** (``POST {base}/mcp``): ``initialize`` →
     ``notifications/initialized`` (best-effort) → ``tools/list``. The
     response body may be raw JSON or SSE-framed (``data: ...`` lines) —
     :func:`parse_mcp_response_body` handles both.
  2. **Classic SSE** (``GET {base}/sse``): read the ``event: endpoint`` frame
     for the POST endpoint (may be a relative path), then POST the same
     JSON-RPC sequence to that endpoint while a background thread reads
     replies off the original SSE stream.

Every probe is wrapped so a single dead/misbehaving server degrades to an
``"unreachable"`` entry rather than aborting the whole run (fail-open).

This module performs no CLI/click concerns and no catalog-file writes — see
``dopemux.commands.mcp_commands`` for the ``snapshot-tools`` subcommand that
wires this up.
"""

from __future__ import annotations

import json
import os
import queue
import re
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

SCHEMA_VERSION = 1
GENERATOR_LABEL = "dopemux mcp snapshot-tools"

_MAX_DESCRIPTION_CHARS = 120
_MCP_PROTOCOL_VERSION = "2024-11-05"

# Seed captures under proof/mcpint-p0/tools_list/ were produced by an earlier
# ad-hoc probing pass that named servers differently from `mcp_catalog.yaml`
# (e.g. by port/compose-service rather than catalog key). Normalize known
# aliases to the catalog's canonical name so a snapshot built from seed data
# merges cleanly with a snapshot built from live catalog-keyed probing,
# instead of producing duplicate entries for the same logical server.
_SEED_NAME_ALIASES: dict[str, str] = {
    "pal-http": "pal",
    "gptr-mcp": "gpt-researcher",
    "task-orchestrator-7890": "task-orchestrator",
    "task-orchestrator-compose-8000": "task-orchestrator",
}


# --------------------------------------------------------------------------
# Small shared helpers
# --------------------------------------------------------------------------


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def _first_line(text: str, limit: int = _MAX_DESCRIPTION_CHARS) -> str:
    """First line of `text`, stripped and truncated to at most `limit` chars."""
    stripped = (text or "").strip()
    if not stripped:
        return ""
    first = stripped.splitlines()[0].strip()
    if len(first) <= limit:
        return first
    return first[: max(limit - 1, 0)].rstrip() + "…"


def _assemble_snapshot(
    servers: dict[str, dict[str, Any]], *, generated_at: str | None = None
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or _now_iso(),
        "generator": GENERATOR_LABEL,
        "servers": servers,
    }


def dump_snapshot(snapshot: dict[str, Any]) -> str:
    """Serialize a snapshot deterministically: sorted keys, stable indentation."""
    return json.dumps(snapshot, indent=2, sort_keys=True) + "\n"


def load_snapshot(path: Path) -> dict[str, Any]:
    """Load a previously written snapshot file, or an empty snapshot if absent/invalid."""
    if not path.exists():
        return _assemble_snapshot({})
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _assemble_snapshot({})
    if not isinstance(data, dict) or not isinstance(data.get("servers"), dict):
        return _assemble_snapshot({})
    return data


# --------------------------------------------------------------------------
# Merge
# --------------------------------------------------------------------------


def merge_snapshots(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge `overlay` over `base`: overlay wins, except when overlay is
    `unreachable` for a server `base` already has data for — in that case the
    base entry is kept (a fresh failed probe must not clobber known-good data).
    """
    base_servers: dict[str, Any] = dict(base.get("servers") or {})
    overlay_servers: dict[str, Any] = overlay.get("servers") or {}

    merged: dict[str, Any] = dict(base_servers)
    for name, overlay_entry in overlay_servers.items():
        if overlay_entry.get("source") == "unreachable" and name in base_servers:
            continue
        merged[name] = overlay_entry

    return _assemble_snapshot(merged)


# --------------------------------------------------------------------------
# Seed ingestion
# --------------------------------------------------------------------------


def _canonical_seed_server_name(raw_name: str) -> str:
    return _SEED_NAME_ALIASES.get(raw_name, raw_name)


def _tools_from_seed_capture(capture: dict[str, Any]) -> dict[str, str]:
    """Extract {tool_name: short_description} from one seed capture file.

    Prefers the full `tools_list.result.tools` array (name + description),
    present for streamable-HTTP captures in this fleet. Falls back to the bare
    `tool_names` list (all this fleet's SSE captures recorded — no
    descriptions were saved for the classic-SSE probe path).
    """
    tools_list = capture.get("tools_list")
    if isinstance(tools_list, dict):
        result = tools_list.get("result")
        raw_tools = result.get("tools") if isinstance(result, dict) else None
        if isinstance(raw_tools, list) and raw_tools:
            return {
                str(tool["name"]): _first_line(str(tool.get("description") or ""))
                for tool in raw_tools
                if isinstance(tool, dict) and tool.get("name")
            }

    tool_names = capture.get("tool_names")
    if isinstance(tool_names, list):
        return {str(name): "" for name in tool_names}

    return {}


def snapshot_from_seed(seed_dir: Path) -> dict[str, Any]:
    """Build a snapshot from prior probe captures (verdict "OK" only).

    Each `*.json` file in `seed_dir` is expected to look like a
    `proof/mcpint-p0/tools_list/<server>.json` capture: at minimum
    `{"server": ..., "verdict": ...}`, plus either `tools_list.result.tools`
    (name+description) or `tool_names` (bare names). Files whose top-level
    `verdict` is not exactly `"OK"` are skipped — no partial/unreachable data
    is ingested from seed captures.
    """
    servers: dict[str, dict[str, Any]] = {}
    now = _now_iso()

    if seed_dir.is_dir():
        for path in sorted(seed_dir.glob("*.json")):
            if path.name.startswith("_"):
                continue  # e.g. _summary.json — not a per-server capture
            try:
                capture = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(capture, dict) or capture.get("verdict") != "OK":
                continue

            raw_name = capture.get("server")
            if not raw_name:
                continue
            name = _canonical_seed_server_name(str(raw_name))
            tools = _tools_from_seed_capture(capture)
            servers[name] = {
                "transport": capture.get("transport") or "unknown",
                "endpoint": capture.get("url"),
                "source": "seed",
                "captured_at": capture.get("ts") or now,
                "tool_count": len(tools),
                "tools": tools,
            }

    return _assemble_snapshot(servers, generated_at=now)


# --------------------------------------------------------------------------
# Live probing — shared JSON-RPC payloads + body parsing
# --------------------------------------------------------------------------


def _initialize_payload(request_id: int = 1) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "initialize",
        "params": {
            "protocolVersion": _MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "dopemux-mcp-snapshot", "version": "1"},
        },
    }


def _initialized_notification() -> dict[str, Any]:
    return {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}


def _tools_list_payload(request_id: int = 2) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "method": "tools/list", "params": {}}


def parse_mcp_response_body(raw: str) -> Any | None:
    """Parse an MCP JSON-RPC response body that may be raw JSON or SSE-framed.

    Some streamable-HTTP servers reply with `Content-Type: text/event-stream`
    even to a single-shot POST, framing the JSON-RPC object behind `data: `
    lines. This accepts either shape:

    - Raw JSON body → parsed directly.
    - SSE-framed body → every `data: ...` line is parsed as JSON; the last
      object carrying a `result` or `error` key wins (falls back to the last
      parseable object if none match, or `None` if nothing parses).
    """
    text = (raw or "").strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    candidates: list[Any] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[len("data:") :].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            candidates.append(json.loads(payload))
        except json.JSONDecodeError:
            continue

    for candidate in reversed(candidates):
        if isinstance(candidate, dict) and (
            "result" in candidate or "error" in candidate
        ):
            return candidate
    return candidates[-1] if candidates else None


def _extract_tools(parsed: Any) -> dict[str, str] | None:
    """Pull {name: short_description} out of a parsed tools/list JSON-RPC reply.

    Returns None (not {}) when the shape doesn't look like a tools/list
    result at all, so callers can distinguish "no tools" from "not parseable".
    """
    if not isinstance(parsed, dict) or "error" in parsed:
        return None
    result = parsed.get("result")
    if not isinstance(result, dict):
        return None
    raw_tools = result.get("tools")
    if not isinstance(raw_tools, list):
        return None
    return {
        str(tool["name"]): _first_line(str(tool.get("description") or ""))
        for tool in raw_tools
        if isinstance(tool, dict) and tool.get("name")
    }


def _unreachable_outcome(reason: str) -> dict[str, Any]:
    return {"ok": False, "tools": None, "reason": reason}


def _ok_outcome(tools: dict[str, str]) -> dict[str, Any]:
    return {"ok": True, "tools": tools, "reason": None}


# --------------------------------------------------------------------------
# Live probing — raw HTTP primitive shared by both transports
# --------------------------------------------------------------------------


@dataclass
class _HttpResponse:
    status: int
    headers: dict[str, str]
    body: str


def _http_post(
    url: str, payload: dict[str, Any], timeout: float, session_id: str | None = None
) -> _HttpResponse:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(
            request, timeout=timeout
        ) as response:  # noqa: S310 - MCP fleet probe
            body = response.read().decode("utf-8", errors="replace")
            resp_headers = {k.lower(): v for k, v in response.headers.items()}
            return _HttpResponse(
                status=response.status, headers=resp_headers, body=body
            )
    except urllib.error.HTTPError as exc:
        body = exc.fp.read().decode("utf-8", errors="replace") if exc.fp else ""
        resp_headers = {
            k.lower(): v for k, v in (exc.headers.items() if exc.headers else [])
        }
        return _HttpResponse(status=exc.code, headers=resp_headers, body=body)


# --------------------------------------------------------------------------
# Live probing — streamable HTTP transport
# --------------------------------------------------------------------------


def probe_streamable_http(mcp_url: str, timeout: float) -> dict[str, Any]:
    """Probe a streamable-HTTP MCP endpoint (`POST {base}/mcp`) for its tools/list."""
    try:
        init_resp = _http_post(mcp_url, _initialize_payload(), timeout)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return _unreachable_outcome(f"initialize failed: {exc}")

    if init_resp.status >= 400:
        return _unreachable_outcome(
            f"initialize HTTP {init_resp.status}: {init_resp.body[:200]}"
        )

    session_id = init_resp.headers.get("mcp-session-id")

    try:
        _http_post(mcp_url, _initialized_notification(), timeout, session_id)
    except Exception:  # noqa: BLE001 - notification failures are explicitly best-effort
        pass

    try:
        tools_resp = _http_post(mcp_url, _tools_list_payload(), timeout, session_id)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return _unreachable_outcome(f"tools/list failed: {exc}")

    if tools_resp.status >= 400:
        return _unreachable_outcome(
            f"tools/list HTTP {tools_resp.status}: {tools_resp.body[:200]}"
        )

    tools = _extract_tools(parse_mcp_response_body(tools_resp.body))
    if tools is None:
        return _unreachable_outcome(
            f"tools/list response did not contain a tools array: {tools_resp.body[:200]}"
        )
    return _ok_outcome(tools)


# --------------------------------------------------------------------------
# Live probing — classic SSE transport (conport, desktop-commander)
# --------------------------------------------------------------------------


def _sse_read_loop(
    sse_url: str,
    timeout: float,
    event_queue: "queue.Queue[dict[str, str]]",
    stop_event: threading.Event,
) -> None:
    """Background-thread reader: parses `event:`/`data:` SSE frames onto a queue."""
    request = urllib.request.Request(
        sse_url, method="GET", headers={"Accept": "text/event-stream"}
    )
    try:
        with urllib.request.urlopen(
            request, timeout=timeout
        ) as response:  # noqa: S310 - MCP fleet probe
            event_name: str | None = None
            data_lines: list[str] = []
            for raw_line in response:
                if stop_event.is_set():
                    return
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                if line == "":
                    if data_lines:
                        event_queue.put(
                            {
                                "event": event_name or "message",
                                "data": "\n".join(data_lines),
                            }
                        )
                    event_name = None
                    data_lines = []
                    continue
                if line.startswith(":"):
                    continue  # SSE comment/heartbeat
                if line.startswith("event:"):
                    event_name = line[len("event:") :].strip()
                elif line.startswith("data:"):
                    data_lines.append(line[len("data:") :].lstrip())
    except (
        Exception
    ) as exc:  # noqa: BLE001 - surfaced to caller via queue; thread must not crash silently
        if not stop_event.is_set():
            event_queue.put({"event": "error", "data": str(exc)})


def _wait_for_sse_event(
    event_queue: "queue.Queue[dict[str, str]]", timeout: float
) -> dict[str, str]:
    try:
        event = event_queue.get(timeout=timeout)
    except queue.Empty:
        raise TimeoutError(
            f"timed out after {timeout}s waiting for an SSE event"
        ) from None
    if event.get("event") == "error":
        raise RuntimeError(str(event.get("data")))
    return event


def _resolve_sse_post_endpoint(sse_url: str, raw_data: str) -> str:
    return urljoin(sse_url, raw_data.strip())


def probe_classic_sse(sse_url: str, timeout: float) -> dict[str, Any]:
    """Probe a classic-SSE MCP endpoint (`GET {base}/sse` + POST to the announced endpoint)."""
    event_queue: "queue.Queue[dict[str, str]]" = queue.Queue()
    stop_event = threading.Event()
    reader = threading.Thread(
        target=_sse_read_loop,
        args=(sse_url, timeout, event_queue, stop_event),
        daemon=True,
    )
    reader.start()

    try:
        try:
            endpoint_event = _wait_for_sse_event(event_queue, timeout)
        except (TimeoutError, RuntimeError) as exc:
            return _unreachable_outcome(str(exc))
        if endpoint_event.get("event") != "endpoint":
            return _unreachable_outcome(
                f"expected SSE 'endpoint' event, got `{endpoint_event.get('event')}`"
            )
        post_endpoint = _resolve_sse_post_endpoint(
            sse_url, endpoint_event.get("data", "")
        )

        try:
            _http_post(post_endpoint, _initialize_payload(), timeout)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            return _unreachable_outcome(f"initialize POST failed: {exc}")

        try:
            _wait_for_sse_event(
                event_queue, timeout
            )  # initialize reply — best-effort, unparsed
        except (TimeoutError, RuntimeError) as exc:
            return _unreachable_outcome(f"no initialize reply on SSE stream: {exc}")

        try:
            _http_post(post_endpoint, _initialized_notification(), timeout)
        except (
            Exception
        ):  # noqa: BLE001 - notification failures are explicitly best-effort
            pass

        try:
            _http_post(post_endpoint, _tools_list_payload(), timeout)
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            return _unreachable_outcome(f"tools/list POST failed: {exc}")

        try:
            tools_event = _wait_for_sse_event(event_queue, timeout)
        except (TimeoutError, RuntimeError) as exc:
            return _unreachable_outcome(f"no tools/list reply on SSE stream: {exc}")
    finally:
        stop_event.set()

    tools = _extract_tools(parse_mcp_response_body(tools_event.get("data", "")))
    if tools is None:
        return _unreachable_outcome(
            f"tools/list SSE reply did not contain a tools array: {tools_event.get('data', '')[:200]}"
        )
    return _ok_outcome(tools)


# --------------------------------------------------------------------------
# Live probing — catalog-driven orchestration
# --------------------------------------------------------------------------


def _resolve_env_template(value: str, env: dict[str, str]) -> str:
    """Resolve `${VAR}` / `${VAR:-default}` placeholders against `env`.

    Deliberately independent of `dopemux.commands.mcp_commands._resolve_env_template`
    (same behavior) to keep this module free of a commands-package import.
    """
    pattern = re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?::-([^}]*))?\}")

    def repl(match: "re.Match[str]") -> str:
        var_name = match.group(1)
        default = match.group(2) or ""
        return env.get(var_name) or default

    return pattern.sub(repl, value)


def _resolve_endpoint(spec: dict[str, Any], env: dict[str, str]) -> str | None:
    if spec.get("transport") not in ("http", "sse"):
        return None
    raw = spec.get("url") or spec.get("url_template")
    if not raw:
        return None
    return _resolve_env_template(str(raw), env)


def _probe_server(
    transport: str, endpoint: str | None, timeout: float
) -> dict[str, Any]:
    if transport == "http":
        if not endpoint:
            return _unreachable_outcome("no resolvable HTTP endpoint")
        try:
            return probe_streamable_http(endpoint, timeout)
        except (
            Exception
        ) as exc:  # noqa: BLE001 - fail-open: one dead server must not abort the run
            return _unreachable_outcome(f"unexpected probe error: {exc}")
    if transport == "sse":
        if not endpoint:
            return _unreachable_outcome("no resolvable SSE endpoint")
        try:
            return probe_classic_sse(endpoint, timeout)
        except (
            Exception
        ) as exc:  # noqa: BLE001 - fail-open: one dead server must not abort the run
            return _unreachable_outcome(f"unexpected probe error: {exc}")
    if transport == "stdio":
        return _unreachable_outcome("stdio transport; capture via seed or session")
    return _unreachable_outcome(f"unsupported transport `{transport}`")


def _build_server_entry(
    *, transport: str, endpoint: str | None, outcome: dict[str, Any], captured_at: str
) -> dict[str, Any]:
    if outcome["ok"]:
        tools = outcome["tools"] or {}
        return {
            "transport": transport,
            "endpoint": endpoint,
            "source": "live",
            "captured_at": captured_at,
            "tool_count": len(tools),
            "tools": tools,
        }
    return {
        "transport": transport,
        "endpoint": endpoint,
        "source": "unreachable",
        "captured_at": captured_at,
        "tool_count": 0,
        "tools": {},
        "reason": outcome.get("reason") or "unreachable",
    }


def snapshot_from_live(catalog: dict[str, Any], timeout: float = 6.0) -> dict[str, Any]:
    """Probe every catalog server's live `tools/list` surface.

    Fail-open per server: any probe error (network, protocol, or unexpected
    exception) becomes an `"unreachable"` entry with a `reason` — it never
    raises out of this function and never aborts the run for other servers.
    """
    env = dict(os.environ)
    now = _now_iso()
    servers: dict[str, dict[str, Any]] = {}

    for name, spec in sorted((catalog.get("servers") or {}).items()):
        transport = spec.get("transport", "http")
        endpoint = _resolve_endpoint(spec, env)
        outcome = _probe_server(transport, endpoint, timeout)
        servers[name] = _build_server_entry(
            transport=transport, endpoint=endpoint, outcome=outcome, captured_at=now
        )

    return _assemble_snapshot(servers, generated_at=now)
