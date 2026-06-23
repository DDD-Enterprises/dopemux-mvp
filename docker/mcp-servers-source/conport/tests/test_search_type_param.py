import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace


CONPORT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONPORT_DIR))

from enhanced_server import EnhancedConPortServer


class _FakeRedis:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return self.values.get(key)

    async def setex(self, key, ttl, value):
        self.values[key] = value


class _FakeAcquire:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, conn):
        self.conn = conn

    def acquire(self):
        return _FakeAcquire(self.conn)


class _FakeConnection:
    def __init__(self):
        self.decision_fetches = 0
        self.progress_fetches = 0

    async def fetch(self, sql, *args):
        if "FROM decisions" in sql:
            self.decision_fetches += 1
            return [
                {
                    "id": "decision-205",
                    "workspace_id": args[0],
                    "summary": "needle decision",
                    "rationale": "structured decision result",
                    "created_at": datetime(2026, 6, 22, tzinfo=timezone.utc),
                    "rank": 0.75,
                }
            ]
        if "FROM progress_entries" in sql:
            self.progress_fetches += 1
            return [
                {
                    "id": "progress-205",
                    "workspace_id": args[0],
                    "description": "needle progress",
                    "status": "IN_PROGRESS",
                    "percentage": 50,
                    "created_at": datetime(2026, 6, 22, tzinfo=timezone.utc),
                }
            ]
        raise AssertionError(f"unexpected query: {sql}")


def _request(search_type=None):
    query = {"q": "needle"}
    if search_type is not None:
        query["type"] = search_type
    return SimpleNamespace(match_info={"workspace_id": "ws-205"}, query=query)


def _server(conn):
    app = EnhancedConPortServer()
    app.redis = _FakeRedis()
    app.db_pool = _FakePool(conn)
    return app


async def _search(search_type=None):
    conn = _FakeConnection()
    response = await _server(conn).search_content(_request(search_type))
    return response, conn


def test_search_type_decisions_returns_only_decision_rows():
    response, conn = asyncio.run(_search("decisions"))
    body = response.text

    assert response.status == 200
    assert "needle decision" in body
    assert "needle progress" not in body
    assert conn.decision_fetches == 1
    assert conn.progress_fetches == 0


def test_search_type_progress_returns_only_progress_rows():
    response, conn = asyncio.run(_search("progress"))
    body = response.text

    assert response.status == 200
    assert "needle progress" in body
    assert "needle decision" not in body
    assert conn.decision_fetches == 0
    assert conn.progress_fetches == 1


def test_search_type_all_returns_decision_and_progress_rows():
    response, conn = asyncio.run(_search("all"))
    body = response.text

    assert response.status == 200
    assert "needle decision" in body
    assert "needle progress" in body
    assert conn.decision_fetches == 1
    assert conn.progress_fetches == 1


def test_search_type_unknown_returns_422():
    response, conn = asyncio.run(_search("unknown_value"))

    assert response.status == 422
    assert "search_type must be one of" in response.text
    assert conn.decision_fetches == 0
    assert conn.progress_fetches == 0


def test_search_type_omitted_defaults_to_all():
    response, conn = asyncio.run(_search())
    body = response.text

    assert response.status == 200
    assert "needle decision" in body
    assert "needle progress" in body
    assert conn.decision_fetches == 1
    assert conn.progress_fetches == 1
