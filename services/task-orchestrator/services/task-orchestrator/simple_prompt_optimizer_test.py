#!/usr/bin/env python3
"""
Simple test for PromptOptimizer functionality.
Tests meta-prompting, critique, and improvement features.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from enhanced_orchestrator import ClaudeBrainManager, OrchestrationTask
    print("✅ Imported ClaudeBrainManager and OrchestrationTask successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_prompt_optimizer():
    """Test the PromptOptimizer with sample tasks."""
    print("🧪 Starting PromptOptimizer tests...")

    # Initialize brain manager
    brain = ClaudeBrainManager()
    optimizer = brain.prompt_optimizer

    # Sample task
    sample_task = OrchestrationTask(
        id="test_task_001",
        title="Implement user authentication",
        description="Create JWT-based authentication with role management for the Dopemux platform",
        complexity_score=0.7,
        cognitive_load=0.6,
        energy_required="medium"
    )

    sample_context = {
        "energy_level": "medium",
        "available_agents": ["CONPORT", "SERENA", "TASKMASTER", "ZEN"]
    }

    # Test 1: Generate optimized prompt
    print("\n1. Testing generate_meta_prompt...")
    try:
        meta_prompt = await optimizer.generate_meta_prompt(sample_task, sample_context)
        print(f"✅ Meta-prompt generated (length: {len(meta_prompt)} chars)")
        print(f"Preview: {meta_prompt[:200]}...")
    except Exception as e:
        print(f"❌ Meta-prompt generation failed: {e}")

    # Test 2: Critique and improve
    print("\n2. Testing critique_and_improve_prompt...")
    try:
        # Use a simple base prompt for testing
        base_prompt = "Recommend an agent for authentication implementation."
        improved_prompt = await optimizer.critique_and_improve_prompt(base_prompt, sample_task)
        print(f"✅ Improved prompt generated (length: {len(improved_prompt)} chars)")
        print(f"Preview: {improved_prompt[:200]}...")
    except Exception as e:
        print(f"❌ Critique/improvement failed: {e}")

    # Test 3: Get performance stats
    print("\n3. Testing get_meta_performance_stats...")
    try:
        stats = optimizer.get_meta_performance_stats()
        print(f"✅ Performance stats: {stats}")
    except Exception as e:
        print(f"❌ Stats retrieval failed: {e}")

    print("\n🎉 PromptOptimizer tests completed!")

if __name__ == "__main__":
    asyncio.run(test_prompt_optimizer())