"""Document indexing pipeline for dope-context docs search."""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..embeddings.contextualized_embedder import ContextualizedEmbedder
from ..preprocessing.document_processor import DocumentProcessor
from ..preprocessing.models import DocumentChunk
from ..search.docs_search import DocumentSearch


logger = logging.getLogger(__name__)


@dataclass
class DocsIndexingProgress:
    """Track docs indexing progress and outcomes."""

    workspace: str
    total_documents: int = 0
    indexed_documents: int = 0
    skipped_documents: int = 0
    error_documents: int = 0
    indexed_chunks: int = 0
    replaced_chunks: int = 0
    total_cost_usd: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    errors: List[Dict[str, str]] = field(default_factory=list)

    def elapsed_seconds(self) -> float:
        end = self.ended_at or datetime.now()
        return (end - self.started_at).total_seconds()

    def summary(self) -> Dict[str, Any]:
        return {
            "workspace": self.workspace,
            "documents_discovered": self.total_documents,
            "documents_indexed": self.indexed_documents,
            "documents_skipped": self.skipped_documents,
            "documents_failed": self.error_documents,
            "chunks_indexed": self.indexed_chunks,
            "chunks_replaced": self.replaced_chunks,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "elapsed_seconds": round(self.elapsed_seconds(), 2),
            "errors": self.errors,
        }


