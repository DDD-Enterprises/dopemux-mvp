"""W1-F01 / W1-F03: workspace_id validation and workspace-scoped writes.

Uses a fake DB pool and fake redis; no Postgres, network or asyncpg import here.
"""
import asyncio
import datetime
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

CONPORT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONPORT_DIR))


class _FastMCPStub:
    def __init__(self, *args, **kwargs):
        pass

    def tool(self, *, name=None, description=None):
        return lambda func: func


for _name, _mod in {
    "mcp": types.ModuleType("mcp"),
    "mcp.server": types.ModuleType("mcp.server"),
    "mcp.server.fastmcp": types.ModuleType("mcp.server.fastmcp"),
    "mcp.server.models": types.ModuleType("mcp.server.models"),
    "mcp.server.stdio": types.ModuleType("mcp.server.stdio"),
}.items():
    sys.modules.setdefault(_name, _mod)
sys.modules["mcp.server.fastmcp"].__dict__.setdefault("FastMCP", _FastMCPStub)
sys.modules["mcp.server.models"].__dict__.setdefault("InitializationOptions", object)
sys.modules["mcp.server.stdio"].__dict__.setdefault("stdio_server", object)

from enhanced_server import EnhancedConPortServer  # noqa: E402

NOW = datetime.datetime(2026, 10, 18)
PID = "11111111-1111-1111-1111-111111111111"
WS_A = "/Users/hue/code/dopemux-mvp"
WS_B = "/Users/hue/code/other repo é"


class FakeConn:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    async def fetchrow(self, sql, *args):
        row = self.rows.get(args[0])
        if row is None:
            return None
        if "workspace_id" in sql.split("WHERE", 1)[-1]:
            if row["workspace_id"] not in args[1:]:
                return None
        return dict(row)

    async def fetch(self, sql, *args):
        return []

    async def execute(self, sql, *args):
        self.executed.append((sql, args))
        return "UPDATE 1"


class FakePool:
    def __init__(self, rows):
        self.conn = FakeConn(rows)

    def acquire(self):
        pool = self

        class _Ctx:
            async def __aenter__(self):
                return pool.conn

            async def __aexit__(self, *exc):
                return False

        return _Ctx()


class FakeRedis:
    async def get(self, key):
        return None

    async def setex(self, *a):
        return None

    async def delete(self, *a):
        return None


def _row(ws):
    return {
        "id": PID, "workspace_id": ws, "description": "d", "status": "IN_PROGRESS",
        "percentage": 0, "linked_decision_id": None, "priority": "medium",
        "estimated_hours": None, "actual_hours": None, "instance_id": None,
        "created_at": NOW, "updated_at": NOW, "completed_at": None,
    }


@pytest.fixture
def srv():
    s = EnhancedConPortServer()
    s.db_pool = FakePool({PID: _row(WS_A)})
    s.redis = FakeRedis()
    s.dopecon_bridge = None
    return s


def run(coro):
    return asyncio.run(coro)


def _writes(srv):
    return srv.db_pool.conn.executed


def _req(match=None, query=None, body=None):
    async def _json():
        return body or {}
    return SimpleNamespace(match_info=match or {}, query=query or {}, json=_json)


def _resp(r):
    return r.status, json.loads(r.text)


BAD = ["", "   ", "\t\n", "a\x00b", "a\x1fb", "a\x7fb", "x" * 1025]


@pytest.mark.parametrize("bad", BAD)
def test_blank_or_control_workspace_rejected_on_reads_and_writes(srv, bad):
    for result in (
        run(srv._get_context(bad)),
        run(srv._get_decisions(bad, 5)),
        run(srv._get_progress(bad, None, 5)),
        run(srv._get_recent_activity(bad, 1)),
        run(srv._get_active_work(bad)),
        run(srv._log_progress({"workspace_id": bad, "description": "x"})),
        run(srv._update_progress(PID, {"workspace_id": bad, "status": "DONE"})),
        run(srv._promote_progress({"progress_id": PID, "workspace_id": bad})),
        run(srv._promote_all({"workspace_id": bad})),
    ):
        assert "error" in result, result
    assert _writes(srv) == []


def test_real_formats_accepted(srv):
    for ws in (WS_A, WS_B, "ws-104", "a" * 1024):
        res = run(srv._get_decisions(ws, 5))
        assert "error" not in res, res


def test_missing_workspace_on_list_still_allowed_f02_held(srv):
    assert "error" not in run(srv._get_decisions(None, 5))
    assert "error" not in run(srv._get_progress(None, None, 5))


def test_update_missing_workspace_rejected(srv):
    res = run(srv._update_progress(PID, {"status": "DONE"}))
    assert "error" in res and _writes(srv) == []


def test_update_other_workspace_row_not_found_no_write(srv):
    res = run(srv._update_progress(PID, {"workspace_id": WS_B, "status": "DONE"}))
    assert res == {"error": "Progress entry not found"}
    assert _writes(srv) == []


def test_update_same_workspace_works(srv):
    res = run(srv._update_progress(PID, {"workspace_id": WS_A, "status": "DONE"}))
    assert res.get("status") == "updated", res
    assert len(_writes(srv)) == 1
    sql, args = _writes(srv)[0]
    assert "workspace_id" in sql.split("WHERE", 1)[1]
    assert WS_A in args


def test_rest_put_accepts_query_param_workspace(srv):
    r = run(srv.update_progress(_req(match={"progress_id": PID}, query={"workspace_id": WS_A},
                                     body={"status": "DONE"})))
    status, body = _resp(r)
    assert status == 200 and body["status"] == "updated", body


def test_rest_put_missing_workspace_is_400(srv):
    r = run(srv.update_progress(_req(match={"progress_id": PID}, body={"status": "DONE"})))
    assert r.status == 400 and _writes(srv) == []


def test_rest_put_other_workspace_is_404(srv):
    r = run(srv.update_progress(_req(match={"progress_id": PID}, query={"workspace_id": WS_B},
                                     body={"status": "DONE"})))
    assert r.status == 404 and _writes(srv) == []


def test_promote_missing_workspace_rejected(srv):
    res = run(srv._promote_progress({"progress_id": PID}))
    assert "error" in res and _writes(srv) == []
    r = run(srv.promote_progress(_req(body={"progress_id": PID})))
    assert r.status == 400


def test_promote_other_workspace_not_found_no_write(srv):
    res = run(srv._promote_progress({"progress_id": PID, "workspace_id": WS_B}))
    assert res == {"error": "not found"}
    assert _writes(srv) == []


def test_promote_same_workspace_works(srv):
    res = run(srv._promote_progress({"progress_id": PID, "workspace_id": WS_A}))
    assert res.get("status") == "promoted", res
    sql, args = _writes(srv)[0]
    assert "workspace_id" in sql.split("WHERE", 1)[1] and WS_A in args


def test_promote_all_update_is_workspace_scoped(srv, monkeypatch):
    import enhanced_server
    monkeypatch.setattr(enhanced_server, "SimpleInstanceDetector",
                        SimpleNamespace(get_instance_id=lambda: "inst1"))
    res = run(srv._promote_all({"workspace_id": WS_A}))
    assert res.get("status") == "promoted_all", res
    for sql, args in _writes(srv):
        assert "workspace_id" in sql.split("WHERE", 1)[1]
        assert WS_A in args


def test_jsonrpc_update_tool_requires_workspace(srv):
    r = run(srv._dispatch_tool(1, "conport_update_progress", {"progress_id": PID, "status": "DONE"}))
    assert "error" in json.loads(r.text) and _writes(srv) == []
