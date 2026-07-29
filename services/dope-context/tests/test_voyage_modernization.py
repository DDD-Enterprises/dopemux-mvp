"""Focused tests for Voyage model, token, cache, and cost modernization."""

import asyncio

import pytest

from src.embeddings.contextualized_embedder import ContextualizedEmbedder
from src.embeddings.model_registry import (
    get_model_spec,
    index_fingerprint,
    resolve_context_model,
    validate_dimension,
)
from src.embeddings.voyage_embedder import EmbeddingRequest, VoyageEmbedder
from src.rerank.voyage_reranker import CostTracker as RerankCostTracker
from src.utils.model_tokenizer import (
    TokenCount,
    allocate_total_tokens,
    conservative_token_estimate,
    partition_indices,
)
from src.utils.token_budget import (
    SAFE_TOKEN_BUDGET,
    estimate_tokens,
    truncate_code_results,
    truncate_text_to_tokens,
)


def test_current_voyage_models_and_prices():
    context = get_model_spec("voyage-context-4", endpoint="contextualized_embeddings")
    code = get_model_spec("voyage-code-3", endpoint="embeddings")
    assert context.price_per_million_tokens == 0.12
    assert code.price_per_million_tokens == 0.18
    assert context.default_dimension == 1024
    assert code.max_request_tokens == 120_000


def test_legacy_context3_migrates_unless_explicitly_allowed(monkeypatch):
    """Legacy hard-coded context-3 selects configured default unless allowed."""
    monkeypatch.delenv("DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3", raising=False)
    assert (
        resolve_context_model("voyage-context-3", "voyage-context-4")
        == "voyage-context-4"
    )
    assert resolve_context_model(None, "voyage-context-4") == "voyage-context-4"
    monkeypatch.setenv("DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3", "1")
    assert (
        resolve_context_model("voyage-context-3", "voyage-context-4")
        == "voyage-context-3"
    )


def test_embedding_cache_key_includes_vector_shape():
    base = EmbeddingRequest(
        text="same",
        model="voyage-code-3",
        input_type="document",
        output_dimension=1024,
        output_dtype="float",
    )
    smaller = EmbeddingRequest(
        text="same",
        model="voyage-code-3",
        input_type="document",
        output_dimension=256,
        output_dtype="float",
    )
    quantized = EmbeddingRequest(
        text="same",
        model="voyage-code-3",
        input_type="document",
        output_dimension=1024,
        output_dtype="int8",
    )
    assert len({base.cache_key(), smaller.cache_key(), quantized.cache_key()}) == 3


def test_contextualized_cache_key_includes_vector_shape():
    kwargs = {
        "document_chunks": ["same"],
        "model": "voyage-context-4",
        "input_type": "document",
        "output_dtype": "float",
        "enable_auto_chunking": False,
        "chunk_size": 512,
        "chunk_overlap": 0,
    }
    first = ContextualizedEmbedder._cache_key(output_dimension=1024, **kwargs)
    second = ContextualizedEmbedder._cache_key(output_dimension=256, **kwargs)
    assert first != second


def test_dimension_validation_is_fail_closed():
    assert validate_dimension("voyage-4", 512) == 512
    try:
        validate_dimension("voyage-4", 768)
    except ValueError as exc:
        assert "does not support" in str(exc)
    else:
        raise AssertionError("unsupported dimensions must fail closed")


def test_token_partitions_preserve_order_and_limits():
    batches = partition_indices(
        [40, 40, 30, 80],
        max_inputs=2,
        max_tokens=100,
    )
    assert batches == [[0, 1], [2], [3]]


def test_actual_token_allocation_preserves_total():
    allocated = allocate_total_tokens([10, 20, 30], 101)
    assert sum(allocated) == 101
    assert allocated[0] < allocated[1] < allocated[2]


