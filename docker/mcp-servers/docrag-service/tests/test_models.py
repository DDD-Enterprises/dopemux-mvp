"""
Tests for DocRAG data models.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from docrag.models import (
    ChunkMetadata,
    DocumentChunk,
    DocumentType,
    SearchQuery,
    IngestionRequest,
)


def test_chunk_metadata_creation():
    """Test ChunkMetadata model creation."""
    metadata = ChunkMetadata(
        source_path="/test/doc.pdf",
        source_hash="abc123",
        chunk_index=0,
        char_count=500,
        token_count=100,
        content_hash="def456",
        document_type=DocumentType.PDF,
    )

    assert metadata.source_path == "/test/doc.pdf"
    assert metadata.document_type == DocumentType.PDF
    assert metadata.chunk_index == 0
    assert isinstance(metadata.created_at, datetime)


def test_document_chunk_validation():
    """Test DocumentChunk validation."""
    metadata = ChunkMetadata(
        source_path="/test/doc.pdf",
        source_hash="abc123",
        chunk_index=0,
        char_count=500,
        token_count=100,
        content_hash="def456",
        document_type=DocumentType.PDF,
    )

    # Valid chunk
    chunk = DocumentChunk(
        text="This is a test document chunk.",
        metadata=metadata,
    )
    assert chunk.text == "This is a test document chunk."

    # Empty text should fail
    with pytest.raises(ValueError, match="Chunk text cannot be empty"):
        DocumentChunk(text="", metadata=metadata)

    # Too long text should fail
    with pytest.raises(ValueError, match="Chunk text too long"):
        DocumentChunk(text="x" * 9000, metadata=metadata)


def test_search_query_validation():
    """Test SearchQuery validation."""
    # Valid query
    query = SearchQuery(query="test query", limit=5)
    assert query.query == "test query"
    assert query.limit == 5
    assert query.rerank is True
    assert query.dense_weight == 0.6
    assert query.sparse_weight == 0.4

    # Invalid limit
    with pytest.raises(ValueError):
        SearchQuery(query="test", limit=0)

    with pytest.raises(ValueError):
        SearchQuery(query="test", limit=100)


def test_ingestion_request_validation():
    """Test IngestionRequest validation."""
    # Valid request
    request = IngestionRequest(source_path="/test/doc.pdf")
    assert request.source_path == "/test/doc.pdf"
    assert request.chunk_size == 1000
    assert request.chunk_overlap == 100

    # Invalid chunk size
    with pytest.raises(ValueError):
        IngestionRequest(source_path="/test/doc.pdf", chunk_size=50)

    with pytest.raises(ValueError):
        IngestionRequest(source_path="/test/doc.pdf", chunk_size=3000)

    # Invalid overlap
    with pytest.raises(ValueError):
        IngestionRequest(
            source_path="/test/doc.pdf",
            chunk_size=1000,
            chunk_overlap=1000
        )