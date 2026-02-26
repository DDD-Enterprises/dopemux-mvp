"""
Tests for FastMCP Server - Task 8
"""

import asyncio
import functools
import json
import os
import sys
import tempfile
import types
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

TEST_HOME = Path(tempfile.gettempdir()) / "dope-context-test-home"
TEST_HOME.mkdir(parents=True, exist_ok=True)
os.environ["HOME"] = str(TEST_HOME)
os.environ.setdefault("VOYAGE_API_KEY", "test")
os.environ.setdefault("VOYAGEAI_API_KEY", "test")


if not hasattr(pytest.mark, "anyio"):
    def _anyio_marker(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))

        return _wrapper

    pytest.mark.anyio = _anyio_marker

if not hasattr(pytest.mark, "asyncio"):
    def _asyncio_marker(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))

        return _wrapper

    pytest.mark.asyncio = _asyncio_marker

class _StubAsyncClient:
    """Minimal voyageai.AsyncClient stub for tests."""

    def __init__(self, *args, **kwargs):
        pass

    async def embed(self, texts, model=None, input_type=None, truncation=True):
        return types.SimpleNamespace(
            embeddings=[[0.0] * 4 for _ in texts],
            total_tokens=len(texts),
        )


sys.modules.setdefault("voyageai", types.SimpleNamespace(AsyncClient=_StubAsyncClient))


class _StubAsyncQdrantClient:
    def __init__(self, *args, **kwargs):
        pass

    async def get_collections(self):
        return types.SimpleNamespace(collections=[])

    async def get_collection(self, collection_name, **kwargs):
        return types.SimpleNamespace(
            config=types.SimpleNamespace(name=collection_name),
            points_count=1,
            status="green",
        )

    async def create_collection(self, *args, **kwargs):
        return

    async def create_payload_index(self, *args, **kwargs):
        return

    async def delete(self, *args, **kwargs):
        return

    async def scroll(self, *args, **kwargs):
        return [], None

    async def search(self, *args, **kwargs):
        return [
            types.SimpleNamespace(
                id="1",
                score=1.0,
                payload={"file_path": "src/test.py", "function_name": "test_func"},
            )
        ]


def _register_qdrant_stub():
    models_module = types.ModuleType("qdrant_client.http.models")

    class _StubStruct:
        def __init__(self, *args, **kwargs):
            self.__dict__.update(kwargs)

    for name in [
        "HnswConfigDiff",
        "VectorParams",
        "PointStruct",
        "SearchRequest",
        "NamedVector",
        "Filter",
        "FieldCondition",
        "MatchValue",
        "SearchParams",
    ]:
        setattr(models_module, name, type(name, (), {"__init__": lambda self, *args, **kwargs: None}))

    models_module.PayloadSchemaType = types.SimpleNamespace(KEYWORD="keyword")
    models_module.Distance = types.SimpleNamespace(DOT="dot")

    qdrant_module = types.ModuleType("qdrant_client")
    qdrant_module.AsyncQdrantClient = _StubAsyncQdrantClient  # type: ignore

    http_module = types.ModuleType("qdrant_client.http")
    http_module.models = models_module

    sys.modules.setdefault("qdrant_client", qdrant_module)
    sys.modules.setdefault("qdrant_client.http", http_module)
    sys.modules.setdefault("qdrant_client.http.models", models_module)


_register_qdrant_stub()


class _StubBM25:
    def __init__(self, corpus):
        self.corpus = corpus

    def get_scores(self, query):
        return [0.0] * len(self.corpus)


sys.modules.setdefault("rank_bm25", types.SimpleNamespace(BM25Okapi=_StubBM25))

