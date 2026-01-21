#!/usr/bin/env python3
"""
Index code-audit workspace for semantic search.
Follows dope-context best practices for embedding models, rate limits, and preprocessing.
"""

import asyncio
import sys
from pathlib import Path

# Add dope-context to path
dope_context_path = Path("/Users/hue/code/code-audit/services/dope-context")
sys.path.insert(0, str(dope_context_path))

from src.pipeline.indexing_pipeline import IndexingPipeline
from src.embeddings.voyage_embedder import VoyageEmbedder
from src.preprocessing.code_chunker import CodeChunker
from src.context.context_generator import ContextGenerator
from src.search.qdrant_store import QdrantVectorStore
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Index code-audit workspace with proper configuration."""

    # Configuration
    workspace_path = Path("/Users/hue/code/code-audit")

    # API keys
    voyage_api_key = os.getenv("VOYAGE_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")  # Optional for context generation

    if not voyage_api_key:
        logger.error("❌ Error: VOYAGE_API_KEY environment variable not set")
        logger.info("Export it: export VOYAGE_API_KEY='your-key'")
        return 1

    logger.info(f"🚀 Starting code-audit workspace indexing")
    logger.info(f"📁 Workspace: {workspace_path}")
    logger.info(f"🔑 Voyage API: {'✅ Set' if voyage_api_key else '❌ Missing'}")
    logger.info(f"🔑 Anthropic API: {'✅ Set (context generation enabled)' if anthropic_api_key else '⚠️  Missing (basic indexing only)'}")
    logger.info()

    # Initialize components with best practices
    logger.info("⚙️  Initializing components...")

    # Embedder with proper rate limiting
    embedder = VoyageEmbedder(
        api_key=voyage_api_key,
        cache_ttl_hours=24,           # Cache embeddings for 24h
        max_batch_size=128,           # Voyage API max
        rate_limit_rpm=2000,          # Voyage code-3 limit
        default_model="voyage-code-3" # Optimized for code
    )
    logger.info("  ✅ VoyageEmbedder initialized (voyage-code-3, 2000 RPM limit, 128 batch size)")

    # Vector store
    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    vector_store = QdrantVectorStore(
        url=qdrant_url,
        port=qdrant_port,
        workspace_path=workspace_path
    )
    logger.info(f"  ✅ QdrantVectorStore initialized ({qdrant_url}:{qdrant_port})")

    # Code chunker with AST awareness
    chunker = CodeChunker(
        chunk_size_tokens=500,        # Sweet spot from config
        overlap_percent=12,           # Recommended range
        use_tree_sitter=True          # AST-aware boundaries
    )
    logger.info("  ✅ CodeChunker initialized (500 tokens, 12% overlap, Tree-sitter enabled)")

    # Context generator (if Anthropic key available)
    context_generator = None
    if anthropic_api_key:
        context_generator = ContextGenerator(
            api_key=anthropic_api_key,
            model="claude-3-5-haiku-20241022"  # Fast, cheap for context generation
        )
        logger.info("  ✅ ContextGenerator initialized (claude-3-5-haiku)")
    else:
        logger.info("  ⚠️  ContextGenerator skipped (no Anthropic key)")

    # Indexing pipeline
    pipeline = IndexingPipeline(
        embedder=embedder,
        vector_store=vector_store,
        chunker=chunker,
        context_generator=context_generator
    )
    logger.info("  ✅ IndexingPipeline initialized")
    logger.info()

    # Indexing parameters
    include_patterns = [
        "*.py",      # Python code
        "*.ts",      # TypeScript
        "*.tsx",     # TypeScript React
        "*.js",      # JavaScript
        "*.jsx",     # JavaScript React
    ]

    exclude_patterns = [
        "*test*",           # Test files
        "*__pycache__*",    # Python cache
        "*.pyc",            # Compiled Python
        "*venv*",           # Virtual environments
        "*node_modules*",   # Node dependencies
        "*.min.js",         # Minified JS
        "*.map",            # Source maps
    ]

    # Start with limited batch for safety
    max_files = 100  # Index 100 files first, then expand

    logger.info(f"📝 Indexing configuration:")
    logger.info(f"  Include patterns: {', '.join(include_patterns)}")
    logger.info(f"  Exclude patterns: {', '.join(exclude_patterns)}")
    logger.info(f"  Max files (first batch): {max_files}")
    logger.info(f"  Embedding model: voyage-code-3")
    logger.info(f"  Rate limit: 2000 RPM")
    logger.info(f"  Batch size: 128 texts/request")
    logger.info(f"  Chunk size: 500 tokens with 12% overlap")
    logger.info(f"  Multi-vector: content (0.7), title (0.2), breadcrumb (0.1)")
    logger.info()

    # Index workspace
    logger.info("🔄 Starting indexing (this may take 5-15 minutes for 100 files)...")
    logger.info("   Progress will be shown as files are processed...")
    logger.info()

    try:
        result = await pipeline.index_workspace(
            workspace_path=workspace_path,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_files=max_files,
            show_progress=True  # ADHD optimization
        )

        # Results
        logger.info()
        logger.info("=" * 60)
        logger.info("✅ INDEXING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Files processed: {result.get('files_indexed', 0)}")
        logger.info(f"Total chunks: {result.get('total_chunks', 0)}")
        logger.info(f"Embedding cost: ${result.get('embedding_cost', 0):.4f}")
        logger.info(f"Context gen cost: ${result.get('context_cost', 0):.4f}")
        logger.info(f"Total cost: ${result.get('total_cost', 0):.4f}")
        logger.info()

        # Cost summary
        cost_summary = embedder.get_cost_summary()
        logger.info("📊 Embedding Statistics:")
        logger.info(f"  Total requests: {cost_summary['total_requests']}")
        logger.info(f"  Total tokens: {cost_summary['total_tokens']:,}")
        logger.info(f"  Cache hits: {cost_summary['cache_hits']} ({cost_summary['cache_rate']:.1%})")
        logger.info(f"  Total cost: ${cost_summary['total_cost_usd']:.4f}")
        logger.info()

        # Next steps
        logger.info("🎯 Next steps:")
        logger.info("  1. Test search: mcp__dope-context__search_code('authentication')")
        logger.info("  2. Index more files: Increase max_files to 500 or remove limit")
        logger.info("  3. Index docs: Run index_docs() for markdown/PDF documentation")
        logger.info()

        return 0

    except Exception as e:
        logger.info()
        logger.info("=" * 60)
        logger.error("❌ INDEXING FAILED")
        logger.info("=" * 60)
        logger.error(f"Error: {e}")
        logger.exception("Indexing failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
