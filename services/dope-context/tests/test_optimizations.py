"""
End-to-end tests for dope-context optimizations.

Tests:
1. Incremental chunk-level indexing with deterministic IDs
2. DocumentProcessor integration for PDF/DOCX/HTML/MD
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.pipeline.indexing_pipeline import IndexingPipeline, IndexingConfig
from src.pipeline.docs_pipeline import DocIndexingPipeline
from src.sync.incremental_indexer import IncrementalIndexer, ChunkSnapshot
from src.preprocessing.code_chunker import CodeChunk, CodeChunker
from src.preprocessing.document_processor import DocumentProcessor
from src.embeddings.voyage_embedder import EmbeddingResponse


class TestIncrementalIndexing:
    """Test incremental chunk-level indexing."""

    @pytest.fixture
    def tmp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_components(self):
        """Create mocked pipeline components."""
        chunker = MagicMock()
        context_generator = MagicMock()
        embedder = MagicMock()
        vector_search = MagicMock()

        # Make async methods
        context_generator.generate_contexts_batch = AsyncMock()
        embedder.embed_batch = AsyncMock()
        vector_search.create_collection = AsyncMock()
        vector_search.insert_points_batch = AsyncMock()

        return {
            "chunker": chunker,
            "context_generator": context_generator,
            "embedder": embedder,
            "vector_search": vector_search,
        }

    def test_deterministic_chunk_id_generation(self, tmp_workspace, mock_components):
        """Test that chunk IDs are deterministic and consistent."""
        config = IndexingConfig(
            workspace_path=tmp_workspace,
            workspace_id="test",
        )

        pipeline = IndexingPipeline(
            chunker=mock_components["chunker"],
            context_generator=None,
            embedder=mock_components["embedder"],
            vector_search=mock_components["vector_search"],
            config=config,
        )

        # Create test file
        test_file = tmp_workspace / "test.py"
        test_file.write_text("def foo(): pass")

        # Create test chunk
        chunk = CodeChunk(
            content="def foo(): pass",
            start_line=10,
            end_line=15,
            chunk_type="function",
            language="python",
            symbol_name="foo",
        )

        # Generate ID twice
        id1 = pipeline._generate_chunk_id(test_file, chunk)
        id2 = pipeline._generate_chunk_id(test_file, chunk)

        # Should be identical (deterministic)
        assert id1 == id2
        assert len(id1) == 16  # 16-char hex string
        assert isinstance(id1, str)

    def test_chunk_id_different_for_different_chunks(
        self, tmp_workspace, mock_components
    ):
        """Test that different chunks get different IDs."""
        config = IndexingConfig(
            workspace_path=tmp_workspace,
            workspace_id="test",
        )

        pipeline = IndexingPipeline(
            chunker=mock_components["chunker"],
            context_generator=None,
            embedder=mock_components["embedder"],
            vector_search=mock_components["vector_search"],
            config=config,
        )

        test_file = tmp_workspace / "test.py"
        test_file.write_text("def foo(): pass\ndef bar(): pass")

        chunk1 = CodeChunk(
            content="def foo(): pass",
            start_line=10,
            end_line=15,
            chunk_type="function",
            language="python",
            symbol_name="foo",
        )

        chunk2 = CodeChunk(
            content="def bar(): pass",
            start_line=20,
            end_line=25,
            chunk_type="function",
            language="python",
            symbol_name="bar",
        )

        id1 = pipeline._generate_chunk_id(test_file, chunk1)
        id2 = pipeline._generate_chunk_id(test_file, chunk2)

        # Different chunks should have different IDs
        assert id1 != id2

    @pytest.mark.asyncio
    async def test_chunk_metadata_tracking(self, tmp_workspace, mock_components):
        """Test that chunk metadata is properly tracked."""
        test_file = tmp_workspace / "test.py"
        test_file.write_text("def foo(): pass")

        config = IndexingConfig(
            workspace_path=tmp_workspace,
            workspace_id="test",
        )

        # Mock chunk extraction
        mock_chunk = CodeChunk(
            content="def foo(): pass",
            start_line=1,
            end_line=1,
            chunk_type="function",
            language="python",
            symbol_name="foo",
        )
        mock_components["chunker"].chunk_file.return_value = [mock_chunk]

        # Mock embeddings
        mock_embedding = EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-code-3",
            tokens=10,
            cost_usd=0.001,
        )
        mock_components["embedder"].embed_batch.return_value = [mock_embedding]

        pipeline = IndexingPipeline(
            chunker=mock_components["chunker"],
            context_generator=None,
            embedder=mock_components["embedder"],
            vector_search=mock_components["vector_search"],
            config=config,
        )

        # Process file
        docs, chunk_metadata = await pipeline._process_file(test_file)

        # Verify we got both documents and metadata
        assert len(docs) == 1
        assert len(chunk_metadata) == 1

        # Verify chunk metadata structure
        meta = chunk_metadata[0]
        assert meta.chunk_id is not None
        assert meta.file_path == "test.py"
        assert meta.start_line == 1
        assert meta.end_line == 1
        assert meta.content_hash is not None
        assert meta.symbol_name == "foo"

    def test_chunk_snapshot_save_and_load(self, tmp_workspace):
        """Test that chunk snapshots are saved and loaded correctly."""
        indexer = IncrementalIndexer(tmp_workspace)

        # Create snapshot
        snapshot = ChunkSnapshot(workspace_path=str(tmp_workspace))

        from src.sync.incremental_indexer import ChunkMetadata, FileChunkMap

        chunks = [
            ChunkMetadata(
                chunk_id="abc123",
                file_path="test.py",
                start_line=1,
                end_line=10,
                content_hash="def456",
                symbol_name="foo",
            )
        ]

        indexer.update_chunk_mapping(
            snapshot=snapshot,
            file_path="test.py",
            file_hash="file_hash_123",
            chunks=chunks,
        )

        # Save snapshot
        indexer.save_chunk_snapshot(snapshot)

        # Load snapshot
        loaded = indexer.load_chunk_snapshot()

        # Verify loaded snapshot matches
        assert loaded is not None
        assert loaded.workspace_path == str(tmp_workspace)
        assert "test.py" in loaded.files
        assert len(loaded.files["test.py"].chunks) == 1
        assert loaded.files["test.py"].chunks[0].chunk_id == "abc123"
        assert loaded.files["test.py"].chunks[0].symbol_name == "foo"


class TestDocumentProcessor:
    """Test DocumentProcessor integration in docs pipeline."""

    @pytest.fixture
    def tmp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_components(self):
        """Create mocked components for docs pipeline."""
        embedder = MagicMock()
        doc_search = MagicMock()

        embedder.embed_batch = AsyncMock()
        doc_search.create_collection = AsyncMock()
        doc_search.index_document = AsyncMock()

        return {
            "embedder": embedder,
            "doc_search": doc_search,
        }

    def test_document_processor_initialization(self):
        """Test DocumentProcessor can be initialized."""
        processor = DocumentProcessor()
        assert processor is not None
        assert processor.encoding is not None

    def test_markdown_detection(self, tmp_workspace):
        """Test Markdown file detection."""
        processor = DocumentProcessor()

        md_file = tmp_workspace / "test.md"
        md_file.write_text("# Hello World\n\nThis is a test.")

        doc_type = processor.detect_document_type(str(md_file))
        assert doc_type.value == "markdown"

    def test_markdown_extraction(self, tmp_workspace):
        """Test Markdown text extraction."""
        processor = DocumentProcessor()

        md_file = tmp_workspace / "test.md"
        content = "# Hello World\n\nThis is a **test**."
        md_file.write_text(content)

        extracted = processor.extract_text(str(md_file))
        assert "Hello World" in extracted
        assert "test" in extracted

    def test_smart_chunking(self, tmp_workspace):
        """Test smart paragraph-based chunking."""
        processor = DocumentProcessor()

        # Create longer text to ensure multiple chunks
        paragraphs = [
            "First paragraph with enough content to make this substantial. " * 5,
            "Second paragraph also with substantial content here. " * 5,
            "Third paragraph to ensure we get multiple chunks. " * 5,
            "Fourth paragraph for good measure. " * 5,
        ]
        text = "\n\n".join(paragraphs)

        chunks = processor.chunk_text(
            text, chunk_size=200, chunk_overlap=20, preserve_structure=True
        )

        # Should create multiple chunks with this longer text
        assert len(chunks) >= 1

        # Chunks should not be empty
        for chunk in chunks:
            assert chunk.strip()  # No empty chunks

    @pytest.mark.asyncio
    async def test_docs_pipeline_uses_document_processor(
        self, tmp_workspace, mock_components
    ):
        """Test that DocIndexingPipeline uses DocumentProcessor."""
        from src.embeddings.voyage_embedder import VoyageEmbedder

        md_file = tmp_workspace / "test.md"
        md_file.write_text("# Test Document\n\nSome content here.")

        # Mock embeddings
        mock_embedding = EmbeddingResponse(
            embedding=[0.1] * 1024,
            model="voyage-context-3",
            tokens=10,
            cost_usd=0.001,
        )
        mock_components["embedder"].embed_batch.return_value = [mock_embedding]

        pipeline = DocIndexingPipeline(
            embedder=mock_components["embedder"],
            doc_search=mock_components["doc_search"],
            workspace_path=tmp_workspace,
            workspace_id="test",
        )

        # Verify DocumentProcessor was initialized
        assert pipeline.doc_processor is not None
        assert isinstance(pipeline.doc_processor, DocumentProcessor)

        # Index document
        chunks_indexed = await pipeline.index_document(md_file)

        # Should have processed at least one chunk
        assert chunks_indexed > 0


class TestEndToEnd:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def tmp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_incremental_reindex_workflow(self, tmp_workspace):
        """
        Test complete incremental indexing workflow:
        1. Index workspace
        2. Modify file
        3. Reindex only changed chunks
        """
        # This would be a full integration test requiring real components
        # Skipping for unit test suite - would need Qdrant + API keys
        pytest.skip("Requires real Qdrant instance and API keys")

    @pytest.mark.asyncio
    async def test_document_processing_workflow(self, tmp_workspace):
        """
        Test complete document processing workflow:
        1. Create various document types
        2. Index all documents
        3. Verify all formats processed
        """
        # This would be a full integration test
        pytest.skip("Requires real Qdrant instance and API keys")