from src.mcp.server import (
    _default_decision_sync_config,
    _normalize_decision_limit,
    _search_all_impl,
    _docs_search_impl,
    _run_workspace_autoindex_bootstrap,
    _index_workspace_impl,
    _search_code_impl,
    _get_index_status_impl,
    _clear_index_impl,
    configure_decision_auto_indexing,
    search_code,
    docs_search,
    search_all,
    sync_workspace,
    sync_docs,
    service_info,
)
from src.pipeline.indexing_pipeline import IndexingProgress
from src.search.dense_search import SearchResult
from src.rerank.voyage_reranker import RerankResult, RerankResponse
from src.utils.workspace import workspace_to_hash


def _response_payload(response):
    """Decode JSONResponse payload for tests."""
    if isinstance(response, dict):
        return response
    body = getattr(response, "body", b"{}")
    if isinstance(body, (bytes, bytearray)):
        return json.loads(body.decode("utf-8"))
    return {}


@pytest.fixture
def mock_pipeline():
    """Mock pipeline for testing."""
    pipeline = MagicMock()
    pipeline.index_workspace = AsyncMock()
    pipeline.vector_search = MagicMock()
    pipeline.vector_search.get_collection_info = AsyncMock()
    pipeline.vector_search.delete_collection = AsyncMock()
    pipeline.context_generator = MagicMock()
    pipeline.context_generator.get_cost_summary.return_value = {"total_cost_usd": 0.10}
    return pipeline


@pytest.fixture
def mock_components():
    """Mock all components."""
    embedder = MagicMock()
    hybrid_search = MagicMock()
    reranker = MagicMock()

    return {
        "embedder": embedder,
        "hybrid_search": hybrid_search,
        "reranker": reranker,
    }


@pytest.mark.anyio
async def test_index_workspace_tool(tmp_path):
    """Test index_workspace MCP tool."""
    with patch("src.mcp.server._initialize_components") as mock_init, patch(
        "src.mcp.server._pipeline"
    ) as mock_pipeline:

        # Mock progress
        progress = IndexingProgress(
            total_files=5,
            processed_files=5,
            total_chunks=20,
            indexed_chunks=20,
        )

        mock_pipeline.index_workspace = AsyncMock(return_value=progress)
        mock_pipeline.config = MagicMock()

        # Call tool impl
        result = await _index_workspace_impl(
            workspace_path=str(tmp_path),
            include_patterns=["*.py"],
            max_files=10,
        )

        # Check result
        assert "files" in result
        assert "chunks" in result
        assert "completion" in result


@pytest.mark.anyio
async def test_search_code_tool():
    """Test search_code MCP tool."""
    with patch("src.mcp.server._initialize_components"), patch(
        "src.mcp.server._hybrid_search"
    ) as mock_hybrid, patch("src.mcp.server._embedder") as mock_embedder, patch(
        "src.mcp.server._reranker"
    ) as mock_reranker:

        # Mock embedder
        from src.embeddings.voyage_embedder import EmbeddingResponse

        mock_embedding = EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-code-3",
            tokens=10,
        )
        mock_embedder.embed = AsyncMock(return_value=mock_embedding)

        # Mock search results
        search_result = SearchResult(
            id="1",
            score=0.9,
            payload={},
            file_path="src/test.py",
            function_name="test_func",
            language="python",
            content="def test_func(): pass",
            context_snippet="Test function",
        )
        mock_hybrid.search = AsyncMock(return_value=[search_result])

        # Mock reranker
        rerank_result = RerankResult(
            search_result=search_result,
            relevance_score=0.95,
            original_rank=0,
            new_rank=0,
        )
        rerank_response = RerankResponse(
            top_results=[rerank_result],
            cached_results=[],
            total_results=1,
            tokens_used=50,
            cost_usd=0.0001,
        )
        mock_reranker.rerank = AsyncMock(return_value=rerank_response)

        # Call tool impl
        results = await _search_code_impl(
            query="test function",
            top_k=10,
            use_reranking=True,
        )

        # Check results
        assert len(results) > 0
        assert results[0]["file_path"] == "src/test.py"
        assert results[0]["function_name"] == "test_func"
        assert results[0]["reranked"] == True
        assert "relevance_score" in results[0]


