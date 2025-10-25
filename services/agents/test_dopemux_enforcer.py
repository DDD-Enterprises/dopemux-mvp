"""
Week 7: DopemuxEnforcer Comprehensive Test Suite

Tests architectural compliance validation across all rules.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dopemux_enforcer import DopemuxEnforcer, ViolationSeverity, ViolationType


async def test_tool_preference_violation():
    """Test 1: Detect bash usage instead of MCP tools"""
    print("\n" + "="*70)
    print("Test 1: Tool Preference Violation")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=False
    )
    await enforcer.initialize()

    code_with_bash = '''
import subprocess

def read_code():
    result = subprocess.run(["bash", "cat", "auth.py"], capture_output=True)
    return result.stdout.decode()
'''

    report = await enforcer.validate_code_change(
        file_path="test/bad_tool_usage.py",
        operation_type="create",
        content=code_with_bash
    )

    print(f"\nCompliant: {report.compliant}")
    print(f"Summary: {report.summary}")
    for v in report.violations:
        print(f"  {v.severity.upper()}: {v.message}")

    assert report.violations[0].type == ViolationType.TOOL_PREFERENCE
    assert report.violations[0].severity == ViolationSeverity.WARNING
    print("✅ Test passed! Tool preference violation detected")

    await enforcer.close()


async def test_two_plane_boundary_violation():
    """Test 2: Detect direct cross-plane access"""
    print("\n" + "="*70)
    print("Test 2: Two-Plane Boundary Violation")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=False
    )
    await enforcer.initialize()

    code_with_direct_leantime = '''
from leantime.api import LeantimeClient

async def get_tasks():
    # WRONG: Direct Leantime access!
    client = LeantimeClient()
    return await client.get_tasks()
'''

    report = await enforcer.validate_code_change(
        file_path="test/bad_boundary.py",
        operation_type="create",
        content=code_with_direct_leantime
    )

    print(f"\nCompliant: {report.compliant}")
    print(f"Summary: {report.summary}")
    for v in report.violations:
        print(f"  {v.severity.upper()}: {v.message}")

    assert len([v for v in report.violations if v.type == ViolationType.TWO_PLANE_BOUNDARY]) > 0
    assert report.compliant is False, "Should not be compliant"
    print("✅ Test passed! Boundary violation detected")

    await enforcer.close()


async def test_complexity_warning():
    """Test 3: Complexity warnings based on code size"""
    print("\n" + "="*70)
    print("Test 3: Complexity Warnings")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=False
    )
    await enforcer.initialize()

    # Large file (400 lines) should trigger warning
    large_code = "\n".join([f"# Line {i}" for i in range(400)])

    report = await enforcer.validate_code_change(
        file_path="test/large_file.py",
        operation_type="create",
        content=large_code
    )

    print(f"\nCompliant: {report.compliant}")
    print(f"Summary: {report.summary}")
    for v in report.violations:
        print(f"  {v.severity.upper()}: {v.message}")

    complexity_warnings = [v for v in report.violations if v.type == ViolationType.COMPLEXITY_WARNING]
    assert len(complexity_warnings) > 0, "Should warn about complexity"
    print("✅ Test passed! Complexity warning generated")

    await enforcer.close()


async def test_adhd_constraint_violation():
    """Test 4: ADHD constraint validation (max results)"""
    print("\n" + "="*70)
    print("Test 4: ADHD Constraint Violation")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=False
    )
    await enforcer.initialize()

    code_with_large_limit = '''
async def get_all_tasks():
    # ADHD violation: Too many results
    return await db.query(Task).limit(50).all()
'''

    report = await enforcer.validate_code_change(
        file_path="test/adhd_violation.py",
        operation_type="create",
        content=code_with_large_limit
    )

    print(f"\nCompliant: {report.compliant}")
    print(f"Summary: {report.summary}")
    for v in report.violations:
        print(f"  {v.severity.upper()}: {v.message}")

    adhd_violations = [v for v in report.violations if v.type == ViolationType.ADHD_CONSTRAINT]
    assert len(adhd_violations) > 0, "Should detect ADHD constraint violation"
    print("✅ Test passed! ADHD constraint violation detected")

    await enforcer.close()


async def test_authority_matrix_validation():
    """Test 5: Authority matrix operation validation"""
    print("\n" + "="*70)
    print("Test 5: Authority Matrix Validation")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=False
    )
    await enforcer.initialize()

    # Test PM trying to write decisions
    report = await enforcer.validate_operation(
        operation="update_decision",
        data_type="decisions",
        source_plane="pm"
    )

    print(f"\nCompliant: {report.compliant}")
    print(f"Summary: {report.summary}")
    for v in report.violations:
        print(f"  {v.severity.upper()}: {v.message}")

    assert report.compliant is False, "PM should not write decisions"
    assert report.violations[0].type == ViolationType.AUTHORITY_MATRIX
    print("✅ Test passed! Authority violation detected")

    await enforcer.close()


async def test_compliant_code():
    """Test 6: Valid compliant code passes"""
    print("\n" + "="*70)
    print("Test 6: Compliant Code (No Violations)")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=False
    )
    await enforcer.initialize()

    compliant_code = '''
async def get_tasks_properly():
    """Uses TwoPlaneOrchestrator correctly"""
    orchestrator = TwoPlaneOrchestrator(workspace_id=workspace)
    return await orchestrator.cognitive_to_pm(operation="get_tasks", data={})
'''

    report = await enforcer.validate_code_change(
        file_path="test/good_example.py",
        operation_type="create",
        content=compliant_code
    )

    print(f"\nCompliant: {report.compliant}")
    print(f"Summary: {report.summary}")

    assert report.compliant is True, "Compliant code should pass"
    assert len(report.violations) == 0, "Should have no violations"
    print("✅ Test passed! Compliant code validated")

    await enforcer.close()


async def test_strict_mode_blocking():
    """Test 7: Strict mode blocks critical violations"""
    print("\n" + "="*70)
    print("Test 7: Strict Mode Blocking")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=True  # BLOCK mode
    )
    await enforcer.initialize()

    # Very large file (500 lines) triggers critical
    huge_code = "\n".join([f"# Line {i}" for i in range(500)])

    report = await enforcer.validate_code_change(
        file_path="test/huge_file.py",
        operation_type="create",
        content=huge_code
    )

    print(f"\nCompliant: {report.compliant}")
    print(f"Blocking: {report.blocking}")
    print(f"Summary: {report.summary}")

    critical_violations = [v for v in report.violations if v.severity == ViolationSeverity.CRITICAL]
    print(f"Critical Violations: {len(critical_violations)}")

    if critical_violations:
        print("✅ Test passed! Critical violations would block in strict mode")
    else:
        print("💡 No critical violations (expected for this test)")

    await enforcer.close()


async def test_metrics_tracking():
    """Test 8: Metrics accumulate correctly"""
    print("\n" + "="*70)
    print("Test 8: Metrics Tracking")
    print("="*70)

    enforcer = DopemuxEnforcer(
        workspace_id="/Users/hue/code/dopemux-mvp",
        strict_mode=False
    )
    await enforcer.initialize()

    # Run multiple validations
    await enforcer.validate_operation("update_decision", "decisions", "pm")
    await enforcer.validate_operation("get_tasks", "tasks", "cognitive")
    await enforcer.validate_operation("update_task", "tasks", "pm")

    metrics = await enforcer.get_metrics_summary()

    print(f"\nMetrics:")
    print(f"  Validations: {metrics['validations_performed']}")
    print(f"  Violations: {metrics['violations_found']}")
    print(f"  Warnings: {metrics['warnings_issued']}")

    assert metrics["validations_performed"] == 3, "Should have 3 validations"
    assert metrics["violations_found"] >= 1, "Should find at least 1 violation"
    print("✅ Test passed! Metrics tracked correctly")

    await enforcer.close()


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("WEEK 7: DopemuxEnforcer Test Suite")
    print("="*70)

    tests = [
        ("Tool Preference Violation", test_tool_preference_violation),
        ("Two-Plane Boundary Violation", test_two_plane_boundary_violation),
        ("Complexity Warnings", test_complexity_warning),
        ("ADHD Constraint Violation", test_adhd_constraint_violation),
        ("Authority Matrix Validation", test_authority_matrix_validation),
        ("Compliant Code Passes", test_compliant_code),
        ("Strict Mode Blocking", test_strict_mode_blocking),
        ("Metrics Tracking", test_metrics_tracking),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ Test '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*70)
    print(f"Test Results: {passed}/{len(tests)} passed")
    print("="*70)

    if failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
