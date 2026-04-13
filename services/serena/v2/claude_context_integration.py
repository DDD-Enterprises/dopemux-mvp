"""
Claude-Context Integration Layer for Serena v2

Integrates Serena's navigation intelligence with claude-context's semantic search.
Enhances semantic search with LSP navigation, structure analysis, and ADHD optimizations.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass

from .mcp_client import McpClient, McpResponse

logger = logging.getLogger(__name__)


@dataclass
class ClaudeContextConfig:
    """Configuration for claude-context integration."""
    mcp_endpoint: str = "http://localhost:3000"  # claude-context MCP endpoint
    timeout: float = 5.0
    max_concurrent_requests: int = 3
    cache_results: bool = True
    cache_ttl: int = 600  # 10 minutes
    performance_target_ms: float = 200.0  # Target response time for ADHD optimization


@dataclass
class SemanticSearchResult:
    """Enhanced semantic search result with navigation intelligence."""
    # claude-context original data
    content: str
    file_path: str
    relevance_score: float
    chunk_id: str

    # Serena navigation enhancements
    symbol_type: Optional[str] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    complexity_score: Optional[float] = None
    navigation_context: Dict[str, Any] = None

    # ADHD optimizations
    cognitive_load: float = 0.5
    adhd_friendly_summary: Optional[str] = None
    requires_focus: bool = False

    def __post_init__(self):
        if self.navigation_context is None:
            self.navigation_context = {}


class ClaudeContextIntegration:
    """
    Integration layer between Serena and claude-context for enhanced code intelligence.

    Features:
    - Calls claude-context for semantic code search
    - Enhances search results with navigation intelligence
    - Adds LSP-based symbol information and structure analysis
    - Provides ADHD-optimized result presentation
    - Caches enhanced results for performance
    """

    def __init__(
        self,
        config: ClaudeContextConfig,
        navigation_cache,  # Serena's NavigationCache
        lsp_wrapper      # Serena's EnhancedLSPWrapper
    ):
        self.config = config
        self.navigation_cache = navigation_cache
        self.lsp_wrapper = lsp_wrapper

        # MCP client for claude-context communication
        self.mcp_client: Optional[McpClient] = None

        # Enhancement state
        self.enhancement_stats = {
            "searches_enhanced": 0,
            "symbols_analyzed": 0,
            "navigation_additions": 0,
            "cache_hits": 0,
            "mcp_calls_made": 0,
            "performance_violations": 0,
            "prefetch_operations": 0,
            "prefetch_hits": 0
        }

        # Intelligent prefetching
        self.prefetch_enabled = True
        self.prefetch_queue = asyncio.Queue(maxsize=10)
        self.prefetch_task = None
        self.recent_navigation_patterns = []
        self.current_context_files = set()  # Files in current work context

    async def initialize(self) -> None:
        """Initialize claude-context integration."""
        logger.info("🔗 Initializing claude-context integration...")

        # Create MCP client for claude-context communication
        self.mcp_client = McpClient(
            server_endpoint=self.config.mcp_endpoint,
            timeout=self.config.timeout,
            max_concurrent_requests=self.config.max_concurrent_requests,
            performance_target_ms=self.config.performance_target_ms
        )

        # Initialize MCP client (includes connectivity test)
        await self.mcp_client.initialize()

        # Start intelligent prefetching background task
        if self.prefetch_enabled:
            self.prefetch_task = asyncio.create_task(self._prefetch_worker())
            logger.info("🔮 Intelligent prefetching started")

        logger.info("✅ Claude-context MCP integration ready!")


    # Enhanced Semantic Search

    async def enhanced_semantic_search(
        self,
        query: str,
        workspace_path: str,
        limit: int = 10,
        include_navigation: bool = True,
        adhd_optimized: bool = True
    ) -> List[SemanticSearchResult]:
        """
        Perform semantic search using claude-context, enhanced with navigation intelligence.

        Args:
            query: Search query
            workspace_path: Workspace to search in
            limit: Maximum results
            include_navigation: Add LSP navigation information
            adhd_optimized: Apply ADHD-friendly optimizations

        Returns:
            Enhanced semantic search results
        """
        try:
            # Check cache first
            cache_key = f"enhanced_search:{hash(query)}:{limit}"
            if self.config.cache_results:
                cached_results = await self.navigation_cache.get_navigation_result(cache_key)
                if cached_results:
                    self.enhancement_stats["cache_hits"] += 1
                    logger.debug(f"🎯 Cache hit: enhanced search for '{query[:30]}...'")
                    return [SemanticSearchResult(**result) for result in cached_results]

            # Call claude-context for semantic search
            semantic_results = await self._call_claude_context_search(
                query, workspace_path, limit, extension_filter=None
            )

            if not semantic_results:
                return []

            # Enhance results with navigation intelligence
            enhanced_results = []

            for result in semantic_results:
                enhanced_result = await self._enhance_search_result(
                    result, include_navigation, adhd_optimized
                )
                enhanced_results.append(enhanced_result)

            # Cache enhanced results
            if self.config.cache_results:
                cache_data = [result.__dict__ for result in enhanced_results]
                await self.navigation_cache.cache_navigation_result(
                    cache_key, cache_data, self.config.cache_ttl
                )

            self.enhancement_stats["searches_enhanced"] += 1
            logger.info(f"🔍 Enhanced semantic search: {len(enhanced_results)} results for '{query[:30]}...'")

            return enhanced_results

        except Exception as e:
            logger.error(f"Enhanced semantic search failed: {e}")
            return []

    async def _call_claude_context_search(
        self,
        query: str,
        workspace_path: str,
        limit: int,
        extension_filter: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Call claude-context MCP server for semantic search."""
        try:
            if not self.mcp_client:
                raise Exception("MCP client not initialized")

            # Ensure workspace is indexed before searching
            indexing_status = await self.mcp_client.get_indexing_status(workspace_path)

            if not indexing_status.success or not indexing_status.data:
                # Try to index the workspace first
                logger.info(f"📋 Indexing workspace: {workspace_path}")
                index_response = await self.mcp_client.index_codebase(
                    workspace_path=workspace_path,
                    force=False,
                    splitter="ast"  # Use AST splitter for better code understanding
                )

                if not index_response.success:
                    logger.error(f"Failed to index workspace: {index_response.error}")
                    return []

            # Perform semantic search
            search_response = await self.mcp_client.search_code(
                workspace_path=workspace_path,
                query=query,
                limit=limit,
                extension_filter=extension_filter
            )

            self.enhancement_stats["mcp_calls_made"] += 1

            # Track performance violations
            if search_response.duration_ms > self.config.performance_target_ms:
                self.enhancement_stats["performance_violations"] += 1

            if search_response.success and search_response.data:
                results = search_response.data

                # Convert to expected format if needed
                formatted_results = []
                for result in results:
                    formatted_result = {
                        "content": result.get("content", ""),
                        "file_path": result.get("file_path", result.get("path", "")),
                        "relevance_score": result.get("score", result.get("relevance_score", 0.5)),
                        "chunk_id": result.get("chunk_id", result.get("id", "")),
                        "line_start": result.get("line_start"),
                        "line_end": result.get("line_end")
                    }
                    formatted_results.append(formatted_result)

                logger.debug(
                    f"🔍 Claude-context search: {len(formatted_results)} results for '{query[:30]}...'"
                    f" ({search_response.duration_ms:.1f}ms)"
                )
                return formatted_results

            else:
                logger.warning(f"Claude-context search failed: {search_response.error}")
                return []

        except Exception as e:
            logger.error(f"Claude-context search call failed: {e}")
            return []

    async def _enhance_search_result(
        self,
        semantic_result: Dict[str, Any],
        include_navigation: bool,
        adhd_optimized: bool
    ) -> SemanticSearchResult:
        """Enhance semantic search result with navigation intelligence."""
        try:
            file_path = semantic_result.get("file_path", "")
            content = semantic_result.get("content", "")

            # Create base enhanced result
            enhanced_result = SemanticSearchResult(
                content=content,
                file_path=file_path,
                relevance_score=semantic_result.get("relevance_score", 0.5),
                chunk_id=semantic_result.get("chunk_id", "")
            )

            # Add navigation intelligence if requested
            if include_navigation and file_path:
                navigation_info = await self._analyze_navigation_context(file_path, content)
                enhanced_result.symbol_type = navigation_info.get("symbol_type")
                enhanced_result.function_name = navigation_info.get("function_name")
                enhanced_result.class_name = navigation_info.get("class_name")
                enhanced_result.navigation_context = navigation_info.get("context", {})

                self.enhancement_stats["navigation_additions"] += 1

            # Add ADHD optimizations if requested
            if adhd_optimized:
                adhd_info = await self._apply_adhd_optimizations(enhanced_result)
                enhanced_result.cognitive_load = adhd_info.get("cognitive_load", 0.5)
                enhanced_result.adhd_friendly_summary = adhd_info.get("summary")
                enhanced_result.requires_focus = adhd_info.get("requires_focus", False)

            return enhanced_result

        except Exception as e:
            logger.error(f"Result enhancement failed: {e}")
            # Return basic result on enhancement failure
            return SemanticSearchResult(
                content=semantic_result.get("content", ""),
                file_path=semantic_result.get("file_path", ""),
                relevance_score=semantic_result.get("relevance_score", 0.5),
                chunk_id=semantic_result.get("chunk_id", "")
            )

    async def _analyze_navigation_context(
        self,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """Analyze navigation context for search result."""
        try:
            navigation_info = {
                "symbol_type": None,
                "function_name": None,
                "class_name": None,
                "context": {}
            }

            # Use LSP to get symbol information
            if self.lsp_wrapper:
                # Get file symbols to understand context
                language = self.lsp_wrapper._detect_file_language(file_path)
                if language:
                    symbols = await self.lsp_wrapper.get_document_symbols(file_path, language)

                    if symbols and symbols.result:
                        # Find relevant symbols in the content area
                        relevant_symbols = self._find_relevant_symbols(content, symbols.result)

                        if relevant_symbols:
                            # Get the most relevant symbol
                            primary_symbol = relevant_symbols[0]
                            navigation_info.update({
                                "symbol_type": self._get_symbol_type_name(primary_symbol.get("kind", 0)),
                                "function_name": primary_symbol.get("name") if primary_symbol.get("kind") in [6, 12] else None,
                                "class_name": primary_symbol.get("name") if primary_symbol.get("kind") == 5 else None,
                                "context": {
                                    "symbols_in_file": len(symbols.result),
                                    "relevant_symbols": len(relevant_symbols),
                                    "file_language": language
                                }
                            })

                            self.enhancement_stats["symbols_analyzed"] += 1

            return navigation_info

        except Exception as e:
            logger.error(f"Navigation context analysis failed: {e}")
            return {"symbol_type": None, "function_name": None, "class_name": None, "context": {}}

    def _find_relevant_symbols(self, content: str, symbols: List[Dict]) -> List[Dict]:
        """Find symbols relevant to the search result content."""
        try:
            relevant_symbols = []

            # Simple relevance: check if symbol name appears in content
            for symbol in symbols:
                symbol_name = symbol.get("name", "")
                if symbol_name and symbol_name.lower() in content.lower():
                    relevant_symbols.append(symbol)

            # Sort by symbol kind importance (functions > variables > etc.)
            importance_order = {5: 1, 6: 2, 12: 3, 13: 4, 14: 5}  # Class, Function, Method, Variable, Constant
            relevant_symbols.sort(key=lambda s: importance_order.get(s.get("kind", 0), 10))

            return relevant_symbols[:3]  # Top 3 most relevant

        except Exception:
            return []

    def _get_symbol_type_name(self, kind: int) -> str:
        """Convert LSP symbol kind to readable name."""
        kind_names = {
            1: "file", 2: "module", 3: "namespace", 4: "package", 5: "class",
            6: "method", 7: "property", 8: "field", 9: "constructor", 10: "enum",
            11: "interface", 12: "function", 13: "variable", 14: "constant"
        }
        return kind_names.get(kind, "unknown")

    async def _apply_adhd_optimizations(
        self,
        result: SemanticSearchResult
    ) -> Dict[str, Any]:
        """Apply ADHD-friendly optimizations to search result."""
        try:
            content = result.content
            file_path = result.file_path

            # Calculate cognitive load based on content complexity
            content_length = len(content)
            content_complexity = self._assess_content_complexity(content)

            # Base cognitive load
            cognitive_load = min(
                (content_length / 500.0) * 0.4 +  # Length factor
                content_complexity * 0.6,          # Complexity factor
                1.0
            )

            # Generate ADHD-friendly summary
            summary = self._generate_adhd_summary(content, file_path)

            # Determine if focus is required
            requires_focus = (
                cognitive_load > 0.7 or
                content_length > 300 or
                "complex" in content.lower()
            )

            return {
                "cognitive_load": cognitive_load,
                "summary": summary,
                "requires_focus": requires_focus,
                "adhd_guidance": self._generate_adhd_guidance(cognitive_load, requires_focus)
            }

        except Exception as e:
            logger.error(f"ADHD optimization failed: {e}")
            return {"cognitive_load": 0.5, "summary": None, "requires_focus": False}

    def _assess_content_complexity(self, content: str) -> float:
        """Assess cognitive complexity of content."""
        try:
            complexity_indicators = [
                "async", "await", "lambda", "decorator", "@",
                "try", "except", "finally", "with",
                "class", "def", "import", "from"
            ]

            indicator_count = sum(1 for indicator in complexity_indicators if indicator in content.lower())
            return min(indicator_count / 10.0, 1.0)  # Normalize to 0-1

        except Exception:
            return 0.5

    def _generate_adhd_summary(self, content: str, file_path: str) -> str:
        """Generate ADHD-friendly summary of content."""
        try:
            file_name = Path(file_path).name

            # Extract first meaningful line or function definition
            lines = content.split('\n')
            first_meaningful_line = next(
                (line.strip() for line in lines if line.strip() and not line.strip().startswith('#')),
                ""
            )

            if "def " in first_meaningful_line:
                return f"📍 Function in {file_name}: {first_meaningful_line[:60]}..."
            elif "class " in first_meaningful_line:
                return f"📍 Class in {file_name}: {first_meaningful_line[:60]}..."
            elif first_meaningful_line:
                return f"📍 Code in {file_name}: {first_meaningful_line[:60]}..."
            else:
                return f"📍 Content in {file_name}"

        except Exception:
            return f"📍 Code content"

    def _generate_adhd_guidance(self, cognitive_load: float, requires_focus: bool) -> str:
        """Generate ADHD-friendly guidance for result."""
        if requires_focus:
            return "🎯 Complex content - consider reviewing during peak focus time"
        elif cognitive_load > 0.5:
            return "🧠 Moderate complexity - good for focused work sessions"
        else:
            return "✅ Straightforward content - good for any energy level"

    # Integration Methods

    async def search_with_navigation_context(
        self,
        query: str,
        workspace_path: str,
        current_file: Optional[str] = None,
        limit: int = 10
    ) -> List[SemanticSearchResult]:
        """
        Search with additional navigation context for better results.

        If current_file is provided, bias results toward related files and symbols.
        """
        try:
            # Get base semantic search results from claude-context
            base_results = await self.enhanced_semantic_search(
                query, workspace_path, limit * 2  # Get extra for filtering
            )

            # If current file provided, enhance with contextual relevance
            if current_file and base_results:
                contextualized_results = await self._add_navigation_context(
                    base_results, current_file, workspace_path
                )
                # Re-sort by enhanced relevance
                contextualized_results.sort(
                    key=lambda r: (r.relevance_score * 0.7 +
                                 r.navigation_context.get("contextual_relevance", 0) * 0.3),
                    reverse=True
                )
                return contextualized_results[:limit]

            return base_results[:limit]

        except Exception as e:
            logger.error(f"Context-aware search failed: {e}")
            return []

    async def _add_navigation_context(
        self,
        results: List[SemanticSearchResult],
        current_file: str,
        workspace_path: str
    ) -> List[SemanticSearchResult]:
        """Add navigation context relevance to search results."""
        try:
            current_file_path = Path(current_file)

            for result in results:
                result_file_path = Path(result.file_path)

                # Calculate contextual relevance
                contextual_relevance = 0.0

                # Same directory bonus
                if result_file_path.parent == current_file_path.parent:
                    contextual_relevance += 0.4

                # Same file type bonus
                if result_file_path.suffix == current_file_path.suffix:
                    contextual_relevance += 0.2

                # Import relationship bonus (would require deeper analysis)
                # For now, simple name similarity
                if current_file_path.stem in result_file_path.stem or result_file_path.stem in current_file_path.stem:
                    contextual_relevance += 0.3

                # Update navigation context
                result.navigation_context["contextual_relevance"] = min(contextual_relevance, 1.0)
                result.navigation_context["current_file_relation"] = self._describe_file_relation(
                    current_file_path, result_file_path
                )

            return results

        except Exception as e:
            logger.error(f"Navigation context addition failed: {e}")
            return results

    def _describe_file_relation(self, current_file: Path, result_file: Path) -> str:
        """Describe relationship between current file and result file."""
        try:
            if current_file == result_file:
                return "same_file"
            elif current_file.parent == result_file.parent:
                return "same_directory"
            elif current_file.suffix == result_file.suffix:
                return "same_language"
            elif any(part in result_file.parts for part in current_file.parts):
                return "related_path"
            else:
                return "different_area"

        except Exception:
            return "unknown"

    # Public API Methods

    async def search_similar_functions(
        self,
        function_name: str,
        workspace_path: str,
        limit: int = 5
    ) -> List[SemanticSearchResult]:
        """Find functions similar to the given function name."""
        query = f"function {function_name} similar implementation"
        return await self.enhanced_semantic_search(query, workspace_path, limit)

    async def search_usage_examples(
        self,
        symbol_name: str,
        workspace_path: str,
        limit: int = 8
    ) -> List[SemanticSearchResult]:
        """Find usage examples for a symbol."""
        query = f"{symbol_name} usage example implementation"
        return await self.enhanced_semantic_search(query, workspace_path, limit)

    async def search_related_patterns(
        self,
        current_file: str,
        workspace_path: str,
        limit: int = 6
    ) -> List[SemanticSearchResult]:
        """Find patterns related to current file."""
        file_content_preview = await self._get_file_content_preview(current_file)
        query = f"similar pattern {file_content_preview}"

        return await self.search_with_navigation_context(
            query, workspace_path, current_file, limit
        )

    # Intelligent Prefetching for ADHD Navigation

    async def _prefetch_worker(self) -> None:
        """Background worker for intelligent prefetching."""
        logger.debug("🔮 Prefetch worker started")

        try:
            while True:
                try:
                    # Wait for prefetch request with timeout
                    prefetch_request = await asyncio.wait_for(
                        self.prefetch_queue.get(),
                        timeout=5.0
                    )

                    await self._execute_prefetch_request(prefetch_request)
                    self.prefetch_queue.task_done()

                except asyncio.TimeoutError:
                    # No prefetch requests, continue monitoring
                    continue
                except Exception as e:
                    logger.error(f"Prefetch worker error: {e}")
                    await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            logger.debug("🔮 Prefetch worker stopped")

    async def _execute_prefetch_request(self, request: Dict[str, Any]) -> None:
        """Execute a prefetch request in the background."""
        try:
            request_type = request.get("type")
            priority = request.get("priority", "low")

            if request_type == "semantic_search":
                await self._prefetch_semantic_search(request)
            elif request_type == "related_files":
                await self._prefetch_related_files(request)
            elif request_type == "similar_functions":
                await self._prefetch_similar_functions(request)

            self.enhancement_stats["prefetch_operations"] += 1
            logger.debug(f"🔮 Prefetch completed: {request_type}")

        except Exception as e:
            logger.error(f"Prefetch execution failed: {e}")

    async def _prefetch_semantic_search(self, request: Dict[str, Any]) -> None:
        """Prefetch semantic search results."""
        query = request.get("query")
        workspace_path = request.get("workspace_path")

        if not query or not workspace_path:
            return

        # Check if already cached
        cache_key = f"enhanced_search:{hash(query)}:10"
        cached_result = await self.navigation_cache.get_navigation_result(cache_key)

        if cached_result:
            # Already cached, count as prefetch hit
            self.enhancement_stats["prefetch_hits"] += 1
            return

        # Perform search with reduced priority
        try:
            results = await self.enhanced_semantic_search(
                query=query,
                workspace_path=workspace_path,
                limit=5,  # Smaller limit for prefetch
                include_navigation=True,
                adhd_optimized=True
            )

            logger.debug(f"🔮 Prefetched search: '{query[:30]}...' - {len(results)} results")

        except Exception as e:
            logger.debug(f"Prefetch search failed: {e}")

    async def _prefetch_related_files(self, request: Dict[str, Any]) -> None:
        """Prefetch related files based on current navigation context."""
        current_file = request.get("current_file")
        workspace_path = request.get("workspace_path")

        if not current_file or not workspace_path:
            return

        try:
            # Generate related file search queries
            file_stem = Path(current_file).stem
            file_queries = [
                f"similar to {file_stem}",
                f"imports from {file_stem}",
                f"uses {file_stem}",
                f"related to {file_stem}"
            ]

            # Prefetch searches for related files
            for query in file_queries[:2]:  # Limit to 2 to avoid overwhelming
                await self._prefetch_semantic_search({
                    "query": query,
                    "workspace_path": workspace_path
                })

        except Exception as e:
            logger.debug(f"Related files prefetch failed: {e}")

    async def _prefetch_similar_functions(self, request: Dict[str, Any]) -> None:
        """Prefetch similar functions based on current symbol context."""
        function_name = request.get("function_name")
        workspace_path = request.get("workspace_path")

        if not function_name or not workspace_path:
            return

        try:
            # Search for similar functions
            similar_query = f"function similar to {function_name}"
            await self._prefetch_semantic_search({
                "query": similar_query,
                "workspace_path": workspace_path
            })

        except Exception as e:
            logger.debug(f"Similar functions prefetch failed: {e}")

    def schedule_prefetch(
        self,
        request_type: str,
        priority: str = "low",
        **kwargs
    ) -> bool:
        """Schedule a prefetch operation for background execution."""
        if not self.prefetch_enabled or not self.prefetch_task:
            return False

        try:
            prefetch_request = {
                "type": request_type,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc),
                **kwargs
            }

            # Try to add to queue without blocking
            try:
                self.prefetch_queue.put_nowait(prefetch_request)
                logger.debug(f"🔮 Scheduled prefetch: {request_type}")
                return True
            except asyncio.QueueFull:
                logger.debug("Prefetch queue full, skipping request")
                return False

        except Exception as e:
            logger.error(f"Failed to schedule prefetch: {e}")
            return False

    def update_navigation_context(
        self,
        current_file: str,
        workspace_path: str,
        symbol_name: str = None,
        navigation_action: str = "navigate"
    ) -> None:
        """Update navigation context and trigger intelligent prefetching."""
        try:
            # Add to current context
            self.current_context_files.add(current_file)

            # Track navigation pattern
            navigation_entry = {
                "file": current_file,
                "symbol": symbol_name,
                "action": navigation_action,
                "timestamp": datetime.now(timezone.utc)
            }

            self.recent_navigation_patterns.append(navigation_entry)

            # Keep pattern history manageable (ADHD optimization)
            if len(self.recent_navigation_patterns) > 20:
                self.recent_navigation_patterns = self.recent_navigation_patterns[-15:]

            # Trigger prefetching based on navigation patterns
            self._trigger_intelligent_prefetching(current_file, workspace_path, symbol_name)

        except Exception as e:
            logger.error(f"Failed to update navigation context: {e}")

    def _trigger_intelligent_prefetching(
        self,
        current_file: str,
        workspace_path: str,
        symbol_name: str = None
    ) -> None:
        """Trigger intelligent prefetching based on navigation patterns."""
        try:
            # Pattern 1: Related files in same directory
            self.schedule_prefetch(
                "related_files",
                priority="medium",
                current_file=current_file,
                workspace_path=workspace_path
            )

            # Pattern 2: Similar functions if symbol provided
            if symbol_name:
                self.schedule_prefetch(
                    "similar_functions",
                    priority="low",
                    function_name=symbol_name,
                    workspace_path=workspace_path
                )

            # Pattern 3: Contextual searches based on file name
            file_stem = Path(current_file).stem
            if len(file_stem) > 3:  # Meaningful file names only
                contextual_queries = [
                    f"tests for {file_stem}",
                    f"documentation {file_stem}",
                    f"examples {file_stem}"
                ]

                for query in contextual_queries[:1]:  # Just one contextual search
                    self.schedule_prefetch(
                        "semantic_search",
                        priority="low",
                        query=query,
                        workspace_path=workspace_path
                    )

        except Exception as e:
            logger.debug(f"Prefetch triggering failed: {e}")

    def check_prefetch_hit(self, query: str, workspace_path: str) -> bool:
        """Check if a search result was prefetched (for analytics)."""
        cache_key = f"enhanced_search:{hash(query)}:10"

        # This is a heuristic - if it's in cache and we recently prefetched, count as hit
        # Real implementation would need more sophisticated tracking

        # Simple check: if any recent prefetch patterns match this query
        query_lower = query.lower()
        for pattern in self.recent_navigation_patterns[-5:]:  # Last 5 patterns
            if pattern.get("file", "").lower() in query_lower:
                self.enhancement_stats["prefetch_hits"] += 1
                return True

        return False

    # Utility Methods

    async def _get_file_content_preview(self, file_path: str) -> str:
        """Get a brief preview of file content for search context."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first few lines for context
                lines = []
                for i, line in enumerate(f):
                    if i >= 10:  # First 10 lines max
                        break
                    if line.strip() and not line.strip().startswith('#'):
                        lines.append(line.strip())

                return ' '.join(lines)[:200]  # First 200 chars

        except Exception:
            return Path(file_path).stem  # Fallback to filename

    # Health and Monitoring

    async def get_integration_health(self) -> Dict[str, Any]:
        """Get integration health status."""
        try:
            if not self.mcp_client:
                return {
                    "status": "🔴 Not Initialized",
                    "error": "MCP client not initialized"
                }

            # Get MCP client health
            mcp_health = await self.mcp_client.health_check()
            claude_context_healthy = mcp_health.get("server_healthy", False)

            return {
                "claude_context_connection": "🟢 Connected" if claude_context_healthy else "🔴 Disconnected",
                "enhancement_stats": self.enhancement_stats,
                "mcp_performance": {
                    "average_response_time_ms": mcp_health.get("stats", {}).get("average_response_time_ms", 0),
                    "performance_target_ms": self.config.performance_target_ms,
                    "target_violations": self.enhancement_stats["performance_violations"],
                    "success_rate": mcp_health.get("success_rate", 0)
                },
                "configuration": {
                    "endpoint": self.config.mcp_endpoint,
                    "timeout": self.config.timeout,
                    "caching_enabled": self.config.cache_results,
                    "performance_target_ms": self.config.performance_target_ms
                },
                "status": "🚀 Enhancing" if claude_context_healthy else "⚠️ Limited"
            }

        except Exception as e:
            logger.error(f"Integration health check failed: {e}")
            return {"status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Close claude-context integration."""
        # Stop prefetching
        if self.prefetch_task:
            self.prefetch_task.cancel()
            try:
                await self.prefetch_task
            except asyncio.CancelledError:
                pass

        # Close MCP client
        if self.mcp_client:
            await self.mcp_client.close()

        logger.info("🔌 Claude-context integration closed")


# Factory function for easy initialization
async def create_claude_context_integration(
    config: ClaudeContextConfig,
    navigation_cache,
    lsp_wrapper
) -> ClaudeContextIntegration:
    """Create and initialize claude-context integration."""
    integration = ClaudeContextIntegration(config, navigation_cache, lsp_wrapper)
    await integration.initialize()
    return integration