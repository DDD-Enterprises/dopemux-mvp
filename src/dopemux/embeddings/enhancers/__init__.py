"""
Enhancement layers for embedding quality and validation.

Provides quality assurance layers including consensus validation,
outlier detection, and embedding quality metrics.
"""

from .base import BaseEnhancer
from .consensus import (
    ConsensusValidator,
    ConsensusConfig,
    ConsensusResult,
    ModelProvider,
    create_consensus_config
)

__all__ = [
    # Base abstractions
    "BaseEnhancer",

    # Consensus validation
    "ConsensusValidator",
    "ConsensusConfig",
    "ConsensusResult",
    "ModelProvider",
    "create_consensus_config"
]