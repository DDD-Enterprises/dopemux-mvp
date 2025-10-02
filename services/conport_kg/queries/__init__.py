"""
ConPort Knowledge Graph Query Interface
Part of CONPORT-KG-2025 (Decision #113, #117)

ADHD-optimized 3-tier progressive disclosure query patterns.

Tier 1 (Overview): Top-3 pattern, <50ms target
Tier 2 (Exploration): Progressive disclosure, <150ms target
Tier 3 (Deep Context): No limits, <500ms target

All tiers use AGEClient with connection pooling for performance.
"""

from .overview import OverviewQueries
from .exploration import ExplorationQueries
from .deep_context import DeepContextQueries

__all__ = [
    'OverviewQueries',
    'ExplorationQueries',
    'DeepContextQueries'
]
