"""Round-6 regression guard: the flat content_vec path must actually work.

D1 moved code ``content_vec`` onto the flat ``embeddings`` endpoint. Two
BLOCKER defects shipped in that change and survived five audit rounds and a
green suite, because every existing test mocks the embedders and none drives
``IndexingPipeline._process_file``:

1. ``content_response`` was only bound in the contextualized branch but read
   unconditionally when summing embedding cost -> ``UnboundLocalError``.
2. ``embed_batch`` returns ``List[EmbeddingResponse]``, not
   ``List[List[float]]``, so ``content_vector`` was handed an object instead
   of a float list.

Both were silent: ``_process_file`` catches every exception, increments
``progress.errors`` and returns ``([], [])``, so a totally broken code index
looks like "no documents" rather than a crash. This test therefore asserts on
returned documents, not on absence of an exception.
"""

from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path

import pytest


def _stub_qdrant() -> None:
    if "qdrant_client" in sys.modules:
        return
    m = types.ModuleType("qdrant_client.http.models")
    for name in ("HnswConfigDiff", "VectorParams", "PointStruct", "NamedVector"):
        setattr(m, name, type(name, (), {"__init__": lambda self, *a, **k: None}))
    m.PayloadSchemaType = types.SimpleNamespace(KEYWORD="keyword")
    m.Distance = types.SimpleNamespace(DOT="dot")
    q = types.ModuleType("qdrant_client")
    q.AsyncQdrantClient = type("AsyncQdrantClient", (), {"__init__": lambda s, *a, **k: None})
    h = types.ModuleType("qdrant_client.http")
    h.models = m
    for key, mod in (("qdrant_client", q), ("qdrant_client.http", h),
                     ("qdrant_client.http.models", m)):
        sys.modules.setdefault(key, mod)


_stub_qdrant()

from src.embeddings.voyage_embedder import EmbeddingResponse  # noqa: E402
from src.pipeline.indexing_pipeline import IndexingConfig, IndexingPipeline  # noqa: E402


class _Chunk:
    def __init__(self, i: int) -> None:
        self.content = f"def f{i}():\n    return {i}\n"
        self.symbol_name = f"f{i}"
        self.chunk_type = "function"
        self.start_line = i * 10
        self.end_line = i * 10 + 3
        self.language = "python"
        self.complexity = 1


class _Chunker:
    chunker_version = "test"

    def chunk_file(self, file_path):  # noqa: ARG002
        return [_Chunk(0), _Chunk(1)]


class _StandardEmbedder:
    """Mirrors the real VoyageEmbedder contract: returns EmbeddingResponse."""

    def __init__(self) -> None:
        self.calls = []

    async def embed_batch(self, texts, model, input_type, output_dimension,
                          output_dtype, truncation=True):
        self.calls.append({"model": model, "truncation": truncation,
                           "n": len(texts)})
        return [
            EmbeddingResponse(embedding=[0.5] * output_dimension, model=model,
                              tokens=7, cost_usd=0.001)
            for _ in texts
        ]


class _ContextualizedEmbedder:
    default_model = "voyage-context-4"
    output_dimension = 1024
    output_dtype = "float"

    async def embed_document(self, **kwargs):  # pragma: no cover - must not run
        raise AssertionError(
            "flat content_vec must not call the contextualized embedder"
        )


class _VectorSearch:
    def __init__(self) -> None:
        self.manifest = None


def _pipeline(tmp_path: Path) -> IndexingPipeline:
    return IndexingPipeline(
        chunker=_Chunker(),
        context_generator=None,
        standard_embedder=_StandardEmbedder(),
        contextualized_embedder=_ContextualizedEmbedder(),
        vector_search=_VectorSearch(),
        config=IndexingConfig(workspace_path=tmp_path, workspace_id="ws"),
    )


def test_flat_content_path_produces_usable_documents(tmp_path):
    """The whole point: real documents, with real float vectors, no swallow."""
    target = tmp_path / "mod.py"
    target.write_text("x = 1\n", encoding="utf-8")
    pipeline = _pipeline(tmp_path)

    documents, metadata = asyncio.run(pipeline._process_file(target))

    # _process_file swallows exceptions and returns ([], []). An empty result
    # is therefore the failure signature, not a benign "nothing to index".
    assert documents, (
        "no documents produced; _process_file swallowed an exception "
        f"(progress.errors={pipeline.progress.errors})"
    )
    assert pipeline.progress.errors == 0
    assert len(documents) == 2

    for doc in documents:
        vector = doc["content_vector"]
        assert isinstance(vector, list), (
            f"content_vector must be List[float], got {type(vector).__name__}; "
            "embed_batch returns EmbeddingResponse objects that need unwrapping"
        )
        assert vector and all(isinstance(v, float) for v in vector)
        assert isinstance(doc["title_vector"], list)
        assert isinstance(doc["breadcrumb_vector"], list)

    assert pipeline.progress.embedding_cost_usd > 0, (
        "embedding cost was not accumulated for the flat content path"
    )


def test_flat_content_embeds_opt_out_of_truncation(tmp_path):
    """Round-5 finding, asserted behaviourally rather than by source scan."""
    target = tmp_path / "mod.py"
    target.write_text("x = 1\n", encoding="utf-8")
    pipeline = _pipeline(tmp_path)

    asyncio.run(pipeline._process_file(target))

    assert pipeline.standard_embedder.calls, "no embed_batch calls recorded"
    for call in pipeline.standard_embedder.calls:
        assert call["truncation"] is False, (
            "flat embeds must pass truncation=False; the library default is "
            "True, which silently truncates oversize input"
        )
