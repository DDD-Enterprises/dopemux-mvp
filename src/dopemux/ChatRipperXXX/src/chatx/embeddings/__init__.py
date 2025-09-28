"""Embedding provider abstractions and implementations."""

from .base import (
    BaseEmbeddingProvider,
    EmbeddingConfig,
    EmbeddingMetrics,
    HardwareInfo,
    ModelInfo
)

try:
    from .psychology import PsychologyEmbeddingProvider
    PSYCHOLOGY_AVAILABLE = True
except ImportError:
    PSYCHOLOGY_AVAILABLE = False

__all__ = [
    "BaseEmbeddingProvider",
    "EmbeddingConfig", 
    "EmbeddingMetrics",
    "HardwareInfo",
    "ModelInfo"
]

if PSYCHOLOGY_AVAILABLE:
    __all__.append("PsychologyEmbeddingProvider")