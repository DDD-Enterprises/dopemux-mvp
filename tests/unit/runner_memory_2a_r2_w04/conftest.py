"""Fixtures for the W04 bridge tests: an in-process fake streamable-HTTP MCP server.

The fake listens on an ephemeral 127.0.0.1 port inside the test process. It is
not a live service: no container, no keychain, no real token. Every token in
these tests is a throwaway value generated here.
"""

from __future__ import annotations

import io
import json
import secrets
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from dopemux.mcp import http_stdio_bridge as bridge

SESSION_ID = "fake-session-1"

# What the fake server advertises in tools/list. Schemas decide which ids the
# bridge may fill; the bridge must never carry its own list of tool names.
DOPE_MEMORY_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "memory_store",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "instance_id": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "memory_search",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
        },
    },
]

CONPORT_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "update_context",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "instance_id": {"type": "string"},
                "patch": {"type": "object"},
            },
        },
    },
    {
        "name": "save_custom_data",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "category": {"type": "string"},
            },
        },
    },
    {
        "name": "fork_instance",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string"},
                "target_instance": {"type": "string"},
            },
            "required": ["target_instance"],
        },
    },
]


@dataclass
class Recorded:
    method: str
    path: str
    headers: Dict[str, str]
    body: Any


@dataclass
class FakeServer:
    """Shared state for the fake; the handler reads and writes it."""

    token: str
    tools: List[Dict[str, Any]]
    sse_responses: bool = True
    auth_status: Optional[int] = None  # force 401/403 on every request
    page_tools: bool = False
    sessions: set = field(default_factory=set)
    requests: List[Recorded] = field(default_factory=list)
    port: int = 0
    _httpd: Optional[ThreadingHTTPServer] = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def expire_sessions(self) -> None:
        with self._lock:
            self.sessions.clear()

    def bodies(self, method: Optional[str] = None) -> List[Dict[str, Any]]:
        out = [r.body for r in self.requests if isinstance(r.body, dict)]
        if method is not None:
            out = [b for b in out if b.get("method") == method]
        return out


def _make_handler(state: FakeServer):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args: Any) -> None:  # silence server logging
            return

        def _send(self, status: int, body: bytes = b"", headers: Optional[Dict[str, str]] = None) -> None:
            self.send_response(status)
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _reply(self, message: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> None:
            payload = json.dumps(message).encode("utf-8")
            if state.sse_responses:
                body = b"event: message\ndata: " + payload + b"\n\n"
                ctype = "text/event-stream"
            else:
                body = payload
                ctype = "application/json"
            self._send(200, body, {"Content-Type": ctype, **(headers or {})})

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw)
            except ValueError:
                body = None
            hdrs = {k.lower(): v for k, v in self.headers.items()}
            state.requests.append(Recorded("POST", self.path, hdrs, body))

            if state.auth_status in (401, 403):
                extra = {"WWW-Authenticate": "Bearer"} if state.auth_status == 401 else {}
                self._send(state.auth_status, b'{"error":"denied"}', extra)
                return
            if hdrs.get("authorization") != f"Bearer {state.token}":
                self._send(401, b'{"error":"unauthenticated"}', {"WWW-Authenticate": "Bearer"})
                return
            accept = hdrs.get("accept", "")
            if "application/json" not in accept or "text/event-stream" not in accept:
                self._send(406, b"Not Acceptable")
                return
            if self.path != "/mcp" or not isinstance(body, dict):
                self._send(404, b"not found")
                return

            method = body.get("method")
            if method == "initialize":
                state.sessions.add(SESSION_ID)
                self._reply(
                    {
                        "jsonrpc": "2.0",
                        "id": body.get("id"),
                        "result": {
                            "protocolVersion": "2025-03-26",
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "fake", "version": "0"},
                        },
                    },
                    {"mcp-session-id": SESSION_ID},
                )
                return
            sid = hdrs.get("mcp-session-id")
            if sid is None:
                self._send(400, b"Bad Request: Missing session ID")
                return
            if sid not in state.sessions:
                self._send(404, b"Session not found")
                return
            if "id" not in body:  # notification
                self._send(202)
                return
            if method == "tools/list":
                tools = state.tools
                result: Dict[str, Any] = {"tools": tools}
                if state.page_tools:
                    cursor = (body.get("params") or {}).get("cursor")
                    if cursor is None:
                        result = {"tools": tools[:1], "nextCursor": "p2"}
                    else:
                        result = {"tools": tools[1:]}
                self._reply({"jsonrpc": "2.0", "id": body["id"], "result": result})
                return
            if method == "tools/call":
                args = (body.get("params") or {}).get("arguments")
                self._reply(
                    {
                        "jsonrpc": "2.0",
                        "id": body["id"],
                        "result": {"content": [{"type": "text", "text": json.dumps(args, sort_keys=True)}]},
                    }
                )
                return
            self._reply({"jsonrpc": "2.0", "id": body["id"], "result": {}})

    return Handler


