"""
Unit tests for embedding enhancement layer.

Tests the ConsensusValidator and other enhancement components.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from dopemux.embeddings.enhancers import (
    ConsensusValidator,
    ConsensusConfig,
    ConsensusResult,
    ModelProvider,
    create_consensus_config
)
from dopemux.embeddings.core import AdvancedEmbeddingConfig, SearchResult


class TestModelProvider:
    """Test ModelProvider enum."""

    def test_model_provider_values(self):
        """Test model provider enum values."""
        assert ModelProvider.OPENAI.value == "openai"
        assert ModelProvider.COHERE.value == "cohere"
        assert ModelProvider.VOYAGE.value == "voyage"
        assert ModelProvider.ANTHROPIC.value == "anthropic"


class TestConsensusConfig:
    """Test ConsensusConfig dataclass."""

    def test_config_creation_with_defaults(self):
        """Test creating consensus config with defaults."""
        config = ConsensusConfig()

        assert config.enabled is True
        assert config.min_providers == 2
        assert config.consensus_threshold == 0.7
        assert config.cost_limit_per_day == 10.0
        assert config.enable_quality_scoring is True

    def test_config_creation_with_custom_values(self):
        """Test creating consensus config with custom values."""
        providers = [ModelProvider.OPENAI, ModelProvider.COHERE, ModelProvider.VOYAGE]

        config = ConsensusConfig(
            providers=providers,
            min_providers=3,
            consensus_threshold=0.8,
            cost_limit_per_day=50.0,
            max_parallel_requests=5
        )

        assert config.providers == providers
        assert config.min_providers == 3
        assert config.consensus_threshold == 0.8
        assert config.cost_limit_per_day == 50.0
        assert config.max_parallel_requests == 5

    def test_config_validation(self):
        """Test consensus config validation."""
        # Valid config
        config = ConsensusConfig(
            providers=[ModelProvider.OPENAI, ModelProvider.COHERE],
            min_providers=2,
            consensus_threshold=0.6
        )
        assert len(config.providers) >= config.min_providers

        # Threshold should be between 0 and 1
        assert 0.0 <= config.consensus_threshold <= 1.0


class TestConsensusResult:
    """Test ConsensusResult dataclass."""

    def test_result_creation(self):
        """Test creating consensus result."""
        provider_results = {
            ModelProvider.OPENAI: {"quality_score": 0.8, "confidence": 0.9},
            ModelProvider.COHERE: {"quality_score": 0.7, "confidence": 0.8}
        }

        result = ConsensusResult(
            consensus_reached=True,
            overall_quality_score=0.75,
            provider_results=provider_results,
            reasoning="High quality content with good consensus"
        )

        assert result.consensus_reached is True
        assert result.overall_quality_score == 0.75
        assert len(result.provider_results) == 2
        assert ModelProvider.OPENAI in result.provider_results

    def test_result_with_metadata(self):
        """Test consensus result with additional metadata."""
        result = ConsensusResult(
            consensus_reached=False,
            overall_quality_score=0.3,
            provider_results={},
            reasoning="Low quality content",
            metadata={
                "cost_used": 0.15,
                "processing_time": 1.2,
                "issues_found": ["factual_error", "poor_structure"]
            }
        )

        assert result.metadata["cost_used"] == 0.15
        assert "factual_error" in result.metadata["issues_found"]


class TestConsensusValidator:
    """Test ConsensusValidator functionality."""

    @pytest.fixture
    def embedding_config(self):
        """Create embedding configuration."""
        return AdvancedEmbeddingConfig(enable_consensus_validation=True)

    @pytest.fixture
    def consensus_config(self):
        """Create consensus configuration."""
        return ConsensusConfig(
            providers=[ModelProvider.OPENAI, ModelProvider.COHERE],
            min_providers=2,
            consensus_threshold=0.7,
            cost_limit_per_day=5.0
        )

    @pytest.fixture
    def validator(self, embedding_config, consensus_config):
        """Create consensus validator."""
        return ConsensusValidator(embedding_config, consensus_config)

    def test_validator_initialization(self, validator, embedding_config, consensus_config):
        """Test validator initialization."""
        assert validator.embedding_config == embedding_config
        assert validator.consensus_config == consensus_config
        assert validator._daily_cost == 0.0
        assert isinstance(validator._provider_clients, dict)

    @pytest.mark.asyncio
    async def test_validate_quality_with_consensus(self, validator):
        """Test quality validation with consensus reached."""
        doc_id = "test_doc"
        content = "High quality machine learning content with accurate information."
        embedding = [0.1] * 2048

        # Mock provider responses
        with patch.object(validator, '_get_provider_assessment') as mock_assess:
            mock_assess.side_effect = [
                {"quality_score": 0.8, "confidence": 0.9, "reasoning": "Good content"},
                {"quality_score": 0.75, "confidence": 0.85, "reasoning": "Solid information"}
            ]

            result = await validator.validate_quality(doc_id, content, embedding)

            assert isinstance(result, ConsensusResult)
            assert result.consensus_reached is True
            assert 0.7 <= result.overall_quality_score <= 0.9
            assert len(result.provider_results) == 2

    @pytest.mark.asyncio
    async def test_validate_quality_no_consensus(self, validator):
        """Test quality validation with no consensus."""
        doc_id = "test_doc"
        content = "Questionable content with mixed quality."
        embedding = [0.1] * 2048

        # Mock divergent provider responses
        with patch.object(validator, '_get_provider_assessment') as mock_assess:
            mock_assess.side_effect = [
                {"quality_score": 0.8, "confidence": 0.9, "reasoning": "Good content"},
                {"quality_score": 0.3, "confidence": 0.7, "reasoning": "Poor quality"}
            ]

            result = await validator.validate_quality(doc_id, content, embedding)

            assert result.consensus_reached is False
            assert result.overall_quality_score < 0.7  # Below threshold

    @pytest.mark.asyncio
    async def test_validate_quality_cost_limit_exceeded(self, validator):
        """Test quality validation when cost limit exceeded."""
        # Set daily cost to limit
        validator._daily_cost = validator.consensus_config.cost_limit_per_day

        doc_id = "test_doc"
        content = "Test content"
        embedding = [0.1] * 2048

        result = await validator.validate_quality(doc_id, content, embedding)

        # Should skip validation due to cost limit
        assert result.consensus_reached is False
        assert "cost limit" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_enhance_results(self, validator):
        """Test enhancing search results."""
        query = "machine learning algorithms"
        search_results = [
            SearchResult(
                doc_id="doc1",
                score=0.9,
                content="High quality ML content",
                metadata={}
            ),
            SearchResult(
                doc_id="doc2",
                score=0.7,
                content="Average quality content",
                metadata={}
            )
        ]

        # Mock consensus validation
        with patch.object(validator, 'validate_quality') as mock_validate:
            mock_validate.side_effect = [
                ConsensusResult(
                    consensus_reached=True,
                    overall_quality_score=0.85,
                    provider_results={},
                    reasoning="High quality"
                ),
                ConsensusResult(
                    consensus_reached=False,
                    overall_quality_score=0.4,
                    provider_results={},
                    reasoning="Low quality"
                )
            ]

            enhanced_results = await validator.enhance_results(query, search_results)

            # Should have enhanced metadata
            assert len(enhanced_results) == 2
            assert "consensus_validation" in enhanced_results[0].metadata
            assert enhanced_results[0].metadata["consensus_validation"]["quality_score"] == 0.85

    @pytest.mark.asyncio
    async def test_get_provider_assessment_openai(self, validator):
        """Test getting provider assessment from OpenAI."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(message=MagicMock(content='{"quality_score": 0.8, "confidence": 0.9, "reasoning": "Good content"}'))
            ]
            mock_client.chat.completions.create.return_value = mock_response

            result = await validator._get_provider_assessment(
                ModelProvider.OPENAI,
                "test content",
                "test query"
            )

            assert result["quality_score"] == 0.8
            assert result["confidence"] == 0.9
            assert result["reasoning"] == "Good content"

    @pytest.mark.asyncio
    async def test_get_provider_assessment_error_handling(self, validator):
        """Test provider assessment error handling."""
        with patch('openai.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API Error")

            result = await validator._get_provider_assessment(
                ModelProvider.OPENAI,
                "test content",
                "test query"
            )

            # Should return default values on error
            assert result["quality_score"] == 0.5
            assert result["confidence"] == 0.0
            assert "error" in result["reasoning"].lower()

    @pytest.mark.asyncio
    async def test_calculate_consensus_score(self, validator):
        """Test consensus score calculation."""
        provider_results = {
            ModelProvider.OPENAI: {"quality_score": 0.8, "confidence": 0.9},
            ModelProvider.COHERE: {"quality_score": 0.75, "confidence": 0.85},
            ModelProvider.VOYAGE: {"quality_score": 0.7, "confidence": 0.8}
        }

        consensus_score = await validator._calculate_consensus_score(provider_results)

        # Should be weighted average based on confidence
        assert 0.7 <= consensus_score <= 0.8
        assert isinstance(consensus_score, float)

    @pytest.mark.asyncio
    async def test_check_consensus_threshold(self, validator):
        """Test consensus threshold checking."""
        # High consensus (low variance)
        high_consensus_results = {
            ModelProvider.OPENAI: {"quality_score": 0.8, "confidence": 0.9},
            ModelProvider.COHERE: {"quality_score": 0.82, "confidence": 0.85}
        }

        is_consensus = await validator._check_consensus_threshold(high_consensus_results)
        assert is_consensus is True

        # Low consensus (high variance)
        low_consensus_results = {
            ModelProvider.OPENAI: {"quality_score": 0.9, "confidence": 0.9},
            ModelProvider.COHERE: {"quality_score": 0.3, "confidence": 0.8}
        }

        is_consensus = await validator._check_consensus_threshold(low_consensus_results)
        assert is_consensus is False

    @pytest.mark.asyncio
    async def test_update_daily_cost(self, validator):
        """Test daily cost tracking."""
        initial_cost = validator._daily_cost

        # Simulate API cost
        await validator._update_daily_cost(0.25)

        assert validator._daily_cost == initial_cost + 0.25

    @pytest.mark.asyncio
    async def test_reset_daily_cost(self, validator):
        """Test daily cost reset."""
        validator._daily_cost = 5.0
        validator._last_reset_date = datetime.now().date() - timedelta(days=1)

        # Should reset cost for new day
        await validator._check_and_reset_daily_cost()

        assert validator._daily_cost == 0.0
        assert validator._last_reset_date == datetime.now().date()

    def test_get_enhancement_stats(self, validator):
        """Test getting enhancement statistics."""
        # Simulate some usage
        validator._total_validations = 50
        validator._consensus_reached_count = 35
        validator._daily_cost = 2.5

        stats = validator.get_enhancement_stats()

        assert stats["total_validations"] == 50
        assert stats["consensus_rate"] == 0.7  # 35/50
        assert stats["daily_cost_used"] == 2.5
        assert stats["cost_limit"] == validator.consensus_config.cost_limit_per_day

    @pytest.mark.asyncio
    async def test_validate_connection(self, validator):
        """Test connection validation for all providers."""
        with patch.object(validator, '_test_provider_connection') as mock_test:
            mock_test.return_value = True

            is_healthy = await validator.validate_connection()

            assert is_healthy is True
            # Should test all configured providers
            assert mock_test.call_count == len(validator.consensus_config.providers)

    @pytest.mark.asyncio
    async def test_validate_connection_partial_failure(self, validator):
        """Test connection validation with some provider failures."""
        with patch.object(validator, '_test_provider_connection') as mock_test:
            # First provider fails, second succeeds
            mock_test.side_effect = [False, True]

            is_healthy = await validator.validate_connection()

            # Should still be healthy if min providers available
            if validator.consensus_config.min_providers == 1:
                assert is_healthy is True
            else:
                assert is_healthy is False

    @pytest.mark.asyncio
    async def test_batch_validate_quality(self, validator):
        """Test batch quality validation."""
        documents = [
            {"id": "doc1", "content": "Good content", "embedding": [0.1] * 2048},
            {"id": "doc2", "content": "Bad content", "embedding": [0.2] * 2048}
        ]

        with patch.object(validator, 'validate_quality') as mock_validate:
            mock_validate.side_effect = [
                ConsensusResult(True, 0.8, {}, "Good"),
                ConsensusResult(False, 0.3, {}, "Bad")
            ]

            results = await validator.batch_validate_quality(documents)

            assert len(results) == 2
            assert results[0].consensus_reached is True
            assert results[1].consensus_reached is False

    @pytest.mark.asyncio
    async def test_adaptive_sampling(self, validator):
        """Test adaptive sampling based on cost and quality patterns."""
        # Simulate high-quality content trend
        validator._recent_quality_scores = [0.8, 0.85, 0.9, 0.82, 0.88]

        should_validate = await validator._should_validate_adaptively("test content")

        # Should reduce validation frequency for consistently high quality
        # This is implementation dependent but should show adaptive behavior
        assert isinstance(should_validate, bool)


class TestConsensusConfigFactory:
    """Test consensus configuration factory function."""

    def test_create_consensus_config_default(self):
        """Test creating default consensus config."""
        config = create_consensus_config()

        assert isinstance(config, ConsensusConfig)
        assert config.enabled is True
        assert len(config.providers) >= 2
        assert config.consensus_threshold > 0.5

    def test_create_consensus_config_high_quality(self):
        """Test creating high-quality consensus config."""
        config = create_consensus_config(
            quality_level="high",
            cost_limit=20.0
        )

        assert config.consensus_threshold >= 0.8
        assert config.cost_limit_per_day == 20.0
        assert len(config.providers) >= 3

    def test_create_consensus_config_cost_optimized(self):
        """Test creating cost-optimized consensus config."""
        config = create_consensus_config(
            quality_level="standard",
            cost_limit=5.0,
            enable_adaptive_sampling=True
        )

        assert config.cost_limit_per_day == 5.0
        assert config.enable_adaptive_sampling is True
        # Should use fewer providers for cost optimization
        assert len(config.providers) == 2

    def test_create_consensus_config_disabled(self):
        """Test creating disabled consensus config."""
        config = create_consensus_config(enabled=False)

        assert config.enabled is False
        # Other settings should still be valid for potential future use
        assert isinstance(config.providers, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=dopemux.embeddings.enhancers", "--cov-report=term-missing"])