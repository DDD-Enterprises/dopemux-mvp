"""
Dynamic Recommendation Count - Week 5 Feature

Adapts number of task recommendations (1-4) based on cognitive load state.

Research Foundation:
- 2024 Choice Overload Meta-Analysis: 3-4 options optimal for ADHD
- 2025 Cognitive Load Study: Reduce choices when overwhelmed
- ADHD Best Practice: Progressive disclosure, avoid decision paralysis

Strategy:
- Low load (0.0-0.3): 4 recommendations (high capacity)
- Medium load (0.3-0.6): 3 recommendations (balanced)
- High load (0.6-0.8): 2 recommendations (reduced choices)
- Critical load (0.8-1.0): 1 recommendation (minimal decision)

Additional Factors:
- Scattered attention: -1 recommendation
- Hyperfocused: +1 recommendation (can handle more)

Created: 2025-10-20
Component: 6 - Phase 2 (Week 5)
"""

from enum import Enum
from typing import Dict, Any


class AttentionLevel(Enum):
    """Attention level categories."""
    SCATTERED = "scattered"
    TRANSITIONING = "transitioning"
    FOCUSED = "focused"
    HYPERFOCUSED = "hyperfocused"


class EnergyLevel(Enum):
    """Energy level categories."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HYPERFOCUS = "hyperfocus"


class DynamicRecommendationCounter:
    """
    Dynamically adjusts recommendation count (1-4) based on ADHD state.
    
    Core principle: Reduce choices when overwhelmed, expand when capable.
    
    Usage:
        counter = DynamicRecommendationCounter()
        
        count = counter.get_recommendation_count(
            cognitive_load=0.75,
            attention_level="scattered",
            energy_level="low"
        )
        # Returns: 1 (high load + scattered = minimal choices)
        
        count = counter.get_recommendation_count(
            cognitive_load=0.4,
            attention_level="focused",
            energy_level="high"
        )
        # Returns: 3 (balanced state)
    """
    
    # Base count from cognitive load
    LOAD_TO_COUNT = {
        # (min_load, max_load): base_count
        (0.0, 0.3): 4,    # Low load - high capacity
        (0.3, 0.6): 3,    # Medium load - balanced
        (0.6, 0.8): 2,    # High load - reduced choices
        (0.8, 1.0): 1     # Critical load - minimal decision
    }
    
    # Attention level modifiers
    ATTENTION_MODIFIERS = {
        AttentionLevel.SCATTERED.value: -1,        # Reduce choices when scattered
        AttentionLevel.TRANSITIONING.value: 0,     # No change
        AttentionLevel.FOCUSED.value: 0,           # No change
        AttentionLevel.HYPERFOCUSED.value: +1      # Can handle more when hyperfocused
    }
    
    # Energy level modifiers (optional)
    ENERGY_MODIFIERS = {
        EnergyLevel.VERY_LOW.value: -1,
        EnergyLevel.LOW.value: 0,
        EnergyLevel.MEDIUM.value: 0,
        EnergyLevel.HIGH.value: 0,
        EnergyLevel.HYPERFOCUS.value: +1
    }
    
    def __init__(
        self,
        min_count: int = 1,
        max_count: int = 4,
        use_energy_modifier: bool = False  # Energy is already in cognitive load
    ):
        """
        Initialize dynamic counter.
        
        Args:
            min_count: Minimum recommendations (default 1)
            max_count: Maximum recommendations (default 4)
            use_energy_modifier: Apply energy modifier (default False)
        """
        self.min_count = min_count
        self.max_count = max_count
        self.use_energy_modifier = use_energy_modifier
        
        # Statistics
        self._count_distribution = {1: 0, 2: 0, 3: 0, 4: 0}
        self._total_calls = 0
    
    def get_recommendation_count(
        self,
        cognitive_load: float,
        attention_level: str = "normal",
        energy_level: str = "medium"
    ) -> int:
        """
        Calculate adaptive recommendation count.
        
        Args:
            cognitive_load: Current cognitive load (0.0-1.0)
            attention_level: Current attention state
            energy_level: Current energy state
        
        Returns:
            Recommendation count (1-4)
        """
        # Step 1: Base count from cognitive load
        base_count = self._get_base_count_from_load(cognitive_load)
        
        # Step 2: Adjust for attention level
        attention_modifier = self.ATTENTION_MODIFIERS.get(attention_level, 0)
        
        # Step 3: Adjust for energy level (if enabled)
        energy_modifier = 0
        if self.use_energy_modifier:
            energy_modifier = self.ENERGY_MODIFIERS.get(energy_level, 0)
        
        # Step 4: Compute final count
        final_count = base_count + attention_modifier + energy_modifier
        
        # Step 5: Clamp to valid range
        final_count = max(self.min_count, min(self.max_count, final_count))
        
        # Track statistics
        self._total_calls += 1
        self._count_distribution[final_count] = self._count_distribution.get(final_count, 0) + 1
        
        return final_count
    
    def _get_base_count_from_load(self, cognitive_load: float) -> int:
        """
        Map cognitive load to base recommendation count.
        
        Args:
            cognitive_load: Load value (0.0-1.0)
        
        Returns:
            Base count (1-4)
        """
        for (min_load, max_load), count in self.LOAD_TO_COUNT.items():
            if min_load <= cognitive_load <= max_load:
                return count
        
        # Fallback (shouldn't happen)
        return 3  # Default to medium
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_calls": self._total_calls,
            "count_distribution": self._count_distribution.copy(),
            "average_count": (
                sum(count * freq for count, freq in self._count_distribution.items()) 
                / max(self._total_calls, 1)
            ) if self._total_calls > 0 else 3.0,
            "config": {
                "min_count": self.min_count,
                "max_count": self.max_count,
                "use_energy_modifier": self.use_energy_modifier
            }
        }


# Convenience function for quick usage
def get_adaptive_recommendation_count(
    cognitive_load: float,
    attention_level: str = "normal",
    energy_level: str = "medium"
) -> int:
    """
    Quick function to get adaptive count without creating counter instance.
    
    Args:
        cognitive_load: Current cognitive load (0.0-1.0)
        attention_level: Current attention state
        energy_level: Current energy state
    
    Returns:
        Recommended task count (1-4)
    
    Example:
        count = get_adaptive_recommendation_count(
            cognitive_load=0.75,
            attention_level="scattered"
        )
        # Returns: 1
    """
    counter = DynamicRecommendationCounter()
    return counter.get_recommendation_count(
        cognitive_load=cognitive_load,
        attention_level=attention_level,
        energy_level=energy_level
    )
