"""Invariant tests for the modernized docs indexing pipeline."""

import asyncio
import os
import sys
import types
import uuid
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
        setattr(
            models_module,
            name,
            type(name, (), {"__init__": lambda self, *args, **kwargs: None}),
        )
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
    def __init__(self, existing_payloads=None):
        self.inserted_batches = []
        self.deleted_ids = []
        self.existing_payloads = list(existing_payloads or [])
        self.get_all_payloads_calls = 0

    async def create_collection(self):
        return None

    async def get_all_payloads(self):
        self.get_all_payloads_calls += 1
        return list(self.existing_payloads)

    async def delete_points(self, point_ids):
        self.deleted_ids.extend(point_ids)

    async def insert_points_batch(self, points):
        self.inserted_batches.append(points)
        return [point[4] for point in points]


class StubEmbedder:
    default_model = "voyage-context-4"
    output_dimension = 1024
    output_dtype = "float"

    def __init__(self, embedding_count: int):
        self.embedding_count = embedding_count

    async def embed_document(
        self,
        chunks,
        model,
        input_type,
        output_dimension,
        output_dtype,
    ):
        assert model == self.default_model
        assert input_type == "document"
        assert output_dimension == self.output_dimension
        assert output_dtype == self.output_dtype
        return SimpleNamespace(
            embeddings=[[0.1] * output_dimension for _ in range(self.embedding_count)],
            cost_usd=0.0,
            model=model,
            output_dimension=output_dimension,
            output_dtype=output_dtype,
            chunk_tokens=[index + 10 for index in range(self.embedding_count)],
        )


class StubProcessor:
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


def _workspace_doc(tmp_path: Path, name: str = "guide.md"):
    workspace = tmp_path / "workspace"
    docs_dir = workspace / "docs"
    docs_dir.mkdir(parents=True)
    file_path = docs_dir / name
    file_path.write_text("# Guide\n\nHello", encoding="utf-8")
    return workspace, file_path


def test_docs_pipeline_indexes_current_model_and_schema(tmp_path):
    async def _run():
        workspace, file_path = _workspace_doc(tmp_path)
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

        point = doc_search.inserted_batches[0][0]
        payload = point[3]
        point_id = point[4]
        uuid.UUID(point_id)
        assert payload["source_type"] == "doc"
        assert payload["embed_model"] == "voyage-context-4"
        assert payload["embed_dimension"] == 1024
        assert payload["embed_dtype"] == "float"
        assert payload["index_schema_version"] == "dope-context-v2"
        assert len(payload["index_fingerprint"]) == 64
        assert payload["doc_id"] == "docs/guide.md"
        assert payload["chunk_id"] == point_id
        assert payload["ordinal"] == 0
        assert payload["token_count"] == 10
        assert payload["instance_id"] == os.getenv(
            "DOPEMUX_WORKSPACE_ID", "ws-test"
        )

    asyncio.run(_run())


def test_docs_pipeline_embedding_mismatch_preserves_existing_index(tmp_path):
    async def _run():
        workspace, file_path = _workspace_doc(tmp_path, "mismatch.md")
        chunks = [
            _chunk(file_path, 0, "Chunk zero"),
            _chunk(file_path, 1, "Chunk one"),
        ]
        doc_search = StubDocSearch(
            existing_payloads=[
                {
                    "id": "existing",
                    "source_path": file_path.as_posix(),
                    "source_uri": "docs/mismatch.md",
                }
            ]
        )
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
        assert doc_search.deleted_ids == []

    asyncio.run(_run())


def test_docs_pipeline_non_contiguous_ordinals_skip_upsert(tmp_path):
    async def _run():
        workspace, file_path = _workspace_doc(tmp_path, "ordinals.md")
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
        assert doc_search.inserted_batches == []
        assert "Chunk ordinal mismatch" in summary["errors"][0]["error"]

    asyncio.run(_run())


