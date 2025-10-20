"""
ADHD Engine Machine Learning Module

Pattern learning and predictive capabilities for personalized ADHD accommodations.

Components:
- pattern_learner.py: Extract and persist user patterns (energy, attention, breaks)
- predictive_engine.py: Predict future states based on learned patterns

IP-005 Days 11-12 implementation.
"""

from .pattern_learner import (
    EnergyPattern,
    AttentionPattern,
    BreakPattern,
    ADHDPatternLearner
)

from .predictive_engine import PredictiveADHDEngine

__all__ = [
    "EnergyPattern",
    "AttentionPattern",
    "BreakPattern",
    "ADHDPatternLearner",
    "PredictiveADHDEngine"
]
