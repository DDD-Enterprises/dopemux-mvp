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
import ast
import json
import logging
import os
import pickle
import subprocess
import aiohttp
from time import perf_counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

FASTMCP_AVAILABLE = True
try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - exercised in constrained envs
    from .fastmcp_stub import FastMCP
    FASTMCP_AVAILABLE = False
try:
    from starlette.requests import Request
    from starlette.responses import JSONResponse
except ImportError:  # pragma: no cover - for constrained test envs
    class Request:  # type: ignore
        """Fallback request stub."""

        def __init__(self, *args, **kwargs):
            self._starlette_unavailable = True

    class JSONResponse(dict):  # type: ignore
        """Fallback JSON response stub."""

        def __init__(self, content=None, **kwargs):
            super().__init__(content or {})

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
from ..utils.workspace import get_workspace_root, get_collection_names, get_snapshot_dir, workspace_to_hash
from ..sync.file_synchronizer import FileSynchronizer, ChangeSet
from ..utils.metrics_tracker import get_tracker
from ..utils.token_budget import truncate_code_results, truncate_docs_results
from ..autonomous.autonomous_controller import AutonomousController, AutonomousConfig

# ConPort-KG Integration (optional)
try:
    from dopecon_bridge_connector import emit_search_completed
    CONPORT_INTEGRATION_AVAILABLE = True
except ImportError:
    CONPORT_INTEGRATION_AVAILABLE = False


logger = logging.getLogger(__name__)

if not FASTMCP_AVAILABLE:
    logger.warning(
        "fastmcp package not installed; falling back to stub FastMCP. "
        "MCP tools remain importable but server.run() is a no-op."
    )

TRINITY_DECISION_DEFAULT_LIMIT = 3
TRINITY_DECISION_MAX_LIMIT = 10
TRINITY_BOUNDARY_MARKER = "search-memory-authority-boundary-v1"


# Initialize FastMCP server
mcp = FastMCP("dope-context")


def _resolve_transport_runtime() -> Tuple[str, str, int]:
    """Resolve active MCP transport/host/port deterministically."""
    transport_env = os.getenv("MCP_TRANSPORT") or os.getenv("FASTMCP_TRANSPORT")
    if transport_env:
        transport = transport_env.strip().lower()
    elif os.getenv("MCP_SERVER_PORT"):
        transport = "http"
    else:
        transport = "stdio"

    valid_transports = {"stdio", "http", "sse", "streamable-http"}
    if transport not in valid_transports:
        logger.warning("Unknown MCP transport '%s'; defaulting to 'stdio'", transport)
        transport = "stdio"

    host = (
        os.getenv("MCP_SERVER_HOST")
        or os.getenv("FASTMCP_HOST")
        or "0.0.0.0"
    )
    port_str = (
        os.getenv("MCP_SERVER_PORT")
        or os.getenv("FASTMCP_PORT")
        or os.getenv("PORT")
    )
    try:
        port = int(port_str) if port_str else 3010
    except (TypeError, ValueError):
        logger.warning("Invalid MCP_SERVER_PORT '%s'; defaulting to 3010", port_str)
        port = 3010

    if transport == "stdio":
        return transport, "stdio", 0
    return transport, host, port


def _transport_connection_url(transport: str, host: str, port: int) -> str:
    """Build user-facing MCP connection URL from runtime transport."""
    if transport == "stdio":
        return "stdio://mcp"
    return f"http://localhost:{port}/mcp"


def _normalize_decision_limit(limit_value: Any) -> int:
    """Clamp cross-plane decision retrieval limits to Trinity boundary rails."""
    try:
        parsed = int(limit_value)
    except (TypeError, ValueError):
        parsed = TRINITY_DECISION_DEFAULT_LIMIT
    return max(1, min(parsed, TRINITY_DECISION_MAX_LIMIT))


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_: Request) -> JSONResponse:
    """Basic health endpoint for container probes."""
    return JSONResponse({"status": "ok"})


@mcp.custom_route("/info", methods=["GET"])
async def service_info(_: Request) -> JSONResponse:
    """Service discovery endpoint - auto-config support (ADR-208)"""
    transport, host, port = _resolve_transport_runtime()
    connection_url = _transport_connection_url(transport, host, port)
    warning = (
        "fastmcp package not installed; stub server active and MCP run loop is a no-op."
        if not FASTMCP_AVAILABLE
        else None
    )
    return JSONResponse({
        "name": "dope-context",
        "version": "1.0.0",
        "fastmcp_available": FASTMCP_AVAILABLE,
        "canonical_entrypoint": "python -m src.mcp.server",
        "mcp": {
            "protocol": "stdio" if transport == "stdio" else "sse",
            "connection": {
                "type": "stdio" if transport == "stdio" else "sse",
                "url": connection_url
            },
            "env": {
                "VOYAGE_API_KEY": "${VOYAGEAI_API_KEY:-}",
                "OPENAI_API_KEY": "${OPENAI_API_KEY:-}",
                "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY:-}"
            }
        },
        "runtime": {
            "transport": transport,
            "host": host,
            "port": port,
            "fastmcp_available": FASTMCP_AVAILABLE,
            "canonical_entrypoint": "python -m src.mcp.server",
        },
        "health": "/health",
        "description": "Semantic code search and autonomous indexing",
        "metadata": {
            "role": "workflow",
            "priority": "high",
            "adhd_integration": True,
            "autonomous_indexing": True,
            "conport_integration": CONPORT_INTEGRATION_AVAILABLE,
            "warning": warning,
        }
    })


@mcp.custom_route("/autoindex/bootstrap", methods=["POST"])
async def autoindex_bootstrap(request: Request) -> JSONResponse:
    """Trigger startup bootstrap indexing then autonomous watchers."""
    payload: Dict[str, Any] = {}
    try:
        if hasattr(request, "json"):
            maybe_payload = await request.json()
            if isinstance(maybe_payload, dict):
                payload = maybe_payload
    except Exception:
        payload = {}

    workspace_path = payload.get("workspace_path")
    force = bool(payload.get("force", False))
    wait_for_completion = bool(payload.get("wait_for_completion", False))
    debounce_seconds = float(payload.get("debounce_seconds", 5.0))
    periodic_interval = int(payload.get("periodic_interval", 600))

    workspace = Path(workspace_path).resolve() if workspace_path else get_workspace_root()
    key = str(workspace)
    running_task = _autoindex_bootstrap_tasks.get(key)

    if running_task and not running_task.done():
        return JSONResponse(
            {
                "status": "already_running",
                "workspace": key,
                "details": _autoindex_bootstrap_status.get(key, {}),
            }
        )

    task = asyncio.create_task(
        _run_workspace_autoindex_bootstrap(
            workspace,
            force=force,
            debounce_seconds=debounce_seconds,
            periodic_interval=periodic_interval,
        )
    )
    _autoindex_bootstrap_tasks[key] = task

    if wait_for_completion:
        result = await task
        return JSONResponse(result)

    return JSONResponse(
        {
            "status": "started",
            "workspace": key,
            "wait_for_completion": False,
            "message": "Bootstrap started in background; use /autoindex/status for progress.",
        }
    )


