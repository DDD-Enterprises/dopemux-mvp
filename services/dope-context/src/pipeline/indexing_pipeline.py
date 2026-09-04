"""
Indexing Pipeline Orchestrator - Task 7
Coordinates all components to build code index from source files.

Pipeline Flow:
File Discovery → Code Chunking → Context Generation →
Multi-Vector Embedding → Qdrant Storage

With: Batching, progress tracking, cost monitoring, error handling
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..embeddings.contextualized_embedder import ContextualizedEmbedder
from ..embeddings.model_registry import build_collection_manifest

# OpenAIContextGenerator imported inside the example function to avoid import-time issues
from ..embeddings.voyage_embedder import VoyageEmbedder
from ..index_profile import (
    CollectionProfile,
    build_code_collection_profile,
    workspace_identity_from_path,
)
from ..preprocessing.code_chunker import ChunkingConfig, CodeChunk, CodeChunker
from ..search.dense_search import MultiVectorSearch
from ..sync.incremental_indexer import ChunkMetadata, ChunkSnapshot, IncrementalIndexer

logger = logging.getLogger(__name__)

CODE_CHUNKER_VERSION = "code_chunker.v1"


@dataclass
class IndexingConfig:
    """Configuration for indexing pipeline."""

    # File discovery
    workspace_path: Path
    include_patterns: List[str] = field(
        default_factory=lambda: ["*.py", "*.js", "*.ts", "*.tsx"]
    )
    exclude_patterns: List[str] = field(
        default_factory=lambda: [
            "*test*",
            "*__pycache__*",
            "*.pyc",
            "*/venv/*",
            "*/.venv/*",
            "*/site-packages/*",
            "*/archive/*",
            "*/ARCHIVED_*/*",
            "*/backup/*",
            "*/processing_inputs/*",
            "*/.worktrees/*",
            "*/node_modules/*",
            "*/dist/*",
            "*/build/*",
        ]
    )
    max_files: Optional[int] = None

    # Batching
    context_batch_size: int = 10  # Claude batch size
    embedding_batch_size: int = 8  # Voyage batch size
    qdrant_batch_size: int = 100  # Qdrant upsert batch

    # Pipeline control
    skip_context_generation: bool = False  # For testing
    # Empty means derive from workspace_path (never hard-code "default" for identity).
    workspace_id: str = ""


@dataclass
class IndexingProgress:
    """Track indexing progress for ADHD users."""

    total_files: int = 0
    processed_files: int = 0
    total_chunks: int = 0
    indexed_chunks: int = 0
    errors: int = 0

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Costs
    total_cost_usd: float = 0.0
    context_cost_usd: float = 0.0
    embedding_cost_usd: float = 0.0

    def percentage_complete(self) -> float:
        """Get completion percentage."""
        if self.total_chunks == 0:
            return 0.0
        return (self.indexed_chunks / self.total_chunks) * 100

    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    def summary(self) -> Dict:
        """Get progress summary."""
        return {
            "files": f"{self.processed_files}/{self.total_files}",
            "chunks": f"{self.indexed_chunks}/{self.total_chunks}",
            "completion": f"{self.percentage_complete():.1f}%",
            "errors": self.errors,
            "elapsed_seconds": round(self.elapsed_seconds(), 1),
            "total_cost_usd": round(self.total_cost_usd, 4),
        }


class IndexingPipeline:
    """
    Orchestrates complete code indexing pipeline.

    Components:
    1. CodeChunker - AST-aware chunking
    2. OpenAIContextGenerator - Contextual snippets
    3. VoyageEmbedder - Multi-vector embeddings
    4. MultiVectorSearch - Qdrant storage

    Features:
    - Batched processing for efficiency
    - Progress tracking for ADHD users
    - Cost monitoring
    - Error handling with graceful degradation
    """

    def __init__(
        self,
        chunker: CodeChunker,
        context_generator: Optional[Any],
        standard_embedder: VoyageEmbedder,
        contextualized_embedder: ContextualizedEmbedder,
        vector_search: MultiVectorSearch,
        config: IndexingConfig,
    ):
        """
        Initialize indexing pipeline.

        Args:
            chunker: Code chunker instance
            context_generator: Context generator (optional for testing)
            standard_embedder: Voyage embedder for title/breadcrumb vectors
            contextualized_embedder: Contextualized embedder for content vector
            vector_search: Multi-vector search instance
            config: Pipeline configuration
        """
        self.chunker = chunker
        self.context_generator = context_generator
        self.standard_embedder = standard_embedder
        self.contextualized_embedder = contextualized_embedder
        self.vector_search = vector_search
        self.config = config
        if not self.config.workspace_id:
            self.config.workspace_id = workspace_identity_from_path(
                self.config.workspace_path
            )
        self.collection_profile: CollectionProfile = build_code_collection_profile()
        self.incremental_indexer = IncrementalIndexer(config.workspace_path)

        self.progress = IndexingProgress()

    def _generate_chunk_id(self, file_path: Path, chunk: CodeChunk) -> str:
        """
        Generate deterministic chunk ID for tracking.

        Uses hash of file_path + start_line + end_line for consistency.

        Args:
            file_path: File path
            chunk: Code chunk

        Returns:
            Deterministic chunk ID (UUID string)
        """
        import uuid

        id_str = f"{file_path}:{chunk.start_line}:{chunk.end_line}"
        # Create UUID from hash (first 16 bytes of SHA256)
        hash_bytes = hashlib.sha256(id_str.encode()).digest()[:16]
        return str(uuid.UUID(bytes=hash_bytes))

    def _discover_files(self) -> List[Path]:
        """
        Discover code files to index.

        Returns:
            List of file paths
        """
        files: Set[Path] = set()

        for pattern in self.config.include_patterns:
            matched = self.config.workspace_path.glob(f"**/{pattern}")
            files.update(matched)

        # Apply exclusions
        filtered_files = []
        for file in files:
            # Check if matches any exclude pattern
            exclude = False
            for pattern in self.config.exclude_patterns:
                if pattern.replace("*", "") in str(file):
                    exclude = True
                    break

            if not exclude:
                filtered_files.append(file)

        # Apply max_files limit
        if self.config.max_files:
            filtered_files = filtered_files[: self.config.max_files]

        logger.info(f"Discovered {len(filtered_files)} files to index")
        return filtered_files

    async def _process_file(
        self, file_path: Path
    ) -> tuple[List[Dict], List[ChunkMetadata]]:
        """
        Process single file through pipeline.

        Returns:
            Tuple of (documents for Qdrant, chunk metadata for tracking)
        """
        try:
            # 1. Chunk file
            chunks = self.chunker.chunk_file(file_path)

            if not chunks:
                logger.debug(f"No chunks extracted from {file_path}")
                return [], []

            logger.debug(f"Extracted {len(chunks)} chunks from {file_path}")

            # 2. Generate contexts (batched)
            contexts = []
            if self.context_generator and not self.config.skip_context_generation:
                file_paths = [str(file_path)] * len(chunks)

                context_responses = (
                    await self.context_generator.generate_contexts_batch(
                        chunks=chunks,
                        file_paths=file_paths,
                    )
                )

                contexts = [resp.context for resp in context_responses]

                # Track context cost
                context_cost = sum(resp.cost_usd for resp in context_responses)
                self.progress.context_cost_usd += context_cost

            else:
                # No context generation - use simple fallback
                contexts = [
                    f"Code from {file_path} (lines {chunk.start_line}-{chunk.end_line})"
                    for chunk in chunks
                ]

            # 3. Prepare texts for embedding
            # Content: contextualized code
            content_texts = [
                f"{context}\n\n{chunk.content}"
                for context, chunk in zip(contexts, chunks)
            ]

            # Titles: function/class names
            title_texts = [
                chunk.symbol_name or f"{chunk.chunk_type}_{chunk.start_line}"
                for chunk in chunks
            ]

            # Breadcrumbs: file path + symbol
            breadcrumb_texts = [
                (
                    f"{file_path}.{chunk.symbol_name}"
                    if chunk.symbol_name
                    else f"{file_path}:{chunk.start_line}"
                )
                for chunk in chunks
            ]

            # 4. Embed all texts using canonical vector profiles (index side).
            content_profile = self.collection_profile.content()
            title_profile = self.collection_profile.title()
            breadcrumb_profile = self.collection_profile.breadcrumb()

            # D1: content_vec is a flat-endpoint vector, same as title and
            # breadcrumb. Dispatch on the profile's endpoint rather than
            # assuming the contextualized embedder — passing a flat code model
            # to contextualized_embed is a hard API rejection, since that
            # endpoint only accepts voyage-context-3/4.
            if content_profile.endpoint == "embeddings":
                content_embeddings = await self.standard_embedder.embed_batch(
                    texts=content_texts,
                    model=content_profile.model,
                    input_type=content_profile.index_input_type,
                    output_dimension=content_profile.dimension,
                    output_dtype=content_profile.dtype,
                )
            else:
                content_response = await self.contextualized_embedder.embed_document(
                    chunks=content_texts,
                    model=content_profile.model,
                    input_type=content_profile.index_input_type,
                    output_dimension=content_profile.dimension,
                    output_dtype=content_profile.dtype,
                )
                content_embeddings = content_response.embeddings

            title_embeddings = await self.standard_embedder.embed_batch(
                texts=title_texts,
                model=title_profile.model,
                input_type=title_profile.index_input_type,
                output_dimension=title_profile.dimension,
                output_dtype=title_profile.dtype,
            )

            breadcrumb_embeddings = await self.standard_embedder.embed_batch(
                texts=breadcrumb_texts,
                model=breadcrumb_profile.model,
                input_type=breadcrumb_profile.index_input_type,
                output_dimension=breadcrumb_profile.dimension,
                output_dtype=breadcrumb_profile.dtype,
            )

            # Track embedding cost
            embedding_cost = (
                content_response.cost_usd
                + sum(resp.cost_usd for resp in title_embeddings)
                + sum(resp.cost_usd for resp in breadcrumb_embeddings)
            )
            self.progress.embedding_cost_usd += embedding_cost

            # 5. Create documents for Qdrant with deterministic chunk IDs
            documents = []
            chunk_metadata = []

            for i, chunk in enumerate(chunks):
                # Generate deterministic chunk ID for incremental updates
                chunk_id = self._generate_chunk_id(file_path, chunk)

                provenance = self.collection_profile.provenance_fields()
                doc = {
                    "content_vector": content_embeddings[i],  # Already List[float]
                    "title_vector": title_embeddings[i].embedding,
                    "breadcrumb_vector": breadcrumb_embeddings[i].embedding,
                    "payload": {
                        "file_path": str(file_path),
                        "source_path": str(file_path),
                        "function_name": chunk.symbol_name,
                        "language": chunk.language,
                        "raw_code": chunk.content,
                        "context_snippet": contexts[i],
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "complexity": chunk.complexity,
                        "workspace_id": self.config.workspace_id,
                        **provenance,
                    },
                    "point_id": chunk_id,  # Deterministic ID for incremental updates
                }
                documents.append(doc)

                # Track chunk metadata for incremental indexing
                chunk_meta = ChunkMetadata(
                    chunk_id=chunk_id,
                    file_path=str(file_path.relative_to(self.config.workspace_path)),
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    content_hash=self.incremental_indexer._hash_content(chunk.content),
                    symbol_name=chunk.symbol_name,
                )
                chunk_metadata.append(chunk_meta)

            self.progress.total_chunks += len(chunks)
            return documents, chunk_metadata

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            self.progress.errors += 1
            return [], []

    async def index_workspace(
        self,
        progress_callback: Optional[callable] = None,
    ) -> IndexingProgress:
        """
        Index entire workspace.

        Args:
            progress_callback: Optional callback(progress) called periodically

        Returns:
            Final IndexingProgress
        """
        self.progress = IndexingProgress(start_time=datetime.now())

        # 1. Discover files
        files = self._discover_files()
        self.progress.total_files = len(files)

        if not files:
            logger.warning("No files found to index")
            self.progress.end_time = datetime.now()
            return self.progress

        # 2. Ensure collection exists.
        # The manifest records the CONTENT vector's model: it determines the
        # primary retrieval space. D1 collapsed code onto a single flat model,
        # so this is now the only model in play for a code collection.
        # Read it from the profile, not from an embedder instance — after D1
        # the contextualized embedder is not the one that produces content_vec,
        # and sourcing the manifest from it would record a model the collection
        # does not actually contain.
        content_profile = self.collection_profile.content()
        self.vector_search.manifest = build_collection_manifest(
            model=content_profile.model,
            output_dimension=content_profile.dimension,
            output_dtype=content_profile.dtype,
            chunker_version=CODE_CHUNKER_VERSION,
        )
        await self.vector_search.create_collection()

        # 3. Initialize chunk snapshot for incremental indexing
        chunk_snapshot = ChunkSnapshot(workspace_path=str(self.config.workspace_path))

        # 4. Process files with rate limiting
        all_documents = []

        # Rate limiting: Anthropic API limits
        # - 50 requests/minute = 1.2s between requests
        # - 50k tokens/minute = ~833 tokens/sec
        # Conservative: 2s delay per file ensures we stay well under both limits
        delay_per_file = 2.0  # seconds

        for idx, file_path in enumerate(files):
            logger.info(f"Processing [{idx+1}/{len(files)}] {file_path.name}...")

            docs, chunk_meta = await self._process_file(file_path)
            all_documents.extend(docs)

            # Update chunk snapshot with file metadata
            if chunk_meta:
                file_hash = self.incremental_indexer._hash_content(
                    file_path.read_text(encoding="utf-8")
                )
                relative_path = str(file_path.relative_to(self.config.workspace_path))

                self.incremental_indexer.update_chunk_mapping(
                    snapshot=chunk_snapshot,
                    file_path=relative_path,
                    file_hash=file_hash,
                    chunks=chunk_meta,
                )

            self.progress.processed_files += 1

            # Rate limiting delay (except for last file)
            if idx < len(files) - 1:
                await asyncio.sleep(delay_per_file)

            # Progress callback
            if progress_callback:
                progress_callback(self.progress)

        # 4. Batch insert into Qdrant
        logger.info(f"Inserting {len(all_documents)} chunks into Qdrant...")

        for i in range(0, len(all_documents), self.config.qdrant_batch_size):
            batch = all_documents[i : i + self.config.qdrant_batch_size]

            # Prepare batch
            batch_points = [
                (
                    doc["content_vector"],
                    doc["title_vector"],
                    doc["breadcrumb_vector"],
                    doc["payload"],
                    doc["point_id"],
                )
                for doc in batch
            ]

            # Insert
            await self.vector_search.insert_points_batch(batch_points)

            self.progress.indexed_chunks += len(batch)

            # Progress callback
            if progress_callback:
                progress_callback(self.progress)

        # 5. Calculate total cost
        self.progress.total_cost_usd = (
            self.progress.context_cost_usd + self.progress.embedding_cost_usd
        )

        self.progress.end_time = datetime.now()

        # 6. Save chunk snapshot for incremental updates
        self.incremental_indexer.save_chunk_snapshot(chunk_snapshot)
        logger.info(
            f"Saved chunk snapshot: {len(chunk_snapshot.files)} files, "
            f"{sum(len(f.chunks) for f in chunk_snapshot.files.values())} chunks"
        )

        logger.info(
            f"Indexing complete: {self.progress.indexed_chunks} chunks "
            f"from {self.progress.processed_files} files "
            f"(${self.progress.total_cost_usd:.4f})"
        )

        return self.progress

    async def index_single_file(
        self,
        file_path: Path,
    ) -> int:
        """
        Index a single file (for incremental updates).

        Args:
            file_path: Path to file

        Returns:
            Number of chunks indexed
        """
        docs, chunk_meta = await self._process_file(file_path)

        if docs:
            batch_points = [
                (
                    doc["content_vector"],
                    doc["title_vector"],
                    doc["breadcrumb_vector"],
                    doc["payload"],
                    doc["point_id"],
                )
                for doc in docs
            ]

            await self.vector_search.insert_points_batch(batch_points)

            # Update chunk snapshot for incremental indexing
            if chunk_meta:
                snapshot = self.incremental_indexer.load_chunk_snapshot()
                if snapshot is None:
                    snapshot = ChunkSnapshot(
                        workspace_path=str(self.config.workspace_path)
                    )

                file_hash = self.incremental_indexer._hash_content(
                    file_path.read_text(encoding="utf-8")
                )
                relative_path = str(file_path.relative_to(self.config.workspace_path))

                self.incremental_indexer.update_chunk_mapping(
                    snapshot=snapshot,
                    file_path=relative_path,
                    file_hash=file_hash,
                    chunks=chunk_meta,
                )

                self.incremental_indexer.save_chunk_snapshot(snapshot)

        return len(docs)

    def get_progress(self) -> IndexingProgress:
        """Get current progress."""
        return self.progress

    def _safe_get_cost_summary(self, obj) -> Dict:
        """Safely get cost summary from an object."""
        try:
            if hasattr(obj, "get_cost_summary"):
                return obj.get_cost_summary()
        except Exception as e:
            logger.warning(f"Failed to get cost summary: {e}")
        return {}

    def get_cost_summary(self) -> Dict:
        """Get detailed cost breakdown."""
        return {
            "context_generation": {
                "cost_usd": round(self.progress.context_cost_usd, 4),
                "summary": (
                    self._safe_get_cost_summary(self.context_generator)
                    if self.context_generator
                    else {}
                ),
            },
            "embeddings": {
                "cost_usd": round(self.progress.embedding_cost_usd, 4),
                "contextualized_summary": self.contextualized_embedder.get_cost_summary(),
                "standard_summary": self.standard_embedder.get_cost_summary(),
            },
            "total_cost_usd": round(self.progress.total_cost_usd, 4),
        }


# Example usage
if __name__ == "__main__":

    async def main():
        """Example usage of IndexingPipeline."""
        import os

        from ..context.openai_generator import OpenAIContextGenerator

        # Initialize components
        chunker = CodeChunker()

        context_generator = OpenAIContextGenerator(
            api_key=os.getenv("OPENAI_API_KEY", "test"),
        )

        # Standard embedder for title + breadcrumb
        standard_embedder = VoyageEmbedder(
            api_key=os.getenv("VOYAGE_API_KEY", "test"),
        )

        # Contextualized embedder: retained for docs and for a contextualized
        # rollback. The "14.24% better accuracy" claim previously noted here was
        # a vendor figure, not a measurement of this corpus; the Wave 0
        # benchmark (2026-09-04) measured the opposite for code retrieval, which
        # is why D1 moved code content_vec to the flat endpoint.
        contextualized_embedder = ContextualizedEmbedder(
            api_key=os.getenv("VOYAGE_API_KEY", "test"),
        )

        vector_search = MultiVectorSearch(
            collection_name="code_index",
        )

        # Configure pipeline
        config = IndexingConfig(
            workspace_path=Path("./src"),
            include_patterns=["*.py"],
            max_files=5,  # Limit for testing
            workspace_id="my-project",
        )

        # Create pipeline
        pipeline = IndexingPipeline(
            chunker=chunker,
            context_generator=context_generator,
            standard_embedder=standard_embedder,
            contextualized_embedder=contextualized_embedder,
            vector_search=vector_search,
            config=config,
        )

        # Progress callback
        def show_progress(progress: IndexingProgress):
            pct = progress.percentage_complete()
            print(
                f"Progress: {progress.processed_files}/{progress.total_files} files, "
                f"{progress.indexed_chunks}/{progress.total_chunks} chunks ({pct:.1f}%)"
            )

        # Index workspace
        final_progress = await pipeline.index_workspace(
            progress_callback=show_progress,
        )

        logger.info(f"\nIndexing complete!")
        logger.info(f"Summary: {final_progress.summary()}")
        logger.info(f"Costs: {pipeline.get_cost_summary()}")

    # Run the example
    asyncio.run(main())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
