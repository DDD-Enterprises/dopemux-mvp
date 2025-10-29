#!/usr/bin/env python3
"""
ConPort Event Bridge
Watches ConPort MCP SQLite and publishes events to Redis Streams
"""

import os
import sys
import logging
import signal
from pathlib import Path
from dotenv import load_dotenv

from watcher import ConPortDBWatcher
from publisher import EventPublisher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventBridge:
    """Main event bridge coordinator"""
    
    def __init__(self):
        # Configuration
        self.db_path = os.getenv(
            'CONPORT_DB_PATH',
            str(Path.home() / 'code/dopemux-mvp/context_portal/context.db')
        )
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Components
        self.publisher = None
        self.watcher = None
        self.observer = None
        
        # Shutdown flag
        self.running = True
    
    def event_callback(self, event):
        """Called when file system event detected"""
        try:
            self.publisher.publish(event)
        except Exception as e:
            logger.error(f"Error in event callback: {e}")
    
    def start(self):
        """Start the event bridge"""
        logger.info("=" * 70)
        logger.info("🌉 ConPort Event Bridge Starting")
        logger.info("=" * 70)
        logger.info(f"📁 Database: {self.db_path}")
        logger.info(f"📮 Redis: {self.redis_url}")
        logger.info("")
        
        # Check database exists
        if not Path(self.db_path).exists():
            logger.error(f"❌ Database not found: {self.db_path}")
            sys.exit(1)
        
        # Connect to Redis
        try:
            self.publisher = EventPublisher(self.redis_url)
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            sys.exit(1)
        
        # Start watcher
        self.watcher = ConPortDBWatcher(self.db_path, self.event_callback)
        self.observer = self.watcher.start_watching()
        
        logger.info("")
        logger.info("✅ Event Bridge Running!")
        logger.info("👁️  Watching for ConPort MCP changes...")
        logger.info("📡 Publishing to Redis Stream: conport:events")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
        
        # Keep running
        try:
            while self.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Shutdown signal received")
            self.stop()
    
    def stop(self):
        """Stop the event bridge"""
        logger.info("🛑 Stopping Event Bridge...")
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        if self.publisher:
            self.publisher.close()
        
        logger.info("✅ Event Bridge Stopped")
        self.running = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start bridge
    bridge = EventBridge()
    bridge.start()