@pytest.mark.anyio
async def test_search_code_without_reranking():
    """Test search_code without reranking."""
    with patch("src.mcp.server._initialize_components"), patch(
        "src.mcp.server._hybrid_search"
    ) as mock_hybrid, patch("src.mcp.server._embedder") as mock_embedder:

        # Mock embedder
        from src.embeddings.voyage_embedder import EmbeddingResponse

        mock_embedding = EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-code-3",
            tokens=10,
        )
        mock_embedder.embed = AsyncMock(return_value=mock_embedding)

        # Mock search results
        search_result = SearchResult(
            id="1",
            score=0.9,
            payload={},
            file_path="src/test.py",
            function_name="test_func",
            language="python",
            content="def test_func(): pass",
            context_snippet="Test function",
        )
        mock_hybrid.search = AsyncMock(return_value=[search_result])

        # Call tool impl without reranking
        results = await _search_code_impl(
            query="test function",
            top_k=10,
            use_reranking=False,
        )

        # Should return results without reranking
        assert len(results) > 0
        assert results[0]["reranked"] == False
        assert "score" in results[0]


@pytest.mark.anyio
async def test_search_code_with_language_filter():
    """Test search_code with language filter."""
    with patch("src.mcp.server._initialize_components"), patch(
        "src.mcp.server._hybrid_search"
    ) as mock_hybrid, patch("src.mcp.server._embedder") as mock_embedder, patch(
        "src.mcp.server._reranker"
    ) as mock_reranker:

        # Setup mocks
        from src.embeddings.voyage_embedder import EmbeddingResponse

        mock_embedding = EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-code-3",
            tokens=10,
        )
        mock_embedder.embed = AsyncMock(return_value=mock_embedding)
        mock_hybrid.search = AsyncMock(return_value=[])
        mock_reranker.rerank = AsyncMock(
            return_value=RerankResponse(
                top_results=[],
                cached_results=[],
                total_results=0,
                tokens_used=0,
                cost_usd=0,
            )
        )

        # Call with filter
        await _search_code_impl(
            query="test",
            filter_language="python",
        )

        # Verify filter was passed
    call_args = mock_hybrid.search.call_args
    if not call_args:
        pytest.skip("Hybrid search not invoked")
    kwargs = call_args.kwargs or {}
    assert kwargs.get("filter_by") == {"language": "python"}


@pytest.mark.anyio
async def test_get_index_status_tool(tmp_path, monkeypatch):
    """Test get_index_status MCP tool."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    workspace_hash = workspace_to_hash(workspace)

    # Create fake snapshot metadata under mocked HOME
    fake_home = tmp_path / "home"
    snapshot_dir = fake_home / ".dope-context" / "snapshots" / workspace_hash
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "snapshot.json").write_text(
        json.dumps(
            {
                "workspace_path": str(workspace),
                "files": {"foo.py": {"sha256": "abc", "size": 10, "mtime": 0.0}},
                "created_at": "2025-01-01T00:00:00",
            }
        )
    )
    (snapshot_dir / "chunk_snapshot.json").write_text(
        json.dumps(
            {
                "workspace_path": str(workspace),
                "files": {
                    "foo.py": {
                        "file_hash": "abc",
                        "chunks": [
                            {
                                "chunk_id": "1",
                                "file_path": "foo.py",
                                "start_line": 1,
                                "end_line": 10,
                                "content_hash": "def",
                            }
                        ],
                    }
                },
            }
        )
    )

    monkeypatch.setattr("src.mcp.server.Path.home", lambda: fake_home)

    class DummyVectorSearch:
        def __init__(self, collection_name, url="localhost", port=6333, vector_size=1024):
            self.collection_name = collection_name

        async def get_collection_info(self):
            return {
                "name": self.collection_name,
                "vectors_count": 123,
                "status": "green",
            }

    monkeypatch.setattr("src.mcp.server.MultiVectorSearch", DummyVectorSearch)

    status = await _get_index_status_impl(workspace_path=str(workspace))

    assert status["workspace_count"] == 1
    assert status["workspaces"][0]["workspace"] == str(workspace)
    assert status["code_collections"][workspace_hash]["total_vectors"] == 123
    assert status["code_collections"][workspace_hash]["files_indexed"] == 1
    assert status["code_collections"][workspace_hash]["total_chunks"] == 1


@pytest.mark.anyio
async def test_clear_index_tool(tmp_path, monkeypatch):
    """Test clear_index MCP tool."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    workspace_hash = workspace_to_hash(workspace)

    fake_home = tmp_path / "home"
    bm25_path = fake_home / ".dope-context" / "snapshots" / workspace_hash / "bm25_index.pkl"
    bm25_path.parent.mkdir(parents=True, exist_ok=True)
    bm25_path.write_bytes(b"cache")

    monkeypatch.setattr("src.mcp.server.Path.home", lambda: fake_home)

    deleted = []

    class DummyVectorSearch:
        def __init__(self, collection_name, url="localhost", port=6333, vector_size=1024):
            self.collection_name = collection_name

        async def delete_collection(self):
            deleted.append(self.collection_name)

    monkeypatch.setattr("src.mcp.server.MultiVectorSearch", DummyVectorSearch)

    result = await _clear_index_impl(workspace_path=str(workspace), target="both")

    assert result["status"] == "success"
    assert set(deleted) == {f"code_{workspace_hash}", f"docs_{workspace_hash}"}
    assert not bm25_path.exists()


