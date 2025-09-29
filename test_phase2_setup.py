#!/usr/bin/env python3
"""
Test script for Serena v2 Phase 2 Intelligence setup and integration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the services directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "services"))

from serena.v2.intelligence import setup_phase2_intelligence, validate_phase2_deployment, DatabaseConfig
from serena.v2.performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Run Phase 2 setup and validation."""
    try:
        logger.info("🚀 Starting Serena v2 Phase 2 Intelligence Setup")

        # Initialize performance monitor
        performance_monitor = PerformanceMonitor()

        # Configure database with correct credentials
        db_config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="serena_intelligence",
            user="serena",
            password="serena_dev_pass"
        )

        # Setup Phase 2 intelligence
        logger.info("📊 Setting up Phase 2 intelligence...")
        database, graph_operations = await setup_phase2_intelligence(
            database_config=db_config,
            performance_monitor=performance_monitor
        )

        logger.info("✅ Phase 2 intelligence setup complete!")
        logger.info(f"📈 Database: {database}")
        logger.info(f"🔗 Graph operations: {graph_operations}")

        # Validate deployment
        logger.info("🧪 Running deployment validation...")
        validation_result = await validate_phase2_deployment(
            database_config=db_config,
            run_integration_tests=True
        )

        logger.info("📋 Validation Results:")
        for key, value in validation_result.items():
            logger.info(f"  {key}: {value}")

        if validation_result.get('overall_success', False):
            logger.info("🎉 Phase 2 deployment validation PASSED!")
        else:
            logger.error("❌ Phase 2 deployment validation FAILED!")

        return validation_result

    except Exception as e:
        logger.error(f"💥 Phase 2 setup failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🏁 Final result: {result}")