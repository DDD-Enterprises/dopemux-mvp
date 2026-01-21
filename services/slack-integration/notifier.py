"""
Slack/Discord ADHD Integration - Team Communication

Posts daily ADHD summaries to Slack/Discord.
Sets status during focus time.

ADHD Benefit: Team visibility, coordinated breaks, status automation
"""

import asyncio
import logging
import os
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Posts ADHD metrics to Slack channels.

    Features:
    - Daily summary posts
    - Focus time status updates
    - Break coordination
    """

    def __init__(
        self,
        webhook_url: str = None,
        activity_capture_url: str = "http://localhost:8096",
        adhd_engine_url: str = "http://localhost:8095"
    ):
        """
        Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL (from env SLACK_WEBHOOK_URL)
            activity_capture_url: Activity Capture URL
            adhd_engine_url: ADHD Engine URL
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.activity_capture_url = activity_capture_url
        self.adhd_engine_url = adhd_engine_url

    async def post_daily_summary(self):
        """Post daily ADHD summary to Slack"""
        if not self.webhook_url:
            logger.warning("Slack webhook not configured (set SLACK_WEBHOOK_URL)")
            return False

        try:
            # Get metrics
            metrics = await self._get_metrics()
            adhd_state = await self._get_adhd_state()

            # Format message
            message = self._format_daily_summary(metrics, adhd_state)

            # Post to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json={"text": message},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Posted daily summary to Slack")
                        return True
                    else:
                        logger.error(f"Slack post failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to post to Slack: {e}")
            return False

    async def _get_metrics(self) -> Dict:
        """Get Activity Capture metrics"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.activity_capture_url}/metrics") as response:
                    return await response.json() if response.status == 200 else {}
        except Exception as e:
            return {}

            logger.error(f"Error: {e}")
    async def _get_adhd_state(self) -> Dict:
        """Get ADHD Engine state"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.adhd_engine_url}/health") as response:
                    return await response.json() if response.status == 200 else {}
        except Exception as e:
            return {}

            logger.error(f"Error: {e}")
    def _format_daily_summary(self, metrics: Dict, adhd_state: Dict) -> str:
        """Format Slack message"""
        sessions = metrics.get("sessions_tracked", 0)
        activities = metrics.get("activities_logged", 0)

        stats = adhd_state.get("accommodation_stats", {})
        breaks = stats.get("breaks_suggested", 0)
        hyperfocus = stats.get("hyperfocus_protections", 0)

        return f"""
*Daily ADHD Summary - {datetime.now().strftime("%Y-%m-%d")}*

:chart_with_upwards_trend: *Productivity*
• Sessions: {sessions}
• Activities logged: {activities}

:coffee: *ADHD Support*
• Break reminders: {breaks}
• Hyperfocus protections: {hyperfocus}

{"✅ Good break compliance!" if breaks > 0 else ""}
{"⚠️ Hyperfocus detected - watch for burnout" if hyperfocus > 0 else ""}

_Automated ADHD intelligence tracking_
"""


class DiscordNotifier(SlackNotifier):
    """Discord notifier (uses same webhook format as Slack)"""
    pass


if __name__ == "__main__":
    async def main():
        notifier = SlackNotifier()
        await notifier.post_daily_summary()

    asyncio.run(main())
