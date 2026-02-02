"""
Energy Trend Visualizer - Track Energy Patterns Over Time

Tracks energy levels throughout the day/week and identifies patterns.
Helps optimize work schedule based on natural energy rhythms.

ADHD Benefit: Know your peak hours, schedule hard work accordingly
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import aiohttp

logger = logging.getLogger(__name__)


class EnergyTrendVisualizer:
    """
    Visualizes energy trends and identifies peak productivity hours.
    """

    def __init__(
        self,
        adhd_engine_url: str = "http://localhost:8095",
        user_id: str = "hue"
    ):
        """
        Initialize energy trend visualizer.

        Args:
            adhd_engine_url: ADHD Engine URL
            user_id: User ID
        """
        self.adhd_engine_url = adhd_engine_url
        self.user_id = user_id

    async def get_current_energy(self) -> str:
        """Get current energy level"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.adhd_engine_url}/api/v1/energy-level/{self.user_id}",
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("energy_level", "unknown")
                    return "unknown"

        except Exception as e:
            logger.error(f"Failed to get energy: {e}")
            return "unknown"

    def _energy_to_bar(self, energy: str, width: int = 20) -> str:
        """Convert energy level to visual bar"""
        energy_map = {
            "hyperfocus": (20, "█"),
            "high": (15, "▓"),
            "medium": (10, "▒"),
            "low": (5, "░"),
            "very_low": (2, "·"),
            "unknown": (0, " ")
        }

        bar_len, char = energy_map.get(energy, (0, " "))
        bar = char * bar_len
        empty = " " * (width - bar_len)

        return f"|{bar}{empty}| {energy}"

    async def generate_daily_trend(self) -> str:
        """
        Generate daily energy trend visualization.

        For MVP: Shows current energy + recommendations
        Future: Track hourly energy throughout day
        """
        current_energy = await self.get_current_energy()
        current_hour = datetime.now().hour

        # Typical energy patterns (based on research)
        typical_patterns = {
            range(6, 9): "Rising - Good for planning",
            range(9, 12): "Peak - Best for complex work",
            range(12, 14): "Dip - Post-lunch slump",
            range(14, 17): "Recovery - Good for meetings",
            range(17, 20): "Declining - Simple tasks only",
            range(20, 24): "Low - Rest and recharge"
        }

        pattern_text = "Unknown time"
        for hour_range, description in typical_patterns.items():
            if current_hour in hour_range:
                pattern_text = description
                break

        report = f"""
╔════════════════════════════════════════════════════════╗
║      Energy Trend Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}      ║
╚════════════════════════════════════════════════════════╝

CURRENT ENERGY:
  {self._energy_to_bar(current_energy, 30)}

CURRENT HOUR: {current_hour}:00
  Typical pattern: {pattern_text}

ENERGY LEVELS:
  Hyperfocus  |██████████████████████| Peak cognitive capacity
  High        |███████████████░░░░░░░| Complex work optimal
  Medium      |██████████░░░░░░░░░░░░| Standard tasks
  Low         |█████░░░░░░░░░░░░░░░░░| Simple work only
  Very Low    |██░░░░░░░░░░░░░░░░░░░░| Rest needed

RECOMMENDATIONS:
  Current: {self._get_recommendation(current_energy, current_hour)}

PEAK PRODUCTIVITY HOURS (Research-based):
  09:00-12:00 - Morning peak (complex problem-solving)
  14:00-17:00 - Afternoon recovery (collaborative work)

AVOID:
  12:00-14:00 - Post-lunch dip (schedule breaks/lunch)
  17:00+ - Evening decline (save simple tasks)

═══════════════════════════════════════════════════════════
Future: Track your actual patterns over time for personalized insights
"""
        return report

    def _get_recommendation(self, energy: str, hour: int) -> str:
        """Get recommendation based on energy and time"""
        if energy in ["hyperfocus", "high"] and 9 <= hour <= 12:
            return "PERFECT! High energy + morning peak - tackle hardest problems now"
        elif energy in ["hyperfocus", "high"]:
            return "Good energy - use for complex work"
        elif energy == "medium" and 9 <= hour <= 17:
            return "Moderate energy - good for standard development tasks"
        elif energy == "medium":
            return "Moderate energy - consider simple tasks in evening hours"
        elif energy in ["low", "very_low"]:
            return "Low energy - take a break, do simple tasks, or call it a day"
        else:
            return "Monitor your energy and adjust tasks accordingly"


if __name__ == "__main__":
    async def main():
        viz = EnergyTrendVisualizer()
        report = await viz.generate_daily_trend()
        logger.info(report)

    asyncio.run(main())
