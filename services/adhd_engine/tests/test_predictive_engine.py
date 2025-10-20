"""
Tests for Predictive ADHD Engine (IP-005 Days 11-12).

Validates:
- Energy level predictions with time/day matching
- Attention state predictions with session context
- Break timing predictions based on effectiveness patterns
- Confidence scoring and fallback logic
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml.predictive_engine import PredictiveADHDEngine
from ml.pattern_learner import EnergyPattern, AttentionPattern, BreakPattern
from models import EnergyLevel, AttentionState


@pytest.fixture
def workspace_id():
    """Test workspace ID."""
    return "/tmp/test-workspace"


@pytest.fixture
def predictive_engine(workspace_id):
    """Create predictive engine instance."""
    return PredictiveADHDEngine(workspace_id)


@pytest.fixture
def mock_energy_patterns():
    """Mock energy patterns for testing."""
    return [
        EnergyPattern(
            time_of_day=9,
            day_of_week=0,  # Monday
            energy_level=EnergyLevel.LOW.value,
            confidence=0.75,
            sample_count=15,
            last_observed=datetime.now(timezone.utc).isoformat()
        ),
        EnergyPattern(
            time_of_day=14,
            day_of_week=0,  # Monday
            energy_level=EnergyLevel.HIGH.value,
            confidence=0.82,
            sample_count=20,
            last_observed=datetime.now(timezone.utc).isoformat()
        ),
        EnergyPattern(
            time_of_day=9,
            day_of_week=5,  # Saturday
            energy_level=EnergyLevel.MEDIUM.value,
            confidence=0.68,
            sample_count=8,
            last_observed=datetime.now(timezone.utc).isoformat()
        )
    ]


@pytest.fixture
def mock_attention_patterns():
    """Mock attention patterns for testing."""
    return [
        AttentionPattern(
            warmup_minutes=15,
            peak_duration_minutes=45,
            optimal_session_length=75,
            confidence=0.71,
            sample_count=12,
            session_type="morning",
            last_observed=datetime.now(timezone.utc).isoformat()
        ),
        AttentionPattern(
            warmup_minutes=10,
            peak_duration_minutes=60,
            optimal_session_length=90,
            confidence=0.79,
            sample_count=18,
            session_type="afternoon",
            last_observed=datetime.now(timezone.utc).isoformat()
        )
    ]


@pytest.fixture
def mock_break_patterns():
    """Mock break patterns for testing."""
    return [
        BreakPattern(
            frequency_minutes=45,
            duration_minutes=5,
            effectiveness_score=0.75,
            confidence=0.80,
            sample_count=25,
            break_type="short",
            last_observed=datetime.now(timezone.utc).isoformat()
        ),
        BreakPattern(
            frequency_minutes=90,
            duration_minutes=15,
            effectiveness_score=0.65,
            confidence=0.72,
            sample_count=15,
            break_type="medium",
            last_observed=datetime.now(timezone.utc).isoformat()
        )
    ]


class TestEnergyPrediction:
    """Test energy level prediction."""

    @pytest.mark.asyncio
    async def test_predict_monday_9am_low_energy(self, predictive_engine, mock_energy_patterns):
        """Should predict LOW energy for Monday 9am based on patterns."""
        # Mock pattern cache
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": mock_energy_patterns, "attention": [], "breaks": []}

            # Predict for Monday 9am
            monday_9am = datetime(2025, 1, 6, 9, 0, tzinfo=timezone.utc)  # Monday
            predicted_energy, confidence, explanation = await predictive_engine.predict_energy_level(
                "test_user", monday_9am
            )

            assert predicted_energy == EnergyLevel.LOW.value, "Should predict LOW energy for Monday 9am"
            assert confidence == 0.75, "Confidence should match pattern"
            assert "Monday" in explanation and "9:00" in explanation

    @pytest.mark.asyncio
    async def test_predict_monday_2pm_high_energy(self, predictive_engine, mock_energy_patterns):
        """Should predict HIGH energy for Monday 2pm."""
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": mock_energy_patterns, "attention": [], "breaks": []}

            monday_2pm = datetime(2025, 1, 6, 14, 0, tzinfo=timezone.utc)
            predicted_energy, confidence, explanation = await predictive_engine.predict_energy_level(
                "test_user", monday_2pm
            )

            assert predicted_energy == EnergyLevel.HIGH.value
            assert confidence == 0.82

    @pytest.mark.asyncio
    async def test_fallback_to_time_of_day_pattern(self, predictive_engine, mock_energy_patterns):
        """Should fall back to hour-only pattern if exact day/hour not found."""
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": mock_energy_patterns, "attention": [], "breaks": []}

            # Tuesday 9am (no exact match, but 9am pattern exists for Monday)
            tuesday_9am = datetime(2025, 1, 7, 9, 0, tzinfo=timezone.utc)
            predicted_energy, confidence, explanation = await predictive_engine.predict_energy_level(
                "test_user", tuesday_9am
            )

            # Should still get a prediction based on time-of-day
            assert predicted_energy is not None
            assert confidence < 0.75  # Reduced confidence for cross-day generalization

    @pytest.mark.asyncio
    async def test_no_patterns_returns_medium(self, predictive_engine):
        """Should return MEDIUM energy with 0.0 confidence when no patterns exist."""
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": [], "attention": [], "breaks": []}

            predicted_energy, confidence, explanation = await predictive_engine.predict_energy_level("test_user")

            assert predicted_energy == EnergyLevel.MEDIUM.value
            assert confidence == 0.0
            assert "No historical data" in explanation


class TestAttentionPrediction:
    """Test attention state prediction."""

    @pytest.mark.asyncio
    async def test_predict_transitioning_during_warmup(self, predictive_engine, mock_attention_patterns):
        """Should predict TRANSITIONING state during warmup period."""
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": [], "attention": mock_attention_patterns, "breaks": []}

            # Morning session, 10 minutes in (still in warmup)
            context = {"session_type": "morning", "session_minutes_elapsed": 10}
            predicted_state, confidence, explanation = await predictive_engine.predict_attention_state(
                "test_user", context
            )

            assert predicted_state == AttentionState.TRANSITIONING.value
            assert ("warmup" in explanation.lower() or "peak focus" in explanation.lower())

    @pytest.mark.asyncio
    async def test_predict_focused_during_peak(self, predictive_engine, mock_attention_patterns):
        """Should predict FOCUSED state during peak attention period."""
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": [], "attention": mock_attention_patterns, "breaks": []}

            # Morning session, 30 minutes in (past warmup, in peak)
            context = {"session_type": "morning", "session_minutes_elapsed": 30}
            predicted_state, confidence, explanation = await predictive_engine.predict_attention_state(
                "test_user", context
            )

            assert predicted_state == AttentionState.FOCUSED.value
            assert "FOCUSED" in explanation

    @pytest.mark.asyncio
    async def test_predict_scattered_beyond_peak(self, predictive_engine, mock_attention_patterns):
        """Should predict SCATTERED state beyond optimal session length."""
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": [], "attention": mock_attention_patterns, "breaks": []}

            # Morning session, 80 minutes in (beyond optimal 75 min)
            context = {"session_type": "morning", "session_minutes_elapsed": 80}
            predicted_state, confidence, explanation = await predictive_engine.predict_attention_state(
                "test_user", context
            )

            assert predicted_state == AttentionState.SCATTERED.value
            assert "break" in explanation.lower()


class TestBreakTimingPrediction:
    """Test break timing prediction."""

    @pytest.mark.asyncio
    async def test_predict_break_in_45_minutes(self, predictive_engine, mock_break_patterns):
        """Should recommend break in 45 minutes based on most effective pattern."""
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": [], "attention": [], "breaks": mock_break_patterns}

            # No session info - should return optimal frequency
            minutes_until_break, confidence, explanation = await predictive_engine.predict_optimal_break_timing(
                "test_user"
            )

            # Should recommend short break pattern (45 min, higher effectiveness 0.75 vs 0.65)
            assert minutes_until_break == 45
            assert "45-minute" in explanation

    @pytest.mark.asyncio
    async def test_predict_break_needed_now(self, predictive_engine, mock_break_patterns):
        """Should recommend break immediately if interval exceeded."""
        with patch.object(predictive_engine, '_get_cached_patterns', new_callable=AsyncMock) as mock_cache:
            mock_cache.return_value = {"energy": [], "attention": [], "breaks": mock_break_patterns}

            # 50 minutes since last break (exceeded 45-minute optimal)
            minutes_until_break, confidence, explanation = await predictive_engine.predict_optimal_break_timing(
                "test_user", minutes_since_break=50
            )

            assert minutes_until_break == 0
            assert "Break recommended now" in explanation


class TestConfidenceThresholds:
    """Test confidence-based fallback logic."""

    def test_high_confidence_uses_ml(self, predictive_engine):
        """Predictions with confidence >= 0.5 should use ML."""
        explanation = predictive_engine.get_prediction_explanation(
            "test_user", "energy", "HIGH", confidence=0.75, sample_count=20
        )
        assert "High confidence" in explanation
        assert "20 observations" in explanation

    def test_low_confidence_fallback(self, predictive_engine):
        """Predictions with confidence < 0.5 should warn about fallback."""
        explanation = predictive_engine.get_prediction_explanation(
            "test_user", "energy", "MEDIUM", confidence=0.35, sample_count=5
        )
        assert "Low confidence" in explanation
        assert "rule-based fallback" in explanation
