"""Voyage reranking with bounded candidate sizing and correct token pricing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

from voyageai import AsyncClient

from ..embeddings.model_registry import DEFAULT_RERANK_MODEL, env_model
from ..search.dense_search import SearchResult
from ..utils.model_tokenizer import VoyageTokenCounter

logger = logging.getLogger(__name__)

RERANK_PRICING_PER_MILLION = {
    "rerank-2.5": 0.05,
    "rerank-2.5-lite": 0.02,
}
RERANK_MAX_DOCUMENTS = 1_000
RERANK_MAX_TOTAL_TOKENS = 600_000
# Vendor per-query ceiling for rerank-2.5 / rerank-2.5-lite -- the only two
# models RERANK_PRICING_PER_MILLION supports; both share this limit.
# https://docs.voyageai.com/reference/reranker-api (verified 2026-07-26).
RERANK_MAX_QUERY_TOKENS = 8_000


class RerankQueryTooLargeError(ValueError):
    """Raised when a rerank query exceeds the vendor per-query token limit.

    Deliberately not caught inside rerank(): an oversized query is a caller
    error, not a degraded-service condition, and must fail loudly (F-014)
    rather than being swallowed into a "successful-looking" fallback (F-011).
    """


@dataclass
class RerankResult:
    search_result: SearchResult
    relevance_score: float
    original_rank: int
    new_rank: int


@dataclass
class RerankResponse:
    top_results: List[RerankResult]
    cached_results: List[RerankResult]
    total_results: int
    tokens_used: int
    cost_usd: float
    # True when the original (dense) ordering was returned instead of a
    # genuine Voyage rerank -- either the API call failed or no candidate fit
    # within the token budget. Callers must not treat a degraded response as
    # a successful rerank (F-011).
    degraded: bool = False

    def get_all_results(self) -> List[RerankResult]:
        return self.top_results + self.cached_results


@dataclass
class CostTracker:
    total_requests: int = 0
    total_documents: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    def add_request(self, model: str, num_documents: int, tokens: int) -> float:
        self.total_requests += 1
        self.total_documents += num_documents
        self.total_tokens += tokens
        price = RERANK_PRICING_PER_MILLION.get(model)
        if price is None:
            raise ValueError(f"Unsupported Voyage reranker model '{model}'")
        cost = (tokens / 1_000_000) * price
        self.total_cost_usd += cost
        return cost

    def summary(self) -> Dict:
        return {
            "total_requests": self.total_requests,
            "total_documents": self.total_documents,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "avg_docs_per_request": round(
                self.total_documents / max(self.total_requests, 1), 1
            ),
        }


class VoyageReranker:
    """Rerank initial candidates with progressive disclosure."""

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        top_n_display: int = 10,
        max_cache: int = 40,
    ):
        self.model = model or env_model(
            "DOPE_CONTEXT_RERANK_MODEL", DEFAULT_RERANK_MODEL
        )
        if self.model not in RERANK_PRICING_PER_MILLION:
            raise ValueError(
                f"Unsupported reranker '{self.model}'; expected one of "
                f"{sorted(RERANK_PRICING_PER_MILLION)}"
            )
        self.client = AsyncClient(api_key=api_key)
        self.token_counter = VoyageTokenCounter(api_key=api_key)
        self.top_n_display = max(1, top_n_display)
        self.max_cache = max(0, max_cache)
        self.cost_tracker = CostTracker()

    @staticmethod
    def _document_text(result: SearchResult) -> str:
        if result.context_snippet:
            return f"{result.context_snippet}\n\n{result.content}"
        return result.content

    async def _bounded_candidates(
        self, query_tokens: int, results: List[SearchResult]
    ) -> tuple[List[SearchResult], List[str], int]:
        candidates = results[:RERANK_MAX_DOCUMENTS]
        documents = [self._document_text(result) for result in candidates]
        document_counts = await self.token_counter.count_each(documents, self.model)

        bounded_results: List[SearchResult] = []
        bounded_documents: List[str] = []
        document_total = 0
        for result, document, token_count in zip(
            candidates, documents, document_counts
        ):
            next_count = len(bounded_documents) + 1
            next_total = (
                query_tokens * next_count
                + document_total
                + token_count.count
            )
            if next_total > RERANK_MAX_TOTAL_TOKENS:
                break
            bounded_results.append(result)
            bounded_documents.append(document)
            document_total += token_count.count

        total_tokens = query_tokens * len(bounded_documents) + document_total
        return bounded_results, bounded_documents, total_tokens

    async def _api_rerank(self, *, query: str, documents: List[str]):
        # return_documents does not exist on this (or any) voyageai SDK
        # release -- verified via inspect.signature(AsyncClient.rerank) on
        # 0.3.7 and 0.5.0 (F-010b). Sending it raised TypeError on every call,
        # which took a compatibility branch that also stripped `truncation`.
        # query/documents/model/top_k/truncation are the full accepted set.
        return await self.client.rerank(
            query=query,
            documents=documents,
            model=self.model,
            top_k=None,
            truncation=True,
        )

    async def rerank(
        self,
        query: str,
        results: List[SearchResult],
    ) -> RerankResponse:
        if not results:
            return RerankResponse([], [], 0, 0, 0.0)

        query_tokens = (
            await self.token_counter.count_each([query], self.model)
        )[0].count
        if query_tokens > RERANK_MAX_QUERY_TOKENS:
            # Not caught below by design (F-014): an oversized query must
            # fail loudly rather than take the silent dense-order fallback.
            raise RerankQueryTooLargeError(
                f"Rerank query has {query_tokens} tokens, exceeding the "
                f"{RERANK_MAX_QUERY_TOKENS}-token limit for '{self.model}'"
            )

        bounded_results, documents, estimated_tokens = await self._bounded_candidates(
            query_tokens, results
        )
        if not documents:
            logger.warning("No rerank candidates fit within Voyage token limits")
            return self._fallback(results)

        if len(bounded_results) < len(results):
            logger.info(
                "Trimmed rerank candidates from %s to %s for token limits",
                len(results),
                len(bounded_results),
            )

        try:
            reranking = await self._api_rerank(query=query, documents=documents)
            tokens = int(getattr(reranking, "total_tokens", 0) or estimated_tokens)
            cost = self.cost_tracker.add_request(
                model=self.model,
                num_documents=len(documents),
                tokens=tokens,
            )

            reranked_results: List[RerankResult] = []
            for new_rank, item in enumerate(reranking.results):
                original_index = int(item.index)
                if original_index >= len(bounded_results):
                    raise ValueError(
                        f"Voyage reranker returned invalid index {original_index}"
                    )
                reranked_results.append(
                    RerankResult(
                        search_result=bounded_results[original_index],
                        relevance_score=float(item.relevance_score),
                        original_rank=original_index,
                        new_rank=new_rank,
                    )
                )

            return self._split(reranked_results, tokens=tokens, cost=cost)
        except Exception as exc:
            logger.error("Reranking failed; preserving initial order: %s", exc)
            return self._fallback(results)

    def _split(
        self,
        results: List[RerankResult],
        *,
        tokens: int,
        cost: float,
        degraded: bool = False,
    ) -> RerankResponse:
        return RerankResponse(
            top_results=results[: self.top_n_display],
            cached_results=results[
                self.top_n_display : self.top_n_display + self.max_cache
            ],
            total_results=len(results),
            tokens_used=tokens,
            cost_usd=cost,
            degraded=degraded,
        )

    def _fallback(self, results: List[SearchResult]) -> RerankResponse:
        fallback = [
            RerankResult(
                search_result=result,
                relevance_score=result.score,
                original_rank=index,
                new_rank=index,
            )
            for index, result in enumerate(results)
        ]
        return self._split(fallback, tokens=0, cost=0.0, degraded=True)

    def get_cost_summary(self) -> Dict:
        return self.cost_tracker.summary()
