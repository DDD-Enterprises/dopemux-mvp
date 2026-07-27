"""Model-aware token accounting for Voyage embedding and rerank requests."""

from __future__ import annotations

import asyncio
import hashlib
import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import voyageai

_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def conservative_token_estimate(text: str) -> int:
    """Estimate tokens without pretending a foreign tokenizer is exact.

    The fallback intentionally overestimates typical English/code input. It is
    used only when Voyage's model-specific tokenizer is unavailable.
    """

    if not text:
        return 0
    byte_estimate = math.ceil(len(text.encode("utf-8")) / 3)
    lexical_estimate = len(_TOKEN_RE.findall(text))
    return max(1, byte_estimate, lexical_estimate)


@dataclass(frozen=True)
class TokenCount:
    count: int
    exact: bool


class VoyageTokenCounter:
    """Use Voyage's model-specific tokenizer with a deterministic fallback.

    Tokenizer/model load is attempted at most once per model per process. A
    blocked Hugging Face / network route is memoized so unique texts do not
    each trigger another failed download (F-006).
    """

    def __init__(self, api_key: Optional[str] = None):
        client_type = getattr(voyageai, "Client", None)
        self._client = client_type(api_key=api_key) if client_type else None
        self._cache: Dict[Tuple[str, str], TokenCount] = {}
        # Per-model load outcome: True = exact tokenizer available, False = failed.
        self._model_tokenizer_ok: Dict[str, bool] = {}
        self._model_load_attempts: Dict[str, int] = {}

    @staticmethod
    def _key(text: str, model: str) -> Tuple[str, str]:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return model, digest

    def _count_uncached(self, texts: Sequence[str], model: str) -> List[TokenCount]:
        if not texts:
            return []

        # Memoized failure: never re-attempt network download per unique text.
        if self._model_tokenizer_ok.get(model) is False:
            return [
                TokenCount(conservative_token_estimate(text), False) for text in texts
            ]

        if self._client is not None and self._model_tokenizer_ok.get(model) is not False:
            try:
                self._model_load_attempts[model] = (
                    self._model_load_attempts.get(model, 0) + 1
                )
                encodings = self._client.tokenize(list(texts), model=model)
                counts: List[TokenCount] = []
                for encoding in encodings:
                    ids = getattr(encoding, "ids", None)
                    tokens = getattr(encoding, "tokens", None)
                    if ids is not None:
                        counts.append(TokenCount(len(ids), True))
                    elif tokens is not None:
                        counts.append(TokenCount(len(tokens), True))
                    else:
                        raise TypeError("Voyage tokenizer returned an unknown encoding")
                if len(counts) == len(texts):
                    self._model_tokenizer_ok[model] = True
                    return counts
            except Exception:
                # Networkless/constrained environments may not have tokenizer
                # files. Memoize failure so subsequent texts do not re-hit the net.
                self._model_tokenizer_ok[model] = False

        return [TokenCount(conservative_token_estimate(text), False) for text in texts]

    def tokenizer_load_attempts(self, model: str) -> int:
        return self._model_load_attempts.get(model, 0)

    def tokenizer_available(self, model: str) -> Optional[bool]:
        return self._model_tokenizer_ok.get(model)

    async def count_each(self, texts: Sequence[str], model: str) -> List[TokenCount]:
        """Count each text without blocking the event loop on tokenizer loading."""

        missing_texts: List[str] = []
        missing_keys: List[Tuple[str, str]] = []
        results: List[Optional[TokenCount]] = []

        for text in texts:
            key = self._key(text, model)
            cached = self._cache.get(key)
            results.append(cached)
            if cached is None:
                missing_texts.append(text)
                missing_keys.append(key)

        if missing_texts:
            new_counts = await asyncio.to_thread(
                self._count_uncached, missing_texts, model
            )
            for key, count in zip(missing_keys, new_counts):
                self._cache[key] = count

            new_iter = iter(new_counts)
            results = [next(new_iter) if value is None else value for value in results]

        return [value for value in results if value is not None]

    async def count_total(self, texts: Sequence[str], model: str) -> TokenCount:
        counts = await self.count_each(texts, model)
        return TokenCount(
            count=sum(item.count for item in counts),
            exact=all(item.exact for item in counts),
        )


def partition_indices(
    counts: Sequence[int],
    *,
    max_inputs: int,
    max_tokens: int,
) -> List[List[int]]:
    """Partition ordered inputs while respecting count and token ceilings."""

    if max_inputs < 1 or max_tokens < 1:
        raise ValueError("max_inputs and max_tokens must be positive")

    batches: List[List[int]] = []
    current: List[int] = []
    current_tokens = 0

    for index, count in enumerate(counts):
        if count < 0:
            raise ValueError("token counts cannot be negative")
        if count > max_tokens:
            raise ValueError(
                f"Input {index} has {count} tokens, exceeding request limit {max_tokens}"
            )
        if current and (
            len(current) >= max_inputs or current_tokens + count > max_tokens
        ):
            batches.append(current)
            current = []
            current_tokens = 0

        current.append(index)
        current_tokens += count

    if current:
        batches.append(current)
    return batches


def allocate_total_tokens(estimated: Sequence[int], actual_total: int) -> List[int]:
    """Allocate an API-reported total while preserving the exact sum."""

    if not estimated:
        return []
    if actual_total < 0:
        raise ValueError("actual_total cannot be negative")

    estimate_total = sum(estimated)
    if estimate_total <= 0:
        base, remainder = divmod(actual_total, len(estimated))
        return [base + (1 if index < remainder else 0) for index in range(len(estimated))]

    raw = [actual_total * value / estimate_total for value in estimated]
    allocated = [math.floor(value) for value in raw]
    remainder = actual_total - sum(allocated)
    order = sorted(
        range(len(raw)),
        key=lambda index: (raw[index] - allocated[index], -index),
        reverse=True,
    )
    for index in order[:remainder]:
        allocated[index] += 1
    return allocated
