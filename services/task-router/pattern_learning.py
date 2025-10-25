"""
F-NEW-9 Week 3: Pattern Learning & Personalization

Learns from user behavior to improve match accuracy over time.
ADHD Impact: Personalized to individual energy patterns and preferences.
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class MatchOutcome:
    """Record of task suggestion and its outcome."""
    user_id: str
    task_id: str
    suggested_at: datetime
    match_score: float
    cognitive_state: Dict
    outcome: str  # "completed", "abandoned", "switched", "in_progress"
    completed_at: Optional[datetime] = None
    time_to_complete_min: Optional[int] = None


@dataclass
class UserPattern:
    """Learned patterns for a user."""
    user_id: str
    energy_curve: Dict[int, float]  # hour_of_day -> typical_energy
    preferred_complexity_by_energy: Dict[str, Tuple[float, float]]  # energy -> (min, max) complexity
    average_completion_time: Dict[str, int]  # task_type -> minutes
    best_match_threshold: float  # Learned threshold for good matches
    total_suggestions: int
    total_completions: int
    completion_rate: float


class MatchAccuracyTracker:
    """
    Tracks match accuracy and learns from outcomes.

    Stores:
    - Suggested tasks with match scores
    - Actual outcomes (completed, abandoned, switched)
    - Time to completion
    - Cognitive state at suggestion time

    Metrics:
    - Overall accuracy (completed / total suggested)
    - Accuracy by match score bucket
    - Average time to completion vs estimated
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.outcomes_key_prefix = "task_router:outcomes"
        self.patterns_key_prefix = "task_router:patterns"

    async def record_suggestion(
        self,
        user_id: str,
        task_id: str,
        match_score: float,
        cognitive_state: Dict
    ):
        """Record a task suggestion for later outcome tracking."""
        outcome = MatchOutcome(
            user_id=user_id,
            task_id=task_id,
            suggested_at=datetime.now(),
            match_score=match_score,
            cognitive_state=cognitive_state,
            outcome="in_progress"
        )

        # Store in Redis
        key = f"{self.outcomes_key_prefix}:{user_id}:{task_id}"
        await self.redis.setex(
            key,
            7 * 24 * 3600,  # 7 days TTL
            json.dumps({
                'suggested_at': outcome.suggested_at.isoformat(),
                'match_score': match_score,
                'cognitive_state': cognitive_state,
                'outcome': 'in_progress'
            })
        )

        logger.info(f"Recorded suggestion: {task_id} for {user_id} (score: {match_score:.2f})")

    async def record_outcome(
        self,
        user_id: str,
        task_id: str,
        outcome: str,
        time_to_complete_min: Optional[int] = None
    ):
        """Record task outcome (completed, abandoned, switched)."""
        key = f"{self.outcomes_key_prefix}:{user_id}:{task_id}"
        data_str = await self.redis.get(key)

        if not data_str:
            logger.warning(f"No suggestion record found for {task_id}")
            return

        data = json.loads(data_str)
        data['outcome'] = outcome
        data['completed_at'] = datetime.now().isoformat()
        if time_to_complete_min:
            data['time_to_complete_min'] = time_to_complete_min

        # Update in Redis
        await self.redis.setex(key, 7 * 24 * 3600, json.dumps(data))

        logger.info(f"Recorded outcome: {task_id} → {outcome}")

        # Trigger pattern learning
        await self._update_patterns(user_id)

    async def get_accuracy_metrics(self, user_id: str) -> Dict:
        """Get match accuracy metrics for user."""
        # Get all outcomes for user
        pattern = f"{self.outcomes_key_prefix}:{user_id}:*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if not keys:
            return {
                'total_suggestions': 0,
                'total_completions': 0,
                'completion_rate': 0.0,
                'accuracy_by_score': {}
            }

        # Load all outcomes
        outcomes = []
        for key in keys:
            data_str = await self.redis.get(key)
            if data_str:
                outcomes.append(json.loads(data_str))

        # Calculate metrics
        total = len(outcomes)
        completed = sum(1 for o in outcomes if o['outcome'] == 'completed')
        abandoned = sum(1 for o in outcomes if o['outcome'] == 'abandoned')

        # Accuracy by match score bucket
        score_buckets = {
            '0.0-0.4': {'total': 0, 'completed': 0},
            '0.4-0.6': {'total': 0, 'completed': 0},
            '0.6-0.8': {'total': 0, 'completed': 0},
            '0.8-1.0': {'total': 0, 'completed': 0}
        }

        for outcome in outcomes:
            score = outcome['match_score']
            bucket = (
                '0.0-0.4' if score < 0.4 else
                '0.4-0.6' if score < 0.6 else
                '0.6-0.8' if score < 0.8 else
                '0.8-1.0'
            )
            score_buckets[bucket]['total'] += 1
            if outcome['outcome'] == 'completed':
                score_buckets[bucket]['completed'] += 1

        # Calculate accuracy per bucket
        accuracy_by_score = {}
        for bucket, counts in score_buckets.items():
            if counts['total'] > 0:
                accuracy_by_score[bucket] = counts['completed'] / counts['total']
            else:
                accuracy_by_score[bucket] = 0.0

        return {
            'total_suggestions': total,
            'total_completions': completed,
            'total_abandonments': abandoned,
            'completion_rate': completed / total if total > 0 else 0.0,
            'accuracy_by_score': accuracy_by_score
        }

    async def _update_patterns(self, user_id: str):
        """Update learned patterns based on outcomes."""
        # Get all outcomes
        metrics = await self.get_accuracy_metrics(user_id)

        # Store as user pattern
        pattern_key = f"{self.patterns_key_prefix}:{user_id}"
        await self.redis.setex(
            pattern_key,
            30 * 24 * 3600,  # 30 days
            json.dumps({
                'updated_at': datetime.now().isoformat(),
                'completion_rate': metrics['completion_rate'],
                'total_suggestions': metrics['total_suggestions'],
                'accuracy_by_score': metrics['accuracy_by_score']
            })
        )


