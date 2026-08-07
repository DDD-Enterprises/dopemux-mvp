"""Regression tests for TP-DOPECONTEXT-SERVICE-HARDENING-0006.

Closes F-006 (tokenizer retry storm), F-010/F-010b (SDK reconciliation and
the dead return_documents parameter), F-011 (invisible rerank failure),
F-012 (unbounded caches / aliased embeddings), F-014 (unenforced reranker
query limit), and F-015 (workspace_id determinism).

No test in this file makes a live Voyage API call or touches Qdrant.
"""

import asyncio
import inspect
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from voyageai import AsyncClient as RealAsyncClient

from src.embeddings.contextualized_embedder import (
    ContextualizedEmbedder,
    ContextualizedEmbeddingResponse,
)
from src.embeddings.voyage_embedder import EmbeddingResponse, VoyageEmbedder
from src.rerank.voyage_reranker import (
    RERANK_MAX_QUERY_TOKENS,
    RerankQueryTooLargeError,
    VoyageReranker,
)
from src.search.dense_search import SearchResult
from src.utils.model_tokenizer import TokenCount, VoyageTokenCounter


def _make_result(index: int, content: str = "print(1)") -> SearchResult:
    return SearchResult(
        id=f"id-{index}",
        score=1.0 - index * 0.01,
        payload={},
        file_path=f"file_{index}.py",
        function_name=None,
        language="python",
        content=content,
    )


# ---------------------------------------------------------------------------
# F-010b: return_documents does not exist on any voyageai SDK release.
# ---------------------------------------------------------------------------


def test_installed_sdk_rerank_signature_has_no_return_documents():
    """Ground truth check, independent of our own code: the installed
    AsyncClient.rerank must not accept return_documents. If a future SDK
    release adds it back, this test -- not just the request-shape test below
    -- will flag the drift."""
    params = set(inspect.signature(RealAsyncClient.rerank).parameters)
    assert "return_documents" not in params


def test_rerank_request_uses_only_installed_sdk_parameters():
    """F-010b: the previous _api_rerank always sent return_documents, which
    raised TypeError on every call and fell into a compatibility branch that
    also stripped truncation -- the real request path was dead code. The
    rerank request must only ever use parameters the installed SDK accepts,
    and truncation must reach the request."""
    allowed = set(inspect.signature(RealAsyncClient.rerank).parameters) - {"self"}

    async def _run():
        reranker = VoyageReranker(api_key="test-not-a-secret")
        captured = {}

        async def _fake_rerank(**kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                results=[SimpleNamespace(index=0, relevance_score=0.9)],
                total_tokens=10,
            )

        reranker.client.rerank = _fake_rerank

        async def _fake_count_each(texts, model):
            return [TokenCount(5, True) for _ in texts]

        reranker.token_counter.count_each = _fake_count_each

        response = await reranker.rerank("query", [_make_result(0)])
        assert response.degraded is False
        assert set(captured) <= allowed
        assert captured["truncation"] is True

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# F-011: rerank failure must be distinguishable from success.
# ---------------------------------------------------------------------------


def test_rerank_degraded_true_when_api_call_fails():
    async def _run():
        reranker = VoyageReranker(api_key="test-not-a-secret")

        async def _fake_count_each(texts, model):
            return [TokenCount(5, True) for _ in texts]

        reranker.token_counter.count_each = _fake_count_each

        async def _raising_rerank(**kwargs):
            raise RuntimeError("simulated Voyage outage")

        reranker.client.rerank = _raising_rerank

        response = await reranker.rerank("query", [_make_result(0), _make_result(1)])
        assert response.degraded is True
        assert response.tokens_used == 0
        assert response.cost_usd == 0.0
        assert [r.original_rank for r in response.top_results] == [0, 1]

    asyncio.run(_run())


def test_rerank_degraded_false_on_success():
    async def _run():
        reranker = VoyageReranker(api_key="test-not-a-secret")

        async def _fake_count_each(texts, model):
            return [TokenCount(5, True) for _ in texts]

        reranker.token_counter.count_each = _fake_count_each

        async def _fake_rerank(**kwargs):
            return SimpleNamespace(
                results=[SimpleNamespace(index=0, relevance_score=0.9)],
                total_tokens=10,
            )

        reranker.client.rerank = _fake_rerank

        response = await reranker.rerank("query", [_make_result(0)])
        assert response.degraded is False

    asyncio.run(_run())


