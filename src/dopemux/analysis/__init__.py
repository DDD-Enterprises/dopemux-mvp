"""
Document analysis and processing package for Dopemux.

Provides comprehensive codebase analysis, semantic search, and knowledge extraction
optimized for ADHD-friendly development workflows.
"""

from .embedder import DocumentEmbedder
from .extractor import MultiAngleExtractor
from .processor import DocumentProcessor, ProcessingConfig

__all__ = [
    "DocumentProcessor",
    "ProcessingConfig",
    "DocumentEmbedder",
    "MultiAngleExtractor",
]