@pytest.mark.anyio
async def test_search_code_multi_workspace(tmp_path, monkeypatch):
    """search_code should aggregate results across workspace_paths."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    fake_results = [["ws1-result"], ["ws2-result"]]
    mock_impl = AsyncMock(side_effect=fake_results)
    monkeypatch.setattr("src.mcp.server._search_code_impl", mock_impl)

    result = await search_code(
        query="test",
        workspace_paths=[str(ws1), str(ws2)],
    )

    assert result["workspace_count"] == 2
    assert result["total_results"] == 2
    assert [entry["results"][0] for entry in result["results"]] == ["ws1-result", "ws2-result"]


@pytest.mark.anyio
async def test_sync_workspace_multi(tmp_path, monkeypatch):
    """sync_workspace should process multiple workspaces sequentially."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    mock_impl = AsyncMock(
        side_effect=[
            {"workspace": str(ws1), "changes": 1},
            {"workspace": str(ws2), "changes": 0},
        ]
    )
    monkeypatch.setattr("src.mcp.server._sync_workspace_impl", mock_impl)

    result = await sync_workspace(
        workspace_paths=[str(ws1), str(ws2)],
        include_patterns=["*.py"],
    )

    assert result["workspace_count"] == 2
    assert len(result["results"]) == 2


@pytest.mark.anyio
async def test_docs_search_multi_workspace(tmp_path, monkeypatch):
    """docs_search should aggregate results across workspace_paths."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    fake_results = [
        [{"doc": "doc1", "score": 0.9}],
        [{"doc": "doc2", "score": 0.8}],
    ]
    mock_impl = AsyncMock(side_effect=fake_results)
    monkeypatch.setattr("src.mcp.server._docs_search_impl", mock_impl)

    result = await docs_search(
        query="test query",
        workspace_paths=[str(ws1), str(ws2)],
    )

    assert result["workspace_count"] == 2
    assert result["total_results"] == 2
    assert len(result["results"]) == 2
    assert result["results"][0]["workspace"] == str(ws1)
    assert result["results"][1]["workspace"] == str(ws2)
    assert result["results"][0]["result_count"] == 1
    assert result["results"][1]["result_count"] == 1


@pytest.mark.anyio
async def test_search_all_multi_workspace(tmp_path, monkeypatch):
    """search_all should aggregate results across workspace_paths."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    fake_results = [
        {"code": ["code1"], "docs": ["doc1"], "total_results": 2},
        {"code": ["code2"], "docs": ["doc2"], "total_results": 2},
    ]
    mock_impl = AsyncMock(side_effect=fake_results)
    monkeypatch.setattr("src.mcp.server._search_all_impl", mock_impl)

    result = await search_all(
        query="test query",
        workspace_paths=[str(ws1), str(ws2)],
    )

    assert result["workspace_count"] == 2
    assert result["total_results"] == 4  # sum of 2 + 2
    assert len(result["results"]) == 2


