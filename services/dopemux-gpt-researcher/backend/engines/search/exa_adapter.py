"""
Exa Search Adapter - Semantic Search for Technical Documentation

Exa provides high-quality semantic search optimized for technical content.
Excellent for finding authoritative documentation, API references, and technical guides.
Particularly strong for developer-focused queries and code-related research.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from .base_adapter import (
    BaseSearchAdapter,
    SearchResult,
    SearchResultType,
    SourceQuality,
    SearchMetadata
)

logger = logging.getLogger(__name__)


class ExaSearchAdapter(BaseSearchAdapter):
    """
    Exa search engine adapter for semantic technical search

    Optimized for:
    - Technical documentation
    - API references
    - Code examples and tutorials
    - Developer resources
    - High-quality technical content
    """

    def __init__(self, api_key: str, **kwargs):
        """
        Initialize Exa search adapter

        Args:
            api_key: Exa API key
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)
        self.base_url = "https://api.exa.ai"
        self._session = None

        # Exa-specific configuration
        self.default_search_type = kwargs.get('search_type', 'auto')  # auto, neural, keyword
        self.include_domains = kwargs.get('include_domains', [])
        self.exclude_domains = kwargs.get('exclude_domains', [])
        self.use_autoprompt = kwargs.get('use_autoprompt', True)

        # Quality domain mappings for technical content
        self.quality_domains = {
            SourceQuality.EXCELLENT: [
                'docs.python.org', 'developer.mozilla.org', 'docs.microsoft.com',
                'docs.aws.amazon.com', 'cloud.google.com', 'docs.github.com',
                'kubernetes.io', 'react.dev', 'nextjs.org', 'docs.docker.com'
            ],
            SourceQuality.GOOD: [
                'stackoverflow.com', 'github.com', 'dev.to', 'medium.com',
                'freecodecamp.org', 'css-tricks.com', 'smashingmagazine.com',
                'auth0.com', 'twilio.com', 'stripe.com'
            ],
            SourceQuality.MODERATE: [
                'blogs.', 'tutorial', '.edu', 'geeksforgeeks.org',
                'w3schools.com', 'tutorialspoint.com'
            ]
        }

    @property
    def engine_name(self) -> str:
        return "exa"

    @property
    def max_results_per_request(self) -> int:
        return 20  # Exa's current limit

    @property
    def supports_date_filtering(self) -> bool:
        return True

    @property
    def supports_domain_filtering(self) -> bool:
        return True

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with proper headers"""
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'DopemuxResearcher/1.0'
        }

        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)

        return aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout
        )

    async def _execute_search(self,
                             query: str,
                             max_results: int,
                             result_types: Optional[List[SearchResultType]],
                             date_filter: Optional[str],
                             domain_filter: Optional[List[str]],
                             **kwargs) -> List[SearchResult]:
        """Execute Exa search with semantic optimization"""

        if not self._session:
            self._session = await self._create_session()

        # Build Exa search request
        search_params = self._build_search_params(
            query, max_results, result_types, date_filter, domain_filter, **kwargs
        )

        try:
            # Execute search request
            async with self._session.post(f"{self.base_url}/search", json=search_params) as response:
                if response.status == 429:
                    # Rate limited - wait and retry once
                    await asyncio.sleep(1)
                    async with self._session.post(f"{self.base_url}/search", json=search_params) as retry_response:
                        response = retry_response

                response.raise_for_status()
                data = await response.json()

                # Update rate limit info
                self._rate_limit_remaining = response.headers.get('x-ratelimit-remaining')
                self._last_request_time = datetime.now()

            # Parse and convert results
            results = self._parse_exa_results(data, query)

            logger.info(f"Exa search returned {len(results)} results for query: {query[:50]}...")
            return results

        except aiohttp.ClientError as e:
            logger.error(f"Exa API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Exa search error: {e}")
            return []

    def _build_search_params(self,
                           query: str,
                           max_results: int,
                           result_types: Optional[List[SearchResultType]],
                           date_filter: Optional[str],
                           domain_filter: Optional[List[str]],
                           **kwargs) -> Dict[str, Any]:
        """Build Exa API search parameters"""

        params = {
            "query": query,
            "num_results": min(max_results, self.max_results_per_request),
            "search_type": kwargs.get('search_type', self.default_search_type),
            "use_autoprompt": self.use_autoprompt,
            "contents": {
                "text": {
                    "max_characters": 2000,  # Limit for ADHD optimization
                    "include_html_tags": False
                }
            },
            "summary": {
                "query": f"Summarize this content for: {query}"
            }
        }

        # Add domain filtering
        include_domains = list(self.include_domains)
        exclude_domains = list(self.exclude_domains)

        if domain_filter:
            include_domains.extend(domain_filter)

        # Add result type specific domain preferences
        if result_types:
            type_domains = self._get_domains_for_result_types(result_types)
            include_domains.extend(type_domains)

        if include_domains:
            params["include_domains"] = include_domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains

        # Add date filtering
        if date_filter:
            params["start_published_date"] = self._parse_date_filter(date_filter)

        # Add category filtering based on result types
        if result_types:
            params["category"] = self._map_result_types_to_categories(result_types)

        return params

    def _get_domains_for_result_types(self, result_types: List[SearchResultType]) -> List[str]:
        """Get preferred domains for specific result types"""
        domains = []

        type_domain_map = {
            SearchResultType.DOCUMENTATION: [
                'docs.', 'developer.', 'api.', 'guide.'
            ],
            SearchResultType.CODE_EXAMPLE: [
                'github.com', 'codepen.io', 'jsfiddle.net', 'codesandbox.io'
            ],
            SearchResultType.API_REFERENCE: [
                'docs.', 'api.', 'developer.', 'reference.'
            ],
            SearchResultType.TUTORIAL: [
                'tutorial', 'learn', 'guide', 'course'
            ],
            SearchResultType.STACK_OVERFLOW: [
                'stackoverflow.com', 'stackexchange.com'
            ]
        }

        for result_type in result_types:
            domains.extend(type_domain_map.get(result_type, []))

        return list(set(domains))  # Remove duplicates

    def _parse_date_filter(self, date_filter: str) -> str:
        """Parse date filter into Exa format"""
        try:
            if date_filter.lower() == 'last_month':
                date = datetime.now() - timedelta(days=30)
            elif date_filter.lower() == 'last_week':
                date = datetime.now() - timedelta(days=7)
            elif date_filter.lower() == 'last_year':
                date = datetime.now() - timedelta(days=365)
            else:
                # Try to parse as ISO date
                date = datetime.fromisoformat(date_filter.replace('Z', '+00:00'))

            return date.strftime('%Y-%m-%d')
        except:
            # If parsing fails, return recent date
            return (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    def _map_result_types_to_categories(self, result_types: List[SearchResultType]) -> str:
        """Map result types to Exa categories"""
        if SearchResultType.DOCUMENTATION in result_types:
            return "programming"
        elif SearchResultType.ACADEMIC_PAPER in result_types:
            return "research_paper"
        elif SearchResultType.NEWS_ARTICLE in result_types:
            return "news"
        else:
            return "programming"  # Default for technical content

    def _parse_exa_results(self, data: Dict[str, Any], query: str) -> List[SearchResult]:
        """Parse Exa API response into SearchResult objects"""
        results = []

        exa_results = data.get('results', [])

        for idx, item in enumerate(exa_results):
            try:
                result = self._convert_exa_item_to_search_result(item, query, idx)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse Exa result {idx}: {e}")
                continue

        return results

    def _convert_exa_item_to_search_result(self, item: Dict[str, Any], query: str, index: int) -> Optional[SearchResult]:
        """Convert single Exa result item to SearchResult"""

        try:
            # Extract basic information
            title = item.get('title', 'Untitled')
            url = item.get('url', '')

            # Get content from text or summary
            content = ""
            summary = ""

            text_content = item.get('text', '')
            if text_content:
                content = text_content
                summary = self._generate_summary(content, max_words=30)

            # Use Exa's summary if available
            exa_summary = item.get('summary', '')
            if exa_summary:
                summary = exa_summary

            if not content and not summary:
                # Skip results without content
                return None

            # Determine result type based on URL and content
            result_type = self._classify_result_type(url, content, title)

            # Assess source quality based on domain
            source_quality = self._assess_source_quality(url)

            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(item, query, index)

            # Extract metadata
            published_date = self._parse_published_date(item.get('publishedDate'))
            author = item.get('author', '')

            # Create SearchResult
            result = SearchResult(
                title=title,
                url=url,
                content=content,
                summary=summary,
                result_type=result_type,
                source_quality=source_quality,
                relevance_score=relevance_score,
                published_date=published_date,
                author=author,
                engine_metadata={
                    'exa_id': item.get('id'),
                    'exa_score': item.get('score'),
                    'exa_highlights': item.get('highlights', []),
                    'autoprompt_string': item.get('autopromptString'),
                    'live_crawl': item.get('liveCrawl', False)
                }
            )

            # Extract code snippets and API endpoints
            self._extract_technical_content(result, content)

            return result

        except Exception as e:
            logger.error(f"Error converting Exa item to SearchResult: {e}")
            return None

    def _classify_result_type(self, url: str, content: str, title: str) -> SearchResultType:
        """Classify result type based on URL patterns and content"""

        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()

        # Check domain patterns
        if 'docs.' in domain or 'documentation' in path:
            return SearchResultType.DOCUMENTATION
        elif 'api.' in domain or '/api/' in path or 'reference' in path:
            return SearchResultType.API_REFERENCE
        elif 'github.com' in domain:
            return SearchResultType.GITHUB_ISSUE if '/issues/' in path else SearchResultType.CODE_EXAMPLE
        elif 'stackoverflow.com' in domain:
            return SearchResultType.STACK_OVERFLOW
        elif any(word in domain for word in ['tutorial', 'learn', 'course']):
            return SearchResultType.TUTORIAL
        elif any(word in domain for word in ['blog', 'medium', 'dev.to']):
            return SearchResultType.BLOG_POST

        # Check content patterns
        content_lower = content.lower()
        if 'tutorial' in title.lower() or 'how to' in title.lower():
            return SearchResultType.TUTORIAL
        elif content.count('```') > 0 or content.count('`') > 5:
            return SearchResultType.CODE_EXAMPLE
        elif 'api' in content_lower and ('endpoint' in content_lower or 'method' in content_lower):
            return SearchResultType.API_REFERENCE

        # Default to documentation for technical content
        return SearchResultType.DOCUMENTATION

    def _assess_source_quality(self, url: str) -> SourceQuality:
        """Assess source quality based on domain reputation"""

        domain = urlparse(url).netloc.lower()

        # Check against quality domain lists
        for quality, domains in self.quality_domains.items():
            if any(quality_domain in domain for quality_domain in domains):
                return quality

        # Additional heuristics
        if domain.endswith('.edu') or domain.endswith('.gov'):
            return SourceQuality.EXCELLENT
        elif 'docs.' in domain or 'developer.' in domain:
            return SourceQuality.EXCELLENT
        elif 'github.com' in domain:
            return SourceQuality.GOOD

        return SourceQuality.MODERATE

    def _calculate_relevance_score(self, item: Dict[str, Any], query: str, index: int) -> float:
        """Calculate relevance score with ADHD optimizations"""

        # Start with Exa's score if available
        base_score = item.get('score', 0.5)

        # Adjust based on position (earlier results are generally more relevant)
        position_factor = 1.0 - (index * 0.05)  # Slight penalty for lower positions

        # Bonus for exact query matches in title
        title = item.get('title', '').lower()
        query_words = query.lower().split()
        title_matches = sum(1 for word in query_words if word in title)
        title_bonus = (title_matches / len(query_words)) * 0.2

        # Calculate final score
        relevance_score = min(1.0, base_score * position_factor + title_bonus)

        return relevance_score

    def _parse_published_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse published date from various formats"""
        if not date_str:
            return None

        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If all else fails, try dateutil
            from dateutil import parser
            return parser.parse(date_str)

        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None

    def _extract_technical_content(self, result: SearchResult, content: str):
        """Extract code snippets and API endpoints from content"""

        # Extract code blocks
        import re

        # Find code blocks (```...``` or `...`)
        code_blocks = re.findall(r'```[\s\S]*?```|`[^`\n]+`', content)
        result.code_snippets = [block.strip('`').strip() for block in code_blocks[:3]]  # Limit for ADHD

        # Find API endpoints (URLs that look like APIs)
        api_patterns = [
            r'https?://[^\s]+/api/[^\s]+',
            r'/api/v?\d*/[^\s]+',
            r'GET|POST|PUT|DELETE\s+/[^\s]+'
        ]

        api_endpoints = []
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            api_endpoints.extend(matches[:2])  # Limit for ADHD

        result.api_endpoints = api_endpoints

    async def get_content_details(self, urls: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get detailed content for specific URLs using Exa's contents API"""

        if not self._session:
            self._session = await self._create_session()

        try:
            params = {
                "ids": urls,
                "contents": {
                    "text": {
                        "max_characters": 5000,
                        "include_html_tags": False
                    },
                    "highlights": {
                        "num_sentences": 3,
                        "query": "technical implementation details"
                    }
                }
            }

            async with self._session.post(f"{self.base_url}/contents", json=params) as response:
                response.raise_for_status()
                data = await response.json()

                return {item['url']: item for item in data.get('contents', [])}

        except Exception as e:
            logger.error(f"Exa contents API error: {e}")
            return {}

    async def find_similar_content(self, url: str, max_results: int = 5) -> List[SearchResult]:
        """Find content similar to a given URL using Exa's find_similar API"""

        if not self._session:
            self._session = await self._create_session()

        try:
            params = {
                "url": url,
                "num_results": max_results,
                "contents": {
                    "text": {
                        "max_characters": 2000
                    }
                }
            }

            async with self._session.post(f"{self.base_url}/findSimilar", json=params) as response:
                response.raise_for_status()
                data = await response.json()

                return self._parse_exa_results(data, f"similar to {url}")

        except Exception as e:
            logger.error(f"Exa find_similar API error: {e}")
            return []