def test_rerank_degraded_true_when_no_candidate_fits_budget():
    """The pre-existing "no candidates fit the token budget" path also goes
    through _fallback and must report degraded, not just the exception path."""

    async def _run():
        reranker = VoyageReranker(api_key="test-not-a-secret")

        async def _fake_count_each(texts, model):
            if texts == ["query"]:
                return [TokenCount(5, True) for _ in texts]
            # Every document "costs" more than the whole request budget.
            return [TokenCount(10_000_000, True) for _ in texts]

        reranker.token_counter.count_each = _fake_count_each

        response = await reranker.rerank("query", [_make_result(0)])
        assert response.degraded is True

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# F-014: the 8,000-token per-query rerank limit must be enforced and must
# fail loudly rather than falling into the F-011 fallback.
# ---------------------------------------------------------------------------


def test_oversized_query_raises_instead_of_silently_falling_back():
    async def _run():
        reranker = VoyageReranker(api_key="test-not-a-secret")

        async def _fake_count_each(texts, model):
            if texts and texts[0] == "oversized":
                return [TokenCount(RERANK_MAX_QUERY_TOKENS + 1, True) for _ in texts]
            return [TokenCount(5, True) for _ in texts]

        reranker.token_counter.count_each = _fake_count_each

        called = {"rerank": False}

        async def _fake_rerank(**kwargs):
            called["rerank"] = True
            return SimpleNamespace(results=[], total_tokens=0)

        reranker.client.rerank = _fake_rerank

        with pytest.raises(RerankQueryTooLargeError):
            await reranker.rerank("oversized", [_make_result(0)])

        assert called["rerank"] is False

    asyncio.run(_run())


def test_query_at_exactly_the_limit_is_allowed():
    async def _run():
        reranker = VoyageReranker(api_key="test-not-a-secret")

        async def _fake_count_each(texts, model):
            if texts and texts[0] == "at-limit":
                return [TokenCount(RERANK_MAX_QUERY_TOKENS, True) for _ in texts]
            return [TokenCount(5, True) for _ in texts]

        reranker.token_counter.count_each = _fake_count_each

        async def _fake_rerank(**kwargs):
            return SimpleNamespace(
                results=[SimpleNamespace(index=0, relevance_score=0.5)],
                total_tokens=5,
            )

        reranker.client.rerank = _fake_rerank

        response = await reranker.rerank("at-limit", [_make_result(0)])
        assert response.degraded is False

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# F-006: a broken tokenizer fetch must be attempted once per model, not once
# per unique chunk.
# ---------------------------------------------------------------------------


def test_tokenizer_failure_is_memoized_per_model_not_per_chunk():
    async def _run():
        counter = VoyageTokenCounter(api_key="test-not-a-secret")
        assert counter._client is not None

        attempts = {"count": 0}

        def _always_fails(texts, model):
            attempts["count"] += 1
            raise RuntimeError("simulated blocked huggingface.co fetch")

        counter._client.tokenize = _always_fails

        for index in range(5):
            counts = await counter.count_each(
                [f"unique chunk body {index}"], "rerank-2.5"
            )
            assert counts[0].exact is False
            assert counts[0].count > 0

        assert attempts["count"] == 1
        assert "rerank-2.5" in counter._unavailable_models

    asyncio.run(_run())


def test_tokenizer_failure_is_scoped_to_one_model():
    """A failure for one model must not poison a different model's attempts,
    since a per-model tokenizer file may fail or succeed independently."""

    async def _run():
        counter = VoyageTokenCounter(api_key="test-not-a-secret")
        attempts = {"rerank-2.5": 0, "rerank-2.5-lite": 0}

        def _fails_only_for_first_model(texts, model):
            attempts[model] += 1
            if model == "rerank-2.5":
                raise RuntimeError("blocked")
            return [SimpleNamespace(ids=[1, 2, 3]) for _ in texts]

        counter._client.tokenize = _fails_only_for_first_model

        await counter.count_each(["a"], "rerank-2.5")
        await counter.count_each(["b"], "rerank-2.5-lite")

        assert attempts == {"rerank-2.5": 1, "rerank-2.5-lite": 1}
        assert "rerank-2.5" in counter._unavailable_models
        assert "rerank-2.5-lite" not in counter._unavailable_models

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# F-012: bounded caches, copy-on-read.
# ---------------------------------------------------------------------------


