"""
Serena v2 Enhanced LSP Wrapper

Async LSP wrapper with intelligent caching, batch operations, and ADHD optimizations.
Foundation for Serena's code intelligence capabilities.
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

from .navigation_cache import NavigationCache
from .adhd_features import ADHDCodeNavigator
from .focus_manager import FocusManager

logger = logging.getLogger(__name__)


class LSPConfig:
    """Configuration for LSP server integration."""
    def __init__(
        self,
        language_servers: Dict[str, Dict[str, Any]] = None,
        cache_ttl: int = 300,  # 5 minutes
        batch_size: int = 20,
        timeout: float = 10.0,
        max_concurrent_requests: int = 5
    ):
        self.language_servers = language_servers or self._default_language_servers()
        self.cache_ttl = cache_ttl
        self.batch_size = batch_size
        self.timeout = timeout
        self.max_concurrent_requests = max_concurrent_requests

    def _default_language_servers(self) -> Dict[str, Dict[str, Any]]:
        """Default language server configurations."""
        return {
            "python": {
                "command": "pylsp",
                "args": [],
                "file_extensions": [".py"],
                "capabilities": ["hover", "definition", "references", "symbols"]
            },
            "typescript": {
                "command": "typescript-language-server",
                "args": ["--stdio"],
                "file_extensions": [".ts", ".tsx", ".js", ".jsx"],
                "capabilities": ["hover", "definition", "references", "symbols", "rename"]
            },
            "rust": {
                "command": "rust-analyzer",
                "args": [],
                "file_extensions": [".rs"],
                "capabilities": ["hover", "definition", "references", "symbols", "rename"]
            }
        }


class LSPResponse:
    """Enhanced LSP response with ADHD-friendly metadata."""
    def __init__(
        self,
        result: Any,
        language: str,
        method: str,
        duration: float,
        cached: bool = False,
        complexity_score: Optional[float] = None
    ):
        self.result = result
        self.language = language
        self.method = method
        self.duration = duration
        self.cached = cached
        self.complexity_score = complexity_score
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "result": self.result,
            "language": self.language,
            "method": self.method,
            "duration": self.duration,
            "cached": self.cached,
            "complexity_score": self.complexity_score,
            "timestamp": self.timestamp.isoformat(),
            "_serena_v2": True
        }


class EnhancedLSPWrapper:
    """
    Enhanced LSP wrapper with async operations and ADHD optimizations.

    Features:
    - Async LSP communication for non-blocking UI
    - Intelligent caching with Redis backend
    - Batch request processing for efficiency
    - ADHD-optimized result presentation
    - Context-aware navigation assistance
    - Focus mode with complexity filtering
    """

    def __init__(
        self,
        config: LSPConfig,
        workspace_path: Path,
        cache: NavigationCache,
        adhd_navigator: ADHDCodeNavigator,
        focus_manager: FocusManager
    ):
        self.config = config
        self.workspace_path = workspace_path
        self.cache = cache
        self.adhd_navigator = adhd_navigator
        self.focus_manager = focus_manager

        # LSP server processes
        self.lsp_servers: Dict[str, subprocess.Popen] = {}
        self.server_ready: Dict[str, asyncio.Event] = {}
        self.request_semaphore = asyncio.Semaphore(config.max_concurrent_requests)

        # Request tracking
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_counter = 0
        self.stats = {
            "requests_sent": 0,
            "cache_hits": 0,
            "average_response_time": 0.0,
            "active_servers": 0
        }

    async def initialize(self) -> None:
        """Initialize LSP servers and components."""
        logger.info("🚀 Initializing Serena v2 Enhanced LSP...")

        # Initialize supporting components
        await asyncio.gather(
            self.cache.initialize(),
            self.adhd_navigator.initialize(self.workspace_path),
            self.focus_manager.initialize()
        )

        # Start language servers for detected languages
        detected_languages = await self._detect_project_languages()
        for language in detected_languages:
            await self._start_language_server(language)

        logger.info(f"✅ Enhanced LSP ready with {len(self.lsp_servers)} language servers")

    async def _detect_project_languages(self) -> List[str]:
        """Detect programming languages used in the project."""
        languages = set()

        # Scan workspace for language indicators
        for lang, config in self.config.language_servers.items():
            extensions = config.get("file_extensions", [])
            for ext in extensions:
                if list(self.workspace_path.rglob(f"*{ext}")):
                    languages.add(lang)
                    break

        # Always include Python (common in Dopemux projects)
        if not languages:
            languages.add("python")

        logger.info(f"📋 Detected languages: {', '.join(sorted(languages))}")
        return list(languages)

    async def _start_language_server(self, language: str) -> bool:
        """Start LSP server for specific language."""
        if language not in self.config.language_servers:
            logger.warning(f"No configuration for language: {language}")
            return False

        server_config = self.config.language_servers[language]
        command = [server_config["command"]] + server_config.get("args", [])

        try:
            # Start LSP server process
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.workspace_path),
                text=True
            )

            self.lsp_servers[language] = process
            self.server_ready[language] = asyncio.Event()

            # Start communication tasks
            asyncio.create_task(self._handle_server_communication(language))

            # Initialize server
            await self._initialize_lsp_server(language)

            logger.info(f"🔧 Started {language} LSP server (PID: {process.pid})")
            return True

        except FileNotFoundError:
            logger.warning(f"LSP server not found for {language}: {server_config['command']}")
            return False
        except Exception as e:
            logger.error(f"Failed to start {language} LSP server: {e}")
            return False

    async def _initialize_lsp_server(self, language: str) -> None:
        """Initialize LSP server with workspace settings."""
        process = self.lsp_servers[language]

        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "processId": None,
                "rootUri": self.workspace_path.as_uri(),
                "workspaceFolders": [
                    {
                        "uri": self.workspace_path.as_uri(),
                        "name": self.workspace_path.name
                    }
                ],
                "capabilities": {
                    "textDocument": {
                        "hover": {"contentFormat": ["markdown", "plaintext"]},
                        "definition": {"linkSupport": True},
                        "references": {"context": {"includeDeclaration": True}},
                        "documentSymbol": {"hierarchicalDocumentSymbolSupport": True}
                    },
                    "workspace": {
                        "symbol": {"symbolKind": {"valueSet": list(range(1, 27))}}
                    }
                }
            }
        }

        # Send initialization
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }

        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()

        # Mark as ready
        self.server_ready[language].set()

    async def _handle_server_communication(self, language: str) -> None:
        """Handle communication with LSP server."""
        process = self.lsp_servers[language]

        try:
            while process.poll() is None:
                # Read response from server
                line = await asyncio.get_event_loop().run_in_executor(
                    None, process.stdout.readline
                )

                if not line:
                    break

                try:
                    response = json.loads(line.strip())
                    await self._process_lsp_response(language, response)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {language} LSP: {line[:100]}...")

        except Exception as e:
            logger.error(f"Communication error with {language} LSP: {e}")
        finally:
            logger.info(f"🔌 {language} LSP communication ended")

    async def _process_lsp_response(self, language: str, response: Dict[str, Any]) -> None:
        """Process response from LSP server."""
        request_id = response.get("id")

        if request_id and request_id in self.pending_requests:
            # Complete pending request
            future = self.pending_requests.pop(request_id)
            if not future.done():
                future.set_result(response)

        elif "method" in response:
            # Handle notifications (diagnostics, etc.)
            await self._handle_lsp_notification(language, response)

    async def _handle_lsp_notification(self, language: str, notification: Dict[str, Any]) -> None:
        """Handle LSP notifications (diagnostics, etc.)."""
        method = notification.get("method", "")

        if method == "textDocument/publishDiagnostics":
            # Handle diagnostics with ADHD-friendly filtering
            params = notification.get("params", {})
            diagnostics = params.get("diagnostics", [])

            # Filter diagnostics based on focus mode
            if self.focus_manager.is_focus_mode_active():
                # In focus mode, only show errors, not warnings
                filtered_diagnostics = [
                    d for d in diagnostics
                    if d.get("severity", 1) <= 2  # Error or Warning
                ]
                logger.debug(f"🎯 Focus mode: filtered {len(diagnostics)} → {len(filtered_diagnostics)} diagnostics")
            else:
                filtered_diagnostics = diagnostics

            # Cache diagnostics for quick access
            file_uri = params.get("uri", "")
            if file_uri:
                await self.cache.cache_diagnostics(file_uri, filtered_diagnostics)

    def _next_request_id(self) -> str:
        """Generate next request ID."""
        self.request_counter += 1
        return f"serena_v2_{self.request_counter}"

    # Enhanced LSP Operations

    async def find_definition(
        self,
        file_path: str,
        line: int,
        character: int,
        language: str = None,
        use_cache: bool = True
    ) -> Optional[LSPResponse]:
        """Find definition with caching and ADHD optimizations."""
        # Auto-detect language if not provided
        if not language:
            language = self._detect_file_language(file_path)

        if not language or language not in self.lsp_servers:
            logger.warning(f"No LSP server available for {file_path}")
            return None

        # Check cache first
        cache_key = f"definition:{file_path}:{line}:{character}"
        if use_cache:
            cached_result = await self.cache.get_navigation_result(cache_key)
            if cached_result:
                logger.debug(f"🎯 Cache hit: definition for {Path(file_path).name}:{line}")
                return LSPResponse(
                    result=cached_result,
                    language=language,
                    method="textDocument/definition",
                    duration=0.001,  # Cache hit
                    cached=True
                )

        # Make LSP request
        start_time = time.time()

        try:
            async with self.request_semaphore:
                # Wait for server to be ready
                await self.server_ready[language].wait()

                # Send definition request
                request = {
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "textDocument/definition",
                    "params": {
                        "textDocument": {"uri": Path(file_path).as_uri()},
                        "position": {"line": line, "character": character}
                    }
                }

                # Create future for response
                future = asyncio.Future()
                self.pending_requests[request["id"]] = future

                # Send request
                process = self.lsp_servers[language]
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()

                # Wait for response with timeout
                response = await asyncio.wait_for(future, timeout=self.config.timeout)

                duration = time.time() - start_time
                self.stats["requests_sent"] += 1
                self.stats["average_response_time"] = (
                    self.stats["average_response_time"] * (self.stats["requests_sent"] - 1) + duration
                ) / self.stats["requests_sent"]

                # Extract result
                result = response.get("result", [])

                # Calculate complexity score for ADHD users
                complexity_score = self._calculate_definition_complexity(result)

                # Cache result
                if use_cache and result:
                    await self.cache.cache_navigation_result(cache_key, result, self.config.cache_ttl)

                # Create enhanced response
                lsp_response = LSPResponse(
                    result=result,
                    language=language,
                    method="textDocument/definition",
                    duration=duration,
                    cached=False,
                    complexity_score=complexity_score
                )

                # Apply ADHD filtering if needed
                if self.focus_manager.is_focus_mode_active():
                    lsp_response = await self.adhd_navigator.filter_for_focus_mode(lsp_response)

                logger.debug(f"🎯 Definition found for {Path(file_path).name}:{line} in {duration:.3f}s")
                return lsp_response

        except asyncio.TimeoutError:
            logger.warning(f"Definition request timed out for {file_path}:{line}")
            return None
        except Exception as e:
            logger.error(f"Definition request failed: {e}")
            return None

    async def find_references(
        self,
        file_path: str,
        line: int,
        character: int,
        include_declaration: bool = True,
        language: str = None,
        progress_callback: Optional[Callable] = None
    ) -> Optional[LSPResponse]:
        """Find references with progressive loading for ADHD users."""
        if not language:
            language = self._detect_file_language(file_path)

        if not language or language not in self.lsp_servers:
            return None

        # Check cache
        cache_key = f"references:{file_path}:{line}:{character}:{include_declaration}"
        cached_result = await self.cache.get_navigation_result(cache_key)
        if cached_result:
            logger.debug(f"🎯 Cache hit: references for {Path(file_path).name}:{line}")
            return LSPResponse(
                result=cached_result,
                language=language,
                method="textDocument/references",
                duration=0.001,
                cached=True
            )

        if progress_callback:
            progress_callback("🔍 Searching for references...")

        start_time = time.time()

        try:
            async with self.request_semaphore:
                await self.server_ready[language].wait()

                request = {
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "textDocument/references",
                    "params": {
                        "textDocument": {"uri": Path(file_path).as_uri()},
                        "position": {"line": line, "character": character},
                        "context": {"includeDeclaration": include_declaration}
                    }
                }

                future = asyncio.Future()
                self.pending_requests[request["id"]] = future

                process = self.lsp_servers[language]
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()

                response = await asyncio.wait_for(future, timeout=self.config.timeout)
                duration = time.time() - start_time

                result = response.get("result", [])

                # ADHD optimization: progressive disclosure for large result sets
                if len(result) > 20 and progress_callback:
                    progress_callback(f"📊 Found {len(result)} references - applying ADHD filtering...")

                # Apply ADHD filtering for large result sets
                filtered_result = await self.adhd_navigator.apply_progressive_disclosure(
                    result, max_initial_items=10
                )

                # Calculate complexity for ADHD users
                complexity_score = len(result) / 50.0  # Rough complexity based on count

                # Cache result
                await self.cache.cache_navigation_result(cache_key, result, self.config.cache_ttl)

                if progress_callback:
                    progress_callback(f"✅ References loaded ({len(filtered_result)} shown initially)")

                return LSPResponse(
                    result=filtered_result,
                    language=language,
                    method="textDocument/references",
                    duration=duration,
                    cached=False,
                    complexity_score=complexity_score
                )

        except asyncio.TimeoutError:
            if progress_callback:
                progress_callback("⏰ Reference search timed out")
            return None
        except Exception as e:
            logger.error(f"References request failed: {e}")
            if progress_callback:
                progress_callback(f"❌ Reference search failed: {str(e)[:50]}...")
            return None

    async def get_document_symbols(
        self,
        file_path: str,
        language: str = None,
        focus_mode: bool = None
    ) -> Optional[LSPResponse]:
        """Get document symbols with ADHD-optimized hierarchical presentation."""
        if not language:
            language = self._detect_file_language(file_path)

        if not language or language not in self.lsp_servers:
            return None

        # Use focus manager setting if not explicitly specified
        if focus_mode is None:
            focus_mode = self.focus_manager.is_focus_mode_active()

        # Check cache
        cache_key = f"symbols:{file_path}:{focus_mode}"
        cached_result = await self.cache.get_navigation_result(cache_key)
        if cached_result:
            return LSPResponse(
                result=cached_result,
                language=language,
                method="textDocument/documentSymbol",
                duration=0.001,
                cached=True
            )

        start_time = time.time()

        try:
            async with self.request_semaphore:
                await self.server_ready[language].wait()

                request = {
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "textDocument/documentSymbol",
                    "params": {
                        "textDocument": {"uri": Path(file_path).as_uri()}
                    }
                }

                future = asyncio.Future()
                self.pending_requests[request["id"]] = future

                process = self.lsp_servers[language]
                process.stdin.write(json.dumps(request) + "\n")
                process.stdin.flush()

                response = await asyncio.wait_for(future, timeout=self.config.timeout)
                duration = time.time() - start_time

                symbols = response.get("result", [])

                # ADHD optimization: hierarchical filtering based on focus mode
                if focus_mode:
                    symbols = await self.adhd_navigator.filter_symbols_for_focus(symbols)

                # Calculate complexity
                complexity_score = self._calculate_symbol_complexity(symbols)

                # Cache result
                await self.cache.cache_navigation_result(cache_key, symbols, self.config.cache_ttl)

                return LSPResponse(
                    result=symbols,
                    language=language,
                    method="textDocument/documentSymbol",
                    duration=duration,
                    cached=False,
                    complexity_score=complexity_score
                )

        except asyncio.TimeoutError:
            logger.warning(f"Document symbols request timed out for {file_path}")
            return None
        except Exception as e:
            logger.error(f"Document symbols request failed: {e}")
            return None

    def _detect_file_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension."""
        file_ext = Path(file_path).suffix.lower()

        extension_map = {}
        for lang, config in self.config.language_servers.items():
            for ext in config.get("file_extensions", []):
                extension_map[ext] = lang

        return extension_map.get(file_ext)

    def _calculate_definition_complexity(self, definitions: List[Dict]) -> float:
        """Calculate complexity score for definition results."""
        if not definitions:
            return 0.0

        # Simple complexity based on number of definitions and their context
        base_complexity = min(len(definitions) / 3.0, 1.0)  # Normalize to 0-1

        # Increase complexity if definitions span multiple files
        files = set()
        for definition in definitions:
            uri = definition.get("uri", "")
            if uri:
                files.add(uri)

        file_complexity = min(len(files) / 5.0, 0.5)  # Max 0.5 for file spread

        return min(base_complexity + file_complexity, 1.0)

    def _calculate_symbol_complexity(self, symbols: List[Dict]) -> float:
        """Calculate complexity score for symbol list."""
        if not symbols:
            return 0.0

        # Count symbols by kind for complexity assessment
        symbol_counts = {}
        total_symbols = 0

        def count_symbols_recursive(symbol_list):
            nonlocal total_symbols
            for symbol in symbol_list:
                kind = symbol.get("kind", 0)
                symbol_counts[kind] = symbol_counts.get(kind, 0) + 1
                total_symbols += 1

                # Count children recursively
                children = symbol.get("children", [])
                if children:
                    count_symbols_recursive(children)

        count_symbols_recursive(symbols)

        # Complexity factors
        total_complexity = min(total_symbols / 50.0, 0.7)  # Base complexity from count
        nesting_complexity = min(len([s for s in symbols if s.get("children")]) / 10.0, 0.3)  # Nesting complexity

        return min(total_complexity + nesting_complexity, 1.0)

    # Performance and monitoring

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring."""
        active_servers = len([p for p in self.lsp_servers.values() if p.poll() is None])

        return {
            **self.stats,
            "active_servers": active_servers,
            "cache_hit_rate": f"{self.stats['cache_hits'] / max(1, self.stats['requests_sent']):.1%}",
            "server_languages": list(self.lsp_servers.keys()),
            "focus_mode_active": self.focus_manager.is_focus_mode_active(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for LSP wrapper."""
        try:
            # Check each component
            health_results = await asyncio.gather(
                self._check_lsp_servers(),
                self.cache.health_check(),
                self.adhd_navigator.health_check(),
                self.focus_manager.health_check(),
                return_exceptions=True
            )

            lsp_health = health_results[0] if not isinstance(health_results[0], Exception) else {"status": "error", "error": str(health_results[0])}
            cache_health = health_results[1] if not isinstance(health_results[1], Exception) else {"status": "error"}
            adhd_health = health_results[2] if not isinstance(health_results[2], Exception) else {"status": "error"}
            focus_health = health_results[3] if not isinstance(health_results[3], Exception) else {"status": "error"}

            # Overall status
            error_count = sum(1 for result in health_results if isinstance(result, Exception))
            if error_count == 0:
                overall_status = "🚀 Excellent"
            elif error_count <= 1:
                overall_status = "✅ Good"
            else:
                overall_status = "⚠️ Degraded"

            return {
                "overall_status": overall_status,
                "components": {
                    "lsp_servers": lsp_health,
                    "cache": cache_health,
                    "adhd_features": adhd_health,
                    "focus_manager": focus_health
                },
                "version": "v2_phase1",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "overall_status": "🔴 Critical",
                "error": str(e),
                "version": "v2_phase1"
            }

    async def _check_lsp_servers(self) -> Dict[str, Any]:
        """Check health of all LSP servers."""
        server_status = {}

        for language, process in self.lsp_servers.items():
            if process.poll() is None:
                server_status[language] = "🟢 Running"
            else:
                server_status[language] = f"🔴 Stopped (exit code: {process.poll()})"

        active_count = sum(1 for status in server_status.values() if "Running" in status)
        total_count = len(server_status)

        return {
            "status": f"🚀 {active_count}/{total_count} servers active",
            "servers": server_status,
            "active_count": active_count,
            "total_count": total_count
        }

    async def close(self) -> None:
        """Shutdown LSP wrapper and all servers."""
        logger.info("🛑 Shutting down Enhanced LSP...")

        # Shutdown LSP servers gracefully
        for language, process in self.lsp_servers.items():
            try:
                # Send shutdown request
                shutdown_request = {
                    "jsonrpc": "2.0",
                    "id": self._next_request_id(),
                    "method": "shutdown",
                    "params": None
                }

                process.stdin.write(json.dumps(shutdown_request) + "\n")
                process.stdin.flush()

                # Wait briefly for graceful shutdown
                await asyncio.sleep(0.5)

                # Terminate if still running
                if process.poll() is None:
                    process.terminate()
                    await asyncio.sleep(1.0)

                # Force kill if necessary
                if process.poll() is None:
                    process.kill()

                logger.debug(f"🔌 Shutdown {language} LSP server")

            except Exception as e:
                logger.error(f"Error shutting down {language} LSP: {e}")

        # Close supporting components
        await asyncio.gather(
            self.cache.close(),
            self.adhd_navigator.close(),
            self.focus_manager.close(),
            return_exceptions=True
        )

        logger.info("✅ Enhanced LSP shutdown complete")

    # Utility methods

    async def list_workspace_symbols(
        self,
        query: str = "",
        language: str = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """List workspace symbols with ADHD-friendly filtering."""
        all_symbols = []

        # Query all available language servers
        languages_to_query = [language] if language else list(self.lsp_servers.keys())

        for lang in languages_to_query:
            if lang not in self.lsp_servers:
                continue

            try:
                async with self.request_semaphore:
                    await self.server_ready[lang].wait()

                    request = {
                        "jsonrpc": "2.0",
                        "id": self._next_request_id(),
                        "method": "workspace/symbol",
                        "params": {"query": query}
                    }

                    future = asyncio.Future()
                    self.pending_requests[request["id"]] = future

                    process = self.lsp_servers[lang]
                    process.stdin.write(json.dumps(request) + "\n")
                    process.stdin.flush()

                    response = await asyncio.wait_for(future, timeout=self.config.timeout)
                    symbols = response.get("result", [])

                    # Add language context to symbols
                    for symbol in symbols:
                        symbol["_language"] = lang

                    all_symbols.extend(symbols)

            except Exception as e:
                logger.error(f"Workspace symbol query failed for {lang}: {e}")

        # ADHD optimization: sort by relevance and limit results
        if query:
            # Simple relevance scoring based on name match
            for symbol in all_symbols:
                name = symbol.get("name", "")
                symbol["_relevance"] = (
                    1.0 if query.lower() in name.lower() else
                    0.5 if any(word in name.lower() for word in query.lower().split()) else
                    0.1
                )

            all_symbols.sort(key=lambda s: s.get("_relevance", 0), reverse=True)

        # Apply ADHD limit
        return all_symbols[:max_results]