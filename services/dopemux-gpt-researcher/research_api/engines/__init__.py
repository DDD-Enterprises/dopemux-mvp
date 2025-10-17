"""
Research Engines - Layer 1 Multi-Tool Orchestration

Core engines for intelligent research processing:
- Query Classification: Intent detection and strategy selection
- Prompt Enhancement: Query optimization for better results
- Search Orchestration: Multi-engine coordination
- Output Formatting: Adaptive result presentation

These engines form the foundation of the ADHD-optimized research system.
"""

from .query_classifier import (
    QueryClassificationEngine,
    QueryIntent,
    ResearchScope,
    OutputFormat,
    SearchEngineStrategy,
    ClassificationResult
)

__all__ = [
    "QueryClassificationEngine",
    "QueryIntent",
    "ResearchScope",
    "OutputFormat",
    "SearchEngineStrategy",
    "ClassificationResult"
]