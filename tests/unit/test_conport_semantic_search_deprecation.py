import importlib
import logging
import sys
import types

import pytest

# ConPort MCP tools expect legacy symbols that may not exist in newer mcp packages.
try:
    mcp_mod = importlib.import_module("mcp")
except ModuleNotFoundError:
    mcp_mod = types.ModuleType("mcp")
    sys.modules["mcp"] = mcp_mod

if not hasattr(mcp_mod, "Tool"):
    mcp_mod.Tool = type("Tool", (), {})
if not hasattr(mcp_mod, "ToolResult"):
    mcp_mod.ToolResult = type("ToolResult", (), {})

try:
    mcp_types_mod = importlib.import_module("mcp.types")
except Exception:
    mcp_types_mod = types.ModuleType("mcp.types")
    sys.modules["mcp.types"] = mcp_types_mod

if not hasattr(mcp_types_mod, "TextContent"):
    mcp_types_mod.TextContent = type("TextContent", (), {})
if not hasattr(mcp_types_mod, "ImageContent"):
    mcp_types_mod.ImageContent = type("ImageContent", (), {})

# Optional DB deps for this module are stubbed for unit testing.
if "asyncpg" not in sys.modules:
    sys.modules["asyncpg"] = types.ModuleType("asyncpg")

if "pgvector" not in sys.modules:
    sys.modules["pgvector"] = types.ModuleType("pgvector")
if "pgvector.asyncpg" not in sys.modules:
    pgvector_asyncpg = types.ModuleType("pgvector.asyncpg")
    pgvector_asyncpg.register_vector = lambda *_args, **_kwargs: None
    sys.modules["pgvector.asyncpg"] = pgvector_asyncpg

from dopemux.mcp.conport_mcp_tools import ConPortMCPTools


class _FakeConn:
    def __init__(self, rows):
        self.rows = rows
        self.last_sql = None
        self.last_args = None

    async def fetch(self, sql, *args):
        self.last_sql = sql
        self.last_args = args
        return self.rows


class _AcquireCtx:
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
        return _AcquireCtx(self.conn)


@pytest.mark.asyncio
async def test_semantic_search_deprecated_keyword_fallback_metadata(caplog):
    rows = [
        {
            "entity_type": "decision",
            "entity_id": "dec-1",
            "content": "Use bridge routing for task orchestration",
            "created_at": "2026-02-06T00:00:00Z",
        }
    ]
    conn = _FakeConn(rows)
    tools = ConPortMCPTools(_FakePool(conn))

    with caplog.at_level(logging.WARNING):
        result = await tools.semantic_search(
            workspace_id="dopemux-mvp",
            query="bridge routing",
            entity_types=["decision"],
            top_k=3,
        )

    assert len(result) == 1
    assert result[0]["entity_type"] == "decision"
    assert result[0]["deprecated"] is True
    assert result[0]["search_mode"] == "keyword_fallback"
    assert "Deprecated compatibility shim" in result[0]["deprecation_notice"]
    assert result[0]["similarity_score"] is None
    assert result[0]["chunk_index"] is None

    assert conn.last_sql is not None
    assert "FROM decisions" in conn.last_sql
    assert "FROM progress_entries" in conn.last_sql
    assert conn.last_args[0] == "dopemux-mvp"
    assert conn.last_args[1] == "%bridge routing%"
    assert conn.last_args[2] == 3
    assert conn.last_args[3] == ["decision"]

    assert any("deprecated and running in keyword fallback mode" in msg for msg in caplog.messages)
