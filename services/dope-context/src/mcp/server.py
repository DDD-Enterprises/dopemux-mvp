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
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastmcp import FastMCP

from ..preprocessing.code_chunker import CodeChunker, ChunkingConfig
from ..context.openai_generator import OpenAIContextGenerator
from ..embeddings.voyage_embedder import VoyageEmbedder
from ..embeddings.contextualized_embedder import ContextualizedEmbedder
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
from ..utils.metrics_tracker import get_tracker
from ..utils.token_budget import truncate_code_results, truncate_docs_results
from ..autonomous.autonomous_controller import AutonomousController, AutonomousConfig

# ConPort-KG Integration (optional)
try:
    from integration_bridge_connector import emit_search_completed
    CONPORT_INTEGRATION_AVAILABLE = True
except ImportError:
    CONPORT_INTEGRATION_AVAILABLE = False


logger = logging.getLogger(__name__)


# Initialize FastMCP server
mcp = FastMCP("dope-context")


# ============================================================================
# ADHD Engine Integration - Dynamic result limits based on user cognitive state
# ============================================================================

# Global ADHD config (initialized on first use)
_adhd_config = None
_adhd_feature_flags = None


async def _get_adhd_config():
    """Get or initialize ADHD config singleton."""
    global _adhd_config, _adhd_feature_flags

    if _adhd_config is None:
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "adhd_engine"))

            from adhd_config_service import get_adhd_config_service
            from feature_flags import ADHDFeatureFlags

            _adhd_config = await get_adhd_config_service()
            _adhd_feature_flags = ADHDFeatureFlags(_adhd_config.redis_client)

            logger.info("✅ dope-context connected to ADHD Engine")
        except Exception as e:
            logger.warning(f"⚠️ ADHD Engine unavailable: {e}")

    return _adhd_config, _adhd_feature_flags


async def get_dynamic_top_k(user_id: str = "default", requested_top_k: int = 10) -> int:
    """
    Get dynamic top_k from ADHD Engine based on user's attention state.

    Returns:
        scattered: 5 results
        focused: 15 results
        hyperfocused: 40 results
        fallback: requested_top_k (original behavior)
    """
    adhd_config, feature_flags = await _get_adhd_config()

    if adhd_config and feature_flags:
        try:
            from feature_flags import FEATURE_ADHD_ENGINE_DOPE_CONTEXT

            if await feature_flags.is_enabled(
                FEATURE_ADHD_ENGINE_DOPE_CONTEXT,
                "dope-context",
                user_id
            ):
                return await adhd_config.get_max_results(user_id)
        except Exception as e:
            logger.error(f"ADHD Engine query failed: {e}")

    # Fallback to requested value
    return requested_top_k


# ============================================================================
# Component Caching Layer - Reduces overhead from ~500ms to ~50ms per search
# ============================================================================

@lru_cache(maxsize=10)
def _get_cached_embedder(api_key: str, model: str = "voyage-code-3") -> VoyageEmbedder:
    """
    Get cached VoyageEmbedder instance (reuses HTTP client).

    Args:
        api_key: Voyage API key (used as cache key)
        model: Default model name

    Returns:
        Cached VoyageEmbedder instance
    """
    logger.info(f"Creating cached VoyageEmbedder for model: {model}")
    return VoyageEmbedder(
        api_key=api_key,
        default_model=model,
    )


@lru_cache(maxsize=10)
def _get_cached_reranker(api_key: str) -> VoyageReranker:
    """
    Get cached VoyageReranker instance (reuses HTTP client).

    Args:
        api_key: Voyage API key (used as cache key)

    Returns:
        Cached VoyageReranker instance
    """
    logger.info("Creating cached VoyageReranker")
    return VoyageReranker(api_key=api_key)


@lru_cache(maxsize=20)
def _get_cached_vector_search(
    collection_name: str,
    url: str,
    port: int
) -> MultiVectorSearch:
    """
    Get cached MultiVectorSearch instance (reuses Qdrant client).

    Args:
        collection_name: Qdrant collection name
        url: Qdrant URL
        port: Qdrant port

    Returns:
        Cached MultiVectorSearch instance
    """
    logger.info(f"Creating cached MultiVectorSearch for collection: {collection_name}")
    return MultiVectorSearch(
        collection_name=collection_name,
        url=url,
        port=port,
    )


@lru_cache(maxsize=10)
def _get_cached_contextualized_embedder(api_key: str) -> ContextualizedEmbedder:
    """
    Get cached ContextualizedEmbedder instance (for docs).

    Args:
        api_key: Voyage API key

    Returns:
        Cached ContextualizedEmbedder instance
    """
    logger.info("Creating cached ContextualizedEmbedder for docs")
    return ContextualizedEmbedder(
        api_key=api_key,
        cache_ttl_hours=24,
    )


