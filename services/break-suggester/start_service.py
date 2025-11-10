#!/usr/bin/env python3
"""
F-NEW-8 Break Suggester Service Launcher

Starts the proactive break suggestion engine as a background service.
Monitors EventBus for cognitive load patterns and suggests breaks.

Usage:
    python start_service.py [user_id]
    python start_service.py alice
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add current directory to path for relative imports
sys.path.insert(0, str(Path(__file__).parent))

from event_consumer import run_break_suggester_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    user_id = sys.argv[1] if len(sys.argv) > 1 else "default"

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    logger.info("=" * 60)
    logger.info("🚀 F-NEW-8: Proactive Break Suggester")
    logger.info("=" * 60)
    logger.info(f"   User ID: {user_id}")
    logger.info(f"   Redis: {redis_url}")
    logger.info(f"   Stream: dopemux:events")
    logger.info(f"   Consumer Group: break-suggester-{user_id}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📡 Monitoring for cognitive load patterns...")
    logger.info("   - High complexity code work (Serena)")
    logger.info("   - Cognitive state changes (ADHD Engine)")
    logger.info("   - Session duration tracking")
    logger.info("")
    logger.info("✨ Will suggest breaks when burnout risk detected")
    logger.info("")

    try:
        await run_break_suggester_service(user_id, redis_url)
    except KeyboardInterrupt:
        logger.info("\n👋 Break suggester service stopped")
    except Exception as e:
        logger.error(f"❌ Service error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
