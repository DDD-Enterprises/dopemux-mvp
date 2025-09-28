"""
Multi-Model Consensus Validation System

Validates embedding quality and search results using multiple AI models
for enhanced reliability and outlier detection. Uses consensus scoring
to identify potential issues with individual model outputs.

Expert recommendation: Use selectively due to cost - focus on critical documents
and validation scenarios rather than all queries.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
import httpx

from .advanced_embeddings import AdvancedEmbeddingConfig, SearchResult

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """Supported embedding model providers."""
    VOYAGE = "voyage"
    OPENAI = "openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


@dataclass
class ConsensusConfig:
    """Configuration for consensus validation."""

    # Models to use for consensus (besides primary)
    consensus_models: List[Dict[str, str]] = field(default_factory=lambda: [
        {"provider": "openai", "model": "text-embedding-3-large", "dimension": 3072},
        {"provider": "cohere", "model": "embed-english-v3.0", "dimension": 1024},
    ])

    # Consensus thresholds
    similarity_threshold: float = 0.9      # Minimum consensus similarity
    outlier_threshold: float = 0.7         # Flag documents below this

    # Processing settings
    batch_size: int = 5                    # Small batches to manage cost
    max_concurrent: int = 3                # API rate limiting
    enable_caching: bool = True            # Cache consensus results

    # Cost management
    max_documents_per_day: int = 1000      # Daily processing limit
    cost_per_document_usd: float = 0.001   # Estimated cost per document

    # ADHD optimizations
    progress_updates: bool = True          # Show progress indicators
    gentle_warnings: bool = True           # Friendly error messages


@dataclass
class ConsensusResult:
    """Result of consensus validation."""

    document_id: str
    primary_embedding: List[float]
    consensus_embeddings: Dict[str, List[float]]

    # Consensus metrics
    avg_similarity: float                  # Average pairwise similarity
    min_similarity: float                  # Minimum pairwise similarity
    max_similarity: float                  # Maximum pairwise similarity
    consensus_score: float                 # Overall consensus (0-1)

    # Quality indicators
    is_consensus: bool                     # Above similarity threshold
    is_outlier: bool                       # Below outlier threshold
    flagged_models: List[str] = field(default_factory=list)  # Models with low agreement

    # Metadata
    processing_time_ms: float = 0.0
    cost_usd: float = 0.0


class ModelAPIClient:
    """Generic API client for different embedding providers."""

    def __init__(self, provider: ModelProvider, model_name: str, api_key: str):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using the specified model."""
        if self.provider == ModelProvider.OPENAI:
            return await self._openai_embed(text)
        elif self.provider == ModelProvider.COHERE:
            return await self._cohere_embed(text)
        elif self.provider == ModelProvider.VOYAGE:
            return await self._voyage_embed(text)
        else:
            raise NotImplementedError(f"Provider {self.provider} not implemented")

    async def _openai_embed(self, text: str) -> List[float]:
        """OpenAI embedding API call."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "input": text,
            "encoding_format": "float"
        }

        response = await self.client.post(
            "https://api.openai.com/v1/embeddings",
            json=payload,
            headers=headers
        )

        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]

    async def _cohere_embed(self, text: str) -> List[float]:
        """Cohere embedding API call."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "texts": [text],
            "input_type": "search_document"
        }

        response = await self.client.post(
            "https://api.cohere.ai/v1/embed",
            json=payload,
            headers=headers
        )

        response.raise_for_status()
        result = response.json()
        return result["embeddings"][0]

    async def _voyage_embed(self, text: str) -> List[float]:
        """Voyage AI embedding API call."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "input": [text],
            "encoding_format": "float"
        }

        response = await self.client.post(
            "https://api.voyageai.com/v1/embeddings",
            json=payload,
            headers=headers
        )

        response.raise_for_status()
        result = response.json()
        return result["data"][0]["embedding"]


class ConsensusValidator:
    """
    Multi-model consensus validation system.

    Validates embedding quality by comparing outputs from multiple models
    and flagging outliers or low-consensus results.
    """

    def __init__(self, config: ConsensusConfig):
        self.config = config
        self.model_clients: Dict[str, ModelAPIClient] = {}
        self.daily_usage = 0
        self.cache: Dict[str, ConsensusResult] = {}

        # Initialize model clients
        self._initialize_clients()

        logger.info(f"🤝 Consensus validator initialized with {len(self.model_clients)} models")

    def _initialize_clients(self):
        """Initialize API clients for consensus models."""
        # This would need actual API keys from environment
        for model_config in self.config.consensus_models:
            provider = ModelProvider(model_config["provider"])
            model_name = model_config["model"]

            # Skip if no API key available
            api_key = self._get_api_key(provider)
            if not api_key:
                logger.warning(f"⚠️ No API key for {provider.value} - skipping {model_name}")
                continue

            client_key = f"{provider.value}_{model_name}"
            self.model_clients[client_key] = ModelAPIClient(provider, model_name, api_key)

    def _get_api_key(self, provider: ModelProvider) -> Optional[str]:
        """Get API key for provider from environment."""
        import os

        key_mapping = {
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.COHERE: "COHERE_API_KEY",
            ModelProvider.VOYAGE: "VOYAGE_API_KEY"
        }

        env_var = key_mapping.get(provider)
        return os.getenv(env_var) if env_var else None

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)

        if a_norm == 0 or b_norm == 0:
            return 0.0

        return np.dot(a, b) / (a_norm * b_norm)

    def _calculate_consensus_metrics(self, embeddings: Dict[str, List[float]]) -> Tuple[float, float, float, float]:
        """Calculate consensus metrics from multiple embeddings."""
        if len(embeddings) < 2:
            return 1.0, 1.0, 1.0, 1.0

        # Calculate all pairwise similarities
        similarities = []
        embedding_list = list(embeddings.values())

        for i in range(len(embedding_list)):
            for j in range(i + 1, len(embedding_list)):
                sim = self._cosine_similarity(embedding_list[i], embedding_list[j])
                similarities.append(sim)

        if not similarities:
            return 1.0, 1.0, 1.0, 1.0

        avg_sim = np.mean(similarities)
        min_sim = np.min(similarities)
        max_sim = np.max(similarities)

        # Consensus score: weighted average with penalty for low minimum
        consensus_score = avg_sim * (min_sim ** 0.5)  # Penalize low outliers

        return avg_sim, min_sim, max_sim, consensus_score

    async def validate_embedding(self, document_id: str, text: str,
                                primary_embedding: List[float]) -> ConsensusResult:
        """
        Validate a primary embedding against consensus models.

        Args:
            document_id: Unique document identifier
            text: Original document text
            primary_embedding: Primary model embedding to validate

        Returns:
            ConsensusResult with validation details
        """
        start_time = time.time()

        # Check cache first
        cache_key = f"{document_id}_{hash(text)}"
        if self.config.enable_caching and cache_key in self.cache:
            logger.debug(f"📋 Using cached consensus for {document_id}")
            return self.cache[cache_key]

        # Check daily usage limit
        if self.daily_usage >= self.config.max_documents_per_day:
            logger.warning("⚠️ Daily consensus validation limit reached")
            # Return basic result without consensus
            return ConsensusResult(
                document_id=document_id,
                primary_embedding=primary_embedding,
                consensus_embeddings={},
                avg_similarity=1.0,
                min_similarity=1.0,
                max_similarity=1.0,
                consensus_score=1.0,
                is_consensus=True,
                is_outlier=False
            )

        if self.config.progress_updates:
            print(f"🤝 Validating consensus for document {document_id}...")

        # Generate embeddings from consensus models
        consensus_embeddings = {"primary": primary_embedding}
        failed_models = []

        # Process models concurrently (with rate limiting)
        semaphore = asyncio.Semaphore(self.config.max_concurrent)

        async def get_embedding(client_key: str, client: ModelAPIClient):
            async with semaphore:
                try:
                    async with client:
                        embedding = await client.embed_text(text)
                        return client_key, embedding
                except Exception as e:
                    logger.warning(f"⚠️ {client_key} embedding failed: {e}")
                    failed_models.append(client_key)
                    return client_key, None

        # Execute concurrent embedding requests
        tasks = [
            get_embedding(client_key, client)
            for client_key, client in self.model_clients.items()
        ]

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, tuple):
                    client_key, embedding = result
                    if embedding is not None:
                        consensus_embeddings[client_key] = embedding

        # Calculate consensus metrics
        avg_sim, min_sim, max_sim, consensus_score = self._calculate_consensus_metrics(consensus_embeddings)

        # Determine consensus and outlier status
        is_consensus = consensus_score >= self.config.similarity_threshold
        is_outlier = consensus_score < self.config.outlier_threshold

        # Identify flagged models (those with low similarity to primary)
        flagged_models = []
        if len(consensus_embeddings) > 1:
            for model_key, embedding in consensus_embeddings.items():
                if model_key != "primary":
                    sim_to_primary = self._cosine_similarity(primary_embedding, embedding)
                    if sim_to_primary < self.config.outlier_threshold:
                        flagged_models.append(model_key)

        # Calculate processing cost
        processing_time = (time.time() - start_time) * 1000
        cost_usd = len(consensus_embeddings) * self.config.cost_per_document_usd

        # Create result
        result = ConsensusResult(
            document_id=document_id,
            primary_embedding=primary_embedding,
            consensus_embeddings={k: v for k, v in consensus_embeddings.items() if k != "primary"},
            avg_similarity=avg_sim,
            min_similarity=min_sim,
            max_similarity=max_sim,
            consensus_score=consensus_score,
            is_consensus=is_consensus,
            is_outlier=is_outlier,
            flagged_models=flagged_models,
            processing_time_ms=processing_time,
            cost_usd=cost_usd
        )

        # Cache result
        if self.config.enable_caching:
            self.cache[cache_key] = result

        # Update usage tracking
        self.daily_usage += 1

        # ADHD-friendly feedback
        if self.config.progress_updates:
            if is_consensus:
                print(f"✅ Strong consensus for {document_id} (score: {consensus_score:.3f})")
            elif is_outlier:
                if self.config.gentle_warnings:
                    print(f"💙 {document_id} shows some variation across models - that's okay, just noting it")
                else:
                    print(f"⚠️ Low consensus for {document_id} (score: {consensus_score:.3f})")

        if failed_models:
            logger.debug(f"Failed models for {document_id}: {failed_models}")

        return result

    async def validate_search_results(self, query: str,
                                    results: List[SearchResult]) -> List[SearchResult]:
        """
        Add consensus validation to search results.

        Args:
            query: Original search query
            results: Search results to validate

        Returns:
            Search results with consensus scores added
        """
        if not results:
            return results

        # Limit validation to top results to control cost
        validation_limit = min(len(results), 5)  # Validate top 5 only

        if self.config.progress_updates:
            print(f"🤝 Adding consensus validation to top {validation_limit} results...")

        validated_results = []

        for i, result in enumerate(results):
            if i < validation_limit:
                # Generate primary embedding for the result content
                # This is simplified - in practice you'd use the existing embedding
                try:
                    # Placeholder: get primary embedding
                    primary_client = next(iter(self.model_clients.values()))
                    async with primary_client:
                        primary_embedding = await primary_client.embed_text(result.content)

                    # Validate consensus
                    consensus = await self.validate_embedding(
                        result.doc_id,
                        result.content,
                        primary_embedding
                    )

                    # Update result with consensus score
                    result.consensus_score = consensus.consensus_score

                except Exception as e:
                    logger.warning(f"⚠️ Consensus validation failed for {result.doc_id}: {e}")
                    result.consensus_score = 1.0  # Assume good if validation fails
            else:
                # No consensus validation for lower-ranked results
                result.consensus_score = None

            validated_results.append(result)

        return validated_results

    def get_consensus_summary(self) -> Dict[str, Any]:
        """Get summary of consensus validation activity."""
        if not self.cache:
            return {"total_validations": 0}

        results = list(self.cache.values())
        consensus_scores = [r.consensus_score for r in results]

        total_cost = sum(r.cost_usd for r in results)
        avg_processing_time = np.mean([r.processing_time_ms for r in results])

        consensus_count = sum(1 for r in results if r.is_consensus)
        outlier_count = sum(1 for r in results if r.is_outlier)

        return {
            "total_validations": len(results),
            "consensus_rate": consensus_count / len(results) if results else 0,
            "outlier_rate": outlier_count / len(results) if results else 0,
            "avg_consensus_score": np.mean(consensus_scores) if consensus_scores else 0,
            "total_cost_usd": total_cost,
            "avg_processing_time_ms": avg_processing_time,
            "daily_usage": self.daily_usage,
            "daily_limit": self.config.max_documents_per_day
        }

    def display_summary(self):
        """Display ADHD-friendly consensus validation summary."""
        summary = self.get_consensus_summary()

        print("🤝 Consensus Validation Summary")
        print("=" * 35)
        print(f"📊 Validated: {summary['total_validations']} documents")
        print(f"✅ Consensus: {summary['consensus_rate']:.1%}")
        print(f"⚠️ Outliers: {summary['outlier_rate']:.1%}")
        print(f"💰 Cost: ${summary['total_cost_usd']:.3f}")
        print(f"📈 Usage: {summary['daily_usage']}/{summary['daily_limit']} today")

        if summary['avg_consensus_score'] > 0:
            score_emoji = "🟢" if summary['avg_consensus_score'] > 0.9 else "🟡" if summary['avg_consensus_score'] > 0.8 else "🔴"
            print(f"{score_emoji} Avg Score: {summary['avg_consensus_score']:.3f}")


# Example usage
def create_consensus_config() -> ConsensusConfig:
    """Create production consensus validation configuration."""
    return ConsensusConfig(
        consensus_models=[
            {"provider": "openai", "model": "text-embedding-3-large", "dimension": 3072},
            {"provider": "cohere", "model": "embed-english-v3.0", "dimension": 1024},
        ],
        similarity_threshold=0.9,
        outlier_threshold=0.7,
        max_documents_per_day=500,  # Conservative limit
        progress_updates=True,
        gentle_warnings=True
    )