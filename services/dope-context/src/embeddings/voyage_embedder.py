"""
VoyageAI Embedder - Task 1
Multi-vector embedding generation with caching and cost tracking.
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Literal, Optional, Tuple

import voyageai
from voyageai import AsyncClient


logger = logging.getLogger(__name__)


@dataclass
class EmbeddingRequest:
    """Single embedding request with metadata."""

    text: str
    model: Literal["voyage-code-3", "voyage-3-lite", "voyage-context-3"]
    input_type: Literal["document", "query"]
    truncation: bool = True

    def cache_key(self) -> str:
        """Generate cache key from request params."""
        content = f"{self.model}:{self.input_type}:{self.text}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class EmbeddingResponse:
    """Embedding response with metadata."""

    embedding: List[float]
    model: str
    tokens: int
    cached: bool = False
    cost_usd: float = 0.0


@dataclass
class CostTracker:
    """Track embedding API costs."""

    total_tokens: int = 0
    total_requests: int = 0
    total_cost_usd: float = 0.0
    cache_hits: int = 0

    # Voyage pricing (per 1M tokens)
    PRICING = {
        "voyage-code-3": 0.12,
        "voyage-3-lite": 0.04,
        "voyage-context-3": 0.12,
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


class VoyageEmbedder:
    """
    VoyageAI embedding client with:
    - Multi-model support (voyage-code-3, voyage-3-lite, voyage-context-3)
    - Request batching (up to 128 texts per call)
    - In-memory caching with TTL
    - Cost tracking
    - Rate limiting
    """

    def __init__(
        self,
        api_key: str,
        cache_ttl_hours: int = 24,
        max_batch_size: int = 128,
        rate_limit_rpm: int = 300,
        default_model: str = "voyage-code-3",
    ):
        """
        Initialize VoyageAI embedder.

        Args:
            api_key: VoyageAI API key
            cache_ttl_hours: Cache TTL in hours (default 24h)
            max_batch_size: Max texts per batch (default 128, Voyage limit)
            rate_limit_rpm: Requests per minute (default 300)
            default_model: Default embedding model (voyage-code-3 for code, voyage-context-3 for docs)
        """
        self.default_model = default_model
        self.client = AsyncClient(api_key=api_key)
        self.cache: Dict[str, Tuple[EmbeddingResponse, datetime]] = {}
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.max_batch_size = max_batch_size
        self.rate_limit_rpm = rate_limit_rpm
        self.cost_tracker = CostTracker()

        # Rate limiting
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()

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

    def _get_cached(self, cache_key: str) -> Optional[EmbeddingResponse]:
        """Get cached embedding if valid."""
        if cache_key not in self.cache:
            return None

        response, cached_at = self.cache[cache_key]

        # Check TTL
        if datetime.now() - cached_at > self.cache_ttl:
            del self.cache[cache_key]
            return None

        # Return cached response
        cached_response = EmbeddingResponse(
            embedding=response.embedding,
            model=response.model,
            tokens=response.tokens,
            cached=True,
            cost_usd=0.0,
        )
        return cached_response

    def _cache_response(self, cache_key: str, response: EmbeddingResponse):
        """Cache embedding response."""
        self.cache[cache_key] = (response, datetime.now())

    async def embed(
        self,
        text: str,
        model: Optional[
            Literal["voyage-code-3", "voyage-3-lite", "voyage-context-3"]
        ] = None,
        input_type: Literal["document", "query"] = "document",
        truncation: bool = True,
    ) -> EmbeddingResponse:
        """
        Embed single text with caching.

        Args:
            text: Text to embed
            model: Voyage model to use (defaults to default_model)
            input_type: "document" for indexing, "query" for search
            truncation: Truncate to model's max length

        Returns:
            EmbeddingResponse with vector and metadata
        """
        if model is None:
            model = self.default_model

        request = EmbeddingRequest(
            text=text,
            model=model,
            input_type=input_type,
            truncation=truncation,
        )

        # Check cache
        cache_key = request.cache_key()
        cached = self._get_cached(cache_key)
        if cached:
            self.cost_tracker.add_request(model, cached.tokens, cached=True)
            logger.debug(f"Cache hit for {model}")
            return cached

        # Rate limit
        await self._check_rate_limit()

        # Call API
        try:
            result = await self.client.embed(
                texts=[text],
                model=model,
                input_type=input_type,
                truncation=truncation,
            )

            # Extract response
            embedding = result.embeddings[0]
            tokens = result.total_tokens

            # Track cost
            cost = self.cost_tracker.add_request(model, tokens, cached=False)

            response = EmbeddingResponse(
                embedding=embedding,
                model=model,
                tokens=tokens,
                cached=False,
                cost_usd=cost,
            )

            # Cache
            self._cache_response(cache_key, response)

            logger.debug(f"Embedded 1 text with {model}: {tokens} tokens, ${cost:.6f}")

            return response

        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    async def embed_batch(
        self,
        texts: List[str],
        model: Literal[
            "voyage-code-3", "voyage-3-lite", "voyage-context-3"
        ] = "voyage-code-3",
        input_type: Literal["document", "query"] = "document",
        truncation: bool = True,
    ) -> List[EmbeddingResponse]:
        """
        Embed batch of texts with caching and batching.

        Automatically splits into sub-batches of max_batch_size.

        Args:
            texts: List of texts to embed
            model: Voyage model to use
            input_type: "document" for indexing, "query" for search
            truncation: Truncate to model's max length

        Returns:
            List of EmbeddingResponse in same order as input
        """
        if not texts:
            return []

        # Check cache for all texts
        responses: List[Optional[EmbeddingResponse]] = []
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        for i, text in enumerate(texts):
            request = EmbeddingRequest(
                text=text,
                model=model,
                input_type=input_type,
                truncation=truncation,
            )
            cache_key = request.cache_key()
            cached = self._get_cached(cache_key)

            if cached:
                self.cost_tracker.add_request(model, cached.tokens, cached=True)
                responses.append(cached)
            else:
                responses.append(None)
                uncached_indices.append(i)
                uncached_texts.append(text)

        # If all cached, return
        if not uncached_texts:
            logger.debug(f"All {len(texts)} texts cached")
            return responses  # type: ignore

        logger.debug(f"Batch: {len(texts)} total, {len(uncached_texts)} uncached")

        # Split into sub-batches
        sub_batches = [
            uncached_texts[i : i + self.max_batch_size]
            for i in range(0, len(uncached_texts), self.max_batch_size)
        ]

        # Embed all sub-batches
        all_embeddings: List[EmbeddingResponse] = []

        for batch in sub_batches:
            await self._check_rate_limit()

            try:
                result = await self.client.embed(
                    texts=batch,
                    model=model,
                    input_type=input_type,
                    truncation=truncation,
                )

                # Process results
                for j, embedding in enumerate(result.embeddings):
                    original_text = batch[j]

                    # Estimate tokens (total / count)
                    tokens = result.total_tokens // len(batch)
                    cost = self.cost_tracker.add_request(model, tokens, cached=False)

                    response = EmbeddingResponse(
                        embedding=embedding,
                        model=model,
                        tokens=tokens,
                        cached=False,
                        cost_usd=cost,
                    )

                    # Cache
                    request = EmbeddingRequest(
                        text=original_text,
                        model=model,
                        input_type=input_type,
                        truncation=truncation,
                    )
                    self._cache_response(request.cache_key(), response)

                    all_embeddings.append(response)

                logger.debug(
                    f"Embedded batch of {len(batch)} with {model}: "
                    f"{result.total_tokens} tokens"
                )

            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                raise

        # Merge cached and new embeddings
        for idx, response in zip(uncached_indices, all_embeddings):
            responses[idx] = response

        return responses  # type: ignore

    def clear_cache(self):
        """Clear embedding cache."""
        self.cache.clear()
        logger.info("Embedding cache cleared")

    def get_cost_summary(self) -> Dict:
        """Get cost tracking summary."""
        return self.cost_tracker.summary()


# Example usage
async def main():
    """Example usage of VoyageEmbedder."""
    import os

    api_key = os.getenv("VOYAGE_API_KEY")
    if not api_key:
        print("Set VOYAGE_API_KEY environment variable")
        return

    embedder = VoyageEmbedder(api_key=api_key, cache_ttl_hours=24)

    # Single embedding
    response = await embedder.embed(
        text="async def process_request(data: dict):",
        model="voyage-code-3",
        input_type="document",
    )
    print(f"Single embedding: {len(response.embedding)}d, ${response.cost_usd:.6f}")

    # Batch embedding
    code_chunks = [
        "def calculate_total(items: List[Item]) -> float:",
        "class UserService:",
        "async with session.begin():",
    ]

    responses = await embedder.embed_batch(
        texts=code_chunks,
        model="voyage-code-3",
        input_type="document",
    )
    print(f"Batch: {len(responses)} embeddings")

    # Cost summary
    summary = embedder.get_cost_summary()
    print(f"Cost summary: {summary}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