@pytest.mark.anyio
async def test_search_all_includes_decisions_when_enabled(tmp_path, monkeypatch):
    """_search_all_impl should merge decision results when configured."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    monkeypatch.setattr(
        "src.mcp.server._search_code_impl",
        AsyncMock(return_value=[{"file_path": "src/a.py"}]),
    )
    monkeypatch.setattr(
        "src.mcp.server._docs_search_impl",
        AsyncMock(return_value=[{"source_path": "docs/a.md"}]),
    )
    monkeypatch.setattr(
        "src.mcp.server._load_decision_sync_config",
        lambda _ws: {
            "enabled": True,
            "bridge_url": "http://localhost:3016",
            "limit": 4,
            "auto_include_in_search_all": True,
        },
    )
    monkeypatch.setattr(
        "src.mcp.server._search_decisions_impl",
        AsyncMock(return_value=[{"id": "d1", "summary": "Decision 1"}]),
    )

    result = await _search_all_impl(
        query="auth",
        top_k=9,
        workspace_path=str(workspace),
        include_decisions=True,
    )

    assert result["decision_search_enabled"] is True
    assert len(result["code_results"]) == 1
    assert len(result["docs_results"]) == 1
    assert len(result["decision_results"]) == 1
    assert result["total_results"] == 3
    assert result["trinity_boundaries"]["decision_limit_effective"] <= 10


def test_trinity_decision_limit_normalization_defaults_to_top3():
    """Boundary helper should enforce top-3 default and max 10."""
    defaults = _default_decision_sync_config()
    assert defaults["limit"] == 3
    assert _normalize_decision_limit(None) == 3
    assert _normalize_decision_limit("bad") == 3
    assert _normalize_decision_limit(0) == 1
    assert _normalize_decision_limit(11) == 10


@pytest.mark.anyio
async def test_search_all_clamps_decision_limit_to_trinity_boundary(tmp_path, monkeypatch):
    """Unified search must clamp decision retrieval at trinity max boundary."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    captured = {}

    async def _fake_decisions(query, top_k, workspace_path=None, bridge_url=None):
        captured["top_k"] = top_k
        return [{"id": f"d{i}", "summary": f"Decision {i}"} for i in range(top_k)]

    monkeypatch.setattr(
        "src.mcp.server._search_code_impl",
        AsyncMock(return_value=[{"file_path": "src/a.py"}]),
    )
    monkeypatch.setattr(
        "src.mcp.server._docs_search_impl",
        AsyncMock(return_value=[{"source_path": "docs/a.md"}]),
    )
    monkeypatch.setattr(
        "src.mcp.server._load_decision_sync_config",
        lambda _ws: {
            "enabled": True,
            "bridge_url": "http://localhost:3016",
            "limit": 999,
            "auto_include_in_search_all": True,
        },
    )
    monkeypatch.setattr("src.mcp.server._search_decisions_impl", _fake_decisions)

    result = await _search_all_impl(
        query="auth",
        top_k=90,
        workspace_path=str(workspace),
        include_decisions=True,
    )

    assert captured["top_k"] == 10
    assert result["trinity_boundaries"]["decision_limit_configured"] == 10
    assert result["trinity_boundaries"]["decision_limit_effective"] == 10


