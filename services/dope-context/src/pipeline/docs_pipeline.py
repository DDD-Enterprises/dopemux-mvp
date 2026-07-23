"""Document indexing pipeline for dope-context docs search."""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..embeddings.contextualized_embedder import ContextualizedEmbedder
from ..embeddings.model_registry import INDEX_SCHEMA_VERSION, index_fingerprint
from ..preprocessing.document_processor import DocumentProcessor
from ..preprocessing.models import DocumentChunk
from ..search.docs_search import DocumentSearch

logger = logging.getLogger(__name__)

CHUNKER_VERSION = "document_processor.v2-voyage-token-accounting"


@dataclass
class DocsIndexingProgress:
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
        return ((self.ended_at or datetime.now()) - self.started_at).total_seconds()

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
    """Process documents, embed grouped chunks, and upsert them idempotently."""

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
        ".worktrees",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".venv",
        "venv",
        "archive",
    }

    def __init__(
        self,
        embedder: ContextualizedEmbedder,
        doc_search: DocumentSearch,
        workspace_path: Path,
        workspace_id: str = "default",
        chunk_size: int = 1500,
        chunk_overlap: int = 0,
        qdrant_batch_size: int = 100,
    ):
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")

        self.embedder = embedder
        self.doc_search = doc_search
        self.workspace_path = workspace_path.resolve()
        self.workspace_id = workspace_id
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.qdrant_batch_size = max(1, qdrant_batch_size)
        self.processor = DocumentProcessor()

    def _should_exclude(self, path: Path) -> bool:
        return any(part in self.DEFAULT_EXCLUDED_SEGMENTS for part in path.parts)

    def _source_uri(self, source: Path) -> str:
        try:
            return source.relative_to(self.workspace_path).as_posix()
        except ValueError:
            return source.as_posix()

    def _doc_id_for_source(self, source: Path) -> str:
        return self._source_uri(source)

    def _point_id_for_chunk(self, doc_id: str, ordinal: int) -> str:
        identity = f"dope-context:{self.workspace_id}:{doc_id}:{ordinal}"
        return str(uuid.uuid5(uuid.NAMESPACE_URL, identity))

    def _validate_chunk_ordinals(
        self, chunks: List[DocumentChunk], source: Path
    ) -> None:
        ordinals = [chunk.metadata.chunk_index for chunk in chunks]
        expected = list(range(len(chunks)))
        if ordinals != expected:
            raise ValueError(
                f"Chunk ordinal mismatch for {source}: expected {expected}, got {ordinals}"
            )

    def _discover_documents(
        self, include_patterns: Optional[List[str]] = None
    ) -> List[Path]:
        patterns = include_patterns or self.DEFAULT_INCLUDE_PATTERNS
        files: Set[Path] = set()
        for pattern in patterns:
            for candidate in self.workspace_path.glob(f"**/{pattern}"):
                if not candidate.is_file():
                    continue
                relative = candidate.relative_to(self.workspace_path)
                if not self._should_exclude(relative):
                    files.add(candidate.resolve())

        discovered = sorted(files, key=lambda path: path.as_posix())
        logger.info(
            "Discovered %s docs files in %s", len(discovered), self.workspace_path
        )
        return discovered

    def _build_chunk_payload(
        self,
        source: Path,
        chunk: DocumentChunk,
        *,
        doc_id: str,
        point_id: str,
        embed_model: str,
        embed_dimension: int,
        embed_dtype: str,
        token_count: int,
    ) -> Dict[str, Any]:
        metadata = chunk.metadata
        source_path = source.as_posix()
        source_uri = self._source_uri(source)
        ordinal = int(metadata.chunk_index)
        instance_id = os.getenv("DOPEMUX_WORKSPACE_ID", self.workspace_id)
        fingerprint = index_fingerprint(
            model=embed_model,
            output_dimension=embed_dimension,
            output_dtype=embed_dtype,
            chunker_version=CHUNKER_VERSION,
        )
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
            "chunk_id": point_id,
            "ordinal": ordinal,
            "embed_model": embed_model,
            "embed_dimension": embed_dimension,
            "embed_dtype": embed_dtype,
            "index_schema_version": INDEX_SCHEMA_VERSION,
            "index_fingerprint": fingerprint,
            "chunker_version": CHUNKER_VERSION,
            "chunk_index": ordinal,
            "char_count": metadata.char_count,
            "token_count": token_count,
            "source_hash": metadata.source_hash,
            "content_hash": metadata.content_hash,
            "section_hierarchy": metadata.section_hierarchy,
            "header_level": metadata.header_level,
            "has_code_blocks": metadata.has_code_blocks,
            "complexity_estimate": metadata.complexity_estimate,
            "parent_section": metadata.parent_section,
            "section_type": metadata.section_type,
        }

    async def _existing_point_ids(self, source: Path) -> Set[str]:
        """Find only exact-path/URI matches, never same-basename guesses."""

        existing_payloads = await self.doc_search.get_all_payloads()
        absolute = source.as_posix()
        uri = self._source_uri(source)
        point_ids: Set[str] = set()

        for payload in existing_payloads or []:
            point_id = payload.get("id")
            if not point_id:
                continue
            if payload.get("source_path") == absolute or payload.get("source_uri") == uri:
                point_ids.add(str(point_id))
        return point_ids

    async def _index_document(self, file_path: Path) -> Tuple[int, float, int]:
        processed_chunks = self.processor.process_document(
            file_path=str(file_path),
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            use_structure_aware=True,
        )
        chunks = [chunk for chunk in processed_chunks if chunk.text.strip()]
        if not chunks:
            return 0, 0.0, 0

        self._validate_chunk_ordinals(chunks, file_path)
        embed_response = await self.embedder.embed_document(
            chunks=[chunk.text for chunk in chunks],
            model=self.embedder.default_model,
            input_type="document",
            output_dimension=self.embedder.output_dimension,
            output_dtype=self.embedder.output_dtype,
        )
        if len(embed_response.embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch for {file_path}: "
                f"{len(embed_response.embeddings)} vectors for {len(chunks)} chunks"
            )

        doc_id = self._doc_id_for_source(file_path)
        existing_ids = await self._existing_point_ids(file_path)
        new_ids: Set[str] = set()
        points = []

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embed_response.embeddings)
        ):
            ordinal = int(chunk.metadata.chunk_index)
            point_id = self._point_id_for_chunk(doc_id, ordinal)
            new_ids.add(point_id)
            token_count = (
                embed_response.chunk_tokens[index]
                if index < len(embed_response.chunk_tokens)
                else chunk.metadata.token_count
            )
            payload = self._build_chunk_payload(
                file_path,
                chunk,
                doc_id=doc_id,
                point_id=point_id,
                embed_model=embed_response.model,
                embed_dimension=embed_response.output_dimension,
                embed_dtype=embed_response.output_dtype,
                token_count=token_count,
            )
            points.append((embedding, embedding, embedding, payload, point_id))

        # Upsert new deterministic points first. If embedding/upsert fails, the
        # previous document remains available instead of being pre-deleted.
        for start in range(0, len(points), self.qdrant_batch_size):
            await self.doc_search.insert_points_batch(
                points[start : start + self.qdrant_batch_size]
            )

        stale_ids = sorted(existing_ids - new_ids)
        if stale_ids:
            await self.doc_search.delete_points(stale_ids)

        return len(points), embed_response.cost_usd, len(existing_ids)

    async def index_workspace(
        self, include_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        progress = DocsIndexingProgress(workspace=str(self.workspace_path))
        await self.doc_search.create_collection()
        docs_files = self._discover_documents(include_patterns=include_patterns)
        progress.total_documents = len(docs_files)

        for file_path in docs_files:
            try:
                chunk_count, cost_usd, replaced = await self._index_document(file_path)
            except Exception as exc:
                progress.error_documents += 1
                progress.errors.append(
                    {"file": file_path.as_posix(), "error": str(exc)}
                )
                logger.warning("Document indexing failed for %s: %s", file_path, exc)
                continue

            if chunk_count == 0:
                progress.skipped_documents += 1
                continue

            progress.indexed_documents += 1
            progress.indexed_chunks += chunk_count
            progress.replaced_chunks += replaced
            progress.total_cost_usd += cost_usd

        progress.ended_at = datetime.now()
        return progress.summary()
