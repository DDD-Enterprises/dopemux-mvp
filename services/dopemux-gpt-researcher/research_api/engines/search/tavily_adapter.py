"""
Tavily Search Adapter - Developer-Focused Real-Time Search

Tavily provides real-time web search optimized for developers and technical content.
Excellent for finding recent code examples, documentation updates, and Stack Overflow solutions.
Particularly strong for current technology trends and troubleshooting.
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


class TavilySearchAdapter(BaseSearchAdapter):
    """
    Tavily search engine adapter for developer-focused real-time search

    Optimized for:
    - Real-time technical content
    - Stack Overflow and GitHub
    - Recent code examples
    - Documentation updates
    - Developer troubleshooting
    """

    def __init__(self, api_key: str, **kwargs):
        """
        Initialize Tavily search adapter

        Args:
            api_key: Tavily API key
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)
        self.base_url = "https://api.tavily.com"
        self._session = None

        # Tavily-specific configuration
        self.search_depth = kwargs.get('search_depth', 'basic')  # basic, advanced
        self.include_answer = kwargs.get('include_answer', True)
        self.include_raw_content = kwargs.get('include_raw_content', False)
        self.include_domains = kwargs.get('include_domains', [])
        self.exclude_domains = kwargs.get('exclude_domains', [])

        # Developer-focused domain quality mappings
        self.quality_domains = {
            SourceQuality.EXCELLENT: [
                'docs.python.org', 'developer.mozilla.org', 'docs.microsoft.com',
                'docs.aws.amazon.com', 'cloud.google.com', 'docs.github.com',
                'kubernetes.io', 'react.dev', 'nextjs.org', 'docs.docker.com',
                'fastapi.tiangolo.com', 'flask.palletsprojects.com', 'djangoproject.com'
            ],
            SourceQuality.GOOD: [
                'stackoverflow.com', 'github.com', 'dev.to', 'medium.com',
                'freecodecamp.org', 'css-tricks.com', 'auth0.com', 'twilio.com',
                'stripe.com', 'digitalocean.com', 'linode.com', 'heroku.com'
            ],
            SourceQuality.MODERATE: [
                'blogs.', 'tutorial', '.edu', 'geeksforgeeks.org',
                'w3schools.com', 'tutorialspoint.com', 'javatpoint.com',
                'codecademy.com', 'udemy.com'
            ]
        }

        # Developer-focused include domains by default
        if not self.include_domains:
            self.include_domains = [
                'stackoverflow.com', 'github.com', 'docs.', 'developer.',
                'dev.to', 'medium.com', 'freecodecamp.org'
            ]

    @property
    def engine_name(self) -> str:
        return "tavily"

    @property
    def max_results_per_request(self) -> int:
        return 20  # Tavily's current limit

    @property
    def supports_date_filtering(self) -> bool:
        return True  # Through max_results and recency

    @property
    def supports_domain_filtering(self) -> bool:
        return True

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with proper headers"""
        headers = {
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
        """Execute Tavily search with developer optimization"""

        if not self._session:
            self._session = await self._create_session()

        # Build Tavily search request
        search_params = self._build_search_params(
            query, max_results, result_types, date_filter, domain_filter, **kwargs
        )

        try:
            # Execute search request
            async with self._session.post(f"{self.base_url}/search", json=search_params) as response:
                if response.status == 429:
                    # Rate limited - wait and retry once
                    await asyncio.sleep(2)
                    async with self._session.post(f"{self.base_url}/search", json=search_params) as retry_response:
                        response = retry_response

                response.raise_for_status()
                data = await response.json()

                # Update rate limit info (if available)
                self._rate_limit_remaining = response.headers.get('x-ratelimit-remaining')
                self._last_request_time = datetime.now()

            # Parse and convert results
            results = self._parse_tavily_results(data, query)

            logger.info(f"Tavily search returned {len(results)} results for query: {query[:50]}...")
            return results

        except aiohttp.ClientError as e:
            logger.error(f"Tavily API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return []

    def _build_search_params(self,
                           query: str,
                           max_results: int,
                           result_types: Optional[List[SearchResultType]],
                           date_filter: Optional[str],
                           domain_filter: Optional[List[str]],
                           **kwargs) -> Dict[str, Any]:
        """Build Tavily API search parameters"""

        # Enhance query for developer context
        enhanced_query = self._enhance_query_for_developers(query, result_types)

        params = {
            "api_key": self.api_key,
            "query": enhanced_query,
            "search_depth": self.search_depth,
            "include_answer": self.include_answer,
            "include_raw_content": self.include_raw_content,
            "max_results": min(max_results, self.max_results_per_request),
            "include_images": False,  # Focus on text content for developers
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

        # Add date preference (Tavily doesn't have explicit date filtering)
        if date_filter:
            # Add recency keywords to query for recent content
            if date_filter.lower() in ['last_week', 'last_month', 'recent']:
                params["query"] += " recent 2024 2025"

        return params

    def _enhance_query_for_developers(self, query: str, result_types: Optional[List[SearchResultType]]) -> str:
        """Enhance query with developer-focused keywords"""
        enhanced = query

        # Add context based on result types
        if result_types:
            if SearchResultType.CODE_EXAMPLE in result_types:
                enhanced += " code example implementation"
            elif SearchResultType.DOCUMENTATION in result_types:
                enhanced += " documentation guide"
            elif SearchResultType.TUTORIAL in result_types:
                enhanced += " tutorial how to"
            elif SearchResultType.STACK_OVERFLOW in result_types:
                enhanced += " stackoverflow solution"
            elif SearchResultType.API_REFERENCE in result_types:
                enhanced += " API reference documentation"

        # Add programming context if not already present
        if not any(word in query.lower() for word in ['code', 'programming', 'development', 'api', 'function']):
            enhanced += " programming development"

        return enhanced

    def _get_domains_for_result_types(self, result_types: List[SearchResultType]) -> List[str]:
        """Get preferred domains for specific result types"""
        domains = []

        type_domain_map = {
            SearchResultType.DOCUMENTATION: [
                'docs.', 'developer.', 'api.', 'guide.', 'documentation.'
            ],
            SearchResultType.CODE_EXAMPLE: [
                'github.com', 'codepen.io', 'jsfiddle.net', 'codesandbox.io',
                'replit.com', 'stackblitz.com'
            ],
            SearchResultType.API_REFERENCE: [
                'docs.', 'api.', 'developer.', 'reference.'
            ],
            SearchResultType.TUTORIAL: [
                'tutorial', 'learn', 'guide', 'course', 'freecodecamp.org',
                'codecademy.com', 'dev.to'
            ],
            SearchResultType.STACK_OVERFLOW: [
                'stackoverflow.com', 'stackexchange.com'
            ],
            SearchResultType.BLOG_POST: [
                'medium.com', 'dev.to', 'hashnode.com', 'blog.'
            ],
            SearchResultType.GITHUB_ISSUE: [
                'github.com'
            ]
        }

        for result_type in result_types:
            domains.extend(type_domain_map.get(result_type, []))

        return list(set(domains))  # Remove duplicates

    def _parse_tavily_results(self, data: Dict[str, Any], query: str) -> List[SearchResult]:
        """Parse Tavily API response into SearchResult objects"""
        results = []

        tavily_results = data.get('results', [])

        for idx, item in enumerate(tavily_results):
            try:
                result = self._convert_tavily_item_to_search_result(item, query, idx)
                if result:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Failed to parse Tavily result {idx}: {e}")
                continue

        return results

    def _convert_tavily_item_to_search_result(self, item: Dict[str, Any], query: str, index: int) -> Optional[SearchResult]:
        """Convert single Tavily result item to SearchResult"""

        try:
            # Extract basic information
            title = item.get('title', 'Untitled')
            url = item.get('url', '')

            # Get content and summary
            content = item.get('content', '')
            summary = content[:200] + '...' if len(content) > 200 else content

            # Use Tavily's summary if available
            if not summary and 'summary' in item:
                summary = item['summary']

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
            published_date = self._parse_published_date(item.get('published_date'))

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
                engine_metadata={
                    'tavily_score': item.get('score'),
                    'tavily_raw_content': item.get('raw_content'),
                    'is_recent': self._is_recent_content(item),
                    'domain_rank': self._get_domain_rank(url)
                }
            )

            # Extract code snippets and API endpoints
            self._extract_technical_content(result, content)

            return result

        except Exception as e:
            logger.error(f"Error converting Tavily item to SearchResult: {e}")
            return None

    def _classify_result_type(self, url: str, content: str, title: str) -> SearchResultType:
        """Classify result type based on URL patterns and content"""

        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()

        # Check domain patterns
        if 'stackoverflow.com' in domain:
            return SearchResultType.STACK_OVERFLOW
        elif 'github.com' in domain:
            if '/issues/' in path:
                return SearchResultType.GITHUB_ISSUE
            elif any(ext in path for ext in ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs']):
                return SearchResultType.CODE_EXAMPLE
            else:
                return SearchResultType.CODE_EXAMPLE  # Default for GitHub
        elif 'docs.' in domain or 'documentation' in path:
            return SearchResultType.DOCUMENTATION
        elif 'api.' in domain or '/api/' in path or 'reference' in path:
            return SearchResultType.API_REFERENCE
        elif any(word in domain for word in ['tutorial', 'learn', 'course']):
            return SearchResultType.TUTORIAL
        elif any(word in domain for word in ['blog', 'medium', 'dev.to', 'hashnode']):
            return SearchResultType.BLOG_POST

        # Check content patterns
        content_lower = content.lower()
        title_lower = title.lower()

        if 'tutorial' in title_lower or 'how to' in title_lower:
            return SearchResultType.TUTORIAL
        elif content.count('```') > 0 or content.count('`') > 5:
            return SearchResultType.CODE_EXAMPLE
        elif 'api' in content_lower and ('endpoint' in content_lower or 'method' in content_lower):
            return SearchResultType.API_REFERENCE
        elif any(word in title_lower for word in ['error', 'problem', 'issue', 'fix', 'solve']):
            return SearchResultType.STACK_OVERFLOW  # Troubleshooting content

        # Default to documentation for technical content
        return SearchResultType.DOCUMENTATION

    def _assess_source_quality(self, url: str) -> SourceQuality:
        """Assess source quality based on domain reputation"""

        domain = urlparse(url).netloc.lower()

        # Check against quality domain lists
        for quality, domains in self.quality_domains.items():
            if any(quality_domain in domain for quality_domain in domains):
                return quality

        # Additional heuristics for developer content
        if domain.endswith('.edu') or domain.endswith('.gov'):
            return SourceQuality.EXCELLENT
        elif 'docs.' in domain or 'developer.' in domain or 'api.' in domain:
            return SourceQuality.EXCELLENT
        elif 'github.com' in domain:
            return SourceQuality.GOOD
        elif 'stackoverflow.com' in domain:
            return SourceQuality.GOOD
        elif any(word in domain for word in ['official', 'main', 'primary']):
            return SourceQuality.GOOD

        return SourceQuality.MODERATE

    def _calculate_relevance_score(self, item: Dict[str, Any], query: str, index: int) -> float:
        """Calculate relevance score with developer-focused optimization"""

        # Start with base score
        base_score = item.get('score', 0.5)
        if isinstance(base_score, str):
            try:
                base_score = float(base_score)
            except:
                base_score = 0.5

        # Adjust based on position
        position_factor = 1.0 - (index * 0.03)  # Slight penalty for lower positions

        # Bonus for exact query matches in title
        title = item.get('title', '').lower()
        query_words = query.lower().split()
        title_matches = sum(1 for word in query_words if word in title)
        title_bonus = (title_matches / len(query_words)) * 0.15 if query_words else 0

        # Developer content bonus
        developer_bonus = 0
        url = item.get('url', '').lower()
        content = item.get('content', '').lower()

        if any(domain in url for domain in ['stackoverflow.com', 'github.com', 'docs.']):
            developer_bonus += 0.1

        if any(word in content for word in ['code', 'function', 'class', 'method', 'api']):
            developer_bonus += 0.05

        # Recency bonus for technical content
        recency_bonus = 0
        if self._is_recent_content(item):
            recency_bonus = 0.1

        # Calculate final score
        relevance_score = min(1.0, base_score * position_factor + title_bonus + developer_bonus + recency_bonus)

        return relevance_score

    def _is_recent_content(self, item: Dict[str, Any]) -> bool:
        """Check if content is recent (helpful for Tavily's real-time search)"""

        # Check if published date is recent
        published_date = self._parse_published_date(item.get('published_date'))
        if published_date:
            days_old = (datetime.now() - published_date).days
            return days_old <= 365  # Within last year

        # Check for recent keywords in content
        content = item.get('content', '').lower()
        recent_keywords = ['2024', '2025', 'latest', 'recent', 'new', 'updated']

        return any(keyword in content for keyword in recent_keywords)

    def _get_domain_rank(self, url: str) -> int:
        """Get domain authority rank (higher is better)"""
        domain = urlparse(url).netloc.lower()

        # High authority domains
        if any(d in domain for d in ['stackoverflow.com', 'github.com', 'docs.', 'developer.']):
            return 5
        elif any(d in domain for d in ['medium.com', 'dev.to', 'freecodecamp.org']):
            return 4
        elif '.edu' in domain or '.gov' in domain:
            return 5
        else:
            return 3

    def _parse_published_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse published date from various formats"""
        if not date_str:
            return None

        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If all else fails, try dateutil
            try:
                from dateutil import parser
                return parser.parse(date_str)
            except ImportError:
                logger.debug("dateutil not available for date parsing")
                return None

        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None

    def _extract_technical_content(self, result: SearchResult, content: str):
        """Extract code snippets and API endpoints from content"""

        import re

        # Find code blocks (```...``` or `...`)
        code_blocks = re.findall(r'```[\s\S]*?```|`[^`\n]+`', content)
        result.code_snippets = [block.strip('`').strip() for block in code_blocks[:3]]  # Limit for ADHD

        # Find API endpoints and HTTP methods
        api_patterns = [
            r'https?://[^\s]+/api/[^\s]+',
            r'/api/v?\d*/[^\s]+',
            r'(GET|POST|PUT|DELETE|PATCH)\s+[/\w\-\.]+',
            r'[A-Z]+\s+https?://[^\s]+'
        ]

        api_endpoints = []
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if isinstance(matches[0], tuple) if matches else False:
                # Handle tuple results from capturing groups
                api_endpoints.extend([' '.join(match) if isinstance(match, tuple) else match for match in matches[:2]])
            else:
                api_endpoints.extend(matches[:2])  # Limit for ADHD

        result.api_endpoints = list(set(api_endpoints))  # Remove duplicates

        # Extract GitHub stars if it's a GitHub URL
        if 'github.com' in result.url:
            star_match = re.search(r'(\d+)\s*star', content, re.IGNORECASE)
            if star_match:
                try:
                    result.github_stars = int(star_match.group(1))
                except ValueError:
                    pass

    async def get_answer(self, query: str) -> Optional[str]:
        """Get direct answer for a query using Tavily's answer feature"""

        if not self._session:
            self._session = await self._create_session()

        try:
            params = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_raw_content": False,
                "max_results": 5,
                "include_domains": self.include_domains
            }

            async with self._session.post(f"{self.base_url}/search", json=params) as response:
                response.raise_for_status()
                data = await response.json()

                return data.get('answer')

        except Exception as e:
            logger.error(f"Tavily answer API error: {e}")
            return None