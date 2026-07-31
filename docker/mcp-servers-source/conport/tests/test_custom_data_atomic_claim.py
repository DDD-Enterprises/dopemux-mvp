"""Tests for ConPort POST /api/custom_data/claim — atomic idempotency claims."""
import asyncio
import json
import sys
import types
from pathlib import Path

import pytest

CONPORT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONPORT_DIR))

# Stub mcp.server.fastmcp + asyncpg + redis before importing conport modules
class _FastMCPStub:
    def __init__(self, *args, **kwargs):
        self.tools = []

    def tool(self):
        def decorator(func):
            self.tools.append(func.__name__)
            return func
        return decorator

fastmcp_module = types.ModuleType("mcp.server.fastmcp")
fastmcp_module.FastMCP = _FastMCPStub
mcp_module = types.ModuleType("mcp")
mcp_server_module = types.ModuleType("mcp.server")
mcp_server_models_module = types.ModuleType("mcp.server.models")
mcp_server_models_module.InitializationOptions = object
mcp_server_stdio_module = types.ModuleType("mcp.server.stdio")
mcp_server_stdio_module.stdio_server = object
sys.modules.setdefault("mcp", mcp_module)
sys.modules.setdefault("mcp.server", mcp_server_module)
sys.modules.setdefault("mcp.server.fastmcp", fastmcp_module)
sys.modules.setdefault("mcp.server.models", mcp_server_models_module)
sys.modules.setdefault("mcp.server.stdio", mcp_server_stdio_module)

# Stub asyncpg and redis so enhanced_server doesn't auto-install
asyncpg_stub = types.ModuleType("asyncpg")
asyncpg_stub.connect = lambda *a, **kw: None
redis_stub = types.ModuleType("redis")
redis_stub.Redis = lambda *a, **kw: None
redis_stub.asyncio = types.ModuleType("redis.asyncio")
redis_stub.asyncio.Redis = lambda *a, **kw: None
aioredis_stub = types.ModuleType("aioredis")
aioredis_stub.Redis = lambda *a, **kw: None
sys.modules.setdefault("asyncpg", asyncpg_stub)
sys.modules.setdefault("redis", redis_stub)
sys.modules.setdefault("redis.asyncio", redis_stub.asyncio)
sys.modules.setdefault("aioredis", aioredis_stub)


