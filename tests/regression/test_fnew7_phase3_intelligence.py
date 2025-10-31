"""
F-NEW-7 Phase 3 Pattern Correlation Tests

Validates cross-agent intelligence pattern detection.

Run: python test_fnew7_phase3_intelligence.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "services" / "intelligence"))

from pattern_correlation_engine import (
    PatternCorrelationEngine,
    IntelligenceType
)


async def test_imports():
    """Test 1: Import pattern correlation engine"""
    print("Test 1: Imports...")
    try:
        from pattern_correlation_engine import PatternCorrelationEngine
        print("  ✅ PatternCorrelationEngine imported\n")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}\n")
        return False


async def test_complexity_cluster_detection():
    """Test 2: Complexity cluster detection"""
    print("Test 2: Complexity cluster detection...")

    engine = PatternCorrelationEngine()

    # Simulate 3 high-complexity events in same directory
    for i in range(3):
        event = {
            'id': f'evt-{i}',
            'type': 'code.complexity.high',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'file': f'services/auth/module_{i}.py',
                'complexity': 0.8 + (i * 0.05)
            }
        }
        insight = await engine.on_event(event)

    # Third event should trigger cluster detection
    if insight and insight.insight_type == IntelligenceType.PATTERN_CLUSTER:
        print(f"  ✅ Cluster detected: {insight.title}")
        print(f"     Priority: {insight.priority}")
        print(f"     Confidence: {insight.confidence}\n")
        return True
    else:
        print(f"  ❌ Cluster not detected (expected after 3 events)\n")
        return False


async def test_cognitive_code_mismatch():
    """Test 3: Cognitive-code mismatch detection"""
    print("Test 3: Cognitive-code mismatch...")

    engine = PatternCorrelationEngine()

    # Low energy state
    cognitive_event = {
        'id': 'cog-1',
        'type': 'cognitive.state.change',
        'timestamp': datetime.now().isoformat(),
        'data': {'energy': 'low', 'attention': 'scattered'}
    }
    await engine.on_event(cognitive_event)

    # High complexity code event
    complexity_event = {
        'id': 'comp-1',
        'type': 'code.complexity.high',
        'timestamp': datetime.now().isoformat(),
        'data': {'file': 'auth.py', 'complexity': 0.85}
    }
    insight = await engine.on_event(complexity_event)

    if insight and insight.insight_type == IntelligenceType.COGNITIVE_CODE:
        print(f"  ✅ Mismatch detected: {insight.title}")
        print(f"     Priority: {insight.priority} (expected: critical)")
        print(f"     Action: {insight.recommended_action}\n")
        return insight.priority == "critical"
    else:
        print(f"  ❌ Mismatch not detected\n")
        return False


async def main():
    """Run all pattern correlation tests"""
    print("=" * 70)
    print("F-NEW-7 Phase 3: Pattern Correlation Engine Tests")
    print("=" * 70)
    print()

    import asyncio
    results = []

    results.append(await test_imports())
    results.append(await test_complexity_cluster_detection())
    results.append(await test_cognitive_code_mismatch())

    print("=" * 70)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)

    if sum(results) == len(results):
        print("✅ PHASE 3 PATTERN CORRELATION VALIDATED!")
        return 0
    else:
        print(f"❌ {len(results) - sum(results)} test(s) failed")
        return 1


if __name__ == "__main__":
    import asyncio
    exit(asyncio.run(main()))
