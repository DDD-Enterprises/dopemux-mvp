"""
ConPort Knowledge Graph Query Interface
Part of CONPORT-KG-2025 (Decision #113)

ADHD-optimized 3-tier progressive disclosure query patterns.
"""

from .overview import OverviewQueries

# Phase 5 & 6 - Coming soon
# from .exploration import ExplorationQueries
# from .deep_context import DeepContextQueries

__all__ = [
    'OverviewQueries',
    # 'ExplorationQueries',  # Phase 5
    # 'DeepContextQueries'  # Phase 6
]
