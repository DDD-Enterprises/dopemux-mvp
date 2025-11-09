"""
Historical Learning System for Enhanced Iterative Agent

Tracks operator performance, learns from past repairs, and enables
intelligent operator selection based on historical success patterns.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import statistics
import json

from shared.mcp.conport_client import ConPortClient

@dataclass
class OperatorPerformance:
    """Performance data for a specific operator."""
    operator_name: str
    total_uses: int
    successful_uses: int
    average_fitness_gain: float
    average_time_cost: float
    success_rate: float
    context_effectiveness: Dict[str, float]  # performance by context type
    last_used: datetime
    confidence_score: float

    @property
    def effectiveness_score(self) -> float:
        """Calculate overall effectiveness score."""
        if self.total_uses == 0:
            return 0.0

        # Weighted combination of success rate and fitness gain
        success_weight = 0.6
        fitness_weight = 0.4

        success_score = self.success_rate
        fitness_score = min(1.0, self.average_fitness_gain / 0.5)  # Normalize to 0-1

        return (success_weight * success_score) + (fitness_weight * fitness_score)

@dataclass
class LearningEvent:
    """A learning event from a repair attempt."""
    event_id: str
    operator_used: str
    context: Dict[str, Any]
    fitness_before: float
    fitness_after: float
    time_cost: float
    success: bool
    timestamp: datetime
    population_size: int
    generation: int

@dataclass
class OperatorRecommendation:
    """Recommendation for operator selection."""
    recommended_operator: str
    confidence: float
    reasoning: str
    alternative_operators: List[Tuple[str, float]]
    expected_performance: float

class HistoricalLearningSystem:
    """
    Learns from past repair attempts to optimize future performance.

    Key Features:
    - Operator performance tracking
    - Context-aware learning
    - Intelligent operator recommendation
    - Performance pattern recognition
    - ConPort integration for persistence
    """

    def __init__(self, conport_client: ConPortClient, workspace_id: str):
        self.conport_client = conport_client
        self.workspace_id = workspace_id

        # Learning data
        self.operator_performance: Dict[str, OperatorPerformance] = {}
        self.learning_events: List[LearningEvent] = []
        self.max_events_memory = 1000

        # Learning parameters
        self.min_confidence_threshold = 0.1
        self.learning_rate = 0.1
        self.forget_factor = 0.95  # How much to weight recent vs old data

        # Initialize with known operators
        self._initialize_known_operators()

    def _initialize_known_operators(self):
        """Initialize performance tracking for known GP operators."""
        known_operators = [
            "mutate_condition",
            "swap_operators",
            "negate_condition",
            "add_statement",
            "remove_statement",
            "replace_expression",
            "subtree_crossover",
            "hoist_mutation",
            "node_replacement",
            "hunk_edit_insert",
            "hunk_edit_delete"
        ]

        for operator in known_operators:
            self.operator_performance[operator] = OperatorPerformance(
                operator_name=operator,
                total_uses=0,
                successful_uses=0,
                average_fitness_gain=0.0,
                average_time_cost=1.0,
                success_rate=0.5,  # Start neutral
                context_effectiveness={},
                last_used=datetime.now(),
                confidence_score=self.min_confidence_threshold
            )

    async def record_repair_attempt(
        self,
        operator_used: str,
        context: Dict[str, Any],
        fitness_before: float,
        fitness_after: float,
        time_cost: float,
        population_size: int,
        generation: int
    ) -> None:
        """
        Record a repair attempt for learning.

        Args:
            operator_used: Name of the operator that was applied
            context: Repair context (complexity, patterns, etc.)
            fitness_before: Fitness before operator application
            fitness_after: Fitness after operator application
            time_cost: Time taken for operator application
            population_size: Size of population when operator was used
            generation: Generation number when operator was used
        """
        # Determine success
        fitness_gain = fitness_after - fitness_before
        success = fitness_gain > 0.05  # 5% improvement threshold

        # Create learning event
        event = LearningEvent(
            event_id=f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.learning_events)}",
            operator_used=operator_used,
            context=context.copy(),
            fitness_before=fitness_before,
            fitness_after=fitness_after,
            time_cost=time_cost,
            success=success,
            timestamp=datetime.now(),
            population_size=population_size,
            generation=generation
        )

        # Add to memory
        self.learning_events.append(event)
        if len(self.learning_events) > self.max_events_memory:
            self.learning_events.pop(0)

        # Update operator performance
        await self._update_operator_performance(operator_used, event)

        # Persist to ConPort
        await self._persist_learning_event(event)

    async def _update_operator_performance(self, operator_name: str, event: LearningEvent):
        """Update performance statistics for an operator."""
        if operator_name not in self.operator_performance:
            # Initialize new operator
            self.operator_performance[operator_name] = OperatorPerformance(
                operator_name=operator_name,
                total_uses=0,
                successful_uses=0,
                average_fitness_gain=0.0,
                average_time_cost=1.0,
                success_rate=0.5,
                context_effectiveness={},
                last_used=datetime.now(),
                confidence_score=self.min_confidence_threshold
            )

        perf = self.operator_performance[operator_name]

        # Update counters
        perf.total_uses += 1
        if event.success:
            perf.success_uses += 1

        # Update averages with learning rate
        fitness_gain = event.fitness_after - event.fitness_before
        perf.average_fitness_gain = (
            (1 - self.learning_rate) * perf.average_fitness_gain +
            self.learning_rate * fitness_gain
        )

        perf.average_time_cost = (
            (1 - self.learning_rate) * perf.average_time_cost +
            self.learning_rate * event.time_cost
        )

        # Update success rate
        perf.success_rate = perf.successful_uses / perf.total_uses

        # Update context effectiveness
        context_type = self._classify_context(event.context)
        if context_type not in perf.context_effectiveness:
            perf.context_effectiveness[context_type] = fitness_gain
        else:
            perf.context_effectiveness[context_type] = (
                (1 - self.learning_rate) * perf.context_effectiveness[context_type] +
                self.learning_rate * fitness_gain
            )

        # Update metadata
        perf.last_used = event.timestamp
        perf.confidence_score = min(1.0, perf.total_uses / 10.0)  # Increase with experience

    def _classify_context(self, context: Dict[str, Any]) -> str:
        """Classify repair context for performance analysis."""
        complexity = context.get('complexity', {}).get('score', 0.5)

        if complexity < 0.3:
            return "simple"
        elif complexity < 0.7:
            return "medium"
        else:
            return "complex"

    async def recommend_operator(
        self,
        context: Dict[str, Any],
        available_operators: List[str],
        population_size: int,
        current_generation: int
    ) -> OperatorRecommendation:
        """
        Recommend the best operator for current context.

        Args:
            context: Current repair context
            available_operators: List of operators that can be applied
            population_size: Current population size
            current_generation: Current generation number

        Returns:
            Operator recommendation with confidence and reasoning
        """
        if not available_operators:
            return OperatorRecommendation(
                recommended_operator="mutate_condition",  # Safe default
                confidence=0.1,
                reasoning="No operators available, using safe default",
                alternative_operators=[],
                expected_performance=0.0
            )

        # Score each available operator
        operator_scores = []
        context_type = self._classify_context(context)

        for operator in available_operators:
            if operator in self.operator_performance:
                perf = self.operator_performance[operator]

                # Base score from effectiveness
                base_score = perf.effectiveness_score

                # Context bonus
                context_bonus = perf.context_effectiveness.get(context_type, 0.0) * 0.2

                # Recency bonus (prefer recently successful operators)
                recency_hours = (datetime.now() - perf.last_used).total_seconds() / 3600
                recency_bonus = max(0, 0.1 * (24 / max(recency_hours, 1)))  # Decay over 24 hours

                # Population size compatibility
                size_factor = 1.0
                if population_size < 10 and "crossover" in operator:
                    size_factor = 0.8  # Crossover less effective in small populations
                elif population_size > 20 and operator in ["hoist_mutation", "node_replacement"]:
                    size_factor = 1.2  # These work better in larger populations

                # Generation stage factor
                generation_factor = 1.0
                if current_generation < 3:
                    # Early generations: prefer exploration operators
                    if operator in ["mutate_condition", "swap_operators", "hunk_edit_insert"]:
                        generation_factor = 1.2
                else:
                    # Later generations: prefer exploitation operators
                    if operator in ["subtree_crossover", "hoist_mutation"]:
                        generation_factor = 1.2

                # Final score
                final_score = (base_score + context_bonus + recency_bonus) * size_factor * generation_factor

                operator_scores.append((operator, final_score, perf.confidence_score))
            else:
                # Unknown operator, neutral score
                operator_scores.append((operator, 0.5, self.min_confidence_threshold))

        # Sort by score
        operator_scores.sort(key=lambda x: x[1], reverse=True)
        best_operator, best_score, confidence = operator_scores[0]

        # Get alternative operators (top 3)
        alternatives = [(op, score) for op, score, _ in operator_scores[1:4]]

        # Calculate expected performance
        expected_performance = self._predict_performance(best_operator, context)

        # Build reasoning
        reasoning_parts = [
            f"Selected '{best_operator}' based on historical performance (effectiveness: {best_score:.2f})",
            f"Context type: {context_type}, population size: {population_size}",
            f"Operator confidence: {confidence:.2f}"
        ]

        if context_bonus > 0:
            reasoning_parts.append(f"Context bonus: +{context_bonus:.2f}")

        if recency_bonus > 0:
            reasoning_parts.append(f"Recency bonus: +{recency_bonus:.2f}")

        reasoning = ". ".join(reasoning_parts)

        return OperatorRecommendation(
            recommended_operator=best_operator,
            confidence=confidence,
            reasoning=reasoning,
            alternative_operators=alternatives,
            expected_performance=expected_performance
        )

    def _predict_performance(self, operator: str, context: Dict[str, Any]) -> float:
        """Predict expected performance for operator in context."""
        if operator not in self.operator_performance:
            return 0.5

        perf = self.operator_performance[operator]
        context_type = self._classify_context(context)

        # Base prediction from historical success
        base_prediction = perf.success_rate

        # Adjust for context
        context_adjustment = perf.context_effectiveness.get(context_type, 0.0) * 0.1

        return max(0.0, min(1.0, base_prediction + context_adjustment))

    async def get_learning_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get insights from historical learning data."""
        insights = []

        # Top performing operators
        if self.operator_performance:
            top_operators = sorted(
                self.operator_performance.values(),
                key=lambda x: x.effectiveness_score,
                reverse=True
            )[:limit]

            for op in top_operators:
                insights.append({
                    "type": "top_operator",
                    "operator": op.operator_name,
                    "effectiveness": op.effectiveness_score,
                    "success_rate": op.success_rate,
                    "total_uses": op.total_uses,
                    "context_specialization": max(op.context_effectiveness.values()) if op.context_effectiveness else 0.0
                })

        # Learning trends
        if len(self.learning_events) >= 10:
            recent_events = self.learning_events[-20:]
            success_rate_trend = sum(1 for e in recent_events if e.success) / len(recent_events)

            insights.append({
                "type": "learning_trend",
                "recent_success_rate": success_rate_trend,
                "total_events": len(self.learning_events),
                "learning_effectiveness": self._calculate_learning_effectiveness()
            })

        return insights

    def _calculate_learning_effectiveness(self) -> float:
        """Calculate how effective the learning system has been."""
        if len(self.learning_events) < 20:
            return 0.0

        # Compare early vs late performance
        early_events = self.learning_events[:10]
        late_events = self.learning_events[-10:]

        early_success = sum(1 for e in early_events if e.success) / len(early_events)
        late_success = sum(1 for e in late_events if e.success) / len(late_events)

        # Improvement indicates learning effectiveness
        return late_success - early_success

    async def _persist_learning_event(self, event: LearningEvent):
        """Persist learning event to ConPort."""
        try:
            event_data = {
                "event_id": event.event_id,
                "operator_used": event.operator_used,
                "context": event.context,
                "fitness_before": event.fitness_before,
                "fitness_after": event.fitness_after,
                "fitness_gain": event.fitness_after - event.fitness_before,
                "time_cost": event.time_cost,
                "success": event.success,
                "timestamp": event.timestamp.isoformat(),
                "population_size": event.population_size,
                "generation": event.generation,
                "workspace_id": self.workspace_id
            }

            try:
                await self.conport_client.log_custom_data(
                    category="operator_learning",
                    key=f"event_{event.event_id}",
                    value=event_data
                )
            except AttributeError:
                # ConPort client doesn't support custom data logging
                pass

        except Exception as e:
            # Log but don't fail the learning process
            print(f"Failed to persist learning event: {e}")

    async def load_historical_data(self) -> None:
        """Load historical learning data from ConPort."""
        try:
            # Load operator performance data
            try:
                perf_data = await self.conport_client.get_custom_data(
                    category="operator_performance"
                )
            except AttributeError:
                perf_data = {}

            for key, data in perf_data.items():
                if isinstance(data, dict) and "operator_name" in data:
                    operator_name = data["operator_name"]
                    self.operator_performance[operator_name] = OperatorPerformance(**data)

            # Load learning events
            try:
                event_data = await self.conport_client.get_custom_data(
                    category="operator_learning"
                )
            except AttributeError:
                event_data = {}

            for key, data in event_data.items():
                if isinstance(data, dict) and "event_id" in data:
                    # Convert timestamp string back to datetime
                    data_copy = data.copy()
                    if "timestamp" in data_copy:
                        data_copy["timestamp"] = datetime.fromisoformat(data_copy["timestamp"])

                    event = LearningEvent(**data_copy)
                    self.learning_events.append(event)

            # Sort events by timestamp and limit memory
            self.learning_events.sort(key=lambda x: x.timestamp)
            if len(self.learning_events) > self.max_events_memory:
                self.learning_events = self.learning_events[-self.max_events_memory:]

        except Exception as e:
            print(f"Failed to load historical data: {e}")

    async def export_learning_model(self) -> Dict[str, Any]:
        """Export the current learning model for analysis or backup."""
        return {
            "operator_performance": {
                name: {
                    "operator_name": perf.operator_name,
                    "total_uses": perf.total_uses,
                    "successful_uses": perf.successful_uses,
                    "average_fitness_gain": perf.average_fitness_gain,
                    "average_time_cost": perf.average_time_cost,
                    "success_rate": perf.success_rate,
                    "context_effectiveness": perf.context_effectiveness,
                    "last_used": perf.last_used.isoformat(),
                    "confidence_score": perf.confidence_score
                }
                for name, perf in self.operator_performance.items()
            },
            "learning_events_count": len(self.learning_events),
            "export_timestamp": datetime.now().isoformat(),
            "learning_effectiveness": self._calculate_learning_effectiveness()
        }