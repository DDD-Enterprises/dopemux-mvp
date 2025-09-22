"""
Voyage AI integration for embeddings and reranking.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from voyageai import Client as VoyageClient

from .config import DocRAGConfig
from .models import SearchResult

logger = structlog.get_logger(__name__)


class VoyageEmbeddings:
    """Voyage AI embedding and reranking service."""

    def __init__(self, config: DocRAGConfig):
        """Initialize Voyage AI client."""
        self.config = config
        self.client = VoyageClient(api_key=config.voyage.api_key)
        self._http_client = httpx.AsyncClient(timeout=config.voyage.timeout)

    async def close(self) -> None:
        """Close HTTP client."""
        await self._http_client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return await self.embed_texts([text])[0]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        try:
            # Use sync client in async context with run_in_executor
            loop = asyncio.get_event_loop()

            result = await loop.run_in_executor(
                None,
                lambda: self.client.embed(
                    texts=texts,
                    model=self.config.voyage.embed_model,
                ),
            )

            embeddings = result.embeddings

            logger.debug(
                "Generated embeddings",
                count=len(texts),
                model=self.config.voyage.embed_model,
                dimension=len(embeddings[0]) if embeddings else 0,
            )

            return embeddings

        except Exception as e:
            logger.error("Failed to generate embeddings", error=str(e))
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> List[Tuple[int, float]]:
        """Rerank documents using Voyage reranker.

        Returns:
            List of (original_index, rerank_score) tuples sorted by score desc.
        """
        if not documents:
            return []

        if top_k is None:
            top_k = len(documents)

        try:
            # Use sync client in async context
            loop = asyncio.get_event_loop()

            result = await loop.run_in_executor(
                None,
                lambda: self.client.rerank(
                    query=query,
                    documents=documents,
                    model=self.config.voyage.rerank_model,
                    top_k=min(top_k, len(documents)),
                ),
            )

            # Extract results
            rerank_results = []
            for item in result.results:
                rerank_results.append((item.index, item.relevance_score))

            logger.debug(
                "Reranked documents",
                original_count=len(documents),
                reranked_count=len(rerank_results),
                model=self.config.voyage.rerank_model,
            )

            return rerank_results

        except Exception as e:
            logger.error("Failed to rerank documents", error=str(e))
            raise

    async def rerank_search_results(
        self,
        query: str,
        results: List[SearchResult],
        top_k: Optional[int] = None,
    ) -> List[SearchResult]:
        """Rerank search results and update their scores."""
        if not results:
            return []

        if top_k is None:
            top_k = len(results)

        # Extract document texts
        documents = [result.text for result in results]

        # Get reranking scores
        rerank_results = await self.rerank(query, documents, top_k)

        # Update search results with rerank scores
        reranked_results = []
        for original_idx, rerank_score in rerank_results:
            result = results[original_idx]
            result.rerank_score = rerank_score
            reranked_results.append(result)

        # Sort by rerank score
        reranked_results.sort(key=lambda x: x.rerank_score or 0, reverse=True)

        return reranked_results[:top_k]

    async def health_check(self) -> bool:
        """Check if Voyage AI service is available."""
        try:
            # Try a simple embedding request
            await self.embed_text("health check")
            return True

        except Exception as e:
            logger.error("Voyage AI health check failed", error=str(e))
            return False


class SparseEncoder:
    """Simple sparse vector encoder for hybrid search."""

    def __init__(self):
        """Initialize sparse encoder."""
        # This is a simplified implementation
        # In production, you might use BGE-M3, SPLADE, or similar models
        pass

    def encode(self, text: str) -> Dict[str, float]:
        """Encode text to sparse vector representation.

        This is a simplified TF-IDF-like approach.
        For production, consider using BGE-M3 or SPLADE models.
        """
        # Simple tokenization and TF computation
        words = text.lower().split()
        word_counts = {}

        for word in words:
            # Simple preprocessing
            word = word.strip('.,!?;:"()[]{}')
            if len(word) > 2:  # Skip very short words
                word_counts[word] = word_counts.get(word, 0) + 1

        # Normalize by document length
        total_words = len(words)
        if total_words == 0:
            return {}

        # Simple TF normalization
        sparse_vector = {}
        for word, count in word_counts.items():
            tf = count / total_words
            if tf > 0.01:  # Only include significant terms
                sparse_vector[word] = tf

        return sparse_vector

    async def encode_texts(self, texts: List[str]) -> List[Dict[str, float]]:
        """Encode multiple texts to sparse vectors."""
        return [self.encode(text) for text in texts]