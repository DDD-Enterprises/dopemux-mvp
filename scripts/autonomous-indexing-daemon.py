#!/usr/bin/env python3
"""
Autonomous Indexing Daemon - ADHD Zero-Touch Background Service

Runs autonomous file monitoring and indexing for code and docs as a background daemon.
Once started, all file changes automatically update the search index with zero manual intervention.

Features:
- File system watching (watchdog)
- 5-second debouncing (batches rapid saves)
- 10-minute periodic fallback (catches missed events)
- Graceful error handling
- Clean shutdown on Ctrl+C

Usage:
    # Start in foreground (see logs)
    python scripts/autonomous-indexing-daemon.py

    # Start in background
    nohup python scripts/autonomous-indexing-daemon.py > logs/autonomous-indexing.log 2>&1 &

    # Check if running
    ps aux | grep autonomous-indexing-daemon

    # Stop
    pkill -f autonomous-indexing-daemon
"""

import asyncio
import hashlib
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# Setup paths for imports
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DOPE_CONTEXT_SRC = PROJECT_ROOT / "services" / "dope-context" / "src"

sys.path.insert(0, str(DOPE_CONTEXT_SRC))
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "autonomous-indexing.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)


def workspace_to_hash(workspace_path: Path) -> str:
    """Generate stable hash from workspace path."""
    normalized = str(workspace_path.resolve())
    hash_full = hashlib.md5(normalized.encode()).hexdigest()
    return hash_full[:8]


