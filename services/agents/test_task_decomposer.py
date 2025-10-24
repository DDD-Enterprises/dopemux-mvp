"""
Test Suite for TaskDecomposer - Week 9

Comprehensive tests covering:
1. Basic decomposition (complex task)
2. No decomposition (simple task)
3. Energy requirement mapping
4. CognitiveGuardian integration
5. ToolOrchestrator integration
6. TwoPlaneOrchestrator routing
7. ConPort logging
8. ADHD limits enforcement

Version: 1.0.0
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from task_decomposer import (
    TaskDecomposer,
    TaskInput,
    SubTask,
    DecompositionResult,
    TaskType
)


# ============================================================================
# Test 1: Basic Decomposition
# ============================================================================

@pytest.mark.asyncio
async def test_basic_decomposition():
    """Test decomposition of 120-minute, 0.8 complexity task."""
    decomposer = TaskDecomposer(workspace_id="/test")

    task = TaskInput(
        id="T-001",
        description="Implement JWT authentication",
        estimated_minutes=120,
        complexity=0.8
    )

    result = await decomposer.decompose_task(
        task,
        validate_readiness=False,
        assign_tools=False,
        log_to_conport=False
    )

    # Assertions
    assert len(result.subtasks) == 5  # 120/25 ≈ 5
    assert result.subtasks[0].complexity == 0.4  # 50% start
    assert result.subtasks[-1].complexity == 0.8  # Reaches parent
    assert all(st.estimated_minutes <= 30 for st in result.subtasks)  # ADHD-safe
    assert result.total_estimated_minutes == 120

    # Progressive complexity
    complexities = [st.complexity for st in result.subtasks]
    assert complexities == sorted(complexities)  # Ascending

    # Dependencies (sequential)
    assert result.subtasks[0].dependencies == []
    assert result.subtasks[1].dependencies == [0]
    assert result.subtasks[2].dependencies == [1]

    print("✅ Test 1: Basic decomposition PASSED")


# ============================================================================
# Test 2: No Decomposition Needed
# ============================================================================

@pytest.mark.asyncio
async def test_no_decomposition_simple_task():
    """Test that simple tasks aren't unnecessarily decomposed."""
    decomposer = TaskDecomposer(workspace_id="/test")

    task = TaskInput(
        id="T-002",
        description="Fix typo in README",
        estimated_minutes=10,
        complexity=0.1
    )

    result = await decomposer.decompose_task(
        task,
        validate_readiness=False,
        assign_tools=False,
        log_to_conport=False
    )

    # Assertions
    assert len(result.subtasks) == 1  # No decomposition
    assert result.subtasks[0].description == task.description
    assert result.subtasks[0].estimated_minutes == task.estimated_minutes
    assert result.subtasks[0].complexity == task.complexity
    assert "ADHD-optimal" in result.recommendations[0]

    print("✅ Test 2: No decomposition for simple tasks PASSED")


# ============================================================================
# Test 3: Energy Requirement Mapping
# ============================================================================

@pytest.mark.asyncio
async def test_energy_mapping():
    """Test energy requirements match complexity levels."""
    decomposer = TaskDecomposer(workspace_id="/test")

    task = TaskInput(
        id="T-003",
        description="Refactor database layer",
        estimated_minutes=100,
        complexity=0.9
    )

    result = await decomposer.decompose_task(
        task,
        validate_readiness=False,
        assign_tools=False,
        log_to_conport=False
    )

    # First subtask: low complexity → low/medium energy
    assert result.subtasks[0].complexity < 0.5
    assert result.subtasks[0].energy_required in ["low", "medium"]

    # Last subtask: high complexity → high energy
    assert result.subtasks[-1].complexity >= 0.7
    assert result.subtasks[-1].energy_required == "high"

    # Energy mapping validation
    for subtask in result.subtasks:
        if subtask.complexity < 0.4:
            assert subtask.energy_required == "low"
        elif subtask.complexity < 0.7:
            assert subtask.energy_required == "medium"
        else:
            assert subtask.energy_required == "high"

    print("✅ Test 3: Energy mapping PASSED")


# ============================================================================
# Test 4: CognitiveGuardian Integration
# ============================================================================

@pytest.mark.asyncio
async def test_cognitive_guardian_integration():
    """Test readiness validation integration."""
    # Mock CognitiveGuardian
    guardian_mock = Mock()
    guardian_mock.check_task_readiness = AsyncMock(return_value={
        "ready": True,
        "reason": "Energy match: high, attention: focused",
        "confidence": 0.85
    })

    decomposer = TaskDecomposer(
        workspace_id="/test",
        cognitive_guardian=guardian_mock
    )

    task = TaskInput(
        id="T-004",
        description="Build microservices API",
        estimated_minutes=150,
        complexity=0.85
    )

    result = await decomposer.decompose_task(
        task,
        validate_readiness=True,  # Enable validation
        assign_tools=False,
        log_to_conport=False
    )

    # Assertions
    assert result.readiness_validations is not None
    assert len(result.readiness_validations) == len(result.subtasks)
    assert all("ready" in v for v in result.readiness_validations)
    assert all("confidence" in v for v in result.readiness_validations)

    # Guardian should be called once per subtask
    assert guardian_mock.check_task_readiness.call_count == len(result.subtasks)

    print("✅ Test 4: CognitiveGuardian integration PASSED")


