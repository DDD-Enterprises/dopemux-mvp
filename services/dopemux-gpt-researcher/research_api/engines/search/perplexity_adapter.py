"""
Perplexity Search Adapter - Web research with citations.

This adapter uses Perplexity's chat-completions API and converts responses into
standardized ``SearchResult`` objects.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

from .base_adapter import (
    BaseSearchAdapter,
    SearchResult,
    SearchResultType,
    SourceQuality,
)

logger = logging.getLogger(__name__)


class PerplexitySearchAdapter(BaseSearchAdapter):
    """Perplexity-backed adapter tuned for ADHD-friendly research output."""

    def __init__(self, api_key: str, **kwargs: Any):
        super().__init__(api_key, **kwargs)
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self._session: Optional[aiohttp.ClientSession] = None
        self.temperature = kwargs.get("temperature", 0.1)
        self.default_max_tokens = kwargs.get("max_tokens", 1200)
        self.models = {
            "fast": kwargs.get("fast_model", "sonar"),
            "balanced": kwargs.get("balanced_model", "sonar-pro"),
            "comprehensive": kwargs.get("comprehensive_model", "sonar-deep-research"),
        }

    @property
    def engine_name(self) -> str:
        return "perplexity"

    @property
    def max_results_per_request(self) -> int:
        return 10

    @property
    def supports_date_filtering(self) -> bool:
        return True

    @property
    def supports_domain_filtering(self) -> bool:
        return True

    async def _create_session(self) -> aiohttp.ClientSession:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "DopemuxResearcher/1.0",
        }
        connector = aiohttp.TCPConnector(limit=8, limit_per_host=4)
        timeout = aiohttp.ClientTimeout(total=40)
        return aiohttp.ClientSession(headers=headers, connector=connector, timeout=timeout)

    async def _execute_search(
        self,
        query: str,
        max_results: int,
        result_types: Optional[List[SearchResultType]],
        date_filter: Optional[str],
        domain_filter: Optional[List[str]],
        **kwargs: Any,
    ) -> List[SearchResult]:
        if not self.api_key:
            logger.warning("Perplexity API key missing; returning no results")
            return []

        if not self._session:
            self._session = await self._create_session()

        model = self._select_model_for_query(query, result_types)
        payload = {
            "model": model,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
            "stream": False,
            "messages": [
                {"role": "system", "content": self._get_system_prompt(result_types)},
                {
                    "role": "user",
                    "content": self._build_user_prompt(
                        query=query,
                        max_results=max_results,
                        date_filter=date_filter,
                        domain_filter=domain_filter,
                    ),
                },
            ],
        }

        try:
            async with self._session.post(self.base_url, json=payload) as response:
                if response.status == 429:
                    await asyncio.sleep(2)
                    async with self._session.post(self.base_url, json=payload) as retry_response:
                        response = retry_response

                response.raise_for_status()
                data = await response.json()
                self._rate_limit_remaining = response.headers.get("x-ratelimit-remaining")
                self._last_request_time = datetime.now()

            results = self._parse_perplexity_response(data, query, max_results)
            logger.info("Perplexity search returned %s results", len(results))
            return results

        except aiohttp.ClientError as exc:
            logger.error("Perplexity API request failed: %s", exc)
            return []
        except Exception as exc:
            logger.error("Perplexity search error: %s", exc)
            return []

    def _select_model_for_query(
        self, query: str, result_types: Optional[List[SearchResultType]]
    ) -> str:
        query_lower = query.lower()
        complexity_markers = [
            "compare",
            "architecture",
            "enterprise",
            "comprehensive",
            "microservices",
            "tradeoff",
            "analysis",
        ]

        if result_types and SearchResultType.CODE_EXAMPLE in result_types:
            return self.models["balanced"]

        if len(query.split()) > 8 or any(marker in query_lower for marker in complexity_markers):
            return self.models["comprehensive"]

        return self.models["fast"]

    def _build_user_prompt(
        self,
        query: str,
        max_results: int,
        date_filter: Optional[str],
        domain_filter: Optional[List[str]],
    ) -> str:
        prompt_parts = [
            f"Query: {query}",
            f"Return up to {max_results} distinct cited sources.",
            "For each source, include title, URL, and a concise summary.",
        ]

        if date_filter:
            prompt_parts.append(f"Prefer sources from: {self._date_filter_text(date_filter)}.")
        if domain_filter:
            prompt_parts.append(f"Restrict results to these domains when possible: {', '.join(domain_filter)}.")

        return "\n".join(prompt_parts)

    def _get_system_prompt(self, result_types: Optional[List[SearchResultType]]) -> str:
        prompt = (
            "You are a technical research assistant. "
            "Always include citations and prioritize trustworthy sources."
        )

        if not result_types:
            return prompt

        if SearchResultType.CODE_EXAMPLE in result_types:
            prompt += " Prioritize code examples with implementation details."
        if SearchResultType.API_REFERENCE in result_types:
            prompt += " Prioritize official API documentation and references."
        if SearchResultType.DOCUMENTATION in result_types:
            prompt += " Prefer official documentation over blogs when possible."
        if SearchResultType.STACK_OVERFLOW in result_types:
            prompt += " Include practical troubleshooting answers where relevant."

        return prompt

    def _parse_perplexity_response(
        self, data: Dict[str, Any], query: str, max_results: int
    ) -> List[SearchResult]:
        choices = data.get("choices", [])
        content = ""
        if choices:
            content = (choices[0].get("message") or {}).get("content", "") or ""

        citations = self._normalize_citations(data)
        results: List[SearchResult] = []

        for index, citation in enumerate(citations[:max_results]):
            url = citation.get("url", "")
            title = citation.get("title") or citation.get("name") or "Perplexity Citation"
            snippet = citation.get("snippet") or citation.get("summary") or content[:500]
            result = SearchResult(
                title=title,
                url=url,
                content=snippet or content,
                summary=(snippet[:200] + "...") if snippet and len(snippet) > 200 else (snippet or content[:200]),
                result_type=self._classify_result_type(url, snippet, title),
                source_quality=self._assess_source_quality(url),
                relevance_score=self._calculate_relevance(index, citations),
                source_domain=urlparse(url).netloc if url else "",
                key_points=[point.strip() for point in (snippet or "").split(".") if point.strip()][:3],
                engine_metadata={"provider": "perplexity", "citation_index": index},
            )
            results.append(result)

        if not results and content:
            results.append(
                SearchResult(
                    title=f"Perplexity summary for: {query}",
                    url="",
                    content=content,
                    summary=content[:200] + ("..." if len(content) > 200 else ""),
                    result_type=SearchResultType.DOCUMENTATION,
                    source_quality=SourceQuality.MODERATE,
                    relevance_score=0.5,
                    engine_metadata={"provider": "perplexity", "synthetic": True},
                )
            )

        return results

    def _normalize_citations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        citations = data.get("citations") or data.get("search_results") or []

        normalized: List[Dict[str, Any]] = []
        for citation in citations:
            if isinstance(citation, str):
                normalized.append({"url": citation})
            elif isinstance(citation, dict):
                normalized.append(citation)
        return normalized

    def _date_filter_text(self, date_filter: str) -> str:
        now = datetime.now()
        lowered = date_filter.lower()
        if lowered == "last_week":
            return f"the past week (since {(now - timedelta(days=7)).date().isoformat()})"
        if lowered == "last_month":
            return f"the past month (since {(now - timedelta(days=30)).date().isoformat()})"
        if lowered == "last_year":
            return f"the past year (since {(now - timedelta(days=365)).date().isoformat()})"
        return date_filter

    def _assess_source_quality(self, url: str) -> SourceQuality:
        if not url:
            return SourceQuality.MODERATE
        domain = urlparse(url).netloc.lower()

        excellent_domains = ("docs.", "developer.", "github.com", "kubernetes.io", "python.org")
        good_domains = ("stackoverflow.com", "medium.com", "dev.to", "hashnode.com")

        if any(token in domain for token in excellent_domains):
            return SourceQuality.EXCELLENT
        if any(token in domain for token in good_domains):
            return SourceQuality.GOOD
        return SourceQuality.MODERATE

    def _classify_result_type(
        self, url: str, content: Optional[str], title: Optional[str]
    ) -> SearchResultType:
        text = f"{url} {content or ''} {title or ''}".lower()

        if "stackoverflow.com" in text:
            return SearchResultType.STACK_OVERFLOW
        if "github.com" in text and "/issues" in text:
            return SearchResultType.GITHUB_ISSUE
        if "github.com" in text:
            return SearchResultType.CODE_EXAMPLE
        if "api" in text or "reference" in text:
            return SearchResultType.API_REFERENCE
        if "docs" in text or "documentation" in text:
            return SearchResultType.DOCUMENTATION
        if "tutorial" in text or "guide" in text:
            return SearchResultType.TUTORIAL
        if "news" in text or "release" in text:
            return SearchResultType.NEWS_ARTICLE
        return SearchResultType.BLOG_POST

    def _calculate_relevance(self, index: int, citations: List[Dict[str, Any]]) -> float:
        if not citations:
            return 0.5
        # Higher score for earlier citations returned by Perplexity.
        return max(0.1, 1.0 - (index / max(1, len(citations))))
