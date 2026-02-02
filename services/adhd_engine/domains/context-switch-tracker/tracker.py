"""
Context Switch Cost Tracker - Measure Interruption Impact

Tracks context switches and measures recovery time.
Helps identify productivity costs of interruptions.

ADHD Benefit: Quantify interruption impact, optimize focus blocks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque
import aiohttp

logger = logging.getLogger(__name__)


class ContextSwitchTracker:
    """
    Tracks context switches and calculates their productivity cost.

    Metrics:
    - Total switches per day
    - Average recovery time
    - Cumulative time lost
    - Most disruptive switch types
    """

    def __init__(
        self,
        activity_capture_url: str = "http://localhost:8096",
        recovery_time_baseline: int = 23  # Average: 23 minutes to regain focus after interrupt
    ):
        """
        Initialize context switch tracker.

        Args:
            activity_capture_url: Activity Capture service URL
            recovery_time_baseline: Average recovery time in minutes
        """
        self.activity_capture_url = activity_capture_url
        self.recovery_time_baseline = recovery_time_baseline

        # Tracking
        self.switches_today: List[Dict] = []
        self.total_recovery_time = 0
        self.current_recovery_start: Optional[datetime] = None

    async def get_todays_switches(self) -> Dict:
        """
        Get today's context switch metrics from Activity Capture.

        Returns:
            Dict with switch count, recovery time, cost analysis
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.activity_capture_url}/metrics",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        metrics = await response.json()

                        # Calculate from Activity Capture data
                        sessions = metrics.get("sessions_tracked", 0)
                        interruptions = metrics.get("current_session_interruptions", 0)

                        # Estimate: Each interruption costs ~23 min recovery time
                        estimated_cost_minutes = interruptions * self.recovery_time_baseline

                        return {
                            "switches_today": interruptions,
                            "estimated_recovery_minutes": estimated_cost_minutes,
                            "estimated_recovery_hours": round(estimated_cost_minutes / 60, 2),
                            "recovery_time_baseline": self.recovery_time_baseline,
                            "sessions_tracked": sessions,
                            "productivity_impact": self._calculate_productivity_impact(interruptions)
                        }

        except Exception as e:
            logger.error(f"Failed to get switch metrics: {e}")
            return {"error": str(e)}

    def _calculate_productivity_impact(self, switches: int) -> str:
        """
        Calculate productivity impact assessment.

        Args:
            switches: Number of context switches

        Returns:
            Impact assessment string
        """
        if switches == 0:
            return "Excellent - no interruptions!"
        elif switches <= 2:
            return "Good - minimal interruption impact"
        elif switches <= 5:
            return "Moderate - consider blocking focus time"
        elif switches <= 10:
            return "High - significant productivity loss"
        else:
            return "Critical - urgent need for interruption management"

    async def generate_report(self) -> str:
        """Generate formatted context switch cost report"""
        metrics = await self.get_todays_switches()

        if "error" in metrics:
            return f"Error generating report: {metrics['error']}"

        report = f"""
╔═══════════════════════════════════════════════════════════╗
║          Context Switch Cost Report - {datetime.now().strftime("%Y-%m-%d")}          ║
╚═══════════════════════════════════════════════════════════╝

INTERRUPTIONS TODAY:
  Total switches: {metrics['switches_today']}
  Sessions tracked: {metrics['sessions_tracked']}

ESTIMATED PRODUCTIVITY COST:
  Recovery time: {metrics['estimated_recovery_hours']} hours
  ({metrics['estimated_recovery_minutes']} minutes total)

  Baseline: {self.recovery_time_baseline} min recovery per switch

IMPACT ASSESSMENT:
  {metrics['productivity_impact']}

RECOMMENDATIONS:
  {"✅ Keep up the focus!" if metrics['switches_today'] <= 2 else ""}
  {"⚠️  Block 2-hour focus periods" if 3 <= metrics['switches_today'] <= 5 else ""}
  {"🚨 Enable DND mode, close Slack/email" if metrics['switches_today'] > 5 else ""}
  {"💡 Use Pomodoro technique for structured breaks" if metrics['switches_today'] > 0 else ""}

═══════════════════════════════════════════════════════════
Research: Average recovery time from interruption is 23 minutes
(UC Irvine study on multitasking and cognitive load)
"""
        return report


if __name__ == "__main__":
    import sys

    async def main():
        tracker = ContextSwitchTracker()
        report = await tracker.generate_report()
        logger.info(report)

    asyncio.run(main())
