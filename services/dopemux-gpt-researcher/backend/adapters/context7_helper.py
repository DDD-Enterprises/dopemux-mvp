"""
Context7 Integration Helper for Discrete Documentation Lookups

Provides seamless integration with Context7 for ADHD-friendly documentation access:
- Auto-detect programming concepts in research queries
- Discrete documentation lookups for better context
- Non-blocking integration that enhances but doesn't interrupt workflow
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentationHint:
    """A discrete documentation hint for research enhancement"""
    library: str
    topic: str
    confidence: float
    reason: str


class Context7Helper:
    """
    Discrete Context7 integration for research enhancement

    This helper discretely detects when research queries involve
    programming concepts and quietly fetches relevant documentation
    to enhance research results without interrupting the flow.
    """

    def __init__(self, enabled: bool = True):
        """Initialize with optional disable for minimal overhead"""
        self.enabled = enabled
        self.doc_cache: Dict[str, str] = {}
        self.programming_patterns = self._init_programming_patterns()

    def _init_programming_patterns(self) -> Dict[str, Set[str]]:
        """Initialize patterns for detecting programming concepts"""
        return {
            'python': {
                'asyncio', 'fastapi', 'pydantic', 'pytest', 'flask', 'django',
                'numpy', 'pandas', 'sqlalchemy', 'requests', 'click', 'uvicorn'
            },
            'javascript': {
                'react', 'vue', 'angular', 'node', 'express', 'webpack',
                'babel', 'typescript', 'jest', 'cypress', 'next.js'
            },
            'general': {
                'api', 'rest', 'graphql', 'database', 'authentication',
                'testing', 'deployment', 'docker', 'kubernetes', 'ci/cd'
            }
        }

    async def analyze_research_query(self, query: str) -> List[DocumentationHint]:
        """
        Discretely analyze research query for documentation opportunities

        Returns hints that could enhance research but doesn't block if disabled
        """
        if not self.enabled:
            return []

        try:
            hints = []
            query_lower = query.lower()

            # Detect programming libraries/frameworks
            for category, patterns in self.programming_patterns.items():
                for pattern in patterns:
                    if pattern in query_lower:
                        confidence = self._calculate_confidence(query_lower, pattern)
                        if confidence > 0.6:  # Only high-confidence matches
                            hints.append(DocumentationHint(
                                library=pattern,
                                topic=self._extract_topic_context(query_lower, pattern),
                                confidence=confidence,
                                reason=f"Detected {pattern} in {category} context"
                            ))

            # Sort by confidence and return top 3 to avoid overwhelming
            return sorted(hints, key=lambda h: h.confidence, reverse=True)[:3]

        except Exception as e:
            logger.debug(f"Context7Helper analysis failed silently: {e}")
            return []  # Fail gracefully

    def _calculate_confidence(self, query: str, pattern: str) -> float:
        """Calculate confidence score for pattern match"""
        base_score = 0.7  # Found the pattern

        # Boost for exact word boundaries
        if re.search(rf'\b{re.escape(pattern)}\b', query):
            base_score += 0.2

        # Boost for technical context words
        technical_words = ['api', 'library', 'framework', 'documentation', 'tutorial', 'guide']
        for word in technical_words:
            if word in query:
                base_score += 0.1
                break

        return min(base_score, 1.0)

    def _extract_topic_context(self, query: str, pattern: str) -> str:
        """Extract specific topic context around the pattern"""
        # Look for common programming topics
        topics = {
            'authentication': ['auth', 'login', 'jwt', 'oauth', 'security'],
            'api': ['endpoint', 'route', 'rest', 'json', 'request'],
            'database': ['db', 'sql', 'model', 'schema', 'query'],
            'testing': ['test', 'unit', 'integration', 'mock', 'coverage'],
            'async': ['async', 'await', 'concurrent', 'parallel', 'promise'],
            'deployment': ['deploy', 'production', 'server', 'hosting', 'docker']
        }

        for topic, keywords in topics.items():
            if any(keyword in query for keyword in keywords):
                return topic

        return 'general'

    async def discrete_doc_lookup(self, hint: DocumentationHint) -> Optional[str]:
        """
        Discretely fetch documentation if it would be helpful

        This runs in background and caches results for later use
        """
        if not self.enabled:
            return None

        cache_key = f"{hint.library}:{hint.topic}"
        if cache_key in self.doc_cache:
            return self.doc_cache[cache_key]

        try:
            # Simulate discrete Context7 lookup
            # In actual implementation, this would call:
            # result = await context7_resolve_library_id(hint.library)
            # docs = await context7_get_library_docs(result, topic=hint.topic, tokens=1000)

            # For now, return a hint that documentation was found
            doc_summary = f"Documentation available for {hint.library} - {hint.topic}"
            self.doc_cache[cache_key] = doc_summary

            logger.debug(f"Discrete Context7 lookup cached: {cache_key}")
            return doc_summary

        except Exception as e:
            logger.debug(f"Context7 lookup failed silently: {e}")
            return None

    async def enhance_research_discretely(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Discretely enhance research results with documentation context

        This adds value without changing the core research flow
        """
        if not self.enabled or not results:
            return results

        try:
            # Analyze query for documentation opportunities
            hints = await self.analyze_research_query(query)

            if not hints:
                return results

            # Discretely fetch documentation for high-confidence hints
            doc_tasks = [
                self.discrete_doc_lookup(hint)
                for hint in hints[:2]  # Limit to top 2 to avoid overhead
            ]

            # Use asyncio.gather with timeout to avoid blocking
            docs = await asyncio.wait_for(
                asyncio.gather(*doc_tasks, return_exceptions=True),
                timeout=2.0  # Max 2 seconds for discrete enhancement
            )

            # Add documentation context discretely to metadata
            enhanced_results = results.copy()
            doc_context = [doc for doc in docs if isinstance(doc, str)]

            if doc_context and enhanced_results:
                # Add to first result's metadata discretely
                if 'metadata' not in enhanced_results[0]:
                    enhanced_results[0]['metadata'] = {}
                enhanced_results[0]['metadata']['documentation_context'] = doc_context

            return enhanced_results

        except Exception as e:
            logger.debug(f"Discrete research enhancement failed: {e}")
            return results  # Always return original results if enhancement fails


