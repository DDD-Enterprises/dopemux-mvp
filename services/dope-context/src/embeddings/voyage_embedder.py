"""Voyage text embedding client with model-aware batching and accounting."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from voyageai import AsyncClient

from ..utils.model_tokenizer import (
    VoyageTokenCounter,
    allocate_total_tokens,
    partition_indices,
)
from ..index_profile import resolve_code_embed_model
from .model_registry import (
    DEFAULT_OUTPUT_DIMENSION,
    DEFAULT_OUTPUT_DTYPE,
    get_model_spec,
    validate_dimension,
)

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_CACHE_MAX = 4096


@dataclass(frozen=True)
class EmbeddingRequest:
    """Single embedding request with all vector-shaping parameters."""

    text: str
    model: str
    input_type: str
    truncation: bool = True
    output_dimension: int = DEFAULT_OUTPUT_DIMENSION
    output_dtype: str = DEFAULT_OUTPUT_DTYPE

    def cache_key(self) -> str:
        content = (
            f"{self.model}:{self.input_type}:{self.truncation}:"
            f"{self.output_dimension}:{self.output_dtype}:{self.text}"
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class EmbeddingResponse:
    """Embedding response with request-local token and cost metadata."""

    embedding: List[float]
    model: str
    tokens: int
    cached: bool = False
    cost_usd: float = 0.0
    output_dimension: int = DEFAULT_OUTPUT_DIMENSION
    output_dtype: str = DEFAULT_OUTPUT_DTYPE
    token_count_exact: bool = True


@dataclass
class CostTracker:
    """Track embedding API usage using current per-token pricing."""

    total_tokens: int = 0
    total_requests: int = 0
    total_cost_usd: float = 0.0
    cache_hits: int = 0

    def add_request(self, model: str, tokens: int, cached: bool = False) -> float:
        self.total_requests += 1
        if cached:
            self.cache_hits += 1
            return 0.0

        self.total_tokens += tokens
        price = get_model_spec(model, endpoint="embeddings").price_per_million_tokens
        cost = (tokens / 1_000_000) * price
        self.total_cost_usd += cost
        return cost

    def summary(self) -> Dict:
        cache_rate = self.cache_hits / max(self.total_requests, 1)
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "cache_hits": self.cache_hits,
            "cache_rate": round(cache_rate, 3),
        }


class VoyageEmbedder:
    """Async Voyage embedding client used by code and identifier vectors.

    The class preserves the original public API while adding:
    - Voyage 4 model support and fail-closed model validation
    - dimension/dtype-aware caching
    - model-specific token counting
    - token-aware request partitioning
    - exact batch cost allocation from API-reported totals
    """

    def __init__(
        self,
        api_key: str,
        cache_ttl_hours: int = 24,
        max_batch_size: int = 128,
        rate_limit_rpm: int = 2000,
        default_model: Optional[str] = None,
        output_dimension: int = DEFAULT_OUTPUT_DIMENSION,
        output_dtype: str = DEFAULT_OUTPUT_DTYPE,
        cache_max_entries: int = DEFAULT_EMBEDDING_CACHE_MAX,
    ):
        self.default_model = default_model or resolve_code_embed_model()
        get_model_spec(self.default_model, endpoint="embeddings")
        self.output_dimension = validate_dimension(self.default_model, output_dimension)
        self.output_dtype = output_dtype
        self.client = AsyncClient(api_key=api_key)
        self.token_counter = VoyageTokenCounter(api_key=api_key)
        self.cache: Dict[str, Tuple[EmbeddingResponse, datetime]] = {}
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.cache_max_entries = max(1, cache_max_entries)
        self.max_batch_size = max(1, max_batch_size)
        self.rate_limit_rpm = max(1, rate_limit_rpm)
        self.cost_tracker = CostTracker()
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()

    def _evict_expired_and_bound_cache(self) -> None:
        now = datetime.now()
        expired = [
            key
            for key, (_, cached_at) in self.cache.items()
            if now - cached_at > self.cache_ttl
        ]
        for key in expired:
            del self.cache[key]
        while len(self.cache) >= self.cache_max_entries:
            oldest = next(iter(self.cache))
            del self.cache[oldest]

    async def _check_rate_limit(self) -> None:
        async with self._rate_limit_lock:
            now = datetime.now()
            self._request_times = [
                value
                for value in self._request_times
                if now - value < timedelta(minutes=1)
            ]
            if len(self._request_times) >= self.rate_limit_rpm:
                oldest = self._request_times[0]
                wait_seconds = 60 - (now - oldest).total_seconds()
                if wait_seconds > 0:
                    logger.info("Voyage RPM limit reached; sleeping %.1fs", wait_seconds)
                    await asyncio.sleep(wait_seconds)
            self._request_times.append(datetime.now())

    def _get_cached(self, cache_key: str) -> Optional[EmbeddingResponse]:
        self._evict_expired_and_bound_cache()
        cached = self.cache.get(cache_key)
        if cached is None:
            return None
        response, cached_at = cached
        if datetime.now() - cached_at > self.cache_ttl:
            del self.cache[cache_key]
            return None
        return EmbeddingResponse(
            embedding=list(response.embedding),
            model=response.model,
            tokens=response.tokens,
            cached=True,
            cost_usd=0.0,
            output_dimension=response.output_dimension,
            output_dtype=response.output_dtype,
            token_count_exact=response.token_count_exact,
        )

    def _cache_response(self, cache_key: str, response: EmbeddingResponse) -> None:
        self._evict_expired_and_bound_cache()
        stored = EmbeddingResponse(
            embedding=list(response.embedding),
            model=response.model,
            tokens=response.tokens,
            cached=False,
            cost_usd=response.cost_usd,
            output_dimension=response.output_dimension,
            output_dtype=response.output_dtype,
            token_count_exact=response.token_count_exact,
        )
        self.cache[cache_key] = (stored, datetime.now())

    async def _api_embed(
        self,
        texts: List[str],
        *,
        model: str,
        input_type: str,
        truncation: bool,
        output_dimension: int,
        output_dtype: str,
    ):
        """Call the modern SDK, with a compatibility path for old test stubs."""

        kwargs = {
            "texts": texts,
            "model": model,
            "input_type": input_type,
            "truncation": truncation,
            "output_dimension": output_dimension,
            "output_dtype": output_dtype,
        }
        try:
            return await self.client.embed(**kwargs)
        except TypeError as exc:
            # Older voyageai releases and repository test doubles do not accept
            # Matryoshka/dtype keywords. Only default-shape requests are safe to
            # retry because silently dropping a non-default shape corrupts schema.
            if (
                output_dimension != DEFAULT_OUTPUT_DIMENSION
                or output_dtype != DEFAULT_OUTPUT_DTYPE
            ):
                raise RuntimeError(
                    "Installed voyageai client does not support output_dimension/"
                    "output_dtype; install voyageai>=0.5.0"
                ) from exc
            legacy_kwargs = {
                key: value
                for key, value in kwargs.items()
                if key not in {"output_dimension", "output_dtype"}
            }
            return await self.client.embed(**legacy_kwargs)

    def _request(
        self,
        text: str,
        *,
        model: str,
        input_type: str,
        truncation: bool,
        output_dimension: int,
        output_dtype: str,
    ) -> EmbeddingRequest:
        if input_type not in {"document", "query"}:
            raise ValueError("input_type must be 'document' or 'query'")
        get_model_spec(model, endpoint="embeddings")
        dimension = validate_dimension(model, output_dimension)
        return EmbeddingRequest(
            text=text,
            model=model,
            input_type=input_type,
            truncation=truncation,
            output_dimension=dimension,
            output_dtype=output_dtype,
        )

    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        input_type: str = "document",
        truncation: bool = True,
        output_dimension: Optional[int] = None,
        output_dtype: Optional[str] = None,
    ) -> EmbeddingResponse:
        model = model or self.default_model
        request = self._request(
            text,
            model=model,
            input_type=input_type,
            truncation=truncation,
            output_dimension=output_dimension or self.output_dimension,
            output_dtype=output_dtype or self.output_dtype,
        )
        cached = self._get_cached(request.cache_key())
        if cached:
            self.cost_tracker.add_request(model, cached.tokens, cached=True)
            return cached

        token_counts = await self.token_counter.count_each([text], model)
        spec = get_model_spec(model, endpoint="embeddings")
        if token_counts[0].count > spec.per_input_tokens and not truncation:
            raise ValueError(
                f"Input has {token_counts[0].count} tokens; model '{model}' "
                f"accepts {spec.per_input_tokens} per input"
            )

        await self._check_rate_limit()
        result = await self._api_embed(
            [text],
            model=model,
            input_type=input_type,
            truncation=truncation,
            output_dimension=request.output_dimension,
            output_dtype=request.output_dtype,
        )
        if not getattr(result, "embeddings", None):
            raise ValueError("Voyage API returned no embeddings")

        api_reported_total = hasattr(result, "total_tokens")
        tokens = int(getattr(result, "total_tokens", token_counts[0].count))
        response = EmbeddingResponse(
            embedding=list(result.embeddings[0]),
            model=model,
            tokens=tokens,
            cost_usd=self.cost_tracker.add_request(model, tokens),
            output_dimension=request.output_dimension,
            output_dtype=request.output_dtype,
            # Exact only when tokenizer counted precisely or the API supplied a
            # real total; never label a pure estimate as exact (F-004).
            token_count_exact=token_counts[0].exact or api_reported_total,
        )
        self._cache_response(request.cache_key(), response)
        return response

    async def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        input_type: str = "document",
        truncation: bool = True,
        output_dimension: Optional[int] = None,
        output_dtype: Optional[str] = None,
    ) -> List[EmbeddingResponse]:
        if not texts:
            return []

        model = model or self.default_model
        dimension = validate_dimension(model, output_dimension or self.output_dimension)
        dtype = output_dtype or self.output_dtype
        spec = get_model_spec(model, endpoint="embeddings")

        responses: List[Optional[EmbeddingResponse]] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_requests: List[EmbeddingRequest] = []

        for index, text in enumerate(texts):
            request = self._request(
                text,
                model=model,
                input_type=input_type,
                truncation=truncation,
                output_dimension=dimension,
                output_dtype=dtype,
            )
            cached = self._get_cached(request.cache_key())
            if cached is not None:
                self.cost_tracker.add_request(model, cached.tokens, cached=True)
                responses[index] = cached
            else:
                uncached_indices.append(index)
                uncached_requests.append(request)

        if not uncached_requests:
            return [response for response in responses if response is not None]

        token_counts = await self.token_counter.count_each(
            [request.text for request in uncached_requests], model
        )
        estimated = [item.count for item in token_counts]
        if not truncation:
            too_large = [
                index
                for index, count in enumerate(estimated)
                if count > spec.per_input_tokens
            ]
            if too_large:
                raise ValueError(
                    f"Inputs {too_large} exceed {spec.per_input_tokens} tokens "
                    f"for model '{model}'"
                )

        effective_counts = [
            min(count, spec.per_input_tokens) if truncation else count
            for count in estimated
        ]
        batches = partition_indices(
            effective_counts,
            max_inputs=min(self.max_batch_size, spec.max_request_inputs),
            max_tokens=spec.max_request_tokens,
        )

        for batch_indices in batches:
            batch_requests = [uncached_requests[index] for index in batch_indices]
            batch_texts = [request.text for request in batch_requests]
            await self._check_rate_limit()
            result = await self._api_embed(
                batch_texts,
                model=model,
                input_type=input_type,
                truncation=truncation,
                output_dimension=dimension,
                output_dtype=dtype,
            )
            embeddings = list(getattr(result, "embeddings", []))
            if len(embeddings) != len(batch_requests):
                raise ValueError(
                    f"Voyage returned {len(embeddings)} embeddings for "
                    f"{len(batch_requests)} inputs"
                )

            batch_estimates = [effective_counts[index] for index in batch_indices]
            api_reported_total = hasattr(result, "total_tokens")
            total_tokens = int(getattr(result, "total_tokens", sum(batch_estimates)))
            allocated = allocate_total_tokens(batch_estimates, total_tokens)

            for local_index, (request, embedding, tokens) in enumerate(
                zip(batch_requests, embeddings, allocated)
            ):
                global_uncached_index = batch_indices[local_index]
                original_index = uncached_indices[global_uncached_index]
                response = EmbeddingResponse(
                    embedding=list(embedding),
                    model=model,
                    tokens=tokens,
                    cost_usd=self.cost_tracker.add_request(model, tokens),
                    output_dimension=dimension,
                    output_dtype=dtype,
                    token_count_exact=(
                        token_counts[global_uncached_index].exact or api_reported_total
                    ),
                )
                self._cache_response(request.cache_key(), response)
                responses[original_index] = response

        if any(response is None for response in responses):
            raise RuntimeError("Internal embedding batch merge left missing responses")
        return [response for response in responses if response is not None]

    def clear_cache(self) -> None:
        self.cache.clear()
        logger.info("Voyage embedding cache cleared")

    def get_cost_summary(self) -> Dict:
        return self.cost_tracker.summary()
