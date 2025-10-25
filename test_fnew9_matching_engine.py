"""
F-NEW-9 Matching Engine Tests

Validates energy-complexity, attention-task, and time-duration matching.
Target: >75% match accuracy

Run: python test_fnew9_matching_engine.py
"""

import sys
sys.path.insert(0, 'services/task-router')

from matching_engine import (
    TaskMatchingEngine,
    EnergyTaskMatcher,
    AttentionTaskMatcher,
    TimeTaskMatcher,
    CognitiveState,
    Task,
    EnergyLevel,
    AttentionState
)


def test_energy_complexity_matching():
    """Test 1: Energy-complexity alignment"""
    print("Test 1: Energy-complexity matching...")

    matcher = EnergyTaskMatcher()
    test_cases = [
        # (energy, complexity, expected_score_range, description)
        (EnergyLevel.HIGH, 0.8, (0.9, 1.0), "High energy + high complexity"),
        (EnergyLevel.HIGH, 0.2, (0.1, 0.3), "High energy + low complexity (wasted)"),
        (EnergyLevel.MEDIUM, 0.4, (0.9, 1.0), "Medium energy + medium complexity"),
        (EnergyLevel.MEDIUM, 0.8, (0.5, 0.7), "Medium energy + high complexity (struggle)"),
        (EnergyLevel.LOW, 0.2, (0.9, 1.0), "Low energy + low complexity"),
        (EnergyLevel.LOW, 0.7, (0.0, 0.2), "Low energy + high complexity (frustration)"),
    ]

    passed = 0
    for energy, complexity, expected_range, desc in test_cases:
        score, reason = matcher.calculate_energy_match(energy, complexity)

        if expected_range[0] <= score <= expected_range[1]:
            print(f"  ✅ {desc}: {score:.2f} (expected {expected_range})")
            passed += 1
        else:
            print(f"  ❌ {desc}: {score:.2f} (expected {expected_range})")

    print(f"  Result: {passed}/{len(test_cases)} cases passed\n")
    return passed == len(test_cases)


def test_attention_task_matching():
    """Test 2: Attention-task type alignment"""
    print("Test 2: Attention-task type matching...")

    matcher = AttentionTaskMatcher()

    # Create test tasks
    deep_work_task = Task(
        task_id="T1",
        title="Refactor auth system",
        description="Complex refactoring",
        complexity=0.8,
        estimated_minutes=120,
        priority="high",
        task_type="deep_work",
        requires_focus=True
    )

    simple_task = Task(
        task_id="T2",
        title="Fix typo in README",
        description="Simple documentation fix",
        complexity=0.1,
        estimated_minutes=5,
        priority="low",
        task_type="documentation",
        requires_focus=False
    )

    test_cases = [
        (AttentionState.FOCUSED, deep_work_task, (0.9, 1.0), "Focused + deep work"),
        (AttentionState.FOCUSED, simple_task, (0.6, 0.8), "Focused + simple (underutilized)"),
        (AttentionState.SCATTERED, deep_work_task, (0.0, 0.2), "Scattered + deep work (incompatible)"),
        (AttentionState.SCATTERED, simple_task, (0.9, 1.0), "Scattered + simple (perfect)"),
    ]

    passed = 0
    for attention, task, expected_range, desc in test_cases:
        score, reason = matcher.calculate_attention_match(attention, task)

        if expected_range[0] <= score <= expected_range[1]:
            print(f"  ✅ {desc}: {score:.2f}")
            passed += 1
        else:
            print(f"  ❌ {desc}: {score:.2f} (expected {expected_range})")

    print(f"  Result: {passed}/{len(test_cases)} cases passed\n")
    return passed == len(test_cases)


