"""
Query Complexity Budgets for Integration Bridge

Prevents expensive pattern detection queries from overwhelming the system:
- Score queries based on complexity (patterns, events, graph depth)
- Budget: 1000 complexity points per user per minute
- Reject expensive queries or return cached results when budget exceeded

Features:
- Pattern-based complexity scoring
- Per-user budget tracking
- Redis-backed budget counters
- Graceful degradation (return cached results)
- ADHD-friendly: Suggests simpler alternatives
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class ComplexityBudgetExceeded(Exception):
    """Exception raised when complexity budget is exceeded"""

    def __init__(self, points_used: int, budget: int, retry_after_seconds: int):
        self.points_used = points_used
        self.budget = budget
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Complexity budget exceeded ({points_used}/{budget} points). "
            f"Retry after {retry_after_seconds} seconds or use simpler query."
        )


class ComplexityScorer:
    """
    Scores query complexity and enforces budgets.

    Complexity Scoring:
    - Base: 10 points per pattern detector
    - Events: 1 point per 10 events analyzed
    - Graph depth: 5 points per hop (future: when graph queries added)

    Budget: 1000 points per user per minute

    Example Queries:
    - Simple (1 pattern, 100 events): 10 + 10 = 20 points
    - Medium (3 patterns, 500 events): 30 + 50 = 80 points
    - Complex (7 patterns, 1000 events): 70 + 100 = 170 points
    - Heavy (7 patterns, 5000 events, depth 3): 70 + 500 + 15 = 585 points
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        budget_per_minute: int = 1000,
        window_seconds: int = 60
    ):
        """
        Initialize complexity scorer.

        Args:
            redis_client: Async Redis client for budget tracking
            budget_per_minute: Complexity point budget per user per minute
            window_seconds: Budget window in seconds (default: 60)
        """
        self.redis_client = redis_client
        self.budget_per_minute = budget_per_minute
        self.window_seconds = window_seconds

        # Complexity weights
        self.pattern_base_cost = 10  # Per pattern detector
        self.events_cost_per_10 = 1  # Per 10 events analyzed
        self.graph_hop_cost = 5  # Per graph traversal hop

        # Metrics
        self.queries_scored = 0
        self.budgets_exceeded = 0
        self.total_complexity_points = 0

    def score_pattern_query(
        self,
        pattern_count: int,
        event_count: int,
        graph_depth: int = 0
    ) -> int:
        """
        Calculate complexity score for pattern detection query.

        Args:
            pattern_count: Number of pattern detectors to run (1-7)
            event_count: Number of events to analyze
            graph_depth: Graph traversal depth (future feature)

        Returns:
            Complexity score in points
        """
        score = 0

        # Base cost per pattern
        score += pattern_count * self.pattern_base_cost

        # Event processing cost
        score += (event_count // 10) * self.events_cost_per_10

        # Graph traversal cost (future)
        if graph_depth > 0:
            score += graph_depth * self.graph_hop_cost

        self.queries_scored += 1
        self.total_complexity_points += score

        return score

    async def check_budget(
        self,
        user_id: str,
        complexity_points: int
    ) -> Tuple[bool, int, int]:
        """
        Check if user has budget for query complexity.

        Args:
            user_id: User identifier
            complexity_points: Points required for query

        Returns:
            Tuple of (allowed: bool, points_used: int, retry_after: int)
        """
        try:
            key = f"complexity:budget:{user_id}"
            current_time = time.time()
            window_start = current_time - self.window_seconds

            # Remove old entries
            await self.redis_client.zremrangebyscore(key, '-inf', window_start)

            # Sum current usage
            entries = await self.redis_client.zrange(key, 0, -1, withscores=True)
            current_usage = sum(float(entry[0]) for entry in entries)

            # Check if new query would exceed budget
            if current_usage + complexity_points > self.budget_per_minute:
                self.budgets_exceeded += 1

                # Calculate retry_after based on oldest entry
                if entries:
                    oldest_timestamp = entries[0][1]
                    retry_after = int(oldest_timestamp + self.window_seconds - current_time) + 1
                else:
                    retry_after = self.window_seconds

                logger.warning(
                    f"Budget exceeded for {user_id}: "
                    f"{current_usage + complexity_points}/{self.budget_per_minute} points"
                )

                return False, int(current_usage), max(1, retry_after)

            # Add query to budget
            await self.redis_client.zadd(
                key,
                {str(complexity_points): current_time}
            )

            # Set expiry
            await self.redis_client.expire(key, self.window_seconds + 10)

            return True, int(current_usage + complexity_points), 0

        except Exception as e:
            logger.error(f"Budget check failed: {e}")
            # Fail open - allow query if Redis unavailable
            return True, 0, 0

    async def get_current_budget_usage(self, user_id: str) -> Dict[str, int]:
        """
        Get current budget usage for user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with usage, budget, remaining
        """
        try:
            key = f"complexity:budget:{user_id}"
            current_time = time.time()
            window_start = current_time - self.window_seconds

            # Clean up old entries
            await self.redis_client.zremrangebyscore(key, '-inf', window_start)

            # Sum current usage
            entries = await self.redis_client.zrange(key, 0, -1, withscores=True)
            current_usage = sum(float(entry[0]) for entry in entries)

            return {
                "used": int(current_usage),
                "budget": self.budget_per_minute,
                "remaining": max(0, self.budget_per_minute - int(current_usage)),
                "window_seconds": self.window_seconds
            }

        except Exception as e:
            logger.error(f"Failed to get budget usage: {e}")
            return {
                "used": 0,
                "budget": self.budget_per_minute,
                "remaining": self.budget_per_minute,
                "window_seconds": self.window_seconds
            }

    def suggest_simpler_query(self, complexity_points: int) -> List[str]:
        """
        Suggest simpler query alternatives.

        Args:
            complexity_points: Complexity of rejected query

        Returns:
            List of suggestions to reduce complexity
        """
        suggestions = []

        if complexity_points > 500:
            suggestions.append("Reduce event window (analyze last 30 min instead of 60 min)")
            suggestions.append("Run fewer pattern detectors (specify 2-3 instead of all 7)")

        if complexity_points > 300:
            suggestions.append("Use cached results from recent pattern detection")
            suggestions.append("Filter events by specific agent (reduce event count)")

        if complexity_points > 100:
            suggestions.append("Limit analysis to high-priority patterns only")

        suggestions.append("Wait for budget to reset (check budget usage)")

        return suggestions

    def get_metrics(self) -> Dict[str, Any]:
        """Get complexity scorer metrics"""
        avg_complexity = (
            self.total_complexity_points / self.queries_scored
            if self.queries_scored > 0
            else 0
        )

        exceeded_rate = (
            (self.budgets_exceeded / self.queries_scored * 100)
            if self.queries_scored > 0
            else 0.0
        )

        return {
            "queries_scored": self.queries_scored,
            "budgets_exceeded": self.budgets_exceeded,
            "exceeded_rate_percent": round(exceeded_rate, 2),
            "total_complexity_points": self.total_complexity_points,
            "average_complexity": round(avg_complexity, 2),
            "budget_per_minute": self.budget_per_minute,
            "pattern_base_cost": self.pattern_base_cost,
            "events_cost_per_10": self.events_cost_per_10
        }

    def reset_metrics(self):
        """Reset metrics counters"""
        self.queries_scored = 0
        self.budgets_exceeded = 0
        self.total_complexity_points = 0
