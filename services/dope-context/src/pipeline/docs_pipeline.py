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
            # NOW WITH STRUCTURE-AWARE CHUNKING! 🚀
            doc_chunks = self.doc_processor.process_document(
                str(file_path),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                use_structure_aware=True,  # Enable optimization!
            )

            # 2. Extract text and preserve metadata
            chunks = [chunk.text for chunk in doc_chunks]
            chunk_metadata = [chunk.metadata for chunk in doc_chunks]

            if not chunks:
                return 0

            # 3. Validate chunk sizes (Voyage context-3 has 32K token limit)
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            MAX_TOKENS = 8000  # Safe limit leaving room for document context

            validated_chunks = []
            for chunk in chunks:
                token_count = len(enc.encode(chunk))
                if token_count > MAX_TOKENS:
                    # Split large chunk into smaller pieces
                    logger.warning(f"Chunk too large ({token_count} tokens), splitting...")
                    words = chunk.split()
                    current = []
                    for word in words:
                        test_chunk = " ".join(current + [word])
                        if len(enc.encode(test_chunk)) > MAX_TOKENS:
                            if current:
                                validated_chunks.append(" ".join(current))
                            current = [word]
                        else:
                            current.append(word)
                    if current:
                        validated_chunks.append(" ".join(current))
                else:
                    validated_chunks.append(chunk)

            chunks = validated_chunks
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

            # For multi-vector search: Create breadcrumbs from hierarchy!
            # This improves search precision significantly
            breadcrumb_texts = []
            for metadata in chunk_metadata:
                if metadata and metadata.parent_section:
                    # Use hierarchy breadcrumb: "Main > Subtopic > Detail"
                    breadcrumb_texts.append(metadata.parent_section)
                else:
                    # Fallback to doc name
                    breadcrumb_texts.append(doc_name)

            # Embed breadcrumbs separately for better multi-vector precision
            if breadcrumb_texts and breadcrumb_texts != [doc_name] * len(breadcrumb_texts):
                breadcrumb_result = await self.embedder.embed_document(
                    chunks=breadcrumb_texts,
                    model="voyage-context-3",
                    input_type="document",
                    output_dimension=1024,
                )
                breadcrumb_embeddings = breadcrumb_result.embeddings
            else:
                # Reuse content embeddings if no hierarchy
                breadcrumb_embeddings = content_embeddings

            # Title embeddings can reuse content (already contextualized)
            title_embeddings = content_embeddings

            # 5. Prepare metadata (NOW WITH STRUCTURE INFO!)
            chunk_dicts = []
            for chunk_text, metadata in zip(chunks, chunk_metadata):
                chunk_dict = {
                    "text": chunk_text,
                    "source_path": str(file_path),
                    "doc_type": file_path.suffix.lstrip("."),
                    "workspace_id": self.workspace_id,
                }

                # Add structure metadata if available
                if metadata:
                    chunk_dict.update({
                        "section_hierarchy": metadata.section_hierarchy,
                        "header_level": metadata.header_level,
                        "has_code_blocks": metadata.has_code_blocks,
                        "complexity_estimate": metadata.complexity_estimate,
                        "parent_section": metadata.parent_section,
                        "section_type": metadata.section_type,
                    })

                chunk_dicts.append(chunk_dict)

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
