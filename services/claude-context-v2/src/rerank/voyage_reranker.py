"""
Voyage Reranking Layer - Task 6
Reranks search results using voyage-rerank-2.5 with ADHD-optimized progressive disclosure.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import voyageai
from voyageai import AsyncClient

from ..search.dense_search import SearchResult


logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """Single reranking result with metadata."""

    search_result: SearchResult
    relevance_score: float
    original_rank: int
    new_rank: int


@dataclass
class RerankResponse:
    """Complete reranking response with ADHD features."""

    # Top-10 results (always displayed)
    top_results: List[RerankResult]

    # Remaining results (cached for "show more")
    cached_results: List[RerankResult]

    # Metadata
    total_results: int
    tokens_used: int
    cost_usd: float

    def get_all_results(self) -> List[RerankResult]:
        """Get all results (top + cached)."""
        return self.top_results + self.cached_results


@dataclass
class CostTracker:
    """Track Voyage reranking costs."""

    total_requests: int = 0
    total_documents: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    # Voyage reranking pricing: $0.05 per 1000 requests
    PRICE_PER_1K_REQUESTS = 0.05

    def add_request(self, num_documents: int, tokens: int = 0) -> float:
        """Add reranking request and return cost."""
        self.total_requests += 1
        self.total_documents += num_documents
        self.total_tokens += tokens

        # Cost based on requests, not documents
        cost = self.PRICE_PER_1K_REQUESTS / 1000
        self.total_cost_usd += cost

        return cost

    def summary(self) -> Dict:
        """Get cost summary."""
        return {
            "total_requests": self.total_requests,
            "total_documents": self.total_documents,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "avg_docs_per_request": round(
                self.total_documents / max(self.total_requests, 1), 1
            ),
        }


class VoyageReranker:
    """
    Voyage reranking layer with ADHD-optimized progressive disclosure.

    Features:
    - voyage-rerank-2.5 model
    - Progressive disclosure (top-10 display, rest cached)
    - Cost tracking
    - Handles up to 1000 documents per request
    """

    def __init__(
        self,
        api_key: str,
        model: str = "rerank-2.5",
        top_n_display: int = 10,
        max_cache: int = 40,
    ):
        """
        Initialize Voyage reranker.

        Args:
            api_key: VoyageAI API key
            model: Reranking model (default: rerank-2.5)
            top_n_display: Number of top results to display (ADHD: 10)
            max_cache: Max cached results beyond top_n (ADHD: 40)
        """
        self.client = AsyncClient(api_key=api_key)
        self.model = model
        self.top_n_display = top_n_display
        self.max_cache = max_cache
        self.cost_tracker = CostTracker()

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
        return_documents: bool = False,
    ) -> RerankResponse:
        """
        Rerank search results using Voyage.

        Args:
            query: Search query
            results: Search results from hybrid search
            return_documents: Whether to return document text in response

        Returns:
            RerankResponse with top-N and cached results
        """
        if not results:
            return RerankResponse(
                top_results=[],
                cached_results=[],
                total_results=0,
                tokens_used=0,
                cost_usd=0.0,
            )

        # Prepare documents for reranking
        # Use contextualized content (context + code)
        documents = []
        for result in results:
            # Combine context snippet and code for better reranking
            if result.context_snippet:
                doc_text = f"{result.context_snippet}\n\n{result.content}"
            else:
                doc_text = result.content

            documents.append(doc_text)

        logger.debug(f"Reranking {len(documents)} results with {self.model}")

        try:
            # Call Voyage rerank API
            reranking = await self.client.rerank(
                query=query,
                documents=documents,
                model=self.model,
                top_k=None,  # Return all with scores
                return_documents=return_documents,
            )

            # Track cost
            tokens = getattr(reranking, 'total_tokens', 0)
            cost = self.cost_tracker.add_request(
                num_documents=len(documents),
                tokens=tokens,
            )

            # Create RerankResult objects
            reranked_results = []

            for rerank_item in reranking.results:
                original_idx = rerank_item.index
                original_result = results[original_idx]

                reranked_results.append(
                    RerankResult(
                        search_result=original_result,
                        relevance_score=rerank_item.relevance_score,
                        original_rank=original_idx,
                        new_rank=len(reranked_results),  # Current position
                    )
                )

            # Split into top-N and cached
            total = len(reranked_results)
            top_results = reranked_results[:self.top_n_display]
            cached_results = reranked_results[
                self.top_n_display:self.top_n_display + self.max_cache
            ]

            logger.info(
                f"Reranked {total} results: {len(top_results)} displayed, "
                f"{len(cached_results)} cached"
            )

            return RerankResponse(
                top_results=top_results,
                cached_results=cached_results,
                total_results=total,
                tokens_used=tokens,
                cost_usd=cost,
            )

        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return original results without reranking
            fallback_results = [
                RerankResult(
                    search_result=result,
                    relevance_score=result.score,
                    original_rank=i,
                    new_rank=i,
                )
                for i, result in enumerate(results)
            ]

            return RerankResponse(
                top_results=fallback_results[:self.top_n_display],
                cached_results=fallback_results[
                    self.top_n_display:self.top_n_display + self.max_cache
                ],
                total_results=len(fallback_results),
                tokens_used=0,
                cost_usd=0.0,
            )

    def get_cost_summary(self) -> Dict:
        """Get cost tracking summary."""
        return self.cost_tracker.summary()


# Example usage
async def main():
    """Example usage of VoyageReranker."""
    import os
    from ..search.dense_search import SearchResult

    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        print("Set VOYAGE_API_KEY environment variable")
        return

    reranker = VoyageReranker(api_key=api_key)

    # Example search results
    search_results = [
        SearchResult(
            id="1",
            score=0.85,
            payload={},
            file_path="src/auth.py",
            function_name="validate_user",
            language="python",
            content="def validate_user(token): return verify_jwt(token)",
            context_snippet="Validates user authentication token",
        ),
        SearchResult(
            id="2",
            score=0.80,
            payload={},
            file_path="src/utils.py",
            function_name="calculate_score",
            language="python",
            content="def calculate_score(data): return sum(data) / len(data)",
            context_snippet="Calculates average score from data",
        ),
    ]

    # Rerank
    response = await reranker.rerank(
        query="user authentication validation",
        results=search_results,
    )

    print(f"Reranked {response.total_results} results:")
    print(f"Top {len(response.top_results)} displayed:")
    for r in response.top_results:
        print(
            f"  {r.search_result.file_path}:{r.search_result.function_name} "
            f"(score: {r.relevance_score:.4f}, rank: {r.original_rank}→{r.new_rank})"
        )

    print(f"\n{len(response.cached_results)} cached for 'show more'")

    # Cost summary
    summary = reranker.get_cost_summary()
    print(f"\nCost summary: {summary}")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
