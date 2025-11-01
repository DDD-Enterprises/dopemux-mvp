"""
Energy Trends Service - Energy Level Pattern Analysis

Analyzes energy level patterns over time to provide predictive insights
and recommendations for optimal work scheduling.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime, timedelta

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EnergyTrendsAnalyzer:
    """
    Analyzes energy level patterns and trends.

    Collects energy data over time and provides predictive insights
    for optimal work scheduling and ADHD accommodation.
    """

    def __init__(self, redis_url: str, user_id: str):
        self.redis_url = redis_url
        self.user_id = user_id
        self.redis: redis.Redis = None

        # Analysis configuration
        self.analysis_window_hours = int(os.getenv("ANALYSIS_WINDOW_HOURS", "24"))
        self.prediction_enabled = os.getenv("PREDICTION_ENABLED", "true").lower() == "true"

        # Data storage
        self.energy_readings: List[Dict[str, Any]] = []

    async def initialize(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(self.redis_url)
        logger.info("Energy Trends Analyzer initialized")

    async def process_energy_reading(self, energy_data: Dict[str, Any]):
        """
        Process new energy level reading.

        Args:
            energy_data: Energy reading with level, timestamp, context
        """
        try:
            reading = {
                "timestamp": energy_data.get("timestamp", asyncio.get_event_loop().time()),
                "energy_level": energy_data.get("energy_level"),
                "attention_state": energy_data.get("attention_state"),
                "context": energy_data.get("context", {}),
                "user_id": self.user_id
            }

            self.energy_readings.append(reading)

            # Keep only recent readings
            cutoff_time = asyncio.get_event_loop().time() - (self.analysis_window_hours * 3600)
            self.energy_readings = [
                reading for reading in self.energy_readings
                if reading["timestamp"] > cutoff_time
            ]

            logger.debug(f"Processed energy reading: {energy_data.get('energy_level')}")

            # Analyze trends periodically
            if len(self.energy_readings) % 10 == 0:  # Every 10 readings
                await self._analyze_energy_trends()

        except Exception as e:
            logger.error(f"Error processing energy reading: {e}")

    async def _analyze_energy_trends(self):
        """Analyze energy level trends and patterns."""
        try:
            if len(self.energy_readings) < 5:
                return  # Need minimum data for analysis

            # Calculate energy level distribution
            energy_levels = [reading["energy_level"] for reading in self.energy_readings]
            level_counts = defaultdict(int)

            for level in energy_levels:
                if isinstance(level, str):
                    level_counts[level] += 1
                elif isinstance(level, (int, float)):
                    # Convert numeric to categorical
                    if level >= 0.8:
                        level_counts["high"] += 1
                    elif level >= 0.6:
                        level_counts["medium"] += 1
                    else:
                        level_counts["low"] += 1

            # Find most common energy level
            most_common_level = max(level_counts.keys(), key=lambda k: level_counts[k])

            # Generate insights
            insights = {
                "most_common_energy_level": most_common_level,
                "total_readings": len(self.energy_readings),
                "analysis_window_hours": self.analysis_window_hours,
                "energy_distribution": dict(level_counts),
                "recommendations": self._generate_energy_recommendations(level_counts)
            }

            # Store insights in Redis
            await self.redis.setex(
                f"energy:insights:{self.user_id}",
                3600,  # 1 hour TTL
                json.dumps(insights)
            )

            logger.info(f"Generated energy insights: {most_common_level} most common")

        except Exception as e:
            logger.error(f"Error analyzing energy trends: {e}")

    def _generate_energy_recommendations(self, level_counts: Dict[str, int]) -> List[str]:
        """
        Generate energy-based recommendations.

        Args:
            level_counts: Distribution of energy levels

        Returns:
            List of recommendations
        """
        recommendations = []

        total_readings = sum(level_counts.values())

        if level_counts.get("low", 0) / total_readings > 0.6:
            recommendations.append("High proportion of low energy periods - consider work schedule optimization")
            recommendations.append("Consider starting work sessions during higher energy periods")

        if level_counts.get("high", 0) / total_readings > 0.7:
            recommendations.append("Consistently high energy - excellent for complex tasks")
            recommendations.append("Consider tackling high-complexity work during peak energy periods")

        if len(level_counts) >= 3:  # Good energy variation
            recommendations.append("Good energy level variation - adaptive work scheduling recommended")

        return recommendations

    async def get_energy_insights(self) -> Dict[str, Any]:
        """Get current energy insights."""
        try:
            insights_data = await self.redis.get(f"energy:insights:{self.user_id}")
            if insights_data:
                return json.loads(insights_data)
            else:
                return {"status": "no_insights_available"}
        except Exception as e:
            logger.error(f"Error getting energy insights: {e}")
            return {"error": str(e)}


async def start_energy_trends_service(user_id: str = "default"):
    """
    Start energy trends analysis service.

    Monitors energy patterns and generates predictive insights.
    """
    redis_url = os.getenv("REDIS_URL", "redis://redis-primary:6379")

    analyzer = EnergyTrendsAnalyzer(redis_url, user_id)
    await analyzer.initialize()

    redis_client = redis.from_url(redis_url)

    logger.info("Energy Trends Service started")

    while True:
        try:
            # Listen for energy reading events
            messages = await redis_client.xread(
                {"dopemux:events": "$"},
                block=1000,
                count=10
            )

            for stream, message_list in messages:
                for message_id, message_data in message_list:
                    try:
                        event_type = message_data.get("type", "")
                        event_data = message_data.get("data", {})

                        # Process energy readings
                        if event_type == "energy.level.reported":
                            await analyzer.process_energy_reading(event_data)

                        # Acknowledge message
                        await redis_client.xack("dopemux:events", f"energy-trends-{user_id}", message_id)

                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Energy trends service error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    user_id = os.getenv("USER_ID", "default")
    asyncio.run(start_energy_trends_service(user_id))