@mcp.custom_route("/autoindex/status", methods=["GET"])
async def autoindex_status(request: Request) -> JSONResponse:
    """Return startup autoindex status for one or all tracked workspaces."""
    workspace_path = None
    try:
        workspace_path = request.query_params.get("workspace_path")
    except Exception:
        workspace_path = None

    if workspace_path:
        key = str(Path(workspace_path).resolve())
        return JSONResponse(
            {
                "workspace": key,
                "status": _autoindex_bootstrap_status.get(
                    key,
                    {"status": "unknown", "message": "No autoindex run recorded."},
                ),
            }
        )

    return JSONResponse(
        {
            "workspace_count": len(_autoindex_bootstrap_status),
            "statuses": _autoindex_bootstrap_status,
        }
    )


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
    if _reranker:
        return _reranker

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

# Docs pipeline (legacy globals retained for backward compatibility)
_docs_pipeline: Optional[DocIndexingPipeline] = None
_docs_search: Optional[DocumentSearch] = None
_docs_embedder: Optional[ContextualizedEmbedder] = None
_autoindex_bootstrap_tasks: Dict[str, asyncio.Task] = {}
_autoindex_bootstrap_status: Dict[str, Dict[str, Any]] = {}

VOYAGE_KEY_ENV_VARS: Tuple[str, ...] = ("VOYAGE_API_KEY", "VOYAGEAI_API_KEY")


def _snapshot_root() -> Path:
    """Return base snapshot directory without creating it."""
    return Path.home() / ".dope-context" / "snapshots"


def _snapshot_dir_for_hash(workspace_hash: str) -> Path:
    """Get snapshot directory for a workspace hash."""
    return _snapshot_root() / workspace_hash


def _autoindex_marker_path(workspace: Path) -> Path:
    """Return marker file path used for bootstrap idempotence checks."""
    workspace_hash = workspace_to_hash(workspace)
    marker_dir = _snapshot_dir_for_hash(workspace_hash)
    marker_dir.mkdir(parents=True, exist_ok=True)
    return marker_dir / "autoindex_bootstrap.json"


