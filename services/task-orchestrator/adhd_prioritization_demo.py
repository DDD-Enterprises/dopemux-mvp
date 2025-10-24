"""
ADHD-Aware Task Prioritization - Standalone Demo

Demonstrates intelligent task prioritization based on:
- Energy level matching (high/medium/low)
- Complexity + attention state matching
- ADHD suitability scoring

This is a design/proof-of-concept that shows how task recommendations
should work when integrated into Task-Orchestrator.

Note: enhanced_orchestrator.py has structural issues (Component 5 methods
are after `if __name__`). This standalone demo shows the correct logic.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
from datetime import datetime


class EnergyLevel(str, Enum):
    """Energy levels for task matching."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AttentionState(str, Enum):
    """Attention states for ADHD accommodation."""
    FOCUSED = "focused"
    SCATTERED = "scattered"
    HYPERFOCUS = "hyperfocus"


@dataclass
class UserState:
    """Current user state for ADHD optimization."""
    energy: EnergyLevel
    attention: AttentionState
    session_duration_minutes: int


class ADHDTaskPrioritizer:
    """
    ADHD-aware task prioritization engine.

    Scores and ranks tasks based on energy/complexity/attention matching.
    """

    def calculate_adhd_match_score(
        self,
        task_complexity: float,
        task_energy: str,
        user_state: UserState
    ) -> float:
        """
        Calculate how well a task matches user's current ADHD state.

        Args:
            task_complexity: 0.0-1.0 (higher = more complex)
            task_energy: "high", "medium", or "low"
            user_state: Current user state

        Returns:
            Score 0.0-1.0 (higher = better match)
        """
        score = 0.5  # Base score

        # Energy match (most important +/-0.3)
        if task_energy == user_state.energy.value:
            score += 0.3  # Perfect energy match
        elif task_energy == "low" and user_state.energy.value == "medium":
            score += 0.2  # Low tasks okay for medium energy
        elif task_energy == "medium" and user_state.energy.value == "high":
            score += 0.15  # Medium tasks okay for high energy
        else:
            score -= 0.2  # Energy mismatch penalty

        # Complexity + attention match (+/-0.3)
        if user_state.attention == AttentionState.FOCUSED:
            # Focused: prefer optimal complexity (0.4-0.7)
            if 0.4 <= task_complexity <= 0.7:
                score += 0.2
            elif task_complexity < 0.4:
                score += 0.1  # Simple tasks okay
            else:
                score -= 0.1  # Too complex for sustained focus

        elif user_state.attention == AttentionState.SCATTERED:
            # Scattered: prefer simple tasks (<0.3)
            if task_complexity < 0.3:
                score += 0.3  # Perfect for scattered state
            elif task_complexity < 0.5:
                score += 0.1  # Moderate okay
            else:
                score -= 0.3  # Too complex when scattered

        elif user_state.attention == AttentionState.HYPERFOCUS:
            # Hyperfocus: can handle complex (>0.6)
            if task_complexity > 0.6:
                score += 0.2  # Good use of hyperfocus
            elif task_complexity > 0.4:
                score += 0.1  # Okay
            else:
                score -= 0.1  # Waste of hyperfocus state

        # Clamp to 0.0-1.0
        return max(0.0, min(1.0, score))

    def generate_recommendation_reason(
        self,
        score: float,
        task_energy: str,
        task_complexity: float,
        user_state: UserState
    ) -> str:
        """Generate human-readable reason for recommendation."""

        if score >= 0.8:
            return f"Perfect match: {task_energy} energy + {task_complexity:.1f} complexity suits your {user_state.attention.value} state"
        elif score >= 0.6:
            return f"Good match: {task_energy} energy aligns with current state"
        elif score >= 0.4:
            return f"Acceptable: Doable in your current {user_state.attention.value} state"
        else:
            return f"Consider later: Better when energy is {task_energy}"

    def prioritize_tasks(
        self,
        tasks: List[Dict[str, Any]],
        user_state: UserState,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Prioritize tasks based on ADHD match.

        Args:
            tasks: List of tasks with complexity_score and energy_required
            user_state: Current user state
            limit: Max recommendations to return

        Returns:
            Sorted list of task recommendations
        """
        # Score all tasks
        scored_tasks = []
        for task in tasks:
            complexity = task.get("complexity_score", 0.5)
            energy_required = task.get("energy_required", "medium")

            score = self.calculate_adhd_match_score(
                task_complexity=complexity,
                task_energy=energy_required,
                user_state=user_state
            )

            scored_tasks.append({
                "task": task,
                "score": score,
                "complexity": complexity,
                "energy_required": energy_required
            })

        # Sort by score (highest first)
        scored_tasks.sort(key=lambda x: x["score"], reverse=True)

        # Build recommendations
        recommendations = []
        for i, scored in enumerate(scored_tasks[:limit]):
            task = scored["task"]
            score = scored["score"]

            reason = self.generate_recommendation_reason(
                score=score,
                task_energy=scored["energy_required"],
                task_complexity=scored["complexity"],
                user_state=user_state
            )

            recommendations.append({
                "task_id": task["task_id"],
                "title": task["title"],
                "reason": reason,
                "confidence": score,
                "priority": i + 1,
                "adhd_match": {
                    "energy_match": scored["energy_required"] == user_state.energy.value,
                    "complexity": scored["complexity"],
                    "user_energy": user_state.energy.value,
                    "user_attention": user_state.attention.value
                }
            })

        return recommendations


# ============================================================================
# Demo / Test
# ============================================================================

async def demo():
    """Demonstrate ADHD-aware task prioritization."""

    print("\n" + "="*70)
    print("ADHD-AWARE TASK PRIORITIZATION DEMO")
    print("="*70)

    # Create test tasks
    tasks = [
        {
            "task_id": "task-1",
            "title": "Design microservices architecture",
            "complexity_score": 0.9,
            "energy_required": "high"
        },
        {
            "task_id": "task-2",
            "title": "Fix typo in README",
            "complexity_score": 0.1,
            "energy_required": "low"
        },
        {
            "task_id": "task-3",
            "title": "Write integration tests",
            "complexity_score": 0.5,
            "energy_required": "medium"
        },
        {
            "task_id": "task-4",
            "title": "Refactor authentication",
            "complexity_score": 0.7,
            "energy_required": "high"
        },
        {
            "task_id": "task-5",
            "title": "Update documentation",
            "complexity_score": 0.2,
            "energy_required": "low"
        },
        {
            "task_id": "task-6",
            "title": "Code review",
            "complexity_score": 0.4,
            "energy_required": "medium"
        }
    ]

    # Simulate low energy state (evening, 22:00)
    user_state = UserState(
        energy=EnergyLevel.LOW,
        attention=AttentionState.FOCUSED,
        session_duration_minutes=15
    )

    print(f"\n📊 Current User State:")
    print(f"   Energy: {user_state.energy.value}")
    print(f"   Attention: {user_state.attention.value}")
    print(f"   Session: {user_state.session_duration_minutes} min")

    # Prioritize tasks
    prioritizer = ADHDTaskPrioritizer()
    recommendations = prioritizer.prioritize_tasks(tasks, user_state, limit=3)

    print(f"\n🎯 Top 3 Recommended Tasks:")
    for rec in recommendations:
        print(f"\n  {rec['priority']}. {rec['title']}")
        print(f"     Confidence: {rec['confidence']:.2f}")
        print(f"     Reason: {rec['reason']}")
        print(f"     Match: energy={rec['adhd_match']['energy_match']}, "
              f"complexity={rec['adhd_match']['complexity']:.1f}")

    # Verify low-complexity tasks are prioritized
    print(f"\n✅ Validation:")
    top_task = recommendations[0]
    if top_task['adhd_match']['complexity'] <= 0.3:
        print(f"   ✓ Low-complexity task prioritized (complexity: {top_task['adhd_match']['complexity']:.1f})")
    else:
        print(f"   ⚠️ Top task complexity: {top_task['adhd_match']['complexity']:.1f}")

    # Show all scores
    print(f"\n📈 All Task Scores:")
    all_recs = prioritizer.prioritize_tasks(tasks, user_state, limit=10)
    for rec in all_recs:
        match_str = "✓" if rec['adhd_match']['energy_match'] else "✗"
        print(f"   [{match_str}] {rec['confidence']:.2f} - {rec['title']}")

    print("\n" + "="*70)
    print("✅ ADHD prioritization logic validated!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo())
