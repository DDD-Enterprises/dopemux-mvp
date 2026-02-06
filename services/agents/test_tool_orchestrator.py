"""
Week 8: ToolOrchestrator Comprehensive Test Suite

Tests intelligent MCP tool and model selection.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tool_orchestrator import ToolOrchestrator, TaskComplexity, ModelTier


async def test_simple_task_fast_model():
    """Test 1: Simple tasks get fast tier models"""
    print("\n" + "="*70)
    print("Test 1: Simple Task → Fast Tier Model")
    print("="*70)

    orchestrator = ToolOrchestrator(workspace_id="/Users/hue/code/dopemux-mvp")
    await orchestrator.initialize()

    # Simple debugging task
    selections = await orchestrator.select_tools_for_task(
        task_type="debugging",
        complexity=0.2  # Simple
    )

    primary = selections["primary"]
    print(f"\nTask: debugging (complexity 0.2)")
    print(f"Selected Tool: {primary.primary_tool}")
    print(f"Selected Model: {primary.model}")
    print(f"Model Tier: Fast (expected)")

    assert primary.primary_tool == "zen", "Should select Zen for debugging"
    assert "fast" in primary.model or "mini" in primary.model or primary.model == "grok-4-fast", \
        f"Should select fast tier model, got {primary.model}"
    print("✅ Test passed! Fast tier model selected for simple task")

    await orchestrator.close()


async def test_medium_task_mid_model():
    """Test 2: Medium tasks get mid tier models"""
    print("\n" + "="*70)
    print("Test 2: Medium Task → Mid Tier Model")
    print("="*70)

    orchestrator = ToolOrchestrator(workspace_id="/Users/hue/code/dopemux-mvp")
    await orchestrator.initialize()

    # Medium analysis task
    selections = await orchestrator.select_tools_for_task(
        task_type="analysis",
        complexity=0.5  # Medium
    )

    primary = selections["primary"]
    print(f"\nTask: analysis (complexity 0.5)")
    print(f"Selected Tool: {primary.primary_tool}")
    print(f"Selected Model: {primary.model}")
    print(f"Model Tier: Mid (expected)")

    assert primary.primary_tool == "zen", "Should select Zen for analysis"
    assert any(name in primary.model for name in ["gpt-5", "gemini-2.5", "codex"]), \
        f"Should select mid tier model, got {primary.model}"
    print("✅ Test passed! Mid tier model selected for medium task")

    await orchestrator.close()


async def test_complex_task_power_model():
    """Test 3: Complex tasks get power tier models"""
    print("\n" + "="*70)
    print("Test 3: Complex Task → Power Tier Model")
    print("="*70)

    orchestrator = ToolOrchestrator(workspace_id="/Users/hue/code/dopemux-mvp")
    await orchestrator.initialize()

    # Complex code review
    model = await orchestrator.select_model_for_zen(
        tool_method="codereview",
        complexity=0.9,  # Complex
        performance_priority="quality"
    )

    print(f"\nTask: codereview (complexity 0.9)")
    print(f"Selected Model: {model}")
    print(f"Model Tier: Power (expected)")

    assert model in ["grok-code-fast-1", "gemini-2.5-pro", "o3-mini"], \
        f"Should select power tier model, got {model}"
    print("✅ Test passed! Power tier model selected for complex task")

    orchestrator.metrics["selections_made"] += 1
    await orchestrator.close()


async def test_code_navigation_selection():
    """Test 4: Code navigation always selects Serena"""
    print("\n" + "="*70)
    print("Test 4: Code Navigation → Serena (Required)")
    print("="*70)

    orchestrator = ToolOrchestrator(workspace_id="/Users/hue/code/dopemux-mvp")
    await orchestrator.initialize()

    selections = await orchestrator.select_tools_for_task(
        task_type="code_navigation",
        complexity=0.5
    )

    primary = selections["primary"]
    print(f"\nTask: code_navigation")
    print(f"Selected Tool: {primary.primary_tool}")
    print(f"Fallback: {primary.fallback_tool}")

    assert primary.primary_tool == "serena", "Should always select Serena for code nav"
    print("✅ Test passed! Serena selected for code navigation")

    await orchestrator.close()


async def test_documentation_with_fallback():
    """Test 5: Documentation task has fallback"""
    print("\n" + "="*70)
    print("Test 5: Documentation → PAL apilookup (with Exa fallback)")
    print("="*70)

    orchestrator = ToolOrchestrator(workspace_id="/Users/hue/code/dopemux-mvp")
    await orchestrator.initialize()

    selections = await orchestrator.select_tools_for_task(
        task_type="documentation",
        complexity=0.3
    )

    primary = selections["primary"]
    print(f"\nTask: documentation")
    print(f"Primary Tool: {primary.primary_tool}")
    print(f"Fallback Tool: {primary.fallback_tool}")

    assert primary.primary_tool == "pal", "Should select PAL apilookup for docs"
    assert primary.fallback_tool == "exa", "Should have Exa as fallback"
    print("✅ Test passed! PAL apilookup with Exa fallback")

    await orchestrator.close()


async def test_task_type_inference():
    """Test 6: Infer task type from natural language"""
    print("\n" + "="*70)
    print("Test 6: Task Type Inference")
    print("="*70)

    orchestrator = ToolOrchestrator(workspace_id="/Users/hue/code/dopemux-mvp")
    await orchestrator.initialize()

    test_cases = [
        ("Analyze why auth is broken", "analysis"),
        ("Debug the login error", "debugging"),
        ("Plan the database migration", "planning"),
        ("Review the authentication code", "code_review"),
        ("Find the calculateTotal function", "code_navigation"),
        ("Research React Server Components", "web_research"),
    ]

    all_passed = True
    for description, expected_type in test_cases:
        inferred = orchestrator._infer_task_type(description)
        match = inferred == expected_type
        status = "✅" if match else "❌"
        print(f"{status} '{description}' → {inferred} (expected: {expected_type})")
        if not match:
            all_passed = False

    assert all_passed, "All task types should be inferred correctly"
    print("\n✅ Test passed! Task type inference working")

    await orchestrator.close()


async def test_free_model_priority():
    """Test 7: FREE models prioritized for cost optimization"""
    print("\n" + "="*70)
    print("Test 7: FREE Model Priority (Cost Optimization)")
    print("="*70)

    orchestrator = ToolOrchestrator(workspace_id="/Users/hue/code/dopemux-mvp")
    await orchestrator.initialize()

    # Fast tier should prioritize FREE models
    model = await orchestrator.select_model_for_zen(
        tool_method="debug",
        complexity=0.2,
        performance_priority="fast"
    )

    print(f"\nSelected Model: {model}")
    model_info = orchestrator.available_models.get(model, {})
    cost = model_info.get("cost_per_1m", 999)
    print(f"Cost: ${cost} per 1M tokens")

    assert cost == 0.0, f"Should select FREE model, got cost ${cost}"
    print("✅ Test passed! FREE model prioritized (grok-4-fast)")

    await orchestrator.close()


async def test_metrics_tracking():
    """Test 8: Metrics accumulate correctly"""
    print("\n" + "="*70)
    print("Test 8: Metrics Tracking")
    print("="*70)

    orchestrator = ToolOrchestrator(workspace_id="/Users/hue/code/dopemux-mvp")
    await orchestrator.initialize()

    # Make several selections
    await orchestrator.select_tools_for_task("debugging", 0.2)  # Fast
    await orchestrator.select_tools_for_task("analysis", 0.5)  # Mid
    await orchestrator.select_tools_for_task("code_review", 0.9)  # Power

    metrics = await orchestrator.get_metrics_summary()

    print(f"\nMetrics:")
    print(f"  Total Selections: {metrics['total_selections']}")
    print(f"  Fast Tier: {metrics['fast_tier_pct']}%")
    print(f"  Mid Tier: {metrics['mid_tier_pct']}%")
    print(f"  Power Tier: {metrics['power_tier_pct']}%")

    assert metrics["total_selections"] == 3, "Should have 3 selections"
    assert metrics["fast_tier_pct"] > 0, "Should have fast tier selections"
    assert metrics["mid_tier_pct"] > 0, "Should have mid tier selections"
    assert metrics["power_tier_pct"] > 0, "Should have power tier selections"
    print("✅ Test passed! Metrics tracked correctly")

    await orchestrator.close()


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("WEEK 8: ToolOrchestrator Test Suite")
    print("="*70)

    tests = [
        ("Simple Task → Fast Model", test_simple_task_fast_model),
        ("Medium Task → Mid Model", test_medium_task_mid_model),
        ("Complex Task → Power Model", test_complex_task_power_model),
        ("Code Navigation → Serena", test_code_navigation_selection),
        ("Documentation → PAL apilookup + Fallback", test_documentation_with_fallback),
        ("Task Type Inference", test_task_type_inference),
        ("FREE Model Priority", test_free_model_priority),
        ("Metrics Tracking", test_metrics_tracking),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ Test '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*70)
    print(f"Test Results: {passed}/{len(tests)} passed")
    print("="*70)

    if failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
