import asyncio
import importlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4


CONPORT_DIR = (
    Path(__file__).resolve().parents[2] / "docker" / "mcp-servers-source" / "conport"
)
sys.path.insert(0, str(CONPORT_DIR))

enhanced_server = importlib.import_module("enhanced_server")
unified_queries = importlib.import_module("unified_queries")


class FakeRedis:
    def __init__(self):
        self.values = {}

    async def get(self, key):
        return None

    async def setex(self, key, ttl, value):
        self.values[key] = {"ttl": ttl, "value": value}

    async def ping(self):
        return True


class FakeAcquire:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, conn=None):
        self.conn = conn

    def acquire(self):
        return FakeAcquire(self.conn)


class FakeSearchConn:
    def __init__(self, decision_id):
        self.decision_id = decision_id

    async def fetch(self, sql, *args):
        return [
            {
                "id": self.decision_id,
                "workspace_id": "ws-1",
                "summary": "ConPort search serialization",
                "rationale": "UUID and Decimal values must be JSON safe",
                "created_at": datetime(2026, 6, 16, tzinfo=timezone.utc),
                "rank": Decimal("0.875"),
            }
        ]


class RecordingConn:
    def __init__(self):
        self.calls = []

    async def fetch(self, sql, *args):
        self.calls.append((sql, args))
        if "user_id" in sql:
            raise AssertionError("active ConPort schema has no user_id column")
        if "source_item_id" in sql or "target_item_id" in sql:
            raise AssertionError("entity_relationships uses source_id/target_id")
        if "::int" in sql:
            raise AssertionError("decisions.id is UUID, not integer")
        return []


def test_unified_query_api_defaults_to_public_schema():
    api = unified_queries.UnifiedQueryAPI(db_pool=object(), redis_client=object())

    assert api.schema == "public"


def test_init_connections_uses_public_schema(monkeypatch):
    async def fake_create_pool(*args, **kwargs):
        return FakePool()

    async def fake_from_url(*args, **kwargs):
        return FakeRedis()

    monkeypatch.setattr(enhanced_server.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(enhanced_server.aioredis, "from_url", fake_from_url)
    monkeypatch.setattr(enhanced_server, "DopeconBridgeClient", None)
    monkeypatch.setattr(
        enhanced_server.EnhancedConPortServer,
        "_ensure_schema",
        lambda self: asyncio.sleep(0),
    )

    server = enhanced_server.EnhancedConPortServer()

    asyncio.run(server.init_connections())

    assert server.unified_query_api.schema == "public"


def test_conport_dockerfile_copies_unified_queries_runtime_module():
    dockerfile = CONPORT_DIR / "Dockerfile"

    assert "COPY docker/mcp-servers-source/conport/unified_queries.py ." in dockerfile.read_text()


def test_search_content_serializes_uuid_and_decimal_rows():
    decision_id = uuid4()
    fake_redis = FakeRedis()
    server = enhanced_server.EnhancedConPortServer()
    server.redis = fake_redis
    server.db_pool = FakePool(FakeSearchConn(decision_id))
    request = SimpleNamespace(
        match_info={"workspace_id": "ws-1"},
        query={"q": "serialization", "type": "decisions"},
    )

    response = asyncio.run(server.search_content(request))

    assert response.status == 200
    payload = json.loads(response.text)
    decision = payload["results"]["decisions"][0]
    assert decision["id"] == str(decision_id)
    assert decision["rank"] == 0.875
    cached_payload = json.loads(next(iter(fake_redis.values.values()))["value"])
    assert cached_payload["results"]["decisions"][0]["id"] == str(decision_id)


def test_unified_search_matches_active_schema_without_user_id_column():
    conn = RecordingConn()
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(conn), redis_client=FakeRedis())

    results = asyncio.run(
        api.search_across_workspaces(
            user_id="ignored-by-active-schema",
            query="test",
            workspaces=["ws-1"],
        )
    )

    assert results == []
    assert conn.calls


def test_relationship_traversal_uses_uuid_relationship_columns():
    conn = RecordingConn()
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(conn), redis_client=FakeRedis())

    graph = asyncio.run(
        api.get_related_decisions(
            decision_id="00000000-0000-0000-0000-000000000001",
            user_id="ignored-by-active-schema",
        )
    )

    assert graph == {
        "root": "00000000-0000-0000-0000-000000000001",
        "nodes": [],
        "total_nodes": 0,
        "max_depth_reached": 0,
    }
