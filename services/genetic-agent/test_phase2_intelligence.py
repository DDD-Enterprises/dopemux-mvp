"""
Test Phase 2 Intelligence Enhancement for Enhanced Iterative Agent

Validates the integration of:
- Failure Analysis Engine
- Adaptive Population Management
- Historical Learning System
- Intelligent strategy determination
- Enhanced iterative repair process
"""

import asyncio
import sys
import os

# Add the genetic agent path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'genetic_agent'))

from genetic_agent.genetic.enhanced_iterative_agent import EnhancedIterativeAgent, RepairStrategy
from genetic_agent.core.config import AgentConfig

class TestConfig:
    """Test configuration for Phase 2 validation."""
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

async def test_phase2_integration():
    """Test Phase 2 intelligence components integration."""
    print("🧠 Testing Phase 2 Intelligence Integration...")

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

    # Verify all intelligence components are initialized
    assert agent.failure_analyzer is not None, "Failure analyzer not initialized"
    assert agent.population_adaptor is not None, "Population adaptor not initialized"
    assert agent.learning_system is not None, "Learning system not initialized"

    print("✅ Intelligence components initialized")

async def test_failure_analysis():
    """Test failure analysis engine."""
    print("📊 Testing Failure Analysis Engine...")

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

    # Mock failure signals and context
    failure_signals = ["complexity_high", "patterns_missing", "llm_insufficient"]
    context = {
        "description": "Variable not defined error",
        "complexity": {"score": 0.8},
        "patterns": {"results": []}
    }
    repair_candidates = []  # Empty for failure case

    # Test failure analysis
    analysis = await agent.failure_analyzer.analyze_failure(
        failure_signals, context, repair_candidates
    )

    assert analysis.primary_failure_mode is not None, "Primary failure mode not identified"
    assert analysis.confidence_score >= 0.0, "Invalid confidence score"
    assert analysis.statistical_insights is not None, "Missing statistical insights"

    print("✅ Failure analysis working")

