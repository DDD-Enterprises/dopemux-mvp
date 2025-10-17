"""
Document processing and chunking utilities.
"""

import hashlib
import re
from pathlib import Path
from typing import List, Optional, Tuple

import tiktoken
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from markdown import markdown
from PyPDF2 import PdfReader

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
        self.encoding = tiktoken.get_encoding(encoding_name)
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
            except Exception:
                pass

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
        doc = DocxDocument(file_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        return "\\n\\n".join(text_parts)

    def _extract_html_text(self, file_path: str) -> str:
        """Extract text from HTML file."""
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
        """Extract text from Markdown file."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            content = file.read()

        # Convert markdown to HTML then extract text
        html = markdown(content)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text().strip()

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

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))

    def compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def process_document(
        self,
        file_path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        metadata_override: Optional[dict] = None,
    ) -> List[DocumentChunk]:
        """Process a document into chunks ready for indexing."""
        # Extract text
        doc_type = self.detect_document_type(file_path)
        text = self.extract_text(file_path, doc_type)

        if not text.strip():
            raise ValueError(f"No text content extracted from {file_path}")

        # Compute document hash
        source_hash = self.compute_content_hash(text)

        # Chunk the text
        chunks = self.chunk_text(text, chunk_size, chunk_overlap)

        # Create document chunks
        document_chunks = []
        for i, chunk_text in enumerate(chunks):
            # Create metadata
            metadata = ChunkMetadata(
                source_path=file_path,
                source_hash=source_hash,
                chunk_index=i,
                char_count=len(chunk_text),
                token_count=self.count_tokens(chunk_text),
                content_hash=self.compute_content_hash(chunk_text),
                document_type=doc_type,
                title=Path(file_path).stem,
            )

            # Apply metadata overrides
            if metadata_override:
                for key, value in metadata_override.items():
                    if hasattr(metadata, key):
                        setattr(metadata, key, value)

            # Create chunk
            chunk = DocumentChunk(
                text=chunk_text,
                metadata=metadata,
            )
            document_chunks.append(chunk)

        return document_chunks
