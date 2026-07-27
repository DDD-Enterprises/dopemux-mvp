"""Focused tests for Voyage model, token, cache, and cost modernization."""

import pytest

from src.embeddings.contextualized_embedder import ContextualizedEmbedder
from src.embeddings.model_registry import (
    get_model_spec,
    index_fingerprint,
    resolve_context_model,
    validate_dimension,
)
from src.embeddings.voyage_embedder import EmbeddingRequest
from src.rerank.voyage_reranker import CostTracker as RerankCostTracker
from src.utils.model_tokenizer import (
    allocate_total_tokens,
    conservative_token_estimate,
    partition_indices,
)
from src.utils.token_budget import estimate_tokens, truncate_text_to_tokens


def test_current_voyage_models_and_prices():
    context = get_model_spec("voyage-context-4", endpoint="contextualized_embeddings")
    code = get_model_spec("voyage-code-3", endpoint="embeddings")
    assert context.price_per_million_tokens == 0.12
    assert code.price_per_million_tokens == 0.18
    assert context.default_dimension == 1024
    assert code.max_request_tokens == 120_000


def test_explicit_context_model_is_never_silently_rewritten(monkeypatch):
    """F-003/invariant: explicit requests are not rewritten into another model."""
    monkeypatch.delenv("DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3", raising=False)
    assert (
        resolve_context_model("voyage-context-3", "voyage-context-4")
        == "voyage-context-3"
    )
    assert resolve_context_model(None, "voyage-context-4") == "voyage-context-4"
    monkeypatch.setenv("DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3", "1")
    # Admission guard is a no-op for selection.
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