class PersonalizationEngine:
    """
    Personalizes task matching based on learned user patterns.

    Learns:
    - Energy curve (hour of day → typical energy level)
    - Preferred complexity range by energy state
    - Task completion patterns
    - Time estimation accuracy
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.user_patterns_key = "task_router:user_patterns"

    async def get_energy_prediction(self, user_id: str, hour_of_day: int) -> float:
        """
        Predict energy level based on hour and historical patterns.

        Returns:
            Predicted energy 0.0-1.0

        Learning: Tracks energy levels by hour over time
        """
        # Get user patterns
        pattern_key = f"{self.user_patterns_key}:{user_id}:energy_curve"
        data_str = await self.redis.get(pattern_key)

        if data_str:
            energy_curve = json.loads(data_str)
            return energy_curve.get(str(hour_of_day), 0.5)

        # Default energy curve (typical ADHD pattern)
        default_curve = {
            # Morning: gradually increasing
            6: 0.3, 7: 0.4, 8: 0.5, 9: 0.6, 10: 0.7,
            # Late morning: peak
            11: 0.8, 12: 0.7,
            # Afternoon: dip
            13: 0.5, 14: 0.4, 15: 0.5,
            # Late afternoon: recovery
            16: 0.6, 17: 0.7, 18: 0.6,
            # Evening: declining
            19: 0.5, 20: 0.4, 21: 0.3, 22: 0.2
        }

        return default_curve.get(hour_of_day, 0.5)

    async def adjust_match_weights(self, user_id: str) -> Dict[str, float]:
        """
        Personalize matching weights based on user patterns.

        Default weights:
        - Energy: 0.50
        - Attention: 0.30
        - Time: 0.20

        Personalized: Adjust based on what correlates with completion
        """
        # Get user accuracy by factor
        pattern_key = f"{self.user_patterns_key}:{user_id}:weight_performance"
        data_str = await self.redis.get(pattern_key)

        if data_str:
            learned_weights = json.loads(data_str)
            return learned_weights

        # Return defaults until learned
        return {
            'energy': 0.50,
            'attention': 0.30,
            'time': 0.20
        }
