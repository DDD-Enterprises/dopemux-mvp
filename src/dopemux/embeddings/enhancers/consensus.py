"""
Provider-assessment consensus validation for embedding search quality.

This module is intentionally non-live by default: provider calls only happen
when callers invoke `_get_provider_assessment`, and tests mock that boundary.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from ..core import AdvancedEmbeddingConfig, SearchResult
from .base import BaseEnhancer

try:  # pragma: no cover - optional dependency surface for patched tests.
    import openai  # type: ignore
    AsyncOpenAI = openai.AsyncOpenAI
except Exception:  # pragma: no cover
    openai = None  # type: ignore
    AsyncOpenAI = None  # type: ignore

try:  # pragma: no cover - optional dependency surface for patched tests.
    import cohere  # type: ignore
except Exception:  # pragma: no cover
    cohere = None  # type: ignore

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported assessment providers."""

    OPENAI = "openai"
    COHERE = "cohere"
    VOYAGE = "voyage"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class ConsensusConfig:
    """Configuration for provider-assessment consensus validation."""

    enabled: bool = True
    providers: List[ModelProvider] = field(
        default_factory=lambda: [ModelProvider.OPENAI, ModelProvider.COHERE]
    )
    min_providers: int = 2
    consensus_threshold: float = 0.7
    cost_limit_per_day: float = 10.0
    max_parallel_requests: int = 3
    enable_quality_scoring: bool = True
    enable_adaptive_sampling: bool = False
    cost_per_assessment_usd: float = 0.01


@dataclass
class ConsensusResult:
    """Result from a provider-assessment consensus pass."""

    consensus_reached: bool
    overall_quality_score: float
    provider_results: Dict[ModelProvider, Dict[str, Any]]
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def consensus_score(self) -> float:
        """Compatibility alias used by older embedding-similarity code."""
        return self.overall_quality_score

    @property
    def is_consensus(self) -> bool:
        """Compatibility alias used by older embedding-similarity code."""
        return self.consensus_reached

    @property
    def is_outlier(self) -> bool:
        """Compatibility alias used by older embedding-similarity code."""
        return not self.consensus_reached

    @property
    def cost_usd(self) -> float:
        """Compatibility alias for summary/stat reporting."""
        return float(self.metadata.get("cost_used", 0.0))

    @property
    def processing_time_ms(self) -> float:
        """Compatibility alias for summary/stat reporting."""
        return float(self.metadata.get("processing_time", 0.0)) * 1000


