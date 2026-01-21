"""
Batch Quality Scorer - Component 6 Phase 3 Week 3

Evaluates task batch quality for ADHD productivity optimization.

Quality Dimensions:
- Cohesion: How similar tasks are (0.0-1.0, target: > 0.7)
- Switch Cost: Total cognitive cost within batch (target: < 0.3)
- Duration Balance: Fits ADHD attention span (60-120 min optimal)
- Complexity Gradient: Smooth progression (target: variance < 0.3)
- Completion Likelihood: Predicted success rate (target: > 0.8)

Created: 2025-10-19
Component: 6 - Phase 3 Week 3
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from .task_batcher import TaskBatch
from .switch_cost_calculator import SwitchCostCalculator

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class BatchQuality:
    """Comprehensive batch quality assessment."""
    overall_score: float  # 0.0-1.0 combined quality
    cohesion: float  # Task similarity (target: > 0.7)
    switch_cost: float  # Cognitive switching cost (target: < 0.3)
    duration_balance: float  # Attention span fit (0.0-1.0)
    complexity_gradient: float  # Smooth progression (0.0-1.0)
    completion_likelihood: float  # Success prediction (target: > 0.8)
    meets_targets: bool  # All targets met?
    recommendations: List[str]  # Improvement suggestions


# ============================================================================
# Batch Quality Scorer
# ============================================================================

class BatchQualityScorer:
    """
    Evaluates task batch quality for ADHD productivity.

    ADHD Quality Targets:
    - Cohesion > 0.7 (high task similarity)
    - Switch Cost < 0.3 (low cognitive friction)
    - Duration: 60-120 min (optimal ADHD focus window)
    - Complexity Gradient: Smooth (variance < 0.3)
    - Completion Likelihood > 0.8 (high success rate)

    Performance: < 20ms per batch evaluation
    """

    # Quality target thresholds (ADHD-optimized)
    TARGETS = {
        "cohesion": 0.7,  # Minimum acceptable cohesion
        "switch_cost": 0.3,  # Maximum acceptable switch cost
        "duration_min": 60,  # Minimum batch duration (minutes)
        "duration_max": 120,  # Maximum batch duration
        "duration_optimal": 90,  # Optimal duration
        "complexity_variance_max": 0.3,  # Maximum complexity variance
        "completion_likelihood": 0.8  # Minimum success prediction
    }

    def __init__(self):
        """Initialize batch quality scorer."""
        self.switch_calculator = SwitchCostCalculator()
        self._scoring_count = 0
        self._average_quality = 0.0
        logger.info("BatchQualityScorer initialized")

    def score_batch(
        self,
        batch: TaskBatch,
        adhd_state: Optional[any] = None,
        flow_state: Optional[any] = None
    ) -> BatchQuality:
        """
        Comprehensive batch quality assessment.

        Args:
            batch: TaskBatch to evaluate
            adhd_state: Current ADHD state (for switch cost calculation)
            flow_state: Current flow state (for switch cost calculation)

        Returns:
            BatchQuality with scores and recommendations

        Performance: < 20ms target
        """
        # 1. Cohesion (from batch metadata)
        cohesion = batch.cohesion_score

        # 2. Switch Cost (calculate cumulative cognitive cost)
        switch_cost = self._calculate_batch_switch_cost(batch, adhd_state, flow_state)

        # 3. Duration Balance (how well duration fits ADHD attention span)
        duration_balance = self._score_duration_balance(batch.estimated_duration_minutes)

        # 4. Complexity Gradient (smoothness of complexity progression)
        complexity_gradient = self._score_complexity_gradient(batch)

        # 5. Completion Likelihood (from batch metadata or recalculate)
        completion_likelihood = batch.completion_likelihood

        # Overall score (weighted average)
        overall_score = (
            0.3 * cohesion +
            0.25 * (1.0 - switch_cost) +  # Invert (low cost = high score)
            0.2 * duration_balance +
            0.15 * complexity_gradient +
            0.1 * completion_likelihood
        )

        # Check if targets met
        meets_targets = self._check_targets(
            cohesion, switch_cost, batch.estimated_duration_minutes,
            complexity_gradient, completion_likelihood
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            batch, cohesion, switch_cost, batch.estimated_duration_minutes,
            complexity_gradient, completion_likelihood
        )

        # Track statistics
        self._scoring_count += 1
        self._average_quality = (
            0.9 * self._average_quality + 0.1 * overall_score
        ) if self._average_quality > 0 else overall_score

        logger.debug(
            f"Batch '{batch.batch_id}' scored: {overall_score:.2f} "
            f"(cohesion: {cohesion:.2f}, switch_cost: {switch_cost:.2f}, "
            f"targets_met: {meets_targets})"
        )

        return BatchQuality(
            overall_score=overall_score,
            cohesion=cohesion,
            switch_cost=switch_cost,
            duration_balance=duration_balance,
            complexity_gradient=complexity_gradient,
            completion_likelihood=completion_likelihood,
            meets_targets=meets_targets,
            recommendations=recommendations
        )

    def _calculate_batch_switch_cost(
        self,
        batch: TaskBatch,
        adhd_state: Optional[any],
        flow_state: Optional[any]
    ) -> float:
        """
        Calculate cumulative switch cost within batch.

        Returns: 0.0-1.0 average switch cost
        """
        if len(batch.tasks) <= 1:
            return 0.0  # No switches

        total_cost = 0.0
        switch_count = len(batch.tasks) - 1

        for i in range(switch_count):
            cost = self.switch_calculator.calculate_switch_cost(
                batch.tasks[i],
                batch.tasks[i + 1],
                adhd_state,
                flow_state
            )
            total_cost += cost.cost

        # Return average cost per switch
        return total_cost / switch_count

    def _score_duration_balance(self, duration_minutes: float) -> float:
        """
        Score how well duration fits ADHD attention span.

        Returns: 0.0-1.0 score (1.0 = optimal)
        """
        if duration_minutes < self.TARGETS["duration_min"]:
            # Too short
            return duration_minutes / self.TARGETS["duration_min"] * 0.7

        elif duration_minutes <= self.TARGETS["duration_optimal"]:
            # Optimal range
            return 1.0

        elif duration_minutes <= self.TARGETS["duration_max"]:
            # Acceptable but suboptimal
            excess = duration_minutes - self.TARGETS["duration_optimal"]
            max_excess = self.TARGETS["duration_max"] - self.TARGETS["duration_optimal"]
            return 1.0 - (excess / max_excess) * 0.3  # 0.7-1.0

        else:
            # Too long
            return max(0.0, 0.5 - (duration_minutes - self.TARGETS["duration_max"]) / 60.0)

    def _score_complexity_gradient(self, batch: TaskBatch) -> float:
        """
        Score smoothness of complexity progression.

        Returns: 0.0-1.0 score (1.0 = smooth)
        """
        if len(batch.tasks) <= 1:
            return 1.0  # No gradient to evaluate

        # Get complexity variance from metadata
        variance = batch.metadata.get("complexity_variance", 0.0)

        # Score based on variance (lower = better)
        if variance <= self.TARGETS["complexity_variance_max"]:
            return 1.0 - (variance / self.TARGETS["complexity_variance_max"]) * 0.3  # 0.7-1.0
        else:
            return max(0.0, 0.5 - (variance - self.TARGETS["complexity_variance_max"]))

    def _check_targets(
        self,
        cohesion: float,
        switch_cost: float,
        duration: float,
        gradient: float,
        completion: float
    ) -> bool:
        """Check if all ADHD quality targets are met."""
        return (
            cohesion >= self.TARGETS["cohesion"] and
            switch_cost <= self.TARGETS["switch_cost"] and
            self.TARGETS["duration_min"] <= duration <= self.TARGETS["duration_max"] and
            gradient >= 0.7 and  # Good gradient score
            completion >= self.TARGETS["completion_likelihood"]
        )

    def _generate_recommendations(
        self,
        batch: TaskBatch,
        cohesion: float,
        switch_cost: float,
        duration: float,
        gradient: float,
        completion: float
    ) -> List[str]:
        """Generate actionable recommendations for batch improvement."""
        recommendations = []

        # Cohesion recommendations
        if cohesion < self.TARGETS["cohesion"]:
            recommendations.append(
                f"Low cohesion ({cohesion:.2f} < {self.TARGETS['cohesion']}): "
                "Consider regrouping tasks by domain or technology"
            )

        # Switch cost recommendations
        if switch_cost > self.TARGETS["switch_cost"]:
            recommendations.append(
                f"High switch cost ({switch_cost:.2f} > {self.TARGETS['switch_cost']}): "
                "Reorder tasks to minimize context switches"
            )

        # Duration recommendations
        if duration < self.TARGETS["duration_min"]:
            recommendations.append(
                f"Batch too short ({duration:.0f} min < {self.TARGETS['duration_min']} min): "
                "Consider merging with another batch"
            )
        elif duration > self.TARGETS["duration_max"]:
            recommendations.append(
                f"Batch too long ({duration:.0f} min > {self.TARGETS['duration_max']} min): "
                "Consider splitting into smaller batches"
            )

        # Complexity recommendations
        if gradient < 0.7:
            recommendations.append(
                "Uneven complexity progression: Reorder for smoother gradient"
            )

        # Completion likelihood recommendations
        if completion < self.TARGETS["completion_likelihood"]:
            recommendations.append(
                f"Low completion likelihood ({completion:.2f} < {self.TARGETS['completion_likelihood']}): "
                "Simplify batch or reduce task count"
            )

        # Positive feedback if all targets met
        if not recommendations:
            recommendations.append("✅ Batch meets all ADHD quality targets - ready for execution!")

        return recommendations

    def get_statistics(self) -> Dict[str, any]:
        """Get batch scoring statistics."""
        return {
            "scoring_count": self._scoring_count,
            "average_quality": self._average_quality,
            "targets": self.TARGETS,
            "switch_calculator_stats": self.switch_calculator.get_statistics()
        }


# ============================================================================
# Helper Functions
# ============================================================================

def score_batch_quality(
    batch: TaskBatch,
    adhd_state: Optional[any] = None
) -> BatchQuality:
    """
    Convenience function for quick batch quality scoring.

    Args:
        batch: TaskBatch to evaluate
        adhd_state: Current ADHD state (optional)

    Returns:
        BatchQuality with scores and recommendations

    Example:
        quality = score_batch_quality(batch, current_adhd_state)
        if quality.meets_targets:
            logger.info("✅ High-quality batch ready for execution")
        else:
            for rec in quality.recommendations:
                logger.info(f"  - {rec}")
    """
    scorer = BatchQualityScorer()
    return scorer.score_batch(batch, adhd_state)