def test_conservative_estimators_handle_short_and_unicode_text():
    assert conservative_token_estimate("x") >= 1
    assert estimate_tokens("x") >= 1
    text = "λ" * 1000
    truncated, changed = truncate_text_to_tokens(text, max_tokens=20)
    assert changed is True
    assert estimate_tokens(truncated) <= 20

    tiny, changed = truncate_text_to_tokens("abcdef", max_tokens=1)
    assert changed is True
    assert estimate_tokens(tiny) <= 1


def test_reranker_cost_is_token_based_not_request_based():
    tracker = RerankCostTracker()
    cost = tracker.add_request("rerank-2.5", num_documents=100, tokens=50_000)
    assert cost == pytest.approx(0.0025)
    assert tracker.total_tokens == 50_000


def test_index_and_query_resolve_same_contextualized_model(monkeypatch):
    """F-003: DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3=1 alone must not split the
    docs index model from the docs query model. Both call sites resolve the
    model via ``ContextualizedEmbedder.default_model`` (mirroring
    ``DocIndexingPipeline._index_document`` and the fixed ``_docs_search_impl``
    in server.py), so they can never diverge regardless of the legacy flag.
    """
    monkeypatch.delenv("DOPE_CONTEXT_DOC_EMBED_MODEL", raising=False)
    monkeypatch.setenv("DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3", "1")

    index_embedder = ContextualizedEmbedder(api_key="test-not-a-secret")
    query_embedder = ContextualizedEmbedder(api_key="test-not-a-secret")

    index_model = index_embedder._resolve_model(index_embedder.default_model)
    query_model = query_embedder._resolve_model(query_embedder.default_model)
    assert index_model == query_model == "voyage-context-4"

    # The only working rollback is the documented configured-model variable,
    # which moves both index and query together.
    monkeypatch.setenv("DOPE_CONTEXT_DOC_EMBED_MODEL", "voyage-context-3")
    rollback_index_embedder = ContextualizedEmbedder(api_key="test-not-a-secret")
    rollback_query_embedder = ContextualizedEmbedder(api_key="test-not-a-secret")
    rollback_index_model = rollback_index_embedder._resolve_model(
        rollback_index_embedder.default_model
    )
    rollback_query_model = rollback_query_embedder._resolve_model(
        rollback_query_embedder.default_model
    )
    assert rollback_index_model == rollback_query_model == "voyage-context-3"


def test_embed_never_reports_estimate_as_exact(monkeypatch):
    """F-004a: embed() must not hard-code token_count_exact=True. It is exact
    only when the tokenizer counted precisely or the API returned a real
    total_tokens -- never when both are estimates."""

    async def _run():
        embedder = VoyageEmbedder(api_key="test-not-a-secret")

        async def _fake_count_each(texts, model):
            return [TokenCount(count=5, exact=False) for _ in texts]

        monkeypatch.setattr(embedder.token_counter, "count_each", _fake_count_each)

        class _FakeResultNoTotal:
            embeddings = [[0.1, 0.2]]

        async def _fake_embed(**kwargs):
            return _FakeResultNoTotal()

        monkeypatch.setattr(embedder.client, "embed", _fake_embed)

        response = await embedder.embed("hello world", model="voyage-code-3")
        assert response.token_count_exact is False

    asyncio.run(_run())


def test_embed_trusts_a_real_api_reported_total(monkeypatch):
    """F-004a: embed() must report exactness when the API actually returned
    total_tokens, even though the local tokenizer estimate was inexact."""

    async def _run():
        embedder = VoyageEmbedder(api_key="test-not-a-secret")

        async def _fake_count_each(texts, model):
            return [TokenCount(count=5, exact=False) for _ in texts]

        monkeypatch.setattr(embedder.token_counter, "count_each", _fake_count_each)

        class _FakeResultWithTotal:
            embeddings = [[0.1, 0.2]]
            total_tokens = 7

        async def _fake_embed(**kwargs):
            return _FakeResultWithTotal()

        monkeypatch.setattr(embedder.client, "embed", _fake_embed)

        response = await embedder.embed("hello world", model="voyage-code-3")
        assert response.token_count_exact is True
        assert response.tokens == 7

    asyncio.run(_run())


