"""
Pipeline orchestration modules for embedding workflows.

Provides end-to-end pipeline orchestrators that coordinate document
ingestion, embedding generation, storage, and integration workflows.
"""

from .base import BasePipeline, PipelineResult, PipelineStage
from .document_pipeline import DocumentPipeline
from .search_pipeline import SearchPipeline
from .sync_pipeline import SyncPipeline

__all__ = [
    # Base abstractions
    "BasePipeline",
    "PipelineResult",
    "PipelineStage",

    # Pipeline implementations
    "DocumentPipeline",
    "SearchPipeline",
    "SyncPipeline"
]
