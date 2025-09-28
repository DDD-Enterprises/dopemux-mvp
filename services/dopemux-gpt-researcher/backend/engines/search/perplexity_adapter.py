"""
Perplexity Search Adapter - AI-Powered Real-Time Search with Citations

Perplexity provides AI-powered search with real-time web crawling and intelligent summarization.
Excellent for getting current information with authoritative citations and ADHD-friendly summaries.
Particularly strong for research questions and up-to-date technical information.
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


class PerplexitySearchAdapter(BaseSearchAdapter):
    """
    Perplexity search engine adapter for AI-powered real-time search

    Optimized for:
    - AI-summarized research answers
    - Real-time current information
    - Authoritative citations
    - Research questions
    - ADHD-friendly summaries
    """

    def __init__(self, api_key: str, **kwargs):
        """
        Initialize Perplexity search adapter

        Args:
            api_key: Perplexity API key
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)
        self.base_url = "https://api.perplexity.ai"
        self._session = None

        # Perplexity-specific configuration
        self.model = kwargs.get('model', 'llama-3.1-sonar-small-128k-online')
        self.temperature = kwargs.get('temperature', 0.2)  # Lower for factual accuracy
        self.max_tokens = kwargs.get('max_tokens', 1000)
        self.return_citations = kwargs.get('return_citations', True)
        self.return_images = kwargs.get('return_images', False)
        self.return_related_questions = kwargs.get('return_related_questions', True)

        # Available Perplexity models for different needs
        self.models = {
            'fast': 'llama-3.1-sonar-small-128k-online',
            'balanced': 'llama-3.1-sonar-large-128k-online',
            'comprehensive': 'llama-3.1-sonar-huge-128k-online'
        }

        # Quality assessment for common technical domains
        self.quality_domains = {
            SourceQuality.EXCELLENT: [
                'docs.python.org', 'developer.mozilla.org', 'docs.microsoft.com',
                'docs.aws.amazon.com', 'cloud.google.com', 'docs.github.com',
                'kubernetes.io', 'react.dev', 'nextjs.org', 'docs.docker.com',
                'arxiv.org', 'acm.org', 'ieee.org', 'nature.com', 'science.org'
            ],
            SourceQuality.GOOD: [
                'stackoverflow.com', 'github.com', 'dev.to', 'medium.com',
                'freecodecamp.org', 'auth0.com', 'stripe.com', 'digitalocean.com',
                'techcrunch.com', 'arstechnica.com', 'theverge.com'
            ],
            SourceQuality.MODERATE: [
                'blogs.', 'tutorial', '.edu', 'geeksforgeeks.org',
                'w3schools.com', 'tutorialspoint.com', 'codecademy.com'
            ]
        }

    @property
    def engine_name(self) -> str:
        return "perplexity"

    @property
    def max_results_per_request(self) -> int:
        return 10  # Perplexity focuses on quality over quantity

    @property
    def supports_date_filtering(self) -> bool:
        return True  # Through query enhancement

    @property
    def supports_domain_filtering(self) -> bool:
        return True  # Through query enhancement

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session with proper headers"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'DopemuxResearcher/1.0'
        }

        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for AI processing

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
        """Execute Perplexity search with AI-powered summarization"""

        if not self._session:
            self._session = await self._create_session()

        # Build Perplexity chat completion request
        chat_params = self._build_chat_params(
            query, max_results, result_types, date_filter, domain_filter, **kwargs
        )

        try:
            # Execute chat completion request (Perplexity uses chat format)
            async with self._session.post(f"{self.base_url}/chat/completions", json=chat_params) as response:
                if response.status == 429:
                    # Rate limited - wait and retry once
                    await asyncio.sleep(3)
                    async with self._session.post(f"{self.base_url}/chat/completions", json=chat_params) as retry_response:
                        response = retry_response

                response.raise_for_status()
                data = await response.json()

                # Update rate limit info (if available)
                self._rate_limit_remaining = response.headers.get('x-ratelimit-remaining')
                self._last_request_time = datetime.now()

            # Parse and convert results
            results = self._parse_perplexity_response(data, query)

            logger.info(f"Perplexity search returned {len(results)} results for query: {query[:50]}...")
            return results

        except aiohttp.ClientError as e:
            logger.error(f"Perplexity API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Perplexity search error: {e}")
            return []

    def _build_chat_params(self,
                          query: str,
                          max_results: int,
                          result_types: Optional[List[SearchResultType]],
                          date_filter: Optional[str],
                          domain_filter: Optional[List[str]],
                          **kwargs) -> Dict[str, Any]:
        """Build Perplexity chat completion parameters"""

        # Enhance query with search context
        enhanced_query = self._enhance_query_for_search(query, result_types, date_filter, domain_filter)

        # Select model based on complexity
        model = kwargs.get('model', self._select_model_for_query(query, result_types))

        params = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": self._get_system_prompt(result_types)
                },
                {
                    "role": "user",
                    "content": enhanced_query
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "return_citations": self.return_citations,
            "return_images": self.return_images,
            "return_related_questions": self.return_related_questions
        }

        return params

    def _get_system_prompt(self, result_types: Optional[List[SearchResultType]]) -> str:
        """Get system prompt optimized for ADHD and result types"""

        base_prompt = """You are a helpful research assistant providing concise, accurate information with authoritative citations.

ADHD Optimization Guidelines:
- Provide clear, well-structured responses
- Use bullet points and numbered lists where helpful
- Lead with the most important information
- Include specific examples when relevant
- Keep explanations concise but comprehensive

Always cite your sources with URLs where possible."""

        # Add result type specific instructions
        if result_types:
            if SearchResultType.CODE_EXAMPLE in result_types:
                base_prompt += "\n\nFocus on providing working code examples with explanations."
            elif SearchResultType.TUTORIAL in result_types:
                base_prompt += "\n\nProvide step-by-step instructions and learning resources."
            elif SearchResultType.API_REFERENCE in result_types:
                base_prompt += "\n\nFocus on API documentation, endpoints, and usage examples."
            elif SearchResultType.DOCUMENTATION in result_types:
                base_prompt += "\n\nProvide official documentation links and authoritative guides."

        return base_prompt

    def _enhance_query_for_search(self,
                                query: str,
                                result_types: Optional[List[SearchResultType]],
                                date_filter: Optional[str],
                                domain_filter: Optional[List[str]]) -> str:
        """Enhance query with search context and filters"""

        enhanced = query

        # Add result type context
        if result_types:
            if SearchResultType.CODE_EXAMPLE in result_types:
                enhanced += " with code examples and implementation details"
            elif SearchResultType.TUTORIAL in result_types:
                enhanced += " with tutorial and step-by-step guide"
            elif SearchResultType.API_REFERENCE in result_types:
                enhanced += " with API documentation and reference"
            elif SearchResultType.DOCUMENTATION in result_types:
                enhanced += " with official documentation"

        # Add recency requirements
        if date_filter:
            if date_filter.lower() in ['last_week', 'recent']:
                enhanced += " (focus on very recent information from 2024-2025)"
            elif date_filter.lower() == 'last_month':
                enhanced += " (focus on recent information from 2024-2025)"
            elif date_filter.lower() == 'last_year':
                enhanced += " (focus on current information from 2024-2025)"

        # Add domain preferences
        if domain_filter:
            domain_context = " ".join(domain_filter)
            enhanced += f" (prioritize information from {domain_context})"

        # Add citation requirement
        enhanced += "\n\nPlease provide detailed citations with URLs for all information."

        return enhanced

    def _select_model_for_query(self, query: str, result_types: Optional[List[SearchResultType]]) -> str:
        """Select appropriate Perplexity model based on query complexity"""

        # Simple queries use fast model
        if len(query.split()) < 5:
            return self.models['fast']

        # Complex research or architectural queries use comprehensive model
        complex_keywords = ['architecture', 'design', 'compare', 'analysis', 'comprehensive', 'detailed']
        if any(keyword in query.lower() for keyword in complex_keywords):
            return self.models['comprehensive']

        # Code and tutorial queries use balanced model
        if result_types:
            if any(rt in result_types for rt in [SearchResultType.CODE_EXAMPLE, SearchResultType.TUTORIAL, SearchResultType.API_REFERENCE]):
                return self.models['balanced']

        return self.models['balanced']  # Default to balanced

    def _parse_perplexity_response(self, data: Dict[str, Any], query: str) -> List[SearchResult]:
        """Parse Perplexity chat completion response into SearchResult objects"""
        results = []

        try:
            # Get the main response
            choices = data.get('choices', [])
            if not choices:
                return results

            choice = choices[0]
            message = choice.get('message', {})
            content = message.get('content', '')

            # Get citations
            citations = data.get('citations', [])

            # Create main summary result
            main_result = self._create_summary_result(content, query, citations)
            if main_result:
                results.append(main_result)

            # Create individual results from citations
            for idx, citation in enumerate(citations[:9]):  # Limit for ADHD optimization
                try:
                    citation_result = self._create_citation_result(citation, query, idx, content)
                    if citation_result:
                        results.append(citation_result)
                except Exception as e:
                    logger.warning(f"Failed to parse citation {idx}: {e}")
                    continue

            # Add related questions as potential search results
            related_questions = data.get('related_questions', [])
            if related_questions:
                # Store related questions in the main result metadata
                if results:
                    results[0].engine_metadata['related_questions'] = related_questions[:3]

        except Exception as e:
            logger.error(f"Error parsing Perplexity response: {e}")

        return results

    def _create_summary_result(self, content: str, query: str, citations: List[Dict]) -> Optional[SearchResult]:
        """Create main summary result from Perplexity's AI response"""

        if not content:
            return None

        try:
            # Create summary result
            result = SearchResult(
                title=f"AI Summary: {query}",
                url="https://perplexity.ai",  # Placeholder URL
                content=content,
                summary=self._generate_summary(content, max_words=50),
                result_type=SearchResultType.DOCUMENTATION,  # Summary type
                source_quality=SourceQuality.GOOD,  # AI-generated with citations
                relevance_score=0.95,  # High relevance for AI summary
                published_date=datetime.now(),
                author="Perplexity AI",
                engine_metadata={
                    'is_ai_summary': True,
                    'citation_count': len(citations),
                    'model_used': self.model,
                    'temperature': self.temperature
                }
            )

            # Extract key points from the AI response
            result.key_points = self._extract_key_points_from_ai_response(content)

            # Assess complexity based on content
            result.complexity_level = self._assess_complexity(content)

            return result

        except Exception as e:
            logger.error(f"Error creating summary result: {e}")
            return None

    def _create_citation_result(self, citation: Dict[str, Any], query: str, index: int, ai_content: str) -> Optional[SearchResult]:
        """Create SearchResult from a citation"""

        try:
            # Extract citation information
            url = citation.get('url', '')
            title = citation.get('title', 'Untitled')

            if not url:
                return None

            # Use snippet or extract relevant content
            content = citation.get('snippet', '')
            if not content and 'text' in citation:
                content = citation['text']

            # Generate summary
            summary = self._generate_summary(content, max_words=30) if content else f"Citation for: {query}"

            # Determine result type based on URL
            result_type = self._classify_result_type(url, content, title)

            # Assess source quality
            source_quality = self._assess_source_quality(url)

            # Calculate relevance based on position and domain quality
            relevance_score = self._calculate_citation_relevance(citation, query, index)

            # Create SearchResult
            result = SearchResult(
                title=title,
                url=url,
                content=content,
                summary=summary,
                result_type=result_type,
                source_quality=source_quality,
                relevance_score=relevance_score,
                published_date=self._parse_published_date(citation.get('date')),
                engine_metadata={
                    'citation_index': index,
                    'is_citation': True,
                    'mentioned_in_ai_response': self._is_mentioned_in_response(url, ai_content)
                }
            )

            # Extract technical content if available
            if content:
                self._extract_technical_content(result, content)

            return result

        except Exception as e:
            logger.error(f"Error creating citation result: {e}")
            return None

    def _classify_result_type(self, url: str, content: str, title: str) -> SearchResultType:
        """Classify result type based on URL patterns and content"""

        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()

        # Check domain patterns
        if 'stackoverflow.com' in domain:
            return SearchResultType.STACK_OVERFLOW
        elif 'github.com' in domain:
            return SearchResultType.GITHUB_ISSUE if '/issues/' in path else SearchResultType.CODE_EXAMPLE
        elif 'docs.' in domain or 'documentation' in path:
            return SearchResultType.DOCUMENTATION
        elif 'api.' in domain or '/api/' in path or 'reference' in path:
            return SearchResultType.API_REFERENCE
        elif any(word in domain for word in ['tutorial', 'learn', 'course']):
            return SearchResultType.TUTORIAL
        elif any(word in domain for word in ['blog', 'medium', 'dev.to']):
            return SearchResultType.BLOG_POST
        elif any(word in domain for word in ['arxiv', 'acm', 'ieee', 'nature', 'science']):
            return SearchResultType.ACADEMIC_PAPER
        elif any(word in domain for word in ['news', 'techcrunch', 'arstechnica', 'theverge']):
            return SearchResultType.NEWS_ARTICLE

        # Check content patterns
        if content:
            content_lower = content.lower()
            if content.count('```') > 0 or content.count('`') > 3:
                return SearchResultType.CODE_EXAMPLE
            elif 'tutorial' in title.lower() or 'how to' in title.lower():
                return SearchResultType.TUTORIAL

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
        elif 'docs.' in domain or 'developer.' in domain or 'api.' in domain:
            return SourceQuality.EXCELLENT
        elif any(official in domain for official in ['official', 'main', 'primary']):
            return SourceQuality.GOOD

        return SourceQuality.MODERATE

    def _calculate_citation_relevance(self, citation: Dict[str, Any], query: str, index: int) -> float:
        """Calculate relevance score for citation"""

        # Base score decreases with position
        base_score = 0.9 - (index * 0.1)

        # Domain quality bonus
        url = citation.get('url', '')
        domain_quality = self._assess_source_quality(url)
        quality_bonus = {
            SourceQuality.EXCELLENT: 0.15,
            SourceQuality.GOOD: 0.1,
            SourceQuality.MODERATE: 0.05,
            SourceQuality.QUESTIONABLE: 0
        }.get(domain_quality, 0)

        # Title relevance bonus
        title = citation.get('title', '').lower()
        query_words = query.lower().split()
        title_matches = sum(1 for word in query_words if word in title)
        title_bonus = (title_matches / len(query_words)) * 0.1 if query_words else 0

        relevance_score = min(1.0, base_score + quality_bonus + title_bonus)
        return relevance_score

    def _extract_key_points_from_ai_response(self, content: str) -> List[str]:
        """Extract key points from AI-generated content"""

        import re

        # Look for numbered lists or bullet points
        points = []

        # Find numbered lists
        numbered_points = re.findall(r'\d+\.\s*([^\n]+)', content)
        points.extend(numbered_points[:3])

        # Find bullet points if no numbered lists
        if not points:
            bullet_points = re.findall(r'[•\-\*]\s*([^\n]+)', content)
            points.extend(bullet_points[:3])

        # If no structured lists, take first few sentences
        if not points:
            sentences = re.split(r'[.!?]+', content)
            for sentence in sentences[:3]:
                sentence = sentence.strip()
                if len(sentence) > 20:  # Skip very short sentences
                    points.append(sentence)

        return points[:3]  # Limit for ADHD optimization

    def _is_mentioned_in_response(self, url: str, ai_content: str) -> bool:
        """Check if URL or domain is mentioned in AI response"""
        domain = urlparse(url).netloc.lower()
        return domain in ai_content.lower() or url in ai_content

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

            # Try dateutil if available
            try:
                from dateutil import parser
                return parser.parse(date_str)
            except ImportError:
                return None

        except Exception as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None

    def _extract_technical_content(self, result: SearchResult, content: str):
        """Extract code snippets and API endpoints from content"""

        import re

        # Find code blocks and inline code
        code_blocks = re.findall(r'```[\s\S]*?```|`[^`\n]+`', content)
        result.code_snippets = [block.strip('`').strip() for block in code_blocks[:3]]

        # Find API endpoints
        api_patterns = [
            r'https?://[^\s]+/api/[^\s]+',
            r'/api/v?\d*/[^\s]+',
            r'(GET|POST|PUT|DELETE|PATCH)\s+[/\w\-\.]+',
        ]

        api_endpoints = []
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            api_endpoints.extend(matches[:2])

        result.api_endpoints = list(set(api_endpoints))

    async def ask_question(self, question: str, **kwargs) -> Optional[str]:
        """Ask a direct question and get an AI-powered answer"""

        if not self._session:
            self._session = await self._create_session()

        try:
            params = {
                "model": self.models['balanced'],
                "messages": [
                    {
                        "role": "system",
                        "content": "Provide concise, accurate answers with authoritative citations. Use bullet points for clarity when helpful."
                    },
                    {
                        "role": "user",
                        "content": question + "\n\nPlease provide citations with URLs."
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": min(800, self.max_tokens),
                "return_citations": True
            }

            async with self._session.post(f"{self.base_url}/chat/completions", json=params) as response:
                response.raise_for_status()
                data = await response.json()

                choices = data.get('choices', [])
                if choices:
                    return choices[0].get('message', {}).get('content')

        except Exception as e:
            logger.error(f"Perplexity question API error: {e}")
            return None

        return None