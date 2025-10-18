"""
Base Search Adapter - Unified Interface for Multi-Engine Research

Provides abstract base class and common data structures for all search engine adapters.
Ensures consistent result formatting and ADHD-optimized response handling.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class SearchResultType(str, Enum):
    """Type of search result for different content categories"""
    DOCUMENTATION = "documentation"
    CODE_EXAMPLE = "code_example"
    TUTORIAL = "tutorial"
    API_REFERENCE = "api_reference"
    BLOG_POST = "blog_post"
    STACK_OVERFLOW = "stack_overflow"
    GITHUB_ISSUE = "github_issue"
    NEWS_ARTICLE = "news_article"
    ACADEMIC_PAPER = "academic_paper"
    FORUM_DISCUSSION = "forum_discussion"


class SourceQuality(str, Enum):
    """Quality rating for search result sources"""
    EXCELLENT = "excellent"  # Official docs, authoritative sources
    GOOD = "good"           # Well-known tech sites, GitHub
    MODERATE = "moderate"   # Community sites, blogs
    QUESTIONABLE = "questionable"  # Unknown sources, outdated content


@dataclass
class SearchMetadata:
    """Metadata about search execution and results"""
    engine_name: str
    query_time_ms: float
    total_results: int
    results_returned: int
    api_cost: Optional[float] = None
    rate_limit_remaining: Optional[int] = None
    search_strategy: Optional[str] = None
    filters_applied: List[str] = None


@dataclass
class SearchResult:
    """Standardized search result across all engines"""

    # Core content
    title: str
    url: str
    content: str  # Main text content
    summary: str  # Brief summary for ADHD optimization

    # Classification
    result_type: SearchResultType
    source_quality: SourceQuality
    relevance_score: float  # 0.0-1.0

    # Metadata
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    source_domain: str = ""

    # Technical details
    code_snippets: List[str] = None
    api_endpoints: List[str] = None
    github_stars: Optional[int] = None

    # ADHD optimizations
    reading_time_minutes: int = 0
    complexity_level: str = "medium"  # low, medium, high
    key_points: List[str] = None

    # Engine-specific
    engine_metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize computed fields"""
        if self.code_snippets is None:
            self.code_snippets = []
        if self.api_endpoints is None:
            self.api_endpoints = []
        if self.key_points is None:
            self.key_points = []
        if self.engine_metadata is None:
            self.engine_metadata = {}

        # Extract domain from URL
        if not self.source_domain and self.url:
            try:
                from urllib.parse import urlparse
                self.source_domain = urlparse(self.url).netloc
            except:
                self.source_domain = "unknown"

        # Estimate reading time based on content length
        if not self.reading_time_minutes and self.content:
            words = len(self.content.split())
            self.reading_time_minutes = max(1, words // 200)  # ~200 WPM

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "summary": self.summary,
            "result_type": self.result_type.value,
            "source_quality": self.source_quality.value,
            "relevance_score": self.relevance_score,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "author": self.author,
            "source_domain": self.source_domain,
            "code_snippets": self.code_snippets,
            "api_endpoints": self.api_endpoints,
            "github_stars": self.github_stars,
            "reading_time_minutes": self.reading_time_minutes,
            "complexity_level": self.complexity_level,
            "key_points": self.key_points,
            "engine_metadata": self.engine_metadata
        }


