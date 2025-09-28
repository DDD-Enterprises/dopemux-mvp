"""Tests for BaseEmbeddingProvider abstract interface."""

import pytest
from abc import ABC
from typing import List
from unittest.mock import Mock, AsyncMock

from chatx.embeddings.base import (
    BaseEmbeddingProvider,
    EmbeddingConfig,
    EmbeddingMetrics,
    HardwareInfo,
    ModelInfo
)


class TestEmbeddingConfig:
    """Test EmbeddingConfig data class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = EmbeddingConfig()
        
        assert config.model_name == "all-MiniLM-L6-v2"
        assert config.max_seq_length == 512
        assert config.dimension == 384
        assert config.batch_size == 32
        assert config.device == "auto"
        assert config.trust_remote_code is False
        assert config.cache_folder is None
        
    def test_custom_config(self):
        """Test custom configuration values."""
        config = EmbeddingConfig(
            model_name="stella-1.5b-v5",
            max_seq_length=8192,
            dimension=1024,
            batch_size=16,
            device="cuda",
            trust_remote_code=True,
            cache_folder="./models"
        )
        
        assert config.model_name == "stella-1.5b-v5"
        assert config.max_seq_length == 8192
        assert config.dimension == 1024
        assert config.batch_size == 16
        assert config.device == "cuda"
        assert config.trust_remote_code is True
        assert config.cache_folder == "./models"


class TestModelInfo:
    """Test ModelInfo data class."""
    
    def test_model_info_creation(self):
        """Test ModelInfo with realistic values."""
        info = ModelInfo(
            name="stella-1.5b-v5",
            dimension=1024,
            max_seq_length=8192,
            size_mb=2800,
            requires_trust_remote=True,
            recommended_hardware=["cuda", "mps"]
        )
        
        assert info.name == "stella-1.5b-v5"
        assert info.dimension == 1024
        assert info.max_seq_length == 8192
        assert info.size_mb == 2800
        assert info.requires_trust_remote is True
        assert "cuda" in info.recommended_hardware
        assert "mps" in info.recommended_hardware


class TestHardwareInfo:
    """Test HardwareInfo data class."""
    
    def test_hardware_info(self):
        """Test HardwareInfo detection results."""
        info = HardwareInfo(
            has_cuda=False,
            has_mps=True,
            memory_gb=16.0,
            cpu_cores=8,
            recommended_device="mps"
        )
        
        assert info.has_cuda is False
        assert info.has_mps is True
        assert info.memory_gb == 16.0
        assert info.cpu_cores == 8
        assert info.recommended_device == "mps"


class TestEmbeddingMetrics:
    """Test EmbeddingMetrics data class."""
    
    def test_metrics_creation(self):
        """Test metrics with performance data."""
        metrics = EmbeddingMetrics(
            texts_processed=1000,
            total_time_seconds=45.2,
            average_time_per_text=0.0452,
            peak_memory_mb=2100.5,
            device_used="mps"
        )
        
        assert metrics.texts_processed == 1000
        assert metrics.total_time_seconds == 45.2
        assert metrics.average_time_per_text == 0.0452
        assert metrics.peak_memory_mb == 2100.5
        assert metrics.device_used == "mps"


class TestBaseEmbeddingProvider:
    """Test BaseEmbeddingProvider abstract interface."""
    
    def test_is_abstract(self):
        """Test that BaseEmbeddingProvider cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseEmbeddingProvider()
    
    def test_abstract_methods_exist(self):
        """Test that all required abstract methods are defined."""
        abstract_methods = BaseEmbeddingProvider.__abstractmethods__
        
        expected_methods = {
            "load_model",
            "encode",
            "encode_batch", 
            "get_model_info",
            "get_embedding_dimension",
            "cleanup"
        }
        
        assert expected_methods == abstract_methods
    
    def test_concrete_implementation_requires_all_methods(self):
        """Test that concrete implementation must implement all abstract methods."""
        
        # Missing one abstract method should fail
        class IncompleteProvider(BaseEmbeddingProvider):
            async def load_model(self, config: EmbeddingConfig) -> None:
                pass
            
            async def encode(self, text: str) -> List[float]:
                return [0.1, 0.2, 0.3]
            
            # Missing encode_batch, get_model_info, get_embedding_dimension, cleanup
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteProvider()
    
    def test_complete_implementation_works(self):
        """Test that complete implementation can be instantiated."""
        
        class CompleteProvider(BaseEmbeddingProvider):
            async def load_model(self, config: EmbeddingConfig) -> None:
                pass
            
            async def encode(self, text: str) -> List[float]:
                return [0.1, 0.2, 0.3]
            
            async def encode_batch(self, texts: List[str]) -> List[List[float]]:
                return [[0.1, 0.2, 0.3] for _ in texts]
            
            def get_model_info(self) -> ModelInfo:
                return ModelInfo(
                    name="test-model",
                    dimension=384,
                    max_seq_length=512,
                    size_mb=100,
                    requires_trust_remote=False,
                    recommended_hardware=["cpu"]
                )
            
            def get_embedding_dimension(self) -> int:
                return 384
            
            async def cleanup(self) -> None:
                pass
        
        # Should not raise an exception
        provider = CompleteProvider()
        assert provider is not None
        assert isinstance(provider, BaseEmbeddingProvider)


class TestProviderLifecycle:
    """Test provider lifecycle methods."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider for testing."""
        provider = Mock(spec=BaseEmbeddingProvider)
        provider.load_model = AsyncMock()
        provider.encode = AsyncMock(return_value=[0.1, 0.2, 0.3])
        provider.encode_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        provider.cleanup = AsyncMock()
        return provider
    
    @pytest.mark.asyncio
    async def test_load_model_called_with_config(self, mock_provider):
        """Test load_model is called with proper config."""
        config = EmbeddingConfig(model_name="test-model")
        
        await mock_provider.load_model(config)
        
        mock_provider.load_model.assert_called_once_with(config)
    
    @pytest.mark.asyncio
    async def test_encode_single_text(self, mock_provider):
        """Test encoding single text."""
        text = "This is a test message."
        
        result = await mock_provider.encode(text)
        
        mock_provider.encode.assert_called_once_with(text)
        assert result == [0.1, 0.2, 0.3]
    
    @pytest.mark.asyncio
    async def test_encode_batch(self, mock_provider):
        """Test batch encoding."""
        texts = ["First message", "Second message"]
        
        result = await mock_provider.encode_batch(texts)
        
        mock_provider.encode_batch.assert_called_once_with(texts)
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]
    
    @pytest.mark.asyncio
    async def test_cleanup_called(self, mock_provider):
        """Test cleanup is properly called."""
        await mock_provider.cleanup()
        
        mock_provider.cleanup.assert_called_once()