def test_embedding_cache_is_bounded_and_evicts_oldest():
    async def _run():
        embedder = VoyageEmbedder(api_key="test-not-a-secret", max_cache_entries=2)

        def _resp():
            return EmbeddingResponse(embedding=[0.0], model="voyage-code-3", tokens=1)

        embedder._cache_response("key-a", _resp())
        embedder._cache_response("key-b", _resp())
        embedder._cache_response("key-c", _resp())

        assert len(embedder.cache) == 2
        assert "key-a" not in embedder.cache
        assert "key-b" in embedder.cache
        assert "key-c" in embedder.cache

    asyncio.run(_run())


def test_embedding_cache_returns_a_copy_not_the_stored_list():
    async def _run():
        embedder = VoyageEmbedder(api_key="test-not-a-secret")
        original = EmbeddingResponse(
            embedding=[1.0, 2.0, 3.0], model="voyage-code-3", tokens=3
        )
        embedder._cache_response("key", original)

        first = embedder._get_cached("key")
        first.embedding[0] = 999.0

        second = embedder._get_cached("key")
        assert second.embedding == [1.0, 2.0, 3.0]

    asyncio.run(_run())


def test_contextualized_cache_is_bounded_and_evicts_oldest():
    async def _run():
        embedder = ContextualizedEmbedder(
            api_key="test-not-a-secret", max_cache_entries=2
        )

        def _resp():
            return ContextualizedEmbeddingResponse(
                embeddings=[[0.0]], model="voyage-context-4", total_tokens=1
            )

        embedder._cache_response("key-a", _resp())
        embedder._cache_response("key-b", _resp())
        embedder._cache_response("key-c", _resp())

        assert len(embedder.cache) == 2
        assert "key-a" not in embedder.cache

    asyncio.run(_run())


def test_contextualized_cache_returns_copies_not_references():
    async def _run():
        embedder = ContextualizedEmbedder(api_key="test-not-a-secret")
        original = ContextualizedEmbeddingResponse(
            embeddings=[[1.0, 2.0]],
            model="voyage-context-4",
            total_tokens=2,
            chunk_tokens=[2],
            chunk_texts=["hello"],
        )
        embedder._cache_response("key", original)

        first = embedder._get_cached("key")
        first.embeddings[0][0] = 999.0
        first.chunk_tokens.append(999)
        first.chunk_texts.append("mutated")

        second = embedder._get_cached("key")
        assert second.embeddings == [[1.0, 2.0]]
        assert second.chunk_tokens == [2]
        assert second.chunk_texts == ["hello"]

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# F-015: workspace_id determinism.
#
# _initialize_components() is not reachable from any MCP tool -- every tool
# (_index_workspace_impl, _index_docs_impl, _search_code_impl,
# _docs_search_impl) builds its own workspace-scoped pipeline instead of
# using the module-level globals this function assigns. Exercising it
# end-to-end would mean reconstructing its entire dependency graph (Voyage
# clients, Qdrant clients, BM25 index, OpenAI context generator) purely to
# cover a code path nothing calls in production. This is a source-level
# regression guard instead: it asserts the fixed derivation is actually in
# the file and the old collision-prone default is gone.
# ---------------------------------------------------------------------------


def test_initialize_components_workspace_id_derived_from_resolved_path():
    server_path = (
        Path(__file__).resolve().parent.parent / "src" / "mcp" / "server.py"
    )
    source = server_path.read_text()
    match = re.search(
        r"def _initialize_components\(\):.*?(?=\n(?:async )?def )", source, re.S
    )
    assert match is not None, "_initialize_components not found in server.py"
    body = match.group(0)

    # Match the actual keyword-argument call, not the explanatory comment
    # above it (which necessarily quotes the old pattern by name).
    assert 'workspace_id=os.getenv("WORKSPACE_ID"' not in body
    assert body.count("workspace_id=str(workspace_root)") == 2
