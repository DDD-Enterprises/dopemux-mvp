#!/usr/bin/env python3
"""
MetaMCP Broker Startup Script

This script starts the MetaMCP broker and configures it to work with Claude Code.
The broker will manage all MCP server connections and provide role-aware tool access.
"""

import asyncio
import sys
import signal
import logging
import os
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dopemux.mcp.broker import MetaMCPBroker, BrokerConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetaMCPService:
    """MetaMCP broker service wrapper for clean startup/shutdown"""

    def __init__(self):
        self.broker: Optional[MetaMCPBroker] = None
        self.running = False

    async def start(self):
        """Start the MetaMCP broker service"""
        try:
            logger.info("🚀 Starting MetaMCP Broker Service")

            # Verify configuration files exist
            broker_config_path = "config/mcp/broker.yaml"
            policy_config_path = "config/mcp/policy.yaml"

            if not os.path.exists(broker_config_path):
                logger.error(f"❌ Broker config not found: {broker_config_path}")
                return False

            if not os.path.exists(policy_config_path):
                logger.error(f"❌ Policy config not found: {policy_config_path}")
                return False

            # Create broker configuration
            config = BrokerConfig(
                name="dopemux-metamcp-broker",
                version="1.0.0",
                host="localhost",
                port=8090,
                broker_config_path=broker_config_path,
                policy_config_path=policy_config_path,
                role_based_mounting=True,
                budget_aware_hooks=True,
                letta_integration=False,  # Disable for initial setup
                adhd_optimizations=True
            )

            # Initialize and start broker
            self.broker = MetaMCPBroker(config)
            await self.broker.start()

            self.running = True
            logger.info("✅ MetaMCP Broker Service started successfully")
            logger.info(f"📡 Listening on {config.host}:{config.port}")
            logger.info("🧠 ADHD optimizations enabled")
            logger.info("💰 Budget-aware hooks active")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to start MetaMCP Broker: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def stop(self):
        """Stop the MetaMCP broker service"""
        if self.broker and self.running:
            logger.info("🛑 Stopping MetaMCP Broker Service...")
            await self.broker.stop()
            self.running = False
            logger.info("✅ MetaMCP Broker Service stopped")

    async def run_forever(self):
        """Run the service until interrupted"""
        if not await self.start():
            return False

        try:
            logger.info("🔄 MetaMCP Broker running - Press Ctrl+C to stop")

            # Run until interrupted
            while self.running:
                await asyncio.sleep(1)

                # Health check every 30 seconds
                if hasattr(self, '_last_health_check'):
                    if (asyncio.get_event_loop().time() - self._last_health_check) > 30:
                        await self._health_check()
                else:
                    self._last_health_check = asyncio.get_event_loop().time()

        except KeyboardInterrupt:
            logger.info("📡 Received interrupt signal")
        finally:
            await self.stop()

        return True

    async def _health_check(self):
        """Periodic health check"""
        try:
            if self.broker:
                health = await self.broker.get_broker_health()
                status = health.get('overall_status', 'unknown')
                active_sessions = health.get('active_sessions', 0)

                if status == 'ready':
                    logger.debug(f"💚 Health check: {status} ({active_sessions} active sessions)")
                else:
                    logger.warning(f"⚠️  Health check: {status} ({active_sessions} active sessions)")

                self._last_health_check = asyncio.get_event_loop().time()

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")


async def main():
    """Main service entry point"""

    # Ensure we're in the right directory
    if not os.path.exists("config/mcp/policy.yaml"):
        logger.error("❌ Please run this script from the dopemux-mvp root directory")
        return 1

    # Create service instance
    service = MetaMCPService()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"📡 Received signal {signum}")
        service.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the service
    success = await service.run_forever()
    return 0 if success else 1


if __name__ == "__main__":
    # Run the service
    exit_code = asyncio.run(main())
    sys.exit(exit_code)