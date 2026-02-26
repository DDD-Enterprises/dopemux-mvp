"""
Document processing and chunking utilities.
"""

import logging

import hashlib
import re
from pathlib import Path
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised in constrained envs
    TIKTOKEN_AVAILABLE = False
    tiktoken = Any  # type: ignore

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:  # pragma: no cover
    BS4_AVAILABLE = False
    BeautifulSoup = Any  # type: ignore

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:  # pragma: no cover
    DOCX_AVAILABLE = False
    DocxDocument = Any  # type: ignore

try:
    from markdown import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:  # pragma: no cover
    MARKDOWN_AVAILABLE = False
    markdown = Any  # type: ignore

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:  # pragma: no cover
    PYPDF2_AVAILABLE = False
    PdfReader = Any  # type: ignore

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from .models import ChunkMetadata, DocumentChunk, DocumentType


class DocumentProcessor:
    """Process various document types into text chunks."""

    def __init__(self, encoding_name: str = "cl100k_base"):
        """Initialize document processor."""
        if TIKTOKEN_AVAILABLE:
            self.encoding = tiktoken.get_encoding(encoding_name)
        else:
            self.encoding = None
        self.magic = magic.Magic(mime=True) if MAGIC_AVAILABLE else None

    def detect_document_type(self, file_path: str) -> DocumentType:
        """Detect document type from file path and content."""
        path = Path(file_path)
        suffix = path.suffix.lower()

        # Check file extension first
        extension_map = {
            ".pdf": DocumentType.PDF,
            ".md": DocumentType.MARKDOWN,
            ".markdown": DocumentType.MARKDOWN,
            ".html": DocumentType.HTML,
            ".htm": DocumentType.HTML,
            ".txt": DocumentType.TEXT,
            ".docx": DocumentType.DOCX,
        }

        if suffix in extension_map:
            return extension_map[suffix]

        # Fallback to MIME type detection (if magic available)
        if self.magic is not None:
            try:
                mime_type = self.magic.from_file(file_path)
                if "pdf" in mime_type:
                    return DocumentType.PDF
                elif "html" in mime_type:
                    return DocumentType.HTML
                elif "text" in mime_type:
                    return DocumentType.TEXT
                elif "officedocument" in mime_type and "wordprocessing" in mime_type:
                    return DocumentType.DOCX
            except Exception as e:
                logger.debug("MIME detection failed for %s: %s", file_path, e)
        return DocumentType.UNKNOWN

    def extract_text(
        self, file_path: str, doc_type: Optional[DocumentType] = None
    ) -> str:
        """Extract text from document."""
        if doc_type is None:
            doc_type = self.detect_document_type(file_path)

        try:
            if doc_type == DocumentType.PDF:
                return self._extract_pdf_text(file_path)
            elif doc_type == DocumentType.DOCX:
                return self._extract_docx_text(file_path)
            elif doc_type == DocumentType.HTML:
                return self._extract_html_text(file_path)
            elif doc_type == DocumentType.MARKDOWN:
                return self._extract_markdown_text(file_path)
            elif doc_type == DocumentType.TEXT:
                return self._extract_text_file(file_path)
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")
        except Exception as e:
            raise ValueError(f"Failed to extract text from {file_path}: {str(e)}")

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        if not PYPDF2_AVAILABLE:
            raise ValueError("PyPDF2 is not installed; cannot read PDF files")
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text.strip())
            return "\\n\\n".join(text_parts)

    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        if not DOCX_AVAILABLE:
            raise ValueError("python-docx is not installed; cannot read DOCX files")
        doc = DocxDocument(file_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        return "\\n\\n".join(text_parts)

    def _extract_html_text(self, file_path: str) -> str:
        """Extract text from HTML file."""
        if not BS4_AVAILABLE:
            raise ValueError("beautifulsoup4 is not installed; cannot read HTML files")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()

        soup = BeautifulSoup(content, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\\n".join(chunk for chunk in chunks if chunk)

        return text

    def _extract_markdown_text(self, file_path: str) -> str:
        """
        Extract text from Markdown file.

        IMPORTANT: Keep raw markdown to preserve structure (headers, code blocks)
        for structure-aware chunking!
        """
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()

        # Return raw markdown (preserves headers for structure-aware chunking)
        return content.strip()

    def _extract_text_file(self, file_path: str) -> str:
        """Extract text from plain text file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            return file.read().strip()

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        preserve_structure: bool = True,
    ) -> List[str]:
        """Chunk text into smaller pieces with proper structure preservation."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []

        if not preserve_structure:
            # Simple character-based chunking
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk = text[i : i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk.strip())
            return chunks

        # Structure-preserving chunking (FIXED)
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If paragraph is small, try to add to current chunk
            if len(paragraph) <= chunk_size:
                test_addition = current_chunk + ("\n\n" if current_chunk else "") + paragraph
                if len(test_addition) <= chunk_size:
                    current_chunk = test_addition
                    continue
                else:
                    # Current chunk is full, save it
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = paragraph
                    continue

            # Paragraph is too large, needs sentence-level splitting
            # First, save current chunk if it exists
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # Split paragraph by sentences
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Try to add sentence to current chunk
                test_addition = current_chunk + (" " if current_chunk else "") + sentence

                if len(test_addition) <= chunk_size:
                    current_chunk = test_addition
                else:
                    # Current chunk is full
                    if current_chunk:
                        chunks.append(current_chunk)
                    # Start new chunk with this sentence
                    # If sentence itself > chunk_size, split by words
                    if len(sentence) > chunk_size:
                        words = sentence.split()
                        word_chunk = ""
                        for word in words:
                            test_word = word_chunk + (" " if word_chunk else "") + word
                            if len(test_word) <= chunk_size:
                                word_chunk = test_word
                            else:
                                if word_chunk:
                                    chunks.append(word_chunk)
                                word_chunk = word
                        current_chunk = word_chunk
                    else:
                        current_chunk = sentence

        # Don't forget final chunk!
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def chunk_markdown_structured(
        self,
        text: str,
        max_chunk_size: int = 1500,
        preserve_hierarchy: bool = True,
    ) -> List[Tuple[str, List[str], int]]:
        """
        Chunk markdown by structure (headers) while preserving hierarchy.

        This is the OPTIMIZATION we want! Chunks by semantic sections instead
        of arbitrary character boundaries.

        Args:
            text: Markdown text to chunk
            max_chunk_size: Maximum chunk size in characters
            preserve_hierarchy: Include parent headers for context

        Returns:
            List of (chunk_text, hierarchy_path, header_level) tuples

        Example:
            Input:
                # Main Topic
                ## Subtopic A
                Content for A...
                ## Subtopic B
                Content for B...

            Output:
                [
                    ("# Main Topic\n## Subtopic A\nContent for A...", ["Main Topic", "Subtopic A"], 2),
                    ("# Main Topic\n## Subtopic B\nContent for B...", ["Main Topic", "Subtopic B"], 2)
                ]
        """
        chunks = []
        current_hierarchy = []  # Stack: [(level, title), ...]
        current_section = []
        current_size = 0

        for line in text.split('\n'):
            # Detect markdown headers
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)

            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()

                # Save current section if we have content and it's large enough
                if current_section and current_size > 100:  # Min 100 chars
                    # Build chunk with hierarchy
                    if preserve_hierarchy and current_hierarchy:
                        # Add parent headers for context
                        hierarchy_headers = []
                        for h_level, h_title in current_hierarchy:
                            hierarchy_headers.append(f"{'#' * h_level} {h_title}")

                        chunk_text = '\n'.join(hierarchy_headers + current_section)
                    else:
                        chunk_text = '\n'.join(current_section)

                    # Extract hierarchy path
                    hierarchy_path = [h[1] for h in current_hierarchy]
                    header_level = current_hierarchy[-1][0] if current_hierarchy else 0

                    chunks.append((chunk_text, hierarchy_path, header_level))

                    # Reset for new section
                    current_section = []
                    current_size = 0

                # Update hierarchy stack
                # Remove items at same or deeper level
                current_hierarchy = [h for h in current_hierarchy if h[0] < level]
                # Add new header
                current_hierarchy.append((level, title))

                # Start new section with header
                current_section.append(line)
                current_size += len(line)

            else:
                # Regular content line
                current_section.append(line)
                current_size += len(line)

                # If chunk gets too large, save it
                if current_size > max_chunk_size:
                    if preserve_hierarchy and current_hierarchy:
                        hierarchy_headers = []
                        for h_level, h_title in current_hierarchy:
                            hierarchy_headers.append(f"{'#' * h_level} {h_title}")
                        chunk_text = '\n'.join(hierarchy_headers + current_section)
                    else:
                        chunk_text = '\n'.join(current_section)

                    hierarchy_path = [h[1] for h in current_hierarchy]
                    header_level = current_hierarchy[-1][0] if current_hierarchy else 0

                    chunks.append((chunk_text, hierarchy_path, header_level))

                    # Start fresh (keep hierarchy, reset content)
                    current_section = []
                    current_size = 0

        # Don't forget final section!
        if current_section and current_size > 100:
            if preserve_hierarchy and current_hierarchy:
                hierarchy_headers = []
                for h_level, h_title in current_hierarchy:
                    hierarchy_headers.append(f"{'#' * h_level} {h_title}")
                chunk_text = '\n'.join(hierarchy_headers + current_section)
            else:
                chunk_text = '\n'.join(current_section)

            hierarchy_path = [h[1] for h in current_hierarchy]
            header_level = current_hierarchy[-1][0] if current_hierarchy else 0

            chunks.append((chunk_text, hierarchy_path, header_level))

        # If no structured chunks created, fall back to basic chunking
        if not chunks and text.strip():
            chunks.append((text, [], 0))

        return chunks

    def estimate_chunk_complexity(self, chunk_text: str) -> float:
        """
        Estimate cognitive complexity of a doc chunk (ADHD optimization).

        Factors:
        - Has code blocks (higher complexity)
        - Has tables (moderate complexity)
        - Length (longer = more complex)
        - Technical density (specialized terms)

        Returns:
            0.0-1.0 complexity score
        """
        complexity = 0.0

        # Code blocks increase complexity
        if '```' in chunk_text or '    ' in chunk_text[:50]:  # Indented code
            complexity += 0.3

        # Tables increase complexity
        if '|' in chunk_text and chunk_text.count('|') > 5:
            complexity += 0.2

        # Length factor
        length_factor = min(len(chunk_text) / 2000, 0.3)
        complexity += length_factor

        # Technical density (capital words, underscores, symbols)
        technical_indicators = len(re.findall(r'[A-Z_]{2,}', chunk_text))
        if technical_indicators > 5:
            complexity += 0.2

        return min(complexity, 1.0)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if self.encoding:
            return len(self.encoding.encode(text))
        # Fallback: rough estimation (4 chars per token)
        return len(text) // 4

    def compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def process_document(
        self,
        file_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        metadata_override: Optional[dict] = None,
        use_structure_aware: bool = True,  # NEW: Enable optimization
    ) -> List[DocumentChunk]:
        """
        Process a document into chunks ready for indexing.

        Now with STRUCTURE-AWARE chunking for markdown! 🚀
        """
        # Extract text
        doc_type = self.detect_document_type(file_path)
        text = self.extract_text(file_path, doc_type)

        if not text.strip():
            raise ValueError(f"No text content extracted from {file_path}")

        # Compute document hash
        source_hash = self.compute_content_hash(text)

        # OPTIMIZATION: Use structure-aware chunking for markdown!
        if use_structure_aware and doc_type == DocumentType.MARKDOWN:
            # Structure-aware chunking returns (text, hierarchy, level) tuples
            structured_chunks = self.chunk_markdown_structured(
                text,
                max_chunk_size=chunk_size,
                preserve_hierarchy=True,
            )

            document_chunks = []
            for i, (chunk_text, hierarchy_path, header_level) in enumerate(structured_chunks):
                # Detect section type
                has_code = '```' in chunk_text
                has_table = '|' in chunk_text and chunk_text.count('|') > 5
                section_type = "code" if has_code else ("table" if has_table else "content")

                # Create enhanced metadata with hierarchy
                metadata = ChunkMetadata(
                    source_path=file_path,
                    source_hash=source_hash,
                    chunk_index=i,
                    char_count=len(chunk_text),
                    token_count=self.count_tokens(chunk_text),
                    content_hash=self.compute_content_hash(chunk_text),
                    document_type=doc_type,
                    title=Path(file_path).stem,
                    # NEW: Structure metadata
                    section_hierarchy=hierarchy_path,
                    header_level=header_level,
                    has_code_blocks=has_code,
                    complexity_estimate=self.estimate_chunk_complexity(chunk_text),
                    parent_section=" > ".join(hierarchy_path) if hierarchy_path else "",
                    section_type=section_type,
                )

                # Apply metadata overrides
                if metadata_override:
                    for key, value in metadata_override.items():
                        if hasattr(metadata, key):
                            setattr(metadata, key, value)

                document_chunks.append(DocumentChunk(text=chunk_text, metadata=metadata))

        else:
            # Fallback to basic chunking for non-markdown or if disabled
            chunks = self.chunk_text(text, chunk_size, chunk_overlap)

            document_chunks = []
            for i, chunk_text in enumerate(chunks):
                metadata = ChunkMetadata(
                    source_path=file_path,
                    source_hash=source_hash,
                    chunk_index=i,
                    char_count=len(chunk_text),
                    token_count=self.count_tokens(chunk_text),
                    content_hash=self.compute_content_hash(chunk_text),
                    document_type=doc_type,
                    title=Path(file_path).stem,
                    complexity_estimate=self.estimate_chunk_complexity(chunk_text),
                )

                if metadata_override:
                    for key, value in metadata_override.items():
                        if hasattr(metadata, key):
                            setattr(metadata, key, value)

                document_chunks.append(DocumentChunk(text=chunk_text, metadata=metadata))

        # Hard invariant: ordinals must be contiguous and deterministic.
        observed = [chunk.metadata.chunk_index for chunk in document_chunks]
        expected = list(range(len(document_chunks)))
        if observed != expected:
            raise ValueError(
                f"Non-contiguous document chunk ordinals for {file_path}: {observed}"
            )

        return document_chunks
