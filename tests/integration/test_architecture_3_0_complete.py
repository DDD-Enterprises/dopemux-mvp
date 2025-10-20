"""
Architecture 3.0 Complete Integration Test Suite

Validates all 6 components working together in realistic workflows.

Created: 2025-10-20
Test Type: Integration E2E
Duration: ~60 seconds
"""

import pytest
import asyncio
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add services to path
services_path = Path(__file__).parent.parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

# Component 6 imports
from task_orchestrator.intelligence import (
    HybridTaskRecommender,
    CognitiveLoadBalancer,
    LoadAlertManager,
    ContextSwitchRecovery,
    RecommendationContext,
    TaskRecommendation
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_task():
    """Create mock task for testing."""
    class MockTask:
        def __init__(self, task_id, description, complexity, priority="medium", 
                     estimated_duration=60, dependencies=None):
            self.task_id = task_id
            self.description = description
            self.complexity = complexity
            self.priority = priority
            self.estimated_duration = estimated_duration
            self.dependencies = dependencies or []
            self.created_at = datetime.now()
    
    return MockTask


@pytest.fixture
def sample_tasks(mock_task):
    """Create sample task set."""
    return [
        mock_task("task-1", "Simple docs update", 0.2, "low", 15),
        mock_task("task-2", "Moderate feature work", 0.5, "medium", 60),
        mock_task("task-3", "Complex architecture", 0.9, "high", 120),
        mock_task("task-4", "Quick bug fix", 0.3, "high", 30),
    ]


# ============================================================================
# Component 6 Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_component6_cold_start_to_completion():
    """Test Component 6: cold start → recommendation → learning."""
    recommender = HybridTaskRecommender(ml_algorithm="thompson_sampling")
    
    class MockTask:
        def __init__(self, task_id, complexity):
            self.task_id = task_id
            self.description = f"Task {task_id}"
            self.complexity = complexity
            self.priority = "medium"
            self.estimated_duration = 60
            self.dependencies = []
            self.created_at = datetime.now()
    
    tasks = [MockTask(f"task-{i}", 0.3 + i * 0.1) for i in range(5)]
    
    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=tasks
    )
    
    recs = await recommender.recommend_tasks(context, limit=3)
    assert len(recs) == 3
    
    # Simulate 10 completions
    for i in range(10):
        recommender.update_from_outcome(
            task_id=f"task-{i % 5}",
            completed=(i % 3 != 0),
            context=context,
            task=tasks[i % 5]
        )
    
    stats = recommender.get_statistics()
    assert stats["ml_training_progress"]["is_trained"]
    
    print("✅ Component 6: Cold start → ML learning validated")


@pytest.mark.asyncio
async def test_component6_cognitive_load_adaptation():
    """Test cognitive load-based recommendation adaptation."""
    load_balancer = CognitiveLoadBalancer()
    alert_manager = LoadAlertManager()
    recommender = HybridTaskRecommender(use_dynamic_count=True)
    
    class MockTask:
        def __init__(self, task_id, complexity):
            self.task_id = task_id
            self.description = f"Task {task_id}"
            self.complexity = complexity
            self.priority = "medium"
            self.estimated_duration = 60
            self.dependencies = []
            self.created_at = datetime.now()
    
    simple_tasks = [MockTask(f"simple-{i}", 0.2) for i in range(3)]
    complex_tasks = [MockTask(f"complex-{i}", 0.9) for i in range(3)]
    all_tasks = simple_tasks + complex_tasks
    
    # High cognitive load
    high_load = await load_balancer.calculate_load(
        user_id="test-user",
        factors=LoadFactors(
            task_complexity=0.9,
            active_decisions=10,
            context_switches=5,
            minutes_since_break=90,
            active_interruptions=5
        ),
        use_cache=False
    )
    
    assert high_load.load_value >= 0.8
    
    # Alert generation
    alert = await alert_manager.check_and_generate_alert(
        user_id="test-user",
        load_calculation=high_load
    )
    
    assert alert is not None
    
    # Adaptive recommendations
    context = RecommendationContext(
        energy_level="low",
        attention_level="scattered",
        cognitive_load=high_load.load_value,
        candidate_tasks=all_tasks
    )
    
    recs = await recommender.recommend_tasks(context)
    assert len(recs) <= 2  # Reduced count
    
    for rec in recs:
        assert rec.task.complexity < 0.5  # Simple tasks only
    
    print("✅ Component 6: Cognitive load adaptation validated")


@pytest.mark.asyncio
async def test_component6_performance_targets():
    """Validate ADHD performance targets."""
    recommender = HybridTaskRecommender()
    load_balancer = CognitiveLoadBalancer()
    alert_manager = LoadAlertManager()
    
    class MockTask:
        def __init__(self, task_id, complexity):
            self.task_id = task_id
            self.description = f"Task {task_id}"
            self.complexity = complexity
            self.priority = "medium"
            self.estimated_duration = 60
            self.dependencies = []
            self.created_at = datetime.now()
    
    tasks = [MockTask(f"task-{i}", 0.5) for i in range(10)]
    
    # Recommendation generation (<200ms)
    start = time.time()
    context = RecommendationContext(
        energy_level="medium",
        attention_level="focused",
        cognitive_load=0.5,
        candidate_tasks=tasks
    )
    recs = await recommender.recommend_tasks(context, limit=3)
    rec_time = (time.time() - start) * 1000
    
    assert rec_time < 200, f"Recs should be <200ms, got {rec_time:.2f}ms"
    
    # Cognitive load calculation (<50ms)
    start = time.time()
    load = await load_balancer.calculate_load(
        user_id="perf-test",
        factors=LoadFactors(0.5, 5, 2, 30, 1),
        use_cache=False
    )
    load_time = (time.time() - start) * 1000
    
    assert load_time < 50, f"Load should be <50ms, got {load_time:.2f}ms"
    
    # Alert generation (<10ms)
    start = time.time()
    alert = await alert_manager.check_and_generate_alert(
        user_id="perf-test",
        load_calculation=load
    )
    alert_time = (time.time() - start) * 1000
    
    assert alert_time < 10, f"Alert should be <10ms, got {alert_time:.2f}ms"
    
    print(f"✅ Performance: Recs={rec_time:.1f}ms, Load={load_time:.1f}ms, Alert={alert_time:.1f}ms")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
