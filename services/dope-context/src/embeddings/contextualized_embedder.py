"""
Contextualized Voyage Embedder for voyage-context-3
Uses contextualized_embed() API for document-aware chunk embeddings.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import voyageai
from voyageai import AsyncClient


logger = logging.getLogger(__name__)


@dataclass
class ContextualizedEmbeddingResponse:
    """Response from contextualized embedding."""

    embeddings: List[List[float]]  # List of chunk embeddings
    model: str
    total_tokens: int
    cached: bool = False
    cost_usd: float = 0.0


@dataclass
class CostTracker:
    """Track embedding API costs."""

    total_tokens: int = 0
    total_requests: int = 0
    total_cost_usd: float = 0.0
    cache_hits: int = 0

    # voyage-context-3 pricing (per 1M tokens)
    PRICING = {
        "voyage-context-3": 0.12,  # Same as voyage-code-3
    }

    def add_request(self, model: str, tokens: int, cached: bool = False) -> float:
        """Add request and return cost."""
        self.total_requests += 1

        if cached:
            self.cache_hits += 1
            return 0.0

        self.total_tokens += tokens
        cost = (tokens / 1_000_000) * self.PRICING.get(model, 0.12)
        self.total_cost_usd += cost
        return cost

    def summary(self) -> Dict:
        """Get cost summary."""
        cache_rate = self.cache_hits / max(self.total_requests, 1)
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "cache_hits": self.cache_hits,
            "cache_rate": round(cache_rate, 3),
        }


class ContextualizedEmbedder:
    """
    Voyage AI contextualized embedding client for voyage-context-3.

    Features:
    - Document-aware chunk embeddings (global context + local content)
    - 14.24% better accuracy than standard embeddings
    - Batching support (up to 1000 inputs, 120K tokens, 16K chunks)
    - In-memory caching with TTL
    - Cost tracking
    """

    def __init__(
        self,
        api_key: str,
        cache_ttl_hours: int = 24,
        rate_limit_rpm: int = 2000,  # Voyage API limit for context-3
    ):
        """
        Initialize contextualized embedder.

        Args:
            api_key: VoyageAI API key
            cache_ttl_hours: Cache TTL in hours (default 24h)
            rate_limit_rpm: Requests per minute (default 300)
        """
        self.client = AsyncClient(api_key=api_key)
        self.cache: Dict[str, Tuple[ContextualizedEmbeddingResponse, datetime]] = {}
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.rate_limit_rpm = rate_limit_rpm
        self.cost_tracker = CostTracker()

        # Rate limiting
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()

    def _cache_key(self, document_chunks: List[str], model: str, input_type: str) -> str:
        """Generate cache key from document chunks."""
        content = f"{model}:{input_type}:" + "|".join(document_chunks)
        return hashlib.sha256(content.encode()).hexdigest()

    def _validate_model(self, model: str) -> None:
        """Fail closed if model drifts from contextualized contract."""
        if model != "voyage-context-3":
            raise ValueError(
                f"ContextualizedEmbedder requires model='voyage-context-3', got '{model}'"
            )

    async def _check_rate_limit(self):
        """Enforce rate limiting."""
        async with self._rate_limit_lock:
            now = datetime.now()

            # Remove requests older than 1 minute
            self._request_times = [
                t for t in self._request_times if now - t < timedelta(minutes=1)
            ]

            # Wait if at limit
            if len(self._request_times) >= self.rate_limit_rpm:
                oldest = self._request_times[0]
                wait_seconds = 60 - (now - oldest).total_seconds()
                if wait_seconds > 0:
                    logger.info(f"Rate limit reached, waiting {wait_seconds:.1f}s")
                    await asyncio.sleep(wait_seconds)

            self._request_times.append(now)

    def _get_cached(self, cache_key: str) -> Optional[ContextualizedEmbeddingResponse]:
        """Get cached embedding if valid."""
        if cache_key not in self.cache:
            return None

        response, cached_at = self.cache[cache_key]

        # Check TTL
        if datetime.now() - cached_at > self.cache_ttl:
            del self.cache[cache_key]
            return None

        # Return cached response
        return ContextualizedEmbeddingResponse(
            embeddings=response.embeddings,
            model=response.model,
            total_tokens=response.total_tokens,
            cached=True,
            cost_usd=0.0,
        )

    def _cache_response(self, cache_key: str, response: ContextualizedEmbeddingResponse):
        """Cache embedding response."""
        self.cache[cache_key] = (response, datetime.now())

    async def embed_document(
        self,
        chunks: List[str],
        model: str = "voyage-context-3",
        input_type: str = "document",
        output_dimension: int = 1024,
    ) -> ContextualizedEmbeddingResponse:
        """
        Embed document chunks with global context.

        Args:
            chunks: List of text chunks from the same document
            model: voyage-context-3 (only supported model)
            input_type: "document" for indexing, "query" for search
            output_dimension: 256, 512, 1024 (default), or 2048

        Returns:
            ContextualizedEmbeddingResponse with embeddings for each chunk
        """
        self._validate_model(model)

        # Check cache
        cache_key = self._cache_key(chunks, model, input_type)
        cached = self._get_cached(cache_key)
        if cached:
            self.cost_tracker.add_request(model, cached.total_tokens, cached=True)
            logger.debug(f"Cache hit for document with {len(chunks)} chunks")
            return cached

        # Rate limit
        await self._check_rate_limit()

        # Call API with contextualized_embed
        try:
            result = await self.client.contextualized_embed(
                inputs=[chunks],  # Single document
                model=model,
                input_type=input_type,
                output_dimension=output_dimension,
            )

            # Extract response (result.results is a list of ContextualizedEmbeddingsResult objects)
            embeddings = result.results[0].embeddings  # First (and only) document
            tokens = result.total_tokens

            # Track cost
            cost = self.cost_tracker.add_request(model, tokens, cached=False)

            response = ContextualizedEmbeddingResponse(
                embeddings=embeddings,
                model=model,
                total_tokens=tokens,
                cached=False,
                cost_usd=cost,
            )

            # Cache
            self._cache_response(cache_key, response)

            logger.debug(
                f"Embedded {len(chunks)} chunks with {model}: "
                f"{tokens} tokens, ${cost:.6f}"
            )

            return response

        except Exception as e:
            logger.error(f"Contextualized embedding failed: {e}")
            raise

    async def embed_documents_batch(
        self,
        documents: List[List[str]],
        model: str = "voyage-context-3",
        input_type: str = "document",
        output_dimension: int = 1024,
    ) -> List[ContextualizedEmbeddingResponse]:
        """
        Embed multiple documents in batch.

        Args:
            documents: List of documents (each document is a list of chunks)
            model: voyage-context-3
            input_type: "document" for indexing, "query" for search
            output_dimension: 256, 512, 1024 (default), or 2048

        Returns:
            List of ContextualizedEmbeddingResponse (one per document)
        """
        self._validate_model(model)

        # Check cache for all documents
        responses: List[Optional[ContextualizedEmbeddingResponse]] = []
        uncached_indices: List[int] = []
        uncached_docs: List[List[str]] = []

        for i, chunks in enumerate(documents):
            cache_key = self._cache_key(chunks, model, input_type)
            cached = self._get_cached(cache_key)

            if cached:
                self.cost_tracker.add_request(model, cached.total_tokens, cached=True)
                responses.append(cached)
            else:
                responses.append(None)
                uncached_indices.append(i)
                uncached_docs.append(chunks)

        # If all cached, return
        if not uncached_docs:
            logger.debug(f"All {len(documents)} documents cached")
            return responses  # type: ignore

        logger.debug(
            f"Batch: {len(documents)} total, {len(uncached_docs)} uncached"
        )

        # Rate limit
        await self._check_rate_limit()

        # Embed uncached documents
        try:
            result = await self.client.contextualized_embed(
                inputs=uncached_docs,
                model=model,
                input_type=input_type,
                output_dimension=output_dimension,
            )

            # Process results (result.results is a list of ContextualizedEmbeddingsResult objects)
            for i, (doc_chunks, result_obj) in enumerate(
                zip(uncached_docs, result.results)
            ):
                embeddings = result_obj.embeddings
                # Estimate tokens per document
                tokens = result.total_tokens // len(uncached_docs)
                cost = self.cost_tracker.add_request(model, tokens, cached=False)

                response = ContextualizedEmbeddingResponse(
                    embeddings=embeddings,
                    model=model,
                    total_tokens=tokens,
                    cached=False,
                    cost_usd=cost,
                )

                # Cache
                cache_key = self._cache_key(doc_chunks, model, input_type)
                self._cache_response(cache_key, response)

                # Store in results
                original_idx = uncached_indices[i]
                responses[original_idx] = response

            logger.debug(
                f"Embedded batch of {len(uncached_docs)} documents: "
                f"{result.total_tokens} tokens"
            )

            return responses  # type: ignore

        except Exception as e:
            logger.error(f"Batch contextualized embedding failed: {e}")
            raise

    async def embed_documents_grouped(
        self,
        documents: List[List[str]],
        model: str = "voyage-context-3",
        input_type: str = "document",
        output_dimension: int = 1024,
    ) -> List[ContextualizedEmbeddingResponse]:
        """
        Contract alias: embed ordered chunk lists grouped by document.
        """
        return await self.embed_documents_batch(
            documents=documents,
            model=model,
            input_type=input_type,
            output_dimension=output_dimension,
        )

    def clear_cache(self):
        """Clear embedding cache."""
        self.cache.clear()
        logger.info("Contextualized embedding cache cleared")

    def get_cost_summary(self) -> Dict:
        """Get cost tracking summary."""
        return self.cost_tracker.summary()


# Example usage
async def main():
    """Example usage of ContextualizedEmbedder."""
    import os

    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        logger.info("Set VOYAGE_API_KEY environment variable")
        return

    embedder = ContextualizedEmbedder(api_key=api_key, cache_ttl_hours=24)

    # Single document
    doc_chunks = [
        "Chapter 1: Introduction to Python",
        "Python is a high-level programming language.",
        "It supports multiple paradigms including OOP and functional.",
    ]

    response = await embedder.embed_document(
        chunks=doc_chunks,
        model="voyage-context-3",
        input_type="document",
    )
    logger.info(f"Single doc: {len(response.embeddings)} chunks, ${response.cost_usd:.6f}")

    # Batch documents
    docs = [
        ["Doc 1 chunk 1", "Doc 1 chunk 2"],
        ["Doc 2 chunk 1", "Doc 2 chunk 2", "Doc 2 chunk 3"],
    ]

    responses = await embedder.embed_documents_batch(
        documents=docs,
        model="voyage-context-3",
        input_type="document",
    )
    logger.info(f"Batch: {len(responses)} documents")

    # Cost summary
    summary = embedder.get_cost_summary()
    logger.info(f"Cost summary: {summary}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
