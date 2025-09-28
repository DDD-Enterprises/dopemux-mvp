"""
Voyage AI provider implementation for embeddings and reranking.

Implements the voyage-context-3 embedding model and voyage-rerank-2.5
with ADHD-optimized error handling and comprehensive cost tracking.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional

import httpx

from ..core import (
    AdvancedEmbeddingConfig,
    EmbeddingProvider,
    RerankProvider,
    EmbeddingError,
    RerankError,
    AsyncContextManager
)

logger = logging.getLogger(__name__)


class VoyageAPIClient(EmbeddingProvider, RerankProvider, AsyncContextManager):
    """
    Async Voyage AI API client with ADHD-optimized error handling.

    Implements both embedding and reranking capabilities using Voyage AI's
    voyage-context-3 and voyage-rerank-2.5 models with comprehensive
    cost tracking and gentle error messaging.
    """

    def __init__(self, config: AdvancedEmbeddingConfig):
        """
        Initialize the Voyage API client.

        Args:
            config: Advanced embedding configuration with API settings

        Raises:
            ValueError: If API key is not configured
        """
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.request_timeout,
            limits=httpx.Limits(max_connections=config.max_concurrent_requests)
        )
        self.api_key = config.voyage_api_key

        # Cost tracking
        self.total_tokens = 0
        self.total_requests = 0
        self.embedding_requests = 0
        self.rerank_requests = 0

        if not self.api_key:
            logger.warning("🔑 Voyage API key not configured - set VOYAGE_API_KEY environment variable")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using voyage-context-3.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (2048-dimensional)

        Raises:
            EmbeddingError: When embedding generation fails
        """
        if not self.api_key:
            raise EmbeddingError("🔑 Voyage API key not configured")

        if not texts:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.embedding_model,
            "input": texts,
            "encoding_format": "float"
        }

        try:
            start_time = time.time()

            response = await self.client.post(
                f"{self.config.api_base_url}/embeddings",
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            result = response.json()
            embeddings = [item["embedding"] for item in result["data"]]

            # Track usage
            self.total_tokens += result.get("usage", {}).get("total_tokens", 0)
            self.total_requests += 1
            self.embedding_requests += 1

            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"✅ Generated {len(embeddings)} embeddings in {processing_time:.1f}ms")

            return embeddings

        except httpx.HTTPError as e:
            if self.config.gentle_error_messages:
                logger.error(f"💙 API request had trouble: {e}. Taking a short break and trying again...")
            else:
                logger.error(f"Voyage API error: {e}")
            raise EmbeddingError(f"Voyage embedding failed: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error during embedding: {e}")
            raise EmbeddingError(f"Unexpected embedding error: {e}") from e

    async def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.

        Args:
            query: Query text to embed

        Returns:
            Query embedding vector (2048-dimensional)

        Raises:
            EmbeddingError: When embedding generation fails
        """
        embeddings = await self.embed_texts([query])
        return embeddings[0] if embeddings else []

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this provider."""
        return self.config.embedding_dimension

    async def rerank(self, query: str, documents: List[str]) -> List[float]:
        """
        Rerank documents using voyage-rerank-2.5.

        Args:
            query: Search query
            documents: List of documents to rerank

        Returns:
            List of relevance scores (0.0 to 1.0)

        Raises:
            RerankError: When reranking fails
        """
        if not self.api_key:
            raise RerankError("🔑 Voyage API key not configured")

        if not documents:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config.rerank_model,
            "query": query,
            "documents": documents,
            "return_documents": False,
            "top_k": len(documents)  # Return scores for all documents
        }

        try:
            start_time = time.time()

            response = await self.client.post(
                f"{self.config.api_base_url}/rerank",
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            result = response.json()
            scores = [item["relevance_score"] for item in result["results"]]

            self.total_requests += 1
            self.rerank_requests += 1

            processing_time = (time.time() - start_time) * 1000
            logger.debug(f"✅ Reranked {len(documents)} documents in {processing_time:.1f}ms")

            return scores

        except httpx.HTTPError as e:
            if self.config.gentle_error_messages:
                logger.error(f"💙 Reranking had trouble: {e}. Your search results might be slightly less optimal, but still good!")
            else:
                logger.error(f"Voyage rerank error: {e}")
            raise RerankError(f"Voyage reranking failed: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected error during reranking: {e}")
            raise RerankError(f"Unexpected reranking error: {e}") from e

    def get_cost_estimate(self) -> Dict[str, float]:
        """
        Estimate API costs based on usage.

        Returns:
            Dictionary with cost breakdown and usage metrics
        """
        # Voyage AI pricing (approximate - check current rates)
        embedding_cost_per_1k = 0.10  # $0.10 per 1K tokens
        rerank_cost_per_1k = 0.03     # $0.03 per 1K queries

        embedding_cost = (self.total_tokens / 1000) * embedding_cost_per_1k
        rerank_cost = (self.rerank_requests / 1000) * rerank_cost_per_1k

        return {
            "embedding_cost": embedding_cost,
            "rerank_cost": rerank_cost,
            "total_cost": embedding_cost + rerank_cost,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "embedding_requests": self.embedding_requests,
            "rerank_requests": self.rerank_requests,
            "avg_tokens_per_request": self.total_tokens / max(self.embedding_requests, 1)
        }

    async def test_connection(self) -> bool:
        """
        Test the API connection with a simple embedding request.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.embed_texts(["test connection"])
            logger.info("✅ Voyage API connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Voyage API connection test failed: {e}")
            return False

    def reset_usage_tracking(self):
        """Reset usage tracking counters (e.g., for monthly reset)."""
        self.total_tokens = 0
        self.total_requests = 0
        self.embedding_requests = 0
        self.rerank_requests = 0
        logger.info("🔄 Voyage API usage tracking reset")

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get current usage statistics.

        Returns:
            Dictionary with usage metrics
        """
        return {
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests,
            "embedding_requests": self.embedding_requests,
            "rerank_requests": self.rerank_requests
        }