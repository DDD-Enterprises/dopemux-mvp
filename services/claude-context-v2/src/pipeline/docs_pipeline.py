"""
Document Indexing Pipeline
Parallel to code pipeline but for documents (PDF, Markdown, HTML, DOCX).
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Note: Imports will need adjustment after document_processor is cleaned up
# from ..preprocessing.document_processor import DocumentProcessor
from ..embeddings.voyage_embedder import VoyageEmbedder
from ..search.docs_search import DocumentSearch


logger = logging.getLogger(__name__)


class DocIndexingPipeline:
    """
    Document indexing pipeline for PDFs, Markdown, HTML, DOCX.

    Parallel architecture to code pipeline:
    - Document chunking (1000 chars with overlap)
    - Multi-vector embeddings (content, title, breadcrumb)
    - Qdrant storage in docs_index collection
    """

    def __init__(
        self,
        embedder: VoyageEmbedder,
        doc_search: DocumentSearch,
        workspace_path: Path,
        workspace_id: str = "default",
    ):
        """
        Initialize document indexing pipeline.

        Args:
            embedder: Voyage embedder (configured for voyage-context-3)
            doc_search: Document search instance
            workspace_path: Path to workspace
            workspace_id: Workspace identifier
        """
        self.embedder = embedder
        self.doc_search = doc_search
        self.workspace_path = workspace_path
        self.workspace_id = workspace_id

        # Stats
        self.docs_processed = 0
        self.chunks_indexed = 0
        self.errors = 0

    async def index_document(
        self,
        file_path: Path,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ) -> int:
        """
        Index a single document.

        Args:
            file_path: Path to document
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks

        Returns:
            Number of chunks indexed
        """
        try:
            # 1. Read document
            # For MVP, simple text file reading
            # TODO: Use DocumentProcessor for PDF/DOCX/HTML/Markdown
            text = file_path.read_text(encoding="utf-8")

            # 2. Simple chunking (for MVP)
            chunks = self._simple_chunk(text, chunk_size, chunk_overlap)

            if not chunks:
                return 0

            # 3. Prepare texts for embedding
            doc_name = file_path.stem

            content_texts = chunks
            title_texts = [f"{doc_name} - Part {i+1}" for i in range(len(chunks))]
            breadcrumb_texts = [f"{file_path.name}#{i}" for i in range(len(chunks))]

            # 4. Embed with voyage-context-3
            content_embeddings = await self.embedder.embed_batch(
                texts=content_texts,
                model="voyage-context-3",
                input_type="document",
            )

            title_embeddings = await self.embedder.embed_batch(
                texts=title_texts,
                model="voyage-context-3",
                input_type="document",
            )

            breadcrumb_embeddings = await self.embedder.embed_batch(
                texts=breadcrumb_texts,
                model="voyage-context-3",
                input_type="document",
            )

            # 5. Prepare metadata
            chunk_dicts = [
                {
                    "text": chunk,
                    "source_path": str(file_path),
                    "doc_type": file_path.suffix.lstrip("."),
                    "workspace_id": self.workspace_id,
                }
                for chunk in chunks
            ]

            # 6. Index in Qdrant
            await self.doc_search.index_document(
                doc_id=str(file_path),
                chunks=chunk_dicts,
                content_vectors=[e.embedding for e in content_embeddings],
                title_vectors=[e.embedding for e in title_embeddings],
                breadcrumb_vectors=[e.embedding for e in breadcrumb_embeddings],
            )

            self.docs_processed += 1
            self.chunks_indexed += len(chunks)

            logger.info(f"Indexed {file_path.name}: {len(chunks)} chunks")
            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}")
            self.errors += 1
            return 0

    def _simple_chunk(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
    ) -> List[str]:
        """
        Simple chunking with overlap.

        For MVP. TODO: Use DocumentProcessor's smarter chunking.
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk)

            start = end - overlap

        return chunks

    async def index_workspace(
        self,
        include_patterns: List[str] = None,
    ) -> Dict:
        """
        Index all documents in workspace.

        Args:
            include_patterns: File patterns (e.g., ["*.md", "*.pdf"])

        Returns:
            Summary statistics
        """
        if include_patterns is None:
            include_patterns = ["*.md", "*.txt", "*.pdf", "*.html"]

        # Create collection
        await self.doc_search.create_collection()

        # Discover files
        files = []
        for pattern in include_patterns:
            files.extend(self.workspace_path.glob(f"**/{pattern}"))

        logger.info(f"Found {len(files)} documents to index")

        # Index each file
        for file_path in files:
            await self.index_document(file_path)

        return {
            "docs_processed": self.docs_processed,
            "chunks_indexed": self.chunks_indexed,
            "errors": self.errors,
        }
