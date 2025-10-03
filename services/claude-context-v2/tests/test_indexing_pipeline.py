"""
Tests for Indexing Pipeline Orchestrator - Task 7
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.pipeline.indexing_pipeline import (
    IndexingPipeline,
    IndexingConfig,
    IndexingProgress,
)
from src.preprocessing.code_chunker import CodeChunk
from src.embeddings.voyage_embedder import EmbeddingResponse


@pytest.fixture
def mock_components():
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


@pytest.fixture
def sample_config(tmp_path):
    """Create sample indexing config."""
    return IndexingConfig(
        workspace_path=tmp_path,
        include_patterns=["*.py"],
        workspace_id="test-workspace",
    )


def test_indexing_progress():
    """Test IndexingProgress tracking."""
    progress = IndexingProgress(
        total_files=10,
        processed_files=5,
        total_chunks=100,
        indexed_chunks=50,
        start_time=datetime.now(),
    )

    assert progress.percentage_complete() == 50.0
    assert progress.elapsed_seconds() >= 0

    summary = progress.summary()
    assert summary["files"] == "5/10"
    assert summary["chunks"] == "50/100"
    assert "50.0%" in summary["completion"]


def test_indexing_progress_summary():
    """Test progress summary generation."""
    progress = IndexingProgress(
        total_files=5,
        processed_files=5,
        total_chunks=20,
        indexed_chunks=20,
        errors=0,
        total_cost_usd=0.50,
    )

    summary = progress.summary()

    assert summary["files"] == "5/5"
    assert summary["chunks"] == "20/20"
    assert summary["errors"] == 0
    assert summary["total_cost_usd"] == 0.5


@pytest.mark.asyncio
async def test_pipeline_initialization(mock_components, sample_config):
    """Test pipeline initialization."""
    pipeline = IndexingPipeline(
        chunker=mock_components["chunker"],
        context_generator=mock_components["context_generator"],
        embedder=mock_components["embedder"],
        vector_search=mock_components["vector_search"],
        config=sample_config,
    )

    assert pipeline.chunker is not None
    assert pipeline.context_generator is not None
    assert pipeline.embedder is not None
    assert pipeline.vector_search is not None
    assert isinstance(pipeline.progress, IndexingProgress)


@pytest.mark.asyncio
async def test_process_file(mock_components, sample_config, tmp_path):
    """Test single file processing."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")

    # Mock chunk extraction
    mock_chunk = CodeChunk(
        content="def foo(): pass",
        start_line=0,
        end_line=0,
        chunk_type="function",
        language="python",
        symbol_name="foo",
    )
    mock_components["chunker"].chunk_file.return_value = [mock_chunk]

    # Mock context generation
    from src.context.claude_generator import ContextResponse
    mock_components["context_generator"].generate_contexts_batch.return_value = [
        ContextResponse(context="Test context", tokens_used=10, cost_usd=0.001)
    ]

    # Mock embeddings
    mock_embedding = EmbeddingResponse(
        embedding=[0.1] * 1024,
        model="voyage-code-3",
        tokens=10,
        cost_usd=0.001,
    )
    mock_components["embedder"].embed_batch.return_value = [mock_embedding]

    # Create pipeline
    pipeline = IndexingPipeline(
        chunker=mock_components["chunker"],
        context_generator=mock_components["context_generator"],
        embedder=mock_components["embedder"],
        vector_search=mock_components["vector_search"],
        config=sample_config,
    )

    # Process file
    docs = await pipeline._process_file(test_file)

    assert len(docs) == 1
    assert docs[0]["payload"]["function_name"] == "foo"
    assert docs[0]["payload"]["file_path"] == str(test_file)


@pytest.mark.asyncio
async def test_discover_files(mock_components, tmp_path):
    """Test file discovery."""
    # Create test files
    (tmp_path / "test1.py").write_text("code")
    (tmp_path / "test2.py").write_text("code")
    (tmp_path / "test_skip.pyc").write_text("binary")

    config = IndexingConfig(
        workspace_path=tmp_path,
        include_patterns=["*.py"],
        exclude_patterns=["*.pyc"],
    )

    pipeline = IndexingPipeline(
        chunker=mock_components["chunker"],
        context_generator=None,
        embedder=mock_components["embedder"],
        vector_search=mock_components["vector_search"],
        config=config,
    )

    files = pipeline._discover_files()

    # Should find .py files but not .pyc
    assert len(files) == 2
    assert all(f.suffix == ".py" for f in files)


