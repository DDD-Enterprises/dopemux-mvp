"""
Document Indexing Pipeline
Parallel to code pipeline but for documents (PDF, Markdown, HTML, DOCX).
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..preprocessing.document_processor import DocumentProcessor
from ..embeddings.contextualized_embedder import ContextualizedEmbedder
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
        embedder: ContextualizedEmbedder,
        doc_search: DocumentSearch,
        workspace_path: Path,
        workspace_id: str = "default",
    ):
        """
        Initialize document indexing pipeline.

        Args:
            embedder: Contextualized embedder (for voyage-context-3)
            doc_search: Document search instance
            workspace_path: Path to workspace
            workspace_id: Workspace identifier
        """
        self.embedder = embedder
        self.doc_search = doc_search
        self.workspace_path = workspace_path
        self.workspace_id = workspace_id
        self.doc_processor = DocumentProcessor()

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
            # 1. Extract text using DocumentProcessor (handles PDF/DOCX/HTML/Markdown)
            doc_chunks = self.doc_processor.process_document(
                str(file_path),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

            # 2. Extract text content from DocumentChunk objects
            chunks = [chunk.text for chunk in doc_chunks]

            if not chunks:
                return 0

            # 3. Prepare texts for embedding
            doc_name = file_path.stem

            # 4. Embed with voyage-context-3 (contextualized embeddings)
            # Content embeddings capture global document context + local chunk details
            result = await self.embedder.embed_document(
                chunks=chunks,
                model="voyage-context-3",
                input_type="document",
                output_dimension=1024,
            )

            content_embeddings = result.embeddings

            # For multi-vector search: reuse content embeddings for title/breadcrumb
            # (voyage-context-3 already captures full document context)
            title_embeddings = content_embeddings
            breadcrumb_embeddings = content_embeddings

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
                content_vectors=content_embeddings,
                title_vectors=title_embeddings,
                breadcrumb_vectors=breadcrumb_embeddings,
            )

            self.docs_processed += 1
            self.chunks_indexed += len(chunks)

            logger.info(f"Indexed {file_path.name}: {len(chunks)} chunks")
            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to index {file_path}: {e}")
            self.errors += 1
            return 0

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