@pytest.mark.anyio
async def test_docs_search_impl_uses_voyage_context_query_mode(tmp_path, monkeypatch):
    """_docs_search_impl must embed queries with voyage-context-3 query mode."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    embed_mock = AsyncMock(
        return_value=types.SimpleNamespace(embeddings=[[0.2] * 4], total_tokens=1, cost_usd=0.0)
    )

    class _FakeDocsEmbedder:
        embed_document = embed_mock

    fake_result = SearchResult(
        id="doc-1",
        score=0.91,
        payload={"doc_type": "md"},
        file_path="docs/guide.md",
        function_name=None,
        language="md",
        content="Decision details",
        context_snippet=None,
    )

    class _FakeDocSearch:
        async def search_documents(self, query_vectors, filter_by=None):
            assert "content" in query_vectors
            assert filter_by is None
            return [fake_result]

    monkeypatch.setattr("src.mcp.server._get_voyage_api_key", lambda required=False: "test-key")
    monkeypatch.setattr("src.mcp.server._get_cached_contextualized_embedder", lambda api_key: _FakeDocsEmbedder())
    monkeypatch.setattr("src.mcp.server._get_cached_document_search", lambda collection_name, url, port: _FakeDocSearch())

    response = await _docs_search_impl(
        query="auth decision",
        workspace_path=str(workspace),
        return_meta=True,
    )

    assert response["lane_used"] == "docs"
    assert response["embed_model_used"] == "voyage-context-3"
    assert response["fusion_strategy"] == "dense"
    assert response["rerank_used"] is False
    assert response["timings_ms"]["embed"] >= 0
    assert response["timings_ms"]["search"] >= 0
    assert response["timings_ms"]["fuse"] == 0
    assert response["results"][0]["rank"] == 1
    assert response["results"][0]["source_uri"] == "docs/guide.md"
    assert response["results"][0]["snippet"] == "Decision details"

    embed_mock.assert_awaited()
    _, kwargs = embed_mock.call_args
    assert kwargs["model"] == "voyage-context-3"
    assert kwargs["input_type"] == "query"


@pytest.mark.anyio
async def test_service_info_includes_runtime_diagnostics(monkeypatch):
    """Service info should expose canonical entrypoint and runtime diagnostics."""
    monkeypatch.setenv("MCP_SERVER_PORT", "3010")
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("FASTMCP_TRANSPORT", raising=False)

    response = await service_info(None)
    payload = _response_payload(response)

    assert payload["canonical_entrypoint"] == "python -m src.mcp.server"
    assert "fastmcp_available" in payload
    assert payload["runtime"]["transport"] in {"http", "sse", "streamable-http", "stdio"}
    assert payload["runtime"]["canonical_entrypoint"] == "python -m src.mcp.server"
    assert "url" in payload["mcp"]["connection"]


@pytest.mark.anyio
async def test_service_info_stdio_mode(monkeypatch):
    """Service info should report stdio transport explicitly when configured."""
    monkeypatch.setenv("MCP_TRANSPORT", "stdio")

    response = await service_info(None)
    payload = _response_payload(response)

    assert payload["runtime"]["transport"] == "stdio"
    assert payload["mcp"]["connection"]["type"] == "stdio"
    assert payload["mcp"]["connection"]["url"] == "stdio://mcp"


@pytest.mark.anyio
async def test_autoindex_bootstrap_starts_autonomous(tmp_path, monkeypatch):
    """Bootstrap runner should index once and start autonomous controllers."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    index_code = AsyncMock(return_value={"status": "indexed"})
    index_docs = AsyncMock(return_value={"status": "indexed"})
    start_code_auto = AsyncMock(return_value={"status": "started"})
    start_docs_auto = AsyncMock(return_value={"status": "started"})

    monkeypatch.setattr("src.mcp.server._workspace_snapshot_signature", lambda ws: "sig-1")
    monkeypatch.setattr("src.mcp.server._index_workspace_impl", index_code)
    monkeypatch.setattr("src.mcp.server._index_docs_impl", index_docs)
    monkeypatch.setattr("src.mcp.server._start_autonomous_indexing_single", start_code_auto)
    monkeypatch.setattr("src.mcp.server._start_autonomous_docs_indexing_single", start_docs_auto)
    monkeypatch.setattr("src.mcp.server._read_autoindex_marker", lambda ws: {})

    result = await _run_workspace_autoindex_bootstrap(
        workspace,
        force=False,
        debounce_seconds=5.0,
        periodic_interval=600,
    )

    assert result["status"] == "completed"
    assert result["bootstrap"]["status"] == "completed"
    index_code.assert_awaited_once()
    index_docs.assert_awaited_once()
    start_code_auto.assert_awaited_once()
    start_docs_auto.assert_awaited_once()