# ============================================================================
# Test 5: ToolOrchestrator Integration
# ============================================================================

@pytest.mark.asyncio
async def test_tool_orchestrator_integration():
    """Test tool/model assignment per subtask."""
    # Mock ToolOrchestrator
    tool_mock = Mock()

    def mock_select_tools(task_type, complexity):
        # Simple tasks get fast models, complex get power models
        if complexity < 0.4:
            return Mock(
                model="grok-4-fast",
                estimated_cost=0.0,
                estimated_latency="500ms"
            )
        elif complexity < 0.7:
            return Mock(
                model="gpt-5-mini",
                estimated_cost=0.50,
                estimated_latency="1s"
            )
        else:
            return Mock(
                model="gpt-5-codex",
                estimated_cost=2.50,
                estimated_latency="2s"
            )

    tool_mock.select_tools_for_task = mock_select_tools

    decomposer = TaskDecomposer(
        workspace_id="/test",
        tool_orchestrator=tool_mock
    )

    task = TaskInput(
        id="T-005",
        description="Code review authentication module",
        estimated_minutes=100,
        complexity=0.9  # High complexity to test power model assignment
    )

    result = await decomposer.decompose_task(
        task,
        validate_readiness=False,
        assign_tools=True,  # Enable tool assignment
        log_to_conport=False
    )

    # Assertions
    assert result.tool_assignments is not None
    assert len(result.tool_assignments) == len(result.subtasks)

    # First subtask (simple) should get fast model
    first_assignment = result.tool_assignments[0]
    assert first_assignment["tools"].model in ["grok-4-fast", "gpt-5-mini"]

    # Last subtask (complex) should get power model
    last_assignment = result.tool_assignments[-1]
    assert last_assignment["tools"].model in ["gpt-5-codex", "gpt-5"]

    # Total cost should be calculated
    assert result.total_estimated_cost > 0

    print("✅ Test 5: ToolOrchestrator integration PASSED")


# ============================================================================
# Test 6: TwoPlaneOrchestrator Routing
# ============================================================================

@pytest.mark.asyncio
async def test_two_plane_routing():
    """Test subtask routing to correct planes."""
    decomposer = TaskDecomposer(workspace_id="/test")

    task = TaskInput(
        id="T-006",
        description="Design and implement user service",
        estimated_minutes=120,
        complexity=0.75
    )

    result = await decomposer.decompose_task(
        task,
        validate_readiness=False,
        assign_tools=False,
        log_to_conport=False
    )

    # Assertions
    assert "pm_plane" in result.plane_routing
    assert "cognitive_plane" in result.plane_routing

    # First subtask (design) should go to PM plane
    pm_tasks = result.plane_routing["pm_plane"]
    assert len(pm_tasks) > 0
    assert any(st.task_type == TaskType.DESIGN for st in pm_tasks)

    # Implementation subtasks should go to Cognitive plane
    cognitive_tasks = result.plane_routing["cognitive_plane"]
    assert len(cognitive_tasks) > 0
    assert any(st.task_type == TaskType.IMPLEMENTATION for st in cognitive_tasks)

    print("✅ Test 6: TwoPlaneOrchestrator routing PASSED")


# ============================================================================
# Test 7: ConPort Logging
# ============================================================================

@pytest.mark.asyncio
async def test_conport_logging():
    """Test decomposition logged to ConPort knowledge graph."""
    # Mock ConPort client
    conport_mock = Mock()
    conport_mock.log_decision = AsyncMock(return_value="decision-123")
    conport_mock.log_progress = AsyncMock(return_value="progress-456")
    conport_mock.link_conport_items = AsyncMock()

    decomposer = TaskDecomposer(
        workspace_id="/test",
        conport_client=conport_mock
    )

    task = TaskInput(
        id="T-007",
        description="Build notification system",
        estimated_minutes=90,
        complexity=0.7
    )

    result = await decomposer.decompose_task(
        task,
        validate_readiness=False,
        assign_tools=False,
        log_to_conport=True  # Enable logging
    )

    # Assertions
    assert result.decomposition_decision_id == "decision-123"

    # Decision should be logged once
    assert conport_mock.log_decision.call_count == 1

    # Progress entries for each subtask
    assert conport_mock.log_progress.call_count == len(result.subtasks)

    # Knowledge graph links for each subtask
    assert conport_mock.link_conport_items.call_count == len(result.subtasks)

    # Verify decision content
    decision_call = conport_mock.log_decision.call_args
    assert "ADHD-optimized subtasks" in decision_call.kwargs["summary"]
    assert "progressive complexity loading" in decision_call.kwargs["rationale"].lower()

    print("✅ Test 7: ConPort logging PASSED")


