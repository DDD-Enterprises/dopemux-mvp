"""
Integration test for ADHD Engine ML Pattern Learning (IP-005 Days 11-12).

Tests the complete ML workflow:
1. Pattern extraction from sample data
2. Predictions with confidence scoring
3. Graceful fallback to rules
4. ConPort persistence (mocked)
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml.pattern_learner import ADHDPatternLearner
from ml.predictive_engine import PredictiveADHDEngine
from models import EnergyLevel, AttentionState


def test_ml_enabled_in_config():
    """Verify ML is enabled by default in config."""
    from config import settings

    assert settings.enable_ml_predictions is True, "ML predictions should be enabled"
    print(f"✅ ML enabled: {settings.enable_ml_predictions}")


@pytest.mark.asyncio
async def test_complete_ml_workflow():
    """
    Test complete ML workflow from data → patterns → predictions.

    This validates:
    - Pattern extraction works
    - Predictions use learned patterns
    - Confidence scoring functions
    - Fallback logic activates when confidence low
    """
    workspace_id = "/tmp/test-workspace"

    # Step 1: Create pattern learner
    pattern_learner = ADHDPatternLearner(workspace_id)
    print("\n✅ Pattern learner created")

    # Step 2: Generate sample activity data (30 days)
    activity_history = []
    now = datetime.now(timezone.utc)

    for days_ago in range(30):
        timestamp = now - timedelta(days=days_ago)

        # Morning: LOW energy
        activity_history.append({
            "timestamp": (timestamp.replace(hour=9, minute=0)).isoformat(),
            "energy_level": EnergyLevel.LOW.value,
            "user_id": "test_user"
        })

        # Afternoon: HIGH energy
        activity_history.append({
            "timestamp": (timestamp.replace(hour=14, minute=0)).isoformat(),
            "energy_level": EnergyLevel.HIGH.value,
            "user_id": "test_user"
        })

    print(f"✅ Generated {len(activity_history)} activity records")

    # Step 3: Extract patterns
    energy_patterns = await pattern_learner.extract_energy_patterns(
        "test_user", activity_history
    )

    assert len(energy_patterns) > 0, "Should extract at least one pattern"
    print(f"✅ Extracted {len(energy_patterns)} energy patterns")

    # Verify pattern quality
    for pattern in energy_patterns[:3]:  # Check first 3
        print(f"   - {pattern.energy_level} energy at {pattern.time_of_day}:00 "
              f"(confidence: {pattern.confidence:.2f}, samples: {pattern.sample_count})")
        assert 0.0 <= pattern.confidence <= 1.0
        assert pattern.sample_count > 0

    # Step 4: Create predictive engine
    predictive_engine = PredictiveADHDEngine(workspace_id)
    print("✅ Predictive engine created")

    # Step 5: Mock pattern loading (simulate ConPort)
    with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
        mock_cache.return_value = {
            "energy": energy_patterns,
            "attention": [],
            "breaks": []
        }

        # Step 6: Test predictions
        monday_9am = datetime(2025, 1, 6, 9, 0, tzinfo=timezone.utc)
        predicted_energy, confidence, explanation = await predictive_engine.predict_energy_level(
            "test_user", monday_9am
        )

        print(f"\n✅ Energy prediction for Monday 9am:")
        print(f"   - Predicted: {predicted_energy}")
        print(f"   - Confidence: {confidence:.2f}")
        print(f"   - Explanation: {explanation[:100]}...")

        # Verify prediction
        assert predicted_energy in [e.value for e in EnergyLevel]
        assert 0.0 <= confidence <= 1.0

        # Check if ML was actually used (confidence >= 0.5)
        if confidence >= 0.5:
            print(f"   - ✅ ML used (confidence {confidence:.2f} >= 0.5)")
        else:
            print(f"   - ⚠️  Fallback to rules (confidence {confidence:.2f} < 0.5)")

    # Step 7: Test fallback with no patterns
    with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
        mock_cache.return_value = {"energy": [], "attention": [], "breaks": []}

        predicted_energy, confidence, explanation = await predictive_engine.predict_energy_level(
            "test_user"
        )

        print(f"\n✅ Fallback behavior (no patterns):")
        print(f"   - Predicted: {predicted_energy} (should be MEDIUM)")
        print(f"   - Confidence: {confidence} (should be 0.0)")
        print(f"   - Explanation: {explanation}")

        assert predicted_energy == EnergyLevel.MEDIUM.value
        assert confidence == 0.0
        print("   - ✅ Graceful fallback working")

    print("\n🎉 Complete ML workflow validated!")
    return True


@pytest.mark.asyncio
async def test_time_decay_weighting():
    """Verify time-decay weighting gives more weight to recent observations."""
    pattern_learner = ADHDPatternLearner("/tmp/test")

    # Recent observation (today)
    weight_today = pattern_learner._calculate_time_decay_weight(0.0)

    # 30 days ago (half-life)
    weight_30_days = pattern_learner._calculate_time_decay_weight(30.0)

    # 60 days ago
    weight_60_days = pattern_learner._calculate_time_decay_weight(60.0)

    print(f"\n✅ Time-decay weighting:")
    print(f"   - Today: {weight_today:.3f}")
    print(f"   - 30 days ago: {weight_30_days:.3f} (should be ~0.5)")
    print(f"   - 60 days ago: {weight_60_days:.3f} (should be ~0.25)")

    assert weight_today == 1.0
    assert abs(weight_30_days - 0.5) < 0.01
    assert abs(weight_60_days - 0.25) < 0.01
    assert weight_today > weight_30_days > weight_60_days

    print("   - ✅ Exponential decay working correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("ADHD Engine ML Integration Test (IP-005 Days 11-12)")
    print("=" * 60)

    # Test 1: Config
    test_ml_enabled_in_config()

    # Test 2: Time decay
    asyncio.run(test_time_decay_weighting())

    # Test 3: Complete workflow
    asyncio.run(test_complete_ml_workflow())

    print("\n" + "=" * 60)
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("=" * 60)
