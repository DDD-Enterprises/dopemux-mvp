"""Reliability repairs: token exactness, tokenizer memoization, budgets, rerank."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.embeddings.voyage_embedder import VoyageEmbedder
from src.pipeline.docs_pipeline import DocIndexingPipeline
from src.rerank.voyage_reranker import RERANK_MAX_QUERY_TOKENS, VoyageReranker
from src.search.dense_search import SearchResult
from src.utils.model_tokenizer import TokenCount, VoyageTokenCounter
from src.utils.token_budget import truncate_code_results


@pytest.mark.anyio
async def test_token_count_exact_false_under_tokenizer_fallback():
    embedder = VoyageEmbedder(api_key="test-key")
    embedder.token_counter.count_each = AsyncMock(
        return_value=[TokenCount(count=12, exact=False)]
    )

    class FakeResult:
        embeddings = [[0.1] * 1024]
        # No total_tokens attribute -> not api_reported

    embedder._api_embed = AsyncMock(return_value=FakeResult())
    embedder._check_rate_limit = AsyncMock()

    response = await embedder.embed("hello", model="voyage-code-3")
    assert response.token_count_exact is False


@pytest.mark.anyio
async def test_tokenizer_load_failure_attempted_once_per_model():
    counter = VoyageTokenCounter(api_key="test-key")

    class BoomClient:
        def tokenize(self, texts, model):
            raise RuntimeError("network blocked")

    counter._client = BoomClient()
    texts = [f"text-{i}" for i in range(5)]
    counts = await counter.count_each(texts, "voyage-code-3")
    assert all(not c.exact for c in counts)
    assert counter.tokenizer_load_attempts("voyage-code-3") == 1
    # Second batch must not re-attempt load.
    await counter.count_each(["more"], "voyage-code-3")
    assert counter.tokenizer_load_attempts("voyage-code-3") == 1


def test_file_path_and_doc_id_legacy_reconciliation(tmp_path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    source = workspace / "a.md"
    source.write_text("x", encoding="utf-8")
    pipeline = DocIndexingPipeline(
        embedder=MagicMock(),
        doc_search=MagicMock(),
        workspace_path=workspace,
        workspace_id="ws1",
    )
    absolute = source.resolve().as_posix()
    uri = pipeline._source_uri(source)
    payloads = [
        {"id": "1", "file_path": absolute},
        {"id": "2", "doc_id": "a.md"},
        {"id": "3", "source_path": (workspace / "other.md").resolve().as_posix()},
        {"id": "4", "source_uri": uri},
    ]
    index = pipeline._build_payload_index(payloads)
    ids = pipeline._existing_point_ids(source, "a.md", index)
    assert ids == {"1", "2", "4"}


def test_same_basename_documents_remain_isolated():
    pipeline = DocIndexingPipeline(
        embedder=MagicMock(),
        doc_search=MagicMock(),
        workspace_path=Path("/tmp/ws"),
        workspace_id="ws1",
    )
    payloads = [
        {"id": "1", "source_path": "/tmp/ws/dir1/readme.md", "doc_id": "dir1/readme.md"},
        {"id": "2", "source_path": "/tmp/ws/dir2/readme.md", "doc_id": "dir2/readme.md"},
    ]
    index = pipeline._build_payload_index(payloads)
    ids = pipeline._existing_point_ids(
        Path("/tmp/ws/dir1/readme.md"), "dir1/readme.md", index
    )
    assert ids == {"1"}
    assert "2" not in ids


def test_cross_workspace_point_ids_differ():
    p1 = DocIndexingPipeline(
        embedder=MagicMock(),
        doc_search=MagicMock(),
        workspace_path=Path("/tmp/ws1"),
        workspace_id="ws-aaa",
    )
    p2 = DocIndexingPipeline(
        embedder=MagicMock(),
        doc_search=MagicMock(),
        workspace_path=Path("/tmp/ws2"),
        workspace_id="ws-bbb",
    )
    assert p1._point_id_for_chunk("doc.md", 0) != p2._point_id_for_chunk("doc.md", 0)


@pytest.mark.anyio
async def test_payload_full_scans_constant_with_document_count():
    class FakeSearch:
        def __init__(self):
            self.scrolls = 0

        async def create_collection(self):
            return None

        async def get_all_payloads(self):
            self.scrolls += 1
            return []

        async def insert_points_batch(self, points):
            return None

        async def delete_points(self, ids):
            return None

    class FakeEmbedder:
        default_model = "voyage-context-4"
        output_dimension = 1024
        output_dtype = "float"

        async def embed_document(self, **kwargs):
            chunks = kwargs["chunks"]
            return SimpleNamespace(
                embeddings=[[0.1] * 1024 for _ in chunks],
                model="voyage-context-4",
                output_dimension=1024,
                output_dtype="float",
                chunk_tokens=[1] * len(chunks),
                cost_usd=0.0,
            )

    search = FakeSearch()
    pipeline = DocIndexingPipeline(
        embedder=FakeEmbedder(),
        doc_search=search,
        workspace_path=Path("/tmp/ws-scan"),
        workspace_id="scan",
    )
    # Bypass discovery with fake files by patching processor and discover.
    files = [Path(f"/tmp/ws-scan/doc{i}.md") for i in range(5)]

    def fake_process(file_path, **kwargs):
        chunk = MagicMock()
        chunk.text = "hello"
        chunk.metadata.chunk_index = 0
        chunk.metadata.document_type.value = "markdown"
        chunk.metadata.title = "t"
        chunk.metadata.char_count = 5
        chunk.metadata.token_count = 1
        chunk.metadata.source_hash = "s"
        chunk.metadata.content_hash = "c"
        chunk.metadata.section_hierarchy = []
        chunk.metadata.header_level = 1
        chunk.metadata.has_code_blocks = False
        chunk.metadata.complexity_estimate = 0
        chunk.metadata.parent_section = None
        chunk.metadata.section_type = None
        return [chunk]

    pipeline.processor.process_document = fake_process
    pipeline._discover_documents = lambda include_patterns=None: files
    pipeline._source_uri = lambda source: source.name
    pipeline._doc_id_for_source = lambda source: source.name
    pipeline._validate_chunk_ordinals = lambda chunks, source: None

    summary = await pipeline.index_workspace()
    assert search.scrolls == 1
    assert summary["payload_full_scans"] == 1


def test_oversized_context_cannot_produce_silent_zero_results():
    results = [
        {
            "code": "def x(): pass",
            "context": "C" * 50_000,
            "file_path": "a.py",
            "score": 0.9,
        },
        {
            "code": "def y(): pass",
            "context": "D" * 50_000,
            "file_path": "b.py",
            "score": 0.8,
        },
    ]
    out, info = truncate_code_results(results, budget_tokens=500, per_item_max_chars=200)
    assert len(out) >= 1
    assert info.final_count >= 1
    assert info.original_count == 2
    # Must not look like "no matches"
    assert out[0].get("file_path") == "a.py"


def test_degraded_guarantee_when_budget_tiny():
    results = [
        {
            "code": "x" * 10_000,
            "context": "y" * 10_000,
            "file_path": "big.py",
            "score": 1.0,
        }
    ]
    out, info = truncate_code_results(results, budget_tokens=250, per_item_max_chars=50)
    assert len(out) == 1
    assert info.degraded_guarantee_applied is True
    assert info.budget_starvation is True


@pytest.mark.anyio
async def test_reranker_degradation_visible():
    reranker = VoyageReranker(api_key="test-key")
    reranker.token_counter.count_each = AsyncMock(
        side_effect=[
            [TokenCount(RERANK_MAX_QUERY_TOKENS + 1, True)],  # query too large
        ]
    )
    results = [
        SearchResult(
            id="1",
            score=0.5,
            payload={},
            file_path="a.py",
            function_name="f",
            language="python",
            content="def f(): pass",
        )
    ]
    response = await reranker.rerank("q" * 100, results)
    assert response.degraded is True
    assert response.failure_reason
    assert "query exceeds" in response.failure_reason


@pytest.mark.anyio
async def test_reranker_api_failure_sets_degraded():
    reranker = VoyageReranker(api_key="test-key")
    reranker.token_counter.count_each = AsyncMock(
        side_effect=[
            [TokenCount(10, True)],
            [TokenCount(20, True)],
        ]
    )
    reranker._api_rerank = AsyncMock(side_effect=RuntimeError("boom"))
    results = [
        SearchResult(
            id="1",
            score=0.5,
            payload={},
            file_path="a.py",
            function_name="f",
            language="python",
            content="def f(): pass",
        )
    ]
    response = await reranker.rerank("query", results)
    assert response.degraded is True
    assert "boom" in (response.failure_reason or "")


def test_voyage_3_lite_request_limit():
    from src.embeddings.model_registry import get_model_spec

    spec = get_model_spec("voyage-3-lite")
    assert spec.max_request_tokens == 120_000


def test_sdk_version_range_in_repo_and_constraints():
    # tests/ -> dope-context -> services -> repo root
    root = Path(__file__).resolve().parents[3]
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    constraints = (
        root / "services" / "dope-context" / "constraints.txt"
    ).read_text(encoding="utf-8")
    assert "voyageai>=0.5.0,<0.6" in pyproject
    assert "voyageai>=0.5.0,<0.6" in constraints


def test_embedding_cache_returns_defensive_copy():
    embedder = VoyageEmbedder(api_key="test-key", cache_max_entries=2)
    from src.embeddings.voyage_embedder import EmbeddingResponse
    from datetime import datetime

    vec = [0.1, 0.2]
    resp = EmbeddingResponse(
        embedding=vec,
        model="voyage-code-3",
        tokens=1,
        token_count_exact=True,
    )
    key = "k"
    embedder._cache_response(key, resp)
    cached = embedder._get_cached(key)
    assert cached is not None
    cached.embedding[0] = 9.9
    cached2 = embedder._get_cached(key)
    assert cached2.embedding[0] == 0.1
