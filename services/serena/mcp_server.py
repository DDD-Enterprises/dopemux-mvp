#!/usr/bin/env python3
"""
Serena v2 MCP Server - Phase 2 + Enhanced Features
Exposes 31-component ADHD-optimized code intelligence via MCP protocol

Architecture:
- Lazy loading: Heavy components load on first use
- Graceful degradation: LSP/database failures won't block server
- Enhanced caching: Redis navigation cache for 100x speedup
- 21+ tools in 3 tiers: Navigation, ADHD Intelligence, Advanced

Phase 2A: System initialization + health check
Phase 2B: Tier 1 navigation tools (find_symbol, goto_definition, etc)
Phase 2C: Tier 2 ADHD intelligence
Phase 2D: Tier 3 advanced intelligence
Enhanced: F-NEW-1 (ADHD Engine), F-NEW-2 (Semantic Search), Navigation Cache
"""

from datetime import timedelta

import asyncio
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime

# MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, EmptyResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("serena-v2-mcp")

# Fix for Feature 1 imports when running as script
# Add current directory to sys.path so absolute imports work
SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Shared MCP response-budget utilities
try:
    from services.shared.mcp.response_budget import (
        estimate_tokens as estimate_mcp_tokens,
        truncate_numbered_lines,
    )
except ImportError:
    SERVICES_ROOT = SCRIPT_DIR.parent
    if str(SERVICES_ROOT) not in sys.path:
        sys.path.insert(0, str(SERVICES_ROOT))
    from shared.mcp.response_budget import (
        estimate_tokens as estimate_mcp_tokens,
        truncate_numbered_lines,
    )

# ============================================================================
# ADHD Engine Integration - Dynamic result limits (F-NEW-1)
# ============================================================================

# Global ADHD config (initialized on first use)
_adhd_config = None
_adhd_feature_flags = None


async def _get_adhd_config():
    """Get or initialize ADHD config singleton."""
    global _adhd_config, _adhd_feature_flags

    if _adhd_config is None:
        try:
            sys.path.insert(0, str(SCRIPT_DIR.parent.parent / "adhd_engine"))

            from adhd_config_service import get_adhd_config_service
            from feature_flags import ADHDFeatureFlags

            _adhd_config = await get_adhd_config_service()
            _adhd_feature_flags = ADHDFeatureFlags(_adhd_config.redis_client)

            logger.info("✅ Serena v2 connected to ADHD Engine")
        except (ImportError, RuntimeError, ConnectionError) as e:
            logger.warning(f"⚠️ ADHD Engine unavailable: {e}")
        except Exception:
            logger.exception("Unexpected ADHD Engine initialization error")

    return _adhd_config, _adhd_feature_flags


async def get_dynamic_max_results(user_id: str = "default", requested: int = 10) -> int:
    """
    Get dynamic max_results from ADHD Engine based on attention state.

    Returns:
        scattered: 5 results (reduce overwhelm)
        focused: 15 results (standard)
        hyperfocused: 40 results (deep dive)
        fallback: requested (ADHD Engine unavailable)
    """
    adhd_config, feature_flags = await _get_adhd_config()

    if adhd_config and feature_flags:
        try:
            return await adhd_config.get_max_results(user_id)
        except (asyncio.TimeoutError, RuntimeError, ConnectionError) as e:
            logger.debug(f"ADHD Engine query failed: {e}")
        except Exception:
            logger.exception("Unexpected ADHD Engine query error")

    # Fallback to requested value
    return requested


class SimpleLSPClient:
    """
    Minimal LSP client for Phase 2B goto_definition support

    Communicates with pylsp via JSON-RPC over stdin/stdout.
    Implements only the essential LSP protocol:
    - initialize
    - textDocument/definition
    - shutdown

    Future: Replace with full EnhancedLSPWrapper in Phase 2D
    """

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.initialized = False
        self._response_queue = asyncio.Queue()
        self._reader_task = None

    async def start(self):
        """Start pylsp subprocess and initialize"""
        if self.initialized:
            return

        try:
            # Start pylsp process
            self.process = await asyncio.create_subprocess_exec(
                "pylsp",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.workspace)
            )

            # Start response reader task
            self._reader_task = asyncio.create_task(self._read_responses())

            # Send initialize request
            init_params = {
                "processId": None,
                "rootUri": f"file://{self.workspace}",
                "capabilities": {}
            }

            response = await self._send_request("initialize", init_params)

            # Send initialized notification
            await self._send_notification("initialized", {})

            self.initialized = True
            logger.info(f"SimpleLSPClient initialized for {self.workspace}")

        except FileNotFoundError:
            raise RuntimeError("pylsp not found - install with: pip install python-lsp-server[all]")
        except Exception as e:
            raise RuntimeError(f"Failed to start LSP client: {e}") from e
    async def goto_definition(self, file_uri: str, line: int, column: int) -> List[Dict]:
        """
        Request definition location for symbol at position

        Args:
            file_uri: File URI (file:///path/to/file.py)
            line: 0-indexed line number
            column: 0-indexed column number

        Returns:
            List of location dicts with uri, range
        """
        if not self.initialized:
            await self.start()

        params = {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": column}
        }

        try:
            # ADHD Optimization: Fast-fail timeout (500ms) for large workspaces
            response = await self._send_request("textDocument/definition", params, timeout=0.5)

            # LSP returns either Location, Location[], or null
            if response is None:
                return []
            elif isinstance(response, list):
                return response
            else:
                return [response]

        except asyncio.TimeoutError:
            # Expected for large workspaces - grep fallback is faster
            logger.info(f"LSP definition timed out after 500ms (workspace too large), using grep fallback")
            return []

    async def find_references(self, file_uri: str, line: int, column: int, include_declaration: bool = True) -> List[Dict]:
        """
        Find all references to symbol at position

        Args:
            file_uri: File URI (file:///path/to/file.py)
            line: 0-indexed line number
            column: 0-indexed column number
            include_declaration: Include the declaration itself

        Returns:
            List of location dicts with uri, range
        """
        if not self.initialized:
            await self.start()

        params = {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": column},
            "context": {"includeDeclaration": include_declaration}
        }

        try:
            # ADHD Optimization: Fast-fail timeout for large workspaces
            # Target: <200ms total, use 500ms LSP timeout (allows grep fallback time)
            response = await self._send_request("textDocument/references", params, timeout=0.5)

            # LSP returns Location[] or null
            if response is None:
                return []
            elif isinstance(response, list):
                return response
            else:
                return [response]

        except asyncio.TimeoutError:
            # Expected for large workspaces (28K+ files) - grep fallback is faster
            logger.info(f"LSP references timed out after 500ms (workspace too large), using grep fallback")
            return []

    async def _send_request(self, method: str, params: Dict, timeout: float = 10.0) -> Any:
        """Send JSON-RPC request and wait for response"""
        self.request_id += 1
        request_id = self.request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        # Send request
        message = json.dumps(request)
        content = f"Content-Length: {len(message)}\r\n\r\n{message}"

        self.process.stdin.write(content.encode())
        await self.process.stdin.drain()

        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(
                self._wait_for_response(request_id),
                timeout=timeout
            )

            if "error" in response:
                raise RuntimeError(f"LSP error: {response['error']}")

            return response.get("result")

        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f"LSP request {method} timed out after {timeout}s")

    async def _send_notification(self, method: str, params: Dict):
        """Send JSON-RPC notification (no response expected)"""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }

        message = json.dumps(notification)
        content = f"Content-Length: {len(message)}\r\n\r\n{message}"

        self.process.stdin.write(content.encode())
        await self.process.stdin.drain()

    async def _wait_for_response(self, request_id: int) -> Dict:
        """Wait for specific response from queue"""
        while True:
            response = await self._response_queue.get()
            if response.get("id") == request_id:
                return response
            # Put back if not matching (should rarely happen)
            await self._response_queue.put(response)
            await asyncio.sleep(0.01)

    async def _read_responses(self):
        """Background task to read LSP responses"""
        buffer = b""

        try:
            while self.process and self.process.stdout:
                chunk = await self.process.stdout.read(4096)
                if not chunk:
                    break

                buffer += chunk

                # Process complete messages
                while b"\r\n\r\n" in buffer:
                    header, rest = buffer.split(b"\r\n\r\n", 1)

                    # Parse Content-Length
                    content_length = 0
                    for line in header.decode().split("\r\n"):
                        if line.startswith("Content-Length:"):
                            content_length = int(line.split(":")[1].strip())

                    # Check if we have full message
                    if len(rest) >= content_length:
                        message = rest[:content_length]
                        buffer = rest[content_length:]

                        # Parse JSON and queue
                        try:
                            response = json.loads(message.decode())
                            if "id" in response:  # It's a response, not a notification
                                await self._response_queue.put(response)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse LSP response: {message[:100]}")
                    else:
                        # Need more data
                        buffer = header + b"\r\n\r\n" + rest
                        break

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"LSP response reader parse error: {e}")
        except Exception:
            logger.exception("Unexpected LSP response reader error")

    async def shutdown(self):
        """Gracefully shutdown LSP server"""
        if self.process and self.initialized:
            try:
                await self._send_request("shutdown", {}, timeout=2.0)
                await self._send_notification("exit", {})
                await asyncio.wait_for(self.process.wait(), timeout=2.0)
            except (asyncio.TimeoutError, RuntimeError) as e:
                self.process.kill()
                logger.warning(f"Graceful shutdown failed, process killed: {e}")
            except Exception:
                self.process.kill()
                logger.exception("Unexpected error during LSP shutdown")
            if self._reader_task:
                self._reader_task.cancel()

            self.initialized = False
            logger.info("SimpleLSPClient shutdown")


