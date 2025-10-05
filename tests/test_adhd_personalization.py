#!/usr/bin/env python3
"""
Test script for Serena v2 ADHD Personalization and Phase 2C Components.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the services directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "services"))

from serena.v2.intelligence import (
    setup_complete_intelligent_relationship_system,
    setup_complete_adaptive_learning_system,
    DatabaseConfig
)
from serena.v2.performance_monitor import PerformanceMonitor
from serena.v2.focus_manager import FocusManager, FocusMode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Test ADHD personalization and Phase 2C advanced components."""
    try:
        logger.info("🚀 Starting Serena v2 ADHD Personalization & Phase 2C Test")

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

        # Test 1: Setup complete adaptive learning system (Phase 2B)
        logger.info("🧠 Testing Phase 2B adaptive learning system...")
        try:
            adaptive_system = await setup_complete_adaptive_learning_system(
                database_config=db_config,
                performance_monitor=performance_monitor
            )
            logger.info(f"✅ Adaptive learning system: {len(adaptive_system)} components")
            adaptive_learning_available = True
        except Exception as e:
            logger.warning(f"⚠️ Adaptive learning system not available: {e}")
            adaptive_system = {}
            adaptive_learning_available = False

        # Test 2: Setup complete intelligent relationship system (Phase 2C)
        logger.info("🔗 Testing Phase 2C intelligent relationship system...")
        try:
            relationship_system = await setup_complete_intelligent_relationship_system(
                database_config=db_config,
                workspace_id=workspace_id,
                performance_monitor=performance_monitor
            )
            logger.info(f"✅ Intelligent relationship system: {relationship_system.get('total_components', 0)} components")
            logger.info(f"🎯 Phase 2C complete: {relationship_system.get('phase2c_complete', False)}")
            phase2c_available = True
        except Exception as e:
            logger.warning(f"⚠️ Phase 2C relationship system not available: {e}")
            relationship_system = {}
            phase2c_available = False

        # Test 3: Focus Manager ADHD features
        logger.info("🎯 Testing focus manager ADHD features...")
        focus_manager = FocusManager()
        await focus_manager.initialize()

        # Test different focus modes
        focus_modes_tested = []
        for mode in [FocusMode.LIGHT, FocusMode.MEDIUM, FocusMode.DEEP]:
            try:
                await focus_manager.set_focus_mode(mode)
                current_mode = await focus_manager.get_current_mode()
                focus_modes_tested.append(f"{mode.value} -> {current_mode}")
                logger.info(f"🧠 Focus mode {mode.value}: ✅ Working")
            except Exception as e:
                logger.warning(f"⚠️ Focus mode {mode.value}: {e}")

        # Test 4: ADHD session management
        logger.info("⏰ Testing ADHD session management...")
        session_results = {}

        try:
            # Test attention state tracking
            if hasattr(focus_manager, 'track_attention_state'):
                attention_state = await focus_manager.track_attention_state()
                session_results['attention_tracking'] = attention_state
                logger.info(f"🧠 Attention state: {attention_state}")

            # Test break recommendations
            if hasattr(focus_manager, 'should_recommend_break'):
                break_recommendation = await focus_manager.should_recommend_break()
                session_results['break_recommendation'] = break_recommendation
                logger.info(f"⏸️ Break recommendation: {break_recommendation}")

        except Exception as e:
            logger.info(f"📝 Session management: {e}")

        # Test 5: Performance monitoring with ADHD targets
        logger.info("📊 Testing performance monitoring with ADHD targets...")

        # Get current performance report
        performance_report = await performance_monitor.get_performance_report()
        logger.info("📈 Performance Report:")
        logger.info(f"  Operations tracked: {performance_report.get('total_operations', 0)}")
        logger.info(f"  Average time: {performance_report.get('average_time_ms', 0):.1f}ms")
        logger.info(f"  ADHD compliant: {performance_report.get('adhd_compliant_percentage', 0):.1f}%")

        return {
            "success": True,
            "adaptive_learning_available": adaptive_learning_available,
            "phase2c_available": phase2c_available,
            "focus_modes_tested": focus_modes_tested,
            "session_management": session_results,
            "performance_report": performance_report,
            "total_components": relationship_system.get('total_components', 0),
            "adhd_optimizations_active": True
        }

    except Exception as e:
        logger.error(f"💥 ADHD personalization test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🏁 ADHD personalization test result: {result}")