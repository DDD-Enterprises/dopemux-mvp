"""Shared fixtures for the Wave 2A R2 W02 (ConPort identity) tests.

The ConPort image copies its modules flat into ``/app`` (``server``,
``enhanced_server``, ``auth_identity`` ...), so they are top-level imports.  The
loader below imports them from the ConPort source directory under a temporary
``sys.path`` entry and then restores any same-named modules that other tests
(for example dope-memory's own ``auth_identity``) already placed in
``sys.modules``.  The returned module objects keep working after the restore.

``enhanced_server`` falls back to ``pip install`` when ``asyncpg`` is missing,
so the loader installs a stub ``asyncpg`` for the import when the real one is
absent (the tests never open a database connection).
"""

from __future__ import annotations

import contextlib
import importlib
import sys
import types
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import pytest

from .helpers import BOUND_WORKSPACE, CONPORT_DIR, INSTANCE, write_hash_file

_FLAT_MODULES = (
    "auth_identity",
    "instance_detector",
    "enhanced_server",
    "server",
    "conport_mcp_stdio",
    "integration_bridge_client",
    "unified_queries",
)


@contextlib.contextmanager
def conport_import_scope():
    saved = {name: sys.modules.pop(name, None) for name in _FLAT_MODULES}
    sys.path.insert(0, str(CONPORT_DIR))
    try:
        yield
    finally:
        try:
            sys.path.remove(str(CONPORT_DIR))
        except ValueError:
            pass
        for name in _FLAT_MODULES:
            sys.modules.pop(name, None)
            if saved[name] is not None:
                sys.modules[name] = saved[name]


def load_conport_module(name: str, monkeypatch: Optional[pytest.MonkeyPatch] = None):
    """Import ``name`` from the ConPort source directory (fresh every call)."""
    if name in ("enhanced_server", "server", "conport_mcp_stdio"):
        pytest.importorskip("aiohttp")
    if name == "enhanced_server":
        pytest.importorskip("redis.asyncio")
        try:
            import asyncpg  # noqa: F401
        except ImportError:
            if monkeypatch is None:
                raise
            monkeypatch.setitem(sys.modules, "asyncpg", types.ModuleType("asyncpg"))
    if name in ("server", "conport_mcp_stdio"):
        pytest.importorskip("mcp.server.fastmcp")
    with conport_import_scope():
        return importlib.import_module(name)


@pytest.fixture()
def auth_identity():
    return load_conport_module("auth_identity")


@pytest.fixture()
def instance_detector():
    return load_conport_module("instance_detector")


# --------------------------------------------------------------------------
# A fake asyncpg pool: records every statement, returns canned rows.
# --------------------------------------------------------------------------

NOW = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
PRINCIPAL_TABLES = ("workspace_contexts", "decisions", "progress_entries", "custom_data")


def _norm(sql: str) -> str:
    return " ".join(sql.split())


class FakeConn:
    def __init__(self, db: "FakeDB"):
        self.db = db

    async def execute(self, sql: str, *args: Any) -> str:
        self.db.calls.append(("execute", _norm(sql), args))
        return "OK"

    async def fetch(self, sql: str, *args: Any):
        norm = _norm(sql)
        self.db.calls.append(("fetch", norm, args))
        if "information_schema.columns" in norm:
            return [{"table_name": table} for table in self.db.principal_tables]
        if "FROM progress_entries" in norm:
            return [dict(self.db.progress_row)]
        return []

    async def fetchrow(self, sql: str, *args: Any):
        norm = _norm(sql)
        self.db.calls.append(("fetchrow", norm, args))
        if "FROM decisions WHERE id" in norm:
            return dict(self.db.decision_row)
        if "FROM progress_entries WHERE id" in norm:
            return dict(self.db.progress_row)
        if "FROM workspace_contexts" in norm:
            return dict(self.db.context_row)
        if "RETURNING value" in norm:
            return {"value": '{"_fingerprint_v1": "x"}'}
        return None

    async def fetchval(self, sql: str, *args: Any):
        self.db.calls.append(("fetchval", _norm(sql), args))
        return 1

    @contextlib.asynccontextmanager
    async def transaction(self):
        yield