def test_docs_pipeline_deletes_only_stale_exact_source_ids(tmp_path):
    async def _run():
        workspace, file_path = _workspace_doc(tmp_path)
        chunks = [_chunk(file_path, 0, "Chunk zero")]
        doc_search = StubDocSearch(
            existing_payloads=[
                {
                    "id": "stale-guide",
                    "source_path": file_path.as_posix(),
                    "source_uri": "docs/guide.md",
                },
                {
                    "id": "other-guide",
                    "source_path": (workspace / "other" / "guide.md").as_posix(),
                    "source_uri": "other/guide.md",
                },
            ]
        )
        pipeline = DocIndexingPipeline(
            embedder=StubEmbedder(embedding_count=1),
            doc_search=doc_search,
            workspace_path=workspace,
            workspace_id="ws-test",
        )
        pipeline.processor = StubProcessor(chunks)

        summary = await pipeline.index_workspace(include_patterns=["*.md"])
        assert summary["documents_indexed"] == 1
        assert summary["chunks_replaced"] == 1
        assert doc_search.deleted_ids == ["stale-guide"]

    asyncio.run(_run())


def test_docs_pipeline_reconciles_legacy_file_path_and_doc_id_only_payloads(
    tmp_path,
):
    """F-004b: legacy points carrying only file_path, or only doc_id, must
    still be found and reconciled as stale -- not just source_path/source_uri.
    """

    async def _run():
        workspace, file_path = _workspace_doc(tmp_path)
        chunks = [_chunk(file_path, 0, "Chunk zero")]
        doc_search = StubDocSearch(
            existing_payloads=[
                {
                    "id": "legacy-file-path-only",
                    "file_path": file_path.as_posix(),
                },
                {
                    "id": "legacy-doc-id-only",
                    "doc_id": "docs/guide.md",
                },
            ]
        )
        pipeline = DocIndexingPipeline(
            embedder=StubEmbedder(embedding_count=1),
            doc_search=doc_search,
            workspace_path=workspace,
            workspace_id="ws-test",
        )
        pipeline.processor = StubProcessor(chunks)

        summary = await pipeline.index_workspace(include_patterns=["*.md"])
        assert summary["documents_indexed"] == 1
        assert summary["chunks_replaced"] == 2
        assert sorted(doc_search.deleted_ids) == [
            "legacy-doc-id-only",
            "legacy-file-path-only",
        ]

    asyncio.run(_run())


def test_docs_pipeline_scans_payloads_once_per_workspace_run(tmp_path):
    """F-007: index_workspace must perform exactly one get_all_payloads scan
    for the whole run, not one per document."""

    async def _run():
        workspace = tmp_path / "workspace"
        docs_dir = workspace / "docs"
        docs_dir.mkdir(parents=True)
        file_a = docs_dir / "a.md"
        file_b = docs_dir / "b.md"
        file_a.write_text("# A", encoding="utf-8")
        file_b.write_text("# B", encoding="utf-8")

        doc_search = StubDocSearch()
        pipeline = DocIndexingPipeline(
            embedder=StubEmbedder(embedding_count=1),
            doc_search=doc_search,
            workspace_path=workspace,
            workspace_id="ws-test",
        )
        pipeline.processor = StubProcessor([_chunk(file_a, 0, "Chunk A")])

        summary = await pipeline.index_workspace(include_patterns=["*.md"])
        assert summary["documents_discovered"] == 2
        assert summary["documents_indexed"] == 2
        assert doc_search.get_all_payloads_calls == 1

    asyncio.run(_run())


def test_point_ids_are_deterministic(tmp_path):
    workspace, _file_path = _workspace_doc(tmp_path)
    pipeline = DocIndexingPipeline(
        embedder=StubEmbedder(embedding_count=1),
        doc_search=StubDocSearch(),
        workspace_path=workspace,
        workspace_id="ws-test",
    )
    first = pipeline._point_id_for_chunk("docs/guide.md", 0)
    second = pipeline._point_id_for_chunk("docs/guide.md", 0)
    different = pipeline._point_id_for_chunk("docs/guide.md", 1)
    assert first == second
    assert first != different
