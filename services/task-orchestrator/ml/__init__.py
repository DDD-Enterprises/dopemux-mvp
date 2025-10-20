"""
Machine Learning components for ADHD Intelligence Layer.

This module contains ML models, feature engineering, and learning algorithms
for Phase 2 of Component 6 (ADHD Intelligence).

Timeline:
- Week 3: Rule-based foundation (complete)
- Week 4: Feature engineering + contextual bandits (current)
- Week 5: Hybrid ML deployment + SHAP explainability

Zen Consensus Validated:
- Contextual bandits (Thompson Sampling, UCB) for safe exploration
- Calibration (Platt/Isotonic) for probability estimates
- SHAP for explainability and trust building
"""

__version__ = "0.1.0-week4"
__all__ = ["FeatureExtractor", "ThompsonSamplingBandit", "UCBBandit"]

# Week 4 exports (when implemented)
try:
    from .feature_engineering import FeatureExtractor
except ImportError:
    FeatureExtractor = None

try:
    from .contextual_bandit import ThompsonSamplingBandit, UCBBandit
except ImportError:
    ThompsonSamplingBandit = None
    UCBBandit = None
