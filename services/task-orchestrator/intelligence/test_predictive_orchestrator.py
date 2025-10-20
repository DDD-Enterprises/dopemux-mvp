"""
Unit tests for Predictive Task Orchestrator (Week 3).

Tests rule-based recommendation system:
- Energy-complexity matching
- Composite scoring algorithm
- Recommendation generation
- Rationale generation
"""

import pytest
from datetime import datetime, timedelta

from .predictive_orchestrator import (
    RuleBasedRecommender,
    RecommendationContext,
    RecommendationSource,
    TaskRecommendation,
)


# ============================================================================
# Test Fixtures
# ============================================================================

class MockTask:
    """Mock task for testing."""
    def __init__(self, task_id, description, complexity, priority="medium",
                 estimated_duration=60, dependencies=None, created_at=None):
        self.task_id = task_id
        self.description = description
        self.complexity = complexity
        self.priority = priority
        self.estimated_duration = estimated_duration
        self.dependencies = dependencies or []
        self.created_at = created_at or datetime.now()


@pytest.fixture
def recommender():
    """Create RuleBasedRecommender instance."""
    return RuleBasedRecommender()


@pytest.fixture
def sample_tasks():
    """Create sample tasks with varying complexity."""
    return [
        MockTask("task-1", "Simple docs update", 0.2, "low", 15),
        MockTask("task-2", "Moderate feature work", 0.5, "medium", 60),
        MockTask("task-3", "Complex architecture", 0.9, "high", 120),
        MockTask("task-4", "Quick bug fix", 0.3, "high", 30),
    ]


# ============================================================================
# Energy-Complexity Matching Tests
# ============================================================================

@pytest.mark.asyncio
async def test_low_energy_recommends_simple_tasks(recommender, sample_tasks):
    """Test that low energy state recommends only simple tasks."""
    context = RecommendationContext(
        energy_level="low",
        attention_level="scattered",
        cognitive_load=0.3,
        candidate_tasks=sample_tasks
    )

    recommendations = await recommender.recommend_tasks(context, limit=3)

    # Should recommend simple tasks (complexity < 0.4)
    for rec in recommendations:
        assert rec.task.complexity <= 0.4, \
            f"Low energy should not recommend complex task (complexity={rec.task.complexity})"


@pytest.mark.asyncio
async def test_hyperfocus_recommends_complex_tasks(recommender, sample_tasks):
    """Test that hyperfocus state recommends complex tasks."""
    context = RecommendationContext(
        energy_level="hyperfocus",
        attention_level="hyperfocused",
        cognitive_load=0.5,
        candidate_tasks=sample_tasks
    )

    recommendations = await recommender.recommend_tasks(context, limit=3)

    # Should recommend complex tasks (complexity >= 0.8)
    assert any(rec.task.complexity >= 0.8 for rec in recommendations), \
        "Hyperfocus should recommend at least one complex task"


@pytest.mark.asyncio
async def test_medium_energy_balanced_recommendations(recommender, sample_tasks):
    """Test that medium energy recommends moderate complexity tasks."""
    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=sample_tasks
    )

    recommendations = await recommender.recommend_tasks(context, limit=3)

    # Should recommend tasks in moderate complexity range (0.3-0.7)
    for rec in recommendations:
        assert 0.3 <= rec.task.complexity <= 0.7, \
            f"Medium energy should recommend moderate tasks (complexity={rec.task.complexity})"


# ============================================================================
# Scoring Algorithm Tests
# ============================================================================

@pytest.mark.asyncio
async def test_high_priority_scores_higher(recommender):
    """Test that high priority tasks score higher than low priority."""
    high_priority = MockTask("high", "High priority task", 0.5, "high", 60)
    low_priority = MockTask("low", "Low priority task", 0.5, "low", 60)

    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=[high_priority, low_priority]
    )

    recommendations = await recommender.recommend_tasks(context, limit=2)

    # High priority should be recommended first
    assert recommendations[0].task.task_id == "high", \
        "High priority task should be ranked first"


@pytest.mark.asyncio
async def test_unblocked_tasks_prioritized(recommender):
    """Test that tasks without dependencies are prioritized."""
    blocked = MockTask("blocked", "Blocked task", 0.5, "high", 60,
                      dependencies=["dep-1", "dep-2"])
    unblocked = MockTask("unblocked", "Unblocked task", 0.5, "high", 60,
                        dependencies=[])

    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=[blocked, unblocked]
    )

    recommendations = await recommender.recommend_tasks(context, limit=2)

    # Unblocked should score higher
    assert recommendations[0].task.task_id == "unblocked", \
        "Unblocked task should be ranked first"


