"""
Document analysis and processing package for Dopemux.

Provides comprehensive codebase analysis, semantic search, and knowledge extraction
optimized for ADHD-friendly development workflows.
"""

from .processor import DocumentProcessor, ProcessingConfig
from .embedder import DocumentEmbedder
from .extractor import MultiAngleExtractor

__all__ = [
    "DocumentProcessor",
    "ProcessingConfig",
    "DocumentEmbedder",
    "MultiAngleExtractor"
]