@lru_cache(maxsize=20)
def _get_cached_document_search(
    collection_name: str,
    url: str,
    port: int
) -> DocumentSearch:
    """
    Get cached DocumentSearch instance (reuses Qdrant client).

    Args:
        collection_name: Qdrant collection name
        url: Qdrant URL
        port: Qdrant port

    Returns:
        Cached DocumentSearch instance
    """
    logger.info(f"Creating cached DocumentSearch for collection: {collection_name}")
    return DocumentSearch(
        collection_name=collection_name,
        url=url,
        port=port,
    )


# Global state (initialized on startup)
_pipeline: Optional[IndexingPipeline] = None
_hybrid_search: Optional[HybridSearch] = None
_reranker: Optional[VoyageReranker] = None
_embedder: Optional[VoyageEmbedder] = None
_bm25_index: Optional[BM25Index] = None

# Docs pipeline (new)
_docs_pipeline: Optional[DocIndexingPipeline] = None
_docs_search: Optional[DocumentSearch] = None
_docs_embedder: Optional[ContextualizedEmbedder] = None


def _initialize_components():
    """Initialize all pipeline components."""
    global _pipeline, _hybrid_search, _reranker, _embedder, _bm25_index
    global _docs_pipeline, _docs_search, _docs_embedder

    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    voyage_key = os.getenv("VOYAGE_API_KEY")
    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    if not voyage_key:
        raise ValueError("VOYAGE_API_KEY environment variable required")

    # Detect workspace and get collection names
    workspace_root = get_workspace_root()
    code_collection, docs_collection = get_collection_names(workspace_root)
    logger.info(f"Using workspace: {workspace_root}")
    logger.info(f"Code collection: {code_collection}, Docs collection: {docs_collection}")

    # Initialize components
    chunker = CodeChunker(config=ChunkingConfig())

    context_generator = None
    if openai_key:
        context_generator = OpenAIContextGenerator(api_key=openai_key)
    else:
        logger.warning("OPENAI_API_KEY not set - context generation disabled")

    _embedder = VoyageEmbedder(api_key=voyage_key)

    # Create contextualized embedder for code content vectors
    code_contextualized_embedder = ContextualizedEmbedder(
        api_key=voyage_key,
        cache_ttl_hours=24,
    )

    vector_search = MultiVectorSearch(
        collection_name=code_collection,
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
        standard_embedder=_embedder,
        contextualized_embedder=code_contextualized_embedder,
        vector_search=vector_search,
        config=config,
    )

    # Initialize docs components (contextualized embeddings)
    _docs_embedder = ContextualizedEmbedder(
        api_key=voyage_key,
        cache_ttl_hours=24,
    )

    _docs_search = DocumentSearch(
        collection_name=docs_collection,
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

    openai_key = os.getenv("OPENAI_API_KEY")
    context_generator = None
    if openai_key:
        context_generator = OpenAIContextGenerator(api_key=openai_key)

    standard_embedder = VoyageEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        default_model="voyage-code-3",
    )

    # Create contextualized embedder for content vectors
    contextualized_embedder = ContextualizedEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        cache_ttl_hours=24,
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
        standard_embedder=standard_embedder,
        contextualized_embedder=contextualized_embedder,
        vector_search=vector_search,
        config=config,
    )

    # Run indexing
    progress = await pipeline.index_workspace()

    # Build BM25 index for hybrid search (after vector indexing completes)
    try:
        logger.info("Building BM25 index for keyword search...")

        # Get all indexed documents from Qdrant
        all_docs = await vector_search.get_all_payloads()

        if all_docs:
            bm25_index = BM25Index()
            bm25_index.build_index(all_docs)

            # Persist BM25 to disk for fast loading
            bm25_cache_path = get_snapshot_dir(workspace) / "bm25_index.pkl"
            with open(bm25_cache_path, 'wb') as f:
                pickle.dump({
                    'bm25': bm25_index.bm25,
                    'documents': bm25_index.documents,
                    'doc_ids': bm25_index.doc_ids,
                }, f)
            logger.info(f"BM25 index built and cached: {len(all_docs)} documents")
        else:
            logger.warning("No documents to build BM25 index")

    except Exception as bm25_error:
        logger.warning(f"BM25 index building failed (non-fatal): {bm25_error}")
        # Non-fatal - dense search will still work

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

    🎯 **WHEN TO USE**:
    - **First time setup**: Enable semantic search for a new project
    - **Major updates**: Reindex after significant code changes
    - **Search failures**: Fix "codebase not indexed" errors

    ⚙️ **CONFIGURATION**:
    - Default patterns: ["*.py", "*.js", "*.ts", "*.tsx"]
    - Auto-excludes: tests, __pycache__, node_modules, .git
    - ADHD-friendly: Runs in background, search works during indexing

    Args:
        workspace_path: Absolute path to workspace root
        include_patterns: File patterns to include (e.g., ["*.py", "*.ts"])
        exclude_patterns: File patterns to exclude (e.g., ["*test*"])
        max_files: Maximum files to index (optional, for large repos)

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
    budget_tokens: int = 9000,
    user_id: str = "default",
) -> List[Dict]:
    """Implementation of search_code tool (NOW WITH DYNAMIC TOP_K!)."""
    try:
        # Get dynamic top_k from ADHD Engine
        top_k = await get_dynamic_top_k(user_id, top_k)

        # Detect workspace
        workspace = Path(workspace_path) if workspace_path else get_workspace_root()
        code_collection, _ = get_collection_names(workspace)

        # Log metrics for benchmarking
        get_tracker().log_search(
            tool_name="search_code",
            query=query,
            workspace=str(workspace),
            top_k=top_k
        )

        logger.info(f"Searching workspace: {workspace} → collection: {code_collection}")

        # Check API keys first
        voyage_key = os.getenv("VOYAGE_API_KEY")
        if not voyage_key:
            logger.error("VOYAGE_API_KEY not set")
            return [{
                "error": "VOYAGE_API_KEY environment variable not set",
                "help": "Set VOYAGE_API_KEY in your environment to enable embeddings and reranking"
            }]

        # Get cached components (reuses HTTP clients and connections)
        qdrant_url = os.getenv("QDRANT_URL", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

        vector_search = _get_cached_vector_search(
            collection_name=code_collection,
            url=qdrant_url,
            port=qdrant_port,
        )

        # Check if collection exists and has data
        try:
            collection_info = await vector_search.get_collection_info()
            vector_count = collection_info.get("vectors_count", 0)

            if vector_count == 0:
                logger.warning(f"Collection '{code_collection}' is empty")
                return [{
                    "error": f"Collection '{code_collection}' is empty. Run index_workspace first.",
                    "workspace": str(workspace),
                    "collection": code_collection,
                    "help": f"Run: mcp__dope-context__index_workspace(workspace_path='{workspace}')"
                }]
        except Exception as collection_error:
            logger.error(f"Collection check failed: {collection_error}")
            return [{
                "error": f"Collection '{code_collection}' not found or inaccessible.",
                "workspace": str(workspace),
                "collection": code_collection,
                "details": str(collection_error),
                "help": f"Run: mcp__dope-context__index_workspace(workspace_path='{workspace}')"
            }]

        embedder = _get_cached_embedder(
            api_key=voyage_key,
            model="voyage-code-3",
        )

        # Load BM25 index from cache if available
        bm25_index = BM25Index()
        bm25_cache_path = get_snapshot_dir(workspace) / "bm25_index.pkl"

        if bm25_cache_path.exists():
            try:
                with open(bm25_cache_path, 'rb') as f:
                    cached = pickle.load(f)
                bm25_index.bm25 = cached['bm25']
                bm25_index.documents = cached['documents']
                bm25_index.doc_ids = cached['doc_ids']
                logger.info(f"Loaded BM25 index from cache: {len(bm25_index.doc_ids)} docs")
            except Exception as cache_error:
                logger.warning(f"BM25 cache load failed, dense-only search: {cache_error}")
                bm25_index = BM25Index()  # Empty fallback
        else:
            logger.info(f"No BM25 cache found at {bm25_cache_path}, using dense-only search")

        hybrid_search = HybridSearch(
            dense_search=vector_search,
            bm25_index=bm25_index,
        )

        reranker = _get_cached_reranker(api_key=voyage_key)

    except Exception as setup_error:
        logger.error(f"Search setup failed: {setup_error}", exc_info=True)
        return [{
            "error": f"Search initialization failed: {str(setup_error)}",
            "query": query,
            "workspace": str(workspace) if 'workspace' in locals() else "unknown"
        }]

    try:
        # Select profile
        profile_map = {
            "implementation": SearchProfile.implementation(),
            "debugging": SearchProfile.debugging(),
            "exploration": SearchProfile.exploration(),
        }
        search_profile = profile_map.get(profile, SearchProfile.implementation())

        # Embed query (3 vectors)
        try:
            query_content = await embedder.embed(
                text=query,
                model="voyage-code-3",
                input_type="query",
            )

            query_title = await embedder.embed(
                text=query,
                model="voyage-code-3",
                input_type="query",
            )

            query_breadcrumb = await embedder.embed(
                text=query,
                model="voyage-code-3",
                input_type="query",
            )
        except Exception as embed_error:
            logger.error(f"Embedding failed: {embed_error}")
            return [{
                "error": f"Query embedding failed: {str(embed_error)}",
                "query": query,
                "help": "Check VOYAGE_API_KEY and network connectivity"
            }]

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
        try:
            search_results = await hybrid_search.search(
                query_vectors=query_vectors,
                query_text=query,
                profile=search_profile,
                filter_by=filter_by if filter_by else None,
            )
        except Exception as search_error:
            logger.error(f"Search failed: {search_error}")
            return [{
                "error": f"Vector search failed: {str(search_error)}",
                "query": query,
                "workspace": str(workspace),
                "collection": code_collection
            }]

        # Rerank if requested
        if use_reranking and search_results:
            try:
                rerank_response = await reranker.rerank(
                    query=query,
                    results=search_results[:50],  # Rerank top-50
                )

                # Return top-k from reranked
                final_results = rerank_response.top_results[:top_k]

                raw_results = [
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

                # Apply token budget truncation
                truncated_results, trunc_info = truncate_code_results(
                    raw_results,
                    budget_tokens=budget_tokens,  # Passed from caller (9K default, 4K for unified)
                    per_item_max_chars=2000,  # ~500 tokens per code snippet
                )

                # Log truncation if it occurred
                if trunc_info.truncated:
                    logger.info(
                        f"Token budget applied: {trunc_info.final_count}/{trunc_info.original_count} results, "
                        f"{trunc_info.estimated_tokens} tokens ({trunc_info.budget_used_pct:.1f}% of budget)"
                    )

                return truncated_results
            except Exception as rerank_error:
                logger.warning(f"Reranking failed, returning dense results: {rerank_error}")
                # Fall through to return without reranking

        # Return without reranking (or reranking failed)
        raw_results = [
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

        # Apply token budget truncation
        truncated_results, trunc_info = truncate_code_results(
            raw_results,
            budget_tokens=budget_tokens,
            per_item_max_chars=2000,
        )

        if trunc_info.truncated:
            logger.info(
                f"Token budget applied: {trunc_info.final_count}/{trunc_info.original_count} results, "
                f"{trunc_info.estimated_tokens} tokens ({trunc_info.budget_used_pct:.1f}% of budget)"
            )

        return truncated_results

    except Exception as execution_error:
        logger.error(f"Search execution failed: {execution_error}", exc_info=True)
        return [{
            "error": f"Search execution failed: {str(execution_error)}",
            "query": query,
            "workspace": str(workspace)
        }]


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

    🎯 **WHEN TO USE** (Search BEFORE these tasks):
    - **Understanding code**: Find how features are implemented
    - **Making changes**: Gather context before modifying code
    - **Debugging issues**: Locate problematic code sections or bugs
    - **Code review**: Understand patterns and existing implementations
    - **Refactoring**: Find all related code pieces that need updates
    - **Feature development**: Learn from similar existing features
    - **Answering questions**: Get relevant code examples and context
    - **Impact analysis**: Find what depends on code you're changing

    🧠 **ADHD OPTIMIZATION**:
    - Max 10 results by default (prevents overwhelm)
    - Progressive disclosure (essential info first)
    - Reranking enabled (best results at top)

    Auto-detects workspace from current directory (or use workspace_path).

    Args:
        query: Natural language search query
        top_k: Number of results to return (default 10, max 50 for ADHD)
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

    docs_embedder = ContextualizedEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        cache_ttl_hours=24,
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
    max_content_length: int = 2000,
    budget_tokens: int = 9000,
) -> List[Dict]:
    """Implementation of docs_search tool."""
    # Detect workspace
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()
    _, docs_collection = get_collection_names(workspace)

    # Log metrics for benchmarking
    get_tracker().log_search(
        tool_name="docs_search",
        query=query,
        workspace=str(workspace),
        top_k=top_k
    )

    logger.info(f"Searching docs: {workspace} → collection: {docs_collection}")

    # Check API key
    voyage_key = os.getenv("VOYAGE_API_KEY")
    if not voyage_key:
        logger.error("VOYAGE_API_KEY not set")
        return [{
            "error": "VOYAGE_API_KEY environment variable not set",
            "help": "Set VOYAGE_API_KEY in your environment"
        }]

    # Get cached components (reuses HTTP clients and connections)
    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    docs_search = _get_cached_document_search(
        collection_name=docs_collection,
        url=qdrant_url,
        port=qdrant_port,
    )

    docs_embedder = _get_cached_contextualized_embedder(api_key=voyage_key)

    # Embed query with voyage-context-3 (contextualized)
    result = await docs_embedder.embed_document(
        chunks=[query],  # Single "chunk" for query
        model="voyage-context-3",
        input_type="query",
        output_dimension=1024,
    )

    # Use same vector for all three (voyage-context-3 has full context)
    query_embedding = result.embeddings[0]
    query_vectors = {
        "content": query_embedding,
        "title": query_embedding,
        "breadcrumb": query_embedding,
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

    # Build raw results with per-item truncation
    raw_results = [
        {
            "source_path": r.file_path,
            "text": r.content[:max_content_length] + ("..." if len(r.content) > max_content_length else ""),
            "score": r.score,
            "doc_type": r.payload.get("doc_type", "unknown"),
            "truncated": len(r.content) > max_content_length,
            "original_length": len(r.content),
        }
        for r in results[:top_k]
    ]

    # Apply token budget truncation across entire result set
    truncated_results, trunc_info = truncate_docs_results(
        raw_results,
        budget_tokens=budget_tokens,
        per_item_max_chars=max_content_length,
    )

    if trunc_info.truncated:
        logger.info(
            f"Docs token budget applied: {trunc_info.final_count}/{trunc_info.original_count} results, "
            f"{trunc_info.estimated_tokens} tokens ({trunc_info.budget_used_pct:.1f}% of budget)"
        )

    return truncated_results


@mcp.tool()
async def docs_search(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
    max_content_length: int = 2000,
) -> List[Dict]:
    """
    Search indexed documents (PDF, Markdown, HTML, text).

    🎯 **WHEN TO USE**:
    - **Learning architecture**: Find design docs, ADRs, and system overviews
    - **API reference**: Locate endpoint documentation and API guides
    - **Setup guides**: Find installation, configuration, and deployment docs
    - **Troubleshooting**: Search error messages, FAQs, and solutions
    - **Requirements**: Find PRDs, feature specifications, and user stories

    Auto-detects workspace from current directory (or use workspace_path).

    Args:
        query: Natural language search query
        top_k: Number of results to return (default 10)
        filter_doc_type: Filter by document type (md, pdf, html, txt)
        workspace_path: Optional workspace path (auto-detects if None)
        max_content_length: Max characters per doc (default 2000, prevents token overflow)

    Returns:
        List of document search results with truncated text and scores.
        Each result includes 'truncated' boolean and 'original_length' for reference.
    """
    return await _docs_search_impl(query, top_k, filter_doc_type, workspace_path, max_content_length)


async def _search_all_impl(
    query: str,
    top_k: int = 10,
    workspace_path: Optional[str] = None,
) -> Dict:
    """Implementation of unified search_all tool."""
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()

    # Log metrics for benchmarking
    get_tracker().log_search(
        tool_name="search_all",
        query=query,
        workspace=str(workspace),
        top_k=top_k
    )

    logger.info(f"Unified search in workspace: {workspace}")

    # Search both code and docs in parallel (split budget to stay under 10K)
    # Each gets 4K token budget (4K code + 4K docs + 1K overhead = 9K total)
    code_results_task = _search_code_impl(
        query, top_k // 2, use_reranking=False, workspace_path=str(workspace),
        budget_tokens=4000  # Half budget for unified search
    )
    docs_results_task = _docs_search_impl(
        query, top_k // 2, workspace_path=str(workspace), max_content_length=1500,
        budget_tokens=4000  # Half budget for unified search
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

    🎯 **WHEN TO USE**:
    - **Complete context**: Need both implementation and documentation together
    - **Feature exploration**: Understand code alongside design docs
    - **Onboarding**: Learn codebase with docs as guide
    - **Cross-reference**: Verify code matches documented behavior

    Auto-detects workspace from current directory (or use workspace_path).

    Args:
        query: Natural language search query
        top_k: Total results (split between code and docs, default 10)
        workspace_path: Optional workspace path (auto-detects if None)

    Returns:
        Combined results with workspace, code_results, docs_results, total_results
    """
    return await _search_all_impl(query, top_k, workspace_path)


# SYNC TOOLS


async def _sync_workspace_impl(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
    auto_reindex: bool = False,
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

    # Incremental reindexing if requested
    if auto_reindex:
        logger.info(f"Auto-reindexing {changes.total_changes()} changed files...")

        try:
            # Get cached components
            qdrant_url = os.getenv("QDRANT_URL", "localhost")
            qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
            vector_search = _get_cached_vector_search(code_collection, qdrant_url, qdrant_port)

            # Create pipeline for incremental updates
            chunker = CodeChunker()
            openai_key = os.getenv("OPENAI_API_KEY")
            context_generator = OpenAIContextGenerator(api_key=openai_key) if openai_key else None
            embedder = _get_cached_embedder(api_key=os.getenv("VOYAGE_API_KEY"))

            config = IndexingConfig(
                workspace_path=workspace,
                include_patterns=include_patterns or ["*.py", "*.js", "*.ts", "*.tsx"],
                workspace_id=str(workspace),
            )

            pipeline = IndexingPipeline(
                chunker=chunker,
                context_generator=context_generator,
                embedder=embedder,
                vector_search=vector_search,
                config=config,
            )

            # Index only changed files
            changed_files = changes.added + changes.modified
            if changed_files:
                # Create temporary config with only changed files
                temp_config = IndexingConfig(
                    workspace_path=workspace,
                    include_patterns=changed_files,  # Only these specific files
                    workspace_id=str(workspace),
                )
                pipeline.config = temp_config
                await pipeline.index_workspace()
                logger.info(f"Reindexed {len(changed_files)} added/modified files")

            # Delete removed files from collection
            if changes.removed:
                # TODO: Delete specific point IDs for removed files
                logger.info(f"Note: {len(changes.removed)} files removed (manual cleanup needed)")

            # Rebuild BM25 index after incremental changes
            try:
                all_docs = await vector_search.get_all_payloads()
                if all_docs:
                    bm25_index = BM25Index()
                    bm25_index.build_index(all_docs)
                    bm25_cache_path = get_snapshot_dir(workspace) / "bm25_index.pkl"
                    with open(bm25_cache_path, 'wb') as f:
                        pickle.dump({
                            'bm25': bm25_index.bm25,
                            'documents': bm25_index.documents,
                            'doc_ids': bm25_index.doc_ids,
                        }, f)
                    logger.info("BM25 index updated after sync")
            except Exception as bm25_error:
                logger.warning(f"BM25 update failed: {bm25_error}")

            return {
                "workspace": str(workspace),
                "changes": changes.total_changes(),
                "added": len(changes.added),
                "modified": len(changes.modified),
                "removed": len(changes.removed),
                "reindexed": len(changed_files),
                "message": f"Synced and reindexed {len(changed_files)} files",
            }

        except Exception as reindex_error:
            logger.error(f"Auto-reindex failed: {reindex_error}")
            return {
                "workspace": str(workspace),
                "changes": changes.total_changes(),
                "added": len(changes.added),
                "modified": len(changes.modified),
                "removed": len(changes.removed),
                "error": f"Sync detected changes but reindexing failed: {str(reindex_error)}",
                "message": f"Detected {changes.total_changes()} changes. Run index_workspace manually.",
            }

    # Just report changes without reindexing
    return {
        "workspace": str(workspace),
        "changes": changes.total_changes(),
        "added": len(changes.added),
        "modified": len(changes.modified),
        "removed": len(changes.removed),
        "message": f"Detected {changes.total_changes()} changes. Run index_workspace to update or use auto_reindex=True.",
    }


@mcp.tool()
async def sync_workspace(
    workspace_path: str,
    include_patterns: Optional[List[str]] = None,
    auto_reindex: bool = False,
) -> Dict:
    """
    Sync workspace index with file changes (incremental).

    Detects added/modified/removed files using SHA256 snapshots.
    Optionally auto-reindexes changed files for true incremental updates.

    Args:
        workspace_path: Absolute workspace path
        include_patterns: File patterns to track (default: code files)
        auto_reindex: Automatically reindex changed files (default: False)

    Returns:
        Change statistics and reindex results
    """
    return await _sync_workspace_impl(workspace_path, include_patterns, auto_reindex)


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


@mcp.tool()
async def get_search_metrics(since_timestamp: Optional[str] = None) -> Dict:
    """
    Get search usage metrics for benchmarking.

    🎯 **USE CASE**: Measure how often LLM uses semantic search

    Args:
        since_timestamp: Optional ISO timestamp (e.g., "2025-10-04T12:00:00")
                        Only include metrics after this time

    Returns:
        {
            "total_searches": int,
            "explicit_searches": int,  # User said "find" or "search"
            "implicit_searches": int,  # LLM searched automatically
            "explicit_percentage": float,
            "implicit_percentage": float,
            "scenarios": {scenario: count},
            "tools": {tool_name: count},
            "sample_queries": {scenario: [query1, query2, query3]}
        }
    """
    return get_tracker().get_summary(since_timestamp=since_timestamp)


@mcp.tool()
async def clear_search_metrics() -> Dict:
    """
    Clear all search metrics (for fresh baseline).

    🎯 **USE CASE**: Reset metrics before/after enhancement testing

    Returns:
        Success message
    """
    get_tracker().clear_metrics()
    return {"status": "success", "message": "All search metrics cleared"}


# ============================================================================
# Autonomous Indexing Tools - Zero-Touch Operation
# ============================================================================


@mcp.tool()
async def start_autonomous_indexing(
    workspace_path: str = None,
    debounce_seconds: float = 5.0,
    periodic_interval: int = 600,
) -> Dict:
    """
    Enable autonomous indexing for workspace.

    🎯 **ADHD BENEFIT**: Zero mental overhead - index updates automatically
    as you code. No manual sync needed ever again!

    Starts three monitoring systems:
    1. File watcher (watchdog) - Immediate response to changes
    2. 5s debouncing - Batches rapid saves for efficiency
    3. 10min periodic fallback - Catches any missed events

    Args:
        workspace_path: Workspace to monitor (defaults to cwd)
        debounce_seconds: Wait time after file changes (default: 5.0)
        periodic_interval: Fallback check interval (default: 600s/10min)

    Returns:
        Status and configuration info
    """
    workspace = get_workspace_root(workspace_path)

    logger.info(f"Starting autonomous indexing for {workspace}")

    # Check if already running
    workspace_key = str(workspace)
    active = AutonomousController.get_active_controllers()

    if workspace_key in active:
        return {
            "status": "already_running",
            "workspace": str(workspace),
            "message": "Autonomous indexing already active for this workspace",
        }

    # Create config
    config = AutonomousConfig(
        enabled=True,
        debounce_seconds=debounce_seconds,
        periodic_interval=periodic_interval,
    )

    # Create callbacks
    async def index_callback(ws_path: Path, changed_files: Optional[Set[str]]):
        """Callback to trigger indexing."""
        await _index_workspace_impl(
            workspace_path=str(ws_path),
            include_patterns=config.include_patterns,
            exclude_patterns=config.exclude_patterns,
        )

    async def sync_callback(ws_path: Path):
        """Callback to trigger sync."""
        return await _sync_workspace_impl(str(ws_path))

    # Create and start controller
    controller = AutonomousController(
        workspace_path=workspace,
        index_callback=index_callback,
        sync_callback=sync_callback,
        config=config,
    )

    await controller.start()

    return {
        "status": "started",
        "workspace": str(workspace),
        "config": {
            "debounce_seconds": debounce_seconds,
            "periodic_interval": periodic_interval,
        },
        "message": f"Autonomous indexing started for {workspace.name}",
    }


@mcp.tool()
async def stop_autonomous_indexing(workspace_path: str = None) -> Dict:
    """
    Stop autonomous indexing for workspace.

    🎯 **USE CASE**: Disable auto-indexing when not needed (saves resources)

    Args:
        workspace_path: Workspace to stop monitoring (defaults to cwd)

    Returns:
        Status info
    """
    workspace = get_workspace_root(workspace_path)
    workspace_key = str(workspace)

    active = AutonomousController.get_active_controllers()

    if workspace_key not in active:
        return {
            "status": "not_running",
            "workspace": str(workspace),
            "message": "No autonomous indexing active for this workspace",
        }

    # Stop controller
    controller = active[workspace_key]
    await controller.stop()

    return {
        "status": "stopped",
        "workspace": str(workspace),
        "message": f"Autonomous indexing stopped for {workspace.name}",
    }


@mcp.tool()
async def get_autonomous_status() -> Dict:
    """
    Get status of all autonomous indexers (code AND docs).

    🎯 **USE CASE**: Health monitoring and debugging

    Returns comprehensive status for all active autonomous indexers including:
    - Workspace paths
    - Type (code or docs)
    - Running state
    - Watchdog status (pending changes)
    - Worker stats (tasks processed, success rate, queue size)
    - Periodic sync stats (sync count, changes detected)

    Returns:
        Dictionary with status of all active controllers
    """
    active = AutonomousController.get_active_controllers()

    if not active:
        return {
            "active_count": 0,
            "code_controllers": [],
            "docs_controllers": [],
            "message": "No autonomous indexing active",
        }

    code_statuses = []
    docs_statuses = []

    for workspace_key, controller in active.items():
        status = controller.get_status()

        # Add type based on workspace key
        if ":docs" in workspace_key:
            status["type"] = "docs"
            docs_statuses.append(status)
        else:
            status["type"] = "code"
            code_statuses.append(status)

    return {
        "active_count": len(active),
        "code_controllers": code_statuses,
        "docs_controllers": docs_statuses,
        "summary": {
            "code_active": len(code_statuses),
            "docs_active": len(docs_statuses),
        },
    }


async def _sync_workspace_impl(workspace_path: str) -> Dict:
    """
    Internal implementation of sync_workspace.

    Args:
        workspace_path: Workspace to sync

    Returns:
        Change detection results
    """
    workspace = Path(workspace_path).resolve()

    synchronizer = FileSynchronizer(
        workspace_path=workspace,
        include_patterns=["*.py", "*.js", "*.ts", "*.tsx"],
        exclude_patterns=[
            "__pycache__",
            "*.pyc",
            "node_modules",
            ".git",
            "dist",
            "build",
        ],
    )

    changes = synchronizer.check_changes()

    return {
        "workspace": str(workspace),
        "added": len(changes.added),
        "modified": len(changes.modified),
        "removed": len(changes.removed),
        "total_changes": changes.total_changes(),
        "has_changes": changes.has_changes(),
        "added_files": changes.added[:10],  # Sample
        "modified_files": changes.modified[:10],
        "removed_files": changes.removed[:10],
    }


# AUTONOMOUS DOCS INDEXING

@mcp.tool()
async def start_autonomous_docs_indexing(
    workspace_path: str = None,
    debounce_seconds: float = 5.0,
    periodic_interval: int = 600,
) -> Dict:
    """
    Enable autonomous docs indexing for workspace.

    🎯 **ADHD BENEFIT**: Zero mental overhead - docs index updates automatically
    as you edit markdown/PDFs. No manual sync needed!

    Starts three monitoring systems:
    1. File watcher (watchdog) - Immediate response to doc changes
    2. 5s debouncing - Batches rapid saves for efficiency
    3. 10min periodic fallback - Catches any missed events

    Args:
        workspace_path: Workspace to monitor (defaults to cwd)
        debounce_seconds: Wait time after file changes (default: 5.0)
        periodic_interval: Fallback check interval (default: 600s/10min)

    Returns:
        Status and configuration info
    """
    workspace = get_workspace_root(workspace_path)

    logger.info(f"Starting autonomous docs indexing for {workspace}")

    # Check if already running (use different key for docs)
    workspace_key = f"{workspace}:docs"
    active = AutonomousController.get_active_controllers()

    if workspace_key in active:
        return {
            "status": "already_running",
            "workspace": str(workspace),
            "type": "docs",
            "message": "Autonomous docs indexing already active for this workspace",
        }

    # Create config for docs (different patterns)
    config = AutonomousConfig(
        enabled=True,
        debounce_seconds=debounce_seconds,
        periodic_interval=periodic_interval,
        include_patterns=["*.md", "*.pdf", "*.html", "*.txt"],
        exclude_patterns=[
            ".git",
            "node_modules",
            "__pycache__",
            "dist",
            "build",
            ".venv",
            "venv",
        ],
    )

    # Create callbacks
    async def docs_index_callback(ws_path: Path, changed_files: Optional[Set[str]]):
        """Callback to trigger docs indexing."""
        await _index_docs_impl(
            workspace_path=str(ws_path),
            include_patterns=config.include_patterns,
        )

    async def docs_sync_callback(ws_path: Path):
        """Callback to trigger docs sync."""
        return await _sync_docs_impl(
            str(ws_path),
            config.include_patterns,
        )

    # Create and start controller
    controller = AutonomousController(
        workspace_path=workspace,
        index_callback=docs_index_callback,
        sync_callback=docs_sync_callback,
        config=config,
    )

    await controller.start()

    # Register with docs-specific key
    AutonomousController._active_controllers[workspace_key] = controller

    return {
        "status": "started",
        "workspace": str(workspace),
        "type": "docs",
        "config": {
            "debounce_seconds": debounce_seconds,
            "periodic_interval": periodic_interval,
            "patterns": config.include_patterns,
        },
        "message": f"Autonomous docs indexing started for {workspace.name}",
    }


@mcp.tool()
async def stop_autonomous_docs_indexing(workspace_path: str = None) -> Dict:
    """
    Stop autonomous docs indexing for workspace.

    🎯 **USE CASE**: Disable auto-indexing when not needed (saves resources)

    Args:
        workspace_path: Workspace to stop monitoring (defaults to cwd)

    Returns:
        Status info
    """
    workspace = get_workspace_root(workspace_path)
    workspace_key = f"{workspace}:docs"

    active = AutonomousController.get_active_controllers()

    if workspace_key not in active:
        return {
            "status": "not_running",
            "workspace": str(workspace),
            "type": "docs",
            "message": "No autonomous docs indexing active for this workspace",
        }

    # Stop controller
    controller = active[workspace_key]
    await controller.stop()

    return {
        "status": "stopped",
        "workspace": str(workspace),
        "type": "docs",
        "message": f"Autonomous docs indexing stopped for {workspace.name}",
    }


@mcp.tool()
async def get_chunk_complexity(file_path: str, symbol: str) -> Dict:
    """
    Get AST-based complexity for code chunk (Synergy A support).

    Returns complexity score 0.0-1.0 from Tree-sitter analysis.
    """
    # TODO: Extract from existing chunking pipeline
    # For now, return moderate complexity
    return {"complexity": 0.5, "method": "tree-sitter-ast", "file_path": file_path, "symbol": symbol}


if __name__ == "__main__":
    # Run server
    logging.basicConfig(level=logging.INFO)
    logger.info("Dope-Context MCP server starting...")
    # Components initialize on first tool call (lazy init)
    mcp.run()
