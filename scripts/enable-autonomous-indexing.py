#!/usr/bin/env python3
"""
Enable Autonomous Indexing - ADHD Zero-Touch Setup

Starts autonomous file monitoring and indexing for code and docs.
Once enabled, all file changes automatically update the search index.

Usage:
    python scripts/enable-autonomous-indexing.py
"""

import asyncio
import sys
from pathlib import Path

# Add dope-context to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "dope-context" / "src"))

from autonomous.autonomous_controller import AutonomousController, AutonomousConfig
from core.workspace_detection import WorkspaceDetector
from pipeline.indexing_pipeline import IndexingPipeline
from preprocessing.code_chunker import CodeChunker
from context.openai_generator import OpenAIContextGenerator
from embeddings.voyage_embedder import VoyageEmbedder
from search.multi_vector_search import MultiVectorSearch
from enrichment.docs_chunker import DocsChunker
from search.docs_search import DocsVectorSearch


async def enable_autonomous_indexing():
    """Enable autonomous indexing for code and docs."""

    # Detect workspace
    workspace_path = Path.cwd().resolve()
    print(f"📂 Workspace: {workspace_path}")
    print()

    # Configuration
    code_config = AutonomousConfig(
        enabled=True,
        debounce_seconds=5.0,
        periodic_interval=600,  # 10 minutes
        include_patterns=["*.py", "*.js", "*.ts", "*.tsx"],
        exclude_patterns=["*test*", "*__pycache__*", "*node_modules*", "*.git*"]
    )

    docs_config = AutonomousConfig(
        enabled=True,
        debounce_seconds=5.0,
        periodic_interval=600,
        include_patterns=["*.md", "*.pdf", "*.html", "*.txt"],
        exclude_patterns=["*node_modules*", "*.git*", "*__pycache__*"]
    )

    # Get collection names
    detector = WorkspaceDetector()
    workspace_hash = detector.get_workspace_hash(workspace_path)
    code_collection = f"dopemux_code_{workspace_hash}"
    docs_collection = f"dopemux_docs_{workspace_hash}"

    print(f"📊 Collections:")
    print(f"   Code: {code_collection}")
    print(f"   Docs: {docs_collection}")
    print()

    try:
        # ========================================
        # CODE AUTONOMOUS INDEXING
        # ========================================

        print("🔧 Step 1/2: Enabling autonomous CODE indexing...")

        # Create code indexing pipeline
        code_vector_search = MultiVectorSearch(
            collection_name=code_collection,
            url="localhost",
            port=6333
        )

        code_chunker = CodeChunker()

        context_generator = None
        if os.getenv("OPENAI_API_KEY"):
            context_generator = OpenAIContextGenerator(
                api_key=os.getenv("OPENAI_API_KEY")
            )

        embedder = VoyageEmbedder(
            api_key=os.getenv("VOYAGE_API_KEY"),
            default_model="voyage-code-3"
        )

        from pipeline.indexing_pipeline import IndexingConfig

        indexing_config = IndexingConfig(
            workspace_path=workspace_path,
            include_patterns=code_config.include_patterns,
            exclude_patterns=code_config.exclude_patterns,
            workspace_id=str(workspace_path)
        )

        code_pipeline = IndexingPipeline(
            chunker=code_chunker,
            context_generator=context_generator,
            embedder=embedder,
            vector_search=code_vector_search,
            config=indexing_config
        )

        # Create callback for file changes
        async def code_index_callback(file_path: Path, changed_files=None):
            """Callback to reindex changed files."""
            try:
                print(f"📝 Reindexing: {file_path}")
                # Reindex just this file
                await code_pipeline.index_file(file_path)
                return True
            except Exception as e:
                print(f"❌ Reindex failed: {e}")
                return False

        # Create autonomous controller
        code_controller = AutonomousController(
            workspace_path=workspace_path,
            config=code_config,
            index_callback=code_index_callback
        )

        # Start autonomous monitoring
        await code_controller.start()

        print("✅ Autonomous CODE indexing enabled!")
        print(f"   Monitoring: {workspace_path}")
        print(f"   Patterns: {code_config.include_patterns}")
        print(f"   Debounce: {code_config.debounce_seconds}s")
        print(f"   Periodic sync: {code_config.periodic_interval}s")
        print()

        # ========================================
        # DOCS AUTONOMOUS INDEXING
        # ========================================

        print("🔧 Step 2/2: Enabling autonomous DOCS indexing...")

        # Create docs indexing pipeline
        docs_vector_search = DocsVectorSearch(
            collection_name=docs_collection,
            url="localhost",
            port=6333
        )

        docs_chunker = DocsChunker()

        # Reuse context generator and embedder (or create new ones)
        docs_embedder = VoyageEmbedder(
            api_key=os.getenv("VOYAGE_API_KEY"),
            default_model="voyage-context-3"  # Different model for docs
        )

        # Create callback for doc changes
        async def docs_index_callback(file_path: Path, changed_files=None):
            """Callback to reindex changed docs."""
            try:
                print(f"📄 Reindexing doc: {file_path}")
                # Reindex this document
                await docs_chunker.chunk_and_index(file_path, docs_vector_search, docs_embedder)
                return True
            except Exception as e:
                print(f"❌ Doc reindex failed: {e}")
                return False

        # Create autonomous controller for docs
        docs_controller = AutonomousController(
            workspace_path=workspace_path,
            config=docs_config,
            index_callback=docs_index_callback
        )

        # Start autonomous monitoring
        await docs_controller.start()

        print("✅ Autonomous DOCS indexing enabled!")
        print(f"   Monitoring: {workspace_path}")
        print(f"   Patterns: {docs_config.include_patterns}")
        print(f"   Debounce: {docs_config.debounce_seconds}s")
        print(f"   Periodic sync: {docs_config.periodic_interval}s")
        print()

        # ========================================
        # SUMMARY & VERIFICATION
        # ========================================

        print("=" * 60)
        print("🎉 AUTONOMOUS INDEXING ENABLED!")
        print("=" * 60)
        print()
        print("✨ Benefits:")
        print("   • Files auto-reindex 5s after save")
        print("   • Periodic sync every 10 minutes catches missed changes")
        print("   • Zero mental overhead - search always current")
        print("   • Interrupt-safe - background operation")
        print()
        print("🧠 ADHD Impact:")
        print("   • 100% cognitive load reduction for indexing")
        print("   • No 'did I reindex?' anxiety")
        print("   • Always-current search results")
        print()
        print("🔍 Try it:")
        print("   1. Edit any .py file and save")
        print("   2. Wait 5 seconds")
        print("   3. Search will include your changes!")
        print()
        print("⚙️  Controllers running in background...")
        print("   Press Ctrl+C to stop (not recommended - keep running!)")
        print()

        # Keep running indefinitely
        try:
            while True:
                await asyncio.sleep(60)
                # Optional: Print periodic status
                code_status = code_controller.get_status()
                docs_status = docs_controller.get_status()

                if code_status["pending_files"] > 0 or docs_status["pending_files"] > 0:
                    print(f"📊 Status: {code_status['pending_files']} code files, "
                          f"{docs_status['pending_files']} docs pending indexing")

        except KeyboardInterrupt:
            print("\n")
            print("🛑 Stopping autonomous indexing...")
            await code_controller.stop()
            await docs_controller.stop()
            print("✅ Stopped cleanly")

    except Exception as e:
        print(f"❌ Failed to enable autonomous indexing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import os

    # Verify environment
    if not os.getenv("VOYAGE_API_KEY"):
        print("❌ VOYAGE_API_KEY not set")
        print("   export VOYAGE_API_KEY='your-key'")
        sys.exit(1)

    print("🚀 Starting Autonomous Indexing Setup")
    print("=" * 60)
    print()

    asyncio.run(enable_autonomous_indexing())