def _workspace_snapshot_signature(workspace: Path) -> str:
    """Return deterministic signature of current workspace snapshot."""
    try:
        result = subprocess.run(
            ["git", "-C", str(workspace), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        head = result.stdout.strip()
        if head:
            return f"git:{head}"
    except Exception as exc:
        # Git may not be available or workspace may not be a git repository;
        # fall back to filesystem-based signature instead.
        logger.debug(
            "Failed to obtain git-based workspace signature for %s: %s",
            workspace,
            exc,
        )
    try:
        return f"mtime:{int(workspace.stat().st_mtime)}"
    except Exception:
        return f"path:{workspace}"


def _read_autoindex_marker(workspace: Path) -> Dict[str, Any]:
    """Load previously stored bootstrap marker for workspace."""
    marker_path = _autoindex_marker_path(workspace)
    if not marker_path.exists():
        return {}
    try:
        return json.loads(marker_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to parse autoindex marker %s: %s", marker_path, exc)
        return {}


def _write_autoindex_marker(workspace: Path, payload: Dict[str, Any]) -> None:
    """Persist bootstrap marker for workspace."""
    marker_path = _autoindex_marker_path(workspace)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_snapshot_metadata(workspace: Path, workspace_hash: str) -> Dict[str, Any]:
    """
    Load stored snapshot metadata (if available) for workspace.

    Returns:
        Dictionary with optional keys: files_indexed, total_chunks, last_snapshot
    """
    snapshot_dir = _snapshot_dir_for_hash(workspace_hash)
    metadata: Dict[str, Any] = {
        "snapshot_dir": str(snapshot_dir),
    }

    snapshot_file = snapshot_dir / "snapshot.json"
    if snapshot_file.exists():
        try:
            data = json.loads(snapshot_file.read_text())
            metadata["files_indexed"] = len(data.get("files", {}))
            metadata["last_snapshot"] = data.get("created_at") or datetime.fromtimestamp(
                snapshot_file.stat().st_mtime
            ).isoformat()
        except Exception as exc:
            logger.debug("Failed to parse snapshot %s: %s", snapshot_file, exc)

    chunk_snapshot_file = snapshot_dir / "chunk_snapshot.json"
    if chunk_snapshot_file.exists():
        try:
            data = json.loads(chunk_snapshot_file.read_text())
            files = data.get("files", {})
            metadata["total_chunks"] = sum(len(file.get("chunks", [])) for file in files.values())
        except Exception as exc:
            logger.debug("Failed to parse chunk snapshot %s: %s", chunk_snapshot_file, exc)

    metadata["workspace_exists"] = workspace.exists()
    return metadata


def _discover_workspaces_from_snapshots() -> List[Path]:
    """
    Discover previously indexed workspaces by reading snapshot metadata.

    Returns:
        List of workspace paths (may include paths that no longer exist)
    """
    base = _snapshot_root()
    if not base.exists():
        return []

    discovered: List[Path] = []
    for child in sorted(base.iterdir()):
        if not child.is_dir():
            continue

        workspace_path: Optional[Path] = None
        for candidate in ("snapshot.json", "chunk_snapshot.json"):
            file_path = child / candidate
            if not file_path.exists():
                continue
            try:
                data = json.loads(file_path.read_text())
                workspace_str = data.get("workspace_path")
            except Exception:
                continue
            if workspace_str:
                workspace_path = Path(workspace_str)
                break

        if workspace_path:
            discovered.append(workspace_path)

    return discovered


def _resolve_target_workspaces(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> List[Path]:
    """
    Resolve a unique ordered list of workspaces to operate on.
    """
    candidates: List[Path] = []

    if workspace_paths:
        candidates.extend(Path(p).expanduser() for p in workspace_paths if p)
    if workspace_path:
        candidates.append(Path(workspace_path).expanduser())

    if not candidates:
        discovered = _discover_workspaces_from_snapshots()
        if discovered:
            candidates.extend(discovered)
        else:
            candidates.append(get_workspace_root())

    resolved: List[Path] = []
    seen: Set[str] = set()
    for candidate in candidates:
        resolved_path = candidate.resolve()
        key = str(resolved_path)
        if key not in seen:
            resolved.append(resolved_path)
            seen.add(key)

    return resolved


def _resolve_explicit_workspaces(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    *,
    fallback_to_current: bool = True,
) -> List[Path]:
    """
    Resolve explicitly requested workspaces (without snapshot discovery).
    """
    candidates: List[Path] = []

    if workspace_paths:
        candidates.extend(Path(p).expanduser() for p in workspace_paths if p)
    if workspace_path:
        candidates.append(Path(workspace_path).expanduser())

    if not candidates and fallback_to_current:
        candidates.append(get_workspace_root())

    resolved: List[Path] = []
    seen: Set[str] = set()
    for candidate in candidates:
        resolved_path = candidate.resolve()
        key = str(resolved_path)
        if key not in seen:
            resolved.append(resolved_path)
            seen.add(key)

    return resolved


async def _run_workspace_autoindex_bootstrap(
    workspace: Path,
    *,
    force: bool,
    debounce_seconds: float,
    periodic_interval: int,
) -> Dict[str, Any]:
    """Run bootstrap indexing once per snapshot, then start autonomous indexing."""
    workspace = workspace.resolve()
    key = str(workspace)
    snapshot_signature = _workspace_snapshot_signature(workspace)
    started_at = datetime.utcnow().isoformat()
    status: Dict[str, Any] = {
        "workspace": key,
        "status": "running",
        "started_at": started_at,
        "snapshot_signature": snapshot_signature,
        "force": force,
    }
    _autoindex_bootstrap_status[key] = status

    try:
        marker = _read_autoindex_marker(workspace)
        skip_bootstrap = (
            not force
            and marker.get("snapshot_signature") == snapshot_signature
            and marker.get("status") == "completed"
        )

        if skip_bootstrap:
            status["bootstrap"] = {
                "status": "skipped",
                "reason": "snapshot_signature_already_bootstrapped",
                "marker_path": str(_autoindex_marker_path(workspace)),
            }
        else:
            code_summary = await _index_workspace_impl(workspace_path=str(workspace))
            docs_summary = await _index_docs_impl(workspace_path=str(workspace))
            status["bootstrap"] = {
                "status": "completed",
                "code": code_summary,
                "docs": docs_summary,
            }
            _write_autoindex_marker(
                workspace,
                {
                    "status": "completed",
                    "workspace": key,
                    "snapshot_signature": snapshot_signature,
                    "completed_at": datetime.utcnow().isoformat(),
                    "trigger": "dopemux_cli_startup",
                },
            )

        code_autonomous = await _start_autonomous_indexing_single(
            workspace_override=workspace,
            debounce_seconds=debounce_seconds,
            periodic_interval=periodic_interval,
        )
        docs_autonomous = await _start_autonomous_docs_indexing_single(
            workspace_override=workspace,
            debounce_seconds=debounce_seconds,
            periodic_interval=periodic_interval,
        )

        status["autonomous"] = {
            "code": code_autonomous,
            "docs": docs_autonomous,
        }
        status["status"] = "completed"
        status["completed_at"] = datetime.utcnow().isoformat()
        return status
    except Exception as exc:
        status["status"] = "failed"
        status["error"] = str(exc)
        status["failed_at"] = datetime.utcnow().isoformat()
        logger.error("Autoindex bootstrap failed for %s: %s", workspace, exc, exc_info=True)
        return status
    finally:
        _autoindex_bootstrap_tasks.pop(key, None)


async def _describe_collection(collection_name: str, url: str, port: int) -> Dict[str, Any]:
    """
    Fetch collection information from Qdrant with graceful error handling.
    """
    search = MultiVectorSearch(
        collection_name=collection_name,
        url=url,
        port=port,
    )

    try:
        info = await search.get_collection_info()
        return {
            "collection_name": info.get("name", collection_name),
            "status": info.get("status", "unknown"),
            "total_vectors": info.get("vectors_count", 0),
        }
    except Exception as exc:
        logger.warning("Collection '%s' unavailable: %s", collection_name, exc)
        return {
            "collection_name": collection_name,
            "status": "unavailable",
            "error": str(exc),
            "total_vectors": 0,
        }


def _get_voyage_api_key(required: bool = True) -> Optional[str]:
    """
    Resolve the Voyage API key from multiple supported environment variables.

    Args:
        required: Whether to raise if no key is found.
    """
    for env_name in VOYAGE_KEY_ENV_VARS:
        value = os.getenv(env_name)
        if value:
            return value

    if required:
        raise ValueError(
            "VOYAGE_API_KEY or VOYAGEAI_API_KEY environment variable required"
        )
    return None


def _initialize_components():
    """Initialize all pipeline components."""
    global _pipeline, _hybrid_search, _reranker, _embedder, _bm25_index
    global _docs_pipeline, _docs_search, _docs_embedder

    # Get API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    voyage_key = _get_voyage_api_key()
    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

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
        api_key=_get_voyage_api_key(),
        default_model="voyage-code-3",
    )

    # Create contextualized embedder for content vectors
    contextualized_embedder = ContextualizedEmbedder(
        api_key=_get_voyage_api_key(),
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
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
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

    Args:
        workspace_path: Path to index (defaults to current repo)
        workspace_paths: Optional list of paths to batch index

    Returns:
        Indexing progress summary (single workspace) or aggregated results
    """
    targets = _resolve_explicit_workspaces(workspace_path, workspace_paths)
    results = []

    for workspace in targets:
        summary = await _index_workspace_impl(
            workspace_path=str(workspace),
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_files=max_files,
        )
        results.append({"workspace": str(workspace), "summary": summary})

    if len(results) == 1:
        return results[0]["summary"]

    return {
        "workspace_count": len(results),
        "results": results,
    }


async def _search_code_impl(
    query: str,
    top_k: int = 10,
    profile: str = "implementation",
    use_reranking: bool = True,
    filter_language: Optional[str] = None,
    workspace_path: Optional[str] = None,
    budget_tokens: int = 9000,
    user_id: str = "default",
    enrich_with_graph: bool = False,  # F-NEW-5: Code graph enrichment
) -> List[Dict]:
    """Implementation of search_code tool (NOW WITH DYNAMIC TOP_K + GRAPH ENRICHMENT!)."""
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
        voyage_key = _get_voyage_api_key(required=False)
        if not voyage_key:
            logger.error(
                "Voyage API key not set (expected VOYAGE_API_KEY or VOYAGEAI_API_KEY)"
            )
            return [{
                "error": "Voyage API key environment variable not set",
                "help": "Set VOYAGE_API_KEY or VOYAGEAI_API_KEY to enable embeddings and reranking"
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
                    raw = f.read()
                import json, pickle
                try:
                    cached = json.loads(raw.decode('utf-8')) if raw.strip().startswith(b'{') else pickle.loads(raw)
                except Exception:
                    cached = pickle.loads(raw)
                    logger.warning("Legacy pickle BM25 cache loaded; consider JSON migration")
                bm25_index.bm25 = cached['bm25']
                bm25_index.documents = cached['documents']
                bm25_index.doc_ids = cached['doc_ids']
                logger.info(f"Loaded BM25 index from cache: {len(bm25_index.doc_ids)} docs")
            except Exception as cache_error:
                logger.warning(f"BM25 cache load failed, dense-only search: {cache_error}")
                bm25_index = BM25Index()  # Empty fallback
        else:
            logger.info(f"No BM25 cache found at {bm25_cache_path}, using dense-only search")

        if _hybrid_search and not isinstance(_hybrid_search, HybridSearch):
            hybrid_search = _hybrid_search
        else:
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
                "help": "Check VOYAGE_API_KEY or VOYAGEAI_API_KEY and network connectivity"
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
                        "start_line": getattr(r.search_result, 'start_line', None),  # F-NEW-5 support
                        "end_line": getattr(r.search_result, 'end_line', None),
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
                "start_line": getattr(r, 'start_line', None),  # F-NEW-5 support
                "end_line": getattr(r, 'end_line', None),
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

        # F-NEW-5: Enrich with code graph relationships if requested
        final_results = truncated_results
        if enrich_with_graph:
            try:
                from enrichment.code_graph_enricher import get_code_graph_enricher

                enricher = await get_code_graph_enricher()
                final_results = await enricher.enrich_results(
                    results=truncated_results,
                    max_enrich=5  # ADHD limit: enrich top 5 only
                )
                logger.info(f"✅ Results enriched with code graph relationships")
            except Exception as enrich_error:
                logger.warning(f"Code graph enrichment failed: {enrich_error}")
                # Continue with unenriched results

        return final_results

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
    workspace_paths: Optional[List[str]] = None,
    enrich_with_graph: bool = False,  # F-NEW-5: Add code graph relationships
) -> Any:
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
        workspace_paths: Optional list of workspaces to query sequentially
        enrich_with_graph: Add code graph relationships from Serena (F-NEW-5)

    Returns:
        List of search results with code, context, and scores
        If enrich_with_graph=True, includes 'relationships' field with:
        - callers: Number of functions that call this
        - callees: Number of functions this calls
        - imports: Number of modules imported
        - impact_score: 0.0-1.0 impact rating
        - impact_level: none/low/medium/high/critical
        - impact_message: ADHD-friendly impact description
    """
    targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=True,
    )

    multi = len(targets) > 1
    aggregated_results = []
    total_results = 0

    for workspace in targets:
        workspace_results = await _search_code_impl(
            query,
            top_k,
            profile,
            use_reranking,
            filter_language,
            str(workspace),
            enrich_with_graph=enrich_with_graph,
        )
        aggregated_results.append(
            {
                "workspace": str(workspace),
                "results": workspace_results,
                "result_count": len(workspace_results),
            }
        )
        total_results += len(workspace_results)

    if not multi:
        return aggregated_results[0]["results"]

    return {
        "workspace_count": len(aggregated_results),
        "total_results": total_results,
        "results": aggregated_results,
    }


async def _get_index_status_impl(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> Dict:
    """Implementation of get_index_status tool."""
    target_workspaces = _resolve_target_workspaces(workspace_path, workspace_paths)
    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    workspaces_summary: List[Dict[str, Any]] = []
    code_collections: Dict[str, Dict[str, Any]] = {}
    docs_collections: Dict[str, Dict[str, Any]] = {}

    for workspace in target_workspaces:
        workspace_hash = workspace_to_hash(workspace)
        code_collection, docs_collection = get_collection_names(workspace)

        code_status = await _describe_collection(code_collection, qdrant_url, qdrant_port)
        docs_status = await _describe_collection(docs_collection, qdrant_url, qdrant_port)
        snapshot_meta = _load_snapshot_metadata(workspace, workspace_hash)

        workspace_entry = {
            "workspace": str(workspace),
            "workspace_hash": workspace_hash,
            "workspace_exists": workspace.exists(),
            "code_collection": code_status,
            "docs_collection": docs_status,
            "snapshot": snapshot_meta,
        }
        workspaces_summary.append(workspace_entry)

        code_details = dict(code_status)
        code_details.update(
            {
                key: value
                for key, value in snapshot_meta.items()
                if key in {"files_indexed", "total_chunks", "last_snapshot"}
            }
        )
        code_collections[workspace_hash] = code_details
        docs_collections[workspace_hash] = dict(docs_status)

    return {
        "workspace_count": len(workspaces_summary),
        "workspaces": workspaces_summary,
        "code_collections": code_collections,
        "docs_collections": docs_collections,
    }


@mcp.tool()
async def get_index_status(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> Dict:
    """
    Get status of code/doc indexes for one or more workspaces.

    Args:
        workspace_path: Optional single workspace path
        workspace_paths: Optional list of workspace paths to aggregate

    Returns:
        Collection information and statistics per workspace
    """
    return await _get_index_status_impl(workspace_path, workspace_paths)


async def _clear_index_impl(
    workspace_path: Optional[str] = None,
    target: str = "code",
) -> Dict:
    """Implementation of clear_index tool."""
    workspace = (
        Path(workspace_path).expanduser().resolve()
        if workspace_path
        else get_workspace_root()
    )
    target_normalized = (target or "code").lower()
    if target_normalized not in {"code", "docs", "both"}:
        raise ValueError("target must be one of: code, docs, both")

    code_collection, docs_collection = get_collection_names(workspace)
    workspace_hash = workspace_to_hash(workspace)
    qdrant_url = os.getenv("QDRANT_URL", "localhost")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))

    cleared: List[str] = []
    errors: List[Dict[str, str]] = []

    async def _delete_collection(collection_name: str, label: str):
        try:
            search = MultiVectorSearch(
                collection_name=collection_name,
                url=qdrant_url,
                port=qdrant_port,
            )
            await search.delete_collection()
            cleared.append(label)
        except Exception as exc:
            errors.append({"index": label, "error": str(exc)})
    if target_normalized in {"code", "both"}:
        await _delete_collection(code_collection, "code")
        bm25_cache_path = _snapshot_dir_for_hash(workspace_hash) / "bm25_index.pkl"
        if bm25_cache_path.exists():
            try:
                bm25_cache_path.unlink()
            except OSError as exc:
                logger.debug("Failed to delete BM25 cache %s: %s", bm25_cache_path, exc)

    if target_normalized in {"docs", "both"}:
        await _delete_collection(docs_collection, "docs")

    status = "success"
    if errors and cleared:
        status = "partial"
    elif errors and not cleared:
        status = "failed"

    return {
        "status": status,
        "workspace": str(workspace),
        "target": target_normalized,
        "cleared": cleared,
        "errors": errors,
    }


@mcp.tool()
async def clear_index(
    workspace_path: Optional[str] = None,
    target: str = "code",
) -> Dict:
    """
    Clear a workspace's index/indices.

    Args:
        workspace_path: Workspace root (defaults to auto-detected root)
        target: Which index to clear - "code", "docs", or "both"

    Returns:
        Success message
    """
    return await _clear_index_impl(workspace_path, target)


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
        api_key=_get_voyage_api_key(),
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
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
) -> Dict:
    """
    Index documents (PDF, Markdown, HTML, text) in workspace.

    Args:
        workspace_path: Path to workspace root (defaults to current repo)
        workspace_paths: Optional list of workspaces to batch index
        include_patterns: File patterns (e.g., ["*.md", "*.pdf"])

    Returns:
        Indexing summary for one or many workspaces
    """
    targets = _resolve_explicit_workspaces(workspace_path, workspace_paths)
    results = []

    for workspace in targets:
        summary = await _index_docs_impl(
            workspace_path=str(workspace),
            include_patterns=include_patterns,
        )
        results.append({"workspace": str(workspace), "summary": summary})

    if len(results) == 1:
        return results[0]["summary"]

    return {
        "workspace_count": len(results),
        "results": results,
    }


async def _docs_search_impl(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
    max_content_length: int = 2000,
    budget_tokens: int = 9000,
    return_meta: bool = False,
) -> Any:
    """Implementation of docs_search tool."""
    # Detect workspace
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()
    _, docs_collection = get_collection_names(workspace)
    embed_model = "voyage-context-3"

    # Log metrics for benchmarking
    get_tracker().log_search(
        tool_name="docs_search",
        query=query,
        workspace=str(workspace),
        top_k=top_k
    )

    logger.info(f"Searching docs: {workspace} → collection: {docs_collection}")
    embed_duration_ms = 0.0
    search_duration_ms = 0.0

    # Check API key
    voyage_key = _get_voyage_api_key(required=False)
    if not voyage_key:
        logger.error(
            "Voyage API key not set (expected VOYAGE_API_KEY or VOYAGEAI_API_KEY)"
        )
        payload = [{
            "error": "Voyage API key environment variable not set",
            "help": "Set VOYAGE_API_KEY or VOYAGEAI_API_KEY in your environment"
        }]
        if return_meta:
            return {
                "lane_used": "docs",
                "fusion_strategy": "dense",
                "rerank_used": False,
                "embed_model_used": embed_model,
                "timings_ms": {
                    "embed": embed_duration_ms,
                    "search": search_duration_ms,
                    "fuse": 0.0,
                    "rerank": 0.0,
                },
                "results": payload,
            }
        return payload

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
    embed_started = perf_counter()
    result = await docs_embedder.embed_document(
        chunks=[query],  # Single "chunk" for query
        model=embed_model,
        input_type="query",
        output_dimension=1024,
    )
    embed_duration_ms = round((perf_counter() - embed_started) * 1000, 3)

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
    search_started = perf_counter()
    results = await docs_search.search_documents(
        query_vectors=query_vectors,
        filter_by=filter_by if filter_by else None,
    )
    search_duration_ms = round((perf_counter() - search_started) * 1000, 3)

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

    enriched_results = []
    for index, item in enumerate(truncated_results, start=1):
        enriched_results.append(
            {
                **item,
                "rank": index,
                "source_uri": item.get("source_path", ""),
                "chunk_id": item.get("chunk_id") or f"doc_chunk_{index}",
                "snippet": item.get("text", ""),
            }
        )

    if return_meta:
        return {
            "lane_used": "docs",
            "fusion_strategy": "dense",
            "rerank_used": False,
            "embed_model_used": embed_model,
            "timings_ms": {
                "embed": embed_duration_ms,
                "search": search_duration_ms,
                "fuse": 0.0,
                "rerank": 0.0,
            },
            "results": enriched_results,
        }

    return enriched_results


@mcp.tool()
async def docs_search(
    query: str,
    top_k: int = 10,
    filter_doc_type: Optional[str] = None,
    workspace_path: Optional[str] = None,
    max_content_length: int = 2000,
    workspace_paths: Optional[List[str]] = None,
) -> Any:
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
        workspace_paths: Optional list of workspaces to query sequentially
        max_content_length: Max characters per doc (default 2000, prevents token overflow)

    Returns:
        List of document search results with truncated text and scores.
        Each result includes 'truncated' boolean and 'original_length' for reference.
    """
    targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=True,
    )

    multi = len(targets) > 1
    aggregated_results = []
    total_results = 0

    for workspace in targets:
        workspace_results = await _docs_search_impl(
            query,
            top_k,
            filter_doc_type,
            str(workspace),
            max_content_length,
            return_meta=True,
        )
        if isinstance(workspace_results, dict):
            result_items = workspace_results.get("results", [])
        else:
            result_items = workspace_results
        aggregated_results.append(
            {
                "workspace": str(workspace),
                "results": workspace_results,
                "result_count": len(result_items),
            }
        )
        total_results += len(result_items)

    if not multi:
        return aggregated_results[0]["results"]

    return {
        "workspace_count": len(aggregated_results),
        "total_results": total_results,
        "results": aggregated_results,
    }


def _decision_sync_config_path(workspace: Path) -> Path:
    """Path to workspace-scoped decision search config."""
    return get_snapshot_dir(workspace) / "decision_sync_config.json"


def _default_decision_sync_config() -> Dict[str, Any]:
    """Default decision-search settings for unified retrieval."""
    return {
        "enabled": False,
        "bridge_url": os.getenv("DOPECON_BRIDGE_URL", "http://localhost:3016"),
        "limit": TRINITY_DECISION_DEFAULT_LIMIT,
        "auto_include_in_search_all": True,
        "updated_at": datetime.utcnow().isoformat(),
    }


def _load_decision_sync_config(workspace: Path) -> Dict[str, Any]:
    """Load decision-search settings; fallback to defaults."""
    defaults = _default_decision_sync_config()
    config_path = _decision_sync_config_path(workspace)

    if not config_path.exists():
        return defaults

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            defaults.update(payload)
    except Exception as exc:
        logger.warning("Failed to load decision sync config at %s: %s", config_path, exc)

    return defaults


def _save_decision_sync_config(workspace: Path, config: Dict[str, Any]) -> Path:
    """Persist decision-search settings for a workspace."""
    config_path = _decision_sync_config_path(workspace)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    normalized = _default_decision_sync_config()
    normalized.update(config)
    normalized["limit"] = _normalize_decision_limit(
        normalized.get("limit", TRINITY_DECISION_DEFAULT_LIMIT)
    )
    normalized["updated_at"] = datetime.utcnow().isoformat()

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2)

    return config_path


async def _search_decisions_impl(
    query: str,
    top_k: int = 6,
    workspace_path: Optional[str] = None,
    bridge_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Query ConPort decisions through dopecon-bridge for unified retrieval.
    """
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()
    config = _load_decision_sync_config(workspace)

    if not config.get("enabled", False):
        return []

    target_url = str(bridge_url or config.get("bridge_url") or "").rstrip("/")
    if not target_url:
        return []

    limit = _normalize_decision_limit(top_k)
    params = {"text": query, "limit": limit}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{target_url}/kg/decisions/search",
                params=params,
                timeout=aiohttp.ClientTimeout(total=5.0),
            ) as response:
                if response.status != 200:
                    logger.debug(
                        "Decision search failed (%s): %s",
                        response.status,
                        target_url,
                    )
                    return []
                payload = await response.json()
    except Exception as exc:
        logger.debug("Decision search unavailable: %s", exc)
        return []

    raw_items = payload.get("decisions") or payload.get("items") or []
    normalized: List[Dict[str, Any]] = []
    for item in raw_items[:limit]:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "id": item.get("id"),
                "summary": item.get("summary") or item.get("title") or "",
                "timestamp": item.get("timestamp") or item.get("updated_at"),
                "source": "conport",
            }
        )

    return normalized


