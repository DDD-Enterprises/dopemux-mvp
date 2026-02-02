#!/usr/bin/env python3
"""
Index codebase and documentation for semantic search.

This script indexes both code files and documentation using the dope-context system.
"""
import asyncio

import logging

logger = logging.getLogger(__name__)

import os
import sys
from pathlib import Path

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "dope-context"))

from src.pipeline.indexing_pipeline import IndexingPipeline, IndexingConfig
from src.preprocessing.code_chunker import CodeChunker, ChunkingConfig
from src.context.claude_generator import ClaudeContextGenerator
from src.embeddings.voyage_embedder import VoyageEmbedder
from src.search.dense_search import MultiVectorSearch


async def index_code_and_docs():
    """Index both code and documentation."""
    workspace = Path("/Users/hue/code/dopemux-mvp")

    logger.info(f"📁 Indexing workspace: {workspace}\n")

    # 1. Create embedder
    embedder = VoyageEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        default_model="voyage-code-3"
    )

    # === CODE INDEXING ===
    logger.info("=" * 60)
    logger.info("CODE INDEXING")
    logger.info("=" * 60 + "\n")

    # Create vector search for code
    code_search = MultiVectorSearch(
        collection_name="code_index_dopemux_mvp",
        url="localhost",
        port=6333,
    )
    await code_search.create_collection()
    logger.info("✅ Code collection created\n")

    # Create chunker with proper config
    chunking_config = ChunkingConfig(
        target_chunk_tokens=512,
        max_chunk_tokens=1024,
        min_chunk_tokens=128
    )
    chunker = CodeChunker(config=chunking_config)

    # Create context generator (optional - uses Claude for better snippets)
    context_generator = ClaudeContextGenerator(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # Configure code indexing
    code_config = IndexingConfig(
        workspace_path=workspace,
        include_patterns=["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"],
        exclude_patterns=[
            "*test*", "*__pycache__*", "*node_modules*",
            "*.pyc", "*venv*", "*dist*", "*build*", "*.git*"
        ],
        workspace_id=str(workspace)
    )

    # Create code pipeline
    code_pipeline = IndexingPipeline(
        chunker=chunker,
        context_generator=context_generator,
        embedder=embedder,
        vector_search=code_search,
        config=code_config
    )

    # Index code files
    logger.info("🔄 Indexing code files...\n")

    def code_progress_callback(progress):
        if progress.processed_files > 0:
            pct = progress.percentage_complete()
            logger.info(f"  Progress: {progress.processed_files}/{progress.total_files} files | {progress.indexed_chunks} chunks | {pct:.1f}% complete")

    code_result = await code_pipeline.index_workspace(progress_callback=code_progress_callback)
    logger.info(f"\n✅ Code indexing complete!")
    logger.info(f"   Files: {code_result.processed_files}")
    logger.info(f"   Chunks: {code_result.indexed_chunks}")
    logger.info(f"   Time: {code_result.elapsed_seconds():.1f}s")

    # === DOCS INDEXING ===
    logger.info("\n" + "=" * 60)
    logger.info("DOCUMENTATION INDEXING")
    logger.info("=" * 60 + "\n")

    # Create vector search for docs
    docs_search = MultiVectorSearch(
        collection_name="docs_index_dopemux_mvp",
        url="localhost",
        port=6333,
    )
    await docs_search.create_collection()
    logger.info("✅ Docs collection created\n")

    # Configure docs indexing
    docs_config = IndexingConfig(
        workspace_path=workspace,
        include_patterns=["*.md", "*.pdf", "*.html", "*.txt"],
        exclude_patterns=[
            "*test*", "*node_modules*", "*venv*", "*dist*",
            "*build*", "*.git*", "*__pycache__*"
        ],
        workspace_id=str(workspace)
    )

    # Create docs pipeline (reuse chunker and context generator)
    docs_pipeline = IndexingPipeline(
        chunker=chunker,
        context_generator=context_generator,
        embedder=embedder,
        vector_search=docs_search,
        config=docs_config
    )

    # Index docs files
    logger.info("🔄 Indexing documentation files...\n")

    def docs_progress_callback(progress):
        if progress.processed_files > 0:
            pct = progress.percentage_complete()
            logger.info(f"  Progress: {progress.processed_files}/{progress.total_files} files | {progress.indexed_chunks} chunks | {pct:.1f}% complete")

    docs_result = await docs_pipeline.index_workspace(progress_callback=docs_progress_callback)
    logger.info(f"\n✅ Documentation indexing complete!")
    logger.info(f"   Files: {docs_result.processed_files}")
    logger.info(f"   Chunks: {docs_result.indexed_chunks}")
    logger.info(f"   Time: {docs_result.elapsed_seconds():.1f}s")

    # === SUMMARY ===
    logger.info("\n" + "=" * 60)
    logger.info("INDEXING SUMMARY")
    logger.info("=" * 60)
    cost = embedder.get_cost_summary()
    logger.info(f"\n💰 Total Cost: ${cost['total_cost_usd']:.4f}")
    logger.info(f"📊 Total Tokens: {cost['total_tokens']:,}")
    logger.info("\n✨ Both code and documentation are now searchable!")


if __name__ == "__main__":
    asyncio.run(index_code_and_docs())
