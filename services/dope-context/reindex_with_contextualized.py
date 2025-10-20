"""
Re-index dopemux-mvp with contextualized multi-vector embeddings.

Production indexing with:
- voyage-context-3 for content vectors (document-aware)
- voyage-code-3 for title/breadcrumb vectors
- Full incremental indexing support
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from src.preprocessing.code_chunker import CodeChunker
from src.context.openai_generator import OpenAIContextGenerator
from src.embeddings.voyage_embedder import VoyageEmbedder
from src.embeddings.contextualized_embedder import ContextualizedEmbedder
from src.search.dense_search import MultiVectorSearch
from src.pipeline.indexing_pipeline import IndexingPipeline, IndexingConfig, IndexingProgress
from src.utils.workspace import get_collection_names


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Re-index dopemux-mvp with contextualized embeddings."""

    logger.info("=" * 80)
    logger.info("DOPEMUX CODE RE-INDEXING WITH CONTEXTUALIZED EMBEDDINGS")
    logger.info("=" * 80)

    # Check API keys
    voyage_key = os.getenv("VOYAGE_API_KEY")
    if not voyage_key:
        logger.error("❌ VOYAGE_API_KEY not set")
        sys.exit(1)

    # Context generation: Use Grok (FREE!) or skip
    # TODO: Integrate Zen MCP for grok-4-fast context generation
    # For now, skip context generation - contextualized embeddings are the main benefit!
    context_generator = None
    logger.info("ℹ️  Skipping AI context generation (using simple fallback)")
    logger.info("   → Contextualized embeddings still provide 14.24% accuracy improvement!")

    # Workspace setup
    workspace_path = Path("/Users/hue/code/dopemux-mvp")
    code_collection, _ = get_collection_names(workspace_path)

    logger.info(f"\n📁 Workspace: {workspace_path}")
    logger.info(f"📦 Collection: {code_collection}")

    # Initialize components
    logger.info("\n🔧 Initializing pipeline components...")

    chunker = CodeChunker()
    standard_embedder = VoyageEmbedder(api_key=voyage_key)
    contextualized_embedder = ContextualizedEmbedder(api_key=voyage_key)

    vector_search = MultiVectorSearch(
        collection_name=code_collection,
        url="localhost",
        port=6333,
        vector_size=1024,
    )

    # Create fresh collection
    logger.info("\n📦 Creating fresh collection...")
    await vector_search.create_collection()

    # Configure pipeline
    config = IndexingConfig(
        workspace_path=workspace_path,
        include_patterns=["*.py", "*.ts", "*.js", "*.tsx"],
        exclude_patterns=[
            "*test*", "*__pycache__*", "*.pyc",
            "*/venv/*", "*/.venv/*", "*/site-packages/*",
            "*/archive/*", "*/ARCHIVED_*/*", "*/backup/*",
            "*/processing_inputs/*", "*/.worktrees/*",
            "*/node_modules/*", "*/dist/*", "*/build/*",
        ],
        max_files=100,  # Start with 100 files
        skip_context_generation=(context_generator is None),
        workspace_id=str(workspace_path),
        context_batch_size=10,
        embedding_batch_size=8,
        qdrant_batch_size=100,
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
        logger.info(
            f"📊 Progress: {progress.processed_files}/{progress.total_files} files | "
            f"{progress.indexed_chunks}/{progress.total_chunks} chunks ({pct:.1f}%) | "
            f"Errors: {progress.errors} | "
            f"Cost: ${progress.total_cost_usd:.4f}"
        )

    # Index workspace
    logger.info("\n🚀 Starting indexing...")
    logger.info("=" * 80)

    try:
        final_progress = await pipeline.index_workspace(
            progress_callback=show_progress,
        )

        logger.info("\n" + "=" * 80)
        logger.info("✅ INDEXING COMPLETE!")
        logger.info("=" * 80)

        logger.info(f"\n📊 Final Statistics:")
        logger.info(f"   Files processed: {final_progress.processed_files}")
        logger.info(f"   Chunks indexed: {final_progress.indexed_chunks}")
        logger.info(f"   Errors: {final_progress.errors}")
        logger.info(f"   Duration: {final_progress.elapsed_seconds():.1f}s")
        logger.info(f"   Total cost: ${final_progress.total_cost_usd:.4f}")

        # Cost breakdown
        cost_summary = pipeline.get_cost_summary()
        logger.info(f"\n💰 Cost Breakdown:")
        logger.info(f"   Context generation: ${cost_summary['context_generation']['cost_usd']:.4f}")
        logger.info(f"   Embeddings (total): ${cost_summary['embeddings']['cost_usd']:.4f}")
        logger.info(f"     - Contextualized: {cost_summary['embeddings']['contextualized_summary']}")
        logger.info(f"     - Standard: {cost_summary['embeddings']['standard_summary']}")

        # Collection info
        info = await vector_search.get_collection_info()
        logger.info(f"\n📦 Collection Status:")
        logger.info(f"   Name: {info['name']}")
        logger.info(f"   Vectors: {info['vectors_count']}")
        logger.info(f"   Status: {info['status']}")

        logger.info("\n🎉 Re-indexing complete! Your code is now searchable with contextualized embeddings.")

    except Exception as e:
        logger.error(f"\n❌ Indexing failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
