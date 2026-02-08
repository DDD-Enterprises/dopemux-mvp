"""
Configuration presets for common embedding system use cases.

Provides expert-validated configurations for different environments
and use cases, reducing setup complexity for users.
"""

from typing import Any

from .config import AdvancedEmbeddingConfig, IndexType, SecurityLevel


def create_production_config(**overrides: Any) -> AdvancedEmbeddingConfig:
    """
    Create production-ready embedding configuration.

    Optimized for high-performance, secure business environments with
    cost management and quality validation enabled.

    Returns:
        Production-grade configuration with expert-validated settings
    """
    config_kwargs = dict(
        # High-performance settings
        embedding_model="voyage-context-3",
        embedding_dimension=2048,
        index_type=IndexType.HYBRID,
        enable_quantization=True,
        enable_reranking=True,

        # Security for business data
        security_level=SecurityLevel.INTERNAL,
        enable_pii_detection=True,
        enable_pii_redaction=True,
        audit_embedding_requests=True,

        # ADHD-optimized experience
        enable_progress_tracking=True,
        visual_progress_indicators=True,
        gentle_error_messages=True,

        # Cost management
        monthly_budget_usd=100.0,
        enable_cost_tracking=True,
    )
    config_kwargs.update(overrides)
    return AdvancedEmbeddingConfig(**config_kwargs)


def create_development_config(**overrides: Any) -> AdvancedEmbeddingConfig:
    """
    Create development/testing configuration.

    Optimized for fast iteration cycles with lower costs and
    more verbose feedback for debugging.

    Returns:
        Development-friendly configuration with debugging optimizations
    """
    config_kwargs = dict(
        # Faster, cheaper settings for development
        batch_size=4,
        top_k_candidates=10,
        enable_quantization=False,  # Simpler for debugging
        security_level=SecurityLevel.PUBLIC,
        enable_pii_detection=False,
        enable_pii_redaction=False,
        log_level="DEBUG",

        # More verbose feedback
        progress_update_interval=10,
        gentle_error_messages=True,

        # Lower cost limits
        monthly_budget_usd=10.0,
    )
    config_kwargs.update(overrides)
    return AdvancedEmbeddingConfig(**config_kwargs)


def create_research_config(**overrides: Any) -> AdvancedEmbeddingConfig:
    """
    Create configuration optimized for research and experimentation.

    Enables multi-model consensus validation and detailed quality metrics
    for academic research and model evaluation.

    Returns:
        Research-oriented configuration with quality validation
    """
    config_kwargs = dict(
        # Research-oriented settings
        enable_consensus=True,  # Multi-model validation
        enable_consensus_validation=True,
        enable_reranking=True,
        enable_learning_to_rank=True,
        consensus_threshold=0.85,  # Slightly lower for research

        # Quality tracking
        enable_progress_tracking=True,
        visual_progress_indicators=True,
        log_level="DEBUG",
        enable_performance_metrics=True,

        # Security (often less restrictive for research)
        security_level=SecurityLevel.PUBLIC,
        enable_pii_redaction=False,

        # Cost management for research budgets
        monthly_budget_usd=50.0,
        cost_alert_threshold=0.9,  # Alert at 90% for tighter budget control
    )
    config_kwargs.update(overrides)
    return AdvancedEmbeddingConfig(**config_kwargs)


def create_high_security_config(**overrides: Any) -> AdvancedEmbeddingConfig:
    """
    Create configuration for high-security environments.

    Forces on-premise processing with comprehensive PII redaction
    for handling sensitive or regulated data.

    Returns:
        High-security configuration with on-premise enforcement
    """
    config_kwargs = dict(
        # Security-first settings
        security_level=SecurityLevel.RESTRICTED,  # Forces on-premise
        enable_pii_detection=True,
        enable_pii_redaction=True,
        pii_redaction_mode="remove",
        audit_embedding_requests=True,
        require_encryption=True,
        use_on_premise=True,

        # Additional privacy protections
        cache_embeddings=False,  # Don't cache sensitive data
        enable_compression=False,  # Avoid potential data leakage

        # Performance (may be lower in secure environments)
        batch_size=4,
        max_concurrent_requests=5,
        request_timeout=15.0,

        # ADHD accommodations still important
        gentle_error_messages=True,
        visual_progress_indicators=True,
    )
    config_kwargs.update(overrides)
    return AdvancedEmbeddingConfig(**config_kwargs)


def create_high_performance_config(**overrides: Any) -> AdvancedEmbeddingConfig:
    """
    Create configuration optimized for maximum performance.

    Maximizes throughput and speed for high-volume document processing
    while maintaining quality and cost controls.

    Returns:
        High-performance configuration with optimized settings
    """
    config_kwargs = dict(
        # Performance-optimized settings
        batch_size=32,  # Larger batches for throughput
        max_concurrent_requests=20,  # Higher concurrency
        top_k_candidates=50,  # More candidates for better quality

        # Advanced indexing
        index_type=IndexType.HNSW,
        enable_quantization=True,  # Memory efficiency at scale
        hnsw_m=64,  # More connections for better recall
        hnsw_ef=256,  # Higher search quality

        # Caching for speed
        cache_embeddings=True,
        enable_compression=True,

        # Quality and monitoring
        enable_progress_tracking=True,
        progress_update_interval=50,  # More frequent updates
        enable_consensus_validation=False,
        security_level=SecurityLevel.PUBLIC,

        # Cost management still important
        monthly_budget_usd=500.0,  # Higher budget for performance
        enable_cost_tracking=True,
    )
    config_kwargs.update(overrides)
    return AdvancedEmbeddingConfig(**config_kwargs)


def create_adhd_optimized_config(**overrides: Any) -> AdvancedEmbeddingConfig:
    """
    Create configuration specifically optimized for ADHD developers.

    Maximizes visual feedback, gentle error handling, and progress
    indicators while maintaining reasonable performance.

    Returns:
        ADHD-optimized configuration with maximum accommodation features
    """
    config_kwargs = dict(
        # ADHD-first optimizations
        enable_progress_tracking=True,
        visual_progress_indicators=True,
        gentle_error_messages=True,
        progress_update_interval=25,  # Frequent feedback
        result_complexity_scoring=True,
        max_results_display=10,
        search_timeout=10.0,
        enable_result_preview=True,

        # Moderate performance (not overwhelming)
        batch_size=6,
        top_k_candidates=15,
        max_concurrent_requests=8,

        # Quality feedback for confidence
        enable_consensus=False,  # Start simple, can enable later

        # Cost awareness to reduce anxiety
        monthly_budget_usd=25.0,
        enable_cost_tracking=True,
        cost_alert_threshold=0.75,  # Early warning

        # Security for peace of mind
        security_level=SecurityLevel.INTERNAL,
        enable_pii_redaction=True,
    )
    config_kwargs.update(overrides)
    return AdvancedEmbeddingConfig(**config_kwargs)
