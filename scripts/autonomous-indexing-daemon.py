#!/usr/bin/env python3
"""
Autonomous Indexing Daemon - ADHD Zero-Touch Background Service

Runs autonomous file monitoring and indexing for code and docs as a background daemon.
Supports monitoring multiple workspaces/worktrees concurrently.

Usage:
    python scripts/autonomous-indexing-daemon.py \
        --workspace /path/to/project \
        --workspace /path/to/worktree-b

    DOPE_CONTEXT_WORKSPACES="/path/a,/path/b" python scripts/autonomous-indexing-daemon.py
"""

import argparse
import asyncio
import hashlib
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DOPE_CONTEXT_SRC = PROJECT_ROOT / "services" / "dope-context" / "src"

sys.path.insert(0, str(DOPE_CONTEXT_SRC))
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
LOG_PATH = PROJECT_ROOT / "logs"
LOG_PATH.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_PATH / "autonomous-indexing.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


def workspace_to_hash(workspace_path: Path) -> str:
    """Generate stable hash from workspace path."""
    normalized = str(workspace_path.resolve())
    hash_full = hashlib.md5(normalized.encode()).hexdigest()
    return hash_full[:8]


async def _start_workspace_controllers(
    workspace_path: Path,
    voyage_key: str,
    openai_key: str | None,
) -> Dict[str, object]:
    """Start code/docs autonomous controllers for a single workspace."""
    workspace_path = workspace_path.resolve()
    workspace_hash = workspace_to_hash(workspace_path)

    print("=" * 70)
    print(f"🚀 Starting autonomous indexing for {workspace_path}")
    print(f"🔑 Hash: {workspace_hash}")
    print(f"📊 Collections: code_{workspace_hash}, docs_{workspace_hash}")

    from autonomous.autonomous_controller import AutonomousController, AutonomousConfig
    from preprocessing.code_chunker import CodeChunker
    from context.openai_generator import OpenAIContextGenerator
    from embeddings.voyage_embedder import VoyageEmbedder
    from search.multi_vector_search import MultiVectorSearch
    from pipeline.indexing_pipeline import IndexingPipeline, IndexingConfig
    from enrichment.docs_chunker import DocsChunker
    from search.docs_search import DocsVectorSearch

    # Shared configs
    code_config = AutonomousConfig(
        enabled=True,
        debounce_seconds=5.0,
        periodic_interval=600,
        include_patterns=["*.py", "*.js", "*.ts", "*.tsx"],
        exclude_patterns=["*test*", "*__pycache__*", "*node_modules*", "*.git*", "*venv*", "*.venv*"],
    )
    docs_config = AutonomousConfig(
        enabled=True,
        debounce_seconds=5.0,
        periodic_interval=600,
        include_patterns=["*.md", "*.pdf", "*.html", "*.txt"],
        exclude_patterns=["*node_modules*", "*.git*", "*__pycache__*", "*venv*"],
    )

    # ---------------- Code indexing ----------------
    code_collection = f"code_{workspace_hash}"
    code_vector_search = MultiVectorSearch(
        collection_name=code_collection,
        url=os.getenv("QDRANT_URL", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
    )

    code_chunker = CodeChunker()

    context_generator = None
    if openai_key:
        context_generator = OpenAIContextGenerator(api_key=openai_key)

    code_embedder = VoyageEmbedder(api_key=voyage_key, default_model="voyage-code-3")

    indexing_config = IndexingConfig(
        workspace_path=workspace_path,
        include_patterns=code_config.include_patterns,
        exclude_patterns=code_config.exclude_patterns,
        workspace_id=str(workspace_path),
    )

    code_pipeline = IndexingPipeline(
        chunker=code_chunker,
        context_generator=context_generator,
        embedder=code_embedder,
        vector_search=code_vector_search,
        config=indexing_config,
    )

    async def code_index_callback(file_path: Path, changed_files=None):
        try:
            logger.info("📝 Reindexing code file: %s", file_path.name)
            await code_pipeline.index_file(file_path)
            return True
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.error("Code indexing failed for %s: %s", file_path, exc)
            return False

    code_controller = AutonomousController(
        workspace_path=workspace_path,
        config=code_config,
        index_callback=code_index_callback,
    )
    await code_controller.start()

    # ---------------- Docs indexing ----------------
    docs_collection = f"docs_{workspace_hash}"
    docs_vector_search = DocsVectorSearch(
        collection_name=docs_collection,
        url=os.getenv("QDRANT_URL", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
    )
    try:
        await docs_vector_search.create_collection()
    except Exception as exc:  # pragma: no cover - collection may exist
        logger.info("Docs collection setup skipped: %s", exc)

    docs_chunker = DocsChunker()
    docs_embedder = VoyageEmbedder(api_key=voyage_key, default_model="voyage-context-3")

    async def docs_index_callback(file_path: Path, changed_files=None):
        try:
            logger.info("📄 Reindexing doc: %s", file_path.name)
            chunks = await docs_chunker.chunk_document(file_path)
            if not chunks:
                return False
            for chunk in chunks:
                embeddings = await docs_embedder.embed_multi_vector(chunk)
                await docs_vector_search.upsert_multi_vector(
                    chunk_id=chunk.chunk_id,
                    embeddings=embeddings,
                    payload=chunk.to_dict(),
                )
            return True
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.error("Doc indexing failed for %s: %s", file_path, exc)
            return False

    docs_controller = AutonomousController(
        workspace_path=workspace_path,
        config=docs_config,
        index_callback=docs_index_callback,
        registry_key=f"{workspace_path}:docs",
    )
    await docs_controller.start()

    print("✅ Controllers ready – code + docs monitoring active.")
    print()

    return {
        "workspace": workspace_path,
        "workspace_hash": workspace_hash,
        "controllers": {
            "code": code_controller,
            "docs": docs_controller,
        },
    }


async def run_autonomous_indexing(workspaces: List[Path]):
    """Main autonomous indexing loop for one or many workspaces."""
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
        print()

    workspace_states = []
    for workspace in workspaces:
        state = await _start_workspace_controllers(workspace, voyage_key, openai_key)
        workspace_states.append(state)

    print("=" * 70)
    print("🎉 AUTONOMOUS INDEXING DAEMON RUNNING")
    print("=" * 70)
    print("🧠 ADHD Impact:")
    print("   • Files auto-reindex 5s after save")
    print("   • Periodic sync every 10 minutes")
    print("   • No 'did I reindex?' anxiety")
    print()

    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        logger.info("Received shutdown signal (%s). Stopping gracefully...", sig)
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while not shutdown_event.is_set():
            await asyncio.sleep(60)
            for state in workspace_states:
                logger.info(
                    "Status • %s • controllers=%s",
                    state["workspace"],
                    ", ".join(state["controllers"].keys()),
                )
    finally:
        for state in workspace_states:
            for controller in state["controllers"].values():
                try:
                    await controller.stop()
                except Exception as exc:  # pragma: no cover - best effort logging
                    logger.error("Failed to stop controller: %s", exc)

        logger.info("All autonomous controllers stopped. Goodbye!")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the autonomous indexing daemon.")
    parser.add_argument(
        "-w",
        "--workspace",
        action="append",
        dest="workspaces",
        help="Workspace path to monitor (repeatable). Defaults to repo root or DOPE_CONTEXT_WORKSPACES env.",
    )
    return parser


def _resolve_workspaces(args: argparse.Namespace) -> List[Path]:
    workspace_inputs: List[str] = []
    if args.workspaces:
        workspace_inputs.extend(args.workspaces)

    env_value = os.getenv("DOPE_CONTEXT_WORKSPACES")
    if env_value:
        workspace_inputs.extend(
            [item.strip() for item in env_value.replace(";", ",").split(",") if item.strip()]
        )

    if not workspace_inputs:
        workspace_inputs = [str(PROJECT_ROOT)]

    return [Path(path).expanduser().resolve() for path in workspace_inputs]


if __name__ == "__main__":
    cli_args = _build_parser().parse_args()
    workspace_list = _resolve_workspaces(cli_args)
    asyncio.run(run_autonomous_indexing(workspace_list))
