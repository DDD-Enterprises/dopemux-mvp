"""
Data models for document processing.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


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
    """Metadata for a document chunk with hierarchy support."""

    source_path: str
    source_hash: str
    chunk_index: int
    char_count: int
    token_count: int
    content_hash: str
    document_type: DocumentType
    title: str

    # NEW: Structure-aware metadata for better search
    section_hierarchy: List[str] = field(default_factory=list)  # ["Main", "Subtopic", "Detail"]
    header_level: int = 0  # 1-6 for markdown (0 = no header)
    page_number: Optional[int] = None  # For PDFs
    has_code_blocks: bool = False  # Contains code snippets
    complexity_estimate: float = 0.0  # 0.0-1.0 (ADHD cognitive load)
    parent_section: str = ""  # "Main > Subtopic"
    section_type: str = "content"  # content, code, table, list
