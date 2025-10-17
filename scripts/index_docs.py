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
        print("❌ Error: VOYAGE_API_KEY not set")
        return 1

    print("=" * 70)
    print("📚 DOCUMENTATION INDEXING")
    print("=" * 70)
    print(f"📁 Workspace: {workspace_path}")
    print(f"🔑 Voyage API: ✅ Configured")
    print()

    # Initialize components
    print("⚙️  Initializing components...")

    # Contextualized embedder for docs
    embedder = ContextualizedEmbedder(
        api_key=voyage_api_key,
        cache_ttl_hours=24,
        rate_limit_rpm=2000  # Voyage voyage-context-3 limit
    )
    print("   ✅ ContextualizedEmbedder (voyage-context-3, 2000 RPM)")

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
    print(f"   ✅ DocumentSearch (collection: {collection_name})")

    # Docs pipeline
    pipeline = DocIndexingPipeline(
        embedder=embedder,
        doc_search=docs_search,  # Note: parameter is doc_search not docs_search
        workspace_path=workspace_path,
        workspace_id="code-audit"
    )
    print("   ✅ DocIndexingPipeline")
    print()

    # Indexing configuration
    include_patterns = [
        "*.md",      # Markdown
        "*.pdf",     # PDFs
        "*.txt",     # Text
        "*.rst",     # reStructuredText
    ]

    print("📋 Indexing Configuration:")
    print(f"   Include: {', '.join(include_patterns)}")
    print(f"   Max files: ALL (no limit)")
    print(f"   Model: voyage-context-3 (optimized for documents)")
    print()

    # Index docs
    print("🔄 Indexing documentation files (5-10 minutes)...")
    print()

    try:
        result = await pipeline.index_workspace(
            include_patterns=include_patterns
        )

        print()
        print("=" * 70)
        print("✅ DOCUMENTATION INDEXING COMPLETE!")
        print("=" * 70)
        print(f"Files processed: {result.get('files_processed', 0)}")
        print(f"Chunks indexed: {result.get('chunks_indexed', 0)}")
        print(f"Errors: {result.get('errors', 0)}")
        print()

        # Cost summary
        print("💰 Cost Summary:")
        print(f"   Embeddings: ${result.get('embedding_cost', 0):.4f}")
        print()

        print("🎯 Next Steps:")
        print("   1. Test: mcp__dope-context__docs_search('architecture')")
        print("   2. Unified: mcp__dope-context__search_all('features')")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ INDEXING FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        logger.exception("Docs indexing failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
