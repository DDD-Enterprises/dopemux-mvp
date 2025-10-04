"""
Data models for document processing.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DocumentType(Enum):
    """Document file type."""

    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class DocumentChunk:
    """A chunk of document text."""

    text: str
    metadata: Optional["ChunkMetadata"] = None


@dataclass
class ChunkMetadata:
    """Metadata for a document chunk."""

    source_path: str
    source_hash: str
    chunk_index: int
    char_count: int
    token_count: int
    content_hash: str
    document_type: DocumentType
    title: str