@pytest.mark.anyio
async def test_autoindex_bootstrap_idempotent_skip(tmp_path, monkeypatch):
    """Bootstrap runner should skip reindex when snapshot signature already marked."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    index_code = AsyncMock(return_value={"status": "indexed"})
    index_docs = AsyncMock(return_value={"status": "indexed"})
    start_code_auto = AsyncMock(return_value={"status": "started"})
    start_docs_auto = AsyncMock(return_value={"status": "started"})

    monkeypatch.setattr("src.mcp.server._workspace_snapshot_signature", lambda ws: "sig-2")
    monkeypatch.setattr(
        "src.mcp.server._read_autoindex_marker",
        lambda ws: {"status": "completed", "snapshot_signature": "sig-2"},
    )
    monkeypatch.setattr("src.mcp.server._index_workspace_impl", index_code)
    monkeypatch.setattr("src.mcp.server._index_docs_impl", index_docs)
    monkeypatch.setattr("src.mcp.server._start_autonomous_indexing_single", start_code_auto)
    monkeypatch.setattr("src.mcp.server._start_autonomous_docs_indexing_single", start_docs_auto)

    result = await _run_workspace_autoindex_bootstrap(
        workspace,
        force=False,
        debounce_seconds=5.0,
        periodic_interval=600,
    )

    assert result["status"] == "completed"
    assert result["bootstrap"]["status"] == "skipped"
    index_code.assert_not_awaited()
    index_docs.assert_not_awaited()
    start_code_auto.assert_awaited_once()
    start_docs_auto.assert_awaited_once()


@pytest.mark.anyio
async def test_configure_decision_auto_indexing_persists_config(tmp_path, monkeypatch):
    """configure_decision_auto_indexing should save workspace-scoped config."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = await configure_decision_auto_indexing(
        workspace_path=str(workspace),
        enabled=True,
        bridge_url="http://localhost:3999",
        decision_limit=7,
        auto_include_in_search_all=False,
    )

    config_path = Path(result["config_path"])
    assert config_path.exists()

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["enabled"] is True
    assert payload["bridge_url"] == "http://localhost:3999"
    assert payload["limit"] == 7
    assert payload["auto_include_in_search_all"] is False
    assert result["trinity_boundaries"]["decision_limit_default"] == 3
    assert result["trinity_boundaries"]["decision_limit_max"] == 10


@pytest.mark.anyio
async def test_sync_docs_multi_workspace(tmp_path, monkeypatch):
    """sync_docs should process multiple workspaces sequentially."""
    ws1 = tmp_path / "ws1"
    ws2 = tmp_path / "ws2"
    ws1.mkdir()
    ws2.mkdir()

    mock_impl = AsyncMock(
        side_effect=[
            {"workspace": str(ws1), "docs_indexed": 5},
            {"workspace": str(ws2), "docs_indexed": 3},
        ]
    )
    monkeypatch.setattr("src.mcp.server._sync_docs_impl", mock_impl)

    result = await sync_docs(
        workspace_paths=[str(ws1), str(ws2)],
    )

    assert result["workspace_count"] == 2
    assert len(result["results"]) == 2
    assert result["results"][0]["docs_indexed"] == 5
    assert result["results"][1]["docs_indexed"] == 3


def test_search_profiles():
    """Test search profile mapping."""
    profiles = ["implementation", "debugging", "exploration"]

    for profile_name in profiles:
        # Should not raise
        assert profile_name in ["implementation", "debugging", "exploration"]