async def run_autonomous_indexing():
    """Main autonomous indexing loop."""

    workspace_path = PROJECT_ROOT
    workspace_hash = workspace_to_hash(workspace_path)

    print("=" * 70)
    print("🚀 Autonomous Indexing Daemon Starting")
    print("=" * 70)
    print(f"📂 Workspace: {workspace_path}")
    print(f"🔑 Hash: {workspace_hash}")
    print(f"📊 Collections: code_{workspace_hash}, docs_{workspace_hash}")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Import autonomous components
    from autonomous.autonomous_controller import AutonomousController, AutonomousConfig
    from autonomous.watchdog_monitor import WatchdogMonitor
    from autonomous.indexing_worker import IndexingWorker
    from autonomous.periodic_sync import PeriodicSync

    # Import indexing components
    from preprocessing.code_chunker import CodeChunker
    from context.openai_generator import OpenAIContextGenerator
    from embeddings.voyage_embedder import VoyageEmbedder
    from search.multi_vector_search import MultiVectorSearch
    from pipeline.indexing_pipeline import IndexingPipeline, IndexingConfig
    from enrichment.docs_chunker import DocsChunker
    from search.docs_search import DocsVectorSearch

    # Verify API keys
    voyage_key = os.getenv("VOYAGE_API_KEY")
    if not voyage_key:
        print("❌ VOYAGE_API_KEY not set - required for embeddings")
        print("   export VOYAGE_API_KEY='your-key'")
        sys.exit(1)

    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not openai_key and not anthropic_key:
        print("⚠️  Warning: Neither OPENAI_API_KEY nor ANTHROPIC_API_KEY set")
        print("   Context generation will be skipped (quality reduced)")
        print("   Consider setting one for better results")
        print()

    # Configuration
    code_config = AutonomousConfig(
        enabled=True,
        debounce_seconds=5.0,
        periodic_interval=600,
        include_patterns=["*.py", "*.js", "*.ts", "*.tsx"],
        exclude_patterns=["*test*", "*__pycache__*", "*node_modules*", "*.git*", "*venv*", "*.venv*"]
    )

    docs_config = AutonomousConfig(
        enabled=True,
        debounce_seconds=5.0,
        periodic_interval=600,
        include_patterns=["*.md", "*.pdf", "*.html", "*.txt"],
        exclude_patterns=["*node_modules*", "*.git*", "*__pycache__*", "*venv*"]
    )

    # ========================================
    # CODE AUTONOMOUS INDEXING
    # ========================================

    print("🔧 Step 1/2: Setting up CODE autonomous indexing...")

    code_collection = f"code_{workspace_hash}"

    # Create indexing components
    code_vector_search = MultiVectorSearch(
        collection_name=code_collection,
        url=os.getenv("QDRANT_URL", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333"))
    )

    # Ensure collection exists
    try:
        await code_vector_search.create_collection()
    except Exception as e:
        logger.info(f"Collection already exists or creation skipped: {e}")

    code_chunker = CodeChunker()

    context_generator = None
    if openai_key:
        context_generator = OpenAIContextGenerator(api_key=openai_key)

    embedder = VoyageEmbedder(
        api_key=voyage_key,
        default_model="voyage-code-3"
    )

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

    # Create indexing callback
    async def code_index_callback(file_path: Path, changed_files=None):
        """Callback to reindex changed code files."""
        try:
            logger.info(f"📝 Reindexing code: {file_path.name}")

            # Index single file
            result = await code_pipeline.index_file(file_path)

            if result:
                logger.info(f"✅ Code indexed: {file_path.name}")
                return True
            else:
                logger.warning(f"⚠️  No chunks generated for: {file_path.name}")
                return False

        except Exception as e:
            logger.error(f"❌ Code indexing failed for {file_path.name}: {e}")
            return False

    # Create autonomous controller for code
    code_controller = AutonomousController(
        workspace_path=workspace_path,
        config=code_config,
        index_callback=code_index_callback
    )

    await code_controller.start()

    print(f"✅ CODE autonomous indexing ENABLED")
    print(f"   Collection: {code_collection}")
    print(f"   Watching: {code_config.include_patterns}")
    print(f"   Debounce: {code_config.debounce_seconds}s")
    print()

    # ========================================
    # DOCS AUTONOMOUS INDEXING
    # ========================================

    print("🔧 Step 2/2: Setting up DOCS autonomous indexing...")

    docs_collection = f"docs_{workspace_hash}"

    # Create docs components
    docs_vector_search = DocsVectorSearch(
        collection_name=docs_collection,
        url=os.getenv("QDRANT_URL", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333"))
    )

    # Ensure collection exists
    try:
        await docs_vector_search.create_collection()
    except Exception as e:
        logger.info(f"Docs collection already exists or creation skipped: {e}")

    docs_chunker = DocsChunker()

    docs_embedder = VoyageEmbedder(
        api_key=voyage_key,
        default_model="voyage-context-3"
    )

    # Create docs indexing callback
    async def docs_index_callback(file_path: Path, changed_files=None):
        """Callback to reindex changed docs."""
        try:
            logger.info(f"📄 Reindexing doc: {file_path.name}")

            # Process document
            chunks = await docs_chunker.chunk_document(file_path)

            if chunks:
                # Embed and store
                for chunk in chunks:
                    embeddings = await docs_embedder.embed_multi_vector(chunk)
                    await docs_vector_search.upsert_multi_vector(
                        chunk_id=chunk.chunk_id,
                        embeddings=embeddings,
                        payload=chunk.to_dict()
                    )

                logger.info(f"✅ Doc indexed: {file_path.name} ({len(chunks)} chunks)")
                return True
            else:
                logger.warning(f"⚠️  No chunks for: {file_path.name}")
                return False

        except Exception as e:
            logger.error(f"❌ Doc indexing failed for {file_path.name}: {e}")
            return False

    # Create autonomous controller for docs
    docs_controller = AutonomousController(
        workspace_path=workspace_path,
        config=docs_config,
        index_callback=docs_index_callback
    )

    await docs_controller.start()

    print(f"✅ DOCS autonomous indexing ENABLED")
    print(f"   Collection: {docs_collection}")
    print(f"   Watching: {docs_config.include_patterns}")
    print(f"   Debounce: {docs_config.debounce_seconds}s")
    print()

    # ========================================
    # DAEMON MAIN LOOP
    # ========================================

    print("=" * 70)
    print("🎉 AUTONOMOUS INDEXING DAEMON RUNNING")
    print("=" * 70)
    print()
    print("✨ Benefits:")
    print("   • Files auto-reindex 5s after save")
    print("   • Periodic sync every 10 minutes")
    print("   • Zero mental overhead - search always current")
    print("   • Interrupt-safe - background operation")
    print()
    print("🧠 ADHD Impact:")
    print("   • 100% cognitive load reduction for indexing")
    print("   • No 'did I reindex?' anxiety")
    print("   • Always-current search results")
    print()
    print("⚙️  Daemon running in background...")
    print("   Press Ctrl+C to stop")
    print()

    # Setup signal handlers for clean shutdown
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, stopping gracefully...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Main loop - wait for shutdown
    try:
        # Periodic status updates
        last_status_time = datetime.now()

        while not shutdown_event.is_set():
            await asyncio.sleep(60)  # Check every minute

            # Print status every 10 minutes
            now = datetime.now()
            if (now - last_status_time).total_seconds() >= 600:
                code_status = code_controller.get_status()
                docs_status = docs_controller.get_status()

                logger.info(
                    f"📊 Status: Code {code_status['files_indexed']} files indexed, "
                    f"Docs {docs_status['files_indexed']} docs indexed"
                )

                if code_status["pending_files"] > 0 or docs_status["pending_files"] > 0:
                    logger.info(
                        f"   Pending: {code_status['pending_files']} code, "
                        f"{docs_status['pending_files']} docs"
                    )

                last_status_time = now

    except asyncio.CancelledError:
        logger.info("Daemon cancelled, shutting down...")

    finally:
        # Clean shutdown
        print()
        print("🛑 Stopping autonomous indexing...")

        await code_controller.stop()
        await docs_controller.stop()

        print("✅ Autonomous indexing stopped cleanly")
        print()

        # Print final stats
        code_status = code_controller.get_status()
        docs_status = docs_controller.get_status()

        print("📊 Final Statistics:")
        print(f"   Code files indexed: {code_status['files_indexed']}")
        print(f"   Docs indexed: {docs_status['files_indexed']}")
        print(f"   Total events processed: {code_status.get('events_processed', 0) + docs_status.get('events_processed', 0)}")
        print()


def check_environment():
    """Verify environment is ready."""
    errors = []

    # Check API keys
    if not os.getenv("VOYAGE_API_KEY"):
        errors.append("VOYAGE_API_KEY not set (required)")

    # Check Qdrant
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 6333))
        sock.close()
        if result != 0:
            errors.append("Qdrant not running on port 6333")
    except Exception as e:
        errors.append(f"Cannot check Qdrant: {e}")

    # Check workspace
    if not (PROJECT_ROOT / "services").exists():
        errors.append(f"Services directory not found at {PROJECT_ROOT / 'services'}")

    return errors


