#!/usr/bin/env python3
"""
ADHD Notifier Service - Break Reminders and Hyperfocus Alerts

Monitors Activity Capture for active sessions and sends desktop notifications
for break reminders and hyperfocus protection.

ADHD Benefits:
- Automatic break reminders (prevent burnout)
- Hyperfocus protection (prevent overwork)
- Zero manual tracking
- Non-intrusive notifications

Usage:
    python main.py                    # Run with defaults
    python main.py --interval 30      # Check every 30 seconds
    python main.py --no-notifications # Test mode (no notifications)
"""

import asyncio
import logging
import argparse
import signal
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from monitor import ADHDMonitor
from services.shared.brand_voice import StatusChip, brand_log, voice_header

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_notifier(
    check_interval: int = 60,
    enable_notifications: bool = True
):
    """
    Run ADHD notification service.

    Args:
        check_interval: Seconds between checks
        enable_notifications: Enable desktop notifications
    """
    # Read configuration from environment
    adhd_engine_url = os.getenv("ADHD_ENGINE_URL", "http://localhost:8095")
    user_id = os.getenv("USER_ID", "hue")

    logger.info(voice_header("ADHD Notifier Service"))
    logger.info(brand_log("Initiating satellite notification sequence.", chip=StatusChip.LIVE))
    logger.info(brand_log(f"ADHD Engine coordinate: {adhd_engine_url}", chip=StatusChip.LOGGED))
    logger.info(brand_log(f"User identity: {user_id}", chip=StatusChip.LOGGED))
    logger.info(brand_log(f"Check frequency: {check_interval}s", chip=StatusChip.LOGGED))
    logger.info(brand_log(f"Notifications: {'enabled' if enable_notifications else 'disabled (test mode)'}", chip=StatusChip.LOGGED))

    # Initialize monitor
    monitor = ADHDMonitor(
        adhd_engine_url=adhd_engine_url,
        user_id=user_id,
        check_interval=check_interval,
        enable_notifications=enable_notifications
    )

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def shutdown():
        logger.info(brand_log("Received shutdown signal.", chip=StatusChip.AFTERCARE))
        monitor.stop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown)

    # Start monitoring
    try:
        await monitor.start_monitoring()

    finally:
        # Show final metrics
        logger.info(brand_log("ADHD Notifier - Sequence Terminated.", chip=StatusChip.AFTERCARE))

        metrics = monitor.get_metrics()
        logger.info(brand_log(f"Total checks performed: {metrics['checks_performed']}", chip=StatusChip.LOGGED))
        logger.info(brand_log(f"Break reminders transmitted: {metrics['break_notifications_sent']}", chip=StatusChip.LOGGED))
        logger.info(brand_log(f"Hyperfocus alerts engaged: {metrics['hyperfocus_notifications_sent']}", chip=StatusChip.LOGGED))
        logger.info(brand_log("Shutdown complete. Ritual preserved.", chip=StatusChip.AFTERCARE))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADHD Notifier - Break reminders and hyperfocus alerts")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60)")
    parser.add_argument("--no-notifications", action="store_true", help="Disable notifications (test mode)")
    args = parser.parse_args()

    enable_notifications = not args.no_notifications

    try:
        asyncio.run(run_notifier(
            check_interval=args.interval,
            enable_notifications=enable_notifications
        ))
    except KeyboardInterrupt:
        logger.info("Stopped by user")
