"""
FastMCP Server - Task 8
Exposes code index as MCP tools for Claude Code integration.

MCP Tools:
1. index_workspace - Index code files
2. search_code - Hybrid search (dense + sparse + rerank)
3. get_index_status - Collection info
4. clear_index - Delete collection
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from fastmcp import FastMCP

from ..preprocessing.code_chunker import CodeChunker, ChunkingConfig
from ..context.claude_generator import ClaudeContextGenerator
from ..embeddings.voyage_embedder import VoyageEmbedder
from ..search.dense_search import MultiVectorSearch, SearchProfile
from ..search.hybrid_search import HybridSearch, BM25Index
from ..rerank.voyage_reranker import VoyageReranker
from ..pipeline.indexing_pipeline import (
    IndexingPipeline,
    IndexingConfig,
    IndexingProgress,
)
from ..pipeline.docs_pipeline import DocIndexingPipeline
from ..search.docs_search import DocumentSearch
from ..utils.workspace import get_workspace_root, get_collection_names, get_snapshot_dir
from ..sync.file_synchronizer import FileSynchronizer, ChangeSet


logger = logging.getLogger(__name__)


# Initialize FastMCP server
mcp = FastMCP("dope-context")


# Global state (initialized on startup)
_pipeline: Optional[IndexingPipeline] = None
_hybrid_search: Optional[HybridSearch] = None
_reranker: Optional[VoyageReranker] = None
_embedder: Optional[VoyageEmbedder] = None
_bm25_index: Optional[BM25Index] = None

# Docs pipeline (new)
_docs_pipeline: Optional[DocIndexingPipeline] = None
_docs_search: Optional[DocumentSearch] = None
_docs_embedder: Optional[VoyageEmbedder] = None


def _initialize_components():
    """Initialize all pipeline components."""
    global _pipeline, _hybrid_search, _reranker, _embedder, _bm25_index
    global _docs_pipeline, _docs_search, _docs_embedder

    # Get API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    voyage_key = os.getenv("VOYAGE_API_KEY")
    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    if not voyage_key:
        raise ValueError("VOYAGE_API_KEY environment variable required")

    # Initialize components
    chunker = CodeChunker(config=ChunkingConfig())

    context_generator = None
    if anthropic_key:
        context_generator = ClaudeContextGenerator(api_key=anthropic_key)
    else:
        logger.warning("ANTHROPIC_API_KEY not set - context generation disabled")

    _embedder = VoyageEmbedder(api_key=voyage_key)

    vector_search = MultiVectorSearch(
        collection_name="code_index",
        url=qdrant_url,
        port=qdrant_port,
    )

    _bm25_index = BM25Index()

    _hybrid_search = HybridSearch(
        dense_search=vector_search,
        bm25_index=_bm25_index,
    )

    _reranker = VoyageReranker(api_key=voyage_key)

    # Create pipeline
    config = IndexingConfig(
        workspace_path=Path.cwd(),
        workspace_id=os.getenv("WORKSPACE_ID", "default"),
    )

    _pipeline = IndexingPipeline(
        chunker=chunker,
        context_generator=context_generator,
        embedder=_embedder,
        vector_search=vector_search,
        config=config,
    )

    # Initialize docs components
    _docs_embedder = VoyageEmbedder(
        api_key=voyage_key,
        default_model="voyage-context-3",
    )

    _docs_search = DocumentSearch(
        collection_name="docs_index",
        url=qdrant_url,
        port=qdrant_port,
    )

    _docs_pipeline = DocIndexingPipeline(
        embedder=_docs_embedder,
        doc_search=_docs_search,
        workspace_path=Path.cwd(),
        workspace_id=os.getenv("WORKSPACE_ID", "default"),
    )

    logger.info("Dope-Context MCP server initialized (code + docs)")


async def _index_workspace_impl(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_files: Optional[int] = None,
) -> Dict:
    """Implementation of index_workspace tool."""
    workspace = Path(workspace_path).resolve()
    code_collection, _ = get_collection_names(workspace)

    logger.info(f"Indexing workspace: {workspace_path} → collection: {code_collection}")

    # Create workspace-specific components
    vector_search = MultiVectorSearch(
        collection_name=code_collection,
        url=os.getenv("QDRANT_URL", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
    )

    await vector_search.create_collection()

    # Create workspace-specific pipeline
    chunker = CodeChunker()

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    context_generator = None
    if anthropic_key:
        context_generator = ClaudeContextGenerator(api_key=anthropic_key)

    embedder = VoyageEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        default_model="voyage-code-3",
    )

    config = IndexingConfig(
        workspace_path=workspace,
        include_patterns=include_patterns or ["*.py", "*.js", "*.ts", "*.tsx"],
        exclude_patterns=exclude_patterns or ["*test*", "*__pycache__*"],
        max_files=max_files,
        workspace_id=str(workspace),
    )

    pipeline = IndexingPipeline(
        chunker=chunker,
        context_generator=context_generator,
        embedder=embedder,
        vector_search=vector_search,
        config=config,
    )

    # Run indexing
    progress = await pipeline.index_workspace()

    return progress.summary()


@mcp.tool()
async def index_workspace(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_files: Optional[int] = None,
) -> Dict:
    """
    Index a workspace directory for code search.

    Args:
        workspace_path: Path to workspace root
        include_patterns: File patterns to include (e.g., ["*.py", "*.ts"])
        exclude_patterns: File patterns to exclude (e.g., ["*test*"])
        max_files: Maximum files to index (optional)

    Returns:
        Indexing progress summary
    """
    return await _index_workspace_impl(
        workspace_path, include_patterns, exclude_patterns, max_files
    )


async def _search_code_impl(
    query: str,
    top_k: int = 10,
    profile: str = "implementation",
    use_reranking: bool = True,
    filter_language: Optional[str] = None,
    workspace_path: Optional[str] = None,
) -> List[Dict]:
    """Implementation of search_code tool."""
    # Detect workspace
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()
    code_collection, _ = get_collection_names(workspace)

    logger.info(f"Searching workspace: {workspace} → collection: {code_collection}")

    # Create workspace-specific search components
    vector_search = MultiVectorSearch(
        collection_name=code_collection,
        url=os.getenv("QDRANT_URL", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
    )

    embedder = VoyageEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        default_model="voyage-code-3",
    )

    bm25_index = BM25Index()  # Will be built on-demand or from cache

    hybrid_search = HybridSearch(
        dense_search=vector_search,
        bm25_index=bm25_index,
    )

    reranker = VoyageReranker(api_key=os.getenv("VOYAGE_API_KEY"))

    # Select profile
    profile_map = {
        "implementation": SearchProfile.implementation(),
        "debugging": SearchProfile.debugging(),
        "exploration": SearchProfile.exploration(),
    }
    search_profile = profile_map.get(profile, SearchProfile.implementation())

    # Embed query (3 vectors)
    query_content = await _embedder.embed(
        text=query,
        model="voyage-code-3",
        input_type="query",
    )

    query_title = await _embedder.embed(
        text=query,
        model="voyage-code-3",
        input_type="query",
    )

    query_breadcrumb = await _embedder.embed(
        text=query,
        model="voyage-code-3",
        input_type="query",
    )

    query_vectors = {
        "content": query_content.embedding,
        "title": query_title.embedding,
        "breadcrumb": query_breadcrumb.embedding,
    }

    # Apply filter
    filter_by = {}
    if filter_language:
        filter_by["language"] = filter_language

    # Hybrid search
    search_results = await _hybrid_search.search(
        query_vectors=query_vectors,
        query_text=query,
        profile=search_profile,
        filter_by=filter_by if filter_by else None,
    )

    # Rerank if requested
    if use_reranking and search_results:
        rerank_response = await _reranker.rerank(
            query=query,
            results=search_results[:50],  # Rerank top-50
        )

        # Return top-k from reranked
        final_results = rerank_response.top_results[:top_k]

        return [
            {
                "file_path": r.search_result.file_path,
                "function_name": r.search_result.function_name,
                "language": r.search_result.language,
                "code": r.search_result.content,
                "context": r.search_result.context_snippet,
                "relevance_score": r.relevance_score,
                "original_rank": r.original_rank,
                "reranked": True,
            }
            for r in final_results
        ]

    else:
        # Return without reranking
        return [
            {
                "file_path": r.file_path,
                "function_name": r.function_name,
                "language": r.language,
                "code": r.content,
                "context": r.context_snippet,
                "score": r.score,
                "reranked": False,
            }
            for r in search_results[:top_k]
        ]


@mcp.tool()
async def search_code(
    query: str,
    top_k: int = 10,
    profile: str = "implementation",
    use_reranking: bool = True,
    filter_language: Optional[str] = None,
    workspace_path: Optional[str] = None,
) -> List[Dict]:
    """
    Search indexed code with hybrid dense + sparse search.

    Auto-detects workspace from current directory (or use workspace_path).

    Args:
        query: Search query (natural language)
        top_k: Number of results to return (ADHD: max 10 default)
        profile: Search profile (implementation, debugging, exploration)
        use_reranking: Whether to rerank with Voyage (default: True)
        filter_language: Filter by language (python, javascript, typescript)
        workspace_path: Optional workspace path (auto-detects if None)

    Returns:
        List of search results with code, context, and scores
    """
    return await _search_code_impl(
        query, top_k, profile, use_reranking, filter_language, workspace_path
    )


async def _get_index_status_impl() -> Dict:
    """Implementation of get_index_status tool."""
    if not _pipeline:
        _initialize_components()

    info = await _pipeline.vector_search.get_collection_info()

    return {
        "collection_name": info.get("name", "code_index"),
        "total_vectors": info.get("vectors_count", 0),
        "status": info.get("status", "unknown"),
        "embedding_cost_summary": _embedder.get_cost_summary() if _embedder else {},
        "context_cost_summary": (
            _pipeline.context_generator.get_cost_summary()
            if _pipeline.context_generator
            else {}
        ),
    }


@mcp.tool()
async def get_index_status() -> Dict:
    """
    Get status of code index.

    Returns:
        Collection information and statistics
    """
    return await _get_index_status_impl()


async def _clear_index_impl() -> Dict:
    """Implementation of clear_index tool."""
    if not _pipeline:
        _initialize_components()

    await _pipeline.vector_search.delete_collection()

    return {"status": "success", "message": "Code index cleared"}


@mcp.tool()
async def clear_index() -> Dict:
    """
    Clear the code index (delete collection).

    Returns:
        Success message
    """
    return await _clear_index_impl()


# NEW DOCS TOOLS


async def _index_docs_impl(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
) -> Dict:
    """Implementation of index_docs tool."""
    workspace = Path(workspace_path).resolve()
    _, docs_collection = get_collection_names(workspace)

    logger.info(f"Indexing docs: {workspace_path} → collection: {docs_collection}")

    # Create workspace-specific components
    docs_search = DocumentSearch(
        collection_name=docs_collection,
        url=os.getenv("QDRANT_URL", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
    )

    docs_embedder = VoyageEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        default_model="voyage-context-3",
    )

    docs_pipeline = DocIndexingPipeline(
        embedder=docs_embedder,
        doc_search=docs_search,
        workspace_path=workspace,
        workspace_id=str(workspace),
    )

    result = await docs_pipeline.index_workspace(
        include_patterns=include_patterns,
    )

    return result


@mcp.tool()
async def index_docs(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
) -> Dict:
    """
    Index documents (PDF, Markdown, HTML, text) in workspace.

    Args:
        workspace_path: Path to workspace root
        include_patterns: File patterns (e.g., ["*.md", "*.pdf"])

    Returns:
        Indexing summary
    """
    return await _index_docs_impl(workspace_path, include_patterns)


async def _docs_search_impl(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
) -> List[Dict]:
    """Implementation of docs_search tool."""
    # Detect workspace
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()
    _, docs_collection = get_collection_names(workspace)

    logger.info(f"Searching docs: {workspace} → collection: {docs_collection}")

    # Create workspace-specific components
    docs_search = DocumentSearch(
        collection_name=docs_collection,
        url=os.getenv("QDRANT_URL", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
    )

    docs_embedder = VoyageEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        default_model="voyage-context-3",
    )

    # Embed query with voyage-context-3
    query_content = await docs_embedder.embed(
        text=query,
        model="voyage-context-3",
        input_type="query",
    )

    query_vectors = {
        "content": query_content.embedding,
        "title": query_content.embedding,
        "breadcrumb": query_content.embedding,
    }

    # Apply filter
    filter_by = {}
    if filter_doc_type:
        filter_by["doc_type"] = filter_doc_type

    # Search
    results = await docs_search.search_documents(
        query_vectors=query_vectors,
        filter_by=filter_by if filter_by else None,
    )

    return [
        {
            "source_path": r.file_path,
            "text": r.content,
            "score": r.score,
            "doc_type": r.payload.get("doc_type", "unknown"),
        }
        for r in results[:top_k]
    ]


@mcp.tool()
async def docs_search(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
) -> List[Dict]:
    """
    Search indexed documents (PDF, Markdown, HTML, text).

    Auto-detects workspace from current directory (or use workspace_path).

    Args:
        query: Search query (natural language)
        top_k: Number of results
        filter_doc_type: Filter by document type (md, pdf, html, txt)
        workspace_path: Optional workspace path (auto-detects if None)

    Returns:
        List of document search results
    """
    return await _docs_search_impl(query, top_k, filter_doc_type, workspace_path)


async def _search_all_impl(
    query: str,
    top_k: int = 10,
    workspace_path: Optional[str] = None,
) -> Dict:
    """Implementation of unified search_all tool."""
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()

    logger.info(f"Unified search in workspace: {workspace}")

    # Search both code and docs in parallel (same workspace)
    code_results_task = _search_code_impl(
        query, top_k // 2, use_reranking=False, workspace_path=str(workspace)
    )
    docs_results_task = _docs_search_impl(
        query, top_k // 2, workspace_path=str(workspace)
    )

    code_results, docs_results = await asyncio.gather(
        code_results_task,
        docs_results_task,
    )

    return {
        "workspace": str(workspace),
        "code_results": code_results,
        "docs_results": docs_results,
        "total_results": len(code_results) + len(docs_results),
    }


@mcp.tool()
async def search_all(
    query: str,
    top_k: int = 10,
    workspace_path: Optional[str] = None,
) -> Dict:
    """
    Unified search across BOTH code and docs.

    Auto-detects workspace from current directory (or use workspace_path).

    Args:
        query: Search query
        top_k: Total results (split between code and docs)
        workspace_path: Optional workspace path (auto-detects if None)

    Returns:
        Combined results with workspace, code_results, and docs_results
    """
    return await _search_all_impl(query, top_k, workspace_path)


# SYNC TOOLS


async def _sync_workspace_impl(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
) -> Dict:
    """Implementation of sync_workspace tool."""
    workspace = Path(workspace_path).resolve()
    code_collection, _ = get_collection_names(workspace)

    logger.info(f"Syncing workspace: {workspace}")

    # Create synchronizer
    sync = FileSynchronizer(
        workspace_path=workspace,
        include_patterns=include_patterns or ["*.py", "*.js", "*.ts", "*.tsx"],
    )

    # Check for changes
    changes = sync.check_changes()

    if not changes.has_changes():
        return {
            "workspace": str(workspace),
            "changes": 0,
            "added": 0,
            "modified": 0,
            "removed": 0,
            "message": "No changes detected",
        }

    # Reindex changed files
    # For now, trigger full reindex of changed files
    # TODO: Optimize to only update specific chunks
    logger.info(f"Reindexing {changes.total_changes()} changed files...")

    return {
        "workspace": str(workspace),
        "changes": changes.total_changes(),
        "added": len(changes.added),
        "modified": len(changes.modified),
        "removed": len(changes.removed),
        "message": f"Detected {changes.total_changes()} changes. Run index_workspace to update.",
    }


@mcp.tool()
async def sync_workspace(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
) -> Dict:
    """
    Sync workspace index with file changes (incremental).

    Detects added/modified/removed files using SHA256 snapshots.
    Does NOT automatically reindex - returns change report.

    Args:
        workspace_path: Absolute workspace path
        include_patterns: File patterns to track (default: code files)

    Returns:
        Change statistics
    """
    return await _sync_workspace_impl(workspace_path, include_patterns)


async def _sync_docs_impl(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
) -> Dict:
    """Implementation of sync_docs tool."""
    workspace = Path(workspace_path).resolve()

    logger.info(f"Syncing docs: {workspace}")

    # Create synchronizer for docs
    sync = FileSynchronizer(
        workspace_path=workspace,
        include_patterns=include_patterns or ["*.md", "*.pdf", "*.html", "*.txt"],
    )

    changes = sync.check_changes()

    if not changes.has_changes():
        return {
            "workspace": str(workspace),
            "changes": 0,
            "message": "No changes detected",
        }

    return {
        "workspace": str(workspace),
        "changes": changes.total_changes(),
        "added": len(changes.added),
        "modified": len(changes.modified),
        "removed": len(changes.removed),
        "message": f"Detected {changes.total_changes()} changes. Run index_docs to update.",
    }


@mcp.tool()
async def sync_docs(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
) -> Dict:
    """
    Sync docs index with file changes (incremental).

    Detects added/modified/removed documents using SHA256 snapshots.

    Args:
        workspace_path: Absolute workspace path
        include_patterns: File patterns to track (default: doc files)

    Returns:
        Change statistics
    """
    return await _sync_docs_impl(workspace_path, include_patterns)


if __name__ == "__main__":
    # Run server
    logging.basicConfig(level=logging.INFO)
    logger.info("Dope-Context MCP server starting...")
    # Components initialize on first tool call (lazy init)
    mcp.run()
