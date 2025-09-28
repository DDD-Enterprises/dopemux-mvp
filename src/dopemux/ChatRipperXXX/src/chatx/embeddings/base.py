"""Base embedding provider interface and data classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EmbeddingConfig:
    """Configuration for embedding models."""
    
    model_name: str = "all-MiniLM-L6-v2"
    max_seq_length: int = 512
    dimension: int = 384
    batch_size: int = 32
    device: str = "auto"
    trust_remote_code: bool = False
    cache_folder: Optional[str] = None


@dataclass
class ModelInfo:
    """Information about an embedding model."""
    
    name: str
    dimension: int
    max_seq_length: int
    size_mb: int
    requires_trust_remote: bool
    recommended_hardware: List[str] = field(default_factory=list)


@dataclass
class HardwareInfo:
    """Information about available hardware."""
    
    has_cuda: bool
    has_mps: bool
    memory_gb: float
    cpu_cores: int
    recommended_device: str


@dataclass
class EmbeddingMetrics:
    """Performance metrics for embedding operations."""
    
    texts_processed: int
    total_time_seconds: float
    average_time_per_text: float
    peak_memory_mb: float
    device_used: str


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    async def load_model(self, config: EmbeddingConfig) -> None:
        """Load the embedding model with given configuration.
        
        Args:
            config: Configuration for the embedding model
            
        Raises:
            RuntimeError: If model loading fails
        """
        pass
    
    @abstractmethod
    async def encode(self, text: str) -> List[float]:
        """Encode a single text into an embedding vector.
        
        Args:
            text: Text to encode
            
        Returns:
            List of floats representing the embedding
            
        Raises:
            RuntimeError: If encoding fails
        """
        pass
    
    @abstractmethod
    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into embedding vectors.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List of embedding vectors
            
        Raises:
            RuntimeError: If batch encoding fails
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Get information about the currently loaded model.
        
        Returns:
            ModelInfo with model specifications
            
        Raises:
            RuntimeError: If no model is loaded
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension as integer
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources and unload model."""
        pass