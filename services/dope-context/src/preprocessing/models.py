"""Shared data models for document preprocessing/indexing."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DocumentType(str, Enum):
    """Supported document types for dope-context docs indexing."""

    PDF = "pdf"
    MARKDOWN = "md"
    HTML = "html"
    TEXT = "txt"
    DOCX = "docx"
    UNKNOWN = "unknown"


@dataclass
class ChunkMetadata:
    """Metadata attached to each indexed document chunk."""

    source_path: str
    source_hash: str
    chunk_index: int
    char_count: int
    token_count: int
    content_hash: str
    document_type: DocumentType
    title: Optional[str] = None

    # Optional structure-aware metadata (primarily for markdown)
    section_hierarchy: List[str] = field(default_factory=list)
    header_level: int = 0
    has_code_blocks: bool = False
    complexity_estimate: float = 0.0
    parent_section: str = ""
    section_type: str = "content"


@dataclass
class DocumentChunk:
    """Single processed document chunk and its metadata."""

    text: str
    metadata: ChunkMetadata
