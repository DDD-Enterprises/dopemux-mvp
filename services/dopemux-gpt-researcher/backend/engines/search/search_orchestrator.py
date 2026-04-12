"""
Search Orchestration Engine - Intelligent Multi-Engine Search Coordination

Orchestrates search across multiple engines with intelligent routing, parallel execution,
and ADHD-optimized result combination. Implements various search strategies based on
query classification and user preferences.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

from .base_adapter import (
    BaseSearchAdapter,
    SearchResult,
    SearchResultType,
    SourceQuality,
    SearchMetadata
)

logger = logging.getLogger(__name__)


class SearchStrategy(str, Enum):
    """Search strategy types for different use cases"""
    DOCUMENTATION_FIRST = "documentation_first"    # Prioritize official docs
    RECENT_DEVELOPMENTS = "recent_developments"     # Focus on current info
    COMPREHENSIVE = "comprehensive"                 # Use all engines
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"    # Detailed technical search
    QUICK_OVERVIEW = "quick_overview"              # Fast, summarized results
    TROUBLESHOOTING = "troubleshooting"            # Problem-solving focus
    COMPARISON = "comparison"                       # Technology comparison


@dataclass
class SearchConfig:
    """Configuration for search orchestration"""
    strategy: SearchStrategy = SearchStrategy.COMPREHENSIVE
    max_total_results: int = 15
    max_per_engine: int = 5
    enable_parallel: bool = True
    deduplicate_results: bool = True
    adhd_mode: bool = True
    timeout_seconds: int = 30


@dataclass
class EngineWeight:
    """Weight configuration for search engines"""
    exa: float = 1.0
    tavily: float = 1.0
    perplexity: float = 1.0
    context7: float = 1.0


class SearchOrchestrator:
    """
    Orchestrates search across multiple engines with intelligent routing

    Features:
    - Strategy-based engine selection
    - Parallel search execution
    - ADHD-optimized result combination
    - Intelligent deduplication
    - Progressive disclosure
    """

    def __init__(self, engines: Dict[str, BaseSearchAdapter], **kwargs):
        """
        Initialize search orchestrator

        Args:
            engines: Dictionary of engine name -> adapter
            **kwargs: Configuration options
        """
        self.engines = engines
        self.config = SearchConfig(**kwargs)

        # Strategy definitions
        self.strategy_configs = self._initialize_strategy_configs()

        # Result deduplication tracking
        self._seen_urls = set()
        self._seen_content_hashes = set()

    def _initialize_strategy_configs(self) -> Dict[SearchStrategy, Dict[str, Any]]:
        """Initialize configuration for each search strategy"""

        return {
            SearchStrategy.DOCUMENTATION_FIRST: {
                'engines': ['context7', 'exa', 'tavily'],
                'weights': EngineWeight(context7=2.0, exa=1.5, tavily=1.0, perplexity=0.5),
                'result_types': [SearchResultType.DOCUMENTATION, SearchResultType.API_REFERENCE],
                'max_per_engine': 4,
                'parallel': True
            },

            SearchStrategy.RECENT_DEVELOPMENTS: {
                'engines': ['perplexity', 'tavily', 'exa'],
                'weights': EngineWeight(perplexity=2.0, tavily=1.5, exa=1.0, context7=0.5),
                'result_types': [SearchResultType.NEWS_ARTICLE, SearchResultType.BLOG_POST],
                'max_per_engine': 5,
                'parallel': True,
                'date_filter': 'last_month'
            },

            SearchStrategy.COMPREHENSIVE: {
                'engines': ['exa', 'tavily', 'perplexity', 'context7'],
                'weights': EngineWeight(exa=1.2, tavily=1.2, perplexity=1.0, context7=1.5),
                'result_types': None,  # All types
                'max_per_engine': 4,
                'parallel': True
            },

            SearchStrategy.TECHNICAL_DEEP_DIVE: {
                'engines': ['context7', 'exa', 'tavily', 'perplexity'],
                'weights': EngineWeight(context7=2.0, exa=1.8, tavily=1.2, perplexity=1.0),
                'result_types': [
                    SearchResultType.DOCUMENTATION,
                    SearchResultType.API_REFERENCE,
                    SearchResultType.CODE_EXAMPLE,
                    SearchResultType.GITHUB_ISSUE
                ],
                'max_per_engine': 6,
                'parallel': True
            },

            SearchStrategy.QUICK_OVERVIEW: {
                'engines': ['perplexity', 'context7'],
                'weights': EngineWeight(perplexity=1.5, context7=1.2, exa=0.8, tavily=0.5),
                'result_types': [SearchResultType.DOCUMENTATION],
                'max_per_engine': 3,
                'parallel': True,
                'summarize': True
            },

            SearchStrategy.TROUBLESHOOTING: {
                'engines': ['tavily', 'perplexity', 'exa'],
                'weights': EngineWeight(tavily=1.8, perplexity=1.5, exa=1.0, context7=0.8),
                'result_types': [
                    SearchResultType.STACK_OVERFLOW,
                    SearchResultType.GITHUB_ISSUE,
                    SearchResultType.BLOG_POST
                ],
                'max_per_engine': 5,
                'parallel': True,
                'domain_filter': ['stackoverflow.com', 'github.com']
            },

            SearchStrategy.COMPARISON: {
                'engines': ['perplexity', 'exa', 'tavily'],
                'weights': EngineWeight(perplexity=1.8, exa=1.2, tavily=1.0, context7=0.8),
                'result_types': [
                    SearchResultType.BLOG_POST,
                    SearchResultType.DOCUMENTATION,
                    SearchResultType.NEWS_ARTICLE
                ],
                'max_per_engine': 4,
                'parallel': True
            }
        }

    async def search(self,
                    query: str,
                    strategy: Optional[SearchStrategy] = None,
                    max_results: Optional[int] = None,
                    **kwargs) -> Tuple[List[SearchResult], SearchMetadata]:
        """
        Execute orchestrated search across multiple engines

        Args:
            query: Search query
            strategy: Search strategy to use
            max_results: Maximum results to return
            **kwargs: Additional search parameters

        Returns:
            Tuple of (results, combined_metadata)
        """

        start_time = datetime.now()

        try:
            # Determine strategy
            if not strategy:
                strategy = self.config.strategy

            # Get strategy configuration
            strategy_config = self.strategy_configs.get(strategy,
                                                      self.strategy_configs[SearchStrategy.COMPREHENSIVE])

            # Override config with kwargs
            effective_config = self._merge_config(strategy_config, kwargs)

            # Select engines for this search
            selected_engines = self._select_engines(strategy, effective_config)

            # Execute searches
            if effective_config.get('parallel', True):
                engine_results = await self._execute_parallel_search(
                    query, selected_engines, effective_config
                )
            else:
                engine_results = await self._execute_sequential_search(
                    query, selected_engines, effective_config
                )

            # Combine and rank results
            combined_results = self._combine_results(engine_results, strategy_config)

            # Apply ADHD optimizations
            optimized_results = self._apply_adhd_optimizations(combined_results, effective_config)

            # Limit final results
            max_total = max_results or self.config.max_total_results
            final_results = optimized_results[:max_total]

            # Create combined metadata
            combined_metadata = self._create_combined_metadata(
                engine_results, start_time, strategy, len(final_results)
            )

            logger.info(f"Orchestrated search completed: {len(final_results)} results from {len(selected_engines)} engines")

            return final_results, combined_metadata

        except Exception as e:
            logger.error(f"Search orchestration failed: {e}")

            # Return empty results with error metadata
            error_metadata = SearchMetadata(
                engine_name="orchestrator",
                query_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                total_results=0,
                results_returned=0,
                search_strategy=strategy.value if strategy else "unknown"
            )

            return [], error_metadata

    def _merge_config(self, strategy_config: Dict[str, Any], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge strategy config with user-provided kwargs"""

        merged = strategy_config.copy()

        # Override with user preferences
        if 'result_types' in kwargs and kwargs['result_types']:
            merged['result_types'] = kwargs['result_types']

        if 'date_filter' in kwargs:
            merged['date_filter'] = kwargs['date_filter']

        if 'domain_filter' in kwargs:
            merged['domain_filter'] = kwargs['domain_filter']

        if 'max_per_engine' in kwargs:
            merged['max_per_engine'] = kwargs['max_per_engine']

        return merged

    def _select_engines(self, strategy: SearchStrategy, config: Dict[str, Any]) -> List[str]:
        """Select engines based on strategy and availability"""

        strategy_engines = config.get('engines', list(self.engines.keys()))
        available_engines = []

        for engine_name in strategy_engines:
            if engine_name in self.engines:
                available_engines.append(engine_name)
            else:
                logger.warning(f"Engine '{engine_name}' not available, skipping")

        if not available_engines:
            logger.warning("No engines available, falling back to all available engines")
            available_engines = list(self.engines.keys())

        return available_engines

    async def _execute_parallel_search(self,
                                     query: str,
                                     engines: List[str],
                                     config: Dict[str, Any]) -> Dict[str, Tuple[List[SearchResult], SearchMetadata]]:
        """Execute searches in parallel across selected engines"""

        tasks = []
        engine_configs = {}

        # Prepare tasks for each engine
        for engine_name in engines:
            if engine_name not in self.engines:
                continue

            engine = self.engines[engine_name]

            # Prepare engine-specific parameters
            search_params = {
                'max_results': config.get('max_per_engine', self.config.max_per_engine),
                'result_types': config.get('result_types'),
                'date_filter': config.get('date_filter'),
                'domain_filter': config.get('domain_filter')
            }

            # Remove None values
            search_params = {k: v for k, v in search_params.items() if v is not None}

            # Create task
            task = asyncio.create_task(
                self._safe_engine_search(engine, query, search_params),
                name=f"search_{engine_name}"
            )
            tasks.append((engine_name, task))

        # Execute all tasks with timeout
        timeout = config.get('timeout_seconds', self.config.timeout_seconds)

        try:
            # Wait for all tasks to complete or timeout
            results = await asyncio.wait_for(
                asyncio.gather(*[task for _, task in tasks], return_exceptions=True),
                timeout=timeout
            )

            # Combine results
            engine_results = {}
            for (engine_name, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"Engine '{engine_name}' failed: {result}")
                    continue

                engine_results[engine_name] = result

        except asyncio.TimeoutError:
            logger.warning(f"Search timeout after {timeout} seconds")

            # Get partial results from completed tasks
            engine_results = {}
            for engine_name, task in tasks:
                if task.done() and not task.exception():
                    try:
                        engine_results[engine_name] = task.result()
                    except Exception as e:
                        logger.error(f"Failed to get result from {engine_name}: {e}")

        return engine_results

    async def _execute_sequential_search(self,
                                       query: str,
                                       engines: List[str],
                                       config: Dict[str, Any]) -> Dict[str, Tuple[List[SearchResult], SearchMetadata]]:
        """Execute searches sequentially across selected engines"""

        engine_results = {}

        for engine_name in engines:
            if engine_name not in self.engines:
                continue

            try:
                engine = self.engines[engine_name]

                search_params = {
                    'max_results': config.get('max_per_engine', self.config.max_per_engine),
                    'result_types': config.get('result_types'),
                    'date_filter': config.get('date_filter'),
                    'domain_filter': config.get('domain_filter')
                }

                # Remove None values
                search_params = {k: v for k, v in search_params.items() if v is not None}

                result = await self._safe_engine_search(engine, query, search_params)
                engine_results[engine_name] = result

            except Exception as e:
                logger.error(f"Sequential search failed for engine '{engine_name}': {e}")
                continue

        return engine_results

    async def _safe_engine_search(self,
                                engine: BaseSearchAdapter,
                                query: str,
                                params: Dict[str, Any]) -> Tuple[List[SearchResult], SearchMetadata]:
        """Execute search with error handling"""

        try:
            return await engine.search(query, **params)
        except Exception as e:
            logger.error(f"Engine search failed: {e}")

            # Return empty results with error metadata
            error_metadata = SearchMetadata(
                engine_name=engine.engine_name,
                query_time_ms=0,
                total_results=0,
                results_returned=0
            )

            return [], error_metadata

    def _combine_results(self,
                        engine_results: Dict[str, Tuple[List[SearchResult], SearchMetadata]],
                        strategy_config: Dict[str, Any]) -> List[SearchResult]:
        """Combine results from multiple engines with intelligent ranking"""

        all_results = []
        weights = strategy_config.get('weights', EngineWeight())

        # Collect all results with engine weights
        for engine_name, (results, metadata) in engine_results.items():
            engine_weight = getattr(weights, engine_name, 1.0)

            for result in results:
                # Apply engine weight to relevance score
                result.relevance_score *= engine_weight

                # Add engine metadata
                if not result.engine_metadata:
                    result.engine_metadata = {}
                result.engine_metadata['source_engine'] = engine_name
                result.engine_metadata['engine_weight'] = engine_weight

                all_results.append(result)

        # Deduplicate if enabled
        if self.config.deduplicate_results:
            all_results = self._deduplicate_results(all_results)

        # Sort by combined relevance score
        all_results.sort(key=lambda r: r.relevance_score, reverse=True)

        return all_results

    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL and content similarity"""

        unique_results = []
        seen_urls = set()
        seen_content_hashes = set()

        for result in results:
            # Check URL duplication
            if result.url in seen_urls:
                continue

            # Check content similarity (simple hash-based approach)
            content_hash = hash(result.content[:500]) if result.content else hash(result.title)
            if content_hash in seen_content_hashes:
                continue

            # Check title similarity (simple approach)
            title_words = set(result.title.lower().split())
            is_similar_title = False

            for existing_result in unique_results:
                existing_words = set(existing_result.title.lower().split())
                overlap = len(title_words & existing_words)

                if overlap > max(3, len(title_words) * 0.7):  # High title overlap
                    is_similar_title = True
                    break

            if is_similar_title:
                continue

            # Add to unique results
            unique_results.append(result)
            seen_urls.add(result.url)
            seen_content_hashes.add(content_hash)

        return unique_results

    def _apply_adhd_optimizations(self,
                                results: List[SearchResult],
                                config: Dict[str, Any]) -> List[SearchResult]:
        """Apply ADHD-specific optimizations to results"""

        if not self.config.adhd_mode:
            return results

        optimized_results = []

        for result in results:
            # Ensure summaries are concise
            if not result.summary or len(result.summary) > 200:
                result.summary = self._generate_adhd_summary(result)

            # Ensure key points are available
            if not result.key_points:
                result.key_points = self._extract_adhd_key_points(result)

            # Limit code snippets for cognitive load
            if len(result.code_snippets) > 3:
                result.code_snippets = result.code_snippets[:3]

            # Assess reading time and complexity
            if result.reading_time_minutes == 0:
                result.reading_time_minutes = self._estimate_reading_time(result)

            if result.complexity_level == "medium":
                result.complexity_level = self._assess_adhd_complexity(result)

            optimized_results.append(result)

        # Sort by ADHD-friendliness (shorter, simpler content first for initial results)
        adhd_sorted = sorted(optimized_results, key=self._adhd_friendliness_score, reverse=True)

        return adhd_sorted

    def _generate_adhd_summary(self, result: SearchResult) -> str:
        """Generate ADHD-friendly summary (concise, action-oriented)"""

        content = result.content or result.title

        # Extract first meaningful sentence
        sentences = content.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 150:
                return sentence + '.'

        # Fallback to truncated content
        return content[:150] + '...' if len(content) > 150 else content

    def _extract_adhd_key_points(self, result: SearchResult) -> List[str]:
        """Extract ADHD-friendly key points (max 3, action-oriented)"""

        content = result.content or result.title

        # Look for action words and important concepts
        import re

        # Find sentences with action words
        action_patterns = [
            r'[^.]*(?:install|configure|setup|create|build|implement|use)[^.]*\.',
            r'[^.]*(?:step \d+|first|then|next|finally)[^.]*\.',
            r'[^.]*(?:important|note|warning|tip)[^.]*\.'
        ]

        key_points = []
        for pattern in action_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            key_points.extend(matches[:2])

            if len(key_points) >= 3:
                break

        # Clean up and limit
        cleaned_points = []
        for point in key_points[:3]:
            point = point.strip()
            if len(point) > 10:
                cleaned_points.append(point)

        return cleaned_points

    def _estimate_reading_time(self, result: SearchResult) -> int:
        """Estimate reading time in minutes (ADHD-adjusted)"""

        content = result.content or result.title
        word_count = len(content.split())

        # ADHD-adjusted reading speed (slower than typical 200 WPM)
        reading_speed = 150  # WPM for technical content

        return max(1, word_count // reading_speed)

    def _assess_adhd_complexity(self, result: SearchResult) -> str:
        """Assess complexity level for ADHD users"""

        content = result.content or ""

        # Count complexity indicators
        complexity_indicators = 0

        # Technical jargon
        jargon_words = ['architecture', 'implementation', 'framework', 'abstraction', 'polymorphism']
        complexity_indicators += sum(1 for word in jargon_words if word in content.lower())

        # Code blocks
        complexity_indicators += min(3, len(result.code_snippets))

        # Length
        if len(content.split()) > 500:
            complexity_indicators += 2
        elif len(content.split()) > 200:
            complexity_indicators += 1

        # Determine complexity level
        if complexity_indicators <= 1:
            return "low"
        elif complexity_indicators <= 3:
            return "medium"
        else:
            return "high"

    def _adhd_friendliness_score(self, result: SearchResult) -> float:
        """Calculate ADHD-friendliness score (higher is better)"""

        score = 50  # Base score

        # Reading time penalty (shorter is better for initial consumption)
        if result.reading_time_minutes <= 3:
            score += 20
        elif result.reading_time_minutes <= 5:
            score += 10
        elif result.reading_time_minutes > 10:
            score -= 10

        # Complexity bonus (simpler is better initially)
        complexity_bonus = {"low": 15, "medium": 5, "high": -5}
        score += complexity_bonus.get(result.complexity_level, 0)

        # Summary quality bonus
        if result.summary and len(result.summary) < 150:
            score += 10

        # Key points bonus
        score += len(result.key_points) * 3

        # Source quality bonus
        quality_bonus = {
            SourceQuality.EXCELLENT: 15,
            SourceQuality.GOOD: 10,
            SourceQuality.MODERATE: 5,
            SourceQuality.QUESTIONABLE: -5
        }
        score += quality_bonus.get(result.source_quality, 0)

        return score

    def _create_combined_metadata(self,
                                engine_results: Dict[str, Tuple[List[SearchResult], SearchMetadata]],
                                start_time: datetime,
                                strategy: SearchStrategy,
                                final_count: int) -> SearchMetadata:
        """Create combined metadata from all engine results"""

        total_query_time = (datetime.now() - start_time).total_seconds() * 1000
        total_results = sum(len(results) for results, _ in engine_results.values())

        # Collect engine metadata
        engine_stats = {}
        for engine_name, (results, metadata) in engine_results.items():
            engine_stats[engine_name] = {
                'results_count': len(results),
                'query_time_ms': metadata.query_time_ms,
                'rate_limit_remaining': metadata.rate_limit_remaining
            }

        return SearchMetadata(
            engine_name="orchestrator",
            query_time_ms=total_query_time,
            total_results=total_results,
            results_returned=final_count,
            search_strategy=strategy.value,
            filters_applied=[f"strategy: {strategy.value}"],
            engine_metadata=engine_stats
        )

    async def get_strategy_recommendation(self,
                                        query: str,
                                        user_context: Optional[Dict[str, Any]] = None) -> SearchStrategy:
        """Recommend search strategy based on query analysis"""

        query_lower = query.lower()

        # Documentation/implementation queries
        if any(word in query_lower for word in ['how to', 'documentation', 'api', 'reference']):
            return SearchStrategy.DOCUMENTATION_FIRST

        # Recent/current information queries
        if any(word in query_lower for word in ['latest', 'recent', 'current', '2024', '2025', 'new']):
            return SearchStrategy.RECENT_DEVELOPMENTS

        # Problem-solving queries
        if any(word in query_lower for word in ['error', 'problem', 'issue', 'fix', 'debug', 'troubleshoot']):
            return SearchStrategy.TROUBLESHOOTING

        # Comparison queries
        if any(word in query_lower for word in ['vs', 'versus', 'compare', 'comparison', 'difference']):
            return SearchStrategy.COMPARISON

        # Quick information queries
        if any(word in query_lower for word in ['what is', 'quick', 'overview', 'summary']):
            return SearchStrategy.QUICK_OVERVIEW

        # Complex architecture queries
        if any(word in query_lower for word in ['architecture', 'design', 'pattern', 'system', 'enterprise']):
            return SearchStrategy.TECHNICAL_DEEP_DIVE

        # Default to comprehensive
        return SearchStrategy.COMPREHENSIVE

    def get_available_strategies(self) -> List[str]:
        """Get list of available search strategies"""
        return [strategy.value for strategy in SearchStrategy]

    def get_strategy_info(self, strategy: SearchStrategy) -> Dict[str, Any]:
        """Get information about a specific search strategy"""
        config = self.strategy_configs.get(strategy, {})

        return {
            'name': strategy.value,
            'engines': config.get('engines', []),
            'result_types': [rt.value for rt in config.get('result_types', [])] if config.get('result_types') else [],
            'description': self._get_strategy_description(strategy)
        }

    def _get_strategy_description(self, strategy: SearchStrategy) -> str:
        """Get human-readable description of search strategy"""

        descriptions = {
            SearchStrategy.DOCUMENTATION_FIRST: "Prioritizes official documentation and API references",
            SearchStrategy.RECENT_DEVELOPMENTS: "Focuses on current information and recent developments",
            SearchStrategy.COMPREHENSIVE: "Uses all engines for complete coverage",
            SearchStrategy.TECHNICAL_DEEP_DIVE: "Detailed technical search for complex topics",
            SearchStrategy.QUICK_OVERVIEW: "Fast, summarized results for quick understanding",
            SearchStrategy.TROUBLESHOOTING: "Problem-solving focus with Stack Overflow and GitHub",
            SearchStrategy.COMPARISON: "Technology comparison and evaluation"
        }

        return descriptions.get(strategy, "Custom search strategy")