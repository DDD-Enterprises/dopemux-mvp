"""
Adaptive Population Management for Enhanced Iterative Agent

Implements dynamic population sizing, complexity-based adaptation,
and performance monitoring for optimal GP evolution.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import statistics

from .population import GPPopulation, GPIndividual

class PopulationStrategy(Enum):
    """Population sizing strategies."""
    FIXED = "fixed"
    COMPLEXITY_BASED = "complexity_based"
    PERFORMANCE_ADAPTIVE = "performance_adaptive"
    RESOURCE_AWARE = "resource_aware"

@dataclass
class PopulationMetrics:
    """Metrics for population performance evaluation."""
    generation: int
    population_size: int
    best_fitness: float
    average_fitness: float
    fitness_variance: float
    convergence_rate: float
    resource_usage: Dict[str, float]
    adaptation_triggers: List[str]
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class ComplexityAssessment:
    """Assessment of problem complexity for population sizing."""
    complexity_score: float
    estimated_difficulty: str  # "easy", "medium", "hard", "extreme"
    recommended_population_size: int
    confidence_intervals: Tuple[int, int]
    reasoning: str

class AdaptivePopulationManager:
    """
    Manages GP population adaptation based on problem complexity and performance.

    Key Features:
    - Dynamic population sizing based on problem characteristics
    - Performance monitoring and adaptation triggers
    - Resource-aware allocation
    - Historical performance learning
    """

    def __init__(self, base_population_size: int = 10):
        self.base_population_size = base_population_size
        self.current_strategy = PopulationStrategy.COMPLEXITY_BASED

        # Performance tracking
        self.performance_history: List[PopulationMetrics] = []
        self.max_history_size = 100

        # Adaptation parameters
        self.convergence_threshold = 0.05  # 5% fitness improvement threshold
        self.resource_limits = {
            'max_population': 50,
            'min_population': 3,
            'memory_limit_mb': 500,
            'time_limit_seconds': 30
        }

        # Complexity mapping
        self.complexity_mapping = {
            (0.0, 0.3): ("easy", 5, (3, 8)),
            (0.3, 0.6): ("medium", 10, (7, 15)),
            (0.6, 0.8): ("hard", 20, (15, 30)),
            (0.8, 1.0): ("extreme", 30, (20, 50))
        }

    def assess_problem_complexity(
        self,
        complexity_score: float,
        pattern_count: int,
        description_length: int,
        historical_performance: Optional[List[float]] = None
    ) -> ComplexityAssessment:
        """
        Assess problem complexity for optimal population sizing.

        Args:
            complexity_score: Code complexity (0.0-1.0)
            pattern_count: Number of similar patterns found
            description_length: Length of bug description
            historical_performance: Past success rates for similar problems

        Returns:
            Complexity assessment with recommended population size
        """
        # Determine difficulty category
        difficulty = "medium"
        recommended_size = self.base_population_size
        confidence_range = (7, 15)

        for (min_complexity, max_complexity), (diff, size, conf_range) in self.complexity_mapping.items():
            if min_complexity <= complexity_score < max_complexity:
                difficulty = diff
                recommended_size = size
                confidence_range = conf_range
                break

        # Adjust based on pattern availability
        if pattern_count < 3:
            # Fewer patterns = harder problem, increase population
            recommended_size = min(recommended_size + 5, self.resource_limits['max_population'])
            confidence_range = (confidence_range[0] + 2, confidence_range[1] + 5)
        elif pattern_count > 10:
            # Many patterns = easier problem, can reduce population
            recommended_size = max(recommended_size - 3, self.resource_limits['min_population'])
            confidence_range = (max(confidence_range[0] - 2, 3), confidence_range[1] - 3)

        # Adjust based on description complexity
        if description_length > 500:
            recommended_size = min(recommended_size + 3, self.resource_limits['max_population'])
        elif description_length < 100:
            recommended_size = max(recommended_size - 2, self.resource_limits['min_population'])

        # Adjust based on historical performance
        if historical_performance:
            avg_performance = statistics.mean(historical_performance)
            if avg_performance < 0.5:
                # Historically difficult, increase population
                recommended_size = min(recommended_size + 5, self.resource_limits['max_population'])
            elif avg_performance > 0.8:
                # Historically successful, can optimize down
                recommended_size = max(int(recommended_size * 0.8), self.resource_limits['min_population'])

        # Build reasoning
        reasoning_parts = [
            f"Complexity score {complexity_score:.2f} indicates {difficulty} difficulty",
            f"Found {pattern_count} similar patterns",
            f"Bug description length: {description_length} characters"
        ]

        if historical_performance:
            reasoning_parts.append(f"Historical success rate: {avg_performance:.2f}")

        reasoning = "; ".join(reasoning_parts)

        return ComplexityAssessment(
            complexity_score=complexity_score,
            estimated_difficulty=difficulty,
            recommended_population_size=recommended_size,
            confidence_intervals=confidence_range,
            reasoning=reasoning
        )

    def adapt_population_size(
        self,
        current_population: GPPopulation,
        problem_complexity: ComplexityAssessment,
        performance_metrics: Dict[str, Any],
        available_resources: Dict[str, float]
    ) -> Tuple[int, str]:
        """
        Adapt population size based on current conditions.

        Args:
            current_population: Current GP population
            problem_complexity: Complexity assessment
            performance_metrics: Current performance data
            available_resources: Available system resources

        Returns:
            Tuple of (new_population_size, adaptation_reason)
        """
        current_size = len(current_population.population)
        recommended_size = problem_complexity.recommended_population_size

        # Check resource constraints
        memory_usage = available_resources.get('memory_mb', 0)
        if memory_usage > self.resource_limits['memory_limit_mb'] * 0.8:
            # High memory usage, reduce population
            max_size = int(self.resource_limits['max_population'] * 0.7)
            recommended_size = min(recommended_size, max_size)
            return min(current_size, max_size), "High memory usage - reducing population"

        # Check performance convergence
        if len(current_population.fitness_history) >= 3:
            recent_fitness = current_population.fitness_history[-3:]
            improvement = (recent_fitness[-1] - recent_fitness[0]) / max(recent_fitness[0], 0.001)

            if improvement < self.convergence_threshold:
                # Converging, can reduce population for efficiency
                efficiency_size = max(int(current_size * 0.8), self.resource_limits['min_population'])
                return efficiency_size, "Population converging - optimizing for efficiency"

        # Check if we're far from recommended size
        size_difference = abs(current_size - recommended_size)
        if size_difference > 5:
            # Significant difference, adapt towards recommended
            if current_size < recommended_size:
                new_size = min(current_size + 3, recommended_size, self.resource_limits['max_population'])
                return new_size, f"Increasing population to {new_size} based on complexity assessment"
            else:
                new_size = max(current_size - 2, recommended_size, self.resource_limits['min_population'])
                return new_size, f"Reducing population to {new_size} for efficiency"

        # Check performance trends
        if len(self.performance_history) >= 2:
            recent_metrics = self.performance_history[-2:]
            fitness_trend = recent_metrics[1].best_fitness - recent_metrics[0].best_fitness

            if fitness_trend < -0.1:
                # Performance declining, increase population
                new_size = min(current_size + 2, self.resource_limits['max_population'])
                return new_size, "Performance declining - increasing population for more exploration"

        # No significant adaptation needed
        return current_size, "Population size optimal for current conditions"

    def monitor_performance(
        self,
        population: GPPopulation,
        generation_time: float,
        memory_usage: float
    ) -> PopulationMetrics:
        """
        Monitor and record population performance metrics.

        Args:
            population: Current GP population
            generation_time: Time taken for last generation
            memory_usage: Memory usage in MB

        Returns:
            Performance metrics snapshot
        """
        if not population.individuals:
            return PopulationMetrics(
                generation=population.generation,
                population_size=0,
                best_fitness=0.0,
                average_fitness=0.0,
                fitness_variance=0.0,
                convergence_rate=0.0,
                resource_usage={'time': generation_time, 'memory': memory_usage},
                adaptation_triggers=[]
            )

        fitnesses = [ind.fitness for ind in population.individuals]
        best_fitness = max(fitnesses)
        average_fitness = statistics.mean(fitnesses)
        variance = statistics.variance(fitnesses) if len(fitnesses) > 1 else 0.0

        # Calculate convergence rate (improvement over last 3 generations)
        convergence_rate = 0.0
        if len(population.fitness_history) >= 3:
            recent = population.fitness_history[-3:]
            convergence_rate = (recent[-1] - recent[0]) / max(recent[0], 0.001)

        # Identify adaptation triggers
        adaptation_triggers = []
        if best_fitness > 0.8:
            adaptation_triggers.append("high_performance")
        if variance < 0.01:
            adaptation_triggers.append("converged")
        if generation_time > 5.0:
            adaptation_triggers.append("slow_generation")
        if memory_usage > self.resource_limits['memory_limit_mb'] * 0.8:
            adaptation_triggers.append("high_memory")

        metrics = PopulationMetrics(
            generation=population.generation,
            population_size=len(population.individuals),
            best_fitness=best_fitness,
            average_fitness=average_fitness,
            fitness_variance=variance,
            convergence_rate=convergence_rate,
            resource_usage={
                'generation_time': generation_time,
                'memory_usage': memory_usage,
                'cpu_usage': 0.0  # Placeholder
            },
            adaptation_triggers=adaptation_triggers
        )

        # Store in history
        self.performance_history.append(metrics)
        if len(self.performance_history) > self.max_history_size:
            self.performance_history.pop(0)

        return metrics

    def get_adaptation_recommendations(
        self,
        current_metrics: PopulationMetrics,
        problem_complexity: ComplexityAssessment
    ) -> List[str]:
        """
        Generate adaptation recommendations based on current state.

        Args:
            current_metrics: Current performance metrics
            problem_complexity: Problem complexity assessment

        Returns:
            List of adaptation recommendations
        """
        recommendations = []

        # Performance-based recommendations
        if current_metrics.best_fitness < 0.5:
            recommendations.append("Consider increasing population size for more exploration")

        if current_metrics.fitness_variance < 0.05:
            recommendations.append("Population may be converging - consider diversification strategies")

        if current_metrics.convergence_rate < 0.01:
            recommendations.append("Slow convergence detected - review fitness function or operators")

        # Resource-based recommendations
        memory_usage = current_metrics.resource_usage.get('memory_usage', 0)
        if memory_usage > self.resource_limits['memory_limit_mb'] * 0.9:
            recommendations.append("High memory usage - consider population size reduction")

        generation_time = current_metrics.resource_usage.get('generation_time', 0)
        if generation_time > 10.0:
            recommendations.append("Slow generation time - consider operator optimization")

        # Complexity-based recommendations
        current_size = current_metrics.population_size
        recommended_size = problem_complexity.recommended_population_size

        if abs(current_size - recommended_size) > 5:
            if current_size < recommended_size:
                recommendations.append(f"Increase population to {recommended_size} for problem complexity")
            else:
                recommendations.append(f"Consider reducing population to {recommended_size} for efficiency")

        # Strategy recommendations
        if "high_performance" in current_metrics.adaptation_triggers:
            recommendations.append("High performance achieved - consider elitism preservation")

        if "converged" in current_metrics.adaptation_triggers:
            recommendations.append("Population converged - ready for exploitation phase")

        return recommendations

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.performance_history:
            return {"status": "no_data", "message": "No performance data available"}

        recent_metrics = self.performance_history[-10:]  # Last 10 generations

        return {
            "total_generations": len(self.performance_history),
            "average_best_fitness": statistics.mean([m.best_fitness for m in recent_metrics]),
            "average_population_size": statistics.mean([m.population_size for m in recent_metrics]),
            "convergence_trend": self._calculate_convergence_trend(recent_metrics),
            "resource_efficiency": self._calculate_resource_efficiency(recent_metrics),
            "adaptation_frequency": self._calculate_adaptation_frequency(recent_metrics),
            "performance_stability": self._calculate_performance_stability(recent_metrics)
        }

    def _calculate_convergence_trend(self, metrics: List[PopulationMetrics]) -> float:
        """Calculate trend in convergence rate."""
        if len(metrics) < 2:
            return 0.0

        convergence_rates = [m.convergence_rate for m in metrics]
        # Positive trend = improving convergence
        return statistics.linear_regression(range(len(convergence_rates)), convergence_rates)[0]

    def _calculate_resource_efficiency(self, metrics: List[PopulationMetrics]) -> float:
        """Calculate resource efficiency score."""
        if not metrics:
            return 0.0

        # Efficiency = fitness improvement per unit resource
        efficiencies = []
        for i, metric in enumerate(metrics[1:], 1):
            prev_metric = metrics[i-1]
            fitness_gain = metric.best_fitness - prev_metric.best_fitness
            time_cost = metric.resource_usage.get('generation_time', 1.0)
            memory_cost = metric.resource_usage.get('memory_usage', 1.0)

            if time_cost > 0:
                efficiency = fitness_gain / (time_cost * memory_cost)
                efficiencies.append(efficiency)

        return statistics.mean(efficiencies) if efficiencies else 0.0

    def _calculate_adaptation_frequency(self, metrics: List[PopulationMetrics]) -> float:
        """Calculate how often adaptations are triggered."""
        if not metrics:
            return 0.0

        adaptation_count = sum(len(m.adaptation_triggers) for m in metrics)
        return adaptation_count / len(metrics)

    def _calculate_performance_stability(self, metrics: List[PopulationMetrics]) -> float:
        """Calculate performance stability (lower variance = more stable)."""
        if len(metrics) < 2:
            return 1.0

        best_fitnesses = [m.best_fitness for m in metrics]
        if len(best_fitnesses) > 1:
            variance = statistics.variance(best_fitnesses)
            # Convert to stability score (0-1, higher = more stable)
            return 1.0 / (1.0 + variance)
        return 1.0