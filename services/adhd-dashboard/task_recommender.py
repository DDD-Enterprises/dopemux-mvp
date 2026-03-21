#!/usr/bin/env python3
"""
Smart Task Recommender - ADHD-Aware Task Selection

Recommends tasks based on current ADHD state (energy/attention).
Helps choose appropriate work for your current cognitive capacity.

ADHD Benefit: "Should I work on this now?" answered automatically
"""

import uvicorn
from datetime import datetime

import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.shared.brand_voice import StatusChip, brand_log, brand_text, voice_header

logger = logging.getLogger(__name__)


class TaskRecommender:
    """
    Recommends tasks based on ADHD state.

    Queries ADHD Engine to assess task suitability.
    """

    def __init__(
        self,
        adhd_engine_url: str = "http://localhost:8095",
        user_id: str = "default",
        api_key: Optional[str] = None,
    ):
        """
        Initialize task recommender.

        Args:
            adhd_engine_url: ADHD Engine URL
            user_id: User ID
        """
        self.adhd_engine_url = adhd_engine_url
        self.user_id = user_id
        self.api_key = api_key or os.getenv("ADHD_ENGINE_API_KEY")

    @property
    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

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
            async with aiohttp.ClientSession(headers=self._headers) as session:
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
                        logger.error(brand_log(f"Task assessment failed: {error}", chip=StatusChip.BLOCKER))
                        return {"error": error}

        except Exception as e:
            logger.error(brand_log(f"Failed to assess task: {e}", chip=StatusChip.BLOCKER))
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
            async with aiohttp.ClientSession(headers=self._headers) as session:
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
                "status_chip": "LIVE",
                "tone": "live",
                "voice_header": voice_header("Task Recommender"),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(brand_log(f"Failed to get recommendation: {e}", chip=StatusChip.BLOCKER))
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
                "suggestion": brand_text("Perfect coordinates for complex ritual execution. High energy + deep focus detected.", chip=StatusChip.LIVE),
                "task_types": ["Architecture design", "Complex refactoring", "New feature implementation"],
                "avoid": []
            }

        # Medium energy + focused = Good for normal work
        elif energy == "medium" and attention == "focused":
            return {
                "work_type": "standard_coding",
                "suggestion": brand_text("Stable operational state. Good time for standard development rituals.", chip=StatusChip.LOGGED),
                "task_types": ["Bug fixes", "Code reviews", "Documentation", "Unit tests"],
                "avoid": ["Complex architecture decisions"]
            }

        # Low energy or scattered = Simple tasks only
        elif energy in ["low", "very_low"] or attention in ["scattered", "transitioning"]:
            return {
                "work_type": "simple_tasks",
                "suggestion": brand_text("Cognitive signal low or scattered. Limit focus to low-complexity maintenance tasks.", chip=StatusChip.EDGE),
                "task_types": ["Code cleanup", "Minor bug fixes", "Documentation updates", "Code reading"],
                "avoid": ["Complex coding", "Architecture design", "Deep debugging"]
            }

        # Overwhelmed = Take a break!
        elif attention == "overwhelmed":
            return {
                "work_type": "break_needed",
                "suggestion": brand_text("Cognitive overwhelm detected. Halt rituals immediately. Initiate 10-minute reset sequence.", chip=StatusChip.BLOCKER),
                "task_types": ["Take a walk", "Hydrate", "Short break"],
                "avoid": ["Any coding work"]
            }

        # Default fallback
        else:
            return {
                "work_type": "moderate_tasks",
                "suggestion": brand_text("Moderate cognitive state. Select medium-complexity rituals.", chip=StatusChip.LOGGED),
                "task_types": ["Bug fixes", "Refactoring", "Tests"],
                "avoid": ["Very complex work"]
            }


if __name__ == "__main__":
    logger.info(brand_log("TaskRecommender module loaded. Import TaskRecommender in a service entrypoint.", chip=StatusChip.LIVE))