@mcp.tool()
async def configure_decision_auto_indexing(
    workspace_path: Optional[str] = None,
    enabled: bool = True,
    bridge_url: Optional[str] = None,
    decision_limit: int = TRINITY_DECISION_DEFAULT_LIMIT,
    auto_include_in_search_all: bool = True,
) -> Dict[str, Any]:
    """
    Configure decision retrieval for unified search.

    This enables `search_all` to automatically include ConPort decision matches
    alongside code and docs results.
    """
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()
    current = _load_decision_sync_config(workspace)
    current.update(
        {
            "enabled": enabled,
            "bridge_url": bridge_url or current.get("bridge_url"),
            "limit": _normalize_decision_limit(decision_limit),
            "auto_include_in_search_all": auto_include_in_search_all,
        }
    )
    config_path = _save_decision_sync_config(workspace, current)

    return {
        "workspace": str(workspace),
        "config_path": str(config_path),
        "config": current,
        "trinity_boundaries": {
            "marker": TRINITY_BOUNDARY_MARKER,
            "decision_limit_default": TRINITY_DECISION_DEFAULT_LIMIT,
            "decision_limit_max": TRINITY_DECISION_MAX_LIMIT,
            "decision_limit_effective": current["limit"],
            "decision_authority": "memory_plane",
            "code_docs_authority": "search_plane",
        },
        "message": (
            "Decision retrieval enabled for search_all"
            if enabled
            else "Decision retrieval disabled for search_all"
        ),
    }


