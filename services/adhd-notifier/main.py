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

from monitor import ADHDMonitor

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

    logger.info("=" * 60)
    logger.info("ADHD Notifier Service - Starting...")
    logger.info("=" * 60)
    logger.info(f"ADHD Engine: {adhd_engine_url}")
    logger.info(f"User: {user_id}")
    logger.info(f"Check interval: {check_interval}s")
    logger.info(f"Notifications: {'enabled' if enable_notifications else 'disabled (test mode)'}")
    logger.info("")

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
        logger.info("Received shutdown signal")
        monitor.stop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown)

    # Start monitoring
    try:
        await monitor.start_monitoring()

    finally:
        # Show final metrics
        logger.info("")
        logger.info("=" * 60)
        logger.info("ADHD Notifier - Shutdown")
        logger.info("=" * 60)

        metrics = monitor.get_metrics()
        logger.info(f"Checks performed: {metrics['checks_performed']}")
        logger.info(f"Break notifications: {metrics['break_notifications_sent']}")
        logger.info(f"Hyperfocus alerts: {metrics['hyperfocus_notifications_sent']}")
        logger.info("Shutdown complete")


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
