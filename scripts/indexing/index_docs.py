#!/usr/bin/env python3
"""Index all documentation files (Markdown, PDFs) for semantic search."""

import asyncio
import sys
import os
import hashlib
import logging
from pathlib import Path

# Add dope-context to path
dope_context_path = Path("/Users/hue/code/code-audit/services/dope-context")
sys.path.insert(0, str(dope_context_path))

from src.pipeline.docs_pipeline import DocIndexingPipeline
from src.embeddings.contextualized_embedder import ContextualizedEmbedder
from src.search.docs_search import DocumentSearch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Index all documentation files."""

    workspace_path = Path("/Users/hue/code/code-audit")

    # API key
    voyage_api_key = os.getenv("VOYAGE_API_KEY")
    if not voyage_api_key:
        logger.error("❌ Error: VOYAGE_API_KEY not set")
        return 1

    logger.info("=" * 70)
    logger.info("📚 DOCUMENTATION INDEXING")
    logger.info("=" * 70)
    logger.info(f"📁 Workspace: {workspace_path}")
    logger.info(f"🔑 Voyage API: ✅ Configured")
    logger.info()

    # Initialize components
    logger.info("⚙️  Initializing components...")

    # Contextualized embedder for docs
    embedder = ContextualizedEmbedder(
        api_key=voyage_api_key,
        cache_ttl_hours=24,
        rate_limit_rpm=2000  # Voyage voyage-context-3 limit
    )
    logger.info("   ✅ ContextualizedEmbedder (voyage-context-3, 2000 RPM)")

    # Docs search (Qdrant)
    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    # Use hash-based collection name (matches MCP)
    workspace_hash = hashlib.md5(str(workspace_path).encode()).hexdigest()[:8]
    collection_name = f"docs_{workspace_hash}"

    docs_search = DocumentSearch(
        collection_name=collection_name,
        url=qdrant_url,
        port=qdrant_port
    )
    logger.info(f"   ✅ DocumentSearch (collection: {collection_name})")

    # Docs pipeline
    pipeline = DocIndexingPipeline(
        embedder=embedder,
        doc_search=docs_search,  # Note: parameter is doc_search not docs_search
        workspace_path=workspace_path,
        workspace_id="code-audit"
    )
    logger.info("   ✅ DocIndexingPipeline")
    logger.info()

    # Indexing configuration
    include_patterns = [
        "*.md",      # Markdown
        "*.pdf",     # PDFs
        "*.txt",     # Text
        "*.rst",     # reStructuredText
    ]

    logger.info("📋 Indexing Configuration:")
    logger.info(f"   Include: {', '.join(include_patterns)}")
    logger.info(f"   Max files: ALL (no limit)")
    logger.info(f"   Model: voyage-context-3 (optimized for documents)")
    logger.info()

    # Index docs
    logger.info("🔄 Indexing documentation files (5-10 minutes)...")
    logger.info()

    try:
        result = await pipeline.index_workspace(
            include_patterns=include_patterns
        )

        logger.info()
        logger.info("=" * 70)
        logger.info("✅ DOCUMENTATION INDEXING COMPLETE!")
        logger.info("=" * 70)
        logger.info(f"Files processed: {result.get('files_processed', 0)}")
        logger.info(f"Chunks indexed: {result.get('chunks_indexed', 0)}")
        logger.error(f"Errors: {result.get('errors', 0)}")
        logger.info()

        # Cost summary
        logger.info("💰 Cost Summary:")
        logger.info(f"   Embeddings: ${result.get('embedding_cost', 0):.4f}")
        logger.info()

        logger.info("🎯 Next Steps:")
        logger.info("   1. Test: mcp__dope-context__docs_search('architecture')")
        logger.info("   2. Unified: mcp__dope-context__search_all('features')")
        logger.info()

        return 0

    except Exception as e:
        logger.info()
        logger.info("=" * 70)
        logger.error("❌ INDEXING FAILED")
        logger.info("=" * 70)
        logger.error(f"Error: {e}")
        logger.exception("Docs indexing failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
