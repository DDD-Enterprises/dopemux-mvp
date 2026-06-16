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
        if key in self.values:
            return self.values[key]["value"]
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

    async def fetchval(self, sql, *args):
        self.calls.append((sql, args))
        return False

    async def fetch(self, sql, *args):
        self.calls.append((sql, args))
        if "user_id" in sql:
            raise AssertionError("active ConPort schema has no user_id column")
        if "source_item_id" in sql or "target_item_id" in sql:
            raise AssertionError("entity_relationships uses source_id/target_id")
        if "::int" in sql:
            raise AssertionError("decisions.id is UUID, not integer")
        return []


class RecordingMigratedConn:
    def __init__(self):
        self.calls = []

    async def fetchval(self, sql, *args):
        self.calls.append((sql, args))
        if args == ("public", "decisions", "user_id"):
            return True
        if args == ("public", "progress_entries", "user_id"):
            return True
        return False

    async def fetch(self, sql, *args):
        self.calls.append((sql, args))
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


def test_unified_search_preserves_user_scope_when_user_id_column_exists():
    conn = RecordingMigratedConn()
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(conn), redis_client=FakeRedis())

    results = asyncio.run(
        api.search_across_workspaces(
            user_id="alice",
            query="test",
            workspaces=["bob-ws"],
        )
    )

    assert results == []
    search_sql, search_args = conn.calls[-1]
    assert "WHERE user_id = $2" in search_sql
    assert "AND workspace_id = ANY($3)" in search_sql
    assert search_args == ("test", "alice", ["bob-ws"], 50)


def test_unified_search_rehydrates_cached_created_at_timestamp():
    fake_redis = FakeRedis()
    fake_redis.values["unified_search:alice:test:ws-1"] = {
        "ttl": 60,
        "value": json.dumps(
            [
                {
                    "decision_id": "decision-1",
                    "workspace_id": "ws-1",
                    "summary": "Cached decision",
                    "rationale": "cached",
                    "created_at": "2026-06-16T06:00:00+00:00",
                    "relevance_score": 0.75,
                    "user_id": "alice",
                    "tags": [],
                }
            ]
        ),
    }
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(RecordingConn()), redis_client=fake_redis)

    results = asyncio.run(
        api.search_across_workspaces(
            user_id="alice",
            query="test",
            workspaces=["ws-1"],
        )
    )

    assert results[0].created_at.isoformat() == "2026-06-16T06:00:00+00:00"


def test_get_user_workspaces_preserves_user_scope_when_user_id_column_exists():
    conn = RecordingMigratedConn()
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(conn), redis_client=FakeRedis())

    workspaces = asyncio.run(api._get_user_workspaces("alice"))

    assert workspaces == []
    workspace_sql, workspace_args = conn.calls[-1]
    assert "WHERE user_id = $1" in workspace_sql
    assert workspace_args == ("alice",)


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


def test_relationship_traversal_restricts_to_same_workspace_when_cross_workspace_disabled():
    conn = RecordingConn()
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(conn), redis_client=FakeRedis())

    graph = asyncio.run(
        api.get_related_decisions(
            decision_id="00000000-0000-0000-0000-000000000001",
            user_id="ignored-by-active-schema",
            include_workspaces=False,
        )
    )

    assert graph["total_nodes"] == 0
    relationship_sql, relationship_args = conn.calls[-1]
    assert "AND d.workspace_id = dg.workspace_id" in relationship_sql
    assert "OR $3 = true" not in relationship_sql
    assert relationship_args == ("00000000-0000-0000-0000-000000000001", 3)


def test_relationship_traversal_preserves_user_scope_when_user_id_column_exists():
    conn = RecordingMigratedConn()
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(conn), redis_client=FakeRedis())

    graph = asyncio.run(
        api.get_related_decisions(
            decision_id="00000000-0000-0000-0000-000000000001",
            user_id="alice",
        )
    )

    assert graph["total_nodes"] == 0
    relationship_sql, relationship_args = conn.calls[-1]
    assert "WHERE id::text = $1 AND user_id = $2" in relationship_sql
    assert "WHERE d.user_id = $2" in relationship_sql
    assert relationship_args == (
        "00000000-0000-0000-0000-000000000001",
        "alice",
        3,
        True,
    )


def test_migrated_relationship_traversal_restricts_to_same_workspace_when_cross_workspace_disabled():
    conn = RecordingMigratedConn()
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(conn), redis_client=FakeRedis())

    graph = asyncio.run(
        api.get_related_decisions(
            decision_id="00000000-0000-0000-0000-000000000001",
            user_id="alice",
            include_workspaces=False,
        )
    )

    assert graph["total_nodes"] == 0
    relationship_sql, relationship_args = conn.calls[-1]
    assert "AND d.workspace_id = dg.workspace_id" in relationship_sql
    assert "OR $4 = true" not in relationship_sql
    assert relationship_args == (
        "00000000-0000-0000-0000-000000000001",
        "alice",
        3,
    )


def test_workspace_summary_preserves_user_scope_when_user_id_columns_exist():
    conn = RecordingMigratedConn()
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(conn), redis_client=FakeRedis())

    summaries = asyncio.run(api.get_workspace_summary("alice"))

    assert summaries == []
    summary_sql, summary_args = conn.calls[-1]
    assert "ON p.workspace_id = d.workspace_id AND p.user_id = d.user_id" in summary_sql
    assert "WHERE d.user_id = $1" in summary_sql
    assert summary_args == ("alice",)


def test_workspace_summary_rehydrates_cached_last_activity_timestamp():
    fake_redis = FakeRedis()
    fake_redis.values["workspace_summary:alice"] = {
        "ttl": 300,
        "value": json.dumps(
            [
                {
                    "workspace_id": "ws-1",
                    "name": "ws-1",
                    "total_decisions": 2,
                    "recent_decisions_7d": 1,
                    "total_progress": 3,
                    "in_progress_count": 1,
                    "last_activity": "2026-06-16T06:00:00+00:00",
                }
            ]
        ),
    }
    api = unified_queries.UnifiedQueryAPI(db_pool=FakePool(RecordingConn()), redis_client=fake_redis)

    summaries = asyncio.run(api.get_workspace_summary("alice"))

    assert summaries[0].last_activity.isoformat() == "2026-06-16T06:00:00+00:00"
