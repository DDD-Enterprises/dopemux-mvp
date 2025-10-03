"""
Unit tests for ADHD Accommodation Engine core logic.
"""

import pytest
from adhd_engine.engine import ADHDAccommodationEngine
from adhd_engine.models import EnergyLevel, AttentionState, CognitiveLoadLevel, ADHDProfile


class TestCognitiveLoadCalculation:
    """Test cognitive load calculation accuracy."""

    def test_base_complexity_factor(self):
        """Low complexity task should have moderate cognitive load."""
        engine = ADHDAccommodationEngine()

        load = engine._calculate_task_cognitive_load(
            complexity=0.3,
            duration=15,
            task_data={"description": "simple refactor", "dependencies": []}
        )

        # Calculation: base(0.12) + duration(0.25) + task_type(0.2) = 0.57
        assert 0.5 <= load <= 0.6, f"Expected moderate load, got {load}"

    def test_duration_factor_impact(self):
        """Longer tasks should have higher cognitive load."""
        engine = ADHDAccommodationEngine()

        short_load = engine._calculate_task_cognitive_load(0.5, 15, {"description": "task", "dependencies": []})
        long_load = engine._calculate_task_cognitive_load(0.5, 90, {"description": "task", "dependencies": []})

        assert long_load > short_load, "Longer tasks should have higher cognitive load"

    def test_task_type_detection(self):
        """Debugging should have higher load than documentation."""
        engine = ADHDAccommodationEngine()

        debug_load = engine._calculate_task_cognitive_load(
            0.5, 25, {"description": "debugging authentication issue", "dependencies": []}
        )
        docs_load = engine._calculate_task_cognitive_load(
            0.5, 25, {"description": "update documentation", "dependencies": []}
        )

        assert debug_load > docs_load, "Debugging should have higher cognitive load than docs"

    def test_dependency_impact(self):
        """Tasks with more dependencies should have higher load."""
        engine = ADHDAccommodationEngine()

        no_deps = engine._calculate_task_cognitive_load(
            0.5, 25, {"description": "task", "dependencies": []}
        )
        many_deps = engine._calculate_task_cognitive_load(
            0.5, 25, {"description": "task", "dependencies": ["dep1", "dep2", "dep3"]}
        )

        assert many_deps > no_deps, "Tasks with dependencies should have higher load"


class TestEnergyMatching:
    """Test energy level task matching."""

    def test_perfect_match_high_score(self):
        """Medium energy + medium load = perfect match."""
        engine = ADHDAccommodationEngine()
        profile = ADHDProfile(user_id="test")

        score = engine._assess_energy_match(
            EnergyLevel.MEDIUM,
            cognitive_load=0.6,
            profile=profile
        )

        assert score >= 0.9, f"Expected high score for perfect match, got {score}"

    def test_mismatch_penalty(self):
        """Low energy + high load = poor match."""
        engine = ADHDAccommodationEngine()
        profile = ADHDProfile(user_id="test")

        score = engine._assess_energy_match(
            EnergyLevel.LOW,
            cognitive_load=0.9,
            profile=profile
        )

        assert score < 0.5, f"Expected low score for energy mismatch, got {score}"

    def test_hyperfocus_bonus(self):
        """Hyperfocus tendency should boost energy match."""
        engine = ADHDAccommodationEngine()
        profile = ADHDProfile(user_id="test", hyperfocus_tendency=0.9)

        score = engine._assess_energy_match(
            EnergyLevel.HYPERFOCUS,
            cognitive_load=0.8,
            profile=profile
        )

        assert score >= 0.8, f"Expected high score with hyperfocus bonus, got {score}"


class TestAttentionCompatibility:
    """Test attention state compatibility assessment."""

    def test_scattered_rejects_complex(self):
        """Scattered state should reject complex tasks."""
        engine = ADHDAccommodationEngine()

        compat = engine._assess_attention_compatibility(
            AttentionState.SCATTERED,
            {"estimated_minutes": 60, "description": "complex task"},
            cognitive_load=0.8
        )

        assert compat < 0.3, f"Scattered state should reject complex tasks, got {compat}"

    def test_focused_accepts_complex(self):
        """Focused state should accept complex tasks."""
        engine = ADHDAccommodationEngine()

        compat = engine._assess_attention_compatibility(
            AttentionState.FOCUSED,
            {"estimated_minutes": 25, "description": "task"},
            cognitive_load=0.7
        )

        assert compat > 0.7, f"Focused state should accept complex tasks, got {compat}"

    def test_overwhelmed_rejects_all(self):
        """Overwhelmed state should reject even simple tasks."""
        engine = ADHDAccommodationEngine()

        compat = engine._assess_attention_compatibility(
            AttentionState.OVERWHELMED,
            {"estimated_minutes": 10, "description": "simple"},
            cognitive_load=0.3
        )

        assert compat < 0.5, f"Overwhelmed state should reject tasks, got {compat}"


class TestCognitiveLoadCategorization:
    """Test cognitive load categorization."""

    def test_load_categories(self):
        """Verify all cognitive load levels categorize correctly."""
        engine = ADHDAccommodationEngine()

        assert engine._categorize_cognitive_load(0.1) == CognitiveLoadLevel.MINIMAL
        assert engine._categorize_cognitive_load(0.3) == CognitiveLoadLevel.LOW
        assert engine._categorize_cognitive_load(0.5) == CognitiveLoadLevel.MODERATE
        assert engine._categorize_cognitive_load(0.7) == CognitiveLoadLevel.HIGH
        assert engine._categorize_cognitive_load(0.9) == CognitiveLoadLevel.EXTREME