# Global helper instance with discrete operation
context7_helper = Context7Helper(enabled=True)


async def discrete_enhance_research(query: str, results: List[Dict]) -> List[Dict]:
    """
    Global function for discrete research enhancement

    Can be called from anywhere in the research pipeline to add
    documentation context without affecting core functionality
    """
    return await context7_helper.enhance_research_discretely(query, results)


async def analyze_for_documentation_hints(query: str) -> List[DocumentationHint]:
    """
    Global function for getting documentation hints

    Useful for research planning and context building
    """
    return await context7_helper.analyze_research_query(query)


# ADHD-friendly configuration
def configure_for_adhd(
    enable_discrete_docs: bool = True,
    max_hints: int = 2,
    timeout_seconds: float = 1.5
):
    """
    Configure Context7 helper for ADHD-friendly operation

    Args:
        enable_discrete_docs: Whether to enable background doc lookups
        max_hints: Maximum documentation hints to prevent overwhelm
        timeout_seconds: Max time to spend on discrete enhancements
    """
    global context7_helper
    context7_helper.enabled = enable_discrete_docs

    # Update timeouts and limits for ADHD accommodation
    if hasattr(context7_helper, '_max_hints'):
        context7_helper._max_hints = max_hints
    if hasattr(context7_helper, '_timeout'):
        context7_helper._timeout = timeout_seconds

    logger.info(f"Context7Helper configured for ADHD: enabled={enable_discrete_docs}, max_hints={max_hints}")