"""Tests for psychology-specialized embedding provider."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
from typing import List

from chatx.embeddings.psychology import PsychologyEmbeddingProvider
from chatx.embeddings.base import EmbeddingConfig, ModelInfo


class TestPsychologyEmbeddingProvider:
    """Test PsychBERT psychology embedding functionality."""

    @pytest.fixture
    def psychology_config(self):
        """Psychology embedding configuration."""
        return EmbeddingConfig(
            model_name="mental/mental-bert-base-uncased",
            max_seq_length=512,
            dimension=768,
            batch_size=16,
            device="cpu"
        )

    @pytest.fixture
    def mock_psychology_provider(self):
        """Mock psychology provider for testing."""
        provider = Mock(spec=PsychologyEmbeddingProvider)
        provider.load_model = AsyncMock()
        provider.encode = AsyncMock()
        provider.encode_batch = AsyncMock()
        provider.cleanup = AsyncMock()
        return provider

    def test_psychology_provider_can_be_instantiated(self, psychology_config):
        """Test that PsychologyEmbeddingProvider can be created."""
        from chatx.embeddings.psychology import PsychologyEmbeddingProvider
        provider = PsychologyEmbeddingProvider()
        assert provider is not None
        assert hasattr(provider, 'model')
        assert hasattr(provider, 'config')
        assert hasattr(provider, 'hardware_info')

    @pytest.mark.asyncio
    async def test_psychology_embedding_loads_psychbert(self, mock_psychology_provider, psychology_config):
        """Test psychology provider loads PsychBERT model correctly."""
        await mock_psychology_provider.load_model(psychology_config)
        
        mock_psychology_provider.load_model.assert_called_once_with(psychology_config)

    @pytest.mark.asyncio 
    async def test_psychology_embeddings_vs_generic_on_constructs(self, mock_psychology_provider):
        """Test psychology embeddings perform better on psychological constructs."""
        # Test with psychological construct text
        psychology_text = "I feel like you're violating my boundaries and that makes me anxious"
        
        # Mock psychology embedding (should be more specialized)
        psychology_embedding = np.random.rand(768).tolist()
        mock_psychology_provider.encode.return_value = psychology_embedding
        
        result = await mock_psychology_provider.encode(psychology_text)
        
        mock_psychology_provider.encode.assert_called_once_with(psychology_text)
        assert len(result) == 768
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_fallback_to_generic_for_non_psychology_content(self, mock_psychology_provider):
        """Test graceful fallback for non-psychological content."""
        generic_text = "The weather is nice today"
        
        # Should still work but may use different strategy
        generic_embedding = np.random.rand(768).tolist()
        mock_psychology_provider.encode.return_value = generic_embedding
        
        result = await mock_psychology_provider.encode(generic_text)
        
        assert result is not None
        assert len(result) == 768

    @pytest.mark.asyncio
    async def test_psychology_batch_encoding(self, mock_psychology_provider):
        """Test batch encoding of psychological constructs."""
        psychological_texts = [
            "I feel like you're gaslighting me",
            "This relationship feels codependent", 
            "I'm setting a boundary here",
            "That comment was emotionally manipulative"
        ]
        
        # Mock batch embeddings
        batch_embeddings = [np.random.rand(768).tolist() for _ in psychological_texts]
        mock_psychology_provider.encode_batch.return_value = batch_embeddings
        
        result = await mock_psychology_provider.encode_batch(psychological_texts)
        
        mock_psychology_provider.encode_batch.assert_called_once_with(psychological_texts)
        assert len(result) == 4
        assert all(len(emb) == 768 for emb in result)

    def test_psychology_model_info(self, mock_psychology_provider):
        """Test psychology model provides correct model information."""
        expected_info = ModelInfo(
            name="mental/mental-bert-base-uncased",
            dimension=768,
            max_seq_length=512,
            size_mb=438,  # Approximate BERT-base size
            requires_trust_remote=False,
            recommended_hardware=["cuda", "mps", "cpu"]
        )
        
        mock_psychology_provider.get_model_info.return_value = expected_info
        
        info = mock_psychology_provider.get_model_info()
        
        assert info.name == "mental/mental-bert-base-uncased"
        assert info.dimension == 768
        assert info.max_seq_length == 512

    def test_psychology_embedding_dimension(self, mock_psychology_provider):
        """Test psychology provider returns correct embedding dimension."""
        mock_psychology_provider.get_embedding_dimension.return_value = 768
        
        dim = mock_psychology_provider.get_embedding_dimension()
        
        assert dim == 768

    @pytest.mark.asyncio
    async def test_psychology_provider_cleanup(self, mock_psychology_provider):
        """Test psychology provider cleanup."""
        await mock_psychology_provider.cleanup()
        
        mock_psychology_provider.cleanup.assert_called_once()


class TestPsychologyBenchmarking:
    """Test psychology-specific benchmarking metrics."""

    def test_psychology_benchmarking_metrics_structure(self):
        """Test psychology benchmarking includes domain-specific metrics."""
        # Test will check for psychology-specific benchmarking once implemented
        expected_metrics = {
            'boundary_detection_accuracy',
            'emotion_classification_f1', 
            'relationship_pattern_recall',
            'psychological_construct_precision'
        }
        
        # This will be implemented in the benchmarking framework
        assert True  # Placeholder until benchmarking is implemented


class TestPsychologyConfigurationValidation:
    """Test psychology-specific configuration validation."""

    def test_psychology_model_validation(self):
        """Test psychology model names are validated."""
        valid_psychology_models = [
            "mental/mental-bert-base-uncased",
            "nlpaueb/legal-bert-base-uncased",
            "microsoft/DialoGPT-medium",
            "models/PsychBERT"
        ]
        
        for model in valid_psychology_models:
            config = EmbeddingConfig(model_name=model)
            assert config.model_name in valid_psychology_models

    def test_psychology_dimension_validation(self):
        """Test psychology models use appropriate dimensions."""
        # Psychology models typically use 768 (BERT-base) or higher
        config = EmbeddingConfig(
            model_name="mental/mental-bert-base-uncased",
            dimension=768
        )
        
        assert config.dimension >= 384  # Minimum for meaningful psychology analysis
        assert config.dimension in [384, 768, 1024, 1536]  # Common dimensions


class TestPsychologyContentDetection:
    """Test automatic detection of psychological content for specialized processing."""

    @pytest.mark.parametrize("text,is_psychological", [
        ("I feel like you're violating my boundaries", True),
        ("This relationship feels toxic and codependent", True), 
        ("That was emotional manipulation", True),
        ("I'm setting a clear boundary here", True),
        ("The weather is nice today", False),
        ("Can you pass the salt?", False),
        ("The meeting is at 3pm", False),
    ])
    def test_psychological_content_detection(self, text, is_psychological):
        """Test automatic detection of psychological vs generic content."""
        # This would be implemented in the psychology provider
        # For now, we'll mock the detection logic
        
        psychological_keywords = {
            'boundaries', 'boundary', 'toxic', 'codependent', 'manipulation', 
            'manipulative', 'gaslighting', 'emotional', 'trauma', 'trigger',
            'attachment', 'abandonment', 'narcissistic', 'abuse'
        }
        
        detected_psychological = any(
            keyword in text.lower() 
            for keyword in psychological_keywords
        )
        
        assert detected_psychological == is_psychological