async def test_adaptive_population():
    """Test adaptive population management."""
    print("🔄 Testing Adaptive Population Management...")

    config = AgentConfig(
        max_tree_depth=10,
        population_size=10,
        max_iterations=3,
        confidence_threshold=0.6,
        serena_url="http://localhost:3006",
        dope_context_url="http://localhost:3010",
        conport_url="http://localhost:3004",
        zen_url="http://localhost:3003",
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    agent = EnhancedIterativeAgent(config)

    # Test complexity assessment
    complexity = agent.population_adaptor.assess_problem_complexity(
        complexity_score=0.7,
        pattern_count=5,
        description_length=200
    )

    assert complexity.estimated_difficulty in ["easy", "medium", "hard", "extreme"], "Invalid difficulty assessment"
    assert complexity.recommended_population_size > 0, "Invalid population recommendation"
    assert 0 <= complexity.confidence_intervals[0] <= complexity.confidence_intervals[1], "Invalid confidence intervals"

    print("✅ Adaptive population management working")

async def test_historical_learning():
    """Test historical learning system."""
    print("📚 Testing Historical Learning System...")

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

    # Test operator recommendation
    context = {
        "complexity": {"score": 0.5},
        "description": "Simple bug fix"
    }

    recommendation = await agent.learning_system.recommend_operator(
        context=context,
        available_operators=["mutate_condition", "swap_operators"],
        population_size=10,
        current_generation=1
    )

    assert recommendation.recommended_operator in ["mutate_condition", "swap_operators"], "Invalid operator recommendation"
    assert 0.0 <= recommendation.confidence <= 1.0, "Invalid confidence score"
    assert recommendation.reasoning is not None, "Missing reasoning"

    print("✅ Historical learning system working")

async def test_strategy_determination():
    """Test intelligent strategy determination."""
    print("🎯 Testing Intelligent Strategy Determination...")

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

    # Test with simple case (should prefer LLM_ONLY)
    simple_analysis = {
        "complexity": {"score": 0.3},
        "patterns": {"results": [1, 2, 3, 4, 5]}
    }

    # Mock empty historical data to test basic logic
    agent.learning_system.learning_events = []
    agent.learning_system.operator_performance = {}

    # Mock async method to return empty list
    async def mock_historical_insights(limit=10):
        return []
    agent.failure_analyzer.get_historical_insights = mock_historical_insights

    strategy = await agent._determine_strategy_with_intelligence(simple_analysis)
    # With empty historical data and failure insights, should fall back to basic strategy determination
    # which should return LLM_ONLY for low complexity + high patterns
    expected_strategy = await agent._determine_strategy(simple_analysis)
    assert strategy == expected_strategy, f"Strategy determination failed: expected {expected_strategy}, got {strategy}"

    # Test with complex case (should prefer FULL_GP or SELECTIVE_GP)
    complex_analysis = {
        "complexity": {"score": 0.9},
        "patterns": {"results": []}
    }

    strategy = await agent._determine_strategy_with_intelligence(complex_analysis)
    assert strategy in [RepairStrategy.FULL_GP, RepairStrategy.SELECTIVE_GP], f"Expected GP strategy for complex case, got {strategy}"

    print("✅ Intelligent strategy determination working")

async def test_intelligence_integration():
    """Test full intelligence integration."""
    print("🔗 Testing Full Intelligence Integration...")

    config = AgentConfig(
        max_tree_depth=10,
        population_size=5,
        max_iterations=2,  # Short for testing
        confidence_threshold=0.8,  # High threshold to ensure failure for testing
        serena_url="http://localhost:3006",
        dope_context_url="http://localhost:3010",
        conport_url="http://localhost:3004",
        zen_url="http://localhost:3003",
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    agent = EnhancedIterativeAgent(config)

    # Mock MCP service calls to avoid requiring running services
    async def mock_analyze_complexity(file_path):
        return {"score": 0.5, "level": "medium"}

    async def mock_search_code(**kwargs):
        return {"results": [{"code": "mock fix", "relevance_score": 0.8}]}

    async def mock_thinkdeep(**kwargs):
        return {"reasoning": {"code": "# Mock fix", "explanation": "Mock explanation", "confidence": 0.6}}

    async def mock_codereview(**kwargs):
        return {"approved": False, "score": 0.4}

    # Apply mocks
    agent.serena_client.analyze_complexity = mock_analyze_complexity
    agent.dope_client.search_code = mock_search_code
    agent.zen_client.thinkdeep = mock_thinkdeep
    agent.zen_client.codereview = mock_codereview

    # Create a test task that will likely fail (high confidence threshold)
    task = {
        "bug_description": "Test bug that should fail with high threshold",
        "file_path": "test.py",
        "line_number": 10
    }

    # Execute repair (will likely fail but test intelligence integration)
    result = await agent._execute_repair(task)

    # Verify response structure
    assert "success" in result, "Missing success field"
    assert "confidence" in result, "Missing confidence field"
    assert "method" in result, "Missing method field"

    # If failed, should have failure analysis
    if not result["success"]:
        assert "failure_analysis" in result, "Missing failure analysis for failed repair"

    print("✅ Full intelligence integration working")

async def run_phase2_tests():
    """Run all Phase 2 intelligence tests."""
    print("🚀 Starting Phase 2 Intelligence Enhancement Tests\n")

    try:
        await test_phase2_integration()
        await test_failure_analysis()
        await test_adaptive_population()
        await test_historical_learning()
        await test_strategy_determination()
        await test_intelligence_integration()

        print("\n🎉 All Phase 2 Intelligence tests passed!")
        print("✨ Enhanced Iterative Agent is now intelligently enhanced with:")
        print("   - Failure pattern analysis and statistical insights")
        print("   - Adaptive population management for optimal sizing")
        print("   - Historical learning system for operator optimization")
        print("   - Intelligent strategy determination with context awareness")
        print("   - Comprehensive MCP integration throughout")
        return True

    except Exception as e:
        print(f"\n❌ Phase 2 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_phase2_tests())
    sys.exit(0 if success else 1)