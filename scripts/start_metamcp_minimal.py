#!/usr/bin/env python3
"""
Minimal MetaMCP Broker Startup
Start MetaMCP broker with only available servers for testing
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Simple logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        logger.info("🚀 Starting Minimal MetaMCP Broker")

        # Import after path setup
        from dopemux.mcp.broker import MetaMCPBroker, BrokerConfig

        config = BrokerConfig(
            name="dopemux-metamcp-minimal",
            version="1.0.0",
            host="localhost",
            port=8091,
            broker_config_path="config/mcp/broker-minimal.yaml",
            policy_config_path="config/mcp/policy.yaml",
            role_based_mounting=True,
            budget_aware_hooks=False,
            letta_integration=False,
            adhd_optimizations=True
        )

        broker = MetaMCPBroker(config)
        await broker.start()

        logger.info("✅ Minimal MetaMCP Broker started on localhost:8091")
        logger.info("🔄 Running - Press Ctrl+C to stop")

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("📡 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Broker failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)