def test_embed_batch_follows_the_same_exactness_rule_as_embed(monkeypatch):
    """F-004a: embed_batch() previously erred the other way, reporting
    inexact even when the API gave a real batch total. Both methods must
    follow one rule."""

    async def _run():
        async def _fake_count_each(texts, model):
            return [TokenCount(count=5, exact=False) for _ in texts]

        with_total_embedder = VoyageEmbedder(api_key="test-not-a-secret")
        monkeypatch.setattr(
            with_total_embedder.token_counter, "count_each", _fake_count_each
        )

        class _FakeBatchResultWithTotal:
            embeddings = [[0.1, 0.2], [0.3, 0.4]]
            total_tokens = 20

        async def _fake_embed_with_total(**kwargs):
            return _FakeBatchResultWithTotal()

        monkeypatch.setattr(
            with_total_embedder.client, "embed", _fake_embed_with_total
        )
        responses = await with_total_embedder.embed_batch(
            ["alpha", "beta"], model="voyage-code-3"
        )
        assert len(responses) == 2
        assert all(response.token_count_exact for response in responses)

        no_total_embedder = VoyageEmbedder(api_key="test-not-a-secret")
        monkeypatch.setattr(
            no_total_embedder.token_counter, "count_each", _fake_count_each
        )

        class _FakeBatchResultNoTotal:
            embeddings = [[0.1, 0.2], [0.3, 0.4]]

        async def _fake_embed_no_total(**kwargs):
            return _FakeBatchResultNoTotal()

        monkeypatch.setattr(no_total_embedder.client, "embed", _fake_embed_no_total)
        responses_no_total = await no_total_embedder.embed_batch(
            ["gamma", "delta"], model="voyage-code-3"
        )
        assert all(
            not response.token_count_exact for response in responses_no_total
        )

    asyncio.run(_run())


def test_voyage_3_lite_request_ceiling_matches_120k_vendor_group():
    """F-013: voyage-3-lite is in vendor's 120K request-token group; only
    voyage-4-lite and voyage-3.5-lite carry the 1M ceiling."""
    spec = get_model_spec("voyage-3-lite", endpoint="embeddings")
    assert spec.max_request_tokens == 120_000


def test_truncate_code_results_caps_oversized_context_sibling():
    """F-017: search_code payloads carry an unbounded 'context' sibling next
    to the already-trimmed 'code' field. Before the fix, one huge context
    value made estimate_dict_tokens measure the whole item as over budget and
    the result was silently dropped."""
    huge_context = "x" * 200_000
    results = [
        {"file_path": "a.py", "code": "print('hi')", "context": huge_context}
    ]
    truncated, info = truncate_code_results(results, budget_tokens=SAFE_TOKEN_BUDGET)
    assert len(truncated) == 1
    assert truncated[0]["file_path"] == "a.py"
    assert len(truncated[0]["context"]) < len(huge_context)


def test_truncate_code_results_never_empty_for_non_empty_input():
    """F-017: non-empty input must never come back as zero results -- an
    empty list is indistinguishable from 'no matches'. This must hold even
    under a budget so tight the normal per-item cap cannot fit."""
    results = [
        {
            "file_path": f"f{index}.py",
            "code": "y" * 5000,
            "context": "z" * 500_000,
        }
        for index in range(3)
    ]
    truncated, info = truncate_code_results(results, budget_tokens=250)
    assert len(truncated) >= 1
    assert info.final_count >= 1
    assert truncated[0]["file_path"] == "f0.py"


def test_index_fingerprint_changes_with_model_or_chunker():
    first = index_fingerprint(
        model="voyage-context-4",
        output_dimension=1024,
        output_dtype="float",
        chunker_version="v1",
    )
    second = index_fingerprint(
        model="voyage-context-4",
        output_dimension=1024,
        output_dtype="float",
        chunker_version="v2",
    )
    third = index_fingerprint(
        model="voyage-4",
        output_dimension=1024,
        output_dtype="float",
        chunker_version="v1",
    )
    assert len({first, second, third}) == 3
