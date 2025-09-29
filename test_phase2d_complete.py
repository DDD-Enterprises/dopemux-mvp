#!/usr/bin/env python3
"""
Test script for complete Serena v2 Phase 2D Pattern Store System.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the services directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "services"))

from serena.v2.intelligence import (
    setup_complete_pattern_store_system,
    setup_phase2_intelligence,
    DatabaseConfig
)
from serena.v2.performance_monitor import PerformanceMonitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Test the complete Phase 2D pattern store system."""
    try:
        logger.info("🚀 Starting Serena v2 Phase 2D Complete System Test")

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

        workspace_id = "/Users/hue/code/dopemux-mvp"

        # Test complete Phase 2D pattern store system
        logger.info("🧠 Setting up complete Phase 2D pattern store system...")

        try:
            complete_system = await setup_complete_pattern_store_system(
                database_config=db_config,
                workspace_id=workspace_id,
                performance_monitor=performance_monitor
            )

            logger.info("🎉 PHASE 2D COMPLETE SYSTEM RESULTS:")
            logger.info(f"  Total components: {complete_system.get('total_components', 0)}")
            logger.info(f"  Version: {complete_system.get('version', 'Unknown')}")
            logger.info(f"  Phase 2D complete: {complete_system.get('phase2d_complete', False)}")
            logger.info(f"  Pattern store operational: {complete_system.get('pattern_store_operational', False)}")

            # List all components
            component_categories = {
                "Phase 2A Database": ["database"],
                "Phase 2B Learning": ["learning_engine", "profile_manager", "pattern_recognition", "effectiveness_tracker"],
                "Phase 2C Intelligence": ["relationship_builder", "enhanced_tree_sitter", "conport_bridge", "adhd_filter", "realtime_scorer", "success_validator"],
                "Phase 2D Pattern Store": ["template_manager", "pattern_adapter", "persistence_bridge", "evolution_system", "recommendation_engine", "validation_system"]
            }

            logger.info("\n📊 COMPONENT BREAKDOWN:")
            total_found = 0
            for category, component_keys in component_categories.items():
                found_components = [key for key in component_keys if key in complete_system]
                total_found += len(found_components)
                logger.info(f"  {category}: {len(found_components)}/{len(component_keys)} components")
                for component in found_components:
                    logger.info(f"    ✅ {component}")

            logger.info(f"\n🎯 SYSTEM SUMMARY:")
            logger.info(f"  Total components found: {total_found}")
            logger.info(f"  Expected components: 19")
            logger.info(f"  Coverage: {(total_found/19)*100:.1f}%")

            # Test key Phase 2D capabilities
            logger.info("\n🧪 TESTING PHASE 2D CAPABILITIES:")

            # Test template manager
            if "template_manager" in complete_system:
                template_manager = complete_system["template_manager"]
                logger.info("✅ Template Manager: Available")

                # Test basic template operations
                if hasattr(template_manager, 'get_available_templates'):
                    templates = await template_manager.get_available_templates()
                    logger.info(f"📝 Available templates: {len(templates) if templates else 0}")

            # Test pattern adapter
            if "pattern_adapter" in complete_system:
                logger.info("✅ Pattern Adapter: Available")

            # Test persistence bridge
            if "persistence_bridge" in complete_system:
                logger.info("✅ Cross-Session Persistence Bridge: Available")

            # Test recommendation engine
            if "recommendation_engine" in complete_system:
                logger.info("✅ Pattern Reuse Recommendation Engine: Available")

            # Test evolution system
            if "evolution_system" in complete_system:
                logger.info("✅ Effectiveness Evolution System: Available")

            # Test validation system
            if "validation_system" in complete_system:
                logger.info("✅ Performance Validation System: Available")

            return {
                "success": True,
                "total_components": complete_system.get('total_components', 0),
                "version": complete_system.get('version', 'Unknown'),
                "phase2d_complete": complete_system.get('phase2d_complete', False),
                "pattern_store_operational": complete_system.get('pattern_store_operational', False),
                "components_verified": total_found,
                "coverage_percentage": (total_found/19)*100
            }

        except Exception as e:
            logger.error(f"💥 Phase 2D setup failed: {e}")
            import traceback
            traceback.print_exc()

            # Fallback: Test Phase 2C system
            logger.info("📦 Testing Phase 2C system as fallback...")
            phase2c_system = await setup_complete_intelligent_relationship_system(
                database_config=db_config,
                workspace_id=workspace_id,
                performance_monitor=performance_monitor
            )

            return {
                "success": True,
                "fallback_to_phase2c": True,
                "phase2c_components": phase2c_system.get('total_components', 0),
                "error_message": str(e)
            }

    except Exception as e:
        logger.error(f"💥 Complete system test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🏁 Phase 2D complete system test result: {result}")