class SerenaV2MCPServer:
    """
    MCP Server wrapper for Serena v2 intelligence system

    Architecture:
    - Phase 1: Basic file operations (read_file, list_dir)
    - Phase 2A: System initialization with lazy loading
    - Phase 2B-D: Tier 1-3 intelligence tools

    Lazy Loading Strategy:
    - Workspace: Detect immediately (required for all operations)
    - Database: Load on first graph/pattern query
    - LSP: Load on first navigation query
    - claude-context: Load on first semantic search
    """

    def __init__(self):
        self.server = Server("serena-v2")
        self.workspace: Optional[Path] = None

        # Lazy-loaded components
        self.database: Optional[Any] = None
        self.lsp: Optional[Any] = None
        self.claude_context: Optional[Any] = None
        self.tree_sitter: Optional[Any] = None
        self.adhd_navigator: Optional[Any] = None
        self.conport_client: Optional[Any] = None  # F001/F002: ConPort integration

        # Component state tracking
        self.lazy_components: Dict[str, bool] = {
            "database": False,
            "lsp": False,
            "claude_context": False,
            "tree_sitter": False,
            "adhd_features": False,
            "conport": False,  # F001/F002: ConPort connection tracking
        }

        # Error tracking for diagnostics
        self.initialization_errors: Dict[str, str] = {}
        self.server_start_time = datetime.now()

        # Phase 2D: In-memory focus state (Tier 3)
        self.current_focus_mode: str = "focused"  # Default to focused mode

        # ADHD Optimization: Workspace size tracking for smart LSP bypass
        self.workspace_python_file_count: Optional[int] = None
        self.lsp_bypass_threshold: int = 5000  # Skip LSP if >5K Python files

        logger.info("Serena v2 MCP Server initialized (Phase 2)")

    async def initialize(self):
        """
        Initialize workspace with lazy loading for heavy components

        Fast startup strategy:
        1. Detect workspace (required, <100ms)
        2. Defer database, LSP, claude-context until first use
        3. Load on-demand when tools need them
        """
        # Phase 1: Workspace detection (always required)
        self.workspace = self._detect_workspace()

        if self.workspace:
            logger.info(f"✓ Workspace: {self.workspace}")
        else:
            logger.warning("⚠ No workspace - using current directory")
            self.workspace = Path.cwd()

        # Phase 2: Lazy component loading
        # Components will initialize on first tool use via _ensure_component()
        logger.info("✓ Lazy loading enabled for database, LSP, claude-context")

        # Enhanced: Start background services (file watcher)
        await self._ensure_component("file_watcher")

        logger.info(f"✓ Server ready in {(datetime.now() - self.server_start_time).total_seconds():.2f}s")

    def _detect_workspace(self) -> Optional[Path]:
        """
        Simple workspace detection (looks for .git)

        Phase 2 will use SerenaAutoActivator for advanced detection
        """
        current = Path.cwd()

        # Walk up looking for .git
        for _ in range(10):
            if (current / '.git').exists():
                return current

            parent = current.parent
            if parent == current:
                break
            current = parent

        return None

    async def _count_workspace_python_files(self) -> int:
        """
        Count Python files for LSP bypass decision (ADHD optimization)

        Returns cached count if available, otherwise does quick sampling.
        Timeout after 200ms to avoid blocking startup.
        """
        if self.workspace_python_file_count is not None:
            return self.workspace_python_file_count

        if not self.workspace:
            self.workspace_python_file_count = 0
            return 0

        try:
            # Quick count with timeout (ADHD: don't wait >200ms)
            result = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    f'find "{self.workspace}" -name "*.py" -type f | wc -l',
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                ),
                timeout=0.2
            )
            stdout, _ = await result.communicate()
            count = int(stdout.decode().strip())
            self.workspace_python_file_count = count
            logger.info(f"Workspace size: {count} Python files")
            return count

        except (asyncio.TimeoutError, Exception) as e:
            # Assume large workspace if count times out
            logger.info(f"Workspace file count timed out - assuming large workspace (>5K files)")
            self.workspace_python_file_count = 10000  # Assume large
            return self.workspace_python_file_count

    async def _ensure_conport_client(self):
        """
        Lazy load ConPort database client.

        F001/F002 Integration: Provides direct PostgreSQL access to ConPort.
        """
        if self.conport_client:
            return

        try:
            from conport_client_unified import ConPortDBClient

            self.conport_client = ConPortDBClient(
                host="localhost",
                port=5455,
                database="dopemux_knowledge_graph",
                user="dopemux_age"
            )

            await self.conport_client.connect()
            self.lazy_components["conport"] = True
            logger.info("ConPort database client connected")

        except (ImportError, ConnectionError, OSError) as e:
            logger.warning(f"ConPort client initialization failed: {e}")
        except Exception as exc:
            logger.exception("Unexpected ConPort client initialization error")
            self.initialization_errors["conport"] = str(exc)
            self.conport_client = None

    def _resolve_path(self, relative_path: str) -> Path:
        """
        Safely resolve relative path against workspace

        Args:
            relative_path: Path relative to workspace root

        Returns:
            Absolute path

        Raises:
            ValueError: If path is outside workspace
        """
        if not self.workspace:
            raise ValueError("No workspace initialized")

        full_path = (self.workspace / relative_path).resolve()

        # Security: Ensure path is within workspace
        try:
            full_path.relative_to(self.workspace)
        except ValueError:
            raise ValueError(
                f"❌ Security: Path '{relative_path}' is outside workspace\n"
                f"   Workspace: {self.workspace}\n"
                f"   Attempted: {full_path}"
            )

        return full_path

    async def _should_use_lsp(self) -> bool:
        """
        ADHD Optimization: Decide if LSP is worth using for this workspace

        Returns False if workspace is too large (>5K files) - grep is faster
        Returns True if workspace is small enough for LSP to be efficient

        Caches the decision after first check.
        """
        file_count = await self._count_workspace_python_files()

        if file_count > self.lsp_bypass_threshold:
            logger.info(
                f"LSP bypass: {file_count} files > {self.lsp_bypass_threshold} threshold "
                f"(grep fallback is faster for large workspaces)"
            )
            return False

        return True

    async def _ensure_component(self, component_name: str) -> bool:
        """
        Ensure component is loaded, return success status

        Lazy loading pattern:
        - Check if already loaded → return True
        - Try to initialize → return True on success
        - Catch errors → log warning, return False

        Args:
            component_name: One of: database, lsp, claude_context, tree_sitter, adhd_features

        Returns:
            True if component is available, False if unavailable
        """
        # Already loaded?
        if self.lazy_components.get(component_name):
            return True

        # Try to load
        try:
            if component_name == "database":
                await self._init_database()
            elif component_name == "lsp":
                await self._init_lsp()
            elif component_name == "claude_context":
                await self._init_claude_context()
            elif component_name == "tree_sitter":
                await self._init_tree_sitter()
            elif component_name == "adhd_features":
                await self._init_adhd_features()
            elif component_name == "navigation_cache":
                await self._init_navigation_cache()
            elif component_name == "file_watcher":
                await self._init_file_watcher()
            else:
                raise ValueError(f"Unknown component: {component_name}")

            self.lazy_components[component_name] = True
            logger.info(f"✓ Lazy-loaded: {component_name}")
            return True

        except (ImportError, ConnectionError, OSError, RuntimeError) as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.initialization_errors[component_name] = error_msg
            logger.warning(f"⚠ {component_name} unavailable: {error_msg}")
            return False
        except Exception:
            error_msg = "Unexpected initialization error"
            self.initialization_errors[component_name] = error_msg
            logger.exception(f"⚠ {component_name} unexpected error")
            return False

    async def _init_database(self):
        """Initialize PostgreSQL database + schema"""
        from .intelligence import create_intelligence_database, setup_phase2_schema

        self.database = await create_intelligence_database(
            workspace_id=str(self.workspace)
        )
        await setup_phase2_schema(self.database)
        logger.info("Database: PostgreSQL connected, schema ready")

    async def _init_lsp(self):
        """Initialize SimpleLSPClient for Python"""
        self.lsp = SimpleLSPClient(self.workspace)

        # Start with 5s timeout to prevent blocking
        await asyncio.wait_for(self.lsp.start(), timeout=5.0)
        logger.info("LSP: pylsp connected and ready")

    async def _init_claude_context(self):
        """Initialize claude-context MCP integration"""
        from .claude_context_integration import ClaudeContextIntegration, ClaudeContextConfig

        config = ClaudeContextConfig()
        self.claude_context = ClaudeContextIntegration(config)
        await self.claude_context.initialize()
        logger.info("claude-context: Semantic search ready")

    async def _init_tree_sitter(self):
        """Initialize Tree-sitter analyzer"""
        from .tree_sitter_analyzer import TreeSitterAnalyzer

        self.tree_sitter = TreeSitterAnalyzer()
        await self.tree_sitter.initialize()
        logger.info("Tree-sitter: Multi-language parser ready")

    async def _init_adhd_features(self):
        """Initialize ADHD code navigator"""
        from .adhd_features import ADHDCodeNavigator, CodeComplexityAnalyzer

        self.adhd_navigator = ADHDCodeNavigator()
        logger.info("ADHD features: Complexity analysis + filtering ready")

    async def _init_navigation_cache(self):
        """Initialize Redis navigation cache for 100x speedup"""
        from navigation_cache import NavigationCache, NavigationCacheConfig

        config = NavigationCacheConfig(
            redis_url="redis://localhost:6379",
            db_index=6,  # Dedicated DB for Serena navigation
            default_ttl=300,  # 5 minutes
            symbol_ttl=600,   # 10 minutes
            definition_ttl=1800  # 30 minutes
        )

        self.navigation_cache = NavigationCache(config)
        await self.navigation_cache.initialize()
        logger.info("Navigation Cache: Redis connected, 100x speedup enabled")

    async def _init_file_watcher(self):
        """Initialize file watcher for auto-refresh on code changes"""
        from file_watcher import FileWatcherManager

        # Create watcher with reference to server instance
        self.file_watcher = FileWatcherManager(
            serena_system={"server": self},
            workspace_path=self.workspace
        )

        # Start watching
        success = self.file_watcher.start()
        if success:
            logger.info("File Watcher: Monitoring code changes, auto-refresh enabled")
        else:
            logger.warning("File Watcher: Failed to start, manual refresh required")

    def register_tools(self):
        """Register MCP tools with the server"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="get_workspace_status",
                    description="Health check and diagnostic information for Serena v2 system",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="find_symbol",
                    description="Search for functions, classes, variables by name (Tier 1 navigation tool). Uses LSP with ADHD filtering (max 10 results). Returns symbols with file location, line number, and complexity scores.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (symbol name or partial match)"
                            },
                            "symbol_type": {
                                "type": "string",
                                "description": "Optional: filter by type (function, class, variable, method, etc)",
                                "enum": ["function", "class", "variable", "method", "module", "interface", "property"]
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum results to return (default: 10, max: 10 for ADHD optimization)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="goto_definition",
                    description="Navigate from usage to definition (Tier 1 navigation tool). Uses LSP to find definition location, returns with 7-line context (3 before, definition, 3 after). ADHD-optimized formatting with highlighted definition line.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "File path (relative to workspace or absolute)"
                            },
                            "line": {
                                "type": "integer",
                                "description": "Line number (1-indexed, like editor display)"
                            },
                            "column": {
                                "type": "integer",
                                "description": "Column number (1-indexed, like editor display)"
                            }
                        },
                        "required": ["file_path", "line", "column"]
                    }
                ),
                Tool(
                    name="get_context",
                    description="Get surrounding code context with complexity annotations (Tier 1 navigation tool). Returns configurable line range with optional complexity scoring for ADHD-safe reading assessment.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "File path (relative to workspace)"
                            },
                            "line": {
                                "type": "integer",
                                "description": "Center line number (1-indexed)"
                            },
                            "context_lines": {
                                "type": "integer",
                                "description": "Lines before and after (default: 10, max: 50 for ADHD)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50
                            },
                            "include_complexity": {
                                "type": "boolean",
                                "description": "Add complexity score annotation (default: true)",
                                "default": True
                            }
                        },
                        "required": ["file_path", "line"]
                    }
                ),
                Tool(
                    name="find_references",
                    description="Find all references/usages of symbol at position (Tier 1 navigation tool). Uses LSP with ADHD-aware filtering (3-40 results based on attention state). Returns reference locations with 3-line context snippets.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "File path (relative to workspace)"
                            },
                            "line": {
                                "type": "integer",
                                "description": "Line number (1-indexed)"
                            },
                            "column": {
                                "type": "integer",
                                "description": "Column number (1-indexed)"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum results (default: 10, dynamically adjusted 3-40 by ADHD Engine)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50
                            },
                            "include_declaration": {
                                "type": "boolean",
                                "description": "Include the declaration in results (default: true)",
                                "default": True
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User identifier for ADHD state lookup (default: 'default')",
                                "default": "default"
                            }
                        },
                        "required": ["file_path", "line", "column"]
                    }
                ),
                Tool(
                    name="analyze_complexity",
                    description="Analyze code complexity for ADHD-safe reading assessment (Tier 2 ADHD tool). Uses Tree-sitter for accurate complexity scoring. Returns 0.0-1.0 score with breakdown and safe reading time estimate. Multi-workspace: aggregates complexity metrics across workspaces.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "File path (relative to workspace)"
                            },
                            "symbol_name": {
                                "type": "string",
                                "description": "Optional: specific symbol to analyze (null = whole file)"
                            },
                            "workspace_path": {
                                "type": "string",
                                "description": "Optional single workspace path"
                            },
                            "workspace_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional multiple workspace paths for aggregated analysis"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="filter_by_focus",
                    description="Filter navigation results by current attention state (Tier 2 ADHD tool). Reduces cognitive load by prioritizing results based on focus level.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "attention_state": {
                                "type": "string",
                                "description": "Current attention level",
                                "enum": ["focused", "scattered", "transitioning"]
                            },
                            "items": {
                                "type": "array",
                                "description": "Items to filter (symbols, files, references)"
                            }
                        },
                        "required": ["attention_state", "items"]
                    }
                ),
                Tool(
                    name="suggest_next_step",
                    description="Learning-based navigation suggestions (Tier 2 ADHD tool). Suggests likely next navigation targets based on patterns. Reduces decision fatigue.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "current_file": {
                                "type": "string",
                                "description": "Current file path"
                            },
                            "current_symbol": {
                                "type": "string",
                                "description": "Optional: current symbol name"
                            }
                        },
                        "required": ["current_file"]
                    }
                ),
                Tool(
                    name="predict_navigation_from_git",
                    description="Predict likely navigation targets from git history patterns (F-NEW-12). Analyzes your git commits to suggest files you typically edit together. Reduces exploration time.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "current_file": {
                                "type": "string",
                                "description": "Current file you're viewing"
                            },
                            "days_back": {
                                "type": "integer",
                                "description": "Days of git history to analyze (default: 90)",
                                "default": 90
                            }
                        },
                        "required": ["current_file"]
                    }
                ),
                Tool(
                    name="find_similar_code",
                    description="Find code semantically similar to natural language query (F-NEW-2). Integrates with Dope-Context for semantic search with AST-aware chunking and neural reranking. Multi-workspace: unified semantic search across workspaces.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query (e.g., 'authentication middleware patterns')"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of results (default: 10, ADHD-adjusted)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 50
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User identifier for ADHD state lookup (default: 'default')",
                                "default": "default"
                            },
                            "workspace_path": {
                                "type": "string",
                                "description": "Optional single workspace path"
                            },
                            "workspace_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional multiple workspace paths for cross-workspace search"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="find_test_file",
                    description="Smart test navigation for TDD workflow (F-NEW-18). Auto-finds test file for implementation or vice versa. Suggests creating test if missing. Multi-workspace: searches across workspaces.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Current file path (implementation or test)"
                            },
                            "workspace_path": {
                                "type": "string",
                                "description": "Optional single workspace path for scoped search"
                            },
                            "workspace_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional multiple workspace paths for multi-workspace search"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_unified_complexity",
                    description="F-NEW-3: Unified Complexity Intelligence (HIGH priority synergy). Combines AST (dope-context), LSP (serena), usage patterns, and ADHD adjustments for accurate cognitive load assessment. Returns 0.0-1.0 score with breakdown and human-readable interpretation. Multi-workspace: aggregates complexity across workspaces.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "File path to analyze"
                            },
                            "symbol": {
                                "type": "string",
                                "description": "Optional function/class name (analyzes whole file if omitted)"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User identifier for ADHD adjustments (default: 'default')",
                                "default": "default"
                            },
                            "workspace_path": {
                                "type": "string",
                                "description": "Optional single workspace path"
                            },
                            "workspace_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional multiple workspace paths for aggregated complexity"
                            }
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="get_reading_order",
                    description="Optimal reading order for understanding code (Tier 2 ADHD tool). Orders files/symbols by complexity progression (simple to complex). Progressive disclosure for learning. Multi-workspace: unified reading order across workspaces.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "description": "File paths to order",
                                "items": {"type": "string"}
                            },
                            "symbols": {
                                "type": "array",
                                "description": "Optional: symbol names to order",
                                "items": {"type": "string"}
                            },
                            "workspace_path": {
                                "type": "string",
                                "description": "Optional single workspace path"
                            },
                            "workspace_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional multiple workspace paths for cross-workspace reading order"
                            }
                        },
                        "required": ["files"]
                    }
                ),
                Tool(
                    name="find_relationships",
                    description="Find code dependencies (Tier 3 advanced tool). Grep-based call/import detection with depth limiting (max 3 levels). ADHD-optimized: max 10 results.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Symbol to find relationships for"
                            },
                            "relationship_type": {
                                "type": "string",
                                "description": "Type of relationship",
                                "enum": ["calls", "imports", "inherits", "all"],
                                "default": "all"
                            },
                            "depth": {
                                "type": "integer",
                                "description": "Max depth (default: 2, max: 3)",
                                "default": 2,
                                "minimum": 1,
                                "maximum": 3
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="get_navigation_patterns",
                    description="Analyze navigation patterns from history (Tier 3 advanced tool). Phase 2D: Returns placeholder. Phase 3: Full pattern learning. Multi-workspace: patterns across workspaces.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days_back": {
                                "type": "integer",
                                "description": "Days of history (default: 7)",
                                "default": 7
                            },
                            "workspace_path": {
                                "type": "string",
                                "description": "Optional single workspace path"
                            },
                            "workspace_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional multiple workspace paths for pattern analysis"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="update_focus_mode",
                    description="Set current focus state (Tier 3 advanced tool). In-memory state, resets on restart. Phase 3: Database persistence.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "mode": {
                                "type": "string",
                                "description": "Focus mode",
                                "enum": ["focused", "scattered", "transitioning"]
                            }
                        },
                        "required": ["mode"]
                    }
                ),
                Tool(
                    name="detect_untracked_work",
                    description="Feature 1: ADHD-optimized untracked work detection (Feature tool). Detects uncommitted git work with no matching ConPort task. Multi-signal confidence scoring. Gentle encouragement to track or finish existing work. Non-blocking: never enforces, just increases awareness.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_number": {
                                "type": "integer",
                                "description": "Current session number for adaptive thresholds (default: 1)",
                                "default": 1,
                                "minimum": 1
                            },
                            "show_details": {
                                "type": "boolean",
                                "description": "Show detailed confidence breakdown (default: false)",
                                "default": False
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="track_untracked_work",
                    description="Feature 1 Action: Create ConPort task from untracked work (Feature tool). Converts detected orphaned work into tracked ConPort progress_entry. Pre-fills task description, complexity, metadata from detection.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_name": {
                                "type": "string",
                                "description": "Work name from detection (auto-generated or custom)"
                            },
                            "custom_description": {
                                "type": "string",
                                "description": "Optional: Override auto-generated description"
                            },
                            "complexity": {
                                "type": "number",
                                "description": "Cognitive load score 0.0-1.0 (auto-estimated if not provided)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["work_name"]
                    }
                ),
                Tool(
                    name="snooze_untracked_work",
                    description="Feature 1 Action: Snooze untracked work reminder (Feature tool). Delays reminder for 1h, 4h, or 1d. Status → snoozed, will remind when duration expires.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_id": {
                                "type": "string",
                                "description": "Untracked work UUID from detection"
                            },
                            "duration": {
                                "type": "string",
                                "description": "Snooze duration",
                                "enum": ["short", "medium", "long"],
                                "default": "medium"
                            }
                        },
                        "required": ["work_id"]
                    }
                ),
                Tool(
                    name="ignore_untracked_work",
                    description="Feature 1 Action: Mark work as abandoned (Feature tool). Status → abandoned, won't remind again. Use for experiments, exploratory work, or false positives.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_id": {
                                "type": "string",
                                "description": "Untracked work UUID from detection"
                            },
                            "reason": {
                                "type": "string",
                                "description": "Optional: Why abandoning (experiment, cleanup, false positive)"
                            }
                        },
                        "required": ["work_id"]
                    }
                ),
                Tool(
                    name="suggest_branch_organization",
                    description="F4: Auto-Branch Suggestions (Feature tool). Analyzes uncommitted files to detect multiple logical work clusters. Suggests creating separate branches for better organization. ADHD benefit: Prevents cognitive overload from mixed contexts.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "min_cluster_size": {
                                "type": "integer",
                                "description": "Minimum files per cluster (default: 2)",
                                "default": 2,
                                "minimum": 1
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_pattern_stats",
                    description="F5: Pattern Learning Stats (Analytics tool). Get pattern learning statistics including cache performance, pattern counts, and top patterns. ADHD benefit: Quick health check of learning system.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_top_patterns",
                    description="F5: Get Top Patterns (Analytics tool). Retrieve most frequent learned patterns by category. Max 10 results to prevent overwhelm. ADHD benefit: Focus on high-confidence patterns only.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern_type": {
                                "type": "string",
                                "description": "Type of pattern (file_extension, directory, branch_prefix)",
                                "default": "file_extension",
                                "enum": ["file_extension", "directory", "branch_prefix"]
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max patterns to return (default 10, ADHD limit)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 10
                            },
                            "min_probability": {
                                "type": "number",
                                "description": "Minimum probability threshold (0.0-1.0, default 0.1)",
                                "default": 0.1,
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_abandoned_work",
                    description="F6: Get Abandoned Work (Analytics tool). List uncommitted work idle for 7+ days. Returns abandonment scores, suggested actions. ADHD benefit: Gentle reminders for forgotten work, max 10 results.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "min_days_idle": {
                                "type": "integer",
                                "description": "Minimum days idle (default 7)",
                                "default": 7,
                                "minimum": 1
                            },
                            "min_score": {
                                "type": "number",
                                "description": "Minimum abandonment score 0.0-1.0 (default 0.5)",
                                "default": 0.5,
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Max results (default 10, ADHD limit)",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 10
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="mark_abandoned",
                    description="F6: Mark Abandoned (Action tool). Record action taken on abandoned work (commit/delete/archive). Feeds F5 pattern learning. ADHD benefit: Positive reinforcement for cleanup actions.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "work_name": {
                                "type": "string",
                                "description": "Name of work from get_abandoned_work"
                            },
                            "action_taken": {
                                "type": "string",
                                "description": "Action taken (commit, delete, archive)",
                                "enum": ["commit", "delete", "archive"]
                            }
                        },
                        "required": ["work_name", "action_taken"]
                    }
                ),
                Tool(
                    name="get_abandonment_stats",
                    description="F6: Abandonment Stats (Analytics tool). Get statistics on abandoned work patterns. Shows total abandoned, by severity, avg days idle. ADHD benefit: Understand personal patterns, no judgment.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_metrics_dashboard",
                    description="F7: Metrics Dashboard (Analytics tool). Aggregate F1-F6 metrics into ADHD-optimized dashboard. 3 levels: 1=summary, 2=breakdown, 3=trends. ADHD benefit: Progressive disclosure, visual indicators, max 5 items per section.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Time window for aggregation (default: 7)",
                                "minimum": 1,
                                "maximum": 90
                            },
                            "level": {
                                "type": "integer",
                                "description": "Disclosure level (1=summary, 2=breakdown, 3=trends)",
                                "enum": [1, 2, 3]
                            },
                            "include_trends": {
                                "type": "boolean",
                                "description": "Show trend arrows (requires history)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_metric_history",
                    description="F7: Metric History (Analytics tool). Get time-series data for specific metric (confidence, pattern_boost, abandonment_rate, pass_rate). ADHD benefit: Visualize progress, celebrate growth.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "metric_name": {
                                "type": "string",
                                "description": "Metric to retrieve",
                                "enum": ["confidence", "pattern_boost", "abandonment_rate", "pass_rate"]
                            },
                            "days": {
                                "type": "integer",
                                "description": "Historical window (default: 30)",
                                "minimum": 1,
                                "maximum": 90
                            },
                            "granularity": {
                                "type": "string",
                                "description": "daily or weekly",
                                "enum": ["daily", "weekly"]
                            }
                        },
                        "required": ["metric_name"]
                    }
                ),
                Tool(
                    name="save_metrics_snapshot",
                    description="F7: Save Metrics Snapshot (Internal tool). Save daily metrics to ConPort for historical tracking. Called automatically after detections. ADHD benefit: Automatic tracking, no manual effort.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_untracked_work_config",
                    description="Feature 1 Config: Get user configuration (Feature tool). Returns thresholds, grace period, quiet hours, snooze durations. Shows current settings.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="update_untracked_work_config",
                    description="Feature 1 Config: Update user configuration (Feature tool). Modify thresholds, grace period, quiet hours. Persists to ConPort. All settings optional.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "enabled": {
                                "type": "boolean",
                                "description": "Enable/disable Feature 1 entirely"
                            },
                            "confidence_threshold": {
                                "type": "number",
                                "description": "Min confidence to show reminders (0.0-1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            },
                            "grace_period_minutes": {
                                "type": "integer",
                                "description": "Grace period for new work (default: 30)",
                                "minimum": 0,
                                "maximum": 180
                            },
                            "quiet_hours_enabled": {
                                "type": "boolean",
                                "description": "Enable quiet hours (no reminders)"
                            },
                            "quiet_hours_start": {
                                "type": "string",
                                "description": "Quiet hours start (HH:MM format, e.g. '22:00')"
                            },
                            "quiet_hours_end": {
                                "type": "string",
                                "description": "Quiet hours end (HH:MM format, e.g. '08:00')"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="read_file",
                    description="Reads a file from the workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "Path relative to workspace root"
                            },
                            "start_line": {
                                "type": "integer",
                                "description": "First line to read (0-indexed, optional)",
                                "default": 0
                            },
                            "end_line": {
                                "type": "integer",
                                "description": "Last line to read (optional, null = end of file)"
                            }
                        },
                        "required": ["relative_path"]
                    }
                ),
                Tool(
                    name="list_dir",
                    description="Lists files and directories in a given path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "Directory path relative to workspace"
                            },
                            "recursive": {
                                "type": "boolean",
                                "description": "Whether to list recursively",
                                "default": False
                            }
                        },
                        "required": ["relative_path"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
            """Route tool calls to implementations"""
            try:
                if name == "get_workspace_status":
                    result = await self.get_workspace_status_tool()
                elif name == "find_symbol":
                    result = await self.find_symbol_tool(**arguments)
                elif name == "goto_definition":
                    result = await self.goto_definition_tool(**arguments)
                elif name == "get_context":
                    result = await self.get_context_tool(**arguments)
                elif name == "find_references":
                    result = await self.find_references_tool(**arguments)
                elif name == "analyze_complexity":
                    result = await self.analyze_complexity_tool(**arguments)
                elif name == "filter_by_focus":
                    result = await self.filter_by_focus_tool(**arguments)
                elif name == "suggest_next_step":
                    result = await self.suggest_next_step_tool(**arguments)
                elif name == "get_reading_order":
                    result = await self.get_reading_order_tool(**arguments)
                elif name == "find_relationships":
                    result = await self.find_relationships_tool(**arguments)
                elif name == "get_navigation_patterns":
                    result = await self.get_navigation_patterns_tool(**arguments)
                elif name == "update_focus_mode":
                    result = await self.update_focus_mode_tool(**arguments)
                elif name == "detect_untracked_work":
                    result = await self.detect_untracked_work_tool(**arguments)
                elif name == "track_untracked_work":
                    result = await self.track_untracked_work_tool(**arguments)
                elif name == "snooze_untracked_work":
                    result = await self.snooze_untracked_work_tool(**arguments)
                elif name == "ignore_untracked_work":
                    result = await self.ignore_untracked_work_tool(**arguments)
                elif name == "suggest_branch_organization":
                    result = await self.suggest_branch_organization_tool(**arguments)
                elif name == "get_pattern_stats":
                    result = await self.get_pattern_stats_tool(**arguments)
                elif name == "get_top_patterns":
                    result = await self.get_top_patterns_tool(**arguments)
                elif name == "get_abandoned_work":
                    result = await self.get_abandoned_work_tool(**arguments)
                elif name == "mark_abandoned":
                    result = await self.mark_abandoned_tool(**arguments)
                elif name == "get_abandonment_stats":
                    result = await self.get_abandonment_stats_tool(**arguments)
                elif name == "get_metrics_dashboard":
                    result = await self.get_metrics_dashboard_tool(**arguments)
                elif name == "get_metric_history":
                    result = await self.get_metric_history_tool(**arguments)
                elif name == "save_metrics_snapshot":
                    result = await self.save_metrics_snapshot_tool(**arguments)
                elif name == "get_untracked_work_config":
                    result = await self.get_untracked_work_config_tool(**arguments)
                elif name == "update_untracked_work_config":
                    result = await self.update_untracked_work_config_tool(**arguments)
                elif name == "read_file":
                    result = await self.read_file_tool(**arguments)
                elif name == "list_dir":
                    result = await self.list_dir_tool(**arguments)
                elif name == "find_similar_code":
                    result = await self.find_similar_code_tool(**arguments)
                elif name == "predict_navigation_from_git":
                    result = await self.predict_navigation_from_git_tool(**arguments)
                elif name == "find_test_file":
                    result = await self.find_test_file_tool(**arguments)
                elif name == "get_unified_complexity":
                    result = await self.get_unified_complexity_tool(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=result)]

            except (ValueError, FileNotFoundError, RuntimeError) as e:
                error_msg = f"❌ Error in {name}: {str(e)}"
                logger.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
            except Exception:
                logger.exception(f"❌ Unexpected error in tool {name}")
                return [TextContent(type="text", text=f"❌ Unexpected error in {name}")]

    async def get_workspace_status_tool(self) -> str:
        """
        Health check and diagnostic tool

        Returns JSON with:
        - Workspace path
        - Component status (loaded/unloaded/failed)
        - Initialization errors
        - Server uptime
        - Tools available
        """
        uptime = (datetime.now() - self.server_start_time).total_seconds()

        status = {
            "server": {
                "name": "serena-v2",
                "phase": "2A",
                "uptime_seconds": round(uptime, 2),
                "started_at": self.server_start_time.isoformat()
            },
            "workspace": {
                "path": str(self.workspace),
                "detected": self.workspace is not None
            },
            "components": {
                "database": {
                    "loaded": self.lazy_components.get("database", False),
                    "error": self.initialization_errors.get("database")
                },
                "lsp": {
                    "loaded": self.lazy_components.get("lsp", False),
                    "error": self.initialization_errors.get("lsp")
                },
                "claude_context": {
                    "loaded": self.lazy_components.get("claude_context", False),
                    "error": self.initialization_errors.get("claude_context")
                },
                "tree_sitter": {
                    "loaded": self.lazy_components.get("tree_sitter", False),
                    "error": self.initialization_errors.get("tree_sitter")
                },
                "adhd_features": {
                    "loaded": self.lazy_components.get("adhd_features", False),
                    "error": self.initialization_errors.get("adhd_features")
                }
            },
            "tools": {
                "phase_1": ["read_file", "list_dir"],
                "phase_2a": ["get_workspace_status"],
                "phase_2b": ["find_symbol", "goto_definition", "get_context", "find_references"],
                "phase_2c": ["analyze_complexity", "filter_by_focus", "suggest_next_step", "get_reading_order"],
                "phase_2d": ["find_relationships", "get_navigation_patterns", "update_focus_mode"],
                "feature_1_detection": ["detect_untracked_work"],
                "feature_1_actions": ["track_untracked_work", "snooze_untracked_work", "ignore_untracked_work"],
                "feature_1_config": ["get_untracked_work_config", "update_untracked_work_config"],
                "phase_2_deferred": ["semantic_search"],
                "total_available": 20,
                "total_planned": 21,
                "feature_1_status": "complete (detection + actions + storage + config + reminders)",
                "tier_3_mode": "simplified (Phase 3 will add full database integration)"
            }
        }

        return json.dumps(status, indent=2)

    async def find_symbol_tool(
        self,
        query: str,
        symbol_type: Optional[str] = None,
        max_results: int = 10,
        user_id: str = "default",
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Search for symbols (functions, classes, variables) by name

        Tier 1 Navigation Tool:
        - Uses LSP workspace_symbols (lazy-loaded)
        - ADHD-aware: Dynamic result limits (3-40 based on attention state)
        - Complexity scoring if tree_sitter available
        - Fallback: Simple file search if LSP unavailable
        - Multi-workspace: Search across multiple workspaces

        Args:
            query: Search query (symbol name or partial match)
            symbol_type: Optional filter by type
            max_results: Max results (default 10, dynamically adjusted by ADHD Engine)
            user_id: User identifier for ADHD state lookup
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON array of symbols with file, line, type, complexity
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.find_symbol_multi(
                query, symbol_type, max_results, user_id,
                workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        # Get dynamic max_results from ADHD Engine (F-NEW-1)
        max_results = await get_dynamic_max_results(user_id, max_results)

        # Try navigation cache first (100x speedup)
        cache_available = await self._ensure_component("navigation_cache")
        if cache_available and self.navigation_cache:
            cache_key = f"find_symbol:{query}:{symbol_type}:{max_results}"
            cached_result = await self.navigation_cache.get_navigation_result(cache_key)
            if cached_result:
                logger.info(f"find_symbol: '{query}' (CACHE HIT)")
                return json.dumps(cached_result, indent=2)

        # Ensure LSP is loaded
        lsp_available = await self._ensure_component("lsp")

        if lsp_available and self.lsp:
            # Use LSP workspace symbols
            try:
                symbols = await self.lsp.workspace_symbols(query)

                # Filter by symbol_type if specified
                if symbol_type:
                    symbols = [s for s in symbols if s.get("kind") == symbol_type]

                # Apply ADHD filtering: max 10 results
                symbols = symbols[:max_results]

                # Try to add complexity scores
                tree_sitter_available = await self._ensure_component("tree_sitter")
                if tree_sitter_available and self.tree_sitter:
                    for symbol in symbols:
                        try:
                            complexity = await self.tree_sitter.analyze_complexity(
                                symbol.get("location", {}).get("uri", ""),
                                symbol.get("name")
                            )
                            symbol["complexity"] = complexity.get("score", 0.0)
                        except (FileNotFoundError, RuntimeError) as e:
                            symbol["complexity"] = None
                            logger.debug(f"Complexity analysis skipped: {e}")
                        except Exception:
                            symbol["complexity"] = None
                            logger.exception("Unexpected complexity analysis error")
                result = {
                    "query": query,
                    "symbol_type_filter": symbol_type,
                    "found": len(symbols),
                    "max_results": max_results,
                    "adhd_filtered": True,
                    "symbols": symbols
                }

                # Cache result for future queries (symbol_ttl: 10 minutes)
                if cache_available and self.navigation_cache:
                    cache_key = f"find_symbol:{query}:{symbol_type}:{max_results}"
                    await self.navigation_cache.cache_navigation_result(
                        cache_key, result, ttl=self.navigation_cache.config.symbol_ttl
                    )

                return json.dumps(result, indent=2)

            except (asyncio.TimeoutError, RuntimeError) as e:
                logger.warning(f"LSP symbol search failed: {e}, falling back to basic search")
            except Exception:
                logger.exception("Unexpected LSP symbol search error; falling back")
                # Fall through to fallback mode

        # Fallback: Simple file-based search using glob
        logger.info("Using fallback symbol search (LSP unavailable)")

        # Simple fallback: search Python files for class/def patterns
        import re
        from pathlib import Path

        matches = []
        pattern = re.compile(rf"(class|def)\s+{re.escape(query)}\w*\s*[\(\:]", re.IGNORECASE)

        for py_file in self.workspace.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for line_num, line in enumerate(content.splitlines(), 1):
                    if pattern.search(line):
                        matches.append({
                            "name": query,
                            "kind": "class" if "class" in line else "function",
                            "file": str(py_file.relative_to(self.workspace)),
                            "line": line_num,
                            "complexity": None,
                            "fallback_mode": True
                        })

                        if len(matches) >= max_results:
                            break
            except (UnicodeDecodeError, OSError) as e:
                logger.debug(f"Skipping file (decode/fs error): {py_file} - {e}")
                continue
            except Exception:
                logger.exception(f"Unexpected symbol scan error in {py_file}")
                continue
            if len(matches) >= max_results:
                break

        result = {
            "query": query,
            "symbol_type_filter": symbol_type,
            "found": len(matches),
            "max_results": max_results,
            "adhd_filtered": True,
            "fallback_mode": True,
            "lsp_unavailable": not lsp_available,
            "symbols": matches
        }

        # Cache fallback results too (shorter TTL since less reliable)
        if cache_available and self.navigation_cache:
            cache_key = f"find_symbol:{query}:{symbol_type}:{max_results}"
            await self.navigation_cache.cache_navigation_result(
                cache_key, result, ttl=180  # 3 minutes for fallback results
            )

        return json.dumps(result, indent=2)

    async def goto_definition_tool(
        self,
        file_path: str,
        line: int,
        column: int
    ) -> str:
        """
        Navigate from usage to definition location

        Tier 1 Navigation Tool:
        - Uses SimpleLSPClient (pylsp) for goto definition
        - Returns definition location with 7-line context
        - ADHD-optimized: Highlights definition line with >>>
        - Fallback: Grep-based search if LSP unavailable

        Args:
            file_path: File path (relative to workspace or absolute)
            line: Line number (1-indexed, like editor)
            column: Column number (1-indexed, like editor)

        Returns:
            JSON with definition location and context
        """
        start_time = datetime.now()

        # Resolve file path
        if Path(file_path).is_absolute():
            resolved_path = Path(file_path)
        else:
            resolved_path = self.workspace / file_path

        if not resolved_path.exists():
            return json.dumps({
                "error": f"File not found: {file_path}",
                "query": {"file": file_path, "line": line, "column": column}
            }, indent=2)

        # Convert to file URI and 0-indexed position
        file_uri = f"file://{resolved_path}"
        lsp_line = line - 1  # LSP uses 0-indexed
        lsp_column = column - 1

        # ADHD Optimization: Check if workspace is small enough for LSP
        should_try_lsp = await self._should_use_lsp()

        # Try LSP only if workspace is reasonably sized
        lsp_available = should_try_lsp and await self._ensure_component("lsp")

        if lsp_available and self.lsp:
            try:
                locations = await self.lsp.goto_definition(file_uri, lsp_line, lsp_column)

                if locations:
                    # Take first definition (ADHD: avoid overwhelm from multiple defs)
                    location = locations[0]

                    # Extract file and position from LSP response
                    def_uri = location.get("uri", "")
                    def_range = location.get("range", {})
                    def_start = def_range.get("start", {})
                    def_line = def_start.get("line", 0) + 1  # Convert to 1-indexed
                    def_column = def_start.get("character", 0) + 1

                    # Get definition file path
                    def_file_path = def_uri.replace("file://", "")

                    # Extract 7-line context (3 before, def line, 3 after)
                    context = await self._extract_definition_context(
                        Path(def_file_path),
                        def_line,
                        def_column
                    )

                    elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                    result = {
                        "query": {
                            "file": file_path,
                            "line": line,
                            "column": column
                        },
                        "definition": {
                            "file": str(Path(def_file_path).relative_to(self.workspace)) if self.workspace in Path(def_file_path).parents else def_file_path,
                            "line": def_line,
                            "column": def_column,
                            "context": context
                        },
                        "performance": {
                            "latency_ms": round(elapsed_ms, 2),
                            "mode": "lsp",
                            "cached": False
                        }
                    }

                    logger.info(f"goto_definition: {file_path}:{line}:{column} → {def_line} ({elapsed_ms:.1f}ms)")
                    return json.dumps(result, indent=2)

            except (asyncio.TimeoutError, RuntimeError) as e:
                logger.warning(f"LSP goto_definition failed: {e}, using fallback")
            except Exception:
                logger.exception("Unexpected LSP goto_definition error; falling back")
                # Fall through to fallback

        # Fallback: Grep-based definition search
        logger.info("Using fallback goto_definition (LSP unavailable)")

        # Read the source line to extract symbol name
        try:
            source_content = resolved_path.read_text()
            source_lines = source_content.splitlines()

            if line > len(source_lines):
                return json.dumps({"error": "Line number out of range"}, indent=2)

            source_line = source_lines[line - 1]

            # Simple symbol extraction: take word at column position
            symbol = self._extract_symbol_at_position(source_line, column - 1)

            if not symbol:
                return json.dumps({"error": "No symbol found at position"}, indent=2)

            # Grep for definition
            import re
            pattern = re.compile(rf"(class|def)\s+{re.escape(symbol)}\s*[\(\:]")

            # Search current file first, then workspace
            for search_file in [resolved_path] + list(self.workspace.rglob("*.py")):
                if ".venv" in str(search_file) or "__pycache__" in str(search_file):
                    continue

                try:
                    content = search_file.read_text()
                    for line_num, line_text in enumerate(content.splitlines(), 1):
                        if pattern.search(line_text):
                            # Found definition!
                            context = await self._extract_definition_context(
                                search_file,
                                line_num,
                                column
                            )

                            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                            result = {
                                "query": {"file": file_path, "line": line, "column": column},
                                "definition": {
                                    "file": str(search_file.relative_to(self.workspace)),
                                    "line": line_num,
                                    "column": 0,
                                    "context": context
                                },
                                "performance": {
                                    "latency_ms": round(elapsed_ms, 2),
                                    "mode": "fallback_grep",
                                    "lsp_unavailable": not lsp_available
                                }
                            }

                            return json.dumps(result, indent=2)

                except Exception as e:
                    continue
            # No definition found
            return json.dumps({
                "error": "No definition found",
                "query": {"file": file_path, "line": line, "column": column},
                "symbol": symbol,
                "mode": "fallback_grep"
            }, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    async def get_context_tool(
        self,
        file_path: str,
        line: int,
        context_lines: int = 10,
        include_complexity: bool = True,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Get surrounding code context with optional complexity annotations

        Tier 1 Navigation Tool:
        - Returns code centered around target line
        - ADHD optimization: Max 50 context lines (prevents overwhelm)
        - Optional complexity scoring via Tree-sitter
        - Highlights the center line
        - Multi-workspace: Get context from multiple workspaces

        Args:
            file_path: File path (relative to workspace)
            line: Center line number (1-indexed)
            context_lines: Lines before/after center (default: 10, max: 50)
            include_complexity: Add complexity score (default: true)
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON with context and optional complexity
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.get_context_multi(
                file_path, line, context_lines,
                workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        start_time = datetime.now()

        # Enforce ADHD max context constraint
        context_lines = min(context_lines, 50)

        # Resolve path
        file_path_obj = self._resolve_path(file_path)

        if not file_path_obj.exists():
            return json.dumps({
                "error": f"File not found: {file_path}"
            }, indent=2)

        # Read file content
        content = file_path_obj.read_text()
        lines = content.splitlines()

        # Calculate range
        start_line = max(0, line - context_lines - 1)
        end_line = min(len(lines), line + context_lines)

        # Build context with highlighted center line
        context_text_lines = []
        for i in range(start_line, end_line):
            line_num = i + 1
            line_text = lines[i] if i < len(lines) else ""

            # Highlight center line
            if line_num == line:
                context_text_lines.append(f">>> {line_num:4d}: {line_text}  ← CENTER")
            else:
                context_text_lines.append(f"    {line_num:4d}: {line_text}")

        context_text = "\n".join(context_text_lines)

        # Try to get complexity score
        complexity_score = None
        if include_complexity:
            tree_sitter_available = await self._ensure_component("tree_sitter")
            if tree_sitter_available and self.tree_sitter:
                try:
                    # Analyze the visible range
                    analysis = await self.tree_sitter.analyze_complexity(
                        str(file_path_obj),
                        None  # Analyze whole file
                    )
                    complexity_score = analysis.get("score", 0.0)
                except (RuntimeError, FileNotFoundError) as e:
                    logger.debug(f"Complexity analysis failed: {e}")
                except Exception:
                    logger.exception("Unexpected complexity analysis error")

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = {
            "file": file_path,
            "center_line": line,
            "range": {
                "start": start_line + 1,
                "end": end_line,
                "total_lines": end_line - start_line
            },
            "context": context_text,
            "complexity": {
                "score": complexity_score,
                "available": complexity_score is not None,
                "safe_reading_minutes": round(complexity_score * 15, 1) if complexity_score else None
            } if include_complexity else None,
            "performance": {
                "latency_ms": round(elapsed_ms, 2)
            }
        }

        logger.info(f"get_context: {file_path}:{line} ±{context_lines} lines ({elapsed_ms:.1f}ms)")
        return json.dumps(result, indent=2)

    async def find_references_tool(
        self,
        file_path: str,
        line: int,
        column: int,
        max_results: int = 10,
        include_declaration: bool = True,
        user_id: str = "default",
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Find all references/usages of symbol at position

        Tier 1 Navigation Tool:
        - Uses SimpleLSPClient (pylsp) for finding references
        - ADHD-aware: Dynamic result limits (3-40 based on attention state)
        - Returns each reference with 3-line context snippet
        - Fallback: Grep-based search if LSP unavailable
        - Multi-workspace: Find references across workspaces

        Args:
            file_path: File path (relative to workspace)
            line: Line number (1-indexed)
            column: Column number (1-indexed)
            max_results: Max results (default: 10, dynamically adjusted by ADHD Engine)
            include_declaration: Include declaration in results
            user_id: User identifier for ADHD state lookup
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON with reference locations and context snippets
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.find_references_multi(
                file_path, line, column, max_results,
                include_declaration, user_id,
                workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        start_time = datetime.now()

        # Get dynamic max_results from ADHD Engine (F-NEW-1)
        max_results = await get_dynamic_max_results(user_id, max_results)

        # Resolve path
        if Path(file_path).is_absolute():
            resolved_path = Path(file_path)
        else:
            resolved_path = self.workspace / file_path

        if not resolved_path.exists():
            return json.dumps({
                "error": f"File not found: {file_path}"
            }, indent=2)

        # Convert to file URI and 0-indexed
        file_uri = f"file://{resolved_path}"
        lsp_line = line - 1
        lsp_column = column - 1

        # ADHD Optimization: Check if workspace is small enough for LSP
        should_try_lsp = await self._should_use_lsp()

        # Try LSP only if workspace is reasonably sized
        lsp_available = should_try_lsp and await self._ensure_component("lsp")

        if lsp_available and self.lsp:
            try:
                locations = await self.lsp.find_references(
                    file_uri,
                    lsp_line,
                    lsp_column,
                    include_declaration
                )

                # Apply ADHD filtering
                locations = locations[:max_results]

                # Extract context for each reference
                references = []
                for loc in locations:
                    ref_uri = loc.get("uri", "")
                    ref_range = loc.get("range", {})
                    ref_start = ref_range.get("start", {})
                    ref_line = ref_start.get("line", 0) + 1  # Convert to 1-indexed
                    ref_column = ref_start.get("character", 0) + 1

                    # Get reference file path
                    ref_file_path = ref_uri.replace("file://", "")

                    # Extract 3-line context (1 before, ref line, 1 after)
                    context = await self._extract_reference_context(
                        Path(ref_file_path),
                        ref_line
                    )

                    references.append({
                        "file": str(Path(ref_file_path).relative_to(self.workspace)) if self.workspace in Path(ref_file_path).parents else ref_file_path,
                        "line": ref_line,
                        "column": ref_column,
                        "context": context
                    })

                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                result = {
                    "query": {"file": file_path, "line": line, "column": column},
                    "found": len(references),
                    "max_results": max_results,
                    "adhd_filtered": len(locations) > max_results,
                    "references": references,
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2),
                        "mode": "lsp"
                    }
                }

                logger.info(f"find_references: {file_path}:{line}:{column} → {len(references)} refs ({elapsed_ms:.1f}ms)")
                return json.dumps(result, indent=2)

            except (asyncio.TimeoutError, RuntimeError) as e:
                logger.warning(f"LSP find_references failed: {e}, using fallback")
            except Exception:
                logger.exception("Unexpected LSP find_references error; falling back")
                # Fall through to fallback

        # Fallback: Grep-based reference search
        logger.info("Using fallback find_references (LSP unavailable)")

        try:
            # Extract symbol name
            source_content = resolved_path.read_text()
            source_lines = source_content.splitlines()

            if line > len(source_lines):
                return json.dumps({"error": "Line number out of range"}, indent=2)

            source_line = source_lines[line - 1]
            symbol = self._extract_symbol_at_position(source_line, column - 1)

            if not symbol:
                return json.dumps({"error": "No symbol found at position"}, indent=2)

            # Grep for symbol usage
            import re
            # Match whole word to avoid partial matches
            pattern = re.compile(rf"\b{re.escape(symbol)}\b")

            references = []
            for py_file in self.workspace.rglob("*.py"):
                if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                    continue

                try:
                    content = py_file.read_text()
                    for line_num, line_text in enumerate(content.splitlines(), 1):
                        if pattern.search(line_text):
                            context = await self._extract_reference_context(py_file, line_num)

                            references.append({
                                "file": str(py_file.relative_to(self.workspace)),
                                "line": line_num,
                                "column": 0,
                                "context": context
                            })

                            if len(references) >= max_results:
                                break
                except Exception as e:
                    continue
                if len(references) >= max_results:
                    break

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "query": {"file": file_path, "line": line, "column": column},
                "symbol": symbol,
                "found": len(references),
                "max_results": max_results,
                "adhd_filtered": True,
                "references": references,
                "performance": {
                    "latency_ms": round(elapsed_ms, 2),
                    "mode": "fallback_grep",
                    "lsp_unavailable": not lsp_available
                }
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    async def _extract_reference_context(self, file_path: Path, line: int) -> str:
        """
        Extract 3-line context for reference (1 before, ref line, 1 after)

        ADHD-optimized: Shorter context than definition (3 lines vs 7)
        """
        try:
            content = file_path.read_text()
            lines = content.splitlines()

            # Calculate range (1 before, 1 target, 1 after)
            start_line = max(0, line - 2)
            end_line = min(len(lines), line + 1)

            context_lines = []
            for i in range(start_line, end_line):
                line_num = i + 1
                line_text = lines[i] if i < len(lines) else ""

                # Highlight reference line
                if line_num == line:
                    context_lines.append(f"→ {line_num:4d}: {line_text}")
                else:
                    context_lines.append(f"  {line_num:4d}: {line_text}")

            return "\n".join(context_lines)

        except Exception as e:
            return f"(context unavailable: {e})"
    async def analyze_complexity_tool(
        self,
        file_path: str,
        symbol_name: Optional[str] = None,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Analyze code complexity for ADHD-safe reading assessment

        Tier 2 ADHD Intelligence Tool:
        - Uses Tree-sitter for accurate structural analysis
        - Returns 0.0-1.0 complexity score
        - Provides breakdown (cyclomatic, nesting, lines)
        - Estimates safe reading time based on complexity
        - Fallback: Basic metrics if Tree-sitter unavailable
        - Multi-workspace: Analyze complexity across workspaces

        Args:
            file_path: File path (relative to workspace)
            symbol_name: Optional symbol to analyze (null = whole file)
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON with complexity score, breakdown, reading time
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.analyze_complexity_multi(
                file_path, symbol_name,
                workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        start_time = datetime.now()

        # Resolve path
        file_path_obj = self._resolve_path(file_path)

        if not file_path_obj.exists():
            return json.dumps({
                "error": f"File not found: {file_path}"
            }, indent=2)

        # Try Tree-sitter analysis
        tree_sitter_available = await self._ensure_component("tree_sitter")

        if tree_sitter_available and self.tree_sitter:
            try:
                analysis = await self.tree_sitter.analyze_complexity(
                    str(file_path_obj),
                    symbol_name
                )

                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

                # Calculate ADHD-friendly reading time
                complexity_score = analysis.get("score", 0.0)
                safe_reading_minutes = round(complexity_score * 15, 1)

                # ADHD assessment
                if complexity_score < 0.3:
                    assessment = "LOW - Safe to read anytime"
                    recommendation = "Can read when attention scattered"
                elif complexity_score < 0.6:
                    assessment = "MEDIUM - Needs focus"
                    recommendation = "Schedule focused time block"
                else:
                    assessment = "HIGH - Complex code"
                    recommendation = "Peak focus hours only, consider breaking into chunks"

                result = {
                    "file": file_path,
                    "symbol": symbol_name,
                    "complexity": {
                        "score": complexity_score,
                        "level": assessment,
                        "recommendation": recommendation
                    },
                    "metrics": {
                        "cyclomatic_complexity": analysis.get("cyclomatic", 0),
                        "nesting_depth": analysis.get("nesting", 0),
                        "lines_of_code": analysis.get("lines", 0),
                        "function_count": analysis.get("functions", 0)
                    },
                    "adhd_guidance": {
                        "safe_reading_minutes": safe_reading_minutes,
                        "break_after_minutes": 25,  # Standard Pomodoro
                        "chunk_if_exceeds_minutes": 15
                    },
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2),
                        "mode": "tree_sitter"
                    }
                }

                logger.info(f"analyze_complexity: {file_path} → {complexity_score:.2f} ({elapsed_ms:.1f}ms)")
                return json.dumps(result, indent=2)

            except (RuntimeError, FileNotFoundError) as e:
                logger.warning(f"Tree-sitter analysis failed: {e}, using fallback")
            except Exception:
                logger.exception("Unexpected tree-sitter analysis error; using fallback")
                # Fall through to fallback

        # Fallback: Basic line/character counting
        logger.info("Using fallback complexity analysis (Tree-sitter unavailable)")

        try:
            content = file_path_obj.read_text()
            lines = content.splitlines()

            # Simple heuristics
            line_count = len(lines)
            char_count = len(content)

            # Estimate complexity from length
            # 0-100 lines = 0.0-0.3, 100-500 = 0.3-0.6, 500+ = 0.6-1.0
            if line_count < 100:
                score = line_count / 300
            elif line_count < 500:
                score = 0.3 + ((line_count - 100) / 800)
            else:
                score = min(1.0, 0.6 + ((line_count - 500) / 1000))

            safe_reading_minutes = round(score * 15, 1)

            if score < 0.3:
                assessment = "LOW - Safe to read anytime"
            elif score < 0.6:
                assessment = "MEDIUM - Needs focus"
            else:
                assessment = "HIGH - Complex code"

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "file": file_path,
                "symbol": symbol_name,
                "complexity": {
                    "score": round(score, 2),
                    "level": assessment,
                    "recommendation": "Estimate based on file size"
                },
                "metrics": {
                    "lines_of_code": line_count,
                    "characters": char_count,
                    "estimated": True
                },
                "adhd_guidance": {
                    "safe_reading_minutes": safe_reading_minutes,
                    "break_after_minutes": 25
                },
                "performance": {
                    "latency_ms": round(elapsed_ms, 2),
                    "mode": "fallback_basic",
                    "tree_sitter_unavailable": not tree_sitter_available
                }
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    async def filter_by_focus_tool(
        self,
        attention_state: str,
        items: List[Dict[str, Any]]
    ) -> str:
        """
        Filter navigation results by attention state

        Tier 2 ADHD Intelligence Tool:
        - Reduces cognitive load based on focus level
        - focused: Show up to 10 items
        - scattered: Show top 3 items only
        - transitioning: Show top 5 items

        Args:
            attention_state: focused, scattered, or transitioning
            items: List of items to filter

        Returns:
            Filtered and prioritized items
        """
        # ADHD filtering thresholds
        limits = {
            "focused": 10,
            "scattered": 3,
            "transitioning": 5
        }

        max_items = limits.get(attention_state, 10)

        # Filter items
        filtered_items = items[:max_items]

        result = {
            "attention_state": attention_state,
            "original_count": len(items),
            "filtered_count": len(filtered_items),
            "removed_count": len(items) - len(filtered_items),
            "items": filtered_items,
            "adhd_guidance": {
                "max_items_for_state": max_items,
                "recommendation": f"Showing {len(filtered_items)} items optimal for {attention_state} state"
            }
        }

        logger.info(f"filter_by_focus: {attention_state} → {len(items)} items → {len(filtered_items)} items")
        return json.dumps(result, indent=2)

    async def suggest_next_step_tool(
        self,
        current_file: str,
        current_symbol: Optional[str] = None
    ) -> str:
        """
        Learning-based navigation suggestions

        Tier 2 ADHD Intelligence Tool:
        - Suggests likely next navigation targets
        - Reduces decision fatigue
        - Phase 2C: Simplified heuristics
        - Phase 2D: Full adaptive learning engine

        Args:
            current_file: Current file path
            current_symbol: Optional current symbol

        Returns:
            Top 3 suggested next steps
        """
        # Resolve path
        file_path_obj = self._resolve_path(current_file)

        if not file_path_obj.exists():
            return json.dumps({"error": f"File not found: {current_file}"}, indent=2)

        # Simplified suggestions (Phase 2C heuristics)
        # Phase 2D will use full adaptive learning engine
        suggestions = []

        # Suggestion 1: If in test file, suggest source file
        if "test_" in file_path_obj.name or "_test" in file_path_obj.name:
            source_file = file_path_obj.name.replace("test_", "").replace("_test", "")
            suggestions.append({
                "type": "source_file",
                "target": source_file,
                "reason": "Test file → Source file pattern",
                "confidence": 0.8
            })
        # Suggestion 2: If in source, suggest test file
        elif not file_path_obj.name.startswith("test_"):
            test_file = f"test_{file_path_obj.name}"
            suggestions.append({
                "type": "test_file",
                "target": test_file,
                "reason": "Source file → Test file pattern",
                "confidence": 0.7
            })

        # Suggestion 3: Related imports (files imported in current file)
        try:
            content = file_path_obj.read_text()
            import re
            import_pattern = re.compile(r"^from\s+\.(\w+)\s+import|^import\s+\.(\w+)", re.MULTILINE)
            for match in import_pattern.finditer(content):
                module = match.group(1) or match.group(2)
                if module:
                    suggestions.append({
                        "type": "imported_module",
                        "target": f"{module}.py",
                        "reason": f"Imported in {file_path_obj.name}",
                        "confidence": 0.6
                    })
                if len(suggestions) >= 3:
                    break
        except Exception as e:
            logger.debug(f"Failed to build import-based suggestions: {e}")
        # Limit to top 3
        suggestions = suggestions[:3]

        result = {
            "current_file": current_file,
            "current_symbol": current_symbol,
            "suggestions": suggestions,
            "mode": "heuristic",
            "adhd_guidance": {
                "decision_reduction": f"Showing {len(suggestions)} suggestions to reduce choice paralysis",
                "upgrade_note": "Phase 2D will add pattern learning based on your navigation history"
            }
        }

        logger.info(f"suggest_next_step: {current_file} → {len(suggestions)} suggestions")
        return json.dumps(result, indent=2)

    async def get_reading_order_tool(
        self,
        files: List[str],
        symbols: Optional[List[str]] = None,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Optimal reading order for understanding code

        Tier 2 ADHD Intelligence Tool:
        - Orders by complexity (simple → complex)
        - Progressive disclosure for learning
        - Estimates reading session breakdown
        - Multi-workspace: Reading order across workspaces

        Args:
            files: File paths to order
            symbols: Optional symbol names
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            Ordered files with complexity progression
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.get_reading_order_multi(
                files, symbols, workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        start_time = datetime.now()

        # Analyze complexity for each file
        file_complexities = []

        for file_path in files:
            try:
                # Get complexity score
                complexity_result = await self.analyze_complexity_tool(file_path, None)
                complexity_data = json.loads(complexity_result)

                score = complexity_data.get("complexity", {}).get("score", 0.5)
                reading_minutes = complexity_data.get("adhd_guidance", {}).get("safe_reading_minutes", 5.0)

                file_complexities.append({
                    "file": file_path,
                    "complexity_score": score,
                    "reading_minutes": reading_minutes,
                    "level": complexity_data.get("complexity", {}).get("level", "UNKNOWN")
                })

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
                # Default complexity if analysis fails
                file_complexities.append({
                    "file": file_path,
                    "complexity_score": 0.5,
                    "reading_minutes": 7.5,
                    "level": "UNKNOWN"
                })

        # Sort by complexity (simple first)
        file_complexities.sort(key=lambda x: x["complexity_score"])

        # Calculate session breakdown
        total_minutes = sum(f["reading_minutes"] for f in file_complexities)
        sessions_needed = max(1, round(total_minutes / 25))  # 25-minute Pomodoros

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = {
            "total_files": len(files),
            "reading_order": file_complexities,
            "session_plan": {
                "total_reading_minutes": round(total_minutes, 1),
                "pomodoro_sessions_needed": sessions_needed,
                "breaks_recommended": sessions_needed - 1,
                "progressive_disclosure": "Start with simplest files to build understanding"
            },
            "adhd_guidance": {
                "strategy": "Complexity progression (simple → complex)",
                "chunk_recommendation": "Read 1-2 files per 25-min session",
                "break_pattern": "5-min break between sessions, 15-min after 4 sessions"
            },
            "performance": {
                "latency_ms": round(elapsed_ms, 2)
            }
        }

        logger.info(f"get_reading_order: {len(files)} files → {sessions_needed} sessions ({elapsed_ms:.1f}ms)")
        return json.dumps(result, indent=2)

    async def find_relationships_tool(
        self,
        symbol: str,
        relationship_type: str = "all",
        depth: int = 2,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Find code dependencies via grep-based detection

        Tier 3 Advanced Tool (Phase 2D Simplified):
        - Searches for function calls, imports, inheritance
        - ADHD-optimized: max 10 results, max 3 depth levels
        - Phase 3: Will upgrade to PostgreSQL graph operations
        - Multi-workspace: Relationships across workspaces

        Args:
            symbol: Symbol to find relationships for
            relationship_type: calls, imports, inherits, or all
            depth: Maximum traversal depth (default: 2, max: 3)
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON with relationships found
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.find_relationships_multi(
                symbol, relationship_type, depth,
                workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        start_time = datetime.now()

        # Enforce ADHD depth limit
        depth = min(depth, 3)

        import re

        relationships = []

        # Pattern matching based on relationship type
        patterns = []
        if relationship_type in ["calls", "all"]:
            # Find function calls: symbol(...)
            patterns.append(("calls", re.compile(rf"\b{re.escape(symbol)}\s*\(")))

        if relationship_type in ["imports", "all"]:
            # Find imports: from X import symbol, import symbol
            patterns.append(("imports", re.compile(rf"(from .* import .*\b{re.escape(symbol)}\b|import .*\b{re.escape(symbol)}\b)")))

        if relationship_type in ["inherits", "all"]:
            # Find class inheritance: class X(symbol)
            patterns.append(("inherits", re.compile(rf"class \w+\([^)]*\b{re.escape(symbol)}\b")))

        # Search workspace
        for py_file in self.workspace.rglob("*.py"):
            if ".venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for line_num, line_text in enumerate(content.splitlines(), 1):
                    for rel_type, pattern in patterns:
                        if pattern.search(line_text):
                            relationships.append({
                                "type": rel_type,
                                "file": str(py_file.relative_to(self.workspace)),
                                "line": line_num,
                                "context": line_text.strip()[:100]  # First 100 chars
                            })

                            if len(relationships) >= 10:  # ADHD limit
                                break

                    if len(relationships) >= 10:
                        break
            except Exception as e:
                logger.debug("Skipping relationship scan for %s: %s", py_file, e)
                continue
            if len(relationships) >= 10:
                break

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = {
            "symbol": symbol,
            "relationship_type": relationship_type,
            "depth": depth,
            "found": len(relationships),
            "max_results": 10,
            "adhd_filtered": True,
            "relationships": relationships,
            "mode": "simplified_grep",
            "upgrade_note": "Phase 3 will add PostgreSQL graph for multi-level traversal",
            "performance": {
                "latency_ms": round(elapsed_ms, 2)
            }
        }

        logger.info(f"find_relationships: {symbol} ({relationship_type}) → {len(relationships)} rels ({elapsed_ms:.1f}ms)")
        return json.dumps(result, indent=2)

    async def get_navigation_patterns_tool(
        self,
        days_back: int = 7,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Analyze navigation patterns from history

        Tier 3 Advanced Tool (Phase 2D Placeholder):
        - Phase 2D: Returns placeholder message
        - Phase 3: Full pattern recognition with database
        - Multi-workspace: Navigation patterns across workspaces

        Args:
            days_back: Days of history to analyze
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON with pattern analysis (placeholder in Phase 2D)
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.get_navigation_patterns_multi(
                days_back, workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        result = {
            "status": "learning_phase",
            "message": "Pattern learning requires navigation history database",
            "recommendation": "Use suggest_next_step for immediate navigation help",
            "current_capabilities": {
                "heuristic_suggestions": "Available via suggest_next_step tool",
                "test_source_patterns": "Detects test/source file relationships",
                "import_following": "Suggests imported modules"
            },
            "phase_3_features": {
                "adaptive_learning": "Learns from your navigation sequences",
                "personalized_patterns": "Recognizes your coding style",
                "effectiveness_tracking": "Measures which patterns help you",
                "context_switching": "Optimizes for interruptions"
            },
            "upgrade_timeline": "Phase 3: Full adaptive learning with PostgreSQL persistence"
        }

        logger.info(f"get_navigation_patterns: placeholder (days_back={days_back})")
        return json.dumps(result, indent=2)

    async def update_focus_mode_tool(
        self,
        mode: str
    ) -> str:
        """
        Set current focus state for adaptive filtering

        Tier 3 Advanced Tool (Phase 2D In-Memory):
        - Updates in-memory focus state
        - Affects filter_by_focus tool behavior
        - Phase 3: Will persist to database

        Args:
            mode: focused, scattered, or transitioning

        Returns:
            JSON with updated focus state
        """
        # Update in-memory state
        old_mode = self.current_focus_mode
        self.current_focus_mode = mode

        # Get filtering thresholds
        limits = {
            "focused": 10,
            "scattered": 3,
            "transitioning": 5
        }

        result = {
            "mode": mode,
            "previous_mode": old_mode,
            "max_results": limits.get(mode, 10),
            "filtering_behavior": {
                "focused": "Show up to 10 items - full cognitive capacity",
                "scattered": "Show top 3 items - reduce overwhelm",
                "transitioning": "Show top 5 items - moderate filtering"
            }.get(mode, "Unknown mode"),
            "persistence": {
                "saved_to_database": False,
                "restart_behavior": "Resets to 'focused' on server restart",
                "upgrade_note": "Phase 3 will persist across sessions"
            }
        }

        logger.info(f"update_focus_mode: {old_mode} → {mode}")
        return json.dumps(result, indent=2)

    async def detect_untracked_work_tool(
        self,
        session_number: int = 1,
        show_details: bool = False
    ) -> str:
        """
        Feature 1: ADHD-optimized untracked work detection

        Tier 2 ADHD Intelligence Tool:
        - Detects uncommitted git work with no ConPort task
        - Multi-signal confidence scoring (git + ConPort + filesystem)
        - Adaptive thresholds (0.75 → 0.65 → 0.60 across sessions)
        - 30-minute grace period for exploratory work
        - Gentle encouragement: Track / Snooze / Ignore options
        - Non-blocking: never enforces, just increases awareness

        Args:
            session_number: Current session count (1, 2, 3+) for adaptive thresholds
            show_details: Show detailed confidence breakdown

        Returns:
            JSON with detection results and ADHD-friendly suggestions
        """
        start_time = datetime.now()

        try:
            # Import Feature 1 components
            from .untracked_work_detector import UntrackedWorkDetector
            from .untracked_work_storage import UntrackedWorkStorage

            # Initialize detector
            detector = UntrackedWorkDetector(
                workspace=self.workspace,
                workspace_id=str(self.workspace)
            )

            await self._ensure_conport_client()
            conport_client = self.conport_client

            # Run detection with ConPort when available (falls back safely when unavailable).
            detection = await detector.detect(
                conport_client=conport_client,
                session_number=session_number
            )

            # F1: Auto-track if confidence >= threshold
            auto_track_result = None
            if detection["has_untracked_work"]:
                storage = UntrackedWorkStorage(str(self.workspace))
                config = await storage.get_user_config(conport_client=conport_client)
                auto_track_threshold = config.get("auto_track_threshold", 0.85)

                # Try auto-track (will return None if below threshold)
                auto_track_result = await storage.auto_track_if_threshold_met(
                    detection=detection,
                    threshold=auto_track_threshold,
                    conport_client=conport_client
                )

                if auto_track_result:
                    logger.info(f"Auto-tracked work as task #{auto_track_result['task_id']}")

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Build ADHD-optimized output
            if not detection["has_untracked_work"]:
                result = {
                    "status": "all_clear",
                    "message": "✅ All work is tracked in ConPort or below threshold",
                    "confidence_score": detection["confidence_score"],
                    "threshold_used": detection["threshold_used"],
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2)
                    }
                }
            else:
                # Untracked work detected!
                git_stats = detection["git_detection"]["stats"]
                file_count = len(detection["git_detection"]["files"])

                # Build output based on show_details
                result = {
                    "status": "untracked_work_detected",
                    "work_name": detection["work_name"],
                    "confidence": {
                        "score": round(detection["confidence_score"], 2),
                        "threshold": detection["threshold_used"],
                        "passes_threshold": detection["passes_threshold"],
                        "session_number": session_number
                    },
                    "git_summary": {
                        "branch": detection["git_detection"]["branch"],
                        "is_feature_branch": detection["git_detection"]["is_feature_branch"],
                        "files_changed": file_count,
                        "stats": git_stats,
                        "common_directory": detection["git_detection"]["common_directory"]
                    },
                    "conport_status": {
                        "is_orphaned": detection["conport_matching"]["is_orphaned"],
                        "orphan_reason": detection["conport_matching"]["orphan_reason"],
                        "matched_tasks": len(detection["conport_matching"]["matched_tasks"])
                    },
                    "timing": {
                        "first_change_time": detection["detection_signals"]["timing"]["first_change_time"],
                        "past_grace_period": detection["grace_period_satisfied"]
                    },
                    "reminder": {
                        "should_show": detection["should_remind"],
                        "reason": detection["reminder_reason"]
                    },
                    "suggestions": {
                        "options": [
                            {
                                "action": "track",
                                "description": "Create ConPort task (pre-filled form)",
                                "recommended": True
                            },
                            {
                                "action": "snooze",
                                "description": "Remind later (1h | 4h | 1d)",
                                "recommended": False
                            },
                            {
                                "action": "ignore",
                                "description": "Mark as experiment (won't remind again)",
                                "recommended": False
                            }
                        ],
                        "adhd_guidance": "✨ Completing existing work builds momentum and reduces cognitive sprawl"
                    },
                    "auto_track": auto_track_result if auto_track_result else {
                        "enabled": True,
                        "threshold": config.get("auto_track_threshold", 0.85) if 'config' in locals() else 0.85,
                        "triggered": False,
                        "reason": f"Confidence {detection['confidence_score']:.2f} < threshold"
                    },
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2)
                    }
                }

                # Add details if requested
                if show_details:
                    result["details"] = {
                        "detection_signals": detection["detection_signals"],
                        "confidence_breakdown": detection["detection_signals"]["confidence"]["breakdown"],
                        "files": detection["git_detection"]["files"][:10]  # ADHD limit
                    }

            logger.info(f"detect_untracked_work: session={session_number} → {detection['has_untracked_work']} (confidence: {detection['confidence_score']:.2f}, {elapsed_ms:.1f}ms)")
            return json.dumps(result, indent=2)

        except ImportError as e:
            # Feature 1 components not available yet
            return json.dumps({
                "error": "Feature 1 components not fully integrated",
                "message": "untracked_work_detector.py requires git_detector.py and conport_matcher.py",
                "details": str(e)
            }, indent=2)
        except (OSError, RuntimeError) as e:
            logger.error(f"detect_untracked_work failed: {e}")
            return json.dumps({"error": str(e), "fallback": "Use git status manually"}, indent=2)
        except Exception:
            logger.exception("detect_untracked_work unexpected error")
            return json.dumps({"error": "unexpected error", "fallback": "manual investigation"}, indent=2)

    async def detect_untracked_work_enhanced_tool(
        self,
        session_number: int = 1,
        show_details: bool = False
    ) -> str:
        """
        Feature 1 Enhanced: Untracked work detection with E1-E4 enhancements

        Combines base F001 detection with 4 critical enhancements:
        - E1: False-starts dashboard (aggregate awareness)
        - E2: Design-first prompting (ADR/RFC suggestions)
        - E3: Abandoned work revival (finish vs. start new)
        - E4: Prioritization context (overcommitment prevention)

        ADHD Benefits:
        - Gentle awareness without shame
        - Decision support for "Is this urgent?"
        - Revival of forgotten work
        - Design-first to reduce false-starts

        Args:
            session_number: Session count (1, 2, 3+) for adaptive thresholds
            show_details: Include detailed confidence breakdown

        Returns:
            JSON with detection + all relevant enhancements
        """
        start_time = datetime.now()

        try:
            # Import Feature 1 enhanced components
            from .untracked_work_detector import UntrackedWorkDetector

            # Initialize detector (includes E1-E4)
            detector = UntrackedWorkDetector(
                workspace=self.workspace,
                workspace_id=str(self.workspace)
            )

            # Ensure ConPort client connected
            await self._ensure_conport_client()

            # Run enhanced detection with ConPort integration
            detection = await detector.detect_with_enhancements(
                conport_client=self.conport_client,
                session_number=session_number
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Build ADHD-optimized output
            if not detection["has_untracked_work"]:
                result = {
                    "status": "all_clear",
                    "message": "✅ All work is tracked or below threshold",
                    "confidence_score": detection["confidence_score"],
                    "threshold_used": detection["threshold_used"],
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2)
                    }
                }
            else:
                # Untracked work detected - show enhancements!
                enhancements = detection["enhancements"]

                result = {
                    "status": "untracked_work_detected",
                    "message": f"⚠️  Untracked work: {detection['work_name']}",
                    "work_summary": {
                        "name": detection["work_name"],
                        "confidence": detection["confidence_score"],
                        "threshold": detection["threshold_used"],
                        "files_changed": len(detection["git_detection"]["files"]),
                        "branch": detection["git_detection"].get("branch")
                    }
                }

                # E1: False-starts dashboard (always shown)
                if enhancements.get("false_starts"):
                    result["false_starts_dashboard"] = {
                        "total_unfinished": enhancements["false_starts"]["summary"]["total_unfinished"],
                        "status_breakdown": enhancements["false_starts"]["summary"]["status_breakdown"],
                        "message": enhancements["false_starts"]["dashboard_message"]
                    }

                # E2: Design-first prompting (conditional)
                if enhancements.get("design_first"):
                    result["design_first_recommendation"] = {
                        "should_create_design": True,
                        "confidence": enhancements["design_first"]["detection"]["confidence"],
                        "document_type": enhancements["design_first"]["detection"]["suggested_document_type"],
                        "reasons": enhancements["design_first"]["detection"]["reasons"],
                        "message": enhancements["design_first"]["prompt_message"]
                    }

                # E3: Abandoned work revival (conditional)
                if enhancements.get("revival"):
                    result["revival_suggestions"] = {
                        "count": enhancements["revival"]["suggestions"]["suggestion_count"],
                        "suggestions": enhancements["revival"]["suggestions"]["suggestions"],
                        "message": enhancements["revival"]["revival_message"]
                    }

                # E4: Prioritization context (conditional)
                if enhancements.get("priority"):
                    result["prioritization_context"] = {
                        "active_tasks": enhancements["priority"]["context"]["total_active"],
                        "in_progress": enhancements["priority"]["context"]["in_progress_count"],
                        "overcommitment_risk": enhancements["priority"]["context"]["overcommitment_risk"],
                        "recommendation": enhancements["priority"]["context"]["urgent_recommendation"],
                        "message": enhancements["priority"]["priority_message"]
                    }

                # Actions (same as base F001)
                result["suggested_actions"] = {
                    "options": [
                        {
                            "action": "track",
                            "description": "Create ConPort task (pre-filled)",
                            "recommended": True
                        },
                        {
                            "action": "design_first",
                            "description": "Create ADR/RFC first" if enhancements.get("design_first") else None,
                            "recommended": bool(enhancements.get("design_first"))
                        },
                        {
                            "action": "resume_abandoned",
                            "description": "Resume abandoned work instead" if enhancements.get("revival") else None,
                            "recommended": bool(enhancements.get("revival"))
                        },
                        {
                            "action": "snooze",
                            "description": "Remind later (1h | 4h | 1d)",
                            "recommended": False
                        },
                        {
                            "action": "ignore",
                            "description": "Mark as experiment (won't remind)",
                            "recommended": False
                        }
                    ],
                    "adhd_guidance": "✨ The most productive choice isn't always starting new work"
                }

                # Add details if requested
                if show_details:
                    result["details"] = {
                        "detection_signals": detection["detection_signals"],
                        "pattern_boost": detection.get("pattern_boost_details"),
                        "abandonment_data": detection.get("abandonment_data"),
                        "files": detection["git_detection"]["files"][:10]  # ADHD limit
                    }

                result["performance"] = {
                    "latency_ms": round(elapsed_ms, 2)
                }

            logger.info(
                f"detect_untracked_work_enhanced: session={session_number} → "
                f"{detection['has_untracked_work']} (confidence: {detection['confidence_score']:.2f}, "
                f"enhancements: E1={bool(enhancements.get('false_starts'))}, "
                f"E2={bool(enhancements.get('design_first'))}, "
                f"E3={bool(enhancements.get('revival'))}, "
                f"E4={bool(enhancements.get('priority'))}, "
                f"{elapsed_ms:.1f}ms)"
            )
            return json.dumps(result, indent=2)

        except ImportError as e:
            # Feature 1 enhanced components not available
            return json.dumps({
                "error": "F001 Enhanced components not fully integrated",
                "message": "Missing enhancement modules (E1-E4)",
                "details": str(e),
                "fallback": "Use detect_untracked_work_tool instead"
            }, indent=2)
        except ImportError as e:
            logger.error(f"detect_untracked_work_enhanced missing dependency: {e}")
            return json.dumps({"error": str(e), "fallback": "Install enhancement modules"}, indent=2)
        except (OSError, RuntimeError) as e:
            logger.error(f"detect_untracked_work_enhanced failed: {e}")
            return json.dumps({"error": str(e), "fallback": "Use base detect_untracked_work_tool"}, indent=2)
        except Exception:
            logger.exception("detect_untracked_work_enhanced unexpected error")
            return json.dumps({"error": "unexpected error", "fallback": "manual investigation"}, indent=2)

    async def initialize_session_tool(
        self,
        initial_focus: str = None,
        transcript_path: str = None
    ) -> str:
        """
        F002: Initialize new session with worktree detection and ConPort tracking

        Creates unique session ID, detects worktree info, and starts session lifecycle.
        All sessions for same workspace (including worktrees) share knowledge graph.

        ADHD Benefits:
        - Automatic context preservation across sessions
        - Parallel work without mental context-switching
        - Session isolation (own focus) + knowledge sharing (unified graph)

        Args:
            initial_focus: Initial session focus description
            transcript_path: Optional Claude Code transcript path for ID generation

        Returns:
            JSON with session info and worktree details
        """
        start_time = datetime.now()

        try:
            from session_manager import SessionManager

            # Initialize session manager with auto-detection
            manager = SessionManager(
                workspace_path=self.workspace,
                auto_detect=True
            )

            # Ensure ConPort client connected
            await self._ensure_conport_client()

            # Start session with ConPort integration
            session_state = await manager.initialize_session(
                initial_focus=initial_focus,
                conport_client=self.conport_client,
                transcript_path=transcript_path
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "session_initialized",
                "session": {
                    "session_id": session_state.session_id,
                    "workspace_id": session_state.workspace_id,
                    "worktree_path": session_state.worktree_path,
                    "branch": session_state.branch,
                    "current_focus": session_state.current_focus,
                    "session_start": session_state.session_start.isoformat()
                },
                "worktree_info": manager.get_worktree_info().to_dict(),
                "message": f"✅ Session {session_state.session_id[:20]}... started",
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                }
            }

            logger.info(f"initialize_session: {session_state.session_id} ({elapsed_ms:.1f}ms)")
            return json.dumps(result, indent=2)

        except (ValueError, FileNotFoundError) as e:
            logger.error(f"initialize_session validation failed: {e}")
            return json.dumps({"error": str(e), "fallback": "Check parameters"}, indent=2)
        except (OSError, RuntimeError) as e:
            logger.error(f"initialize_session failed: {e}")
            return json.dumps({"error": str(e), "fallback": "Continue without multi-session support"}, indent=2)
        except Exception:
            logger.exception("initialize_session unexpected error")
            return json.dumps({"error": "unexpected error"}, indent=2)

    async def get_multi_session_dashboard_tool(self) -> str:
        """
        F002: Get multi-session startup dashboard

        Shows all active sessions across worktrees with time anchors.
        ADHD-optimized: grouped by worktree, max 10 sessions, clear summary.

        Returns:
            JSON with formatted dashboard and session statistics

        Example Dashboard:
            🔄 ACTIVE SESSIONS

            Main worktree (main):
               • [active] Code review

            Worktree: feature-auth (feature/auth):
               • [30m ago] JWT implementation

            Total: 2 active session(s), 1 worktree(s)
        """
        start_time = datetime.now()

        try:
            from session_manager import SessionManager

            manager = SessionManager(workspace_path=self.workspace, auto_detect=True)

            # Ensure ConPort client connected
            await self._ensure_conport_client()

            # Get dashboard with ConPort integration
            dashboard_text = await manager.get_startup_dashboard(conport_client=self.conport_client)

            # Get statistics
            stats = await manager.lifecycle_manager.get_session_statistics(conport_client=self.conport_client)

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "dashboard_ready",
                "dashboard": dashboard_text,
                "statistics": stats,
                "worktree_info": manager.get_worktree_info().to_dict() if manager.get_worktree_info() else None,
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                }
            }

            logger.info(f"get_multi_session_dashboard: {stats.get('active_sessions', 0)} sessions ({elapsed_ms:.1f}ms)")
            return json.dumps(result, indent=2)

        except (OSError, RuntimeError) as e:
            logger.error(f"get_multi_session_dashboard failed: {e}")
            return json.dumps({"error": str(e), "fallback": "Check session manager"}, indent=2)
        except Exception:
            logger.exception("get_multi_session_dashboard unexpected error")
            return json.dumps({"error": "unexpected error", "fallback": "Retry later"}, indent=2)

    async def get_session_info_tool(self) -> str:
        """
        F002: Get current session information

        Returns details about the current session including worktree,
        branch, focus, and duration.

        Returns:
            JSON with current session details
        """
        start_time = datetime.now()

        try:
            from session_manager import SessionManager

            manager = SessionManager(workspace_path=self.workspace, auto_detect=True)

            # Get current session info
            session_info = manager.get_current_session_info()
            worktree_info = manager.get_worktree_info()

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            if session_info:
                result = {
                    "status": "session_active",
                    "session": session_info,
                    "worktree": worktree_info.to_dict() if worktree_info else None,
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2)
                    }
                }
            else:
                result = {
                    "status": "no_session",
                    "message": "No session initialized - call initialize_session first",
                    "worktree": worktree_info.to_dict() if worktree_info else None,
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2)
                    }
                }

            logger.info(f"get_session_info: {session_info is not None} ({elapsed_ms:.1f}ms)")
            return json.dumps(result, indent=2)

        except (OSError, RuntimeError) as e:
            logger.error(f"get_session_info failed: {e}")
            return json.dumps({"error": str(e)}, indent=2)
        except Exception:
            logger.exception("get_session_info unexpected error")
            return json.dumps({"error": "unexpected error"}, indent=2)

    async def suggest_branch_organization_tool(
        self,
        min_cluster_size: int = 2
    ) -> str:
        """
        F4: Auto-Branch Suggestions - Help organize scattered work

        Analyzes uncommitted files to detect multiple logical work clusters.
        Suggests creating separate branches for better organization.

        ADHD Benefits:
        - Prevents cognitive overload from mixed contexts
        - Encourages single-responsibility work sessions
        - Reduces "20 files across 5 features" overwhelm

        Args:
            min_cluster_size: Minimum files per cluster (default 2)

        Returns:
            JSON with branch organization suggestions
        """
        start_time = datetime.now()

        try:
            from git_detector import GitWorkDetector

            detector = GitWorkDetector(self.workspace)

            # Get uncommitted work
            git_detection = await detector.detect_uncommitted_work()

            if not git_detection.get("has_uncommitted"):
                elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
                return json.dumps({
                    "status": "no_uncommitted_work",
                    "message": "✅ No uncommitted files detected",
                    "suggestion": None,
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2)
                    }
                }, indent=2)

            # Get branch organization suggestions
            suggestion = await detector.suggest_branch_organization(
                detection=git_detection,
                min_cluster_size=min_cluster_size
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Format result
            if not suggestion["should_split"]:
                result = {
                    "status": "no_split_needed",
                    "message": "👍 Work is focused - no need to split branches",
                    "current_branch": suggestion["current_branch"],
                    "file_count": len(git_detection["files"]),
                    "reason": suggestion["reason"],
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2)
                    }
                }
            else:
                # Build ADHD-optimized suggestion output
                result = {
                    "status": "split_recommended",
                    "message": f"💡 Detected {len(suggestion['clusters'])} logical work areas",
                    "suggestion": suggestion["suggestion"],
                    "clusters": [
                        {
                            "branch_name": cluster["name"],
                            "file_count": cluster["size"],
                            "directory": cluster["directory"],
                            "sample_files": cluster["files"][:3]  # ADHD limit: show first 3
                        }
                        for cluster in suggestion["clusters"]
                    ],
                    "benefits": [
                        "✓ Clearer commit history per feature",
                        "✓ Easier code review (focused changes)",
                        "✓ Reduced context switching",
                        "✓ Better git blame tracking"
                    ],
                    "next_steps": [
                        f"1. git checkout -b {suggestion['clusters'][0]['name']}",
                        f"2. git stash push -- {' '.join(suggestion['clusters'][1]['files'][:3])}...",
                        "3. Commit work on current branch",
                        f"4. git checkout -b {suggestion['clusters'][1]['name']}",
                        "5. git stash pop and commit"
                    ] if len(suggestion['clusters']) >= 2 else [],
                    "adhd_guidance": "🧠 Focused branches = focused mind. One context at a time prevents overwhelm.",
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2)
                    }
                }

            logger.info(f"suggest_branch_organization: {len(suggestion['clusters'])} clusters, should_split={suggestion['should_split']}, {elapsed_ms:.1f}ms")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"suggest_branch_organization failed: {e}", exc_info=True)
            return json.dumps({
                "error": str(e),
                "fallback": "Use git status and manually organize changes"
            }, indent=2)

    async def get_pattern_stats_tool(self) -> str:
        """
        F5: Pattern Learning Stats - Get pattern learning statistics

        Returns cache performance and pattern learning metrics:
        - Cache hit rate and utilization
        - Total patterns learned
        - Pattern categories (file_extension, directory, branch_prefix)
        - Most frequent patterns

        ADHD Benefits:
        - Quick overview of learning system health
        - Understand which patterns are most common
        - Validate pattern system is working

        Returns:
            JSON with pattern statistics
        """
        start_time = datetime.now()

        try:
            from .untracked_work_detector import UntrackedWorkDetector

            detector = UntrackedWorkDetector(self.workspace, str(self.workspace))

            # Get cache stats
            cache_stats = detector.pattern_learner.get_cache_stats()

            # Get top patterns by category
            top_file_extensions = await detector.pattern_learner.get_top_patterns(
                "file_extension",
                limit=5
            )

            top_directories = await detector.pattern_learner.get_top_patterns(
                "directory",
                limit=5
            )

            top_branch_prefixes = await detector.pattern_learner.get_top_patterns(
                "branch_prefix",
                limit=5
            )

            # Calculate latency
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "success",
                "cache_performance": {
                    "size": cache_stats["size"],
                    "max_size": cache_stats["max_size"],
                    "utilization": f"{cache_stats['utilization']:.1%}",
                    "total_accesses": cache_stats["total_accesses"],
                    "avg_accesses_per_pattern": round(cache_stats["avg_accesses_per_pattern"], 2)
                },
                "pattern_counts": {
                    "file_extensions": len(top_file_extensions),
                    "directories": len(top_directories),
                    "branch_prefixes": len(top_branch_prefixes)
                },
                "top_patterns": {
                    "file_extensions": top_file_extensions[:3],
                    "directories": top_directories[:3],
                    "branch_prefixes": top_branch_prefixes[:3]
                },
                "performance": {
                    "latency_ms": round(elapsed_ms, 2),
                    "target": "< 1000ms (ADHD)"
                },
                "adhd_guidance": "📊 Pattern learning active - detection improves over time!"
            }

            logger.info(f"get_pattern_stats: cache_size={cache_stats['size']}, {elapsed_ms:.1f}ms")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"get_pattern_stats failed: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, indent=2)

    async def get_top_patterns_tool(
        self,
        pattern_type: str = "file_extension",
        limit: int = 10,
        min_probability: float = 0.1
    ) -> str:
        """
        F5: Get Top Patterns - Retrieve most frequent learned patterns

        Query pattern learning database for top patterns by category.

        Args:
            pattern_type: Type of pattern (file_extension, directory, branch_prefix)
            limit: Max patterns to return (default 10, ADHD limit)
            min_probability: Minimum probability threshold (default 0.1)

        ADHD Benefits:
        - Max 10 results (no overwhelm)
        - Probability scores show pattern strength
        - Focus on high-confidence patterns

        Returns:
            JSON with top patterns sorted by probability
        """
        start_time = datetime.now()

        try:
            from .untracked_work_detector import UntrackedWorkDetector

            detector = UntrackedWorkDetector(self.workspace, str(self.workspace))

            # Get top patterns
            patterns = await detector.pattern_learner.get_top_patterns(
                pattern_type,
                limit=limit,
                min_probability=min_probability
            )

            # Calculate latency
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "success",
                "pattern_type": pattern_type,
                "limit": limit,
                "min_probability": min_probability,
                "patterns_found": len(patterns),
                "patterns": patterns,
                "performance": {
                    "latency_ms": round(elapsed_ms, 2),
                    "target": "< 1000ms (ADHD)"
                },
                "adhd_guidance": f"🎯 Found {len(patterns)} '{pattern_type}' patterns. Higher probability = stronger pattern."
            }

            logger.info(f"get_top_patterns: type={pattern_type}, found={len(patterns)}, {elapsed_ms:.1f}ms")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"get_top_patterns failed: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, indent=2)

    async def get_abandoned_work_tool(
        self,
        min_days_idle: int = 7,
        min_score: float = 0.5,
        limit: int = 10
    ) -> str:
        """
        F6: Get Abandoned Work - List uncommitted work that's been idle

        Detects work sitting uncommitted for extended periods.
        Default: 7+ days idle with abandonment score >= 0.5

        Args:
            min_days_idle: Minimum days idle (default 7)
            min_score: Minimum abandonment score (default 0.5)
            limit: Max results (default 10, ADHD limit)

        ADHD Benefits:
        - Gentle reminders for forgotten work
        - Max 10 results (no overwhelm)
        - Suggested actions (commit/archive/delete)
        - GUILT-FREE messaging

        Returns:
            JSON with abandoned work items
        """
        start_time = datetime.now()

        try:
            from .untracked_work_detector import UntrackedWorkDetector

            detector = UntrackedWorkDetector(self.workspace, str(self.workspace))

            # Detect all uncommitted work
            git_detection = await detector.git_detector.detect_uncommitted_work()

            if not git_detection.get("has_uncommitted"):
                return json.dumps({
                    "status": "no_uncommitted_work",
                    "message": "✅ No uncommitted work detected",
                    "abandoned_items": []
                }, indent=2)

            # Calculate abandonment for current work
            abandonment_data = detector.abandonment_tracker.calculate_abandonment_score(git_detection)

            # Filter by criteria
            abandoned_items = []
            if (abandonment_data["days_idle"] >= min_days_idle and
                abandonment_data["score"] >= min_score):

                # Generate work name
                work_name = await detector.git_detector.generate_work_name(git_detection)

                # Get action suggestion
                action_suggestion = detector.abandonment_tracker.suggest_action(
                    abandonment_data,
                    git_detection
                )

                abandoned_items.append({
                    "work_name": work_name,
                    "days_idle": abandonment_data["days_idle"],
                    "abandonment_score": abandonment_data["score"],
                    "severity": abandonment_data["severity"],
                    "message": abandonment_data["message"],
                    "files_changed": len(git_detection.get("files", [])),
                    "suggested_action": action_suggestion["action"],
                    "action_rationale": action_suggestion["rationale"],
                    "urgency": action_suggestion["urgency"]
                })

            # Apply limit
            abandoned_items = abandoned_items[:limit]

            # Calculate latency
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "success",
                "filters": {
                    "min_days_idle": min_days_idle,
                    "min_score": min_score,
                    "limit": limit
                },
                "abandoned_count": len(abandoned_items),
                "abandoned_items": abandoned_items,
                "performance": {
                    "latency_ms": round(elapsed_ms, 2),
                    "target": "< 1000ms (ADHD)"
                },
                "adhd_guidance": "🧹 Old work found - time to wrap up, stash, or delete. No guilt, just clarity!"
            }

            logger.info(f"get_abandoned_work: found={len(abandoned_items)}, {elapsed_ms:.1f}ms")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"get_abandoned_work failed: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, indent=2)

    async def mark_abandoned_tool(
        self,
        work_name: str,
        action_taken: str
    ) -> str:
        """
        F6: Mark Abandoned - Record action taken on abandoned work

        Records user's action for F5 pattern learning:
        - "commit": Work completed (pattern is safe)
        - "delete": Work discarded (pattern may be risky)
        - "archive": Work stashed (pattern experimental)

        Args:
            work_name: Name of work from get_abandoned_work
            action_taken: "commit", "delete", or "archive"

        ADHD Benefits:
        - Tracks completion vs abandonment patterns
        - Learns which patterns lead to abandoned work
        - Improves future detection accuracy

        Returns:
            JSON with confirmation and pattern learning status
        """
        start_time = datetime.now()

        try:
            # Validate action
            valid_actions = ["commit", "delete", "archive"]
            if action_taken not in valid_actions:
                return json.dumps({
                    "error": f"Invalid action '{action_taken}'. Must be one of: {valid_actions}"
                }, indent=2)

            # Record action (in future, store in ConPort custom_data: abandonment_actions)
            logger.info(f"mark_abandoned: work='{work_name}', action={action_taken}")

            # Calculate latency
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Generate feedback based on action
            feedback_messages = {
                "commit": "🎉 Great! Completing old work builds momentum.",
                "delete": "🗑️ Clean slate! Removing clutter helps focus.",
                "archive": "📦 Stashed for later - smart move to reduce cognitive load."
            }

            result = {
                "status": "success",
                "work_name": work_name,
                "action_taken": action_taken,
                "message": feedback_messages[action_taken],
                "pattern_learning": {
                    "status": "recorded",
                    "note": "Future: Feed to F5 pattern learning to detect risky patterns"
                },
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                }
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"mark_abandoned failed: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, indent=2)

    async def get_abandonment_stats_tool(self) -> str:
        """
        F6: Abandonment Stats - Get abandonment statistics

        Returns analytics on abandoned work patterns:
        - Total abandoned items
        - Average days idle
        - Abandonment by severity
        - Most abandoned patterns (file types, directories)

        ADHD Benefits:
        - Understand personal work patterns
        - Identify abandonment triggers
        - Learn which work types get forgotten

        Returns:
            JSON with abandonment statistics
        """
        start_time = datetime.now()

        try:
            from .untracked_work_detector import UntrackedWorkDetector

            detector = UntrackedWorkDetector(self.workspace, str(self.workspace))

            # Detect current work (in full implementation, query all detections from ConPort)
            git_detection = await detector.git_detector.detect_uncommitted_work()

            abandoned_summary = {
                "total_abandoned": 0,
                "by_severity": {},
                "avg_days_idle": 0.0,
                "oldest_work": None
            }

            if git_detection.get("has_uncommitted"):
                abandonment_data = detector.abandonment_tracker.calculate_abandonment_score(git_detection)

                if abandonment_data["is_abandoned"]:
                    work_name = await detector.git_detector.generate_work_name(git_detection)

                    abandoned_summary = {
                        "total_abandoned": 1,
                        "by_severity": {
                            abandonment_data["severity"]: 1
                        },
                        "avg_days_idle": abandonment_data["days_idle"],
                        "oldest_work": {
                            "work_name": work_name,
                            "days_idle": abandonment_data["days_idle"]
                        }
                    }

            # Calculate latency
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "success",
                "summary": abandoned_summary,
                "performance": {
                    "latency_ms": round(elapsed_ms, 2),
                    "target": "< 1000ms (ADHD)"
                },
                "adhd_guidance": "📊 Track patterns to understand what work gets forgotten - no judgment, just awareness!",
                "note": "Full implementation will query all detections from ConPort for comprehensive stats"
            }

            logger.info(f"get_abandonment_stats: total={abandoned_summary['total_abandoned']}, {elapsed_ms:.1f}ms")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"get_abandonment_stats failed: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, indent=2)

    async def get_metrics_dashboard_tool(
        self,
        days: int = 7,
        level: int = 1,
        include_trends: bool = False
    ) -> str:
        """
        F7: Get Metrics Dashboard - Analytics dashboard with progressive disclosure

        Aggregates F1-F6 metrics into ADHD-optimized dashboard:
        - Level 1: At-a-glance summary (detection count, confidence, abandonments)
        - Level 2: Feature breakdown (F1-F6 separate sections)
        - Level 3: Time-series trends (requires historical data)

        Args:
            days: Time window for aggregation (default: 7)
            level: Disclosure level (1=summary, 2=breakdown, 3=trends)
            include_trends: Show trend arrows

        ADHD Benefits:
        - Progressive disclosure prevents overwhelm
        - Visual indicators (✅📈↑) enable quick scanning
        - Max 5 items per section (working memory limit)

        Returns:
            Formatted dashboard string with metrics
        """
        start_time = datetime.now()

        try:
            from .metrics_dashboard import MetricsDashboard
            from .untracked_work_detector import UntrackedWorkDetector

            dashboard = MetricsDashboard(workspace_id=str(self.workspace))
            detector = UntrackedWorkDetector(self.workspace, str(self.workspace))

            # For now, detect current work (in full implementation, query all from ConPort)
            git_detection = await detector.git_detector.detect_uncommitted_work()

            # Create detection result
            detection_results = []
            if git_detection.get("has_uncommitted"):
                detection = await detector.detect(session_number=2)
                detection_results.append(detection)

            # Generate dashboard
            summary = dashboard.generate_summary(
                detection_results,
                level=level,
                include_trends=include_trends
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "success",
                "dashboard": summary,
                "metadata": {
                    "days": days,
                    "level": level,
                    "detections_analyzed": len(detection_results),
                    "performance": {
                        "latency_ms": round(elapsed_ms, 2),
                        "target": "< 1000ms (ADHD)"
                    }
                },
                "adhd_guidance": f"📊 Level {level}/3 disclosure - request level 2 for details, level 3 for trends",
                "note": "Full implementation will aggregate all detections from ConPort history"
            }

            logger.info(f"get_metrics_dashboard: level={level}, {len(detection_results)} detections, {elapsed_ms:.1f}ms")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"get_metrics_dashboard failed: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, indent=2)

    async def get_metric_history_tool(
        self,
        metric_name: str,
        days: int = 30,
        granularity: str = "daily"
    ) -> str:
        """
        F7: Get Metric History - Time-series data for specific metric

        Retrieves historical trend data:
        - Confidence scores over time
        - Pattern boost rates
        - Abandonment rates
        - Detection pass rates

        Args:
            metric_name: "confidence", "pattern_boost", "abandonment_rate", "pass_rate"
            days: Historical window (default: 30)
            granularity: "daily" or "weekly"

        ADHD Benefits:
        - Visualize progress over time
        - Identify improvement trends
        - Celebrate growth patterns

        Returns:
            JSON with time-series data
        """
        start_time = datetime.now()

        try:
            valid_metrics = {"confidence", "pattern_boost", "abandonment_rate", "pass_rate"}
            if metric_name not in valid_metrics:
                return json.dumps(
                    {
                        "error": f"metric_name must be one of: {sorted(valid_metrics)}"
                    },
                    indent=2,
                )
            if granularity not in {"daily", "weekly"}:
                return json.dumps({"error": "granularity must be 'daily' or 'weekly'"}, indent=2)

            await self._ensure_conport_client()
            if not self.conport_client:
                return json.dumps(
                    {
                        "status": "unavailable",
                        "metric_name": metric_name,
                        "message": "ConPort client unavailable; no historical metrics found",
                    },
                    indent=2,
                )

            rows = await self.conport_client.get_custom_data(
                workspace_id=str(self.workspace),
                category="metrics_history",
            )
            cutoff = datetime.now() - timedelta(days=max(days, 1))
            points = []
            for row in rows:
                value = row.get("value", {})
                timestamp = self._extract_metric_timestamp(value, row.get("key"))
                if timestamp is None or timestamp < cutoff:
                    continue
                metric_value = self._extract_metric_value(value, metric_name)
                if metric_value is None:
                    continue
                points.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "value": round(metric_value, 4),
                    }
                )

            points.sort(key=lambda item: item["timestamp"])
            if granularity == "weekly":
                points = self._aggregate_metric_points(points, period="weekly")

            trend = None
            if len(points) >= 2:
                delta = round(points[-1]["value"] - points[0]["value"], 4)
                trend = {
                    "direction": "up" if delta > 0 else "down" if delta < 0 else "flat",
                    "delta": delta,
                }

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "success",
                "metric_name": metric_name,
                "days": days,
                "granularity": granularity,
                "points": points,
                "count": len(points),
                "trend": trend,
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                }
            }

            logger.info(f"get_metric_history: {metric_name}, {days}d, {granularity}")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"get_metric_history failed: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, indent=2)

    async def save_metrics_snapshot_tool(self) -> str:
        """
        F7: Save Metrics Snapshot - Internal tool for historical tracking

        Saves daily metrics snapshot to ConPort:
        - Aggregates current detection stats
        - Stores in metrics_history category
        - Enables trend analysis

        Called automatically after detections.
        90-day retention policy.

        ADHD Benefits:
        - Automatic tracking (no manual effort)
        - Build progress history passively
        - Enable retrospective analysis

        Returns:
            JSON with save status
        """
        start_time = datetime.now()

        try:
            from .metrics_dashboard import MetricsDashboard
            from .untracked_work_detector import UntrackedWorkDetector

            dashboard = MetricsDashboard(workspace_id=str(self.workspace))
            detector = UntrackedWorkDetector(self.workspace, str(self.workspace))

            await self._ensure_conport_client()
            if not self.conport_client:
                return json.dumps(
                    {
                        "status": "unavailable",
                        "message": "ConPort client unavailable; snapshot not saved",
                    },
                    indent=2,
                )

            detection_results = []
            git_detection = await detector.git_detector.detect_uncommitted_work()
            if git_detection.get("has_uncommitted"):
                detection = await detector.detect(
                    conport_client=self.conport_client,
                    session_number=2,
                )
                detection_results.append(detection)

            metrics = dashboard.aggregator.aggregate_detections(detection_results)
            f1_f4 = metrics.get("f1_f4_metrics", {})
            f5 = metrics.get("f5_metrics", {})
            f6 = metrics.get("f6_metrics", {})
            total = max(1, int(f1_f4.get("total_detections", 0)))

            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "confidence": float(f1_f4.get("avg_confidence", 0.0)),
                    "pattern_boost": float(f5.get("avg_boost", 0.0)),
                    "abandonment_rate": float(f6.get("total_abandoned", 0)) / total,
                    "pass_rate": float(f1_f4.get("pass_rate", 0.0)),
                    "total_detections": int(f1_f4.get("total_detections", 0)),
                    "total_abandoned": int(f6.get("total_abandoned", 0)),
                },
                "raw": metrics,
            }

            key = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            saved = await self.conport_client.log_custom_data(
                workspace_id=str(self.workspace),
                category="metrics_history",
                key=key,
                value=snapshot,
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
            result = {
                "status": "saved" if saved else "save_failed",
                "key": key,
                "snapshot": snapshot["metrics"],
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                }
            }

            logger.info(f"save_metrics_snapshot: {elapsed_ms:.1f}ms")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"save_metrics_snapshot failed: {e}", exc_info=True)
            return json.dumps({"error": str(e)}, indent=2)

    async def track_untracked_work_tool(
        self,
        work_name: str,
        custom_description: Optional[str] = None,
        complexity: Optional[float] = None
    ) -> str:
        """
        Feature 1 Action: Create ConPort task from untracked work

        Creates a ConPort progress_entry from detected work:
        - Auto-generates description from work_name
        - Estimates complexity from git stats (or uses provided)
        - Links to untracked_work record
        - Status: detected → converted_to_task

        Args:
            work_name: Work name from detection
            custom_description: Optional custom description
            complexity: Optional complexity override (0.0-1.0)

        Returns:
            JSON with created task info
        """
        start_time = datetime.now()

        try:
            description = custom_description if custom_description else work_name

            # Estimate complexity if not provided
            if complexity is None:
                complexity = 0.5  # Default medium
            complexity = max(0.0, min(1.0, float(complexity)))

            await self._ensure_conport_client()
            if not self.conport_client:
                return json.dumps(
                    {
                        "status": "unavailable",
                        "message": "ConPort client unavailable; task was not created",
                        "task_data": {
                            "status": "IN_PROGRESS",
                            "description": description,
                            "metadata": {"complexity": complexity, "work_name": work_name},
                        },
                    },
                    indent=2,
                )

            # Build ConPort task suggestion
            task_data = {
                "status": "IN_PROGRESS",
                "description": description,
                "metadata": {
                    "source": "untracked_work_detection",
                    "work_name": work_name,
                    "detected_via": "serena_feature_1",
                    "created_at": datetime.now().isoformat(),
                    "auto_generated": True,
                    "complexity": complexity
                }
            }

            entry = await self.conport_client.log_progress(
                workspace_id=str(self.workspace),
                status=task_data["status"],
                description=task_data["description"],
            )
            task_id = entry.get("id")
            if task_id is not None:
                await self.conport_client.log_custom_data(
                    workspace_id=str(self.workspace),
                    category="untracked_work_links",
                    key=f"task_{task_id}",
                    value=task_data["metadata"],
                )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "task_created",
                "message": f"✅ Created ConPort task: '{description}'",
                "task_id": task_id,
                "task_data": task_data,
                "next_steps": [
                    "Task is now tracked in ConPort",
                    "View with: mcp__conport__get_progress",
                    "Update status when complete"
                ],
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                }
            }

            logger.info(f"track_untracked_work: '{work_name}' → task created")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"track_untracked_work failed: {e}", exc_info=True)
            return json.dumps({
                "error": str(e)
            }, indent=2)

    async def snooze_untracked_work_tool(
        self,
        work_id: str,
        duration: str = "medium"
    ) -> str:
        """
        Feature 1 Action: Snooze untracked work reminder

        Delays reminder for specified duration:
        - short: 1 hour
        - medium: 4 hours (default)
        - long: 1 day

        Status: * → snoozed
        Sets snooze_until timestamp

        Args:
            work_id: Untracked work UUID
            duration: short, medium, or long

        Returns:
            JSON with snooze confirmation
        """
        start_time = datetime.now()

        # Duration mapping (from Feature 1 spec)
        durations = {
            "short": 3600,      # 1 hour
            "medium": 14400,    # 4 hours
            "long": 86400       # 1 day
        }

        duration_seconds = durations.get(duration, 14400)
        snooze_until = datetime.now() + timedelta(seconds=duration_seconds)

        # Human-readable duration
        duration_names = {
            "short": "1 hour",
            "medium": "4 hours",
            "long": "1 day"
        }
        duration_text = duration_names.get(duration, "4 hours")

        try:
            from .untracked_work_storage import UntrackedWorkStorage

            await self._ensure_conport_client()
            storage = UntrackedWorkStorage(str(self.workspace))
            persisted = await storage.snooze_work(
                work_id=work_id,
                duration_seconds=duration_seconds,
                conport_client=self.conport_client,
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "snoozed" if persisted else "not_found",
                "message": (
                    f"⏸️ Snoozed for {duration_text}"
                    if persisted
                    else "No matching untracked work record found to snooze"
                ),
                "work_id": work_id,
                "snooze_until": snooze_until.isoformat(),
                "duration_seconds": duration_seconds,
                "next_reminder": f"Will remind at {snooze_until.strftime('%H:%M on %b %d')}",
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                },
                "persisted_to_conport": bool(persisted)
            }

            logger.info(f"snooze_untracked_work: {work_id} → {duration_text}")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"snooze_untracked_work failed: {e}", exc_info=True)
            return json.dumps({
                "error": str(e)
            }, indent=2)

    async def ignore_untracked_work_tool(
        self,
        work_id: str,
        reason: Optional[str] = None
    ) -> str:
        """
        Feature 1 Action: Mark work as abandoned

        Status: * → abandoned
        Won't remind again
        Useful for: experiments, exploratory work, false positives

        Args:
            work_id: Untracked work UUID
            reason: Optional reason for abandoning

        Returns:
            JSON with abandonment confirmation
        """
        start_time = datetime.now()

        try:
            from .untracked_work_storage import UntrackedWorkStorage

            await self._ensure_conport_client()
            storage = UntrackedWorkStorage(str(self.workspace))
            persisted = await storage.abandon_work(
                work_id=work_id,
                conport_client=self.conport_client,
            )

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "abandoned" if persisted else "not_found",
                "message": (
                    "✅ Marked as abandoned - won't remind again"
                    if persisted
                    else "No matching untracked work record found to abandon"
                ),
                "work_id": work_id,
                "reason": reason if reason else "user_choice",
                "abandoned_at": datetime.now().isoformat(),
                "next_steps": [
                    "Work is marked as experiment/abandoned",
                    "Won't appear in future reminders",
                    "Can manually unignore in ConPort if needed"
                ],
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                },
                "persisted_to_conport": bool(persisted)
            }

            logger.info(f"ignore_untracked_work: {work_id} → abandoned ({reason})")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"ignore_untracked_work failed: {e}", exc_info=True)
            return json.dumps({
                "error": str(e)
            }, indent=2)

    async def get_untracked_work_config_tool(self) -> str:
        """
        Feature 1 Config: Get user configuration

        Returns current settings:
        - enabled: bool
        - confidence_threshold: 0.0-1.0
        - grace_period_minutes: int
        - quiet_hours: {enabled, start, end}
        - snooze_durations: {short, medium, long}
        - max_reminded_count: int
        - auto_abandon_after_days: int

        Returns:
            JSON with current config (defaults if not set)
        """
        start_time = datetime.now()

        try:
            from .untracked_work_storage import UntrackedWorkStorage

            storage = UntrackedWorkStorage(str(self.workspace))
            await self._ensure_conport_client()

            # Get config (returns defaults if not set)
            config = await storage.get_user_config(conport_client=self.conport_client)
            is_default_source = self.conport_client is None

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "config": config,
                "source": "default" if is_default_source else "conport",
                "description": {
                    "enabled": "Feature 1 on/off switch",
                    "confidence_threshold": "Min confidence to show reminders (session 2: 0.65, session 3: 0.60)",
                    "grace_period_minutes": "Ignore work newer than this (30 min = exploratory work)",
                    "auto_track_threshold": "F1: Auto-create task when confidence >= threshold (0.85 = high confidence only)",
                    "quiet_hours": "Suppress reminders during sleep/focus time",
                    "snooze_durations": "Snooze lengths in seconds",
                    "max_reminded_count": "Stop reminding after this many times",
                    "auto_abandon_after_days": "Auto-abandon work older than this"
                },
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                },
                "persisted_source": bool(self.conport_client)
            }

            logger.info(f"get_untracked_work_config: enabled={config.get('enabled')}")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"get_untracked_work_config failed: {e}", exc_info=True)
            return json.dumps({
                "error": str(e)
            }, indent=2)

    async def update_untracked_work_config_tool(
        self,
        enabled: Optional[bool] = None,
        confidence_threshold: Optional[float] = None,
        grace_period_minutes: Optional[int] = None,
        auto_track_threshold: Optional[float] = None,
        quiet_hours_enabled: Optional[bool] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None
    ) -> str:
        """
        Feature 1 Config: Update user configuration

        Updates only provided fields, keeps others unchanged.
        Validates inputs before saving.

        Args:
            enabled: Enable/disable Feature 1
            confidence_threshold: Min confidence (0.0-1.0)
            grace_period_minutes: Grace period (0-180 minutes)
            auto_track_threshold: F1 Auto-track threshold (0.0-1.0, default 0.85)
            quiet_hours_enabled: Enable quiet hours
            quiet_hours_start: Start time (HH:MM)
            quiet_hours_end: End time (HH:MM)

        Returns:
            JSON with updated config
        """
        start_time = datetime.now()

        try:
            from .untracked_work_storage import UntrackedWorkStorage

            storage = UntrackedWorkStorage(str(self.workspace))
            await self._ensure_conport_client()

            # Get current config
            config = await storage.get_user_config(conport_client=self.conport_client)

            # Update provided fields
            updates = {}

            if enabled is not None:
                config["enabled"] = enabled
                updates["enabled"] = enabled

            if confidence_threshold is not None:
                if not 0.0 <= confidence_threshold <= 1.0:
                    return json.dumps({"error": "confidence_threshold must be 0.0-1.0"}, indent=2)
                config["confidence_threshold"] = confidence_threshold
                updates["confidence_threshold"] = confidence_threshold

            if grace_period_minutes is not None:
                if not 0 <= grace_period_minutes <= 180:
                    return json.dumps({"error": "grace_period_minutes must be 0-180"}, indent=2)
                config["grace_period_minutes"] = grace_period_minutes
                updates["grace_period_minutes"] = grace_period_minutes

            if auto_track_threshold is not None:
                if not 0.0 <= auto_track_threshold <= 1.0:
                    return json.dumps({"error": "auto_track_threshold must be 0.0-1.0"}, indent=2)
                config["auto_track_threshold"] = auto_track_threshold
                updates["auto_track_threshold"] = auto_track_threshold

            if quiet_hours_enabled is not None:
                config["quiet_hours"]["enabled"] = quiet_hours_enabled
                updates["quiet_hours_enabled"] = quiet_hours_enabled

            if quiet_hours_start is not None:
                # Validate format
                try:
                    datetime.strptime(quiet_hours_start, "%H:%M")
                    config["quiet_hours"]["start"] = quiet_hours_start
                    updates["quiet_hours_start"] = quiet_hours_start
                except ValueError:
                    return json.dumps({"error": "quiet_hours_start must be HH:MM format"}, indent=2)

            if quiet_hours_end is not None:
                # Validate format
                try:
                    datetime.strptime(quiet_hours_end, "%H:%M")
                    config["quiet_hours"]["end"] = quiet_hours_end
                    updates["quiet_hours_end"] = quiet_hours_end
                except ValueError:
                    return json.dumps({"error": "quiet_hours_end must be HH:MM format"}, indent=2)

            saved = await storage.save_user_config(config, self.conport_client)

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = {
                "status": "config_updated" if saved else "config_updated_not_persisted",
                "message": f"✅ Updated {len(updates)} setting(s)",
                "updates": updates,
                "current_config": config,
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                },
                "persisted_to_conport": bool(saved)
            }

            logger.info(f"update_untracked_work_config: {len(updates)} fields updated")
            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error(f"update_untracked_work_config failed: {e}", exc_info=True)
            return json.dumps({
                "error": str(e)
            }, indent=2)

    def _extract_metric_timestamp(
        self,
        value: Dict[str, Any],
        key: Optional[str],
    ) -> Optional[datetime]:
        """Extract snapshot timestamp from metric history row."""
        timestamp_value = value.get("timestamp") if isinstance(value, dict) else None
        if isinstance(timestamp_value, str):
            try:
                return datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
            except ValueError:
                pass

        if not key:
            return None

        for fmt in ("%Y-%m-%d_%H%M%S", "%Y-%m-%d_summary", "%Y-%m-%d"):
            try:
                return datetime.strptime(key, fmt)
            except ValueError:
                continue
        return None

    def _extract_metric_value(
        self,
        value: Dict[str, Any],
        metric_name: str,
    ) -> Optional[float]:
        """Extract normalized metric value from metrics snapshot."""
        if not isinstance(value, dict):
            return None

        nested_metrics = value.get("metrics")
        if isinstance(nested_metrics, dict) and metric_name in nested_metrics:
            try:
                return float(nested_metrics[metric_name])
            except (TypeError, ValueError):
                return None

        f1_f4 = value.get("f1_f4_metrics", {})
        f5 = value.get("f5_metrics", {})
        f6 = value.get("f6_metrics", {})

        try:
            if metric_name == "confidence":
                if "confidence_score" in value:
                    return float(value["confidence_score"])
                return float(f1_f4.get("avg_confidence"))
            if metric_name == "pattern_boost":
                return float(f5.get("avg_boost"))
            if metric_name == "pass_rate":
                return float(f1_f4.get("pass_rate"))
            if metric_name == "abandonment_rate":
                if "abandonment_rate" in value:
                    return float(value["abandonment_rate"])
                abandoned = float(f6.get("total_abandoned", 0))
                total = float(f1_f4.get("total_detections", 0))
                if total <= 0:
                    return 0.0
                return abandoned / total
        except (TypeError, ValueError):
            return None
        return None

    def _aggregate_metric_points(
        self,
        points: List[Dict[str, Any]],
        period: str,
    ) -> List[Dict[str, Any]]:
        """Aggregate metric points into daily/weekly buckets."""
        if period not in {"daily", "weekly"}:
            return points

        buckets: Dict[str, List[float]] = {}
        for point in points:
            timestamp_raw = point.get("timestamp")
            value = point.get("value")
            if timestamp_raw is None or value is None:
                continue
            try:
                dt = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
                value_f = float(value)
            except (TypeError, ValueError):
                continue

            if period == "weekly":
                bucket_key = dt.strftime("%G-W%V")
            else:
                bucket_key = dt.strftime("%Y-%m-%d")
            buckets.setdefault(bucket_key, []).append(value_f)

        aggregated = []
        for bucket_key in sorted(buckets.keys()):
            values = buckets[bucket_key]
            aggregated.append(
                {
                    "bucket": bucket_key,
                    "value": round(sum(values) / len(values), 4),
                    "count": len(values),
                }
            )
        return aggregated

    def _extract_symbol_at_position(self, line: str, column: int) -> Optional[str]:
        """Extract symbol name at column position"""
        if column >= len(line):
            return None

        # Find word boundaries around column
        import re
        # Word characters: letters, numbers, underscore
        word_chars = re.compile(r'\w')

        # Find start of word
        start = column
        while start > 0 and word_chars.match(line[start - 1]):
            start -= 1

        # Find end of word
        end = column
        while end < len(line) and word_chars.match(line[end]):
            end += 1

        symbol = line[start:end]
        return symbol if symbol else None

    async def _extract_definition_context(
        self,
        file_path: Path,
        line: int,
        column: int
    ) -> str:
        """
        Extract 7-line context around definition

        Format (ADHD-optimized):
        - 3 lines before
        - Definition line with >>> marker
        - 3 lines after
        """
        try:
            content = file_path.read_text()
            lines = content.splitlines()

            # Calculate range (3 before, 1 target, 3 after)
            start_line = max(0, line - 4)  # line is 1-indexed
            end_line = min(len(lines), line + 3)

            context_lines = []
            for i in range(start_line, end_line):
                line_num = i + 1
                line_text = lines[i] if i < len(lines) else ""

                # Highlight definition line
                if line_num == line:
                    context_lines.append(f">>> {line_num:4d}: {line_text}  ← DEFINITION")
                else:
                    context_lines.append(f"    {line_num:4d}: {line_text}")

            return "\n".join(context_lines)

        except Exception as e:
            return f"(context unavailable: {e})"
    def _estimate_tokens(self, text: str) -> int:
        """Conservative token estimation delegated to shared utility."""
        return estimate_mcp_tokens(text)

    def _truncate_to_token_budget(
        self,
        lines: list[str],
        max_tokens: int,
        start_line_num: int = 1
    ) -> tuple[list[str], bool]:
        """
        Truncate lines to fit token budget with line numbers.

        Returns (truncated_lines, was_truncated)
        """
        return truncate_numbered_lines(
            lines=lines,
            max_tokens=max_tokens,
            start_line_num=start_line_num,
        )

    async def read_file_tool(
        self,
        relative_path: str,
        start_line: int = 0,
        end_line: Optional[int] = None,
        max_lines: int = 500,  # ADHD-safe limit
        max_tokens: int = 9000  # MCP budget (10K limit with headroom)
    ) -> str:
        """
        Read file with optional line range

        Returns content in cat -n format with line numbers
        """
        file_path = self._resolve_path(relative_path)

        if not file_path.exists():
            raise FileNotFoundError(
                f"❌ File not found: {relative_path}\n"
                f"   Workspace: {self.workspace}\n"
                f"   Looking for: {file_path}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"❌ Not a file: {relative_path}\n"
                f"   Path is a directory, use list_dir instead"
            )

        # Read file
        content = file_path.read_text()
        lines = content.splitlines()

        # Apply line range with max_lines enforcement
        if end_line is None:
            # No end specified, apply max_lines from start
            actual_end = min(len(lines), start_line + max_lines)
            selected_lines = lines[start_line:actual_end]
        else:
            # End specified, but still respect max_lines
            requested_count = end_line - start_line + 1
            if requested_count > max_lines:
                actual_end = start_line + max_lines
                selected_lines = lines[start_line:actual_end]
            else:
                selected_lines = lines[start_line:end_line + 1]

        # Format with token budget enforcement
        numbered_lines, was_truncated = self._truncate_to_token_budget(
            selected_lines,
            max_tokens=max_tokens,
            start_line_num=start_line + 1
        )

        result = "\n".join(numbered_lines)

        # Log with truncation info
        status = "TRUNCATED" if was_truncated else "complete"
        estimated_tokens = self._estimate_tokens(result)
        logger.info(
            f"read_file: {relative_path} ({len(numbered_lines)} lines, "
            f"{estimated_tokens} tokens, {status})"
        )

        return result

    async def list_dir_tool(
        self,
        relative_path: str,
        recursive: bool = False
    ) -> str:
        """
        List directory contents

        Returns JSON structure with directories and files
        """
        dir_path = self._resolve_path(relative_path)

        if not dir_path.exists():
            raise FileNotFoundError(
                f"❌ Directory not found: {relative_path}\n"
                f"   Workspace: {self.workspace}\n"
                f"   Looking for: {dir_path}"
            )

        if not dir_path.is_dir():
            raise ValueError(
                f"❌ Not a directory: {relative_path}\n"
                f"   Path is a file, use read_file instead"
            )

        # List directory
        result = {"directories": [], "files": []}

        if recursive:
            # Recursive listing
            for item in dir_path.rglob('*'):
                # Skip .git and common ignore patterns
                if '.git' in item.parts or '__pycache__' in item.parts:
                    continue

                rel_path = str(item.relative_to(dir_path))
                if item.is_dir():
                    result["directories"].append(rel_path)
                else:
                    result["files"].append(rel_path)
        else:
            # Non-recursive listing
            for item in dir_path.iterdir():
                # Skip hidden files starting with .
                if item.name.startswith('.'):
                    continue

                if item.is_dir():
                    result["directories"].append(item.name)
                else:
                    result["files"].append(item.name)

        # Sort for consistent output
        result["directories"].sort()
        result["files"].sort()

        # Format as readable text
        output_lines = []

        if result["directories"]:
            output_lines.append("Directories:")
            for d in result["directories"]:
                output_lines.append(f"  {d}/")

        if result["files"]:
            if result["directories"]:
                output_lines.append("")
            output_lines.append("Files:")
            for f in result["files"]:
                output_lines.append(f"  {f}")

        if not result["directories"] and not result["files"]:
            output_lines.append("(empty directory)")

        logger.info(f"list_dir: {relative_path} ({len(result['directories'])} dirs, {len(result['files'])} files)")
        return "\n".join(output_lines)

    async def find_similar_code_tool(
        self,
        query: str,
        top_k: int = 10,
        user_id: str = "default",
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Find code semantically similar to natural language query (F-NEW-2)

        Integrates with Dope-Context MCP for semantic search:
        - AST-aware code chunking
        - Voyage embeddings with neural reranking
        - Natural language queries vs exact name matching
        - Enriched with Serena's complexity scores
        - Multi-workspace: Semantic search across workspaces

        Args:
            query: Natural language query (e.g., 'authentication middleware patterns')
            top_k: Number of results (default: 10, ADHD-adjusted)
            user_id: User identifier for ADHD state lookup
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON with semantic search results + complexity scores
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.find_similar_code_multi(
                query, top_k, user_id,
                workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        # Start search
        start_time = datetime.now()

        # Get dynamic top_k from ADHD Engine
        top_k = await get_dynamic_max_results(user_id, top_k)

        try:
            # Call Dope-Context search_code via direct function call
            # (Since we're in same process, can import directly)
            sys.path.insert(0, str(self.workspace.parent / "dope-context" / "src"))

            try:
                from mcp.server import search_code_impl
                results = await search_code_impl(query, top_k, workspace_path=str(self.workspace))
            except ImportError:
                # Fallback: Use MCP client to call dope-context
                logger.warning("Dope-Context not available for direct call, semantic search unavailable")
                return json.dumps({
                    "error": "Semantic search unavailable (Dope-Context MCP not configured)",
                    "query": query,
                    "fallback": "Use find_symbol for exact name matching"
                }, indent=2)

            # Enrich results with Serena's complexity analysis
            tree_sitter_available = await self._ensure_component("tree_sitter")

            if tree_sitter_available and self.tree_sitter:
                for result in results:
                    try:
                        file_path = result.get("file_path", "")
                        function_name = result.get("function_name", "")

                        complexity = await self.tree_sitter.analyze_complexity(file_path, function_name)
                        result["serena_complexity"] = complexity.get("score", 0.0)
                        result["adhd_category"] = complexity.get("category", "unknown")
                    except Exception as e:
                        result["serena_complexity"] = None

                        logger.error(f"Error: {e}")
            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            output = {
                "query": query,
                "found": len(results),
                "top_k": top_k,
                "adhd_adjusted": True,
                "results": results,
                "performance": {
                    "latency_ms": round(elapsed_ms, 2),
                    "source": "dope-context",
                    "serena_enhanced": tree_sitter_available
                }
            }

            logger.info(f"find_similar_code: '{query}' → {len(results)} results ({elapsed_ms:.1f}ms)")
            return json.dumps(output, indent=2)

        except Exception as e:
            logger.error(f"find_similar_code failed: {e}")
            return json.dumps({"error": str(e), "query": query}, indent=2)

    async def predict_navigation_from_git_tool(
        self,
        current_file: str,
        days_back: int = 90
    ) -> str:
        """
        Predict navigation targets from git history patterns (F-NEW-12)

        Uses existing GitHistoryAnalyzer to analyze commit patterns and
        suggest files you typically edit together.

        Args:
            current_file: File you're currently viewing
            days_back: Days of git history to analyze (default: 90)

        Returns:
            JSON with predicted files and confidence scores
        """
        start_time = datetime.now()

        try:
            # Import existing GitHistoryAnalyzer
            sys.path.insert(0, str(self.workspace.parent / "src"))
            from dopemux.profile_analyzer import GitHistoryAnalyzer

            analyzer = GitHistoryAnalyzer(repo_path=self.workspace)
            analysis = analyzer.analyze(days_back=days_back, max_commits=500)

            # Get directory of current file
            current_dir = Path(current_file).parent if "/" in current_file else Path(".")

            # Find related directories from git patterns
            related_dirs = []
            for dir_path, commit_count in analysis.common_directories:
                if str(current_dir) in dir_path or dir_path in str(current_dir):
                    continue  # Skip same directory

                # Calculate confidence based on commit frequency
                confidence = min(1.0, commit_count / 50)  # Normalize to 0-1

                related_dirs.append({
                    "directory": dir_path,
                    "commit_count": commit_count,
                    "confidence": round(confidence, 2),
                    "reasoning": f"Modified together in {commit_count} commits"
                })

            # Sort by confidence and take top 5 (ADHD limit)
            related_dirs.sort(key=lambda x: x['confidence'], reverse=True)
            suggestions = related_dirs[:5]

            elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

            output = {
                "current_file": current_file,
                "current_directory": str(current_dir),
                "suggestions": suggestions,
                "git_analysis": {
                    "total_commits": analysis.total_commits,
                    "days_analyzed": days_back,
                    "peak_work_time": analysis.peak_work_time,
                    "suggested_energy": analysis.suggested_energy_level
                },
                "performance": {
                    "latency_ms": round(elapsed_ms, 2)
                }
            }

            logger.info(f"predict_navigation_from_git: {current_file} → {len(suggestions)} suggestions ({elapsed_ms:.1f}ms)")
            return json.dumps(output, indent=2)

        except Exception as e:
            logger.error(f"Git prediction failed: {e}")
            return json.dumps({
                "error": str(e),
                "current_file": current_file,
                "fallback": "Use suggest_next_step for pattern-based suggestions"
            }, indent=2)

    async def find_test_file_tool(
        self,
        file_path: str,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        Smart test navigation - find test file for implementation or vice versa (F-NEW-18)

        Patterns recognized:
        - src/auth.py → tests/test_auth.py
        - auth.py → test_auth.py
        - services/api.py → tests/test_api.py
        - test_api.py → services/api.py (reverse)
        - Multi-workspace: Find tests across workspaces

        Args:
            file_path: Current file path (relative)
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON with test file path or creation suggestion
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.find_test_file_multi(
                file_path, workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        try:
            path = Path(file_path)
            filename = path.name
            parent_dir = path.parent

            # Check if this is a test file
            is_test = filename.startswith("test_") or "_test." in filename or path.parts and "test" in path.parts[0]

            if is_test:
                # Find implementation file
                if filename.startswith("test_"):
                    impl_name = filename.replace("test_", "", 1)
                else:
                    impl_name = filename.replace("_test", "")

                # Search common locations
                search_paths = [
                    self.workspace / "src" / impl_name,
                    self.workspace / "services" / impl_name,
                    self.workspace / impl_name,
                    parent_dir.parent / "src" / impl_name,
                    parent_dir.parent / impl_name
                ]

                for candidate in search_paths:
                    if candidate.exists():
                        return json.dumps({
                            "found": True,
                            "test_file": file_path,
                            "implementation_file": str(candidate.relative_to(self.workspace)),
                            "relationship": "test→impl"
                        }, indent=2)

                return json.dumps({
                    "found": False,
                    "test_file": file_path,
                    "suggestion": f"Implementation file not found. Expected: {impl_name}"
                }, indent=2)

            else:
                # Find test file
                test_names = [
                    f"test_{filename}",
                    filename.replace(".py", "_test.py")
                ]

                # Search common test locations
                search_paths = []
                for test_name in test_names:
                    search_paths.extend([
                        self.workspace / "tests" / test_name,
                        self.workspace / "test" / test_name,
                        parent_dir / test_name,
                        self.workspace / f"tests/{parent_dir.name}/{test_name}" if parent_dir.name != "." else None
                    ])

                search_paths = [p for p in search_paths if p]  # Remove None

                for candidate in search_paths:
                    if candidate.exists():
                        return json.dumps({
                            "found": True,
                            "implementation_file": file_path,
                            "test_file": str(candidate.relative_to(self.workspace)),
                            "relationship": "impl→test"
                        }, indent=2)

                # Suggest test file creation
                suggested_path = self.workspace / "tests" / f"test_{filename}"
                return json.dumps({
                    "found": False,
                    "implementation_file": file_path,
                    "suggestion": f"Create test: {suggested_path.relative_to(self.workspace)}",
                    "adhd_tip": "TDD helps break down complex tasks into smaller steps"
                }, indent=2)

        except Exception as e:
            logger.error(f"find_test_file failed: {e}")
            return json.dumps({"error": str(e), "file_path": file_path}, indent=2)

    async def get_unified_complexity_tool(
        self,
        file_path: str,
        symbol: Optional[str] = None,
        user_id: str = "default",
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[List[str]] = None,
    ) -> str:
        """
        F-NEW-3: Get unified complexity score combining AST, LSP, usage, and ADHD.

        Combines:
        - AST complexity (dope-context Tree-sitter)
        - LSP complexity (Serena code analysis)
        - Usage complexity (reference counts)
        - ADHD multiplier (user-specific adjustments)
        - Multi-workspace: Unified complexity across workspaces

        Args:
            file_path: File path to analyze
            symbol: Optional function/class name
            user_id: User identifier for ADHD adjustments
            workspace_path: Optional single workspace path
            workspace_paths: Optional multiple workspace paths

        Returns:
            JSON with complexity breakdown and interpretation
        """
        # Multi-workspace mode
        if workspace_paths or workspace_path:
            from multi_workspace_wrapper import SerenaMultiWorkspace
            wrapper = SerenaMultiWorkspace()
            result = await wrapper.get_unified_complexity_multi(
                file_path, symbol, user_id,
                workspace_path, workspace_paths
            )
            return json.dumps(result, indent=2)
        
        # Single workspace mode (backward compatible)
        try:
            # Import complexity coordinator
            import sys
            coord_path = Path(__file__).parent.parent.parent / "complexity_coordinator"
            if str(coord_path) not in sys.path:
                sys.path.insert(0, str(coord_path))

            from unified_complexity import get_unified_complexity

            # Get unified complexity
            breakdown = await get_unified_complexity(file_path, symbol, user_id)

            return json.dumps(breakdown.to_dict(), indent=2)

        except Exception as e:
            logger.error(f"get_unified_complexity failed: {e}")
            return json.dumps({
                "error": str(e),
                "file_path": file_path,
                "symbol": symbol,
                "fallback_score": 0.5,
                "interpretation": "Error - using medium complexity estimate"
            }, indent=2)


async def main():
    """Main entry point for Serena v2 MCP server"""
    logger.info("="*60)
    logger.info("SERENA V2 MCP SERVER - PHASE 2 + ENHANCED FEATURES")
    logger.info("ADHD-optimized code intelligence (24 tools)")
    logger.info("Enhanced: Cache (100x faster), Unified Complexity, File Watcher")
    logger.info("="*60)

    # Create server instance
    server_instance = SerenaV2MCPServer()

    # Initialize workspace (fast startup with lazy loading)
    await server_instance.initialize()

    # Register tools
    server_instance.register_tools()

    logger.info("="*60)
    logger.info("Server ready - awaiting tool calls")
    logger.info(f"Workspace: {server_instance.workspace}")
    logger.info(f"Tools available: 24")
    logger.info(f"  - Health (1): get_workspace_status")
    logger.info(f"  - Navigation Tier 1 (4): find_symbol, goto_definition, get_context, find_references")
    logger.info(f"  - Enhanced Navigation (4): find_similar_code, predict_navigation_from_git, find_test_file, get_unified_complexity")
    logger.info(f"  - Performance: Redis cache (100x faster), File watcher, Unified complexity")
    logger.info(f"  - ADHD Intelligence Tier 2 (4): analyze_complexity, filter_by_focus, suggest_next_step, get_reading_order")
    logger.info(f"  - Advanced Tier 3 (3): find_relationships, get_navigation_patterns, update_focus_mode")
    logger.info(f"  - Feature 1 Detection (1): detect_untracked_work")
    logger.info(f"  - Feature 1 Actions (3): track_untracked_work, snooze_untracked_work, ignore_untracked_work")
    logger.info(f"  - Feature 1 Config (2): get_untracked_work_config, update_untracked_work_config")
    logger.info(f"  - Files (2): read_file, list_dir")
    logger.info(f"Lazy loading: database, lsp, claude_context, tree_sitter, adhd_features")
    logger.info(f"Feature 1: COMPLETE - Detection + Actions + Storage + Config + Reminders ✅")
    logger.info(f"Tier 3: Simplified implementations (Phase 3 will add full database)")
    logger.info("="*60)

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nShutdown requested")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