async def _search_all_impl(
    query: str,
    top_k: int = 10,
    workspace_path: Optional[str] = None,
    include_decisions: bool = True,
) -> Dict:
    """Implementation of unified search_all tool."""
    search_started = perf_counter()
    requested_top_k = max(1, int(top_k))
    workspace = Path(workspace_path) if workspace_path else get_workspace_root()
    decision_config = _load_decision_sync_config(workspace)
    configured_decision_limit = _normalize_decision_limit(
        decision_config.get("limit", TRINITY_DECISION_DEFAULT_LIMIT)
    )
    decision_enabled = bool(
        include_decisions
        and decision_config.get("enabled", False)
        and decision_config.get("auto_include_in_search_all", True)
    )
    if decision_enabled and requested_top_k < 3:
        decision_enabled = False

    code_top_k = max(1, requested_top_k // 2)
    docs_top_k = max(1, requested_top_k - code_top_k)
    decision_top_k = 0
    code_budget = 4000
    docs_budget = 4000

    if decision_enabled:
        decision_top_k = min(configured_decision_limit, max(1, requested_top_k // 3))
        remaining_budget = max(2, requested_top_k - decision_top_k)
        code_top_k = max(1, remaining_budget // 2)
        docs_top_k = max(1, remaining_budget - code_top_k)
        code_budget = 3200
        docs_budget = 3200

    # Log metrics for benchmarking
    get_tracker().log_search(
        tool_name="search_all",
        query=query,
        workspace=str(workspace),
        top_k=requested_top_k
    )

    logger.info(f"Unified search in workspace: {workspace}")

    # Search code + docs in parallel, optionally adding ConPort decision retrieval.
    code_results_task = _search_code_impl(
        query,
        code_top_k,
        use_reranking=False,
        workspace_path=str(workspace),
        budget_tokens=code_budget,
    )
    docs_results_task = _docs_search_impl(
        query,
        docs_top_k,
        workspace_path=str(workspace),
        max_content_length=1500,
        budget_tokens=docs_budget,
    )

    if decision_enabled:
        decision_results_task = _search_decisions_impl(
            query=query,
            top_k=decision_top_k,
            workspace_path=str(workspace),
            bridge_url=decision_config.get("bridge_url"),
        )
        code_results, docs_results, decision_results = await asyncio.gather(
            code_results_task,
            docs_results_task,
            decision_results_task,
        )
    else:
        code_results, docs_results = await asyncio.gather(
            code_results_task,
            docs_results_task,
        )
        decision_results = []

    search_duration_ms = round((perf_counter() - search_started) * 1000, 3)

    return {
        "workspace": str(workspace),
        "lane_used": "mixed",
        "fusion_strategy": "hybrid_rrf",
        "rerank_used": False,
        "embed_model_used": "mixed",
        "timings_ms": {
            "embed": 0.0,
            "search": search_duration_ms,
            "fuse": 0.0,
            "rerank": 0.0,
        },
        "code_results": code_results,
        "docs_results": docs_results,
        "decision_results": decision_results,
        "decision_search_enabled": decision_enabled,
        "trinity_boundaries": {
            "marker": TRINITY_BOUNDARY_MARKER,
            "decision_limit_default": TRINITY_DECISION_DEFAULT_LIMIT,
            "decision_limit_max": TRINITY_DECISION_MAX_LIMIT,
            "decision_limit_configured": configured_decision_limit,
            "decision_limit_effective": decision_top_k,
            "top_k_requested": requested_top_k,
            "decision_authority": "memory_plane",
            "code_docs_authority": "search_plane",
        },
        "total_results": len(code_results) + len(docs_results) + len(decision_results),
    }


@mcp.tool()
async def search_all(
    query: str,
    top_k: int = 10,
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    include_decisions: bool = True,
) -> Any:
    """
    Unified search across code, docs, and optional ConPort decisions.

    🎯 **WHEN TO USE**:
    - **Complete context**: Need both implementation and documentation together
    - **Feature exploration**: Understand code alongside design docs
    - **Onboarding**: Learn codebase with docs as guide
    - **Cross-reference**: Verify code matches documented behavior

    Auto-detects workspace from current directory (or use workspace_path).

    Args:
        query: Natural language search query
        top_k: Total results budget (default 10)
        workspace_path: Optional workspace path (auto-detects if None)
        workspace_paths: Optional list of workspaces to query sequentially
        include_decisions: Include decision matches when configured

    Returns:
        Combined results with workspace, code_results, docs_results,
        decision_results, and total_results.
    """
    targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=True,
    )

    multi = len(targets) > 1
    aggregated_results = []
    total_results = 0

    for workspace in targets:
        workspace_results = await _search_all_impl(
            query,
            top_k,
            str(workspace),
            include_decisions=include_decisions,
        )
        aggregated_results.append(workspace_results)
        total_results += workspace_results.get("total_results", 0)

    if not multi:
        return aggregated_results[0]

    return {
        "workspace_count": len(aggregated_results),
        "total_results": total_results,
        "results": aggregated_results,
    }


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
            "has_changes": False,
            "total_changes": 0,
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
            voyage_key = _get_voyage_api_key()
            standard_embedder = _get_cached_embedder(api_key=voyage_key)
            contextualized_embedder = _get_cached_contextualized_embedder(api_key=voyage_key)

            config = IndexingConfig(
                workspace_path=workspace,
                include_patterns=include_patterns or ["*.py", "*.js", "*.ts", "*.tsx"],
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

            # Index only changed files
            changed_files = changes.added + changes.modified
            if changed_files:
                changed_patterns = [Path(path).as_posix().lstrip("./") for path in changed_files]
                # Create temporary config with only changed files
                temp_config = IndexingConfig(
                    workspace_path=workspace,
                    include_patterns=changed_patterns,  # Only these specific files
                    workspace_id=str(workspace),
                )
                pipeline.config = temp_config
                await pipeline.index_workspace()
                logger.info(f"Reindexed {len(changed_files)} added/modified files")

            # Delete removed files from collection
            if changes.removed:
                all_docs = await vector_search.get_all_payloads()
                removed_set = {Path(path).as_posix() for path in changes.removed}
                removed_basenames = {Path(path).name for path in changes.removed}
                point_ids_to_delete: List[str] = []
                for doc in all_docs:
                    source_path = doc.get("file_path") or doc.get("source_path")
                    point_id = doc.get("id")
                    if not source_path or not point_id:
                        continue
                    source_norm = Path(str(source_path)).as_posix()
                    if (
                        source_norm in removed_set
                        or source_norm.lstrip("./") in removed_set
                        or Path(source_norm).name in removed_basenames
                    ):
                        point_ids_to_delete.append(str(point_id))
                if point_ids_to_delete:
                    await vector_search.delete_points(point_ids_to_delete)
                    logger.info(
                        "Deleted %s vectors for %s removed files",
                        len(point_ids_to_delete),
                        len(changes.removed),
                    )
                else:
                    logger.info(
                        "No matching vector points found for %s removed files",
                        len(changes.removed),
                    )

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
                "has_changes": changes.total_changes() > 0,
                "total_changes": changes.total_changes(),
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
                "has_changes": changes.total_changes() > 0,
                "total_changes": changes.total_changes(),
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
        "has_changes": changes.total_changes() > 0,
        "total_changes": changes.total_changes(),
        "changes": changes.total_changes(),
        "added": len(changes.added),
        "modified": len(changes.modified),
        "removed": len(changes.removed),
        "message": f"Detected {changes.total_changes()} changes. Run index_workspace to update or use auto_reindex=True.",
    }


@mcp.tool()
async def sync_workspace(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
    auto_reindex: bool = False,
) -> Any:
    """
    Sync workspace index with file changes (incremental).

    Detects added/modified/removed files using SHA256 snapshots.
    Optionally auto-reindexes changed files for true incremental updates.

    Args:
        workspace_path: Absolute workspace path
        workspace_paths: Optional list of workspaces to process sequentially
        include_patterns: File patterns to track (default: code files)
        auto_reindex: Automatically reindex changed files (default: False)

    Returns:
        Change statistics and reindex results
    """
    targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=True,
    )

    results = []
    for workspace in targets:
        result = await _sync_workspace_impl(str(workspace), include_patterns, auto_reindex)
        results.append(result)

    if len(results) == 1:
        return results[0]

    return {
        "workspace_count": len(results),
        "results": results,
    }


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
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    include_patterns: Optional[List[str]] = None,
) -> Any:
    """
    Sync docs index with file changes (incremental).

    Detects added/modified/removed documents using SHA256 snapshots.

    Args:
        workspace_path: Absolute workspace path
        workspace_paths: Optional list of workspaces to process sequentially
        include_patterns: File patterns to track (default: doc files)

    Returns:
        Change statistics
    """
    targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=True,
    )

    results = []
    for workspace in targets:
        result = await _sync_docs_impl(str(workspace), include_patterns)
        results.append(result)

    if len(results) == 1:
        return results[0]

    return {
        "workspace_count": len(results),
        "results": results,
    }


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


