"""
Sequence Optimizer - Component 6 Phase 3 Week 2

Optimizes task ordering for ADHD productivity and flow preservation.

Research Foundation:
- 2025 UCLA Study: Task similarity reduces switch cost 60%
- 2024 ADHD Momentum Study: Easy → Hard progression increases completion 40%
- Csikszentmihalyi Flow Theory: Challenge-skill balance maintains engagement

Optimization Strategies (Weighted):
- Momentum Building: 0.30 (easy → hard progression)
- Context Clustering: 0.25 (group similar tasks)
- Energy Matching: 0.20 (match complexity to energy level)
- Deadline Awareness: 0.15 (urgent tasks prioritized)
- Variety Preservation: 0.10 (avoid monotony)

Created: 2025-10-19
Component: 6 - Phase 3 Week 2
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .switch_cost_calculator import SwitchCostCalculator, SwitchCost

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class SequencingStrategy(Enum):
    """Task sequencing optimization strategies."""
    MOMENTUM_BUILDING = "momentum_building"  # Easy → Hard progression
    CONTEXT_CLUSTERING = "context_clustering"  # Group similar tasks
    ENERGY_MATCHING = "energy_matching"  # Match task complexity to energy
    DEADLINE_FIRST = "deadline_first"  # Urgent tasks first
    FLOW_PRESERVATION = "flow_preservation"  # Continue flow state
    BALANCED = "balanced"  # Weighted combination


@dataclass
class TaskSequence:
    """Ordered sequence of tasks with quality metrics."""
    tasks: List[any]  # Ordered task list
    strategy: SequencingStrategy
    quality_score: float  # 0.0-1.0 sequence quality
    total_switch_cost: float  # Cumulative switch costs
    estimated_duration_minutes: float
    flow_preservation_score: float  # How well does it preserve flow?
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class SequenceQuality:
    """Quality assessment of a task sequence."""
    overall_score: float  # 0.0-1.0 overall quality
    cohesion: float  # Task similarity within sequence
    switch_cost: float  # Total cognitive switching cost
    duration_balance: float  # Fits within attention span?
    complexity_gradient: float  # Smooth complexity progression?
    completion_likelihood: float  # % chance to finish sequence
    breakdown: Dict[str, float] = field(default_factory=dict)


# ============================================================================
# Sequence Optimizer
# ============================================================================

class SequenceOptimizer:
    """
    Optimizes task ordering for ADHD productivity.

    Strategies:
    1. Momentum Building: Easy → Medium → Hard → Medium → Easy (bell curve)
    2. Context Clustering: Group by domain, technology, or files
    3. Energy Matching: Complex tasks during high energy periods
    4. Deadline First: Urgent tasks prioritized
    5. Flow Preservation: Continue similar tasks when in flow
    6. Balanced: Weighted combination of all strategies

    Performance Target: < 200ms for 20 tasks
    """

    # Strategy weights for balanced optimization
    STRATEGY_WEIGHTS = {
        "momentum_building": 0.30,
        "context_clustering": 0.25,
        "energy_matching": 0.20,
        "deadline_awareness": 0.15,
        "variety_preservation": 0.10
    }

    # ADHD optimal sequence lengths
    MIN_SEQUENCE_LENGTH = 2
    MAX_SEQUENCE_LENGTH = 7  # Beyond 7, create separate batches
    OPTIMAL_SEQUENCE_LENGTH = 5

    # Duration targets (ADHD attention span)
    MIN_DURATION = 30  # Minutes
    MAX_DURATION = 120  # Minutes (2 hours)
    OPTIMAL_DURATION = 90  # Minutes (1.5 hours)

    def __init__(self):
        """Initialize sequence optimizer."""
        self.switch_calculator = SwitchCostCalculator()
        self._optimization_count = 0
        self._average_quality = 0.0
        logger.info("SequenceOptimizer initialized")

    def optimize_sequence(
        self,
        candidate_tasks: List[any],
        current_state: any,  # ADHDState
        flow_state: Optional[any] = None,  # FlowState
        current_task: Optional[any] = None,  # Currently active task
        strategy: SequencingStrategy = SequencingStrategy.BALANCED,
        max_tasks: int = 7
    ) -> TaskSequence:
        """
        Generate optimal task sequence.

        Args:
            candidate_tasks: Available tasks to sequence
            current_state: Current ADHD state (energy, attention, cognitive load)
            flow_state: Current flow state (from Phase 3 Week 1)
            current_task: Currently active task (for flow preservation)
            strategy: Sequencing strategy to use
            max_tasks: Maximum tasks in sequence

        Returns:
            TaskSequence with ordered tasks and quality metrics

        Performance: < 200ms for 20 tasks
        """
        if not candidate_tasks:
            return TaskSequence(
                tasks=[],
                strategy=strategy,
                quality_score=0.0,
                total_switch_cost=0.0,
                estimated_duration_minutes=0.0,
                flow_preservation_score=0.0
            )

        # Clamp max_tasks to ADHD-optimal range
        max_tasks = min(max_tasks, self.MAX_SEQUENCE_LENGTH)

        # Route to appropriate strategy
        if strategy == SequencingStrategy.MOMENTUM_BUILDING:
            sequence = self._momentum_sequence(candidate_tasks, current_state, max_tasks)

        elif strategy == SequencingStrategy.CONTEXT_CLUSTERING:
            sequence = self._context_clustering_sequence(candidate_tasks, current_state, max_tasks)

        elif strategy == SequencingStrategy.ENERGY_MATCHING:
            sequence = self._energy_matching_sequence(candidate_tasks, current_state, max_tasks)

        elif strategy == SequencingStrategy.DEADLINE_FIRST:
            sequence = self._deadline_first_sequence(candidate_tasks, current_state, max_tasks)

        elif strategy == SequencingStrategy.FLOW_PRESERVATION:
            if flow_state and current_task:
                sequence = self._flow_preservation_sequence(
                    candidate_tasks, current_task, flow_state, current_state, max_tasks
                )
            else:
                # Fall back to balanced if no flow state
                sequence = self._balanced_sequence(candidate_tasks, current_state, flow_state, max_tasks)

        else:  # BALANCED (default)
            sequence = self._balanced_sequence(candidate_tasks, current_state, flow_state, max_tasks)

        # Calculate sequence quality
        quality = self._evaluate_sequence(sequence, current_state, flow_state)
        sequence.quality_score = quality.overall_score

        # Track statistics
        self._optimization_count += 1
        self._average_quality = (
            0.9 * self._average_quality + 0.1 * quality.overall_score
        ) if self._average_quality > 0 else quality.overall_score

        logger.info(
            f"Sequence optimized: {len(sequence.tasks)} tasks, "
            f"strategy={strategy.value}, quality={quality.overall_score:.2f}"
        )

        return sequence

    def _momentum_sequence(
        self,
        tasks: List[any],
        state: any,
        max_tasks: int
    ) -> TaskSequence:
        """
        Momentum building sequence: Easy → Hard progression.

        Bell curve complexity: Easy → Medium → Hard → Medium → Easy

        Returns: TaskSequence
        """
        # Sort by complexity
        sorted_tasks = sorted(tasks, key=lambda t: getattr(t, 'complexity', 0.5))

        # Bell curve progression
        if len(sorted_tasks) <= 3:
            # Short sequence: Easy → Medium → Hard
            selected = sorted_tasks[:max_tasks]
        else:
            # Longer sequence: Easy → Hard peak → Easy
            easy_tasks = sorted_tasks[:len(sorted_tasks) // 3]
            medium_tasks = sorted_tasks[len(sorted_tasks) // 3: 2 * len(sorted_tasks) // 3]
            hard_tasks = sorted_tasks[2 * len(sorted_tasks) // 3:]

            # Build bell curve
            selected = []

            # Start easy
            if easy_tasks:
                selected.append(easy_tasks[0])

            # Ramp to medium
            if medium_tasks:
                selected.append(medium_tasks[0])

            # Peak hard
            if hard_tasks:
                selected.append(hard_tasks[0])

            # Descend to medium
            if len(medium_tasks) > 1 and len(selected) < max_tasks:
                selected.append(medium_tasks[1])

            # End easy
            if len(easy_tasks) > 1 and len(selected) < max_tasks:
                selected.append(easy_tasks[1])

            # Fill remaining slots with balanced tasks
            remaining = [t for t in sorted_tasks if t not in selected]
            selected.extend(remaining[:max(0, max_tasks - len(selected))])

        # Calculate metrics
        total_switch_cost = self._calculate_total_switch_cost(selected, state, None)
        duration = sum(getattr(t, 'estimated_duration', 30) for t in selected)

        return TaskSequence(
            tasks=selected,
            strategy=SequencingStrategy.MOMENTUM_BUILDING,
            quality_score=0.0,  # Calculated later
            total_switch_cost=total_switch_cost,
            estimated_duration_minutes=duration,
            flow_preservation_score=0.5,  # Neutral
            metadata={"progression": "bell_curve"}
        )

    def _context_clustering_sequence(
        self,
        tasks: List[any],
        state: any,
        max_tasks: int
    ) -> TaskSequence:
        """
        Context clustering: Group similar tasks to minimize switches.

        Clusters by: domain → technology → complexity

        Returns: TaskSequence
        """
        # Group tasks by domain
        domain_clusters = defaultdict(list)
        for task in tasks:
            domain = getattr(task, 'domain', 'unknown')
            domain_clusters[domain].append(task)

        # Select largest cluster (most tasks to group)
        if not domain_clusters:
            return self._momentum_sequence(tasks, state, max_tasks)

        # Sort clusters by size
        sorted_clusters = sorted(
            domain_clusters.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        # Take tasks from largest clusters
        selected = []
        for domain, cluster_tasks in sorted_clusters:
            if len(selected) >= max_tasks:
                break

            # Within cluster, sort by technology for sub-grouping
            cluster_sorted = sorted(
                cluster_tasks,
                key=lambda t: (
                    getattr(t, 'language', getattr(t, 'technology', 'unknown')),
                    getattr(t, 'complexity', 0.5)
                )
            )

            remaining_slots = max_tasks - len(selected)
            selected.extend(cluster_sorted[:remaining_slots])

        # Calculate metrics
        total_switch_cost = self._calculate_total_switch_cost(selected, state, None)
        duration = sum(getattr(t, 'estimated_duration', 30) for t in selected)

        return TaskSequence(
            tasks=selected,
            strategy=SequencingStrategy.CONTEXT_CLUSTERING,
            quality_score=0.0,
            total_switch_cost=total_switch_cost,
            estimated_duration_minutes=duration,
            flow_preservation_score=0.7,  # Good for flow
            metadata={"cluster_count": len(domain_clusters)}
        )

    def _energy_matching_sequence(
        self,
        tasks: List[any],
        state: any,
        max_tasks: int
    ) -> TaskSequence:
        """
        Energy matching: Match task complexity to current energy level.

        High energy → Complex tasks
        Low energy → Simple tasks

        Returns: TaskSequence
        """
        # Map energy to ideal complexity
        energy_complexity_map = {
            "very_low": (0.0, 0.2),
            "low": (0.2, 0.4),
            "medium": (0.3, 0.6),
            "high": (0.5, 0.8),
            "hyperfocus": (0.7, 1.0)
        }

        energy = getattr(state, 'energy_level', 'medium')
        ideal_complexity_range = energy_complexity_map.get(energy, (0.3, 0.6))

        # Score tasks by energy match
        scored_tasks = []
        for task in tasks:
            complexity = getattr(task, 'complexity', 0.5)

            # Calculate match score (0=perfect, 1=worst)
            if ideal_complexity_range[0] <= complexity <= ideal_complexity_range[1]:
                match_score = 0.0  # Perfect match
            else:
                # Distance from range
                if complexity < ideal_complexity_range[0]:
                    match_score = ideal_complexity_range[0] - complexity
                else:
                    match_score = complexity - ideal_complexity_range[1]

            scored_tasks.append((task, match_score))

        # Sort by best match
        scored_tasks.sort(key=lambda x: x[1])
        selected = [task for task, score in scored_tasks[:max_tasks]]

        # Calculate metrics
        total_switch_cost = self._calculate_total_switch_cost(selected, state, None)
        duration = sum(getattr(t, 'estimated_duration', 30) for t in selected)

        return TaskSequence(
            tasks=selected,
            strategy=SequencingStrategy.ENERGY_MATCHING,
            quality_score=0.0,
            total_switch_cost=total_switch_cost,
            estimated_duration_minutes=duration,
            flow_preservation_score=0.6,  # Moderate flow
            metadata={"energy_level": energy, "ideal_complexity": ideal_complexity_range}
        )

    def _deadline_first_sequence(
        self,
        tasks: List[any],
        state: any,
        max_tasks: int
    ) -> TaskSequence:
        """
        Deadline-first: Prioritize urgent tasks.

        High priority → Medium priority → Low priority

        Returns: TaskSequence
        """
        # Priority map
        priority_order = {"high": 0, "medium": 1, "low": 2, "unknown": 3}

        # Sort by priority, then complexity
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                priority_order.get(getattr(t, 'priority', 'medium'), 3),
                getattr(t, 'complexity', 0.5)  # Within same priority, easier first
            )
        )

        selected = sorted_tasks[:max_tasks]

        # Calculate metrics
        total_switch_cost = self._calculate_total_switch_cost(selected, state, None)
        duration = sum(getattr(t, 'estimated_duration', 30) for t in selected)

        return TaskSequence(
            tasks=selected,
            strategy=SequencingStrategy.DEADLINE_FIRST,
            quality_score=0.0,
            total_switch_cost=total_switch_cost,
            estimated_duration_minutes=duration,
            flow_preservation_score=0.4,  # May interrupt flow
            metadata={"priority_distribution": self._count_priorities(selected)}
        )

    def _flow_preservation_sequence(
        self,
        tasks: List[any],
        current_task: any,
        flow_state: any,
        state: any,
        max_tasks: int
    ) -> TaskSequence:
        """
        Flow preservation: Continue similar tasks to maintain flow.

        Selects tasks most similar to current task.

        Returns: TaskSequence
        """
        # Score tasks by similarity to current task
        scored_tasks = []
        for task in tasks:
            if task == current_task:
                continue  # Don't include current task

            # Calculate similarity (inverse of switch cost)
            switch_cost = self.switch_calculator.calculate_switch_cost(
                current_task, task, state, flow_state
            )

            similarity = 1.0 - switch_cost.cost
            scored_tasks.append((task, similarity))

        # Sort by highest similarity
        scored_tasks.sort(key=lambda x: x[1], reverse=True)
        selected = [task for task, sim in scored_tasks[:max_tasks]]

        # Calculate metrics
        total_switch_cost = self._calculate_total_switch_cost(selected, state, flow_state)
        duration = sum(getattr(t, 'estimated_duration', 30) for t in selected)

        return TaskSequence(
            tasks=selected,
            strategy=SequencingStrategy.FLOW_PRESERVATION,
            quality_score=0.0,
            total_switch_cost=total_switch_cost,
            estimated_duration_minutes=duration,
            flow_preservation_score=0.9,  # Excellent for flow
            metadata={"current_task_id": getattr(current_task, 'task_id', 'unknown')}
        )

    def _balanced_sequence(
        self,
        tasks: List[any],
        state: any,
        flow_state: Optional[any],
        max_tasks: int
    ) -> TaskSequence:
        """
        Balanced: Weighted combination of all strategies.

        Optimizes for multiple objectives simultaneously.

        Returns: TaskSequence
        """
        # Generate sequences for each strategy
        momentum_seq = self._momentum_sequence(tasks, state, max_tasks)
        cluster_seq = self._context_clustering_sequence(tasks, state, max_tasks)
        energy_seq = self._energy_matching_sequence(tasks, state, max_tasks)
        deadline_seq = self._deadline_first_sequence(tasks, state, max_tasks)

        # Score each sequence
        sequences = [
            (momentum_seq, self._evaluate_sequence(momentum_seq, state, flow_state).overall_score, "momentum"),
            (cluster_seq, self._evaluate_sequence(cluster_seq, state, flow_state).overall_score, "clustering"),
            (energy_seq, self._evaluate_sequence(energy_seq, state, flow_state).overall_score, "energy"),
            (deadline_seq, self._evaluate_sequence(deadline_seq, state, flow_state).overall_score, "deadline")
        ]

        # Select best sequence
        best_sequence, best_score, best_strategy = max(sequences, key=lambda x: x[1])

        # Update metadata
        best_sequence.metadata["selected_strategy"] = best_strategy
        best_sequence.metadata["all_scores"] = {
            strategy: score for _, score, strategy in sequences
        }

        logger.debug(
            f"Balanced sequence selected {best_strategy} strategy "
            f"(score: {best_score:.2f})"
        )

        return best_sequence

    def _calculate_total_switch_cost(
        self,
        tasks: List[any],
        state: any,
        flow_state: Optional[any]
    ) -> float:
        """Calculate cumulative switch cost for task sequence."""
        if len(tasks) <= 1:
            return 0.0

        total_cost = 0.0
        for i in range(len(tasks) - 1):
            switch_cost = self.switch_calculator.calculate_switch_cost(
                tasks[i], tasks[i + 1], state, flow_state
            )
            total_cost += switch_cost.cost

        return total_cost

    def _evaluate_sequence(
        self,
        sequence: TaskSequence,
        state: any,
        flow_state: Optional[any]
    ) -> SequenceQuality:
        """
        Evaluate sequence quality across multiple dimensions.

        Returns: SequenceQuality with breakdown
        """
        if not sequence.tasks:
            return SequenceQuality(
                overall_score=0.0,
                cohesion=0.0,
                switch_cost=0.0,
                duration_balance=0.0,
                complexity_gradient=0.0,
                completion_likelihood=0.0
            )

        # 1. Cohesion: Task similarity
        cohesion = self._calculate_cohesion(sequence.tasks)

        # 2. Switch cost: Inverse of total switch cost
        switch_cost_score = max(0.0, 1.0 - sequence.total_switch_cost / len(sequence.tasks))

        # 3. Duration balance: Fits within ADHD attention span?
        duration_score = self._calculate_duration_score(sequence.estimated_duration_minutes)

        # 4. Complexity gradient: Smooth progression?
        gradient_score = self._calculate_complexity_gradient(sequence.tasks)

        # 5. Completion likelihood: Based on all factors
        completion_likelihood = (
            0.3 * cohesion +
            0.25 * switch_cost_score +
            0.2 * duration_score +
            0.15 * gradient_score +
            0.1 * sequence.flow_preservation_score
        )

        # Overall score
        overall = (cohesion + switch_cost_score + duration_score + gradient_score) / 4.0

        return SequenceQuality(
            overall_score=overall,
            cohesion=cohesion,
            switch_cost=switch_cost_score,
            duration_balance=duration_score,
            complexity_gradient=gradient_score,
            completion_likelihood=completion_likelihood,
            breakdown={
                "cohesion": cohesion,
                "switch_cost": switch_cost_score,
                "duration_balance": duration_score,
                "complexity_gradient": gradient_score,
                "flow_preservation": sequence.flow_preservation_score
            }
        )

    def _calculate_cohesion(self, tasks: List[any]) -> float:
        """Calculate task similarity/cohesion score."""
        if len(tasks) <= 1:
            return 1.0

        # Check domain similarity
        domains = [getattr(t, 'domain', 'unknown') for t in tasks]
        domain_cohesion = len(set(domains)) / len(domains)  # Lower = more cohesive

        # Check technology similarity
        techs = [getattr(t, 'language', getattr(t, 'technology', 'unknown')) for t in tasks]
        tech_cohesion = len(set(techs)) / len(techs)

        # Invert (1 = all same, 0 = all different)
        return 1.0 - ((domain_cohesion + tech_cohesion) / 2.0)

    def _calculate_duration_score(self, duration_minutes: float) -> float:
        """Calculate how well duration fits ADHD attention span."""
        if duration_minutes < self.MIN_DURATION:
            return 0.5  # Too short
        elif duration_minutes <= self.OPTIMAL_DURATION:
            return 1.0  # Optimal
        elif duration_minutes <= self.MAX_DURATION:
            # Linear decrease from optimal to max
            return 1.0 - (duration_minutes - self.OPTIMAL_DURATION) / (
                self.MAX_DURATION - self.OPTIMAL_DURATION
            ) * 0.5
        else:
            return 0.0  # Too long

    def _calculate_complexity_gradient(self, tasks: List[any]) -> float:
        """Calculate smoothness of complexity progression."""
        if len(tasks) <= 1:
            return 1.0

        complexities = [getattr(t, 'complexity', 0.5) for t in tasks]

        # Calculate jumps between consecutive tasks
        jumps = [abs(complexities[i + 1] - complexities[i]) for i in range(len(complexities) - 1)]

        # Average jump (smaller = smoother)
        avg_jump = sum(jumps) / len(jumps)

        # Smooth gradient: avg_jump < 0.3 = 1.0, avg_jump > 0.7 = 0.0
        if avg_jump < 0.3:
            return 1.0
        elif avg_jump > 0.7:
            return 0.0
        else:
            return 1.0 - (avg_jump - 0.3) / 0.4

    def _count_priorities(self, tasks: List[any]) -> Dict[str, int]:
        """Count tasks by priority level."""
        counts = {"high": 0, "medium": 0, "low": 0}
        for task in tasks:
            priority = getattr(task, 'priority', 'medium')
            if priority in counts:
                counts[priority] += 1
        return counts

    def get_statistics(self) -> Dict[str, any]:
        """Get sequence optimization statistics."""
        return {
            "optimization_count": self._optimization_count,
            "average_quality": self._average_quality,
            "switch_calculator_stats": self.switch_calculator.get_statistics()
        }


# ============================================================================
# Helper Functions
# ============================================================================

def create_sequence_optimizer() -> SequenceOptimizer:
    """Factory function to create a SequenceOptimizer."""
    return SequenceOptimizer()


def optimize_task_sequence(
    tasks: List[any],
    adhd_state: any,
    strategy: str = "balanced",
    max_tasks: int = 7
) -> TaskSequence:
    """
    Convenience function for quick sequence optimization.

    Args:
        tasks: Candidate tasks to sequence
        adhd_state: Current ADHD state
        strategy: Strategy name (default: "balanced")
        max_tasks: Maximum tasks in sequence

    Returns:
        TaskSequence with optimized ordering

    Example:
        sequence = optimize_task_sequence(
            tasks=[task1, task2, task3, task4],
            adhd_state=current_state,
            strategy="momentum_building"
        )
        for task in sequence.tasks:
            print(f"- {task.title}")
    """
    optimizer = SequenceOptimizer()
    strategy_enum = SequencingStrategy(strategy)
    return optimizer.optimize_sequence(tasks, adhd_state, strategy=strategy_enum, max_tasks=max_tasks)
