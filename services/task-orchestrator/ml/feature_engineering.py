"""
Feature Engineering for ADHD-Aware ML Models

Transforms ADHD state and task attributes into numerical feature vectors
for machine learning models (contextual bandits, completion prediction).

Created: 2025-10-20
Component: 6 - Phase 2 Week 4 (ML Infrastructure)
Purpose: Convert raw context into ML-ready features

Key Features:
1. ADHD state encoding (energy, attention, cognitive load)
2. Temporal feature extraction (hour, day, patterns)
3. Task attribute normalization (complexity, duration, priority)
4. Derived features (interaction terms, temporal cycles)
5. Feature scaling and normalization
6. Feature importance tracking
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass, field


@dataclass
class FeatureVector:
    """
    Complete feature vector for ML model input.

    Attributes:
        features: Numerical feature array (ready for ML)
        feature_names: Names of each feature (for interpretability)
        raw_context: Original context before transformation
        metadata: Additional context (for debugging)
    """
    features: np.ndarray
    feature_names: List[str]
    raw_context: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, float]:
        """Return features as named dictionary."""
        return dict(zip(self.feature_names, self.features))


class FeatureEngineer:
    """
    Feature engineering for ADHD-aware task recommendation.

    Transforms RecommendationContext into numerical feature vectors
    suitable for ML models (contextual bandits, gradient boosting).

    Feature Categories:
    1. ADHD State (8 features): energy, attention, cognitive load
    2. Temporal (6 features): hour, day, week position, circadian
    3. Task Attributes (7 features): complexity, duration, priority, dependencies
    4. Historical (4 features): velocity, completion rate, patterns
    5. Derived (5 features): interactions, temporal patterns

    Total: 30 features

    Usage:
        engineer = FeatureEngineer()

        # Transform context to features
        feature_vector = engineer.extract_features(
            recommendation_context=context,
            task=candidate_task
        )

        # Use in ML model
        features = feature_vector.features  # numpy array
        prediction = model.predict(features.reshape(1, -1))
    """

    # Energy level encoding (one-hot)
    ENERGY_LEVELS = ["very_low", "low", "medium", "high", "hyperfocus"]

    # Attention level encoding (one-hot)
    ATTENTION_LEVELS = ["scattered", "transitioning", "focused", "hyperfocused"]

    # Priority encoding
    PRIORITY_MAP = {"low": 0.3, "medium": 0.6, "high": 1.0}

    def __init__(self):
        """Initialize feature engineer."""
        self.feature_count = 30  # Total features extracted
        self._feature_names = self._generate_feature_names()

    def extract_features(
        self,
        recommendation_context: Any,  # RecommendationContext
        task: Any  # Task object
    ) -> FeatureVector:
        """
        Extract complete feature vector from context and task.

        Args:
            recommendation_context: Current ADHD/temporal state
            task: Candidate task to evaluate

        Returns:
            FeatureVector with 30 numerical features

        Performance Target: < 10ms for feature extraction
        """
        features = []

        # 1. ADHD State Features (8 features)
        adhd_features = self._extract_adhd_features(recommendation_context)
        features.extend(adhd_features)

        # 2. Temporal Features (6 features)
        temporal_features = self._extract_temporal_features(recommendation_context)
        features.extend(temporal_features)

        # 3. Task Attribute Features (7 features)
        task_features = self._extract_task_features(task)
        features.extend(task_features)

        # 4. Historical Features (4 features)
        historical_features = self._extract_historical_features(recommendation_context)
        features.extend(historical_features)

        # 5. Derived Features (5 features)
        derived_features = self._extract_derived_features(
            recommendation_context, task
        )
        features.extend(derived_features)

        # Convert to numpy array
        feature_array = np.array(features, dtype=np.float32)

        # Validate feature count
        if len(feature_array) != self.feature_count:
            raise ValueError(
                f"Feature count mismatch: expected {self.feature_count}, "
                f"got {len(feature_array)}"
            )

        return FeatureVector(
            features=feature_array,
            feature_names=self._feature_names,
            raw_context={
                "energy": recommendation_context.energy_level,
                "attention": recommendation_context.attention_level,
                "cognitive_load": recommendation_context.cognitive_load,
                "task_id": getattr(task, 'task_id', 'unknown'),
                "task_complexity": getattr(task, 'complexity', 0.5)
            },
            metadata={
                "extracted_at": datetime.now(),
                "feature_version": "1.0"
            }
        )

    def _extract_adhd_features(self, context: Any) -> List[float]:
        """
        Extract ADHD state features (8 features).

        Features:
        1. energy_very_low (0/1)
        2. energy_low (0/1)
        3. energy_medium (0/1)
        4. energy_high (0/1)
        5. energy_hyperfocus (0/1)
        6. attention_scattered (0/1)
        7. attention_focused (0/1)
        8. cognitive_load (0.0-1.0)
        """
        features = []

        # One-hot encode energy level (5 features)
        energy = context.energy_level
        for level in self.ENERGY_LEVELS:
            features.append(1.0 if energy == level else 0.0)

        # Simplified attention encoding (2 features: scattered vs focused)
        attention = context.attention_level
        features.append(1.0 if attention in ["scattered", "transitioning"] else 0.0)
        features.append(1.0 if attention in ["focused", "hyperfocused"] else 0.0)

        # Cognitive load (1 feature)
        features.append(float(context.cognitive_load))

        return features

    def _extract_temporal_features(self, context: Any) -> List[float]:
        """
        Extract temporal features (6 features).

        Features:
        1. hour_sin (cyclic encoding)
        2. hour_cos (cyclic encoding)
        3. day_sin (cyclic encoding)
        4. day_cos (cyclic encoding)
        5. is_morning (0/1)
        6. context_switches_normalized (0.0-1.0)
        """
        features = []

        # Cyclic encoding for hour (24-hour cycle)
        hour = context.time_of_day
        hour_radians = 2 * np.pi * hour / 24
        features.append(np.sin(hour_radians))
        features.append(np.cos(hour_radians))

        # Cyclic encoding for day of week (7-day cycle)
        day = context.day_of_week
        day_radians = 2 * np.pi * day / 7
        features.append(np.sin(day_radians))
        features.append(np.cos(day_radians))

        # Is morning (6am-12pm) - peak ADHD productivity window
        features.append(1.0 if 6 <= hour < 12 else 0.0)

        # Context switches today (normalized to 0-1, max 10)
        switches = min(context.context_switches_today, 10)
        features.append(switches / 10.0)

        return features

    def _extract_task_features(self, task: Any) -> List[float]:
        """
        Extract task attribute features (7 features).

        Features:
        1. complexity (0.0-1.0)
        2. estimated_duration_normalized (0.0-1.0, max 240 min)
        3. priority_low (0/1)
        4. priority_medium (0/1)
        5. priority_high (0/1)
        6. has_dependencies (0/1)
        7. dependency_count_normalized (0.0-1.0, max 5)
        """
        features = []

        # Complexity (already 0-1)
        complexity = getattr(task, 'complexity', 0.5)
        features.append(float(complexity))

        # Duration (normalized to 0-1, assuming max 240 min = 4 hours)
        duration = getattr(task, 'estimated_duration', 60)
        features.append(min(duration / 240.0, 1.0))

        # Priority (one-hot encoding)
        priority = getattr(task, 'priority', 'medium')
        features.append(1.0 if priority == 'low' else 0.0)
        features.append(1.0 if priority == 'medium' else 0.0)
        features.append(1.0 if priority == 'high' else 0.0)

        # Dependencies
        dependencies = getattr(task, 'dependencies', [])
        features.append(1.0 if dependencies else 0.0)
        features.append(min(len(dependencies) / 5.0, 1.0))

        return features

    def _extract_historical_features(self, context: Any) -> List[float]:
        """
        Extract historical pattern features (4 features).

        Features:
        1. tasks_completed_today_normalized (0.0-1.0, max 10)
        2. average_velocity (0.0-1.0, max 8 tasks/day)
        3. preferred_complexity_min (0.0-1.0)
        4. preferred_complexity_max (0.0-1.0)
        """
        features = []

        # Tasks completed today
        completed = min(context.tasks_completed_today, 10)
        features.append(completed / 10.0)

        # Average velocity (tasks per day)
        velocity = min(context.average_velocity, 8.0)
        features.append(velocity / 8.0)

        # Preferred complexity range
        min_complexity, max_complexity = context.preferred_complexity_range
        features.append(float(min_complexity))
        features.append(float(max_complexity))

        return features

    def _extract_derived_features(
        self,
        context: Any,
        task: Any
    ) -> List[float]:
        """
        Extract derived/interaction features (5 features).

        Features:
        1. energy_complexity_match (0.0-1.0)
        2. cognitive_capacity_available (0.0-1.0)
        3. is_optimal_time_for_complexity (0/1)
        4. fatigue_factor (0.0-1.0)
        5. urgency_pressure (0.0-1.0)
        """
        features = []

        # Energy-complexity match (how well task matches energy)
        task_complexity = getattr(task, 'complexity', 0.5)
        energy = context.energy_level

        # Energy to ideal complexity mapping
        energy_ideal_map = {
            "very_low": 0.1,
            "low": 0.3,
            "medium": 0.5,
            "high": 0.7,
            "hyperfocus": 0.9
        }
        ideal_complexity = energy_ideal_map.get(energy, 0.5)

        # Match score (1.0 = perfect match, 0.0 = complete mismatch)
        complexity_diff = abs(task_complexity - ideal_complexity)
        match_score = 1.0 - complexity_diff
        features.append(match_score)

        # Cognitive capacity available (1.0 - cognitive_load)
        features.append(1.0 - context.cognitive_load)

        # Is optimal time for this complexity?
        # Morning (6-12) = high complexity, Afternoon (12-18) = medium, Evening (18-24) = low
        hour = context.time_of_day
        if 6 <= hour < 12 and task_complexity > 0.6:
            optimal = 1.0
        elif 12 <= hour < 18 and 0.3 <= task_complexity <= 0.7:
            optimal = 1.0
        elif 18 <= hour < 24 and task_complexity < 0.4:
            optimal = 1.0
        else:
            optimal = 0.0
        features.append(optimal)

        # Fatigue factor (based on switches and time)
        switches_penalty = min(context.context_switches_today / 10.0, 1.0)
        # Evening penalty (after 6pm)
        evening_penalty = 0.5 if hour >= 18 else 0.0
        fatigue = min(switches_penalty + evening_penalty, 1.0)
        features.append(fatigue)

        # Urgency pressure (high priority + few tasks completed)
        priority = getattr(task, 'priority', 'medium')
        priority_score = self.PRIORITY_MAP.get(priority, 0.6)

        # More urgent if few tasks completed today
        completion_penalty = 1.0 - min(context.tasks_completed_today / 5.0, 1.0)

        urgency = (priority_score + completion_penalty) / 2.0
        features.append(urgency)

        return features

    def _generate_feature_names(self) -> List[str]:
        """Generate human-readable feature names."""
        names = []

        # ADHD features (8)
        names.extend([
            "energy_very_low", "energy_low", "energy_medium",
            "energy_high", "energy_hyperfocus",
            "attention_scattered", "attention_focused",
            "cognitive_load"
        ])

        # Temporal features (6)
        names.extend([
            "hour_sin", "hour_cos",
            "day_sin", "day_cos",
            "is_morning",
            "context_switches_norm"
        ])

        # Task features (7)
        names.extend([
            "complexity",
            "duration_norm",
            "priority_low", "priority_medium", "priority_high",
            "has_dependencies", "dependency_count_norm"
        ])

        # Historical features (4)
        names.extend([
            "tasks_completed_norm",
            "average_velocity_norm",
            "preferred_complexity_min",
            "preferred_complexity_max"
        ])

        # Derived features (5)
        names.extend([
            "energy_complexity_match",
            "cognitive_capacity",
            "is_optimal_time",
            "fatigue_factor",
            "urgency_pressure"
        ])

        return names

    def get_feature_importance_template(self) -> Dict[str, str]:
        """
        Get template explaining what each feature represents.

        Useful for SHAP explainability and model interpretation.
        """
        return {
            "energy_*": "User's current energy level (one-hot encoded)",
            "attention_*": "User's attention state (scattered vs focused)",
            "cognitive_load": "Current mental load (0=low, 1=overwhelmed)",
            "hour_sin/cos": "Time of day (cyclic encoding for 24h pattern)",
            "day_sin/cos": "Day of week (cyclic encoding for weekly pattern)",
            "is_morning": "Peak ADHD productivity window (6am-12pm)",
            "context_switches_norm": "Mental switching penalty today",
            "complexity": "Task cognitive complexity (0=trivial, 1=hard)",
            "duration_norm": "Estimated time to complete (normalized)",
            "priority_*": "Task urgency level (one-hot encoded)",
            "has_dependencies": "Task blocked by other tasks",
            "dependency_count_norm": "Number of blocking dependencies",
            "tasks_completed_norm": "Progress made today",
            "average_velocity_norm": "Typical daily task completion rate",
            "preferred_complexity_*": "User's historical complexity sweet spot",
            "energy_complexity_match": "How well task matches current energy",
            "cognitive_capacity": "Available mental bandwidth (1-load)",
            "is_optimal_time": "Best time of day for this task type",
            "fatigue_factor": "Accumulated mental fatigue (switches + time)",
            "urgency_pressure": "Combined priority + deadline pressure"
        }


# Convenience function
def extract_features_from_context(
    recommendation_context: Any,
    task: Any
) -> FeatureVector:
    """
    Convenience function for feature extraction.

    Args:
        recommendation_context: RecommendationContext with ADHD state
        task: Candidate task to evaluate

    Returns:
        FeatureVector ready for ML model input

    Example:
        features = extract_features_from_context(context, task)
        model_input = features.features  # numpy array
    """
    engineer = FeatureEngineer()
    return engineer.extract_features(recommendation_context, task)