# ============================================================================
# Test 8: ADHD Limits Enforcement
# ============================================================================

@pytest.mark.asyncio
async def test_adhd_limits():
    """Test ADHD constraints are enforced."""
    decomposer = TaskDecomposer(workspace_id="/test")

    task = TaskInput(
        id="T-008",
        description="Massive refactoring project",
        estimated_minutes=500,  # Very long
        complexity=0.95
    )

    result = await decomposer.decompose_task(
        task,
        validate_readiness=False,
        assign_tools=False,
        log_to_conport=False
    )

    # Assertions
    # Hard max: 5 subtasks (decision fatigue prevention)
    assert len(result.subtasks) <= 5
    assert len(result.subtasks) >= 3  # Hard min

    # All subtasks should have reasonable estimates
    assert all(st.estimated_minutes > 0 for st in result.subtasks)

    # Progressive complexity maintained
    complexities = [st.complexity for st in result.subtasks]
    assert complexities == sorted(complexities)  # Ascending order

    # Complexity should start at 50% and reach parent
    assert result.subtasks[0].complexity >= task.complexity * 0.45  # ~50%
    assert result.subtasks[-1].complexity >= task.complexity * 0.9  # Approaches parent

    # Recommendations should exist
    assert len(result.recommendations) > 0

    print("✅ Test 8: ADHD limits enforcement PASSED")


# ============================================================================
# Bonus Test: Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_edge_cases():
    """Test edge cases and boundary conditions."""
    decomposer = TaskDecomposer(workspace_id="/test")

    # Edge case 1: Exactly 25 minutes, low complexity (no decomposition)
    task1 = TaskInput(
        id="T-EDGE-1",
        description="Quick task",
        estimated_minutes=25,
        complexity=0.2
    )
    result1 = await decomposer.decompose_task(
        task1, validate_readiness=False, assign_tools=False, log_to_conport=False
    )
    assert len(result1.subtasks) == 1  # No decomposition

    # Edge case 2: 26 minutes (just over threshold)
    task2 = TaskInput(
        id="T-EDGE-2",
        description="Slightly longer task",
        estimated_minutes=26,
        complexity=0.2
    )
    result2 = await decomposer.decompose_task(
        task2, validate_readiness=False, assign_tools=False, log_to_conport=False
    )
    assert len(result2.subtasks) >= 3  # Decomposition triggered

    # Edge case 3: Low minutes, high complexity
    task3 = TaskInput(
        id="T-EDGE-3",
        description="Complex but quick",
        estimated_minutes=20,
        complexity=0.9
    )
    result3 = await decomposer.decompose_task(
        task3, validate_readiness=False, assign_tools=False, log_to_conport=False
    )
    assert len(result3.subtasks) >= 3  # Complexity triggers decomposition

    # Edge case 4: Maximum complexity (1.0)
    task4 = TaskInput(
        id="T-EDGE-4",
        description="Maximum complexity task",
        estimated_minutes=100,
        complexity=1.0
    )
    result4 = await decomposer.decompose_task(
        task4, validate_readiness=False, assign_tools=False, log_to_conport=False
    )
    assert result4.subtasks[-1].complexity <= 1.0  # Capped at 1.0

    print("✅ Bonus Test: Edge cases PASSED")


# ============================================================================
# Test Runner
# ============================================================================

async def run_all_tests():
    """Run all tests in sequence."""
    print("\n" + "="*70)
    print("TaskDecomposer Test Suite - Week 9")
    print("="*70 + "\n")

    tests = [
        ("Test 1: Basic Decomposition", test_basic_decomposition),
        ("Test 2: No Decomposition Needed", test_no_decomposition_simple_task),
        ("Test 3: Energy Mapping", test_energy_mapping),
        ("Test 4: CognitiveGuardian Integration", test_cognitive_guardian_integration),
        ("Test 5: ToolOrchestrator Integration", test_tool_orchestrator_integration),
        ("Test 6: TwoPlaneOrchestrator Routing", test_two_plane_routing),
        ("Test 7: ConPort Logging", test_conport_logging),
        ("Test 8: ADHD Limits Enforcement", test_adhd_limits),
        ("Bonus: Edge Cases", test_edge_cases),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"Running {test_name}...")
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            failed += 1
        print()

    # Summary
    print("="*70)
    print(f"Test Results: {passed}/{len(tests)} passed")
    if failed == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {failed} tests failed")
    print("="*70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
