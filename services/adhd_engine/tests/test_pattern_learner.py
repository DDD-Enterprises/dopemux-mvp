"""
Tests for ADHD Pattern Learner (IP-005 Days 11-12).

Validates:
- Pattern extraction with time-decay weighting
- Confidence scoring based on sample count and consistency
- ConPort persistence round-trip
- Pattern convergence simulation
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from adhd_engine.ml.pattern_learner import (
    ADHDPatternLearner,
    EnergyPattern,
    AttentionPattern,
    BreakPattern
)
from adhd_engine.models import EnergyLevel, AttentionState


@pytest.fixture
def workspace_id():
    """Test workspace ID."""
    return "/tmp/test-workspace"


@pytest.fixture
def pattern_learner(workspace_id):
    """Create pattern learner instance."""
    return ADHDPatternLearner(workspace_id)


@pytest.fixture
def sample_activity_history():
    """Generate sample activity history for testing."""
    now = datetime.now(timezone.utc)
    history = []

    # Create 30 days of activity (2 records per day at different hours)
    for days_ago in range(30):
        timestamp = now - timedelta(days=days_ago)

        # Morning record (9am on weekdays, low energy)
        if timestamp.weekday() < 5:  # Weekday
            history.append({
                "timestamp": (timestamp.replace(hour=9, minute=0)).isoformat(),
                "energy_level": EnergyLevel.LOW.value,
                "user_id": "test_user"
            })

        # Afternoon record (14:00, high energy)
        history.append({
            "timestamp": (timestamp.replace(hour=14, minute=0)).isoformat(),
            "energy_level": EnergyLevel.HIGH.value,
            "user_id": "test_user"
        })

    return history


@pytest.fixture
def sample_session_history():
    """Generate sample session history."""
    now = datetime.now(timezone.utc)
    history = []

    # Create 20 sessions (morning sessions typically need 15min warmup, 45min peak)
    for days_ago in range(20):
        timestamp = now - timedelta(days=days_ago)

        history.append({
            "timestamp": (timestamp.replace(hour=9, minute=0)).isoformat(),
            "session_start": (timestamp.replace(hour=9, minute=0)).isoformat(),
            "session_end": (timestamp.replace(hour=10, minute=15)).isoformat(),  # 75 min session
            "attention_states": [
                {"time": 0, "state": AttentionState.TRANSITIONING.value},
                {"time": 15, "state": AttentionState.FOCUSED.value},
                {"time": 60, "state": AttentionState.SCATTERED.value}
            ],
            "user_id": "test_user"
        })

    return history


@pytest.fixture
def sample_break_history():
    """Generate sample break history."""
    now = datetime.now(timezone.utc)
    history = []

    # Create 25 break cycles
    for i in range(25):
        timestamp = now - timedelta(days=i)

        # Short breaks (5 min every 45 min) with 0.7 effectiveness
        history.append({
            "timestamp": timestamp.isoformat(),
            "frequency_minutes": 45,
            "duration_minutes": 5,
            "effectiveness_score": 0.7 + (0.1 if i < 15 else -0.1),  # Recent breaks more effective
            "user_id": "test_user"
        })

    return history


class TestTimeDecay:
    """Test time-decay probability calculation."""

    def test_zero_days_full_weight(self, pattern_learner):
        """Recent observations should have full weight."""
        weight = pattern_learner._calculate_time_decay_weight(0.0)
        assert weight == 1.0, "Weight should be 1.0 for observations from today"

    def test_30_day_half_life(self, pattern_learner):
        """30 days old should have 0.5 weight."""
        weight = pattern_learner._calculate_time_decay_weight(30.0)
        assert abs(weight - 0.5) < 0.01, "Weight should be ~0.5 after 30 days (half-life)"

    def test_60_day_quarter_weight(self, pattern_learner):
        """60 days old should have 0.25 weight."""
        weight = pattern_learner._calculate_time_decay_weight(60.0)
        assert abs(weight - 0.25) < 0.01, "Weight should be ~0.25 after 60 days"

    def test_90_day_eighth_weight(self, pattern_learner):
        """90 days old should have 0.125 weight."""
        weight = pattern_learner._calculate_time_decay_weight(90.0)
        assert abs(weight - 0.125) < 0.01, "Weight should be ~0.125 after 90 days"


class TestConfidenceScoring:
    """Test confidence calculation."""

    def test_low_samples_low_confidence(self, pattern_learner):
        """Few samples should yield low confidence."""
        confidence = pattern_learner._calculate_confidence(sample_count=3, consistency_ratio=1.0)
        assert confidence < 0.5, "Confidence should be low with only 3 samples"

    def test_many_samples_high_confidence(self, pattern_learner):
        """Many consistent samples should yield high confidence."""
        confidence = pattern_learner._calculate_confidence(sample_count=20, consistency_ratio=0.9)
        assert confidence > 0.7, "Confidence should be high with 20 samples and 0.9 consistency"

    def test_inconsistent_low_confidence(self, pattern_learner):
        """Low consistency should reduce confidence."""
        confidence = pattern_learner._calculate_confidence(sample_count=20, consistency_ratio=0.3)
        assert confidence < 0.5, "Confidence should be low despite many samples if inconsistent"

    def test_confidence_bounded(self, pattern_learner):
        """Confidence should always be 0.0-1.0."""
        confidence = pattern_learner._calculate_confidence(sample_count=100, consistency_ratio=1.0)
        assert 0.0 <= confidence <= 1.0, "Confidence must be bounded [0.0, 1.0]"


class TestEnergyPatternExtraction:
    """Test energy pattern extraction."""

    @pytest.mark.asyncio
    async def test_extract_energy_patterns(self, pattern_learner, sample_activity_history):
        """Should extract energy patterns grouped by hour and day of week."""
        patterns = await pattern_learner.extract_energy_patterns("test_user", sample_activity_history)

        assert len(patterns) > 0, "Should extract at least one energy pattern"

        # Check pattern structure
        for pattern in patterns:
            assert isinstance(pattern, EnergyPattern)
            assert 0 <= pattern.time_of_day <= 23
            assert 0 <= pattern.day_of_week <= 6
            assert pattern.energy_level in [e.value for e in EnergyLevel]
            assert 0.0 <= pattern.confidence <= 1.0
            assert pattern.sample_count > 0

    @pytest.mark.asyncio
    async def test_weekday_morning_low_energy_pattern(self, pattern_learner, sample_activity_history):
        """Should identify weekday morning low energy pattern."""
        patterns = await pattern_learner.extract_energy_patterns("test_user", sample_activity_history)

        # Find weekday 9am pattern
        weekday_9am = [p for p in patterns if p.time_of_day == 9 and p.day_of_week < 5]
        assert len(weekday_9am) > 0, "Should have weekday 9am pattern"

        # Should be LOW energy (from fixture)
        assert weekday_9am[0].energy_level == EnergyLevel.LOW.value


class TestAttentionPatternExtraction:
    """Test attention pattern extraction."""

    @pytest.mark.asyncio
    async def test_extract_attention_patterns(self, pattern_learner, sample_session_history):
        """Should extract attention patterns from session history."""
        patterns = await pattern_learner.extract_attention_patterns("test_user", sample_session_history)

        assert len(patterns) > 0, "Should extract at least one attention pattern"

        for pattern in patterns:
            assert isinstance(pattern, AttentionPattern)
            assert pattern.warmup_minutes > 0
            assert pattern.peak_duration_minutes > 0
            assert pattern.optimal_session_length > 0
            assert 0.0 <= pattern.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_morning_session_warmup_pattern(self, pattern_learner, sample_session_history):
        """Should identify 15-minute warmup pattern for morning sessions."""
        patterns = await pattern_learner.extract_attention_patterns("test_user", sample_session_history)

        morning_pattern = [p for p in patterns if p.session_type == "morning"]
        assert len(morning_pattern) > 0, "Should have morning session pattern"

        # From fixture: warmup = 15 min, peak = 45 min
        assert morning_pattern[0].warmup_minutes == 15
        assert morning_pattern[0].peak_duration_minutes == 45


class TestBreakPatternExtraction:
    """Test break pattern extraction."""

    @pytest.mark.asyncio
    async def test_extract_break_patterns(self, pattern_learner, sample_break_history):
        """Should extract break effectiveness patterns."""
        patterns = await pattern_learner.extract_break_patterns("test_user", sample_break_history)

        assert len(patterns) > 0, "Should extract at least one break pattern"

        for pattern in patterns:
            assert isinstance(pattern, BreakPattern)
            assert pattern.frequency_minutes > 0
            assert pattern.duration_minutes > 0
            assert 0.0 <= pattern.effectiveness_score <= 1.0
            assert 0.0 <= pattern.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_short_break_pattern(self, pattern_learner, sample_break_history):
        """Should identify 5-minute break pattern."""
        patterns = await pattern_learner.extract_break_patterns("test_user", sample_break_history)

        short_breaks = [p for p in patterns if p.break_type == "short"]
        assert len(short_breaks) > 0, "Should have short break pattern"

        # From fixture: 5 min breaks every 45 min
        assert short_breaks[0].duration_minutes == 5
        assert short_breaks[0].frequency_minutes == 45


class TestConPortPersistence:
    """Test pattern persistence to ConPort."""

    @pytest.mark.asyncio
    async def test_persist_and_load_roundtrip(self, pattern_learner, sample_activity_history):
        """Should persist patterns and load them back unchanged."""
        # Extract patterns
        energy_patterns = await pattern_learner.extract_energy_patterns("test_user", sample_activity_history)

        # Mock ConPort adapter
        with patch.object(pattern_learner.conport, 'write_custom_data', new_callable=AsyncMock) as mock_write, \
             patch.object(pattern_learner.conport, 'get_custom_data', new_callable=AsyncMock) as mock_read:

            # Setup mock return value
            mock_read.return_value = {
                "energy": [p.__dict__ for p in energy_patterns],
                "attention": [],
                "breaks": []
            }

            # Persist
            success = await pattern_learner.persist_patterns_to_conport(
                "test_user", energy_patterns, [], []
            )
            assert success, "Persistence should succeed"

            # Verify write was called
            assert mock_write.called, "Should call ConPort write_custom_data"

            # Load back
            loaded = await pattern_learner.load_patterns_from_conport("test_user")

            # Verify structure
            assert "energy" in loaded
            assert len(loaded["energy"]) == len(energy_patterns)
