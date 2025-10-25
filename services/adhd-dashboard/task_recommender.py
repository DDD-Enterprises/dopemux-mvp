#!/usr/bin/env python3
"""
Smart Task Recommender - ADHD-Aware Task Selection

Recommends tasks based on current ADHD state (energy/attention).
Helps choose appropriate work for your current cognitive capacity.

ADHD Benefit: "Should I work on this now?" answered automatically
"""

import asyncio
import logging
import aiohttp
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TaskRecommender:
    """
    Recommends tasks based on ADHD state.

    Queries ADHD Engine to assess task suitability.
    """

    def __init__(
        self,
        adhd_engine_url: str = "http://localhost:8095",
        user_id: str = "hue"
    ):
        """
        Initialize task recommender.

        Args:
            adhd_engine_url: ADHD Engine URL
            user_id: User ID
        """
        self.adhd_engine_url = adhd_engine_url
        self.user_id = user_id

    async def assess_task(
        self,
        task_id: str,
        task_description: str,
        complexity: float,
        estimated_minutes: int,
        requires_deep_focus: bool = False
    ) -> Dict[str, Any]:
        """
        Assess if task is suitable for current ADHD state.

        Args:
            task_id: Task identifier
            task_description: Task description
            complexity: Task complexity (0.0-1.0)
            estimated_minutes: Estimated duration
            requires_deep_focus: Whether task needs deep focus

        Returns:
            Assessment with suitability score and recommendations
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "user_id": self.user_id,
                    "task_id": task_id,
                    "task_data": {
                        "description": task_description,
                        "complexity_score": complexity,
                        "estimated_minutes": estimated_minutes,
                        "requires_deep_focus": requires_deep_focus
                    }
                }

                async with session.post(
                    f"{self.adhd_engine_url}/api/v1/assess-task",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error = await response.text()
                        logger.error(f"Task assessment failed: {error}")
                        return {"error": error}

        except Exception as e:
            logger.error(f"Failed to assess task: {e}")
            return {"error": str(e)}

    async def recommend_from_list(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank tasks by suitability for current ADHD state.

        Args:
            tasks: List of task dicts with id, description, complexity, duration

        Returns:
            Sorted list of tasks with suitability scores
        """
        assessments = []

        for task in tasks:
            assessment = await self.assess_task(
                task_id=task.get("id", "unknown"),
                task_description=task.get("description", ""),
                complexity=task.get("complexity", 0.5),
                estimated_minutes=task.get("estimated_minutes", 25),
                requires_deep_focus=task.get("requires_deep_focus", False)
            )

            if "error" not in assessment:
                assessments.append({
                    "task": task,
                    "suitability": assessment.get("suitability_score", 0.5),
                    "recommendations": assessment.get("recommendations", [])
                })

        # Sort by suitability (highest first)
        assessments.sort(key=lambda x: x["suitability"], reverse=True)

        return assessments

    async def get_current_recommendation(self) -> Dict[str, Any]:
        """
        Get recommendation for what to work on now.

        Returns:
            Recommendation with energy/attention context
        """
        try:
            # Get current ADHD state
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.adhd_engine_url}/api/v1/energy-level/{self.user_id}") as response:
                    energy_data = await response.json() if response.status == 200 else {}

                async with session.get(f"{self.adhd_engine_url}/api/v1/attention-state/{self.user_id}") as response:
                    attention_data = await response.json() if response.status == 200 else {}

            energy = energy_data.get("energy_level", "unknown")
            attention = attention_data.get("attention_state", "unknown")

            # Generate recommendation
            recommendation = self._generate_recommendation(energy, attention)

            return {
                "energy": energy,
                "attention": attention,
                "recommendation": recommendation,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get recommendation: {e}")
            return {"error": str(e)}

    def _generate_recommendation(self, energy: str, attention: str) -> Dict[str, Any]:
        """
        Generate task recommendation based on ADHD state.

        Args:
            energy: Energy level (high/medium/low)
            attention: Attention state (focused/scattered/transitioning)

        Returns:
            Recommendation dict
        """
        # High energy + focused = Best time for complex work
        if energy in ["high", "hyperfocus"] and attention == "focused":
            return {
                "work_type": "complex_coding",
                "suggestion": "Perfect time for challenging tasks! High energy + deep focus.",
                "task_types": ["Architecture design", "Complex refactoring", "New feature implementation"],
                "avoid": []
            }

        # Medium energy + focused = Good for normal work
        elif energy == "medium" and attention == "focused":
            return {
                "work_type": "standard_coding",
                "suggestion": "Good time for regular development work.",
                "task_types": ["Bug fixes", "Code reviews", "Documentation", "Unit tests"],
                "avoid": ["Complex architecture decisions"]
            }

        # Low energy or scattered = Simple tasks only
        elif energy in ["low", "very_low"] or attention in ["scattered", "transitioning"]:
            return {
                "work_type": "simple_tasks",
                "suggestion": "Low energy or scattered attention. Stick to simple tasks.",
                "task_types": ["Code cleanup", "Minor bug fixes", "Documentation updates", "Code reading"],
                "avoid": ["Complex coding", "Architecture design", "Deep debugging"]
            }

        # Overwhelmed = Take a break!
        elif attention == "overwhelmed":
            return {
                "work_type": "break_needed",
                "suggestion": "You're overwhelmed. Take a break before continuing.",
                "task_types": ["Take a walk", "Hydrate", "Short break"],
                "avoid": ["Any coding work"]
            }

        # Default fallback
        else:
            return {
                "work_type": "moderate_tasks",
                "suggestion": "Moderate state. Choose medium-complexity tasks.",
                "task_types": ["Bug fixes", "Refactoring", "Tests"],
                "avoid": ["Very complex work"]
            }


if __name__ == "__main__":
    logger.info("Starting ADHD Dashboard...")
    uvicorn.run(app, host="0.0.0.0", port=8097, log_level="info")