class BaseSearchAdapter(ABC):
    """
    Abstract base class for all search engine adapters

    Provides unified interface for different search engines while maintaining
    their unique capabilities and optimization strategies.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize search adapter

        Args:
            api_key: API key for the search service
            **kwargs: Engine-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        self._session = None
        self._rate_limit_remaining = None
        self._last_request_time = None

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Return the name of this search engine"""
        pass

    @property
    @abstractmethod
    def max_results_per_request(self) -> int:
        """Maximum results this engine can return in one request"""
        pass

    @property
    @abstractmethod
    def supports_date_filtering(self) -> bool:
        """Whether this engine supports filtering by date"""
        pass

    @property
    @abstractmethod
    def supports_domain_filtering(self) -> bool:
        """Whether this engine supports filtering by domain"""
        pass

    async def search(self,
                    query: str,
                    max_results: int = 10,
                    result_types: Optional[List[SearchResultType]] = None,
                    date_filter: Optional[str] = None,
                    domain_filter: Optional[List[str]] = None,
                    **kwargs) -> Tuple[List[SearchResult], SearchMetadata]:
        """
        Execute search query with optional filters

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            result_types: Filter by result types
            date_filter: Date range filter (engine-specific format)
            domain_filter: Limit to specific domains
            **kwargs: Engine-specific parameters

        Returns:
            Tuple of (results, metadata)
        """
        start_time = datetime.now()

        try:
            # Validate inputs
            self._validate_search_params(query, max_results, result_types, date_filter, domain_filter)

            # Apply ADHD optimizations
            optimized_query = self._optimize_query_for_adhd(query)

            # Execute engine-specific search
            results = await self._execute_search(
                optimized_query, max_results, result_types,
                date_filter, domain_filter, **kwargs
            )

            # Post-process results for ADHD optimization
            processed_results = self._post_process_results(results, query)

            # Create metadata
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            metadata = SearchMetadata(
                engine_name=self.engine_name,
                query_time_ms=query_time,
                total_results=len(results),
                results_returned=len(processed_results),
                rate_limit_remaining=self._rate_limit_remaining,
                filters_applied=self._get_applied_filters(result_types, date_filter, domain_filter)
            )

            return processed_results, metadata

        except Exception as e:
            # Create error metadata
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            metadata = SearchMetadata(
                engine_name=self.engine_name,
                query_time_ms=query_time,
                total_results=0,
                results_returned=0
            )

            # Log error but don't break the search orchestrator
            import logging
            logging.error(f"{self.engine_name} search failed: {e}")
            return [], metadata

    @abstractmethod
    async def _execute_search(self,
                             query: str,
                             max_results: int,
                             result_types: Optional[List[SearchResultType]],
                             date_filter: Optional[str],
                             domain_filter: Optional[List[str]],
                             **kwargs) -> List[SearchResult]:
        """
        Engine-specific search implementation

        This method must be implemented by each search adapter to handle
        the actual API calls and result parsing.
        """
        pass

    def _validate_search_params(self, query: str, max_results: int,
                               result_types: Optional[List[SearchResultType]],
                               date_filter: Optional[str],
                               domain_filter: Optional[List[str]]):
        """Validate search parameters"""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if max_results <= 0 or max_results > self.max_results_per_request:
            raise ValueError(f"max_results must be between 1 and {self.max_results_per_request}")

        if date_filter and not self.supports_date_filtering:
            raise ValueError(f"{self.engine_name} does not support date filtering")

        if domain_filter and not self.supports_domain_filtering:
            raise ValueError(f"{self.engine_name} does not support domain filtering")

    def _optimize_query_for_adhd(self, query: str) -> str:
        """
        Optimize query for ADHD-friendly results

        - Simplify complex technical terms
        - Add context keywords for better relevance
        - Remove unnecessary complexity
        """
        # Basic optimization - can be enhanced later
        optimized = query.strip()

        # Add context keywords for better technical results
        if any(term in optimized.lower() for term in ['implement', 'build', 'create']):
            optimized += " tutorial example"

        return optimized

    def _post_process_results(self, results: List[SearchResult], original_query: str) -> List[SearchResult]:
        """
        Post-process results for ADHD optimization

        - Generate summaries if missing
        - Extract key points
        - Assess complexity
        - Rank by relevance and ADHD-friendliness
        """
        processed = []

        for result in results:
            # Generate summary if missing
            if not result.summary and result.content:
                result.summary = self._generate_summary(result.content)

            # Extract key points if missing
            if not result.key_points and result.content:
                result.key_points = self._extract_key_points(result.content)

            # Assess complexity if not set
            if result.complexity_level == "medium":
                result.complexity_level = self._assess_complexity(result.content)

            processed.append(result)

        # Sort by relevance and ADHD-friendliness
        return sorted(processed, key=self._adhd_ranking_score, reverse=True)

    def _generate_summary(self, content: str, max_words: int = 50) -> str:
        """Generate brief summary for ADHD optimization"""
        if not content:
            return ""

        # Simple extractive summary - first meaningful sentences
        sentences = content.split('.')
        summary_parts = []
        word_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            words = sentence.split()
            if word_count + len(words) <= max_words:
                summary_parts.append(sentence)
                word_count += len(words)
            else:
                break

        return '. '.join(summary_parts) + '.' if summary_parts else content[:200] + '...'

    def _extract_key_points(self, content: str, max_points: int = 3) -> List[str]:
        """Extract key points for ADHD-friendly scanning"""
        if not content:
            return []

        # Simple extraction based on common patterns
        points = []

        # Look for bullet points
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                points.append(line.lstrip('•-* '))
                if len(points) >= max_points:
                    break

        # If no bullet points, extract first few sentences
        if not points:
            sentences = content.split('.')
            for sentence in sentences[:max_points]:
                sentence = sentence.strip()
                if len(sentence) > 10:  # Skip very short sentences
                    points.append(sentence)

        return points[:max_points]

    def _assess_complexity(self, content: str) -> str:
        """Assess content complexity for ADHD optimization"""
        if not content:
            return "low"

        # Simple heuristics for complexity assessment
        technical_terms = 0
        code_blocks = content.count('```') + content.count('`')

        technical_keywords = [
            'api', 'algorithm', 'architecture', 'async', 'authentication',
            'configuration', 'deployment', 'framework', 'integration',
            'microservices', 'middleware', 'optimization', 'protocol',
            'scalability', 'security', 'synchronization'
        ]

        for keyword in technical_keywords:
            technical_terms += content.lower().count(keyword)

        # Determine complexity based on technical density
        word_count = len(content.split())
        if word_count == 0:
            return "low"

        technical_density = technical_terms / word_count

        if technical_density > 0.05 or code_blocks > 3:
            return "high"
        elif technical_density > 0.02 or code_blocks > 1:
            return "medium"
        else:
            return "low"

    def _adhd_ranking_score(self, result: SearchResult) -> float:
        """
        Calculate ADHD-optimized ranking score

        Considers:
        - Relevance score (primary)
        - Source quality
        - Reading time (shorter is better for ADHD)
        - Complexity (simpler is better initially)
        """
        score = result.relevance_score * 100  # Base relevance (0-100)

        # Quality bonus
        quality_bonus = {
            SourceQuality.EXCELLENT: 20,
            SourceQuality.GOOD: 10,
            SourceQuality.MODERATE: 0,
            SourceQuality.QUESTIONABLE: -10
        }
        score += quality_bonus.get(result.source_quality, 0)

        # Reading time penalty (prefer shorter content for ADHD)
        if result.reading_time_minutes > 10:
            score -= (result.reading_time_minutes - 10) * 2

        # Complexity adjustment
        complexity_adjustment = {
            "low": 5,
            "medium": 0,
            "high": -5
        }
        score += complexity_adjustment.get(result.complexity_level, 0)

        # Result type bonuses for different contexts
        type_bonus = {
            SearchResultType.DOCUMENTATION: 15,
            SearchResultType.CODE_EXAMPLE: 10,
            SearchResultType.TUTORIAL: 8,
            SearchResultType.API_REFERENCE: 5
        }
        score += type_bonus.get(result.result_type, 0)

        return score

    def _get_applied_filters(self,
                           result_types: Optional[List[SearchResultType]],
                           date_filter: Optional[str],
                           domain_filter: Optional[List[str]]) -> List[str]:
        """Get list of filters that were applied"""
        filters = []

        if result_types:
            filters.append(f"result_types: {[t.value for t in result_types]}")

        if date_filter:
            filters.append(f"date_filter: {date_filter}")

        if domain_filter:
            filters.append(f"domain_filter: {domain_filter}")

        return filters

    async def test_connection(self) -> bool:
        """Test if the search engine is accessible and working"""
        try:
            results, metadata = await self.search("test query", max_results=1)
            return True
        except:
            return False

    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        return {
            "engine": self.engine_name,
            "remaining": self._rate_limit_remaining,
            "last_request": self._last_request_time
        }

    async def __aenter__(self):
        """Async context manager entry"""
        if hasattr(self, '_create_session'):
            self._session = await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session and hasattr(self._session, 'close'):
            await self._session.close()