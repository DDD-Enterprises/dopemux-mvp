#!/usr/bin/env python3
"""
Enable Autonomous Indexing - ADHD Zero-Touch Setup

Bootstrap script that sets up autonomous file monitoring and indexing for code and docs.
This script starts the controllers but exits immediately after setup.

For long-running background monitoring, use autonomous-indexing-daemon.py instead.

Usage:
    python scripts/enable-autonomous-indexing.py \
        --workspace /path/to/project \
        --workspace /path/to/worktree-b

    # or via environment variable
    DOPE_CONTEXT_WORKSPACES="/path/a,/path/b" python scripts/enable-autonomous-indexing.py

Note: This is a setup/bootstrap script. Use autonomous-indexing-daemon.py for persistent monitoring.
"""

import argparse

import logging

logger = logging.getLogger(__name__)

import asyncio
import os
import sys
from pathlib import Path
from typing import List

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


async def enable_autonomous_indexing_for_workspace(workspace_path: Path) -> None:
    """Enable autonomous indexing for a specific workspace."""
    workspace_path = workspace_path.resolve()

    logger.info("=" * 70)
    logger.info(f"📂 Workspace: {workspace_path}")

    code_config = AutonomousConfig(
        enabled=True,
        debounce_seconds=5.0,
        periodic_interval=600,  # 10 minutes
        include_patterns=["*.py", "*.js", "*.ts", "*.tsx"],
        exclude_patterns=["*test*", "*__pycache__*", "*node_modules*", "*.git*"],
    )

    docs_config = AutonomousConfig(
        enabled=True,
        debounce_seconds=5.0,
        periodic_interval=600,
        include_patterns=["*.md", "*.pdf", "*.html", "*.txt"],
        exclude_patterns=["*node_modules*", "*.git*", "*__pycache__*"],
    )

    detector = WorkspaceDetector()
    workspace_hash = detector.get_workspace_hash(workspace_path)
    code_collection = f"dopemux_code_{workspace_hash}"
    docs_collection = f"dopemux_docs_{workspace_hash}"

    logger.info(f"📊 Collections:")
    logger.info(f"   Code: {code_collection}")
    logger.info(f"   Docs: {docs_collection}")
    logger.info()

    try:
        # ========================================
        # CODE AUTONOMOUS INDEXING
        # ========================================

        logger.info("🔧 Step 1/2: Enabling autonomous CODE indexing...")

        code_vector_search = MultiVectorSearch(
            collection_name=code_collection,
            url="localhost",
            port=6333,
        )

        code_chunker = CodeChunker()

        context_generator = None
        if os.getenv("OPENAI_API_KEY"):
            context_generator = OpenAIContextGenerator(api_key=os.getenv("OPENAI_API_KEY"))

        embedder = VoyageEmbedder(
            api_key=os.getenv("VOYAGE_API_KEY"),
            default_model="voyage-code-3",
        )

        from pipeline.indexing_pipeline import IndexingConfig

        indexing_config = IndexingConfig(
            workspace_path=workspace_path,
            include_patterns=code_config.include_patterns,
            exclude_patterns=code_config.exclude_patterns,
            workspace_id=str(workspace_path),
        )

        code_pipeline = IndexingPipeline(
            chunker=code_chunker,
            context_generator=context_generator,
            embedder=embedder,
            vector_search=code_vector_search,
            config=indexing_config,
        )

        async def code_index_callback(file_path: Path, changed_files=None):
            try:
                logger.info(f"📝 Reindexing: {file_path}")
                await code_pipeline.index_file(file_path)
                return True
            except Exception as exc:  # pragma: no cover - best effort logging
                logger.error(f"❌ Reindex failed: {exc}")
                return False

        code_controller = AutonomousController(
            workspace_path=workspace_path,
            config=code_config,
            index_callback=code_index_callback,
        )
        await code_controller.start()

        logger.info("✅ Autonomous CODE indexing enabled!")
        logger.info(f"   Monitoring: {workspace_path}")
        logger.info(f"   Patterns: {code_config.include_patterns}")
        logger.info(f"   Debounce: {code_config.debounce_seconds}s")
        logger.info(f"   Periodic sync: {code_config.periodic_interval}s")
        logger.info()

        # ========================================
        # DOCS AUTONOMOUS INDEXING
        # ========================================

        logger.info("🔧 Step 2/2: Enabling autonomous DOCS indexing...")

        docs_vector_search = DocsVectorSearch(
            collection_name=docs_collection,
            url="localhost",
            port=6333,
        )

        docs_chunker = DocsChunker()

        docs_embedder = VoyageEmbedder(
            api_key=os.getenv("VOYAGE_API_KEY"),
            default_model="voyage-context-3",
        )

        async def docs_index_callback(file_path: Path, changed_files=None):
            try:
                logger.info(f"📄 Reindexing doc: {file_path}")
                await docs_chunker.chunk_and_index(file_path, docs_vector_search, docs_embedder)
                return True
            except Exception as exc:  # pragma: no cover - best effort logging
                logger.error(f"❌ Doc reindex failed: {exc}")
                return False

        docs_controller = AutonomousController(
            workspace_path=workspace_path,
            config=docs_config,
            index_callback=docs_index_callback,
            registry_key=f"{workspace_path}:docs",
        )
        await docs_controller.start()

        logger.info("✅ Autonomous DOCS indexing enabled!")
        logger.info(f"   Monitoring: {workspace_path}")
        logger.info(f"   Patterns: {docs_config.include_patterns}")
        logger.info(f"   Debounce: {docs_config.debounce_seconds}s")
        logger.info(f"   Periodic sync: {docs_config.periodic_interval}s")
        logger.info()

        logger.info("🎉 AUTONOMOUS INDEXING ENABLED!")
        logger.info("   • Files auto-reindex 5s after save")
        logger.info("   • Periodic sync every 10 minutes")
        logger.info("   • Zero mental overhead - search always current")
        logger.info()

    except Exception as exc:  # pragma: no cover - best effort logging
        logger.error(f"❌ Failed to enable autonomous indexing: {exc}")


def _parse_workspace_args() -> List[Path]:
    parser = argparse.ArgumentParser(description="Enable autonomous indexing across one or more workspaces.")
    parser.add_argument(
        "-w",
        "--workspace",
        action="append",
        dest="workspaces",
        help="Workspace path to monitor (repeatable). Defaults to current directory.",
    )
    args = parser.parse_args()

    workspace_inputs: List[str] = []
    if args.workspaces:
        workspace_inputs.extend(args.workspaces)

    env_value = os.getenv("DOPE_CONTEXT_WORKSPACES")
    if env_value:
        workspace_inputs.extend(
            [item.strip() for item in env_value.replace(";", ",").split(",") if item.strip()]
        )

    if not workspace_inputs:
        workspace_inputs = [str(Path.cwd())]

    resolved = [Path(path).expanduser().resolve() for path in workspace_inputs]
    return resolved


async def main() -> None:
    workspaces = _parse_workspace_args()
    for workspace in workspaces:
        await enable_autonomous_indexing_for_workspace(workspace)


if __name__ == "__main__":
    asyncio.run(main())