@pytest.mark.asyncio
async def test_short_duration_preferred_when_low_energy(recommender):
    """Test that short tasks are preferred when energy is low."""
    short_task = MockTask("short", "Short task", 0.2, "medium", 15)
    long_task = MockTask("long", "Long task", 0.3, "medium", 90)

    context = RecommendationContext(
        energy_level="low",
        attention_level="scattered",
        cognitive_load=0.4,
        candidate_tasks=[short_task, long_task]
    )

    recommendations = await recommender.recommend_tasks(context, limit=2)

    # Short task should be first
    assert recommendations[0].task.task_id == "short", \
        "Short task should be recommended first when energy is low"


# ============================================================================
# Recommendation Limit Tests
# ============================================================================

@pytest.mark.asyncio
async def test_respects_recommendation_limit(recommender, sample_tasks):
    """Test that recommender respects the limit parameter."""
    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=sample_tasks
    )

    recommendations = await recommender.recommend_tasks(context, limit=2)

    assert len(recommendations) == 2, \
        "Should return exactly 2 recommendations when limit=2"


@pytest.mark.asyncio
async def test_handles_empty_candidate_list(recommender):
    """Test that recommender handles empty candidate list gracefully."""
    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=[]
    )

    recommendations = await recommender.recommend_tasks(context, limit=3)

    assert len(recommendations) == 0, \
        "Should return empty list when no candidates available"


# ============================================================================
# Cognitive Load Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_high_cognitive_load_filters_complex_tasks(recommender):
    """Test that high cognitive load (>0.8) filters out complex tasks."""
    complex_task = MockTask("complex", "Complex task", 0.8, "high", 60)
    simple_task = MockTask("simple", "Simple task", 0.2, "medium", 30)

    context = RecommendationContext(
        energy_level="medium",
        attention_level="scattered",
        cognitive_load=0.9,  # High load
        candidate_tasks=[complex_task, simple_task]
    )

    recommendations = await recommender.recommend_tasks(context, limit=2)

    # Should only recommend simple task due to high cognitive load
    assert all(rec.task.complexity < 0.3 for rec in recommendations), \
        "High cognitive load should filter out complex tasks"


# ============================================================================
# Rationale Generation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_rationale_includes_energy_match(recommender):
    """Test that rationale mentions energy level match."""
    task = MockTask("task", "Test task", 0.5, "medium", 60)

    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=[task]
    )

    recommendations = await recommender.recommend_tasks(context, limit=1)

    assert len(recommendations) == 1
    assert "medium energy" in recommendations[0].rationale.lower(), \
        "Rationale should mention energy level"


@pytest.mark.asyncio
async def test_recommendation_has_required_fields(recommender, sample_tasks):
    """Test that recommendations contain all required fields."""
    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=sample_tasks
    )

    recommendations = await recommender.recommend_tasks(context, limit=1)

    assert len(recommendations) == 1
    rec = recommendations[0]

    # Check required fields
    assert rec.task_id is not None
    assert rec.task is not None
    assert 0.0 <= rec.confidence <= 1.0
    assert 0.0 <= rec.completion_probability <= 1.0
    assert rec.recommendation_source == RecommendationSource.RULE_BASED
    assert len(rec.rationale) > 0
    assert isinstance(rec.ranking_factors, dict)
    assert rec.user_energy == "medium"
    assert rec.user_attention == "focused"


# ============================================================================
# Completion Probability Tests
# ============================================================================

@pytest.mark.asyncio
async def test_completion_probability_higher_for_matched_task(recommender):
    """Test that well-matched tasks have higher completion probability."""
    # Perfect match: high priority, unblocked, matches energy
    perfect_match = MockTask("perfect", "Perfect task", 0.5, "high", 30)

    # Poor match: low priority, blocked, wrong complexity
    poor_match = MockTask("poor", "Poor task", 0.1, "low", 120,
                         dependencies=["dep"])

    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=[perfect_match, poor_match]
    )

    recommendations = await recommender.recommend_tasks(context, limit=2)

    perfect_rec = next(r for r in recommendations if r.task.task_id == "perfect")
    poor_rec = next(r for r in recommendations if r.task.task_id == "poor")

    assert perfect_rec.completion_probability > poor_rec.completion_probability, \
        "Well-matched task should have higher completion probability"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
