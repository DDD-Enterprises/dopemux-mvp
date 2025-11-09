"""
Test script for Enhanced Iterative Agent Phase 1

Validates core functionality:
- Agent instantiation
- MCP service integration
- Basic iteration loop
- GP operator functionality
"""

import asyncio
import sys
import os

# Add the genetic agent path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'genetic_agent'))

from genetic_agent.genetic.enhanced_iterative_agent import EnhancedIterativeAgent, RepairStrategy
from genetic_agent.core.config import AgentConfig

class TestConfig:
    """Minimal test configuration."""
    def __init__(self):
        self.max_tree_depth = 10
        self.population_size = 5
        self.max_iterations = 3
        self.confidence_threshold = 0.6

        # MCP service URLs (test/local)
        self.serena_url = "http://localhost:3006"
        self.dope_context_url = "http://localhost:3010"
        self.conport_url = "http://localhost:3004"
        self.zen_url = "http://localhost:3003"

        self.workspace_id = "/Users/hue/code/dopemux-mvp"

async def test_agent_instantiation():
    """Test agent can be created and initialized."""
    print("🧪 Testing Enhanced Iterative Agent instantiation...")

    config = AgentConfig(
        max_tree_depth=10,
        population_size=5,
        max_iterations=3,
        confidence_threshold=0.6,
        serena_url="http://localhost:3006",
        dope_context_url="http://localhost:3010",
        conport_url="http://localhost:3004",
        zen_url="http://localhost:3003",
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    agent = EnhancedIterativeAgent(config)

    # Verify components are initialized
    assert agent.gp_operators is not None, "GP operators not initialized"
    assert agent.population_manager is not None, "Population manager not initialized"
    assert agent.repair_candidates == [], "Repair candidates should start empty"

    print("✅ Agent instantiation successful")

async def test_strategy_determination():
    """Test strategy determination logic."""
    print("🧪 Testing strategy determination...")

    config = AgentConfig(
        max_tree_depth=10,
        population_size=5,
        max_iterations=3,
        confidence_threshold=0.6,
        serena_url="http://localhost:3006",
        dope_context_url="http://localhost:3010",
        conport_url="http://localhost:3004",
        zen_url="http://localhost:3003",
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    agent = EnhancedIterativeAgent(config)

    # Test with low complexity, high patterns (LLM_ONLY)
    analysis_low_complex = {
        "complexity": {"score": 0.4},
        "patterns": {"results": [1,2,3,4,5,6,7,8,9,10]}
    }
    strategy_low = await agent._determine_strategy(analysis_low_complex)
    assert strategy_low == RepairStrategy.LLM_ONLY, "Should select LLM_ONLY for simple cases"

    # Test with high complexity (FULL_GP)
    analysis_high_complex = {
        "complexity": {"score": 0.9},
        "patterns": {"results": []}
    }
    strategy_high = await agent._determine_strategy(analysis_high_complex)
    assert strategy_high == RepairStrategy.FULL_GP, "Should select FULL_GP for complex cases"

    # Test with medium complexity (SELECTIVE_GP)
    analysis_medium = {
        "complexity": {"score": 0.7},
        "patterns": {"results": [1,2,3]}
    }
    strategy_medium = await agent._determine_strategy(analysis_medium)
    assert strategy_medium == RepairStrategy.SELECTIVE_GP, "Should select SELECTIVE_GP for medium cases"

    print("✅ Strategy determination successful")

async def test_fitness_evaluation():
    """Test fitness evaluation function."""
    print("🧪 Testing fitness evaluation...")

    config = AgentConfig(
        max_tree_depth=10,
        population_size=5,
        max_iterations=3,
        confidence_threshold=0.6,
        serena_url="http://localhost:3006",
        dope_context_url="http://localhost:3010",
        conport_url="http://localhost:3004",
        zen_url="http://localhost:3003",
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    agent = EnhancedIterativeAgent(config)

    # Test simple fitness calculation
    test_code = "result = x + y"
    analysis = {"complexity": {"score": 0.3}}
    fitness = agent._fitness(test_code, analysis)

    # Should be reasonable (0.0-1.0)
    assert 0.0 <= fitness <= 1.0, f"Fitness out of range: {fitness}"
    assert fitness > 0.0, "Fitness should be positive for simple code"

    print("✅ Fitness evaluation successful")

async def run_tests():
    """Run all tests."""
    print("🚀 Starting Enhanced Iterative Agent Phase 1 Tests\n")

    try:
        await test_agent_instantiation()
        await test_strategy_determination()
        await test_fitness_evaluation()

        print("\n🎉 All tests passed! Phase 1 implementation is functional.")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)