"""
Unified Document Extraction System for Dopemux

Integrates ADHD-optimized patterns, markdown extraction, YAML parsing,
and multi-angle entity detection into a comprehensive pipeline.
"""

from .unified_extractor import UnifiedDocumentExtractor, ExtractionResult
from .pipeline_orchestrator import UnifiedDocumentPipeline, PipelineConfig

__all__ = [
    "UnifiedDocumentExtractor",
    "ExtractionResult",
    "UnifiedDocumentPipeline",
    "PipelineConfig"
]