class DocIndexingPipeline:
    """Pipeline to process and index markdown/pdf/html/txt/docx documents."""

    DEFAULT_INCLUDE_PATTERNS = [
        "*.md",
        "*.markdown",
        "*.txt",
        "*.html",
        "*.htm",
        "*.pdf",
        "*.docx",
    ]

    DEFAULT_EXCLUDED_SEGMENTS = {
        ".git",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".venv",
        "venv",
    }

    def __init__(
        self,
        embedder: ContextualizedEmbedder,
        doc_search: DocumentSearch,
        workspace_path: Path,
        workspace_id: str = "default",
        chunk_size: int = 1500,
        chunk_overlap: int = 150,
        qdrant_batch_size: int = 100,
    ):
        self.embedder = embedder
        self.doc_search = doc_search
        self.workspace_path = workspace_path.resolve()
        self.workspace_id = workspace_id
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.qdrant_batch_size = qdrant_batch_size
        self.processor = DocumentProcessor()

    def _should_exclude(self, path: Path) -> bool:
        return any(part in self.DEFAULT_EXCLUDED_SEGMENTS for part in path.parts)

    def _source_uri(self, source: Path) -> str:
        """Return stable workspace-relative URI when possible."""
        try:
            return source.relative_to(self.workspace_path).as_posix()
        except ValueError:
            return source.as_posix()

    def _doc_id_for_source(self, source: Path) -> str:
        """Return deterministic document ID for a source file."""
        return self._source_uri(source)

    def _chunk_id_for_doc(self, doc_id: str, ordinal: int) -> str:
        """Return deterministic chunk identifier for a document ordinal."""
        return f"{doc_id}::chunk::{ordinal}"

    def _validate_chunk_ordinals(self, chunks: List[DocumentChunk], source: Path) -> None:
        """Validate chunk ordinal continuity for fail-closed indexing."""
        ordinals = [chunk.metadata.chunk_index for chunk in chunks]
        expected = list(range(len(chunks)))
        if ordinals != expected:
            raise ValueError(
                f"Chunk ordinal mismatch for {source}: expected {expected}, got {ordinals}"
            )

    def _discover_documents(self, include_patterns: Optional[List[str]] = None) -> List[Path]:
        """Discover candidate docs files for indexing."""
        patterns = include_patterns or self.DEFAULT_INCLUDE_PATTERNS
        files: Set[Path] = set()

        for pattern in patterns:
            for candidate in self.workspace_path.glob(f"**/{pattern}"):
                if candidate.is_file() and not self._should_exclude(candidate.relative_to(self.workspace_path)):
                    files.add(candidate.resolve())

        discovered = sorted(files)
        logger.info("Discovered %s docs files in %s", len(discovered), self.workspace_path)
        return discovered

    def _build_chunk_payload(
        self,
        source: Path,
        chunk: DocumentChunk,
        *,
        doc_id: str,
    ) -> Dict[str, Any]:
        """Convert processed chunk metadata into Qdrant payload."""
        metadata = chunk.metadata
        source_path = source.as_posix()
        source_uri = self._source_uri(source)
        ordinal = int(metadata.chunk_index)
        chunk_id = self._chunk_id_for_doc(doc_id, ordinal)
        instance_id = os.getenv("DOPEMUX_WORKSPACE_ID", self.workspace_id)
        return {
            "source_path": source_path,
            "source_uri": source_uri,
            "file_path": source_path,
            "text": chunk.text,
            "doc_type": metadata.document_type.value,
            "title": metadata.title or source.stem,
            "workspace_id": self.workspace_id,
            "instance_id": instance_id,
            "source_type": "doc",
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "ordinal": ordinal,
            "embed_model": "voyage-context-3",
            "chunker_version": "document_processor.v1",
            "chunk_index": metadata.chunk_index,
            "char_count": metadata.char_count,
            "token_count": metadata.token_count,
            "source_hash": metadata.source_hash,
            "content_hash": metadata.content_hash,
            "section_hierarchy": metadata.section_hierarchy,
            "header_level": metadata.header_level,
            "has_code_blocks": metadata.has_code_blocks,
            "complexity_estimate": metadata.complexity_estimate,
            "parent_section": metadata.parent_section,
            "section_type": metadata.section_type,
        }

    async def _delete_existing_chunks(self, source_paths: Set[str]) -> int:
        """
        Remove existing chunks for documents being reindexed.
        """
        if not source_paths:
            return 0

        existing_payloads = await self.doc_search.get_all_payloads()
        if not existing_payloads:
            return 0

        target_paths = {Path(path).as_posix() for path in source_paths}
        target_basenames = {Path(path).name for path in source_paths}
        point_ids: List[str] = []

        for payload in existing_payloads:
            point_id = payload.get("id")
            source_path = payload.get("source_path") or payload.get("file_path")
            if not point_id or not source_path:
                continue

            normalized_source = Path(str(source_path)).as_posix()
            if (
                normalized_source in target_paths
                or normalized_source.lstrip("./") in target_paths
                or Path(normalized_source).name in target_basenames
            ):
                point_ids.append(str(point_id))

        if point_ids:
            await self.doc_search.delete_points(point_ids)
            logger.info("Removed %s stale doc chunks before reindex", len(point_ids))

        return len(point_ids)

    async def _index_document(self, file_path: Path) -> Tuple[int, float]:
        """
        Process and index one document.

        Returns:
            Tuple of (chunk_count, embedding_cost_usd)
        """
        processed_chunks = self.processor.process_document(
            file_path=str(file_path),
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            use_structure_aware=True,
        )

        chunks = [chunk for chunk in processed_chunks if chunk.text.strip()]
        if not chunks:
            return 0, 0.0

        self._validate_chunk_ordinals(chunks, file_path)

        embed_response = await self.embedder.embed_document(
            chunks=[chunk.text for chunk in chunks],
            model="voyage-context-3",
            input_type="document",
            output_dimension=1024,
        )

        if len(embed_response.embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch for {file_path}: "
                f"{len(embed_response.embeddings)} vectors for {len(chunks)} chunks"
            )

        points = []
        doc_id = self._doc_id_for_source(file_path)
        for chunk, embedding in zip(chunks, embed_response.embeddings):
            payload = self._build_chunk_payload(
                file_path,
                chunk,
                doc_id=doc_id,
            )
            # Docs currently use one contextualized embedding for all three vectors.
            points.append((embedding, embedding, embedding, payload, None))

        for i in range(0, len(points), self.qdrant_batch_size):
            await self.doc_search.insert_points_batch(points[i : i + self.qdrant_batch_size])

        return len(points), embed_response.cost_usd

    async def index_workspace(self, include_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Index all matching documents in the workspace."""
        progress = DocsIndexingProgress(workspace=str(self.workspace_path))
        await self.doc_search.create_collection()

        docs_files = self._discover_documents(include_patterns=include_patterns)
        progress.total_documents = len(docs_files)

        progress.replaced_chunks = await self._delete_existing_chunks(
            {path.as_posix() for path in docs_files}
        )

        for file_path in docs_files:
            try:
                chunk_count, cost_usd = await self._index_document(file_path)
            except Exception as exc:
                progress.error_documents += 1
                progress.errors.append({"file": file_path.as_posix(), "error": str(exc)})
                logger.warning("Document indexing failed for %s: %s", file_path, exc)
                continue

            if chunk_count == 0:
                progress.skipped_documents += 1
                logger.debug("Skipped empty document %s", file_path)
                continue

            progress.indexed_documents += 1
            progress.indexed_chunks += chunk_count
            progress.total_cost_usd += cost_usd

        progress.ended_at = datetime.now()
        return progress.summary()
