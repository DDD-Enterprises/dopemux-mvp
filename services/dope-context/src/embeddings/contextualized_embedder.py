"""Voyage contextualized embedding client for document-aware retrieval."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from voyageai import AsyncClient

from ..utils.model_tokenizer import (
    VoyageTokenCounter,
    allocate_total_tokens,
    partition_indices,
)
from .model_registry import (
    DEFAULT_DOC_MODEL,
    DEFAULT_OUTPUT_DIMENSION,
    DEFAULT_OUTPUT_DTYPE,
    env_model,
    get_model_spec,
    resolve_context_model,
    validate_dimension,
)

logger = logging.getLogger(__name__)

# F-012: bound the contextualized-embedding cache so a long-running
# server process cannot grow it without limit. See voyage_embedder.py for
# the matching code-vector cache.
DEFAULT_MAX_CACHE_ENTRIES = 10_000


@dataclass
class ContextualizedEmbeddingResponse:
    """Contextualized vectors and model-specific accounting for one document."""

    embeddings: List[List[float]]
    model: str
    total_tokens: int
    cached: bool = False
    cost_usd: float = 0.0
    chunk_tokens: List[int] = field(default_factory=list)
    chunk_texts: List[str] = field(default_factory=list)
    output_dimension: int = DEFAULT_OUTPUT_DIMENSION
    output_dtype: str = DEFAULT_OUTPUT_DTYPE
    token_count_exact: bool = True


@dataclass
class CostTracker:
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
        price = get_model_spec(
            model, endpoint="contextualized_embeddings"
        ).price_per_million_tokens
        cost = (tokens / 1_000_000) * price
        self.total_cost_usd += cost
        return cost

    def summary(self) -> Dict:
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "cache_hits": self.cache_hits,
            "cache_rate": round(self.cache_hits / max(self.total_requests, 1), 3),
        }


class ContextualizedEmbedder:
    """Contextualized Voyage client with a context-4 default.

    Existing context-3 call sites are migrated onto the configured model unless
    ``DOPE_CONTEXT_ALLOW_LEGACY_CONTEXT3`` is explicitly enabled. This keeps
    rollback possible while preventing stale literals from pinning production
    to the legacy model forever.
    """

    def __init__(
        self,
        api_key: str,
        cache_ttl_hours: int = 24,
        rate_limit_rpm: int = 2000,
        default_model: Optional[str] = None,
        output_dimension: int = DEFAULT_OUTPUT_DIMENSION,
        output_dtype: str = DEFAULT_OUTPUT_DTYPE,
        max_cache_entries: int = DEFAULT_MAX_CACHE_ENTRIES,
    ):
        self.default_model = default_model or env_model(
            "DOPE_CONTEXT_DOC_EMBED_MODEL", DEFAULT_DOC_MODEL
        )
        get_model_spec(self.default_model, endpoint="contextualized_embeddings")
        self.output_dimension = validate_dimension(self.default_model, output_dimension)
        self.output_dtype = output_dtype
        self.client = AsyncClient(api_key=api_key)
        self.token_counter = VoyageTokenCounter(api_key=api_key)
        self.cache: Dict[str, Tuple[ContextualizedEmbeddingResponse, datetime]] = {}
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.max_cache_entries = max(1, max_cache_entries)
        self.rate_limit_rpm = max(1, rate_limit_rpm)
        self.cost_tracker = CostTracker()
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()

    def _resolve_model(self, requested: Optional[str]) -> str:
        model = resolve_context_model(requested, self.default_model)
        get_model_spec(model, endpoint="contextualized_embeddings")
        if requested == "voyage-context-3" and model != requested:
            logger.warning(
                "Migrating legacy voyage-context-3 request to configured model %s",
                model,
            )
        return model

    @staticmethod
    def _cache_key(
        document_chunks: Sequence[str],
        *,
        model: str,
        input_type: str,
        output_dimension: int,
        output_dtype: str,
        enable_auto_chunking: bool,
        chunk_size: int,
        chunk_overlap: int,
    ) -> str:
        payload = "\x1e".join(document_chunks)
        content = (
            f"{model}:{input_type}:{output_dimension}:{output_dtype}:"
            f"{enable_auto_chunking}:{chunk_size}:{chunk_overlap}:{payload}"
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

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

    def _get_cached(
        self, cache_key: str
    ) -> Optional[ContextualizedEmbeddingResponse]:
        cached = self.cache.get(cache_key)
        if cached is None:
            return None
        response, cached_at = cached
        if datetime.now() - cached_at > self.cache_ttl:
            del self.cache[cache_key]
            return None
        return ContextualizedEmbeddingResponse(
            # Copy, not alias (F-012): callers may mutate these lists in
            # place. Handing out the cached lists by reference would let
            # that mutation corrupt every future cache hit.
            embeddings=[list(vector) for vector in response.embeddings],
            model=response.model,
            total_tokens=response.total_tokens,
            cached=True,
            cost_usd=0.0,
            chunk_tokens=list(response.chunk_tokens),
            chunk_texts=list(response.chunk_texts),
            output_dimension=response.output_dimension,
            output_dtype=response.output_dtype,
            token_count_exact=response.token_count_exact,
        )

    def _evict_expired(self) -> None:
        now = datetime.now()
        expired = [
            key
            for key, (_, cached_at) in self.cache.items()
            if now - cached_at > self.cache_ttl
        ]
        for key in expired:
            del self.cache[key]

    def _cache_response(
        self, cache_key: str, response: ContextualizedEmbeddingResponse
    ) -> None:
        # Bound the cache (F-012): see voyage_embedder.py._cache_response for
        # the matching rationale -- expire first, then evict oldest-first so
        # a long-running server cannot grow this dict without limit.
        if (
            cache_key not in self.cache
            and len(self.cache) >= self.max_cache_entries
        ):
            self._evict_expired()
            while len(self.cache) >= self.max_cache_entries:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
        self.cache[cache_key] = (response, datetime.now())

    async def _api_contextualized_embed(
        self,
        inputs,
        *,
        model: str,
        input_type: str,
        output_dimension: int,
        output_dtype: str,
        enable_auto_chunking: bool = False,
        chunk_size: int = 512,
        chunk_overlap: int = 0,
    ):
        kwargs = {
            "inputs": inputs,
            "model": model,
            "input_type": input_type,
            "output_dimension": output_dimension,
            "output_dtype": output_dtype,
            "enable_auto_chunking": enable_auto_chunking,
        }
        if enable_auto_chunking:
            kwargs["chunk_size"] = chunk_size
            kwargs["chunk_overlap"] = chunk_overlap
        try:
            return await self.client.contextualized_embed(**kwargs)
        except TypeError as exc:
            if (
                model != "voyage-context-3"
                or output_dimension != DEFAULT_OUTPUT_DIMENSION
                or output_dtype != DEFAULT_OUTPUT_DTYPE
                or enable_auto_chunking
            ):
                raise RuntimeError(
                    "Installed voyageai client lacks voyage-context-4 options; "
                    "install voyageai>=0.5.0"
                ) from exc
            legacy = {
                key: value
                for key, value in kwargs.items()
                if key
                not in {
                    "output_dtype",
                    "enable_auto_chunking",
                    "chunk_size",
                    "chunk_overlap",
                }
            }
            return await self.client.contextualized_embed(**legacy)

    @staticmethod
    def _result_objects(result) -> List:
        objects = getattr(result, "results", None)
        if objects is None:
            objects = getattr(result, "data", None)
        if objects is None:
            raise ValueError("Voyage contextualized API returned no results")
        return list(objects)

    @staticmethod
    def _extract_embeddings(result_object) -> List[List[float]]:
        embeddings = getattr(result_object, "embeddings", None)
        if embeddings is not None:
            return list(embeddings)

        data = getattr(result_object, "data", None)
        if data is not None:
            return [list(item.embedding) for item in data]

        raise ValueError("Voyage contextualized result has no embeddings")

    @staticmethod
    def _extract_chunk_texts(result_object, fallback: Sequence[str]) -> List[str]:
        chunk_texts = getattr(result_object, "chunk_texts", None)
        if chunk_texts is not None:
            return list(chunk_texts)

        data = getattr(result_object, "data", None)
        if data is not None:
            texts = [getattr(item, "text", None) for item in data]
            if all(text is not None for text in texts):
                return [str(text) for text in texts]

        return list(fallback)

    async def embed_document(
        self,
        chunks: List[str],
        model: Optional[str] = None,
        input_type: str = "document",
        output_dimension: Optional[int] = None,
        output_dtype: Optional[str] = None,
        enable_auto_chunking: bool = False,
        chunk_size: int = 512,
        chunk_overlap: int = 0,
    ) -> ContextualizedEmbeddingResponse:
        if not chunks:
            raise ValueError("chunks cannot be empty")
        if input_type not in {"document", "query"}:
            raise ValueError("input_type must be 'document' or 'query'")
        if enable_auto_chunking and len(chunks) != 1:
            raise ValueError(
                "auto-chunking accepts one full document per embed_document call"
            )
        if enable_auto_chunking and chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        model = self._resolve_model(model)
        dimension = validate_dimension(model, output_dimension or self.output_dimension)
        dtype = output_dtype or self.output_dtype
        cache_key = self._cache_key(
            chunks,
            model=model,
            input_type=input_type,
            output_dimension=dimension,
            output_dtype=dtype,
            enable_auto_chunking=enable_auto_chunking,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            self.cost_tracker.add_request(model, cached.total_tokens, cached=True)
            return cached

        counts = await self.token_counter.count_each(chunks, model)
        spec = get_model_spec(model, endpoint="contextualized_embeddings")
        if len(chunks) > 16_000:
            raise ValueError("Contextualized requests cannot exceed 16,000 chunks")
        if sum(item.count for item in counts) > spec.max_request_tokens:
            raise ValueError(
                f"Document has {sum(item.count for item in counts)} tokens; "
                f"request limit is {spec.max_request_tokens}"
            )
        too_large = [
            index
            for index, item in enumerate(counts)
            if item.count > spec.per_input_tokens
        ]
        if too_large and not enable_auto_chunking:
            raise ValueError(
                f"Chunks {too_large} exceed {spec.per_input_tokens} tokens each"
            )

        await self._check_rate_limit()
        api_inputs = chunks if enable_auto_chunking else [chunks]
        result = await self._api_contextualized_embed(
            api_inputs,
            model=model,
            input_type=input_type,
            output_dimension=dimension,
            output_dtype=dtype,
            enable_auto_chunking=enable_auto_chunking,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        result_objects = self._result_objects(result)
        if len(result_objects) != 1:
            raise ValueError(
                f"Expected one contextualized result, got {len(result_objects)}"
            )

        result_object = result_objects[0]
        embeddings = self._extract_embeddings(result_object)
        returned_texts = self._extract_chunk_texts(result_object, chunks)
        if len(embeddings) != len(returned_texts):
            raise ValueError(
                f"Voyage returned {len(embeddings)} vectors for "
                f"{len(returned_texts)} chunks"
            )

        returned_counts = await self.token_counter.count_each(returned_texts, model)
        total_tokens = int(
            getattr(result, "total_tokens", sum(item.count for item in returned_counts))
        )
        chunk_tokens = allocate_total_tokens(
            [item.count for item in returned_counts], total_tokens
        )
        response = ContextualizedEmbeddingResponse(
            embeddings=embeddings,
            model=model,
            total_tokens=total_tokens,
            cost_usd=self.cost_tracker.add_request(model, total_tokens),
            chunk_tokens=chunk_tokens,
            chunk_texts=returned_texts,
            output_dimension=dimension,
            output_dtype=dtype,
            token_count_exact=all(item.exact for item in returned_counts),
        )
        self._cache_response(cache_key, response)
        return response

    async def embed_documents_batch(
        self,
        documents: List[List[str]],
        model: Optional[str] = None,
        input_type: str = "document",
        output_dimension: Optional[int] = None,
        output_dtype: Optional[str] = None,
    ) -> List[ContextualizedEmbeddingResponse]:
        if not documents:
            return []
        if any(not document for document in documents):
            raise ValueError("documents cannot contain empty chunk lists")

        model = self._resolve_model(model)
        dimension = validate_dimension(model, output_dimension or self.output_dimension)
        dtype = output_dtype or self.output_dtype
        spec = get_model_spec(model, endpoint="contextualized_embeddings")

        responses: List[Optional[ContextualizedEmbeddingResponse]] = [None] * len(
            documents
        )
        uncached_indices: List[int] = []
        uncached_documents: List[List[str]] = []
        uncached_keys: List[str] = []

        for index, chunks in enumerate(documents):
            key = self._cache_key(
                chunks,
                model=model,
                input_type=input_type,
                output_dimension=dimension,
                output_dtype=dtype,
                enable_auto_chunking=False,
                chunk_size=512,
                chunk_overlap=0,
            )
            cached = self._get_cached(key)
            if cached is not None:
                self.cost_tracker.add_request(model, cached.total_tokens, cached=True)
                responses[index] = cached
            else:
                uncached_indices.append(index)
                uncached_documents.append(chunks)
                uncached_keys.append(key)

        if not uncached_documents:
            return [response for response in responses if response is not None]

        doc_counts = []
        for document in uncached_documents:
            counts = await self.token_counter.count_each(document, model)
            values = [item.count for item in counts]
            if any(value > spec.per_input_tokens for value in values):
                raise ValueError(
                    f"A document chunk exceeds {spec.per_input_tokens} tokens"
                )
            doc_counts.append(sum(values))

        batch_indices = partition_indices(
            doc_counts,
            max_inputs=spec.max_request_inputs,
            max_tokens=spec.max_request_tokens,
        )

        for group in batch_indices:
            group_documents = [uncached_documents[index] for index in group]
            if sum(len(document) for document in group_documents) > 16_000:
                raise ValueError(
                    "Contextualized request cannot exceed 16,000 total chunks"
                )

            await self._check_rate_limit()
            result = await self._api_contextualized_embed(
                group_documents,
                model=model,
                input_type=input_type,
                output_dimension=dimension,
                output_dtype=dtype,
            )
            objects = self._result_objects(result)
            if len(objects) != len(group_documents):
                raise ValueError(
                    f"Voyage returned {len(objects)} document results for "
                    f"{len(group_documents)} documents"
                )

            group_estimates = [doc_counts[index] for index in group]
            group_total = int(getattr(result, "total_tokens", sum(group_estimates)))
            allocated_docs = allocate_total_tokens(group_estimates, group_total)

            for local_index, (document, result_object, doc_tokens) in enumerate(
                zip(group_documents, objects, allocated_docs)
            ):
                uncached_index = group[local_index]
                embeddings = self._extract_embeddings(result_object)
                returned_texts = self._extract_chunk_texts(result_object, document)
                if len(embeddings) != len(returned_texts):
                    raise ValueError(
                        "Contextualized embedding count does not match chunk count"
                    )
                returned_counts = await self.token_counter.count_each(
                    returned_texts, model
                )
                chunk_tokens = allocate_total_tokens(
                    [item.count for item in returned_counts], doc_tokens
                )
                response = ContextualizedEmbeddingResponse(
                    embeddings=embeddings,
                    model=model,
                    total_tokens=doc_tokens,
                    cost_usd=self.cost_tracker.add_request(model, doc_tokens),
                    chunk_tokens=chunk_tokens,
                    chunk_texts=returned_texts,
                    output_dimension=dimension,
                    output_dtype=dtype,
                    token_count_exact=all(item.exact for item in returned_counts),
                )
                self._cache_response(uncached_keys[uncached_index], response)
                responses[uncached_indices[uncached_index]] = response

        if any(response is None for response in responses):
            raise RuntimeError("Internal contextualized batch merge is incomplete")
        return [response for response in responses if response is not None]

    async def embed_documents_grouped(
        self,
        documents: List[List[str]],
        model: Optional[str] = None,
        input_type: str = "document",
        output_dimension: Optional[int] = None,
        output_dtype: Optional[str] = None,
    ) -> List[ContextualizedEmbeddingResponse]:
        return await self.embed_documents_batch(
            documents=documents,
            model=model,
            input_type=input_type,
            output_dimension=output_dimension,
            output_dtype=output_dtype,
        )

    def clear_cache(self) -> None:
        self.cache.clear()
        logger.info("Contextualized embedding cache cleared")

    def get_cost_summary(self) -> Dict:
        return self.cost_tracker.summary()