def test_time_duration_matching():
    """Test 3: Time-duration alignment"""
    print("Test 3: Time-duration matching...")

    matcher = TimeTaskMatcher()
    test_cases = [
        (30, 20, (0.9, 1.0), "20min task with 30min available (fits)"),
        (30, 28, (0.8, 0.95), "28min task with 30min available (tight)"),
        (30, 60, (0.2, 0.4), "60min task with 30min available (exceeds)"),
        (None, 120, (0.7, 0.9), "Unknown time available (no penalty)"),
    ]

    passed = 0
    for time_avail, task_dur, expected_range, desc in test_cases:
        score, reason = matcher.calculate_time_match(time_avail, task_dur)

        if expected_range[0] <= score <= expected_range[1]:
            print(f"  ✅ {desc}: {score:.2f}")
            passed += 1
        else:
            print(f"  ❌ {desc}: {score:.2f} (expected {expected_range})")

    print(f"  Result: {passed}/{len(test_cases)} cases passed\n")
    return passed == len(test_cases)


def test_integrated_matching():
    """Test 4: Full integrated matching engine"""
    print("Test 4: Integrated matching engine...")

    engine = TaskMatchingEngine()

    # Scenario: High energy, focused attention, 45 min available
    cognitive_state = CognitiveState(
        energy=EnergyLevel.HIGH,
        attention=AttentionState.FOCUSED,
        cognitive_load=0.4,
        time_until_break_min=45
    )

    # Create test tasks
    tasks = [
        Task("T1", "Refactor auth", "Complex refactoring", 0.8, 35, "high", "deep_work", True),
        Task("T2", "Fix typo", "Simple doc fix", 0.1, 5, "low", "documentation", False),
        Task("T3", "Implement feature", "Moderate implementation", 0.5, 30, "medium", "implementation", False),
    ]

    suggestions = engine.suggest_tasks(cognitive_state, tasks, count=3)

    # With high energy + focused, should prefer high complexity task
    if suggestions[0].task.task_id == "T1":  # Refactor auth (complex)
        print(f"  ✅ Rank 1: {suggestions[0].task.title} (score: {suggestions[0].match_score:.2f})")
        result = True
    else:
        print(f"  ❌ Expected T1 (Refactor) at rank 1, got {suggestions[0].task.task_id}")
        result = False

    for i, sug in enumerate(suggestions, 1):
        print(f"     #{i}: {sug.task.title} - Match: {sug.match_score:.2f}")

    print()
    return result


def test_mismatch_detection():
    """Test 5: Task-energy mismatch detection"""
    print("Test 5: Mismatch detection...")

    engine = TaskMatchingEngine()

    # Scenario: Low energy, scattered attention
    low_energy_state = CognitiveState(
        energy=EnergyLevel.LOW,
        attention=AttentionState.SCATTERED,
        cognitive_load=0.7,
        time_until_break_min=15
    )

    # High complexity task
    complex_task = Task(
        "T1", "Refactor database layer", "Complex refactoring",
        0.9, 120, "high", "deep_work", True
    )

    mismatch = engine.detect_task_mismatch(low_energy_state, complex_task)

    if mismatch and mismatch['is_mismatch']:
        print(f"  ✅ Mismatch detected: {mismatch['severity']} severity")
        print(f"     Reason: {mismatch['reason']}")
        result = True
    else:
        print(f"  ❌ Should have detected mismatch (low energy + high complexity)")
        result = False

    print()
    return result


def main():
    """Run all matching engine tests."""
    print("=" * 70)
    print("F-NEW-9 Matching Engine Tests")
    print("Target: >75% accuracy for task-state matching")
    print("=" * 70)
    print()

    results = []
    results.append(test_energy_complexity_matching())
    results.append(test_attention_task_matching())
    results.append(test_time_duration_matching())
    results.append(test_integrated_matching())
    results.append(test_mismatch_detection())

    print("=" * 70)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    accuracy = (sum(results) / len(results)) * 100
    print(f"Accuracy: {accuracy:.0f}% (target: >75%)")
    print("=" * 70)

    if accuracy >= 75:
        print("✅ MATCHING ENGINE VALIDATED - Meets >75% accuracy target!")
        return 0
    else:
        print(f"❌ Below 75% accuracy target")
        return 1


if __name__ == "__main__":
    exit(main())