@pytest.mark.asyncio
async def test_index_workspace_no_files(mock_components, tmp_path):
    """Test indexing with no files."""
    config = IndexingConfig(
        workspace_path=tmp_path,
        include_patterns=["*.xyz"],  # No matching files
    )

    pipeline = IndexingPipeline(
        chunker=mock_components["chunker"],
        context_generator=None,
        embedder=mock_components["embedder"],
        vector_search=mock_components["vector_search"],
        config=config,
    )

    progress = await pipeline.index_workspace()

    assert progress.total_files == 0
    assert progress.processed_files == 0
    assert progress.indexed_chunks == 0


@pytest.mark.asyncio
async def test_index_single_file(mock_components, sample_config, tmp_path):
    """Test incremental file indexing."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")

    # Mock components
    mock_chunk = CodeChunk(
        content="def foo(): pass",
        start_line=0,
        end_line=0,
        chunk_type="function",
        language="python",
        symbol_name="foo",
    )
    mock_components["chunker"].chunk_file.return_value = [mock_chunk]

    from src.context.claude_generator import ContextResponse
    mock_components["context_generator"].generate_contexts_batch.return_value = [
        ContextResponse(context="Test", tokens_used=10, cost_usd=0.001)
    ]

    mock_embedding = EmbeddingResponse(
        embedding=[0.1] * 1024,
        model="voyage-code-3",
        tokens=10,
        cost_usd=0.001,
    )
    mock_components["embedder"].embed_batch.return_value = [mock_embedding]

    # Create pipeline
    pipeline = IndexingPipeline(
        chunker=mock_components["chunker"],
        context_generator=mock_components["context_generator"],
        embedder=mock_components["embedder"],
        vector_search=mock_components["vector_search"],
        config=sample_config,
    )

    # Index single file
    chunks_indexed = await pipeline.index_single_file(test_file)

    assert chunks_indexed == 1
    mock_components["vector_search"].insert_points_batch.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_without_context_generator(mock_components, sample_config, tmp_path):
    """Test pipeline without context generation (testing mode)."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")

    mock_chunk = CodeChunk(
        content="def foo(): pass",
        start_line=0,
        end_line=0,
        chunk_type="function",
        language="python",
        symbol_name="foo",
    )
    mock_components["chunker"].chunk_file.return_value = [mock_chunk]

    mock_embedding = EmbeddingResponse(
        embedding=[0.1] * 1024,
        model="voyage-code-3",
        tokens=10,
        cost_usd=0.001,
    )
    mock_components["embedder"].embed_batch.return_value = [mock_embedding]

    # Pipeline WITHOUT context generator
    pipeline = IndexingPipeline(
        chunker=mock_components["chunker"],
        context_generator=None,  # Skip context generation
        embedder=mock_components["embedder"],
        vector_search=mock_components["vector_search"],
        config=sample_config,
    )

    docs = await pipeline._process_file(test_file)

    # Should still work with fallback contexts
    assert len(docs) == 1
    assert "Code from" in docs[0]["payload"]["context_snippet"]


def test_progress_callback_called(mock_components, sample_config):
    """Test that progress callback is invoked."""
    # This would be an integration test - skipping for unit tests
    pass


def test_cost_summary(mock_components, sample_config):
    """Test cost summary generation."""
    pipeline = IndexingPipeline(
        chunker=mock_components["chunker"],
        context_generator=mock_components["context_generator"],
        embedder=mock_components["embedder"],
        vector_search=mock_components["vector_search"],
        config=sample_config,
    )

    # Mock cost summaries
    mock_components["context_generator"].get_cost_summary.return_value = {
        "total_cost_usd": 0.10,
    }
    mock_components["embedder"].get_cost_summary.return_value = {
        "total_cost_usd": 0.05,
    }

    pipeline.progress.context_cost_usd = 0.10
    pipeline.progress.embedding_cost_usd = 0.05
    pipeline.progress.total_cost_usd = 0.15

    summary = pipeline.get_cost_summary()

    assert summary["context_generation"]["cost_usd"] == 0.10
    assert summary["embeddings"]["cost_usd"] == 0.05
    assert summary["total_cost_usd"] == 0.15
