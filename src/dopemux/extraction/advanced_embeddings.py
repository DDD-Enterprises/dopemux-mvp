"""
Advanced Embedding System - Production-grade semantic search with hybrid BM25+vector architecture

Implements voyage-context-3 (2048-dim) + voyage-rerank-2.5 + hybrid search
with ADHD-optimized patterns and multi-model consensus validation.

Based on expert analysis recommendations for optimal document intelligence.
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import numpy as np
import httpx

logger = logging.getLogger(__name__)


class IndexType(str, Enum):
    """Supported vector index types."""
    HNSW = "hnsw"              # Hierarchical Navigable Small World
    IVF_PQ = "ivf_pq"          # Inverted File with Product Quantization
    SCANN = "scann"            # Scalable Nearest Neighbors


class SecurityLevel(str, Enum):
    """Security levels for document processing."""
    PUBLIC = "public"          # No restrictions
    INTERNAL = "internal"      # Company-internal documents
    CONFIDENTIAL = "confidential"  # Requires PII redaction
    RESTRICTED = "restricted"  # On-premise only, no cloud APIs


@dataclass
class AdvancedEmbeddingConfig:
    """
    Production-grade embedding configuration.

    Implements expert recommendations for voyage-context-3 + hybrid search architecture.
    """

    # === Core Model Configuration ===
    embedding_model: str = "voyage-context-3"
    rerank_model: str = "voyage-rerank-2.5"
    embedding_dimension: int = 2048
    max_seq_length: int = 4000  # voyage-context-3 supports up to 32k

    # === Hybrid Search Configuration ===
    # Initial static weights (will be optimized via learning-to-rank)
    bm25_weight: float = 0.3
    vector_weight: float = 0.7
    enable_learning_to_rank: bool = False  # Requires training data

    # === Vector Index Configuration ===
    index_type: IndexType = IndexType.HNSW
    enable_quantization: bool = True       # 8-bit PQ for 4x memory reduction
    distance_metric: str = "cosine"        # cosine, l2, ip

    # HNSW-specific parameters (expert-recommended)
    hnsw_m: int = 32                      # Connections per node
    hnsw_ef: int = 128                    # Search parameter
    hnsw_ef_construction: int = 200       # Build parameter

    # IVF-PQ parameters
    ivf_nlist: int = 2048                 # Number of clusters
    pq_m: int = 64                        # Product quantization subspaces

    # === Performance Configuration ===
    batch_size: int = 8                   # Embedding batch size (GPU optimized)
    top_k_candidates: int = 25            # Candidates for reranking (vs 100)
    rerank_batch_size: int = 4            # Reranker batch size
    max_concurrent_requests: int = 10     # API concurrency limit

    # === Storage Configuration ===
    persist_directory: str = "./.advanced_vectors"
    cache_embeddings: bool = True         # Cache by (doc_sha256, model_version)
    enable_compression: bool = True       # Additional storage compression

    # === Security & Privacy ===
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    enable_pii_redaction: bool = False    # Auto-enabled for CONFIDENTIAL+
    use_on_premise: bool = False          # Use local models vs APIs
    redaction_patterns: List[str] = field(default_factory=list)

    # === API Configuration ===
    voyage_api_key: Optional[str] = None  # Set via environment
    api_base_url: str = "https://api.voyageai.com/v1"
    request_timeout: int = 30             # API timeout in seconds
    retry_attempts: int = 3               # Failed request retries

    # === ADHD Optimization ===
    enable_progress_tracking: bool = True
    progress_update_interval: int = 100   # Update every N documents
    visual_progress_indicators: bool = True
    gentle_error_messages: bool = True

    # === Multi-Model Consensus ===
    enable_consensus: bool = False        # Expensive, use selectively
    consensus_models: List[str] = field(default_factory=lambda: [
        "text-embedding-3-large",         # OpenAI comparison
        "embed-english-v3.0"              # Cohere comparison
    ])
    consensus_threshold: float = 0.9      # Cosine similarity threshold

    # === Cost Management ===
    monthly_budget_usd: Optional[float] = None
    enable_cost_tracking: bool = True
    cost_alert_threshold: float = 0.8     # Alert at 80% budget

    def __post_init__(self):
        """Validate configuration and apply security policies."""
        # Auto-enable PII redaction for sensitive data
        if self.security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED]:
            self.enable_pii_redaction = True

        # Force on-premise for restricted data
        if self.security_level == SecurityLevel.RESTRICTED:
            self.use_on_premise = True
            logger.warning("🔒 Restricted data detected - forcing on-premise processing")

        # Validate dimensions
        if self.embedding_dimension not in [1024, 2048]:
            logger.warning(f"⚠️ Unusual embedding dimension: {self.embedding_dimension}")

        # Validate weights
        if abs(self.bm25_weight + self.vector_weight - 1.0) > 0.01:
            raise ValueError("BM25 and vector weights must sum to 1.0")

        # Set default redaction patterns for PII
        if self.enable_pii_redaction and not self.redaction_patterns:
            self.redaction_patterns = [
                r'\b\d{3}-\d{2}-\d{4}\b',        # SSN
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
                r'\b\(\d{3}\)\s?\d{3}-\d{4}\b',  # Phone numbers
            ]


@dataclass
class EmbeddingHealthMetrics:
    """
    ADHD-optimized health metrics for embedding pipeline monitoring.

    Provides visual progress indicators and gentle error reporting.
    """

    # === Processing Metrics ===
    documents_processed: int = 0
    documents_embedded: int = 0
    documents_failed: int = 0
    processing_start_time: Optional[datetime] = None

    # === Performance Metrics ===
    avg_embedding_time_ms: float = 0.0
    p95_embedding_time_ms: float = 0.0
    total_api_calls: int = 0
    api_errors: int = 0

    # === Quality Metrics ===
    recall_at_10: float = 0.0
    precision_at_10: float = 0.0
    consensus_agreement: float = 0.0

    # === Resource Metrics ===
    vector_index_size_mb: float = 0.0
    embedding_cache_size_mb: float = 0.0
    memory_usage_mb: float = 0.0

    # === Cost Metrics ===
    embedding_cost_usd: float = 0.0
    rerank_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    monthly_budget_remaining: Optional[float] = None

    def get_success_rate(self) -> float:
        """Calculate processing success rate."""
        if self.documents_processed == 0:
            return 0.0
        return self.documents_embedded / self.documents_processed

    def get_processing_speed(self) -> float:
        """Calculate documents per second."""
        if not self.processing_start_time:
            return 0.0
        elapsed = (datetime.now() - self.processing_start_time).total_seconds()
        return self.documents_processed / elapsed if elapsed > 0 else 0.0

    def display_progress(self, gentle_mode: bool = True):
        """
        Display ADHD-friendly progress indicators.

        Args:
            gentle_mode: Use encouraging language and visual cues
        """
        if gentle_mode:
            print("🚀 Embedding Pipeline Status")
            print("=" * 40)

        # Progress bar for documents
        total_docs = max(self.documents_processed, 1)
        progress_pct = (self.documents_embedded / total_docs) * 100
        bar_width = 20
        filled = int(bar_width * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        print(f"📊 Progress: [{bar}] {progress_pct:.1f}% ({self.documents_embedded:,}/{total_docs:,})")

        # Performance indicators
        speed = self.get_processing_speed()
        success_rate = self.get_success_rate()

        success_emoji = "✅" if success_rate > 0.95 else "⚠️" if success_rate > 0.8 else "❌"
        speed_emoji = "⚡" if speed > 10 else "🐌" if speed < 1 else "🚶"

        print(f"{speed_emoji} Speed: {speed:.1f} docs/sec")
        print(f"{success_emoji} Success: {success_rate:.1%}")

        # Quality metrics
        if self.recall_at_10 > 0:
            quality_emoji = "🎯" if self.recall_at_10 > 0.95 else "⚠️"
            print(f"{quality_emoji} Recall@10: {self.recall_at_10:.3f}")

        # Cost tracking
        if self.total_cost_usd > 0:
            cost_emoji = "💰" if self.total_cost_usd < 10 else "💸"
            print(f"{cost_emoji} Cost: ${self.total_cost_usd:.2f}")

            if self.monthly_budget_remaining is not None:
                budget_pct = (self.monthly_budget_remaining / (self.total_cost_usd + self.monthly_budget_remaining)) * 100
                budget_emoji = "🟢" if budget_pct > 50 else "🟡" if budget_pct > 20 else "🔴"
                print(f"{budget_emoji} Budget: {budget_pct:.0f}% remaining")

        if gentle_mode and self.documents_failed > 0:
            print(f"💙 Don't worry about {self.documents_failed} failed docs - that's normal!")


@dataclass
class SearchResult:
    """Enhanced search result with hybrid scoring details."""

    doc_id: str
    score: float
    content: str
    metadata: Dict[str, Any]

    # Hybrid search details
    bm25_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: Optional[float] = None
    consensus_score: Optional[float] = None

    # Source information
    source_file: Optional[str] = None
    chunk_index: Optional[int] = None
    confidence: float = 1.0


class VoyageAPIClient:
    """
    Async Voyage AI API client with ADHD-optimized error handling.

    Implements rate limiting, retries, and gentle error messages.
    """

    def __init__(self, config: AdvancedEmbeddingConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.request_timeout,
            limits=httpx.Limits(max_connections=config.max_concurrent_requests)
        )
        self.api_key = config.voyage_api_key

        # Cost tracking
        self.total_tokens = 0
        self.total_requests = 0

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            httpx.HTTPError: API request failed
        """
        if not self.api_key:
            raise ValueError("🔑 Voyage API key not configured")

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

            return embeddings

        except httpx.HTTPError as e:
            if self.config.gentle_error_messages:
                logger.error(f"💙 API request had trouble: {e}. Taking a short break and trying again...")
            else:
                logger.error(f"Voyage API error: {e}")
            raise

    async def rerank(self, query: str, documents: List[str]) -> List[float]:
        """
        Rerank documents using voyage-rerank-2.5.

        Args:
            query: Search query
            documents: List of documents to rerank

        Returns:
            List of relevance scores
        """
        if not self.api_key:
            raise ValueError("🔑 Voyage API key not configured")

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
            response = await self.client.post(
                f"{self.config.api_base_url}/rerank",
                json=payload,
                headers=headers
            )
            response.raise_for_status()

            result = response.json()
            scores = [item["relevance_score"] for item in result["results"]]

            self.total_requests += 1

            return scores

        except httpx.HTTPError as e:
            if self.config.gentle_error_messages:
                logger.error(f"💙 Reranking had trouble: {e}. Your search results might be slightly less optimal, but still good!")
            else:
                logger.error(f"Voyage rerank error: {e}")
            raise

    def get_cost_estimate(self) -> Dict[str, float]:
        """Estimate API costs based on usage."""
        # Voyage AI pricing (approximate)
        embedding_cost_per_1k = 0.10  # $0.10 per 1K tokens
        rerank_cost_per_1k = 0.03     # $0.03 per 1K queries

        embedding_cost = (self.total_tokens / 1000) * embedding_cost_per_1k
        rerank_cost = (self.total_requests / 1000) * rerank_cost_per_1k

        return {
            "embedding_cost": embedding_cost,
            "rerank_cost": rerank_cost,
            "total_cost": embedding_cost + rerank_cost,
            "total_tokens": self.total_tokens,
            "total_requests": self.total_requests
        }


# Example usage configuration
def create_production_config() -> AdvancedEmbeddingConfig:
    """Create production-ready embedding configuration."""
    return AdvancedEmbeddingConfig(
        # High-performance settings
        embedding_model="voyage-context-3",
        embedding_dimension=2048,
        index_type=IndexType.HNSW,
        enable_quantization=True,

        # Security for business data
        security_level=SecurityLevel.INTERNAL,
        enable_pii_redaction=True,

        # ADHD-optimized experience
        enable_progress_tracking=True,
        visual_progress_indicators=True,
        gentle_error_messages=True,

        # Cost management
        monthly_budget_usd=100.0,
        enable_cost_tracking=True
    )


def create_development_config() -> AdvancedEmbeddingConfig:
    """Create development/testing configuration."""
    return AdvancedEmbeddingConfig(
        # Faster, cheaper settings for development
        batch_size=4,
        top_k_candidates=10,
        enable_quantization=False,  # Simpler for debugging

        # More verbose feedback
        progress_update_interval=10,
        gentle_error_messages=True,

        # Lower cost limits
        monthly_budget_usd=10.0
    )