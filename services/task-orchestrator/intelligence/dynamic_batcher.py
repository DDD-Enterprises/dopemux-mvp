"""
Dynamic Batcher - Component 6 Phase 3 Week 3

Adaptive batch re-optimization based on real-time task completion performance.

Triggers for Re-Batching:
- Task completion (adjust remaining batch)
- Energy/attention drop (simplify remaining tasks)
- Cognitive load spike (reduce batch complexity)
- Deadline urgency (promote urgent task)
- Flow state change (adapt to new state)

Created: 2025-10-19
Component: 6 - Phase 3 Week 3
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .task_batcher import TaskBatch, TaskBatcher
from .batch_scorer import BatchQualityScorer

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class RebatchDecision:
    """Decision whether to re-batch remaining tasks."""
    should_rebatch: bool
    reason: str
    trigger: str  # completion, energy_drop, load_spike, deadline, flow_change
    confidence: float  # 0.0-1.0 confidence in decision
    recommended_strategy: Optional[str] = None


# ============================================================================
# Dynamic Batcher
# ============================================================================

class DynamicBatcher:
    """
    Adaptively re-batches tasks based on real-time performance.

    Re-Batching Triggers:
    1. Task completion → Adjust remaining batch
    2. Energy drop → Simplify to lower complexity tasks
    3. Cognitive load spike → Reduce batch size
    4. Attention scattered → Increase cohesion requirement
    5. Flow state entered → Preserve flow with similar tasks

    Performance: < 50ms per re-batch decision
    """

    # Re-batching thresholds
    REBATCH_THRESHOLDS = {
        "energy_drop": 2,  # Energy drops 2+ levels
        "cognitive_load_spike": 0.3,  # Load increases > 0.3
        "attention_degradation": 1,  # Attention drops 1+ level
        "completion_rate_low": 0.5,  # < 50% tasks completed
        "time_overrun": 1.5  # 50% over estimated time
    }

    # Energy level encoding (for comparison)
    ENERGY_LEVELS = {
        "very_low": 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "hyperfocus": 4
    }

    def __init__(self):
        """Initialize dynamic batcher."""
        self.batcher = TaskBatcher()
        self.scorer = BatchQualityScorer()
        self._rebatch_count = 0
        logger.info("DynamicBatcher initialized")

    def check_rebatch_needed(
        self,
        current_batch: TaskBatch,
        completed_task: any,
        current_state: any,
        previous_state: Optional[any] = None,
        flow_state: Optional[any] = None
    ) -> RebatchDecision:
        """
        Decide if remaining batch should be re-optimized.

        Args:
            current_batch: Active batch being executed
            completed_task: Task that was just completed
            current_state: Current ADHD state
            previous_state: Previous ADHD state (for comparison)
            flow_state: Current flow state

        Returns:
            RebatchDecision with should_rebatch flag and reasoning

        Performance: < 50ms target
        """
        # Check each rebatch trigger
        triggers = []

        # 1. Energy drop check
        if previous_state:
            energy_drop = self._check_energy_drop(previous_state, current_state)
            if energy_drop >= self.REBATCH_THRESHOLDS["energy_drop"]:
                triggers.append(("energy_drop", energy_drop, 0.9))

        # 2. Cognitive load spike
        if previous_state:
            load_spike = self._check_cognitive_load_spike(previous_state, current_state)
            if load_spike >= self.REBATCH_THRESHOLDS["cognitive_load_spike"]:
                triggers.append(("load_spike", load_spike, 0.85))

        # 3. Attention degradation
        if previous_state:
            attention_drop = self._check_attention_degradation(previous_state, current_state)
            if attention_drop >= self.REBATCH_THRESHOLDS["attention_degradation"]:
                triggers.append(("attention_degradation", attention_drop, 0.8))

        # 4. Flow state change (important for preservation)
        if flow_state and previous_state:
            flow_change = self._check_flow_state_change(flow_state)
            if flow_change:
                triggers.append(("flow_change", 1.0, 0.95))

        # 5. Time overrun (estimated vs actual)
        time_overrun = self._check_time_overrun(current_batch, completed_task)
        if time_overrun >= self.REBATCH_THRESHOLDS["time_overrun"]:
            triggers.append(("time_overrun", time_overrun, 0.7))

        # Decision logic
        if not triggers:
            return RebatchDecision(
                should_rebatch=False,
                reason="No significant state changes detected",
                trigger="none",
                confidence=0.9
            )

        # Select strongest trigger
        strongest_trigger = max(triggers, key=lambda t: t[1] * t[2])  # value * confidence
        trigger_name, trigger_value, confidence = strongest_trigger

        # Recommend strategy based on trigger
        strategy = self._recommend_strategy(trigger_name, current_state, flow_state)

        logger.info(
            f"Re-batch triggered: {trigger_name} "
            f"(value: {trigger_value:.2f}, confidence: {confidence:.2f})"
        )

        return RebatchDecision(
            should_rebatch=True,
            reason=f"Triggered by {trigger_name}: {self._explain_trigger(trigger_name, trigger_value)}",
            trigger=trigger_name,
            confidence=confidence,
            recommended_strategy=strategy
        )

    def re_batch_on_completion(
        self,
        completed_task: any,
        remaining_batch: TaskBatch,
        current_state: any,
        flow_state: Optional[any] = None
    ) -> TaskBatch:
        """
        Re-optimize remaining batch after task completion.

        Args:
            completed_task: Task that was just completed
            remaining_batch: Current batch with remaining tasks
            current_state: Current ADHD state
            flow_state: Current flow state

        Returns:
            Updated TaskBatch with re-optimized task order
        """
        if not remaining_batch.tasks:
            return remaining_batch  # No tasks left

        # Determine re-batching strategy
        if flow_state:
            flow_level = getattr(flow_state, 'level', None)
            if flow_level:
                flow_level_str = flow_level.value if hasattr(flow_level, 'value') else str(flow_level)
                if flow_level_str in ['flow', 'focused']:
                    # Preserve flow - use similarity batching
                    strategy = "flow_first"
                else:
                    strategy = "balanced"
            else:
                strategy = "balanced"
        else:
            strategy = "balanced"

        # Re-batch remaining tasks
        new_batches = self.batcher.create_batches(
            candidate_tasks=remaining_batch.tasks,
            adhd_state=current_state,
            batching_mode=strategy,
            flow_state=flow_state
        )

        # Return first batch (should contain all remaining tasks if similar)
        if new_batches:
            self._rebatch_count += 1
            logger.info(
                f"Re-batched {len(remaining_batch.tasks)} remaining tasks "
                f"(strategy: {strategy})"
            )
            return new_batches[0]

        return remaining_batch  # Fallback

    def _check_energy_drop(self, previous_state: any, current_state: any) -> int:
        """Check if energy level dropped significantly."""
        prev_energy = getattr(previous_state, 'energy_level', 'medium')
        curr_energy = getattr(current_state, 'energy_level', 'medium')

        prev_level = self.ENERGY_LEVELS.get(prev_energy, 2)
        curr_level = self.ENERGY_LEVELS.get(curr_energy, 2)

        return max(0, prev_level - curr_level)  # Positive if dropped

    def _check_cognitive_load_spike(self, previous_state: any, current_state: any) -> float:
        """Check if cognitive load spiked significantly."""
        prev_load = getattr(previous_state, 'cognitive_load', 0.5)
        curr_load = getattr(current_state, 'cognitive_load', 0.5)

        return max(0.0, curr_load - prev_load)  # Positive if increased

    def _check_attention_degradation(self, previous_state: any, current_state: any) -> int:
        """Check if attention level degraded."""
        attention_levels = {
            "scattered": 0,
            "transitioning": 1,
            "focused": 2,
            "hyperfocused": 3
        }

        prev_attention = getattr(previous_state, 'attention_level', 'normal')
        curr_attention = getattr(current_state, 'attention_level', 'normal')

        prev_level = attention_levels.get(prev_attention, 1)
        curr_level = attention_levels.get(curr_attention, 1)

        return max(0, prev_level - curr_level)  # Positive if degraded

    def _check_flow_state_change(self, flow_state: any) -> bool:
        """Check if flow state just changed significantly."""
        # If just entered flow or focused state, should re-batch to preserve
        flow_level = getattr(flow_state, 'level', None)
        if flow_level:
            flow_level_str = flow_level.value if hasattr(flow_level, 'value') else str(flow_level)
            duration = getattr(flow_state, 'duration_minutes', 0.0)

            # Just entered flow/focused (< 5 min in state)
            if flow_level_str in ['flow', 'focused'] and duration < 5.0:
                return True

        return False

    def _check_time_overrun(self, batch: TaskBatch, completed_task: any) -> float:
        """Check if task took significantly longer than estimated."""
        estimated = getattr(completed_task, 'estimated_duration', 30)
        actual = getattr(completed_task, 'actual_duration', estimated)  # May not be tracked

        if actual > 0 and estimated > 0:
            return actual / estimated

        return 1.0  # No overrun if not tracked

    def _recommend_strategy(
        self,
        trigger: str,
        current_state: any,
        flow_state: Optional[any]
    ) -> str:
        """Recommend batching strategy based on trigger."""
        if trigger == "energy_drop":
            return "momentum_first"  # Easier tasks first

        elif trigger == "load_spike":
            return "similarity_first"  # Reduce context switching

        elif trigger == "attention_degradation":
            return "similarity_first"  # High cohesion helps focus

        elif trigger == "flow_change":
            return "flow_first"  # Preserve flow state

        elif trigger == "time_overrun":
            return "deadline_first"  # Prioritize completion

        else:
            return "balanced"  # Default

    def _explain_trigger(self, trigger_name: str, value: float) -> str:
        """Generate human-readable explanation of trigger."""
        explanations = {
            "energy_drop": f"Energy dropped {int(value)} levels",
            "load_spike": f"Cognitive load increased {value:.1%}",
            "attention_degradation": f"Attention degraded {int(value)} levels",
            "flow_change": "Entered flow state - preserving with similar tasks",
            "time_overrun": f"Task took {value:.0%} of estimated time"
        }

        return explanations.get(trigger_name, f"Trigger value: {value:.2f}")

    def get_statistics(self) -> Dict[str, any]:
        """Get dynamic batching statistics."""
        return {
            "rebatch_count": self._rebatch_count,
            "batcher_stats": self.batcher.get_statistics(),
            "scorer_stats": self.scorer.get_statistics()
        }


# ============================================================================
# Helper Functions
# ============================================================================

def check_rebatch(
    batch: TaskBatch,
    completed_task: any,
    current_state: any,
    previous_state: Optional[any] = None
) -> RebatchDecision:
    """
    Convenience function for quick rebatch check.

    Args:
        batch: Current active batch
        completed_task: Task just completed
        current_state: Current ADHD state
        previous_state: Previous ADHD state (for comparison)

    Returns:
        RebatchDecision with recommendation

    Example:
        decision = check_rebatch(batch, completed_task, current_state, previous_state)
        if decision.should_rebatch:
            print(f"Re-batching recommended: {decision.reason}")
            # Re-batch with decision.recommended_strategy
    """
    batcher = DynamicBatcher()
    return batcher.check_rebatch_needed(batch, completed_task, current_state, previous_state)
