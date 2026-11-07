#!/usr/bin/env python3
"""Bridge stdio JSON-RPC traffic to an MCP HTTP endpoint.

Two modes:

* ``--base-url URL`` (original): forward each line to ``URL/mcp`` as plain
  JSON-RPC, unauthenticated.
* ``--server dope-memory|conport --principal runner:<name>`` (Wave 2A): find the
  server's port in the nearest ``.envrc.dopemux-mcp``, read the principal's
  bearer token through ``dopemux.auth.get_token``, speak streamable HTTP
  (session id echoed, SSE or JSON responses) and fill ``workspace_id`` /
  ``instance_id`` where the tool schema declares them and the caller omitted
  them. Every failure to find a port or a token ends in a stderr message and a
  JSON-RPC error; no request is ever sent without ``Authorization``.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from dopemux.auth import AuthError, get_token
from dopemux.mcp.envrc import is_secret_like_key, parse_envrc_text, safe_port_int


JSONRPC_VERSION = "2.0"
PARSE_ERROR_CODE = -32700
INVALID_REQUEST_CODE = -32600
INTERNAL_ERROR_CODE = -32603
SERVER_ERROR_CODE = -32000
DEFAULT_TIMEOUT = 30.0

EXIT_STARTUP = 2  # no envrc / port / token: nothing was sent
EXIT_AUTH = 3  # the server answered 401 or 403: stopped, nothing more is sent

ENVRC_FILENAME = ".envrc.dopemux-mcp"
STREAMABLE_ACCEPT = "application/json, text/event-stream"
ID_KEYS = ("workspace_id", "instance_id")
MAX_TOOL_PAGES = 10

logger = logging.getLogger(__name__)


def _jsonrpc_error(
    request_id: Any, code: int, message: str, data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }
    if data:
        payload["error"]["data"] = data
    return payload


def _write_stdout(payload: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, separators=(",", ":")))
    sys.stdout.write("\n")
    sys.stdout.flush()


def _stderr(message: str) -> None:
    sys.stderr.write(f"dopemux-mcp-bridge: {message}\n")
    sys.stderr.flush()


def _resolve_timeout(cli_timeout: Optional[float]) -> float:
    if cli_timeout is not None:
        return cli_timeout

    raw_timeout = os.getenv("DOPEMUX_MCP_BRIDGE_TIMEOUT")
    if not raw_timeout:
        return DEFAULT_TIMEOUT

    try:
        parsed = float(raw_timeout)
    except ValueError:
        return DEFAULT_TIMEOUT

    return parsed if parsed > 0 else DEFAULT_TIMEOUT


def _forward_request(base_url: str, request_data: Dict[str, Any], timeout: float) -> Dict[str, Any]:
    endpoint = f"{base_url.rstrip('/')}/mcp"
    request_body = json.dumps(request_data).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=request_body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8").strip()
    except urllib.error.HTTPError as exc:
        detail = ""
        if exc.fp is not None:
            detail = exc.fp.read().decode("utf-8", errors="replace").strip()
        message = f"HTTP {exc.code} from MCP endpoint"
        if detail:
            message = f"{message}: {detail[:400]}"
        raise RuntimeError(message) from exc
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, socket.timeout):
            raise RuntimeError(f"Timeout contacting MCP endpoint after {timeout}s") from exc
        raise RuntimeError(f"Connection error to MCP endpoint: {reason}") from exc
    except socket.timeout as exc:
        raise RuntimeError(f"Timeout contacting MCP endpoint after {timeout}s") from exc

    if not body:
        raise RuntimeError("Empty response body from MCP endpoint")

    try:
        parsed = json.loads(body)
    except JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from MCP endpoint: {body[:200]}") from exc

    if not isinstance(parsed, dict):
        raise RuntimeError("Invalid MCP response payload: expected JSON object")

    return parsed


# --------------------------------------------------------------------------
# Wave 2A: discovery, identity and streamable HTTP
# --------------------------------------------------------------------------


class BridgeStartupError(RuntimeError):
    """Discovery or token lookup failed; nothing was sent."""


class BridgeAuthError(RuntimeError):
    """The server answered 401 or 403."""

    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP {status} from MCP endpoint")
        self.status = status


class _SessionExpired(RuntimeError):
    """HTTP 404 on a request that carried a session id."""


@dataclass(frozen=True)
class _Profile:
    port_key: str
    workspace_key: str
    instance_key: str

    @property
    def keys(self) -> frozenset:
        return frozenset({self.port_key, self.workspace_key, self.instance_key})


# dope-memory and ConPort bind to different workspace/instance keys (W01, W02
# returns); each server is sent only the pair it checks.
PROFILES: Dict[str, _Profile] = {
    "dope-memory": _Profile("DOPE_MEMORY_PORT", "DOPE_MEMORY_WORKSPACE_ID", "DOPE_MEMORY_INSTANCE_ID"),
    "conport": _Profile("CONPORT_MCP_PORT", "DOPEMUX_WORKSPACE_ID", "DOPEMUX_INSTANCE_ID"),
}

_ENVRC_KEY_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


@dataclass(frozen=True)
class Discovery:
    """What the bridge keeps from the envrc: one port and up to two ids."""

    server: str
    envrc_path: Path
    port: int
    ids: Mapping[str, str]

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"


def _find_envrc(start: Path) -> Optional[Path]:
    """Nearest envrc at or above ``start``, never leaving the checkout.

    A directory holding ``.git`` (a worktree has a ``.git`` file) is the
    checkout root: if it has no envrc, the answer is None. This keeps a
    worktree under ``<main>/.worktrees/`` from silently binding to the main
    checkout's containers.
    """
    current = start.resolve()
    while True:
        candidate = current / ENVRC_FILENAME
        if candidate.is_file():
            return candidate
        if (current / ".git").exists() or current.parent == current:
            return None
        current = current.parent


def _read_selected_keys(path: Path, keys: frozenset) -> Dict[str, str]:
    """Parse only the lines whose key is in ``keys``.

    The file also exports a database password. Other lines are dropped before
    the parser sees them, so no other value is held, logged or exported.
    """
    kept: List[str] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for raw in handle:
                match = _ENVRC_KEY_RE.match(raw)
                if match and match.group(1) in keys and not is_secret_like_key(match.group(1)):
                    kept.append(raw)
    except (OSError, UnicodeDecodeError) as exc:
        raise BridgeStartupError(f"cannot read {path}: {type(exc).__name__}") from None
    values, _errors = parse_envrc_text("".join(kept))
    return {key: value for key, value in values.items() if key in keys}


def discover_profile(server: str, start_dir: Path) -> Discovery:
    """Resolve ``server``'s port and ids from the checkout's envrc, or fail closed."""
    profile = PROFILES[server]
    envrc = _find_envrc(Path(start_dir))
    if envrc is None:
        raise BridgeStartupError(
            f"no {ENVRC_FILENAME} found from {start_dir} up to the checkout root; "
            "run `dopemux mcp init` in this checkout (another checkout's file is never used)"
        )
    values = _read_selected_keys(envrc, profile.keys)
    port = safe_port_int(values, profile.port_key)
    if port is None:
        raise BridgeStartupError(
            f"{envrc} has no valid {profile.port_key}; "
            "run `dopemux mcp init` / `dopemux mcp start` in this checkout"
        )
    ids = {
        name: values[key]
        for name, key in (("workspace_id", profile.workspace_key), ("instance_id", profile.instance_key))
        if values.get(key)
    }
    return Discovery(server=server, envrc_path=envrc, port=port, ids=ids)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: the bearer token must not leave the host we resolved."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


# An empty ProxyHandler keeps the token away from any environment proxy.
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())


def _parse_body(body: str, content_type: str) -> List[Dict[str, Any]]:
    """Messages in a response body: SSE-framed or plain JSON."""
    text = body.strip()
    if not text:
        return []
    if "text/event-stream" in content_type:
        payloads = []
        for event in text.replace("\r\n", "\n").split("\n\n"):
            data_lines = [
                line[5:][1:] if line[5:].startswith(" ") else line[5:]
                for line in event.split("\n")
                if line.startswith("data:")
            ]
            if data_lines:
                payloads.append("\n".join(data_lines))
    else:
        payloads = [text]
    messages: List[Dict[str, Any]] = []
    for payload in payloads:
        try:
            parsed = json.loads(payload)
        except JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON response from MCP endpoint: {payload[:200]}") from exc
        items = parsed if isinstance(parsed, list) else [parsed]
        for item in items:
            if not isinstance(item, dict):
                raise RuntimeError("Invalid MCP response payload: expected JSON object")
            messages.append(item)
    return messages


class _StreamableClient:
    """One streamable-HTTP session; the token lives only in the Authorization header."""

    def __init__(self, endpoint: str, token: str, ids: Mapping[str, str], timeout: float) -> None:
        self.endpoint = endpoint
        self.session_id: Optional[str] = None
        self._token = token
        self._ids = dict(ids)
        self._timeout = timeout
        self._init_message: Optional[Dict[str, Any]] = None
        self._schemas: Dict[str, Tuple[str, ...]] = {}
        self._listed = False
        self._counter = 0

    def __repr__(self) -> str:
        return f"_StreamableClient(endpoint={self.endpoint!r}, session={self.session_id is not None})"

    def _scrub(self, text: str) -> str:
        return text.replace(self._token, "[REDACTED]") if self._token else text

    def _exchange(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """POST one message; return the messages in the reply (empty for a 202)."""
        is_initialize = message.get("method") == "initialize"
        if is_initialize:
            self.session_id = None
        headers = {
            "Accept": STREAMABLE_ACCEPT,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(message).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with _OPENER.open(request, timeout=self._timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                content_type = response.headers.get("Content-Type", "")
                new_session = response.headers.get("Mcp-Session-Id")
        except urllib.error.HTTPError as exc:
            detail = ""
            if exc.fp is not None:
                detail = exc.fp.read().decode("utf-8", errors="replace").strip()
            if exc.code in (401, 403):
                raise BridgeAuthError(exc.code) from None
            if exc.code == 404 and self.session_id:
                raise _SessionExpired("MCP session expired (HTTP 404)") from None
            text = f"HTTP {exc.code} from MCP endpoint"
            if detail:
                text = f"{text}: {self._scrub(detail)[:400]}"
            raise RuntimeError(text) from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise RuntimeError(f"Timeout contacting MCP endpoint after {self._timeout}s") from None
            raise RuntimeError(f"Connection error to MCP endpoint: {exc.reason}") from None
        except socket.timeout:
            raise RuntimeError(f"Timeout contacting MCP endpoint after {self._timeout}s") from None

        if is_initialize and new_session:
            self.session_id = new_session
        return _parse_body(self._scrub(body), content_type)

    def _exchange_with_reinit(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """``_exchange``, re-initializing once if the server dropped the session."""
        try:
            return self._exchange(message)
        except _SessionExpired:
            if self._init_message is None:
                raise RuntimeError("MCP session expired and the client never initialized it") from None
        _stderr("MCP session expired; re-initializing once")
        self.session_id = None
        self._exchange(self._init_message)
        self._exchange({"jsonrpc": JSONRPC_VERSION, "method": "notifications/initialized"})
        return self._exchange(message)

    # -- identity ----------------------------------------------------------

    def _learn_schemas(self, messages: Sequence[Dict[str, Any]]) -> None:
        for message in messages:
            result = message.get("result")
            tools = result.get("tools") if isinstance(result, dict) else None
            if not isinstance(tools, list):
                continue
            for tool in tools:
                if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
                    continue
                schema = tool.get("inputSchema")
                props = schema.get("properties") if isinstance(schema, dict) else None
                declared = props if isinstance(props, dict) else {}
                self._schemas[tool["name"]] = tuple(key for key in ID_KEYS if key in declared)

    def _fetch_tools(self) -> None:
        """Ask the server for its tool schemas once (the client never listed them)."""
        self._listed = True
        cursor: Optional[str] = None
        for _ in range(MAX_TOOL_PAGES):
            self._counter += 1
            request: Dict[str, Any] = {
                "jsonrpc": JSONRPC_VERSION,
                "id": f"dopemux-bridge-tools-list-{self._counter}",
                "method": "tools/list",
            }
            if cursor:
                request["params"] = {"cursor": cursor}
            try:
                replies = self._exchange_with_reinit(request)
            except BridgeAuthError:
                raise
            except Exception:
                logger.debug("tool schema lookup failed", exc_info=True)
                return
            self._learn_schemas(replies)
            cursor = next(
                (
                    r["result"]["nextCursor"]
                    for r in replies
                    if isinstance(r.get("result"), dict) and r["result"].get("nextCursor")
                ),
                None,
            )
            if not cursor:
                return

    def _hide_filled_required(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Copy of a ``tools/list`` reply with the ids the bridge fills no longer required.

        Otherwise the model, told the ids are required, invents values the
        server then rejects. Properties and every other field stay as the
        server sent them; an id the bridge holds no value for stays required.
        Only the copy printed for the client changes: ``_learn_schemas`` has
        already read the original, so filling still knows the tool declares the id.
        """
        fillable = set(self._ids)
        if not fillable:
            return messages
        shown: List[Dict[str, Any]] = []
        for message in messages:
            result = message.get("result")
            tools = result.get("tools") if isinstance(result, dict) else None
            if not isinstance(tools, list):
                shown.append(message)
                continue
            new_tools = []
            for tool in tools:
                schema = tool.get("inputSchema") if isinstance(tool, dict) else None
                required = schema.get("required") if isinstance(schema, dict) else None
                if not isinstance(required, list) or not fillable.intersection(required):
                    new_tools.append(tool)
                    continue
                kept = [item for item in required if item not in fillable]
                new_schema = {}
                for key, value in schema.items():
                    if key != "required":
                        new_schema[key] = value
                    elif kept:
                        new_schema[key] = kept
                new_tools.append({**tool, "inputSchema": new_schema})
            shown.append({**message, "result": {**result, "tools": new_tools}})
        return shown

    def _fill_ids(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Add the ids a tool declares and the caller omitted; never replace a caller value."""
        if message.get("method") != "tools/call" or not self._ids:
            return message
        params = message.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("name"), str):
            return message
        arguments = params.get("arguments")
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            return message
        name = params["name"]
        if name not in self._schemas and not self._listed and self.session_id:
            self._fetch_tools()
        additions = {
            key: self._ids[key]
            for key in self._schemas.get(name, ())
            if key in self._ids and key not in arguments
        }
        if not additions:
            return message
        return {**message, "params": {**params, "arguments": {**arguments, **additions}}}

    # -- entry point -------------------------------------------------------

    def send(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Forward one client message; return what must be printed on stdout."""
        outgoing = self._fill_ids(message)
        replies = self._exchange_with_reinit(outgoing)
        method = message.get("method")
        if method == "initialize":
            self._init_message = message
        elif method == "tools/list":
            self._learn_schemas(replies)
            return self._hide_filled_required(replies)
        return replies


def _parse_line(line: str) -> Optional[Dict[str, Any]]:
    """Decode one stdin line; write the JSON-RPC error and return None if it is bad."""
    try:
        request_data = json.loads(line)
    except JSONDecodeError:
        _write_stdout(_jsonrpc_error(None, PARSE_ERROR_CODE, "Parse error"))
        return None
    if not isinstance(request_data, dict):
        _write_stdout(_jsonrpc_error(None, INVALID_REQUEST_CODE, "Invalid Request"))
        return None
    return request_data


def _fail_startup(message: str) -> int:
    """Fail closed: stderr message, a JSON-RPC error for the first request, nonzero exit."""
    _stderr(message)
    while True:
        line = sys.stdin.readline()
        if line == "":
            return EXIT_STARTUP
        line = line.strip()
        if not line:
            continue
        request_data = _parse_line(line)
        if request_data is not None and "id" in request_data:
            _write_stdout(_jsonrpc_error(request_data["id"], SERVER_ERROR_CODE, message))
            return EXIT_STARTUP


def _run_streamable(server: str, principal: str, timeout: float) -> int:
    try:
        discovery = discover_profile(server, Path.cwd())
        token = get_token(principal)
        if not token:
            raise BridgeStartupError(f"the token for principal {principal} is empty")
    except BridgeStartupError as exc:
        return _fail_startup(str(exc))
    except AuthError as exc:
        return _fail_startup(f"cannot get the token for principal {principal}: {exc}")
    except OSError as exc:
        return _fail_startup(f"cannot read the working directory: {type(exc).__name__}")

    client = _StreamableClient(f"{discovery.base_url}/mcp", token, discovery.ids, timeout)
    del token

    while True:
        line = sys.stdin.readline()
        if line == "":
            return 0
        line = line.strip()
        if not line:
            continue
        request_data = _parse_line(line)
        if request_data is None:
            continue

        is_request = "id" in request_data
        request_id = request_data.get("id")
        try:
            replies = client.send(request_data)
        except BridgeAuthError as exc:
            message = (
                f"HTTP {exc.status} from {server} for principal {principal}: the token was rejected; "
                f"check that it is issued and that the server is configured to accept it. Stopping."
            )
            _stderr(message)
            if is_request:
                _write_stdout(_jsonrpc_error(request_id, SERVER_ERROR_CODE, message))
            return EXIT_AUTH
        except Exception as exc:
            logger.debug("Bridge forward error", exc_info=True)
            if is_request:
                _write_stdout(
                    _jsonrpc_error(
                        request_id,
                        SERVER_ERROR_CODE,
                        "Bridge transport error",
                        {"detail": str(exc)},
                    )
                )
            else:
                _stderr(f"notification not delivered: {exc}")
            continue

        for reply in replies:
            _write_stdout(reply)
        if is_request and not replies:
            _write_stdout(
                _jsonrpc_error(
                    request_id,
                    SERVER_ERROR_CODE,
                    "Bridge transport error",
                    {"detail": "Empty response body from MCP endpoint"},
                )
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bridge stdio JSON-RPC to MCP HTTP")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--base-url", help="MCP server base URL (for example: http://localhost:3004)")
    mode.add_argument(
        "--server",
        choices=sorted(PROFILES),
        help="Authenticated streamable-HTTP mode: find this server's port in the nearest "
        f"{ENVRC_FILENAME} (requires --principal)",
    )
    parser.add_argument("--principal", help="Principal whose keychain token is sent (for example: runner:codex)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="HTTP timeout in seconds (defaults to DOPEMUX_MCP_BRIDGE_TIMEOUT or 30)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.server and not args.principal:
        parser.error("--server requires --principal")
    if args.principal and not args.server:
        parser.error("--principal is only used with --server")

    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    timeout = _resolve_timeout(args.timeout)

    if args.server:
        return _run_streamable(args.server, args.principal, timeout)

    while True:
        line = sys.stdin.readline()
        if line == "":
            return 0

        line = line.strip()
        if not line:
            continue

        request_data = _parse_line(line)
        if request_data is None:
            continue

        request_id: Any = request_data.get("id")
        try:
            response = _forward_request(args.base_url, request_data, timeout)
        except Exception as exc:
            logger.debug("Bridge forward error", exc_info=True)
            _write_stdout(
                _jsonrpc_error(
                    request_id,
                    SERVER_ERROR_CODE,
                    "Bridge transport error",
                    {"detail": str(exc)},
                )
            )
            continue

        _write_stdout(response)


if __name__ == "__main__":
    raise SystemExit(main())
