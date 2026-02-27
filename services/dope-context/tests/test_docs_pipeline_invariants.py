"""Invariant tests for docs indexing pipeline."""

import asyncio
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace


def _register_qdrant_stub():
    models_module = types.ModuleType("qdrant_client.http.models")
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
    qdrant_module.AsyncQdrantClient = type(
        "AsyncQdrantClient",
        (),
        {"__init__": lambda self, *args, **kwargs: None},
    )

    http_module = types.ModuleType("qdrant_client.http")
    http_module.models = models_module

    sys.modules.setdefault("qdrant_client", qdrant_module)
    sys.modules.setdefault("qdrant_client.http", http_module)
    sys.modules.setdefault("qdrant_client.http.models", models_module)


_register_qdrant_stub()

from src.pipeline.docs_pipeline import DocIndexingPipeline
from src.preprocessing.models import ChunkMetadata, DocumentChunk, DocumentType


class StubDocSearch:
    """Minimal doc search stub for pipeline tests."""

    def __init__(self):
        self.inserted_batches = []

    async def create_collection(self):
        return None

    async def get_all_payloads(self):
        return []

    async def delete_points(self, _point_ids):
        return None

    async def insert_points_batch(self, points):
        self.inserted_batches.append(points)
        return []


class StubEmbedder:
    """Embedder stub returning configured vectors."""

    def __init__(self, embedding_count: int):
        self.embedding_count = embedding_count

    async def embed_document(self, chunks, model, input_type, output_dimension):
        assert model == "voyage-context-3"
        assert input_type == "document"
        assert output_dimension == 1024
        return SimpleNamespace(
            embeddings=[[0.1] * 8 for _ in range(self.embedding_count)],
            cost_usd=0.0,
        )


class StubProcessor:
    """Document processor stub returning predetermined chunks."""

    def __init__(self, chunks):
        self._chunks = chunks

    def process_document(
        self,
        file_path: str,
        chunk_size: int,
        chunk_overlap: int,
        use_structure_aware: bool,
    ):
        assert isinstance(file_path, str)
        assert chunk_size > 0
        assert chunk_overlap >= 0
        assert use_structure_aware is True
        return list(self._chunks)


def _chunk(file_path: Path, index: int, text: str) -> DocumentChunk:
    metadata = ChunkMetadata(
        source_path=str(file_path),
        source_hash="source-hash",
        chunk_index=index,
        char_count=len(text),
        token_count=max(1, len(text) // 4),
        content_hash=f"hash-{index}",
        document_type=DocumentType.MARKDOWN,
        title=file_path.stem,
    )
    return DocumentChunk(text=text, metadata=metadata)


def test_docs_pipeline_indexes_with_required_metadata(tmp_path):
    async def _run():
        workspace = tmp_path / "workspace"
        docs_dir = workspace / "docs"
        docs_dir.mkdir(parents=True)
        file_path = docs_dir / "guide.md"
        file_path.write_text("# Guide\n\nHello", encoding="utf-8")

        chunks = [
            _chunk(file_path, 0, "Chunk zero"),
            _chunk(file_path, 1, "Chunk one"),
        ]
        doc_search = StubDocSearch()
        pipeline = DocIndexingPipeline(
            embedder=StubEmbedder(embedding_count=2),
            doc_search=doc_search,
            workspace_path=workspace,
            workspace_id="ws-test",
        )
        pipeline.processor = StubProcessor(chunks)

        summary = await pipeline.index_workspace(include_patterns=["*.md"])
        assert summary["documents_indexed"] == 1
        assert summary["documents_failed"] == 0
        assert len(doc_search.inserted_batches) == 1
        assert len(doc_search.inserted_batches[0]) == 2

        payload = doc_search.inserted_batches[0][0][3]
        assert payload["source_type"] == "doc"
        assert payload["embed_model"] == "voyage-context-3"
        assert payload["doc_id"] == "docs/guide.md"
        assert payload["chunk_id"] == "docs/guide.md::chunk::0"
        assert payload["ordinal"] == 0
        assert payload["instance_id"] == os.getenv("DOPEMUX_WORKSPACE_ID", "ws-test")

    asyncio.run(_run())


def test_docs_pipeline_embedding_mismatch_skips_upsert(tmp_path):
    async def _run():
        workspace = tmp_path / "workspace"
        docs_dir = workspace / "docs"
        docs_dir.mkdir(parents=True)
        file_path = docs_dir / "mismatch.md"
        file_path.write_text("# Mismatch\n\nHello", encoding="utf-8")

        chunks = [
            _chunk(file_path, 0, "Chunk zero"),
            _chunk(file_path, 1, "Chunk one"),
        ]
        doc_search = StubDocSearch()
        pipeline = DocIndexingPipeline(
            embedder=StubEmbedder(embedding_count=1),
            doc_search=doc_search,
            workspace_path=workspace,
            workspace_id="ws-test",
        )
        pipeline.processor = StubProcessor(chunks)

        summary = await pipeline.index_workspace(include_patterns=["*.md"])
        assert summary["documents_indexed"] == 0
        assert summary["documents_failed"] == 1
        assert summary["chunks_indexed"] == 0
        assert doc_search.inserted_batches == []

    asyncio.run(_run())


def test_docs_pipeline_non_contiguous_ordinals_skip_upsert(tmp_path):
    async def _run():
        workspace = tmp_path / "workspace"
        docs_dir = workspace / "docs"
        docs_dir.mkdir(parents=True)
        file_path = docs_dir / "ordinals.md"
        file_path.write_text("# Ordinals\n\nHello", encoding="utf-8")

        chunks = [
            _chunk(file_path, 0, "Chunk zero"),
            _chunk(file_path, 2, "Chunk two"),
        ]
        doc_search = StubDocSearch()
        pipeline = DocIndexingPipeline(
            embedder=StubEmbedder(embedding_count=2),
            doc_search=doc_search,
            workspace_path=workspace,
            workspace_id="ws-test",
        )
        pipeline.processor = StubProcessor(chunks)

        summary = await pipeline.index_workspace(include_patterns=["*.md"])
        assert summary["documents_indexed"] == 0
        assert summary["documents_failed"] == 1
        assert summary["chunks_indexed"] == 0
        assert doc_search.inserted_batches == []
        assert "Chunk ordinal mismatch" in summary["errors"][0]["error"]

    asyncio.run(_run())
