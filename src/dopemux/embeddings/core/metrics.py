"""
ADHD-optimized health metrics and monitoring for the embedding system.

Provides visual progress indicators, gentle error reporting, and comprehensive
performance tracking designed to reduce cognitive load.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class EmbeddingHealthMetrics:
    """
    ADHD-optimized health metrics for embedding pipeline monitoring.

    Provides visual progress indicators and gentle error reporting
    designed to reduce cognitive load and provide encouraging feedback.
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

    def update_cost_metrics(self, embedding_cost: float = 0.0, rerank_cost: float = 0.0):
        """
        Update cost tracking metrics.

        Args:
            embedding_cost: Cost of embedding operations
            rerank_cost: Cost of reranking operations
        """
        self.embedding_cost_usd += embedding_cost
        self.rerank_cost_usd += rerank_cost
        self.total_cost_usd = self.embedding_cost_usd + self.rerank_cost_usd

    def update_performance_metrics(self, embedding_time_ms: float, api_success: bool = True):
        """
        Update performance tracking metrics.

        Args:
            embedding_time_ms: Time taken for embedding operation
            api_success: Whether the API call succeeded
        """
        self.total_api_calls += 1
        if not api_success:
            self.api_errors += 1

        # Update average embedding time (simple moving average)
        if self.avg_embedding_time_ms == 0:
            self.avg_embedding_time_ms = embedding_time_ms
        else:
            # Exponential moving average
            alpha = 0.1  # Smoothing factor
            self.avg_embedding_time_ms = (alpha * embedding_time_ms +
                                        (1 - alpha) * self.avg_embedding_time_ms)

        # Update P95 (simplified - would need proper percentile tracking in production)
        self.p95_embedding_time_ms = max(self.p95_embedding_time_ms, embedding_time_ms)

    def update_quality_metrics(self, recall_at_10: float = 0.0,
                             precision_at_10: float = 0.0,
                             consensus_agreement: float = 0.0):
        """
        Update quality metrics.

        Args:
            recall_at_10: Recall at 10 metric
            precision_at_10: Precision at 10 metric
            consensus_agreement: Multi-model consensus agreement
        """
        if recall_at_10 > 0:
            self.recall_at_10 = recall_at_10
        if precision_at_10 > 0:
            self.precision_at_10 = precision_at_10
        if consensus_agreement > 0:
            self.consensus_agreement = consensus_agreement

    def get_summary(self) -> dict:
        """Get a summary of all metrics as a dictionary."""
        return {
            "processing": {
                "total_processed": self.documents_processed,
                "embedded": self.documents_embedded,
                "failed": self.documents_failed,
                "success_rate": self.get_success_rate(),
                "speed_docs_per_sec": self.get_processing_speed()
            },
            "performance": {
                "avg_embedding_time_ms": self.avg_embedding_time_ms,
                "p95_embedding_time_ms": self.p95_embedding_time_ms,
                "total_api_calls": self.total_api_calls,
                "api_errors": self.api_errors,
                "api_success_rate": 1 - (self.api_errors / max(self.total_api_calls, 1))
            },
            "quality": {
                "recall_at_10": self.recall_at_10,
                "precision_at_10": self.precision_at_10,
                "consensus_agreement": self.consensus_agreement
            },
            "resources": {
                "vector_index_size_mb": self.vector_index_size_mb,
                "embedding_cache_size_mb": self.embedding_cache_size_mb,
                "memory_usage_mb": self.memory_usage_mb
            },
            "cost": {
                "embedding_cost_usd": self.embedding_cost_usd,
                "rerank_cost_usd": self.rerank_cost_usd,
                "total_cost_usd": self.total_cost_usd,
                "budget_remaining": self.monthly_budget_remaining
            }
        }