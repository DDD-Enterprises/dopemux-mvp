"""
Feature Engineering - Week 4 (Contextual Bandit Features)

Extracts 14 features from ADHD state for ML training.
Created: 2025-10-20
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """Extracted features for ML."""
    features: Dict[str, float]
    feature_names: List[str]
    feature_values: List[float]
    raw_data: Dict[str, Any]
    extracted_at: datetime


class FeatureExtractor:
    """Extract ADHD state features for contextual bandits."""

    def __init__(self, version: str = "v1"):
        self.version = version
        self.energy_levels = ["very_low", "low", "medium", "high", "hyperfocus"]
        self.attention_levels = ["scattered", "transitioning", "focused", "hyperfocused"]
        self.priority_levels = ["low", "medium", "high", "urgent"]
        logger.info(f"FeatureExtractor v{version} initialized")

    def extract_features(self, task: Any, adhd_state: Dict[str, Any]) -> FeatureVector:
        """Extract 14 features from task and ADHD state."""
        features = {
            "task_complexity": getattr(task, "complexity", 0.5),
            "task_priority": self._encode_ordinal(getattr(task, "priority", "medium"), self.priority_levels),
            "energy_level": self._encode_ordinal(adhd_state.get("energy_level", "medium"), self.energy_levels),
            "attention_level": self._encode_ordinal(adhd_state.get("attention_level", "focused"), self.attention_levels),
            "cognitive_load": adhd_state.get("cognitive_load", 0.5),
        }
        
        feature_names = sorted(features.keys())
        feature_values = [features[n] for n in feature_names]
        
        return FeatureVector(
            features=features,
            feature_names=feature_names,
            feature_values=feature_values,
            raw_data={"task": task, "adhd_state": adhd_state},
            extracted_at=datetime.now()
        )

    def _encode_ordinal(self, value: str, levels: List[str]) -> float:
        """Encode ordinal to [0, 1]."""
        if value not in levels:
            return 0.5
        return levels.index(value) / max(len(levels) - 1, 1)
