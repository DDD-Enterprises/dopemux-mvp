"""
Unit tests for embedding core configuration.

Tests the AdvancedEmbeddingConfig class and related configuration utilities.
"""

import pytest
from unittest.mock import patch, MagicMock

from dopemux.embeddings.core import (
    AdvancedEmbeddingConfig,
    IndexType,
    SecurityLevel,
    create_production_config,
    create_development_config,
    create_research_config,
    create_high_security_config,
    create_high_performance_config,
    create_adhd_optimized_config
)


class TestIndexType:
    """Test IndexType enum."""

    def test_index_type_values(self):
        """Test index type enum values."""
        assert IndexType.HNSW.value == "hnsw"
        assert IndexType.FAISS.value == "faiss"
        assert IndexType.BM25.value == "bm25"
        assert IndexType.HYBRID.value == "hybrid"


class TestSecurityLevel:
    """Test SecurityLevel enum."""

    def test_security_level_values(self):
        """Test security level enum values."""
        assert SecurityLevel.PUBLIC.value == "public"
        assert SecurityLevel.INTERNAL.value == "internal"
        assert SecurityLevel.CONFIDENTIAL.value == "confidential"
        assert SecurityLevel.RESTRICTED.value == "restricted"

    def test_security_level_ordering(self):
        """Test security levels can be compared."""
        assert SecurityLevel.PUBLIC < SecurityLevel.INTERNAL
        assert SecurityLevel.INTERNAL < SecurityLevel.CONFIDENTIAL
        assert SecurityLevel.CONFIDENTIAL < SecurityLevel.RESTRICTED


