#!/usr/bin/env python3
"""
Index code-audit workspace using dope-context IndexingPipeline.
Follows actual API from services/dope-context/src/pipeline/indexing_pipeline.py
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add dope-context to Python path
dope_context_path = Path("/Users/hue/code/code-audit/services/dope-context")
sys.path.insert(0, str(dope_context_path))

from src.pipeline.indexing_pipeline import IndexingPipeline, IndexingConfig, IndexingProgress
from src.preprocessing.code_chunker import CodeChunker
from src.context.claude_generator import ClaudeContextGenerator
from src.embeddings.voyage_embedder import VoyageEmbedder
from src.search.dense_search import MultiVectorSearch

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Index code-audit workspace."""

    # Workspace configuration
    workspace_path = Path("/Users/hue/code/code-audit")

    # API keys
    voyage_api_key = os.getenv("VOYAGE_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    if not voyage_api_key:
        print("❌ Error: VOYAGE_API_KEY not set")
        print("   Run: export VOYAGE_API_KEY='your-key'")
        return 1

    print("=" * 70)
    print("🚀 CODE-AUDIT WORKSPACE INDEXING")
    print("=" * 70)
    print(f"📁 Workspace: {workspace_path}")
    print(f"🔑 Voyage API: ✅ Configured")
    print(f"🔑 Anthropic API: {'✅ Configured' if anthropic_api_key else '⚠️  Optional (skipping context generation)'}")
    print()

    # Initialize components
    print("⚙️  Initializing pipeline components...")

    # 1. Code chunker (AST-aware with Tree-sitter)
    chunker = CodeChunker()
    print("   ✅ CodeChunker (500 tokens, 12% overlap, Tree-sitter)")

    # 2. Context generator (optional - requires Anthropic key)
    context_generator = None
    if anthropic_api_key:
        context_generator = ClaudeContextGenerator(
            api_key=anthropic_api_key,
            model="claude-3-5-haiku-20241022",  # Fast & cheap
            cache_ttl_hours=24
        )
        print("   ✅ ClaudeContextGenerator (claude-3-5-haiku)")
    else:
        print("   ⏭️  ClaudeContextGenerator skipped (no Anthropic key)")

    # 3. Voyage embedder (multi-vector with rate limiting)
    embedder = VoyageEmbedder(
        api_key=voyage_api_key,
        cache_ttl_hours=24,
        max_batch_size=128,        # Voyage API max
        rate_limit_rpm=2000,       # voyage-code-3 limit
        default_model="voyage-code-3"
    )
    print("   ✅ VoyageEmbedder (voyage-code-3, 2000 RPM, 128 batch)")

    # 4. Vector search (Qdrant multi-vector)
    # Use hash-based collection name (matches MCP workspace detection)
    import hashlib
    workspace_hash = hashlib.md5(str(workspace_path).encode()).hexdigest()[:8]
    collection_name = f"code_{workspace_hash}"

    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    vector_search = MultiVectorSearch(
        collection_name=collection_name,
        url=qdrant_url,
        port=qdrant_port
    )
    print(f"   ✅ MultiVectorSearch (Qdrant @ {qdrant_url}:{qdrant_port}, collection: {collection_name})")

    # 5. Indexing configuration
    config = IndexingConfig(
        workspace_path=workspace_path,
        include_patterns=["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"],
        exclude_patterns=[
            "*test*", "*__pycache__*", "*.pyc",
            "*/venv/*", "*/.venv/*", "*/node_modules/*",
            "*/dist/*", "*/build/*", "*/.git/*"
        ],
        max_files=None,  # Index ALL files (no limit)
        skip_context_generation=(context_generator is None),
        workspace_id="code-audit"
    )
    print(f"   ✅ IndexingConfig (indexing ALL files - no limit)")
    print()

    # Create pipeline
    pipeline = IndexingPipeline(
        chunker=chunker,
        context_generator=context_generator,
        embedder=embedder,
        vector_search=vector_search,
        config=config
    )

    print("📋 Indexing Configuration:")
    print(f"   Include: {', '.join(config.include_patterns)}")
    print(f"   Exclude: {', '.join(config.exclude_patterns[:3])}... ({len(config.exclude_patterns)} total)")
    print(f"   Max files: {'ALL (no limit)' if config.max_files is None else config.max_files}")
    print(f"   Multi-vector: content (0.7), title (0.2), breadcrumb (0.1)")
    print(f"   Context generation: {'✅ Enabled' if context_generator else '❌ Disabled'}")
    print()

    # Progress callback
    def show_progress(progress: IndexingProgress):
        """ADHD-optimized progress display."""
        pct = progress.percentage_complete()
        elapsed = progress.elapsed_seconds()

        print(
            f"   [{progress.processed_files}/{progress.total_files} files] "
            f"[{progress.indexed_chunks}/{progress.total_chunks} chunks] "
            f"[{pct:.1f}%] "
            f"[{elapsed:.0f}s] "
            f"[${progress.total_cost_usd:.3f}]",
            end="\r"
        )

    # Index workspace
    print("🔄 Indexing FULL workspace (this will take 10-20 minutes for all 331 files)...")
    print("   Progress will update every file...")
    print()

    try:
        final_progress = await pipeline.index_workspace(
            progress_callback=show_progress
        )

        # Clear progress line
        print(" " * 100, end="\r")

        # Final results
        print()
        print("=" * 70)
        print("✅ INDEXING COMPLETE!")
        print("=" * 70)
        print(f"Files processed: {final_progress.processed_files}/{final_progress.total_files}")
        print(f"Chunks indexed: {final_progress.indexed_chunks}/{final_progress.total_chunks}")
        print(f"Errors: {final_progress.errors}")
        print(f"Time elapsed: {final_progress.elapsed_seconds():.1f}s")
        print()

        # Cost breakdown
        cost_summary = pipeline.get_cost_summary()
        print("💰 Cost Breakdown:")
        print(f"   Context generation: ${cost_summary['context_generation']['cost_usd']:.4f}")
        print(f"   Embeddings: ${cost_summary['embeddings']['cost_usd']:.4f}")
        print(f"   Total: ${cost_summary['total_cost_usd']:.4f}")
        print()

        # Embedding stats
        emb_stats = cost_summary['embeddings']['summary']
        print("📊 Embedding Statistics:")
        print(f"   Requests: {emb_stats['total_requests']}")
        print(f"   Tokens: {emb_stats['total_tokens']:,}")
        print(f"   Cache hits: {emb_stats['cache_hits']} ({emb_stats['cache_rate']:.1%})")
        print()

        # Next steps
        print("🎯 Next Steps:")
        print("   1. Test search: mcp__dope-context__search_code('authentication')")
        print("   2. Index more: Edit script to increase max_files or remove limit")
        print("   3. Index docs: Use docs_pipeline.py for Markdown/PDF files")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ INDEXING FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        logger.exception("Indexing failed with exception:")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
