#!/usr/bin/env python3
"""
Voyage AI Integration Module

Provides vector embedding capabilities using Voyage AI's context-aware models.
Optimized for conversational data and long-context understanding.

Models:
- voyage-3: High-performance embeddings for general use (<512 tokens)
- voyage-context-3: Long-context embeddings for extended content (512-4096 tokens)
"""

import os
import time
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
import hashlib
import json
import logging
from datetime import datetime, timedelta

import httpx
import numpy as np
from redis import Redis
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class EmbeddingRequest:
    """Represents a single embedding request."""
    text: str
    model: str
    chunk_id: str
    metadata: Dict[str, Any] = None

@dataclass
class EmbeddingResult:
    """Represents the result of an embedding operation."""
    chunk_id: str
    text: str
    embedding: List[float]
    model: str
    token_count: int
    metadata: Dict[str, Any] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

class VoyageEmbeddingCache:
    """Redis-based caching for embeddings to avoid reprocessing."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis = Redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            self.cache_enabled = True
            logger.info("Voyage embedding cache connected to Redis")
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}")
            self.cache_enabled = False

    def _cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model combination."""
        content_hash = hashlib.sha256(f"{text}:{model}".encode()).hexdigest()
        return f"voyage_embedding:{model}:{content_hash[:16]}"

    def get(self, text: str, model: str) -> Optional[EmbeddingResult]:
        """Retrieve cached embedding if available."""
        if not self.cache_enabled:
            return None

        try:
            key = self._cache_key(text, model)
            cached = self.redis.get(key)
            if cached:
                data = json.loads(cached)
                return EmbeddingResult(**data)
        except Exception as e:
            logger.warning(f"Cache retrieval error: {e}")
        return None

    def set(self, result: EmbeddingResult, ttl: int = 86400 * 7) -> None:
        """Cache embedding result for 7 days by default."""
        if not self.cache_enabled:
            return

        try:
            key = self._cache_key(result.text, result.model)
            data = asdict(result)
            self.redis.setex(key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache storage error: {e}")

class VoyageClient:
    """
    Client for Voyage AI embedding API with ADHD-friendly features.

    Features:
    - Automatic model selection based on text length
    - Batch processing with rate limiting
    - Progress visualization
    - Caching for efficiency
    - Error handling and retries
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_enabled: bool = True,
        redis_url: str = "redis://localhost:6379/0"
    ):
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Voyage API key required. Set VOYAGE_API_KEY environment variable.")

        self.base_url = "https://api.voyageai.com/v1"
        self.cache = VoyageEmbeddingCache(redis_url) if cache_enabled else None

        # Model configurations
        self.models = {
            "voyage-3": {
                "max_tokens": 512,
                "embedding_dim": 1024,
                "cost_per_1k": 0.00012  # USD
            },
            "voyage-context-3": {
                "max_tokens": 4096,
                "embedding_dim": 1024,
                "cost_per_1k": 0.00012  # USD
            }
        }

        # Rate limiting
        self.max_requests_per_minute = 300
        self.max_tokens_per_minute = 1_000_000
        self.request_timestamps = []
        self.token_usage = []

    def _select_model(self, text: str) -> str:
        """Automatically select best model based on text length."""
        # Rough token estimation (1 token ~= 4 chars for English)
        estimated_tokens = len(text) // 4

        if estimated_tokens <= 512:
            return "voyage-3"
        elif estimated_tokens <= 4096:
            return "voyage-context-3"
        else:
            # Text too long, will need chunking
            logger.warning(f"Text length {estimated_tokens} tokens exceeds max. Consider chunking.")
            return "voyage-context-3"

    def _check_rate_limits(self, token_count: int) -> float:
        """Check rate limits and return delay if needed."""
        now = time.time()
        minute_ago = now - 60

        # Clean old timestamps
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > minute_ago]
        self.token_usage = [(ts, tokens) for ts, tokens in self.token_usage if ts > minute_ago]

        # Check request rate
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            return 60 - (now - self.request_timestamps[0])

        # Check token rate
        current_tokens = sum(tokens for _, tokens in self.token_usage)
        if current_tokens + token_count > self.max_tokens_per_minute:
            return 60 - (now - self.token_usage[0][0])

        return 0

    async def _make_request(
        self,
        texts: List[str],
        model: str,
        client: httpx.AsyncClient
    ) -> Dict[str, Any]:
        """Make API request to Voyage with rate limiting."""

        # Estimate tokens for rate limiting
        estimated_tokens = sum(len(text) // 4 for text in texts)

        # Check rate limits
        delay = self._check_rate_limits(estimated_tokens)
        if delay > 0:
            logger.info(f"Rate limit reached, waiting {delay:.1f}s")
            await asyncio.sleep(delay)

        # Track usage
        now = time.time()
        self.request_timestamps.append(now)
        self.token_usage.append((now, estimated_tokens))

        # Make request
        payload = {
            "input": texts,
            "model": model,
            "input_type": "document"  # Optimized for document embedding
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = await client.post(
            f"{self.base_url}/embeddings",
            json=payload,
            headers=headers,
            timeout=30.0
        )

        response.raise_for_status()
        return response.json()

    async def embed_single(
        self,
        text: str,
        model: Optional[str] = None,
        chunk_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmbeddingResult:
        """Embed a single text with caching support."""

        # Auto-select model if not specified
        if model is None:
            model = self._select_model(text)

        # Generate chunk ID if not provided
        if chunk_id is None:
            chunk_id = hashlib.sha256(text.encode()).hexdigest()[:12]

        # Check cache first
        if self.cache:
            cached = self.cache.get(text, model)
            if cached:
                logger.debug(f"Cache hit for chunk {chunk_id}")
                return cached

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await self._make_request([text], model, client)

        # Extract embedding
        embedding = response["data"][0]["embedding"]
        token_count = response["usage"]["total_tokens"]

        # Create result
        result = EmbeddingResult(
            chunk_id=chunk_id,
            text=text,
            embedding=embedding,
            model=model,
            token_count=token_count,
            metadata=metadata or {}
        )

        # Cache result
        if self.cache:
            self.cache.set(result)

        return result

    async def embed_batch(
        self,
        requests: List[EmbeddingRequest],
        batch_size: int = 128,
        show_progress: bool = True
    ) -> List[EmbeddingResult]:
        """Embed multiple texts in batches with progress tracking."""

        results = []

        # Group by model for efficient batching
        model_groups = {}
        for req in requests:
            model = req.model or self._select_model(req.text)
            if model not in model_groups:
                model_groups[model] = []
            model_groups[model].append(req)

        total_requests = len(requests)
        processed = 0

        if show_progress:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
                TimeElapsedColumn(),
                console=console
            )
            task = progress.add_task("Embedding texts...", total=total_requests)
            progress.start()

        try:
            async with httpx.AsyncClient() as client:
                for model, model_requests in model_groups.items():

                    # Process in batches
                    for i in range(0, len(model_requests), batch_size):
                        batch = model_requests[i:i + batch_size]

                        # Check cache for each request
                        cached_results = []
                        api_requests = []

                        for req in batch:
                            if self.cache:
                                cached = self.cache.get(req.text, model)
                                if cached:
                                    cached_results.append(cached)
                                    continue
                            api_requests.append(req)

                        # Make API request for non-cached items
                        if api_requests:
                            texts = [req.text for req in api_requests]
                            response = await self._make_request(texts, model, client)

                            # Process response
                            for j, req in enumerate(api_requests):
                                embedding = response["data"][j]["embedding"]
                                token_count = response["usage"]["total_tokens"] // len(api_requests)

                                result = EmbeddingResult(
                                    chunk_id=req.chunk_id,
                                    text=req.text,
                                    embedding=embedding,
                                    model=model,
                                    token_count=token_count,
                                    metadata=req.metadata or {}
                                )

                                # Cache result
                                if self.cache:
                                    self.cache.set(result)

                                results.append(result)

                        # Add cached results
                        results.extend(cached_results)

                        # Update progress
                        processed += len(batch)
                        if show_progress:
                            progress.update(
                                task,
                                advance=len(batch),
                                description=f"Embedding with {model}... [{processed}/{total_requests}]"
                            )

                        # Small delay between batches
                        await asyncio.sleep(0.1)

        finally:
            if show_progress:
                progress.stop()

        # Sort results to match input order
        result_map = {r.chunk_id: r for r in results}
        ordered_results = [result_map[req.chunk_id] for req in requests]

        return ordered_results

    def calculate_cost(self, results: List[EmbeddingResult]) -> Dict[str, Any]:
        """Calculate cost breakdown for embedding requests."""
        cost_breakdown = {}
        total_cost = 0
        total_tokens = 0

        for result in results:
            model = result.model
            tokens = result.token_count
            cost = (tokens / 1000) * self.models[model]["cost_per_1k"]

            if model not in cost_breakdown:
                cost_breakdown[model] = {
                    "tokens": 0,
                    "cost": 0,
                    "requests": 0
                }

            cost_breakdown[model]["tokens"] += tokens
            cost_breakdown[model]["cost"] += cost
            cost_breakdown[model]["requests"] += 1

            total_cost += cost
            total_tokens += tokens

        return {
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "breakdown": cost_breakdown,
            "timestamp": datetime.utcnow().isoformat()
        }

    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        # Convert to numpy arrays
        a = np.array(embedding1)
        b = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        return dot_product / (norm_a * norm_b)

    def find_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[Tuple[str, List[float]]],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find most similar embeddings to query."""

        similarities = []
        for chunk_id, embedding in candidate_embeddings:
            sim = self.similarity(query_embedding, embedding)
            similarities.append((chunk_id, sim))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

# Example usage and testing
async def test_voyage_client():
    """Test the Voyage client with sample data."""
    client = VoyageClient()

    # Test single embedding
    result = await client.embed_single(
        "This is a test conversation about product features and user requirements.",
        chunk_id="test_001"
    )

    console.print(f"✅ Single embedding: {len(result.embedding)} dimensions")

    # Test batch embedding
    requests = [
        EmbeddingRequest(
            text=f"Sample conversation segment {i}",
            model=None,  # Auto-select
            chunk_id=f"batch_{i:03d}",
            metadata={"segment": i}
        )
        for i in range(5)
    ]

    results = await client.embed_batch(requests)
    cost_info = client.calculate_cost(results)

    console.print(f"✅ Batch embedding: {len(results)} results")
    console.print(f"💰 Total cost: ${cost_info['total_cost_usd']}")

    return results

if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_voyage_client())