@pytest.mark.asyncio
class TestCustomDataAtomicClaim:
    """Owner-level contract tests for the atomic claim endpoint."""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """In-memory fake ConPort DB mimicking asyncpg pool/conn/transaction."""
        self.store = {}
        self.deleted_keys = set()
        self.insert_calls = [0]

        store_ref = self.store
        deleted_ref = self.deleted_keys
        insert_counter = self.insert_calls

        class FakeRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

        class FakeTransaction:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                pass

        class FakeConnection:
            def transaction(self):
                return FakeTransaction()

            async def fetchrow(self, sql, *args):
                if 'INSERT' in sql and 'ON CONFLICT' in sql:
                    ws_id, cat, key, val_json = args[0], args[1], args[2], args[3]
                    lookup = (ws_id, cat, key)
                    insert_counter[0] += 1
                    if lookup in store_ref and lookup not in deleted_ref:
                        return None
                    parsed = json.loads(val_json)
                    store_ref[lookup] = parsed
                    return FakeRow({'value': val_json})

                if 'SELECT value FROM custom_data' in sql:
                    ws_id, cat, key = args[0], args[1], args[2]
                    lookup = (ws_id, cat, key)
                    if lookup not in store_ref or lookup in deleted_ref:
                        return None
                    return FakeRow({'value': json.dumps(store_ref[lookup])})

                return None

            async def execute(self, sql, *args):
                return "DONE"

        class FakePoolAcquireContext:
            async def __aenter__(self):
                return FakeConnection()

            async def __aexit__(self, exc_type, exc, tb):
                pass

        class FakePool:
            def acquire(self):
                return FakePoolAcquireContext()

        self.fake_pool = FakePool()
        self.store.clear()
        self.deleted_keys.clear()
        self.insert_calls = [0]

        yield

    def _make_claim(self, ws="ws-1", cat="workflow_epics", key="epic_abc", fp="abc123", payload=None):
        if payload is None:
            payload = {"title": "Fix races", "_fingerprint_v1": fp}
        return {
            "workspace_id": ws,
            "category": cat,
            "key": key,
            "value": payload,
        }

    async def test_first_claim_returns_created(self, monkeypatch):
        from enhanced_server import EnhancedConPortServer
        app = EnhancedConPortServer()
        app.db_pool = self.fake_pool

        from aiohttp import web
        body = self._make_claim()
        req = self._fake_request(body)

        resp = await app.claim_custom_data(req)
        data = json.loads(resp.text)
        assert data["result"] == "CREATED"
        assert data["workspace_id"] == "ws-1"
        assert data["category"] == "workflow_epics"
        assert data["key"] == "epic_abc"
        assert data["value"]["_fingerprint_v1"] == "abc123"
        assert resp.status == 200

    async def test_identical_second_claim_returns_matched(self, monkeypatch):
        from enhanced_server import EnhancedConPortServer
        app = EnhancedConPortServer()
        app.db_pool = self.fake_pool

        from aiohttp import web
        body = self._make_claim(fp="abc123")

        resp1 = await app.claim_custom_data(self._fake_request(body))
        assert json.loads(resp1.text)["result"] == "CREATED"

        resp2 = await app.claim_custom_data(self._fake_request(body))
        data = json.loads(resp2.text)
        assert data["result"] == "MATCHED"
        assert data["value"]["_fingerprint_v1"] == "abc123"
        assert resp2.status == 200

    async def test_different_second_claim_returns_conflict(self, monkeypatch):
        from enhanced_server import EnhancedConPortServer
        app = EnhancedConPortServer()
        app.db_pool = self.fake_pool

        from aiohttp import web
        body1 = self._make_claim(fp="abc123", payload={"title": "Fix races", "_fingerprint_v1": "abc123"})
        body2 = self._make_claim(fp="xyz789", payload={"title": "Different", "_fingerprint_v1": "xyz789"})

        resp1 = await app.claim_custom_data(self._fake_request(body1))
        assert json.loads(resp1.text)["result"] == "CREATED"

        resp2 = await app.claim_custom_data(self._fake_request(body2))
        data = json.loads(resp2.text)
        assert data["result"] == "CONFLICT"
        assert data["value"]["_fingerprint_v1"] == "abc123"
        assert resp2.status == 200

    async def test_legacy_row_returns_legacy_unfingerprinted(self, monkeypatch):
        from enhanced_server import EnhancedConPortServer
        app = EnhancedConPortServer()
        app.db_pool = self.fake_pool

        self.store[("ws-1", "workflow_epics", "epic_abc")] = {"title": "Old", "priority": "high"}

        from aiohttp import web
        resp = await app.claim_custom_data(self._fake_request(self._make_claim(fp="abc123")))
        data = json.loads(resp.text)
        assert data["result"] == "LEGACY_UNFINGERPRINTED"
        assert data["value"]["title"] == "Old"
        assert "_fingerprint_v1" not in data["value"]

    async def test_missing_fingerprint_returns_400(self, monkeypatch):
        from enhanced_server import EnhancedConPortServer
        app = EnhancedConPortServer()
        app.db_pool = self.fake_pool

        body = {"workspace_id": "ws-1", "category": "x", "key": "y", "value": {"no_fp": True}}
        from aiohttp import web
        resp = await app.claim_custom_data(self._fake_request(body))
        assert resp.status == 400
        assert json.loads(resp.text)["result"] == "MISSING_FINGERPRINT"

    async def test_20_concurrent_identical_claims(self, monkeypatch):
        from enhanced_server import EnhancedConPortServer
        app = EnhancedConPortServer()
        app.db_pool = self.fake_pool

        from aiohttp import web
        body = self._make_claim(fp="concurrent-fp-1")

        async def one_claim():
            return await app.claim_custom_data(self._fake_request(body))

        results = await asyncio.gather(*[one_claim() for _ in range(20)])
        parsed = [json.loads(r.text) for r in results]

        created = [p for p in parsed if p["result"] == "CREATED"]
        matched = [p for p in parsed if p["result"] == "MATCHED"]

        assert len(created) == 1
        assert len(matched) == 19

        match_set = {json.dumps(p["value"], sort_keys=True) for p in parsed}
        assert len(match_set) == 1

    async def test_20_concurrent_conflicting_claims(self, monkeypatch):
        from enhanced_server import EnhancedConPortServer
        app = EnhancedConPortServer()
        app.db_pool = self.fake_pool

        from aiohttp import web

        async def one_claim(idx):
            fp = f"conflict-fp-{idx}"
            body = self._make_claim(fp=fp, payload={"title": f"T{idx}", "_fingerprint_v1": fp})
            return await app.claim_custom_data(self._fake_request(body))

        results = await asyncio.gather(*[one_claim(i) for i in range(20)])
        parsed = [json.loads(r.text) for r in results]

        created = [p for p in parsed if p["result"] == "CREATED"]
        conflicted = [p for p in parsed if p["result"] == "CONFLICT"]

        assert len(created) == 1
        assert len(conflicted) == 19, f"Expected 19 CONFLICT, got {len(conflicted)}: {[p['result'] for p in parsed]}"

        persisted_keys = set(self.store.keys())
        assert persisted_keys == {("ws-1", "workflow_epics", "epic_abc")}

    def _fake_request(self, body_dict):
        import aiohttp

        class FakeRequest:
            async def json(self):
                return body_dict

            @property
            def method(self):
                return "POST"

        return FakeRequest()
