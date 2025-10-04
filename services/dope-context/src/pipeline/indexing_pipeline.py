"""
Indexing Pipeline Orchestrator - Task 7
Coordinates all components to build code index from source files.

Pipeline Flow:
File Discovery → Code Chunking → Context Generation →
Multi-Vector Embedding → Qdrant Storage

With: Batching, progress tracking, cost monitoring, error handling
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from uuid import uuid4

from ..preprocessing.code_chunker import CodeChunker, CodeChunk, ChunkingConfig
from ..context.claude_generator import ClaudeContextGenerator
from ..embeddings.voyage_embedder import VoyageEmbedder
from ..search.dense_search import MultiVectorSearch


logger = logging.getLogger(__name__)


@dataclass
class IndexingConfig:
    """Configuration for indexing pipeline."""

    # File discovery
    workspace_path: Path
    include_patterns: List[str] = field(
        default_factory=lambda: ["*.py", "*.js", "*.ts", "*.tsx"]
    )
    exclude_patterns: List[str] = field(
        default_factory=lambda: ["*test*", "*__pycache__*", "*.pyc"]
    )
    max_files: Optional[int] = None

    # Batching
    context_batch_size: int = 10  # Claude batch size
    embedding_batch_size: int = 8  # Voyage batch size
    qdrant_batch_size: int = 100  # Qdrant upsert batch

    # Pipeline control
    skip_context_generation: bool = False  # For testing
    workspace_id: str = "default"


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
    2. ClaudeContextGenerator - Contextual snippets
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
        context_generator: Optional[ClaudeContextGenerator],
        embedder: VoyageEmbedder,
        vector_search: MultiVectorSearch,
        config: IndexingConfig,
    ):
        """
        Initialize indexing pipeline.

        Args:
            chunker: Code chunker instance
            context_generator: Context generator (optional for testing)
            embedder: Voyage embedder instance
            vector_search: Multi-vector search instance
            config: Pipeline configuration
        """
        self.chunker = chunker
        self.context_generator = context_generator
        self.embedder = embedder
        self.vector_search = vector_search
        self.config = config

        self.progress = IndexingProgress()

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

    async def _process_file(self, file_path: Path) -> List[Dict]:
        """
        Process single file through pipeline.

        Returns:
            List of indexed documents ready for Qdrant
        """
        try:
            # 1. Chunk file
            chunks = self.chunker.chunk_file(file_path)

            if not chunks:
                logger.debug(f"No chunks extracted from {file_path}")
                return []

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

            # 4. Embed all texts (batched)
            content_embeddings = await self.embedder.embed_batch(
                texts=content_texts,
                model="voyage-code-3",
                input_type="document",
            )

            title_embeddings = await self.embedder.embed_batch(
                texts=title_texts,
                model="voyage-code-3",
                input_type="document",
            )

            breadcrumb_embeddings = await self.embedder.embed_batch(
                texts=breadcrumb_texts,
                model="voyage-code-3",
                input_type="document",
            )

            # Track embedding cost
            embedding_cost = sum(
                resp.cost_usd
                for resp in (
                    content_embeddings + title_embeddings + breadcrumb_embeddings
                )
            )
            self.progress.embedding_cost_usd += embedding_cost

            # 5. Create documents for Qdrant
            documents = []
            for i, chunk in enumerate(chunks):
                doc = {
                    "content_vector": content_embeddings[i].embedding,
                    "title_vector": title_embeddings[i].embedding,
                    "breadcrumb_vector": breadcrumb_embeddings[i].embedding,
                    "payload": {
                        "file_path": str(file_path),
                        "function_name": chunk.symbol_name,
                        "language": chunk.language,
                        "raw_code": chunk.content,
                        "context_snippet": contexts[i],
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "complexity": chunk.complexity,
                        "workspace_id": self.config.workspace_id,
                    },
                    "point_id": str(uuid4()),  # Qdrant requires UUID or int
                }
                documents.append(doc)

            self.progress.total_chunks += len(chunks)
            return documents

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            self.progress.errors += 1
            return []

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

        # 2. Ensure collection exists
        await self.vector_search.create_collection()

        # 3. Process files with rate limiting
        all_documents = []

        # Rate limiting: Anthropic API limits
        # - 50 requests/minute = 1.2s between requests
        # - 50k tokens/minute = ~833 tokens/sec
        # Conservative: 2s delay per file ensures we stay well under both limits
        delay_per_file = 2.0  # seconds

        for idx, file_path in enumerate(files):
            logger.info(f"Processing [{idx+1}/{len(files)}] {file_path.name}...")

            docs = await self._process_file(file_path)
            all_documents.extend(docs)

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
        docs = await self._process_file(file_path)

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

        return len(docs)

    def get_progress(self) -> IndexingProgress:
        """Get current progress."""
        return self.progress

    def get_cost_summary(self) -> Dict:
        """Get detailed cost breakdown."""
        return {
            "context_generation": {
                "cost_usd": round(self.progress.context_cost_usd, 4),
                "summary": (
                    self.context_generator.get_cost_summary()
                    if self.context_generator
                    else {}
                ),
            },
            "embeddings": {
                "cost_usd": round(self.progress.embedding_cost_usd, 4),
                "summary": self.embedder.get_cost_summary(),
            },
            "total_cost_usd": round(self.progress.total_cost_usd, 4),
        }


# Example usage
async def main():
    """Example usage of IndexingPipeline."""
    import os

    # Initialize components
    chunker = CodeChunker()

    context_generator = ClaudeContextGenerator(
        api_key=os.getenv("ANTHROPIC_API_KEY", "test"),
    )

    embedder = VoyageEmbedder(
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
        embedder=embedder,
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

    print(f"\nIndexing complete!")
    print(f"Summary: {final_progress.summary()}")
    print(f"Costs: {pipeline.get_cost_summary()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