async def _start_autonomous_indexing_single(
    workspace_override: Optional[Path],
    debounce_seconds: float,
    periodic_interval: int,
) -> Dict:
    """Start autonomous indexing for a single workspace."""
    workspace = get_workspace_root(workspace_override)

    logger.info(f"Starting autonomous indexing for {workspace}")

    workspace_key = str(workspace)
    active = AutonomousController.get_active_controllers()

    if workspace_key in active:
        return {
            "status": "already_running",
            "workspace": str(workspace),
            "message": "Autonomous indexing already active for this workspace",
        }

    config = AutonomousConfig(
        enabled=True,
        debounce_seconds=debounce_seconds,
        periodic_interval=periodic_interval,
    )

    async def index_callback(ws_path: Path, changed_files: Optional[Set[str]]):
        await _index_workspace_impl(
            workspace_path=str(ws_path),
            include_patterns=config.include_patterns,
            exclude_patterns=config.exclude_patterns,
        )

    async def sync_callback(ws_path: Path):
        return await _sync_workspace_impl(str(ws_path))

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
async def start_autonomous_indexing(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
    debounce_seconds: float = 5.0,
    periodic_interval: int = 600,
) -> Dict:
    """
    Enable autonomous indexing for one or many workspaces.

    🎯 **ADHD BENEFIT**: Zero mental overhead - index updates automatically
    as you code. No manual sync needed ever again!

    Starts three monitoring systems:
    1. File watcher (watchdog) - Immediate response to changes
    2. 5s debouncing - Batches rapid saves for efficiency
    3. 10min periodic fallback - Catches any missed events

    Args:
        workspace_path: Workspace to monitor (defaults to cwd)
        workspace_paths: Optional list of workspaces to monitor
        debounce_seconds: Wait time after file changes (default: 5.0)
        periodic_interval: Fallback check interval (default: 600s/10min)

    Returns:
        Status and configuration info (single or aggregated)
    """
    explicit_targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=False,
    )
    target_overrides: List[Optional[Path]] = explicit_targets or [None]

    results = []
    for override in target_overrides:
        status = await _start_autonomous_indexing_single(
            workspace_override=override,
            debounce_seconds=debounce_seconds,
            periodic_interval=periodic_interval,
        )
        results.append(status)

    if len(results) == 1:
        return results[0]

    return {
        "workspace_count": len(results),
        "results": results,
    }


