"""
Voyage AI provider implementation for embeddings and reranking.

Implements the voyage-context-3 embedding model and voyage-rerank-2.5
with ADHD-optimized error handling and comprehensive cost tracking.
"""

import asyncio
import logging
import time
from types import SimpleNamespace
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

# Import the global error handling framework
from ..error_handling import (
    GlobalErrorHandler,
    with_error_handling,
    create_dopemux_error,
    ErrorType,
    ErrorSeverity,
    RetryPolicy
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

        # Initialize error handling framework
        self.error_handler = GlobalErrorHandler("voyage_api_client")

        # Register retry policy for API calls (gentle backoff for external APIs)
        api_retry_policy = RetryPolicy(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=15.0,
            backoff_factor=2.0,
            jitter=True
        )
        self.error_handler.register_retry_policy("api_retry", api_retry_policy)

        if not self.api_key:
            logger.warning("🔑 Voyage API key not configured - set VOYAGE_API_KEY environment variable")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    @with_error_handling("embed_texts", retry_policy="api_retry")
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
            # Convert HTTP errors to DopemuxError for consistent handling
            if self.config.gentle_error_messages:
                logger.error(f"💙 API request had trouble: {e}. Taking a short break and trying again...")
            else:
                logger.error(f"Voyage API error: {e}")

            # Determine error type based on HTTP status
            if hasattr(e, 'response') and e.response:
                if e.response.status_code == 429:
                    error_type = ErrorType.RATE_LIMIT
                    severity = ErrorSeverity.MEDIUM
                elif e.response.status_code >= 500:
                    error_type = ErrorType.SERVICE_UNAVAILABLE
                    severity = ErrorSeverity.HIGH
                elif e.response.status_code >= 400:
                    error_type = ErrorType.AUTHENTICATION if e.response.status_code == 401 else ErrorType.DATA_VALIDATION
                    severity = ErrorSeverity.MEDIUM
                else:
                    error_type = ErrorType.NETWORK
                    severity = ErrorSeverity.MEDIUM
            else:
                error_type = ErrorType.NETWORK
                severity = ErrorSeverity.MEDIUM

            raise create_dopemux_error(
                error_type=error_type,
                severity=severity,
                message=f"Voyage API request failed: {e}",
                service_name="voyage_api_client",
                operation="embed_texts",
                details={"http_error": str(e), "texts_count": len(texts)}
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error during embedding: {e}")
            raise create_dopemux_error(
                error_type=ErrorType.UNKNOWN,
                severity=ErrorSeverity.HIGH,
                message=f"Unexpected embedding error: {e}",
                service_name="voyage_api_client",
                operation="embed_texts",
                details={"error": str(e), "texts_count": len(texts)}
            ) from e

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

    @with_error_handling("rerank", retry_policy="api_retry")
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
            # Convert HTTP errors to DopemuxError for consistent handling
            if self.config.gentle_error_messages:
                logger.error(f"💙 Reranking had trouble: {e}. Your search results might be slightly less optimal, but still good!")
            else:
                logger.error(f"Voyage rerank error: {e}")

            # Determine error type based on HTTP status
            if hasattr(e, 'response') and e.response:
                if e.response.status_code == 429:
                    error_type = ErrorType.RATE_LIMIT
                    severity = ErrorSeverity.MEDIUM
                elif e.response.status_code >= 500:
                    error_type = ErrorType.SERVICE_UNAVAILABLE
                    severity = ErrorSeverity.HIGH
                elif e.response.status_code >= 400:
                    error_type = ErrorType.AUTHENTICATION if e.response.status_code == 401 else ErrorType.DATA_VALIDATION
                    severity = ErrorSeverity.MEDIUM
                else:
                    error_type = ErrorType.NETWORK
                    severity = ErrorSeverity.MEDIUM
            else:
                error_type = ErrorType.NETWORK
                severity = ErrorSeverity.MEDIUM

            raise create_dopemux_error(
                error_type=error_type,
                severity=severity,
                message=f"Voyage API reranking failed: {e}",
                service_name="voyage_api_client",
                operation="rerank",
                details={"http_error": str(e), "documents_count": len(documents)}
            ) from e

        except Exception as e:
            logger.error(f"Unexpected error during reranking: {e}")
            raise create_dopemux_error(
                error_type=ErrorType.UNKNOWN,
                severity=ErrorSeverity.HIGH,
                message=f"Unexpected reranking error: {e}",
                service_name="voyage_api_client",
                operation="rerank",
                details={"error": str(e), "documents_count": len(documents)}
            ) from e

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

    async def validate_connection(self) -> bool:
        """Backward-compatible alias for connection health checks."""
        return await self.test_connection()

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

    async def get_health_metrics(self):
        """Return provider health metrics in an attribute-friendly object."""
        return SimpleNamespace(
            provider_name="voyage",
            total_requests=self.total_requests,
            total_tokens=self.total_tokens,
            embedding_requests=self.embedding_requests,
            rerank_requests=self.rerank_requests,
        )
