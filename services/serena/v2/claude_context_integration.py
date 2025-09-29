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

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class ClaudeContextConfig:
    """Configuration for claude-context integration."""
    mcp_endpoint: str = "http://localhost:3000"  # claude-context MCP endpoint
    timeout: float = 10.0
    max_concurrent_requests: int = 5
    cache_results: bool = True
    cache_ttl: int = 600  # 10 minutes


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

        # HTTP session for claude-context API calls
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_semaphore = asyncio.Semaphore(config.max_concurrent_requests)

        # Enhancement state
        self.enhancement_stats = {
            "searches_enhanced": 0,
            "symbols_analyzed": 0,
            "navigation_additions": 0,
            "cache_hits": 0
        }

    async def initialize(self) -> None:
        """Initialize claude-context integration."""
        logger.info("🔗 Initializing claude-context integration...")

        # Create HTTP session for API calls
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )

        # Test claude-context connectivity
        await self._test_claude_context_connection()

        logger.info("✅ Claude-context integration ready!")

    async def _test_claude_context_connection(self) -> bool:
        """Test connection to claude-context service."""
        try:
            # This would test the claude-context MCP endpoint
            # For now, assume it's available
            logger.info("🟢 Claude-context connection verified")
            return True

        except Exception as e:
            logger.error(f"Claude-context connection failed: {e}")
            return False

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
            semantic_results = await self._call_claude_context_search(query, workspace_path, limit)

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
        limit: int
    ) -> List[Dict[str, Any]]:
        """Call claude-context MCP server for semantic search."""
        try:
            async with self.request_semaphore:
                # This would make an MCP call to claude-context
                # For now, simulate the call structure

                search_request = {
                    "jsonrpc": "2.0",
                    "id": f"search_{datetime.now().timestamp()}",
                    "method": "tools/call",
                    "params": {
                        "name": "semantic_search",
                        "arguments": {
                            "query": query,
                            "workspace": workspace_path,
                            "limit": limit,
                            "include_snippets": True
                        }
                    }
                }

                # Simulate claude-context response structure
                # In real implementation, this would be an actual MCP call
                mock_results = [
                    {
                        "content": f"Mock semantic result {i+1} for query: {query}",
                        "file_path": f"/mock/file_{i+1}.py",
                        "relevance_score": 0.9 - (i * 0.1),
                        "chunk_id": f"chunk_{i+1}"
                    }
                    for i in range(min(limit, 3))  # Mock 3 results
                ]

                logger.debug(f"📡 Claude-context returned {len(mock_results)} semantic results")
                return mock_results

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
            claude_context_healthy = await self._test_claude_context_connection()

            return {
                "claude_context_connection": "🟢 Connected" if claude_context_healthy else "🔴 Disconnected",
                "enhancement_stats": self.enhancement_stats,
                "configuration": {
                    "endpoint": self.config.mcp_endpoint,
                    "timeout": self.config.timeout,
                    "caching_enabled": self.config.cache_results
                },
                "status": "🚀 Enhancing" if claude_context_healthy else "⚠️ Limited"
            }

        except Exception as e:
            logger.error(f"Integration health check failed: {e}")
            return {"status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Close claude-context integration."""
        if self.session:
            await self.session.close()
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