if __name__ == "__main__":
    print()
    print("🔍 Pre-flight Checks")
    print("=" * 70)

    # Create logs directory
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    # Check environment
    errors = check_environment()

    if errors:
        print("❌ Environment check failed:")
        for error in errors:
            print(f"   • {error}")
        print()
        print("💡 Fix these issues and try again:")
        print("   export VOYAGE_API_KEY='your-key'")
        print("   docker ps | grep qdrant  # Verify Qdrant running")
        sys.exit(1)

    print("✅ Environment check passed")
    print()

    # Verify Qdrant collections exist
    try:
        import httpx
        resp = httpx.get("http://localhost:6333/collections")
        if resp.status_code == 200:
            collections = resp.json().get("result", {}).get("collections", [])
            collection_names = [c["name"] for c in collections]

            workspace_hash = workspace_to_hash(PROJECT_ROOT)
            code_coll = f"code_{workspace_hash}"
            docs_coll = f"docs_{workspace_hash}"

            if code_coll in collection_names:
                print(f"✅ Code collection exists: {code_coll}")
            else:
                print(f"⚠️  Code collection not found: {code_coll}")
                print("   Will be created on first file change")

            if docs_coll in collection_names:
                print(f"✅ Docs collection exists: {docs_coll}")
            else:
                print(f"⚠️  Docs collection not found: {docs_coll}")
                print("   Will be created on first file change")
            print()
    except Exception as e:
        print(f"⚠️  Could not verify collections: {e}")
        print()

    # Run the daemon
    try:
        asyncio.run(run_autonomous_indexing())
    except KeyboardInterrupt:
        print()
        print("👋 Daemon stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Daemon crashed: {e}", exc_info=True)
        sys.exit(1)
