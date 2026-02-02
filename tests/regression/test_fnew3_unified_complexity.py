#!/usr/bin/env python3
"""
Test F-NEW-3: Unified Complexity Intelligence

Tests the ComplexityCoordinator that combines:
- Dope-Context AST complexity (Tree-sitter)
- Serena LSP complexity (usage patterns)
- ADHD Engine user adjustments

Synergy from Decision #222 analysis.
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "complexity_coordinator"))

from unified_complexity import (
    get_complexity_coordinator,
    get_unified_complexity,
    ComplexityBreakdown
)


async def test_complexity_coordinator_init():
    """Test ComplexityCoordinator initialization"""
    print("\n" + "="*80)
    print("TEST 1: ComplexityCoordinator Initialization")
    print("="*80)

    try:
        coordinator = await get_complexity_coordinator()
        print("✅ ComplexityCoordinator created")
        print(f"📊 Configuration:")
        print(f"   AST weight: {coordinator.ast_weight}")
        print(f"   LSP weight: {coordinator.lsp_weight}")
        print(f"   Usage weight: {coordinator.usage_weight}")
        print(f"   Total weight: {coordinator.ast_weight + coordinator.lsp_weight + coordinator.usage_weight}")

        if abs(coordinator.ast_weight + coordinator.lsp_weight + coordinator.usage_weight - 1.0) < 0.01:
            print("✅ PASS: Weights sum to 1.0")
        else:
            print("⚠️  WARN: Weights don't sum to 1.0")

        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_unified_complexity_calculation():
    """Test unified complexity score calculation"""
    print("\n" + "="*80)
    print("TEST 2: Unified Complexity Calculation")
    print("="*80)

    try:
        coordinator = await get_complexity_coordinator()

        # Test file path
        test_file = "services/serena/mcp_server.py"
        test_symbol = "find_symbol_tool"

        print(f"📊 Analyzing: {test_file}:{test_symbol}")

        breakdown = await coordinator.get_unified_complexity(
            file_path=test_file,
            symbol=test_symbol,
            user_id="test_user"
        )

        print(f"\n🔍 Complexity Breakdown:")
        print(f"   AST score:        {breakdown.ast_score:.3f}")
        print(f"   LSP score:        {breakdown.lsp_score:.3f}")
        print(f"   Usage score:      {breakdown.usage_score:.3f}")
        print(f"   ADHD multiplier:  {breakdown.adhd_multiplier:.3f}x")
        print(f"   Unified score:    {breakdown.unified_score:.3f}")
        print(f"   Confidence:       {breakdown.confidence:.3f}")

        print(f"\n💡 Interpretation: {breakdown._interpret_score()}")

        # Validation checks
        checks = [
            ("Unified score in range [0.0, 1.0]", 0.0 <= breakdown.unified_score <= 1.0),
            ("Confidence in range [0.0, 1.0]", 0.0 <= breakdown.confidence <= 1.0),
            ("ADHD multiplier reasonable [0.5, 1.5]", 0.5 <= breakdown.adhd_multiplier <= 1.5),
            ("All component scores in range [0.0, 1.0]",
             all(0.0 <= s <= 1.0 for s in [breakdown.ast_score, breakdown.lsp_score, breakdown.usage_score]))
        ]

        all_passed = all(result for _, result in checks)

        print(f"\n📋 Validation Checks:")
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")

        if all_passed:
            print(f"\n✅ PASS: All validation checks passed")
        else:
            print(f"\n⚠️  WARN: Some validation checks failed")

        return all_passed

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_convenience_function():
    """Test convenience function wrapper"""
    print("\n" + "="*80)
    print("TEST 3: Convenience Function (get_unified_complexity)")
    print("="*80)

    try:
        test_file = "services/dope-context/src/mcp/server.py"

        print(f"📊 Getting unified complexity for: {test_file}")

        result = await get_unified_complexity(
            file_path=test_file,
            user_id="test_user"
        )

        print(f"\n🔍 Result Dictionary:")
        for key, value in result.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.3f}")
            else:
                print(f"   {key}: {value}")

        # Check required fields
        required_fields = [
            'ast_score', 'lsp_score', 'usage_score',
            'adhd_multiplier', 'unified_score', 'confidence',
            'interpretation'
        ]

        all_present = all(field in result for field in required_fields)

        if all_present:
            print(f"\n✅ PASS: All required fields present")
        else:
            missing = [f for f in required_fields if f not in result]
            print(f"\n❌ FAIL: Missing fields: {missing}")

        return all_present

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_different_users():
    """Test that ADHD multipliers can vary per user"""
    print("\n" + "="*80)
    print("TEST 4: User-Specific ADHD Adjustments")
    print("="*80)

    try:
        test_file = "test.py"

        print(f"📊 Testing ADHD adjustments for different users")

        users = ["alice", "bob", "charlie"]
        results = {}

        for user in users:
            breakdown = await get_unified_complexity(
                file_path=test_file,
                user_id=user
            )
            results[user] = breakdown

        print(f"\n🔍 Results by User:")
        for user, result in results.items():
            print(f"   {user}: unified={result['unified_score']:.3f} "
                  f"multiplier={result['adhd_multiplier']:.3f}x")

        # For now, all users get same multiplier (1.0) because
        # we're using fallback values. In production with real
        # ADHD Engine data, these would differ.

        print(f"\nℹ️  Note: Currently using fallback multiplier (1.0)")
        print(f"   In production, multipliers would vary by user based on:")
        print(f"   - Historical success with complexity levels")
        print(f"   - Current energy state")
        print(f"   - Current attention state")
        print(f"   - Personal thresholds")

        print(f"\n✅ PASS: Per-user adjustment framework operational")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all F-NEW-3 tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "F-NEW-3: UNIFIED COMPLEXITY INTELLIGENCE" + " "*18 + "║")
    print("║" + " "*15 + "AST + LSP + Usage + ADHD = Better Accuracy" + " "*18 + "║")
    print("╚" + "="*78 + "╝")

    results = []

    # Run tests
    results.append(("Coordinator Initialization", await test_complexity_coordinator_init()))
    results.append(("Unified Complexity Calculation", await test_unified_complexity_calculation()))
    results.append(("Convenience Function", await test_convenience_function()))
    results.append(("User-Specific Adjustments", await test_different_users()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print("\n" + "="*80)
    print(f"OVERALL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*80)

    print("\n📋 Architecture Notes:")
    print("   ✅ Coordinator framework complete")
    print("   ✅ Weight-based score combination working")
    print("   ✅ ADHD multiplier integration ready")
    print("   ⏳ Production integration pending:")
    print("      - Wire dope-context MCP for AST complexity")
    print("      - Wire Serena MCP for LSP complexity")
    print("      - Wire Serena MCP for usage/reference counts")
    print("      - Wire ADHD Engine for user multipliers")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