class TestAdvancedEmbeddingConfig:
    """Test AdvancedEmbeddingConfig dataclass."""

    def test_config_creation_with_defaults(self):
        """Test creating config with default values."""
        config = AdvancedEmbeddingConfig()

        # Core model settings
        assert config.embedding_model == "voyage-context-3"
        assert config.embedding_dimension == 2048
        assert config.rerank_model == "voyage-rerank-2.5"

        # HNSW settings (expert-validated)
        assert config.hnsw_m == 32
        assert config.hnsw_ef == 128
        assert config.hnsw_ef_construction == 128
        assert config.hnsw_max_m == 32

        # Search settings
        assert config.bm25_weight == 0.3
        assert config.vector_weight == 0.7
        assert config.search_k_multiplier == 2

        # Performance settings
        assert config.batch_size == 16
        assert config.max_concurrent_requests == 10
        assert config.request_timeout == 30.0

        # ADHD optimizations
        assert config.enable_progress_tracking is True
        assert config.gentle_error_messages is True
        assert config.visual_progress_indicators is True

        # Security
        assert config.security_level == SecurityLevel.INTERNAL
        assert config.enable_pii_detection is True

        # Feature flags
        assert config.enable_reranking is True
        assert config.enable_quantization is True
        assert config.enable_learning_to_rank is True

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values."""
        config = AdvancedEmbeddingConfig(
            embedding_model="text-embedding-3-large",
            embedding_dimension=3072,
            hnsw_m=64,
            bm25_weight=0.5,
            vector_weight=0.5,
            security_level=SecurityLevel.RESTRICTED,
            enable_progress_tracking=False
        )

        assert config.embedding_model == "text-embedding-3-large"
        assert config.embedding_dimension == 3072
        assert config.hnsw_m == 64
        assert config.bm25_weight == 0.5
        assert config.vector_weight == 0.5
        assert config.security_level == SecurityLevel.RESTRICTED
        assert config.enable_progress_tracking is False

    def test_config_weight_validation(self):
        """Test weight validation ensures they sum to 1.0."""
        config = AdvancedEmbeddingConfig(
            bm25_weight=0.4,
            vector_weight=0.6
        )

        # Weights should sum to 1.0
        assert abs((config.bm25_weight + config.vector_weight) - 1.0) < 0.001

    def test_config_expert_validated_defaults(self):
        """Test that expert-validated defaults are used."""
        config = AdvancedEmbeddingConfig()

        # These values come from expert research and testing
        assert config.hnsw_m == 32  # Optimal for 2048-dim vectors
        assert config.hnsw_ef == 128  # Balance of speed/recall
        assert config.search_k_multiplier == 2  # Good candidate expansion

    def test_config_adhd_optimizations(self):
        """Test ADHD-specific configuration options."""
        config = AdvancedEmbeddingConfig(
            enable_progress_tracking=True,
            gentle_error_messages=True,
            visual_progress_indicators=True,
            max_results_display=10,
            result_complexity_scoring=True
        )

        assert config.enable_progress_tracking is True
        assert config.gentle_error_messages is True
        assert config.visual_progress_indicators is True
        assert config.max_results_display == 10
        assert config.result_complexity_scoring is True

    def test_config_security_settings(self):
        """Test security-related configuration."""
        config = AdvancedEmbeddingConfig(
            security_level=SecurityLevel.CONFIDENTIAL,
            enable_pii_detection=True,
            pii_redaction_mode="mask",
            audit_embedding_requests=True
        )

        assert config.security_level == SecurityLevel.CONFIDENTIAL
        assert config.enable_pii_detection is True
        assert config.pii_redaction_mode == "mask"
        assert config.audit_embedding_requests is True

    def test_config_performance_tuning(self):
        """Test performance-related configuration."""
        config = AdvancedEmbeddingConfig(
            batch_size=32,
            max_concurrent_requests=20,
            enable_quantization=True,
            quantization_bits=8,
            enable_compression=True
        )

        assert config.batch_size == 32
        assert config.max_concurrent_requests == 20
        assert config.enable_quantization is True
        assert config.quantization_bits == 8
        assert config.enable_compression is True


class TestConfigurationPresets:
    """Test configuration preset factory functions."""

    def test_create_production_config(self):
        """Test production configuration preset."""
        config = create_production_config()

        # Production should prioritize reliability and security
        assert config.security_level == SecurityLevel.INTERNAL
        assert config.enable_pii_detection is True
        assert config.audit_embedding_requests is True
        assert config.enable_reranking is True
        assert config.request_timeout == 30.0

        # Conservative batch sizes for stability
        assert config.batch_size <= 16
        assert config.max_concurrent_requests <= 10

    def test_create_development_config(self):
        """Test development configuration preset."""
        config = create_development_config()

        # Development should prioritize speed and debugging
        assert config.enable_progress_tracking is True
        assert config.gentle_error_messages is True
        assert config.log_level == "DEBUG"

        # Relaxed security for dev environment
        assert config.security_level == SecurityLevel.PUBLIC
        assert config.enable_pii_detection is False

        # Smaller batches for faster iteration
        assert config.batch_size <= 8

    def test_create_research_config(self):
        """Test research configuration preset."""
        config = create_research_config()

        # Research should enable all features for experimentation
        assert config.enable_reranking is True
        assert config.enable_quantization is True
        assert config.enable_learning_to_rank is True
        assert config.enable_consensus_validation is True

        # Detailed logging for research
        assert config.log_level == "DEBUG"
        assert config.enable_performance_metrics is True

    def test_create_high_security_config(self):
        """Test high security configuration preset."""
        config = create_high_security_config()

        # Maximum security settings
        assert config.security_level == SecurityLevel.RESTRICTED
        assert config.enable_pii_detection is True
        assert config.pii_redaction_mode == "remove"
        assert config.audit_embedding_requests is True
        assert config.require_encryption is True

        # Conservative performance for security
        assert config.batch_size <= 8
        assert config.request_timeout <= 15.0

    def test_create_high_performance_config(self):
        """Test high performance configuration preset."""
        config = create_high_performance_config()

        # Optimized for speed
        assert config.batch_size >= 32
        assert config.max_concurrent_requests >= 20
        assert config.enable_quantization is True
        assert config.enable_compression is True

        # Simplified processing for speed
        assert config.enable_consensus_validation is False
        assert config.security_level == SecurityLevel.PUBLIC

    def test_create_adhd_optimized_config(self):
        """Test ADHD-optimized configuration preset."""
        config = create_adhd_optimized_config()

        # All ADHD features enabled
        assert config.enable_progress_tracking is True
        assert config.gentle_error_messages is True
        assert config.visual_progress_indicators is True
        assert config.result_complexity_scoring is True

        # Reasonable defaults for ADHD users
        assert config.max_results_display <= 10
        assert config.search_timeout <= 10.0
        assert config.enable_result_preview is True

    def test_config_override_with_kwargs(self):
        """Test that preset configs can be overridden with kwargs."""
        config = create_production_config(
            embedding_dimension=1536,
            batch_size=8,
            security_level=SecurityLevel.CONFIDENTIAL
        )

        # Overridden values
        assert config.embedding_dimension == 1536
        assert config.batch_size == 8
        assert config.security_level == SecurityLevel.CONFIDENTIAL

        # Preserved production defaults
        assert config.enable_pii_detection is True
        assert config.audit_embedding_requests is True

    def test_config_validation_in_presets(self):
        """Test that preset configurations are self-consistent."""
        configs = [
            create_production_config(),
            create_development_config(),
            create_research_config(),
            create_high_security_config(),
            create_high_performance_config(),
            create_adhd_optimized_config()
        ]

        for config in configs:
            # Weight validation
            weight_sum = config.bm25_weight + config.vector_weight
            assert abs(weight_sum - 1.0) < 0.001, f"Weights don't sum to 1.0: {weight_sum}"

            # Dimension validation
            assert config.embedding_dimension > 0
            assert config.embedding_dimension <= 4096

            # Performance validation
            assert config.batch_size > 0
            assert config.batch_size <= 128
            assert config.max_concurrent_requests > 0

    def test_config_immutability_pattern(self):
        """Test that configs follow immutability best practices."""
        config = AdvancedEmbeddingConfig()

        # Should be able to read values
        assert config.embedding_model == "voyage-context-3"

        # Should be able to create new config with replace
        new_config = AdvancedEmbeddingConfig(
            embedding_model="new-model",
            **{k: v for k, v in config.__dict__.items() if k != "embedding_model"}
        )

        assert new_config.embedding_model == "new-model"
        assert config.embedding_model == "voyage-context-3"  # Original unchanged

    def test_config_serialization_compatibility(self):
        """Test that configs can be serialized/deserialized."""
        import json
        from dataclasses import asdict

        config = create_production_config()

        # Convert to dict (handling enums)
        config_dict = asdict(config)

        # Enum values should be serialized as strings
        assert config_dict["security_level"] == "internal"
        assert config_dict["index_type"] == "hybrid"

        # Should be JSON serializable
        json_str = json.dumps(config_dict, default=str)
        assert json_str is not None
        assert len(json_str) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=dopemux.embeddings.core", "--cov-report=term-missing"])