@pytest.fixture
def fake_token() -> str:
    return "fake-" + secrets.token_urlsafe(24)


@pytest.fixture
def fake_server(fake_token: str):
    state = FakeServer(token=fake_token, tools=DOPE_MEMORY_TOOLS)
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _make_handler(state))
    httpd.daemon_threads = True
    state.port = httpd.server_address[1]
    state._httpd = httpd
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield state
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


@pytest.fixture
def fake_password() -> str:
    return "pw-" + secrets.token_urlsafe(18)


@pytest.fixture
def repo(tmp_path: Path, fake_server: FakeServer, fake_password: str, monkeypatch) -> Path:
    """A fake checkout (has .git) whose envrc points at the fake server."""
    root = tmp_path / "checkout"
    root.mkdir()
    (root / ".git").write_text("gitdir: /nonexistent\n")
    (root / ".envrc.dopemux-mcp").write_text(
        "\n".join(
            [
                "# Generated by dopemux mcp start",
                f"CONPORT_MCP_PORT={fake_server.port}",
                f"DOPE_MEMORY_PORT={fake_server.port}",
                "DOPE_MEMORY_WORKSPACE_ID=wt-memory-ws",
                "DOPE_MEMORY_INSTANCE_ID=wt-memory-inst",
                "DOPEMUX_WORKSPACE_ID=/abs/conport/ws",
                "DOPEMUX_INSTANCE_ID=wt-conport-inst",
                f"POSTGRES_PASSWORD={fake_password}",
                f"export DATABASE_URL=postgresql://u:{fake_password}@localhost/db",
                "",
            ]
        )
    )
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def tokens(monkeypatch, fake_token: str):
    """Monkeypatch the W03 helper; records which principals were requested."""
    asked: List[str] = []

    def _get_token(principal: str) -> str:
        asked.append(principal)
        return fake_token

    monkeypatch.setattr(bridge, "get_token", _get_token)
    return asked


@dataclass
class Run:
    code: int
    stdout: str
    stderr: str

    def lines(self) -> List[Dict[str, Any]]:
        return [json.loads(line) for line in self.stdout.splitlines() if line.strip()]


@pytest.fixture
def run_bridge(monkeypatch, capsys):
    """Run ``bridge.main(argv)`` with the given JSON-RPC messages on stdin."""

    def _run(argv: List[str], messages: List[Dict[str, Any]]) -> Run:
        stdin = "".join(json.dumps(m) + "\n" for m in messages)
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
        capsys.readouterr()  # drop anything from earlier in the test
        code = bridge.main(argv)
        out = capsys.readouterr()
        return Run(code=code, stdout=out.out, stderr=out.err)

    return _run


def init_msg(msg_id: int = 1) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"},
        },
    }


def initialized_msg() -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "method": "notifications/initialized"}


def call_msg(msg_id: int, name: str, arguments: Any = None, *, omit_arguments: bool = False) -> Dict[str, Any]:
    params: Dict[str, Any] = {"name": name}
    if not omit_arguments:
        params["arguments"] = arguments
    return {"jsonrpc": "2.0", "id": msg_id, "method": "tools/call", "params": params}


def list_msg(msg_id: int) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "method": "tools/list"}