class ConsensusValidator(BaseEnhancer):
    """
    Validate content/search-result quality by comparing provider assessments.

    The constructor accepts either the current public shape
    `(embedding_config, consensus_config)` or the older single
    `ConsensusConfig` shape.
    """

    def __init__(
        self,
        embedding_config: Optional[AdvancedEmbeddingConfig | ConsensusConfig] = None,
        consensus_config: Optional[ConsensusConfig] = None,
    ):
        if isinstance(embedding_config, ConsensusConfig) and consensus_config is None:
            self.embedding_config: Optional[AdvancedEmbeddingConfig] = None
            self.consensus_config = embedding_config
        else:
            self.embedding_config = (
                embedding_config if isinstance(embedding_config, AdvancedEmbeddingConfig) else None
            )
            self.consensus_config = consensus_config or create_consensus_config()

        self.config = self.consensus_config
        self._daily_cost = 0.0
        self._last_reset_date = date.today()
        self._provider_clients: Dict[ModelProvider, Any] = {}
        self._total_validations = 0
        self._consensus_reached_count = 0
        self._recent_quality_scores: List[float] = []

    async def validate_quality(
        self,
        document_id: Optional[str] = None,
        content: str = "",
        embedding: Optional[List[float]] = None,
        **kwargs: Any,
    ) -> ConsensusResult:
        """Validate document quality through configured provider assessments."""
        del embedding
        doc_id = kwargs.get("doc_id") or document_id or "unknown"
        query = kwargs.get("query", "")

        await self._check_and_reset_daily_cost()

        if not self.consensus_config.enabled:
            return ConsensusResult(False, 0.0, {}, "Consensus validation disabled")

        if self._daily_cost >= self.consensus_config.cost_limit_per_day:
            return ConsensusResult(False, 0.0, {}, "Skipped: daily cost limit exceeded")

        if not await self._should_validate_adaptively(content):
            return ConsensusResult(True, 1.0, {}, "Skipped by adaptive sampling")

        semaphore = asyncio.Semaphore(self.consensus_config.max_parallel_requests)

        async def assess(provider: ModelProvider) -> tuple[ModelProvider, Dict[str, Any]]:
            async with semaphore:
                return provider, await self._get_provider_assessment(provider, content, query)

        provider_results: Dict[ModelProvider, Dict[str, Any]] = {}
        for provider, result in await asyncio.gather(
            *(assess(provider) for provider in self.consensus_config.providers)
        ):
            provider_results[provider] = result

        quality_score = await self._calculate_consensus_score(provider_results)
        consensus_reached = (
            len(provider_results) >= self.consensus_config.min_providers
            and quality_score >= self.consensus_config.consensus_threshold
            and await self._check_consensus_threshold(provider_results)
        )

        reasoning = self._combine_reasoning(provider_results, consensus_reached, doc_id)
        cost_used = len(provider_results) * self.consensus_config.cost_per_assessment_usd
        await self._update_daily_cost(cost_used)

        self._total_validations += 1
        if consensus_reached:
            self._consensus_reached_count += 1
        self._recent_quality_scores.append(quality_score)
        self._recent_quality_scores = self._recent_quality_scores[-20:]

        return ConsensusResult(
            consensus_reached=consensus_reached,
            overall_quality_score=quality_score,
            provider_results=provider_results,
            reasoning=reasoning,
            metadata={"cost_used": cost_used, "document_id": doc_id},
        )

    async def validate_embedding(
        self,
        document_id: str,
        text: str,
        primary_embedding: List[float],
    ) -> ConsensusResult:
        """Compatibility entry point for older embedding pipeline code."""
        return await self.validate_quality(document_id, text, primary_embedding)

    async def enhance_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """Add consensus validation metadata to search results."""
        enhanced: List[SearchResult] = []
        for result in results:
            validation = await self.validate_quality(
                document_id=result.doc_id,
                content=result.content,
                embedding=[],
                query=query,
            )
            result.metadata["consensus_validation"] = {
                "consensus_reached": validation.consensus_reached,
                "quality_score": validation.overall_quality_score,
                "reasoning": validation.reasoning,
            }
            enhanced.append(result)
        return enhanced

    async def batch_validate_quality(self, documents: List[Dict[str, Any]]) -> List[ConsensusResult]:
        """Validate a batch of documents."""
        return [
            await self.validate_quality(
                document_id=document.get("id"),
                content=document.get("content", ""),
                embedding=document.get("embedding", []),
            )
            for document in documents
        ]

    async def validate_connection(self) -> bool:
        """Return true when enough configured providers pass connection checks."""
        checks = [
            await self._test_provider_connection(provider)
            for provider in self.consensus_config.providers
        ]
        return sum(1 for ok in checks if ok) >= self.consensus_config.min_providers

    async def _test_provider_connection(self, provider: ModelProvider) -> bool:
        """Provider preflight hook. Real callers may override/mock this."""
        del provider
        return False

    async def _get_provider_assessment(
        self,
        provider: ModelProvider,
        content: str,
        query: str,
    ) -> Dict[str, Any]:
        """Fetch a quality assessment from one provider."""
        try:
            if provider == ModelProvider.OPENAI:
                if openai is None or not hasattr(openai, "AsyncOpenAI"):
                    raise RuntimeError("openai client is not installed")
                client = openai.AsyncOpenAI()
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Return JSON with quality_score, confidence, and reasoning."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Query: {query}\n\nContent:\n{content}",
                        },
                    ],
                    temperature=0,
                )
                raw = response.choices[0].message.content
                return self._normalize_assessment(json.loads(raw))

            return {
                "quality_score": 0.5,
                "confidence": 0.0,
                "reasoning": f"{provider.value} assessment client not configured",
            }
        except Exception as exc:
            return {
                "quality_score": 0.5,
                "confidence": 0.0,
                "reasoning": f"Provider assessment error: {exc}",
            }

    def _normalize_assessment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize provider JSON into the stable assessment shape."""
        return {
            "quality_score": float(payload.get("quality_score", 0.5)),
            "confidence": float(payload.get("confidence", 0.0)),
            "reasoning": str(payload.get("reasoning", "")),
        }

    async def _calculate_consensus_score(
        self,
        provider_results: Dict[ModelProvider, Dict[str, Any]],
    ) -> float:
        """Calculate confidence-weighted quality score."""
        if not provider_results:
            return 0.0

        weighted_sum = 0.0
        confidence_sum = 0.0
        for result in provider_results.values():
            confidence = float(result.get("confidence", 0.0))
            score = float(result.get("quality_score", 0.0))
            weighted_sum += score * confidence
            confidence_sum += confidence

        if confidence_sum <= 0:
            return sum(float(r.get("quality_score", 0.0)) for r in provider_results.values()) / len(provider_results)
        return weighted_sum / confidence_sum

    async def _check_consensus_threshold(
        self,
        provider_results: Dict[ModelProvider, Dict[str, Any]],
    ) -> bool:
        """Check whether provider scores are close enough to count as consensus."""
        if len(provider_results) < 2:
            return len(provider_results) >= self.consensus_config.min_providers

        scores = [float(result.get("quality_score", 0.0)) for result in provider_results.values()]
        max_allowed_spread = 1.0 - self.consensus_config.consensus_threshold
        return (max(scores) - min(scores)) <= max_allowed_spread

    async def _update_daily_cost(self, amount: float) -> None:
        """Add to tracked daily consensus cost."""
        self._daily_cost += amount

    async def _check_and_reset_daily_cost(self) -> None:
        """Reset tracked daily cost when the local date changes."""
        today = date.today()
        if self._last_reset_date != today:
            self._daily_cost = 0.0
            self._last_reset_date = today

    async def _should_validate_adaptively(self, content: str) -> bool:
        """Return whether adaptive sampling should run validation."""
        del content
        if not self.consensus_config.enable_adaptive_sampling:
            return True
        if len(self._recent_quality_scores) < 5:
            return True
        avg_recent = sum(self._recent_quality_scores[-5:]) / 5
        return avg_recent < 0.85

    def get_enhancement_stats(self) -> Dict[str, Any]:
        """Get summary of consensus validation activity."""
        consensus_rate = (
            self._consensus_reached_count / self._total_validations
            if self._total_validations
            else 0
        )
        return {
            "total_validations": self._total_validations,
            "consensus_rate": consensus_rate,
            "daily_cost_used": self._daily_cost,
            "cost_limit": self.consensus_config.cost_limit_per_day,
        }

    def _combine_reasoning(
        self,
        provider_results: Dict[ModelProvider, Dict[str, Any]],
        consensus_reached: bool,
        doc_id: str,
    ) -> str:
        """Build short operator-readable reasoning."""
        prefix = "Consensus reached" if consensus_reached else "Consensus not reached"
        reasons = [
            str(result.get("reasoning", ""))
            for result in provider_results.values()
            if result.get("reasoning")
        ]
        detail = "; ".join(reasons[:3])
        return f"{prefix} for {doc_id}" + (f": {detail}" if detail else "")


def create_consensus_config(
    quality_level: str = "standard",
    cost_limit: float = 10.0,
    enable_adaptive_sampling: bool = False,
    enabled: bool = True,
) -> ConsensusConfig:
    """Create a consensus validation configuration."""
    if quality_level == "high":
        providers = [
            ModelProvider.OPENAI,
            ModelProvider.COHERE,
            ModelProvider.VOYAGE,
        ]
        threshold = 0.85
        min_providers = 3
    else:
        providers = [ModelProvider.OPENAI, ModelProvider.COHERE]
        threshold = 0.7
        min_providers = 2

    return ConsensusConfig(
        enabled=enabled,
        providers=providers,
        min_providers=min_providers,
        consensus_threshold=threshold,
        cost_limit_per_day=cost_limit,
        enable_adaptive_sampling=enable_adaptive_sampling,
    )