class FakeDB:
    def __init__(self, principal_tables=PRINCIPAL_TABLES, progress_workspace: str = BOUND_WORKSPACE):
        self.calls: list[tuple[str, str, tuple]] = []
        self.principal_tables = tuple(principal_tables)
        self.decision_row = {
            "id": "11111111-1111-1111-1111-111111111111",
            "workspace_id": BOUND_WORKSPACE,
            "summary": "s",
            "rationale": "r",
            "alternatives": "[]",
            "tags": [],
            "created_at": NOW,
            "updated_at": NOW,
        }
        self.progress_row = {
            "id": "22222222-2222-2222-2222-222222222222",
            "workspace_id": progress_workspace,
            "description": "d",
            "status": "IN_PROGRESS",
            "percentage": 0,
            "linked_decision_id": None,
            "priority": "medium",
            "estimated_hours": None,
            "actual_hours": None,
            "instance_id": None,
            "created_at": NOW,
            "updated_at": NOW,
            "completed_at": None,
        }
        self.context_row = {
            "workspace_id": BOUND_WORKSPACE,
            "instance_id": INSTANCE,
            "active_context": "c",
            "last_activity": "a",
            "session_time": "1m",
            "focus_state": "f",
            "session_milestone": None,
            "updated_at": NOW,
        }

    # -- pool interface ----------------------------------------------------
    @contextlib.asynccontextmanager
    async def acquire(self):
        yield FakeConn(self)

    async def fetch(self, sql: str, *args: Any):
        return await FakeConn(self).fetch(sql, *args)

    # -- inspection helpers --------------------------------------------------
    def writes(self) -> list[tuple[str, tuple]]:
        out = []
        for kind, sql, args in self.calls:
            if kind == "execute" or (kind == "fetchrow" and sql.startswith("INSERT")):
                out.append((sql, args))
        return out

    def write_sql(self, fragment: str) -> list[tuple[str, tuple]]:
        return [(sql, args) for sql, args in self.writes() if fragment in sql]


class FakeRedis:
    async def get(self, key):
        return None

    async def setex(self, *args, **kwargs):
        return True

    async def delete(self, *args, **kwargs):
        return 1

    async def ping(self):
        return True


@pytest.fixture()
def enhanced_server_module(monkeypatch):
    return load_conport_module("enhanced_server", monkeypatch)


@pytest.fixture()
def make_rest_server(monkeypatch, tmp_path, enhanced_server_module):
    """Factory: an ``EnhancedConPortServer`` wired to fakes (no network, no DB)."""

    def factory(
        mode: str = "log",
        tokens: Optional[dict[str, str]] = None,
        *,
        bound_workspace: Optional[str] = BOUND_WORKSPACE,
        principal_tables=PRINCIPAL_TABLES,
        write_hash_dir: bool = True,
        progress_workspace: str = BOUND_WORKSPACE,
    ):
        monkeypatch.setenv("CONPORT_AUTH_MODE", mode)
        if write_hash_dir:
            auth_dir = tmp_path / "auth"
            write_hash_file(auth_dir, tokens or {})
            monkeypatch.setenv("CONPORT_AUTH_DIR", str(auth_dir))
        else:
            monkeypatch.delenv("CONPORT_AUTH_DIR", raising=False)
        if bound_workspace is None:
            monkeypatch.delenv("DOPEMUX_WORKSPACE_ID", raising=False)
        else:
            monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", bound_workspace)
        monkeypatch.setenv("DOPEMUX_AUTO_FORK_PROGRESS", "0")
        server = enhanced_server_module.EnhancedConPortServer()
        server.db_pool = FakeDB(principal_tables, progress_workspace)
        server.redis = FakeRedis()
        server.dopecon_bridge = None
        return server

    return factory


def rest_client(server):
    """An aiohttp ``TestClient`` for the server's app (use as ``async with``)."""
    from aiohttp.test_utils import TestClient, TestServer

    return TestClient(TestServer(server.app))
