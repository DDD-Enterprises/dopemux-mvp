"""
Daily ADHD Reporter - Generate Daily/Weekly ADHD Summaries

Creates summary reports of ADHD metrics, sessions, and patterns.
Useful for tracking progress and identifying trends.

ADHD Benefits:
- See patterns over time
- Identify peak productivity hours
- Track break compliance
- Celebrate accomplishments
"""

import asyncio
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DailyReporter:
    """
    Generates daily/weekly ADHD activity reports.

    Queries Activity Capture and ADHD Engine for metrics.
    """

    def __init__(
        self,
        activity_capture_url: str = "http://localhost:8096",
        adhd_engine_url: str = "http://localhost:8095",
        user_id: str = "hue"
    ):
        """
        Initialize daily reporter.

        Args:
            activity_capture_url: Activity Capture service URL
            adhd_engine_url: ADHD Engine URL
            user_id: User ID to report on
        """
        self.activity_capture_url = activity_capture_url
        self.adhd_engine_url = adhd_engine_url
        self.user_id = user_id

    async def generate_daily_report(self) -> str:
        """
        Generate daily ADHD activity report.

        Returns:
            Formatted report string
        """
        logger.info("Generating daily ADHD report...")

        # Get metrics
        activity_metrics = await self._get_activity_metrics()
        adhd_state = await self._get_adhd_state()

        # Generate report
        report = self._format_daily_report(activity_metrics, adhd_state)

        logger.info("Daily report generated")
        return report

    async def _get_activity_metrics(self) -> Dict[str, Any]:
        """Get metrics from Activity Capture"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.activity_capture_url}/metrics",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}

        except Exception as e:
            logger.error(f"Failed to get activity metrics: {e}")
            return {}

    async def _get_adhd_state(self) -> Dict[str, Any]:
        """Get ADHD Engine state"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get health
                async with session.get(
                    f"{self.adhd_engine_url}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return {}

        except Exception as e:
            logger.error(f"Failed to get ADHD state: {e}")
            return {}

    def _format_daily_report(
        self,
        activity_metrics: Dict[str, Any],
        adhd_state: Dict[str, Any]
    ) -> str:
        """
        Format daily report.

        Args:
            activity_metrics: Activity Capture metrics
            adhd_state: ADHD Engine state

        Returns:
            Formatted report text
        """
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Extract metrics
        sessions = activity_metrics.get("sessions_tracked", 0)
        activities = activity_metrics.get("activities_logged", 0)
        errors = activity_metrics.get("logging_errors", 0)

        # ADHD stats
        stats = adhd_state.get("accommodation_stats", {})
        breaks_suggested = stats.get("breaks_suggested", 0)
        hyperfocus_protections = stats.get("hyperfocus_protections", 0)

        # Build report
        report = f"""
╔════════════════════════════════════════════════════════════╗
║          ADHD Activity Report - {date_str}          ║
╚════════════════════════════════════════════════════════════╝

SESSIONS & PRODUCTIVITY
  Sessions tracked: {sessions}
  Activities logged: {activities}
  Logging errors: {errors}

ADHD ACCOMMODATIONS
  Break reminders: {breaks_suggested}
  Hyperfocus protections: {hyperfocus_protections}

CURRENT STATE
  Energy: {adhd_state.get('current_state', {}).get('energy_levels', {}).get('hue', 'unknown')}
  Attention: {adhd_state.get('current_state', {}).get('attention_states', {}).get('hue', 'unknown')}

INSIGHTS
  {'✅ Good break compliance!' if breaks_suggested > 0 else '⚠️  No breaks tracked yet'}
  {'⚠️  Hyperfocus detected - watch for burnout' if hyperfocus_protections > 0 else '✅ No hyperfocus issues'}
  {'✅ Active ADHD monitoring' if activities > 0 else '📊 Building baseline data...'}

═══════════════════════════════════════════════════════════
Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        return report

    async def save_report_to_file(self, report: str, filename: Optional[str] = None):
        """
        Save report to file.

        Args:
            report: Report text
            filename: Optional custom filename
        """
        if not filename:
            filename = f"adhd-report-{datetime.now().strftime('%Y-%m-%d')}.txt"

        try:
            report_dir = Path.home() / "adhd-reports"
            report_dir.mkdir(exist_ok=True)

            report_path = report_dir / filename

            with open(report_path, "w") as f:
                f.write(report)

            logger.info(f"Report saved: {report_path}")
            return str(report_path)

        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return None


# Helper function for manual report generation
async def generate_and_print_report():
    """Generate and print daily report"""
    reporter = DailyReporter()
    report = await reporter.generate_daily_report()
    logger.info(report)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    asyncio.run(generate_and_print_report())