@mcp.tool()
async def stop_autonomous_indexing(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> Dict:
    """
    Stop autonomous indexing for workspace.

    🎯 **USE CASE**: Disable auto-indexing when not needed (saves resources)

    Args:
        workspace_path: Workspace to stop monitoring (defaults to cwd)
        workspace_paths: Optional list of workspaces to stop

    Returns:
        Status info
    """
    explicit_targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=False,
    )
    target_overrides: List[Optional[Path]] = explicit_targets or [None]

    results = []
    active = AutonomousController.get_active_controllers()

    for override in target_overrides:
        workspace = get_workspace_root(override)
        workspace_key = str(workspace)

        if workspace_key not in active:
            results.append(
                {
                    "status": "not_running",
                    "workspace": str(workspace),
                    "message": "No autonomous indexing active for this workspace",
                }
            )
            continue

        controller = active[workspace_key]
        await controller.stop()
        results.append(
            {
                "status": "stopped",
                "workspace": str(workspace),
                "message": f"Autonomous indexing stopped for {workspace.name}",
            }
        )

    if len(results) == 1:
        return results[0]

    return {
        "workspace_count": len(results),
        "results": results,
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




# AUTONOMOUS DOCS INDEXING


async def _start_autonomous_docs_indexing_single(
    workspace_override: Optional[Path],
    debounce_seconds: float,
    periodic_interval: int,
) -> Dict:
    """Start autonomous docs indexing for a single workspace."""
    workspace = get_workspace_root(workspace_override)

    logger.info(f"Starting autonomous docs indexing for {workspace}")

    workspace_key = f"{workspace}:docs"
    active = AutonomousController.get_active_controllers()

    if workspace_key in active:
        return {
            "status": "already_running",
            "workspace": str(workspace),
            "type": "docs",
            "message": "Autonomous docs indexing already active for this workspace",
        }

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

    async def docs_index_callback(ws_path: Path, changed_files: Optional[Set[str]]):
        await _index_docs_impl(
            workspace_path=str(ws_path),
            include_patterns=config.include_patterns,
        )

    async def docs_sync_callback(ws_path: Path):
        return await _sync_docs_impl(
            str(ws_path),
            config.include_patterns,
        )

    controller = AutonomousController(
        workspace_path=workspace,
        index_callback=docs_index_callback,
        sync_callback=docs_sync_callback,
        config=config,
        registry_key=workspace_key,
    )

    await controller.start()

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
async def start_autonomous_docs_indexing(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
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
        workspace_paths: Optional list of workspaces to monitor
        debounce_seconds: Wait time after file changes (default: 5.0)
        periodic_interval: Fallback check interval (default: 600s/10min)

    Returns:
        Status and configuration info (single or aggregated)
    """
    explicit_targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=False,
    )
    target_overrides: List[Optional[Path]] = explicit_targets or [None]

    results = []
    for override in target_overrides:
        status = await _start_autonomous_docs_indexing_single(
            workspace_override=override,
            debounce_seconds=debounce_seconds,
            periodic_interval=periodic_interval,
        )
        results.append(status)

    if len(results) == 1:
        return results[0]

    return {
        "workspace_count": len(results),
        "results": results,
    }


@mcp.tool()
async def stop_autonomous_docs_indexing(
    workspace_path: Optional[str] = None,
    workspace_paths: Optional[List[str]] = None,
) -> Dict:
    """
    Stop autonomous docs indexing for workspace.

    🎯 **USE CASE**: Disable auto-indexing when not needed (saves resources)

    Args:
        workspace_path: Workspace to stop monitoring (defaults to cwd)
        workspace_paths: Optional list of workspaces to stop

    Returns:
        Status info
    """
    explicit_targets = _resolve_explicit_workspaces(
        workspace_path,
        workspace_paths,
        fallback_to_current=False,
    )
    target_overrides: List[Optional[Path]] = explicit_targets or [None]

    results = []
    active = AutonomousController.get_active_controllers()

    for override in target_overrides:
        workspace = get_workspace_root(override)
        workspace_key = f"{workspace}:docs"

        if workspace_key not in active:
            results.append(
                {
                    "status": "not_running",
                    "workspace": str(workspace),
                    "type": "docs",
                    "message": "No autonomous docs indexing active for this workspace",
                }
            )
            continue

        controller = active[workspace_key]
        await controller.stop()

        results.append(
            {
                "status": "stopped",
                "workspace": str(workspace),
                "type": "docs",
                "message": f"Autonomous docs indexing stopped for {workspace.name}",
            }
        )

    if len(results) == 1:
        return results[0]

    return {
        "workspace_count": len(results),
        "results": results,
    }


@mcp.tool()
async def get_chunk_complexity(file_path: str, symbol: str) -> Dict:
    """
    Get AST-based complexity for code chunk (Synergy A support).

    Returns complexity score 0.0-1.0 from Tree-sitter analysis.
    """
    resolved = Path(file_path).expanduser()
    if not resolved.is_absolute():
        resolved = (Path.cwd() / resolved).resolve()
    if not resolved.exists():
        return {
            "complexity": 0.5,
            "method": "ast-heuristic",
            "file_path": str(resolved),
            "symbol": symbol,
            "reason": "file_not_found",
        }

    try:
        source = resolved.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        return {
            "complexity": 0.5,
            "method": "ast-heuristic",
            "file_path": str(resolved),
            "symbol": symbol,
            "reason": f"read_error:{exc}",
        }

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fallback heuristic for non-Python files or parse failures.
        line_count = max(1, len(source.splitlines()))
        keyword_hits = sum(
            source.lower().count(keyword)
            for keyword in ("if ", "for ", "while ", "try:", "except", "class ", "def ")
        )
        complexity = min(1.0, 0.15 + (line_count / 400.0) + (keyword_hits / 100.0))
        return {
            "complexity": round(complexity, 3),
            "method": "text-heuristic",
            "file_path": str(resolved),
            "symbol": symbol,
            "line_count": line_count,
            "keyword_hits": keyword_hits,
        }

    symbol_node: Optional[ast.AST] = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if getattr(node, "name", None) == symbol:
                symbol_node = node
                break

    if symbol_node is not None:
        start = getattr(symbol_node, "lineno", 1)
        end = getattr(symbol_node, "end_lineno", start)
        target_source = "\n".join(source.splitlines()[start - 1 : end])
        target_tree = symbol_node
    else:
        start = 1
        end = len(source.splitlines())
        target_source = source
        target_tree = tree

    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.With,
        ast.AsyncWith,
        ast.Match,
        ast.comprehension,
    )
    branch_count = sum(1 for node in ast.walk(target_tree) if isinstance(node, branch_nodes))

    def _max_depth(node: ast.AST, depth: int = 0) -> int:
        children = list(ast.iter_child_nodes(node))
        if not children:
            return depth
        return max(_max_depth(child, depth + 1) for child in children)

    max_depth = _max_depth(target_tree)
    line_count = max(1, len(target_source.splitlines()))

    complexity = min(
        1.0,
        0.1 + (line_count / 220.0) + (branch_count / 20.0) + (max_depth / 30.0),
    )
    return {
        "complexity": round(complexity, 3),
        "method": "ast-heuristic",
        "file_path": str(resolved),
        "symbol": symbol,
        "line_count": line_count,
        "branch_count": branch_count,
        "max_depth": max_depth,
        "scope_start_line": start,
        "scope_end_line": end,
    }


if __name__ == "__main__":
    # Run server
    logging.basicConfig(level=logging.INFO)
    logger.info("Dope-Context MCP server starting...")
    transport, host, port = _resolve_transport_runtime()

    run_kwargs: Dict[str, Any] = {}
    if transport != "stdio":
        run_kwargs.update(host=host, port=port)
        logger.info("HTTP transport configured on %s:%s", host, port)
    else:
        logger.info("Using stdio transport")

    # Components initialize on first tool call (lazy init)
    mcp.run(transport=transport, **run_kwargs)
