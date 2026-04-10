"""Prescan library: Pre-extraction intelligence engine for the repo-truth-extractor.

Provides corpus analysis, duplicate detection, code intelligence, and multi-stage
Grok passes to prepare extraction payloads with comprehensive context awareness.
"""

from .engine import PrescanEngine
from .models import PrescanConfig, PrescanResult, FileEntry
from .grok_passes import GrokPassRunner
from .batch_planner import BatchPlanner
from ..intelligence_router import IntelligenceRouter

__all__ = [
    "PrescanEngine",
    "PrescanConfig",
    "PrescanResult",
    "FileEntry",
    "GrokPassRunner",
    "BatchPlanner",
    "IntelligenceRouter",
]
