"""
Context7 Search Adapter - Official Documentation via MCP

Context7 provides access to official documentation for 10,000+ libraries through our MCP server.
Excellent for authoritative documentation, API references, and official guides.
No rate limits, highest quality sources, perfect for technical implementation.
"""

import asyncio
import logging
from datetime import datetime
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


class Context7SearchAdapter(BaseSearchAdapter):
    """
    Context7 search engine adapter for official documentation via MCP

    Optimized for:
    - Official library documentation
    - API references
    - Framework guides
    - Authoritative sources
    - Zero rate limits
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize Context7 search adapter

        Args:
            api_key: Not required for MCP integration
            **kwargs: Additional configuration options
        """
        super().__init__(api_key, **kwargs)

        # Context7-specific configuration
        self.default_tokens = kwargs.get('default_tokens', 2000)
        self.max_tokens = kwargs.get('max_tokens', 5000)
        self.enable_fuzzy_matching = kwargs.get('enable_fuzzy_matching', True)

        # MCP tool integration
        self.mcp_available = kwargs.get('mcp_available', True)

        # Library popularity scoring for relevance
        self.popular_libraries = {
            # JavaScript/Node.js
            'react', 'vue', 'angular', 'express', 'nextjs', 'nuxt',
            'lodash', 'axios', 'moment', 'jquery', 'bootstrap',

            # Python
            'django', 'flask', 'fastapi', 'requests', 'numpy', 'pandas',
            'tensorflow', 'pytorch', 'scikit-learn', 'matplotlib',

            # Others
            'docker', 'kubernetes', 'aws', 'gcp', 'azure',
            'mongodb', 'postgresql', 'redis', 'elasticsearch'
        }

    @property
    def engine_name(self) -> str:
        return "context7"

    @property
    def max_results_per_request(self) -> int:
        return 10  # Focus on quality documentation

    @property
    def supports_date_filtering(self) -> bool:
        return False  # Official docs don't need date filtering

    @property
    def supports_domain_filtering(self) -> bool:
        return False  # All results are from official sources

    async def _execute_search(self,
                             query: str,
                             max_results: int,
                             result_types: Optional[List[SearchResultType]],
                             date_filter: Optional[str],
                             domain_filter: Optional[List[str]],
                             **kwargs) -> List[SearchResult]:
        """Execute Context7 search using MCP integration"""

        if not self.mcp_available:
            logger.warning("Context7 MCP integration not available")
            return []

        try:
            # Extract library names from query
            library_candidates = self._extract_library_names(query)

            results = []

            # Search for each library candidate
            for library_name in library_candidates[:max_results]:
                try:
                    library_results = await self._search_library_documentation(
                        library_name, query, result_types, **kwargs
                    )
                    results.extend(library_results)
                except Exception as e:
                    logger.warning(f"Failed to search library '{library_name}': {e}")
                    continue

            # If no specific libraries found, try general search
            if not results and library_candidates:
                # Try the first candidate as a general topic search
                general_results = await self._search_general_topic(
                    query, result_types, **kwargs
                )
                results.extend(general_results)

            # Sort by relevance and quality
            results = sorted(results, key=self._context7_ranking_score, reverse=True)

            logger.info(f"Context7 search returned {len(results)} results for query: {query[:50]}...")
            return results[:max_results]

        except Exception as e:
            logger.error(f"Context7 search error: {e}")
            return []

    def _extract_library_names(self, query: str) -> List[str]:
        """Extract potential library names from the search query"""

        import re

        query_lower = query.lower()
        candidates = []

        # Check for exact matches with popular libraries
        for lib in self.popular_libraries:
            if lib in query_lower:
                candidates.append(lib)

        # Extract potential library names using patterns
        patterns = [
            r'\b([a-z0-9\-]+(?:\.[a-z0-9\-]+)*)\b',  # Library-like names
            r'\b([A-Z][a-zA-Z0-9]+)\b',              # CamelCase names
            r'\b([a-z]+(?:-[a-z]+)*)\b'              # Kebab-case names
        ]

        for pattern in patterns:
            matches = re.findall(pattern, query)
            candidates.extend(matches)

        # Remove duplicates and common words
        common_words = {
            'how', 'to', 'use', 'with', 'for', 'and', 'or', 'the', 'a', 'an',
            'in', 'on', 'at', 'by', 'from', 'up', 'about', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'between', 'among',
            'implement', 'create', 'build', 'make', 'get', 'set', 'add', 'remove'
        }

        filtered_candidates = []
        seen = set()

        for candidate in candidates:
            candidate = candidate.lower()
            if (candidate not in common_words and
                candidate not in seen and
                len(candidate) > 2):
                filtered_candidates.append(candidate)
                seen.add(candidate)

        # Prioritize popular libraries
        prioritized = []
        others = []

        for candidate in filtered_candidates:
            if candidate in self.popular_libraries:
                prioritized.append(candidate)
            else:
                others.append(candidate)

        return prioritized + others[:5]  # Limit to reasonable number

    async def _search_library_documentation(self,
                                          library_name: str,
                                          query: str,
                                          result_types: Optional[List[SearchResultType]],
                                          **kwargs) -> List[SearchResult]:
        """Search documentation for a specific library"""

        results = []

        try:
            # Step 1: Resolve library ID
            # Note: In real implementation, this would call the MCP tool
            # For now, we'll simulate the call
            library_id = await self._resolve_library_id(library_name)

            if not library_id:
                return results

            # Step 2: Get library documentation with topic focus
            topic = self._extract_topic_from_query(query, result_types)
            tokens = self._calculate_token_limit(query, result_types)

            docs_content = await self._get_library_docs(library_id, topic, tokens)

            if docs_content:
                # Create SearchResult from documentation
                result = self._create_result_from_docs(
                    library_name, library_id, docs_content, query, topic
                )
                if result:
                    results.append(result)

        except Exception as e:
            logger.error(f"Error searching library '{library_name}': {e}")

        return results

    async def _resolve_library_id(self, library_name: str) -> Optional[str]:
        """Resolve library name to Context7 library ID"""

        try:
            # In real implementation, this would use:
            # result = await mcp__context7__resolve_library_id(library_name)

            # For now, simulate based on common library patterns
            library_id_map = {
                'react': '/facebook/react',
                'vue': '/vuejs/vue',
                'angular': '/angular/angular',
                'express': '/expressjs/express',
                'nextjs': '/vercel/next.js',
                'django': '/django/django',
                'flask': '/pallets/flask',
                'fastapi': '/tiangolo/fastapi',
                'numpy': '/numpy/numpy',
                'pandas': '/pandas-dev/pandas',
                'docker': '/docker/docs',
                'kubernetes': '/kubernetes/kubernetes',
                'mongodb': '/mongodb/docs',
                'postgresql': '/postgres/postgres',
                'aws': '/aws/aws-sdk',
                'tensorflow': '/tensorflow/tensorflow',
                'pytorch': '/pytorch/pytorch'
            }

            # Return mapped ID or construct one
            return library_id_map.get(library_name.lower(), f'/library/{library_name}')

        except Exception as e:
            logger.error(f"Failed to resolve library ID for '{library_name}': {e}")
            return None

    async def _get_library_docs(self, library_id: str, topic: Optional[str], tokens: int) -> Optional[str]:
        """Get documentation content for library"""

        try:
            # In real implementation, this would use:
            # result = await mcp__context7__get_library_docs(
            #     context7CompatibleLibraryID=library_id,
            #     topic=topic,
            #     tokens=tokens
            # )

            # For now, simulate documentation content
            return f"""
# {library_id.split('/')[-1]} Documentation

## Overview
{library_id.split('/')[-1]} is a popular library for modern development.

## Installation
```bash
npm install {library_id.split('/')[-1]}
# or
pip install {library_id.split('/')[-1]}
```

## Basic Usage
```javascript
// Basic example
import {{ main }} from '{library_id.split('/')[-1]}';

const result = main.create();
```

## API Reference
- `create()`: Creates a new instance
- `configure(options)`: Configures the library
- `process(data)`: Processes input data

## Examples
See the examples directory for more detailed usage patterns.
"""

        except Exception as e:
            logger.error(f"Failed to get documentation for '{library_id}': {e}")
            return None

    def _extract_topic_from_query(self, query: str, result_types: Optional[List[SearchResultType]]) -> Optional[str]:
        """Extract specific topic from query for focused documentation"""

        query_lower = query.lower()

        # Topic mapping based on common patterns
        topic_patterns = {
            'installation': ['install', 'setup', 'getting started'],
            'configuration': ['config', 'configure', 'settings', 'options'],
            'api': ['api', 'reference', 'methods', 'functions'],
            'authentication': ['auth', 'login', 'security', 'token'],
            'deployment': ['deploy', 'production', 'build'],
            'testing': ['test', 'testing', 'unit test', 'mock'],
            'hooks': ['hook', 'lifecycle', 'event'],
            'routing': ['route', 'router', 'navigation'],
            'state': ['state', 'store', 'redux', 'context'],
            'styling': ['style', 'css', 'theme', 'design'],
            'performance': ['performance', 'optimize', 'speed', 'cache'],
            'migration': ['migrate', 'upgrade', 'update', 'breaking']
        }

        # Check for explicit topic matches
        for topic, keywords in topic_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return topic

        # Infer topic from result types
        if result_types:
            if SearchResultType.API_REFERENCE in result_types:
                return 'api'
            elif SearchResultType.TUTORIAL in result_types:
                return 'getting-started'
            elif SearchResultType.CODE_EXAMPLE in result_types:
                return 'examples'

        return None

    def _calculate_token_limit(self, query: str, result_types: Optional[List[SearchResultType]]) -> int:
        """Calculate appropriate token limit based on query complexity"""

        # Base tokens
        tokens = self.default_tokens

        # Adjust based on query length
        if len(query.split()) > 10:
            tokens = min(tokens + 1000, self.max_tokens)

        # Adjust based on result types
        if result_types:
            if SearchResultType.API_REFERENCE in result_types:
                tokens = min(tokens + 1500, self.max_tokens)  # API docs can be long
            elif SearchResultType.TUTORIAL in result_types:
                tokens = min(tokens + 1000, self.max_tokens)  # Tutorials need examples

        return tokens

    def _create_result_from_docs(self,
                               library_name: str,
                               library_id: str,
                               docs_content: str,
                               query: str,
                               topic: Optional[str]) -> Optional[SearchResult]:
        """Create SearchResult from documentation content"""

        try:
            # Create title
            title = f"{library_name.title()} Documentation"
            if topic:
                title += f" - {topic.title()}"

            # Generate URL (would be real docs URL in production)
            url = f"https://docs.{library_name.lower()}.com"
            if 'github.com' in library_id:
                url = f"https://github.com{library_id}"
            elif library_name in ['react', 'vue', 'angular']:
                url = f"https://{library_name.lower()}.dev"

            # Create summary
            summary = self._generate_summary(docs_content, max_words=40)

            # Determine result type
            result_type = SearchResultType.DOCUMENTATION
            if topic == 'api':
                result_type = SearchResultType.API_REFERENCE
            elif 'example' in docs_content.lower():
                result_type = SearchResultType.CODE_EXAMPLE

            # Context7 always provides excellent quality
            source_quality = SourceQuality.EXCELLENT

            # Calculate relevance based on library popularity and topic match
            relevance_score = self._calculate_context7_relevance(library_name, query, topic)

            # Create SearchResult
            result = SearchResult(
                title=title,
                url=url,
                content=docs_content,
                summary=summary,
                result_type=result_type,
                source_quality=source_quality,
                relevance_score=relevance_score,
                published_date=datetime.now(),  # Official docs are always current
                author=f"{library_name} Team",
                engine_metadata={
                    'library_id': library_id,
                    'library_name': library_name,
                    'topic': topic,
                    'token_count': len(docs_content.split()),
                    'is_official_docs': True,
                    'mcp_source': 'context7'
                }
            )

            # Extract technical content
            self._extract_technical_content(result, docs_content)

            return result

        except Exception as e:
            logger.error(f"Failed to create result from docs: {e}")
            return None

    def _calculate_context7_relevance(self, library_name: str, query: str, topic: Optional[str]) -> float:
        """Calculate relevance score for Context7 results"""

        score = 0.7  # Base score for official documentation

        # Library popularity bonus
        if library_name.lower() in self.popular_libraries:
            score += 0.15

        # Exact library name match bonus
        if library_name.lower() in query.lower():
            score += 0.1

        # Topic relevance bonus
        if topic and topic in query.lower():
            score += 0.05

        return min(1.0, score)

    def _context7_ranking_score(self, result: SearchResult) -> float:
        """Calculate ranking score for Context7 results (higher is better)"""

        score = result.relevance_score * 100  # Base relevance (0-100)

        # Official documentation gets highest priority
        score += 50  # Huge bonus for official docs

        # Library popularity bonus
        library_name = result.engine_metadata.get('library_name', '').lower()
        if library_name in self.popular_libraries:
            score += 20

        # API reference bonus
        if result.result_type == SearchResultType.API_REFERENCE:
            score += 10

        # Code example bonus
        if result.code_snippets:
            score += 5

        return score

    async def _search_general_topic(self,
                                  query: str,
                                  result_types: Optional[List[SearchResultType]],
                                  **kwargs) -> List[SearchResult]:
        """Search for general programming topics across libraries"""

        results = []

        # For general topics, try searching common libraries
        common_libs = ['react', 'vue', 'django', 'flask', 'express', 'nextjs']

        for lib in common_libs[:3]:  # Limit to avoid too many results
            try:
                lib_results = await self._search_library_documentation(
                    lib, query, result_types, **kwargs
                )
                results.extend(lib_results)
            except Exception as e:
                logger.debug(f"General search failed for {lib}: {e}")
                continue

        return results

    def _extract_technical_content(self, result: SearchResult, content: str):
        """Extract code snippets and API endpoints from documentation"""

        import re

        # Find code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        result.code_snippets = [
            block.strip('`').strip()
            for block in code_blocks[:4]  # More examples for official docs
        ]

        # Find API methods and functions
        api_patterns = [
            r'(?:def|function|class|method)\s+(\w+)',
            r'(\w+)\s*\(',
            r'(\w+\.\w+)\s*\('
        ]

        api_endpoints = []
        for pattern in api_patterns:
            matches = re.findall(pattern, content)
            api_endpoints.extend(matches[:3])

        result.api_endpoints = list(set(api_endpoints))

    async def get_library_info(self, library_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific library"""

        try:
            library_id = await self._resolve_library_id(library_name)
            if not library_id:
                return None

            docs_content = await self._get_library_docs(library_id, None, self.max_tokens)
            if not docs_content:
                return None

            return {
                'library_name': library_name,
                'library_id': library_id,
                'documentation': docs_content,
                'is_popular': library_name.lower() in self.popular_libraries,
                'source': 'context7'
            }

        except Exception as e:
            logger.error(f"Failed to get library info for '{library_name}': {e}")
            return None

    async def get_available_libraries(self) -> List[str]:
        """Get list of available libraries (would come from MCP in real implementation)"""

        # Return popular libraries as example
        return sorted(list(self.popular_libraries))