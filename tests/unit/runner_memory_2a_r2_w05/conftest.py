"""Fixtures for the W05 HTTP-caller tests.

Nothing here is live: the "server" is a throwaway HTTP listener on an
ephemeral 127.0.0.1 port inside the test process, and every token is a fake
value generated in this file. ``dopemux.auth.get_token`` is always replaced,
and the real ``/usr/bin/security`` path is blanked so that no test can reach
the keychain even when a fixture forgets to patch ``get_token``.
"""

from __future__ import annotations

import importlib
import json
import secrets
import sys
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlsplit

import pytest

from dopemux.auth import KeychainError, TokenNotFoundError
from dopemux.instance_state import InstanceStateManager

# tests/conftest.py replaces save_instance_state with a no-op for every test
# (it guards against writes to a live ConPort). Capture the real method now,
# before any fixture runs, so the instance_state tests can aim it at the fake.
_REAL_SAVE_INSTANCE_STATE = InstanceStateManager.save_instance_state

# Obviously fake; generated per test session, never a real credential.
FAKE_TOKEN = "fake-w05-" + secrets.token_urlsafe(18)

_ID_ENV = (
    "DOPEMUX_WORKSPACE_ID",
    "DOPEMUX_INSTANCE_ID",
    "DOPE_MEMORY_WORKSPACE_ID",
    "DOPE_MEMORY_INSTANCE_ID",
    "CONPORT_URL",
    "DOPE_MEMORY_URL",
)

# One body that satisfies every caller's response parsing.
_REPLY = {
    "status": "logged",
    "success": True,
    "entry_id": "entry-1",
    "decision": {"id": 1},
    "progress": {"id": "p-1"},
    "decision_id": "dec-1",
    "items": [],
    "count": 0,
}


@dataclass
class Seen:
    method: str
    path: str
    query: Dict[str, List[str]]
    headers: Dict[str, str]
    body: Optional[Any]

    @property
    def authorization(self) -> Optional[str]:
        return self.headers.get("authorization")


@dataclass
class FakeServer:
    url: str
    port: int
    requests: List[Seen] = field(default_factory=list)

    def writes(self) -> List[Seen]:
        return [r for r in self.requests if r.method != "GET"]


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """No ambient ids, and no path to the real keychain."""
    for name in _ID_ENV:
        monkeypatch.delenv(name, raising=False)
    keychain = importlib.import_module("dopemux.auth.keychain")
    monkeypatch.setattr(keychain, "SECURITY_BIN", "/nonexistent/security")


@pytest.fixture
def real_instance_state_save(monkeypatch):
    """Undo the root guard for one test; the target is always the 127.0.0.1 fake."""
    monkeypatch.setattr(InstanceStateManager, "save_instance_state", _REAL_SAVE_INSTANCE_STATE)


@pytest.fixture
def fake_server():
    store: List[Seen] = []

    class Handler(BaseHTTPRequestHandler):
        def _handle(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                body = json.loads(raw) if raw else None
            except ValueError:
                body = None
            parts = urlsplit(self.path)
            store.append(
                Seen(
                    method=self.command,
                    path=parts.path,
                    query=parse_qs(parts.query),
                    headers={k.lower(): v for k, v in self.headers.items()},
                    body=body,
                )
            )
            payload = json.dumps(_REPLY).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _handle

        def log_message(self, *args: Any) -> None:  # keep test output quiet
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield FakeServer(url=f"http://127.0.0.1:{port}", port=port, requests=store)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


@pytest.fixture
def token_ok(monkeypatch):
    """get_token returns the fake token; the list records which principals asked."""
    asked: List[str] = []

    def fake_get_token(principal: str) -> str:
        asked.append(principal)
        return FAKE_TOKEN

    auth = importlib.import_module("dopemux.auth")
    monkeypatch.setattr(auth, "get_token", fake_get_token)
    return asked


@pytest.fixture
def token_missing(monkeypatch):
    """get_token fails the way it does with no keychain item."""
    asked: List[str] = []

    def fake_get_token(principal: str) -> str:
        asked.append(principal)
        raise TokenNotFoundError(f"no dopemux-mcp keychain item for {principal}")

    auth = importlib.import_module("dopemux.auth")
    monkeypatch.setattr(auth, "get_token", fake_get_token)
    return asked


@pytest.fixture
def token_keychain_down(monkeypatch):
    """get_token raises KeychainError, as inside a Linux container."""

    def fake_get_token(principal: str) -> str:
        raise KeychainError("cannot run /usr/bin/security (FileNotFoundError); needs macOS")

    auth = importlib.import_module("dopemux.auth")
    monkeypatch.setattr(auth, "get_token", fake_get_token)


@pytest.fixture
def no_auth_package(monkeypatch):
    """`from dopemux.auth import ...` raises ImportError (a service image without it)."""
    monkeypatch.setitem(sys.modules, "dopemux.auth", None)


def assert_no_secret(caplog, capsys) -> None:
    out = capsys.readouterr()
    assert FAKE_TOKEN not in caplog.text
    assert FAKE_TOKEN not in out.out
    assert FAKE_TOKEN not in out.err
