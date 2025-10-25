"""
Week 10: WorkflowCoordinator Comprehensive Test Suite
Tests multi-step workflow orchestration
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from workflow_coordinator import WorkflowCoordinator, WorkflowType, StepType


async def test_load_workflow_templates():
    """Test 1: Workflow templates loaded"""
    print("\n" + "="*70)
    print("Test 1: Load Workflow Templates")
    print("="*70)

    coordinator = WorkflowCoordinator(workspace_id="/Users/hue/code/dopemux-mvp")
    await coordinator.initialize()

    print(f"\nTemplates Loaded: {len(coordinator.templates)}")

    for wf_type, template in coordinator.templates.items():
        print(f"\n  {template.name}:")
        print(f"    Type: {wf_type.value}")
        print(f"    Steps: {len(template.steps)}")
        print(f"    Estimated: {template.total_estimated_minutes} min")

    assert len(coordinator.templates) >= 3, "Should have at least 3 templates"
    assert WorkflowType.FEATURE_IMPLEMENTATION in coordinator.templates
    assert WorkflowType.BUG_INVESTIGATION in coordinator.templates
    assert WorkflowType.ARCHITECTURE_DECISION in coordinator.templates
    print("\n✅ Test passed! Templates loaded correctly")

    await coordinator.close()


async def test_start_workflow():
    """Test 2: Start workflow execution"""
    print("\n" + "="*70)
    print("Test 2: Start Workflow Execution")
    print("="*70)

    coordinator = WorkflowCoordinator(workspace_id="/Users/hue/code/dopemux-mvp")
    await coordinator.initialize()

    execution = await coordinator.start_workflow(
        workflow_type=WorkflowType.FEATURE_IMPLEMENTATION,
        description="Add user authentication"
    )

    print(f"\nWorkflow ID: {execution.workflow_id}")
    print(f"Workflow Type: {execution.workflow_type.value}")
    print(f"Started At: {execution.started_at}")
    print(f"Current Step: {execution.current_step}")

    assert execution.workflow_id is not None, "Should have workflow ID"
    assert execution.current_step == 0, "Should start at step 0"
    assert len(execution.completed_steps) == 0, "No steps completed yet"
    print("\n✅ Test passed! Workflow started successfully")

    await coordinator.close()


async def test_execute_workflow_step():
    """Test 3: Execute workflow step"""
    print("\n" + "="*70)
    print("Test 3: Execute Workflow Step")
    print("="*70)

    coordinator = WorkflowCoordinator(workspace_id="/Users/hue/code/dopemux-mvp")
    await coordinator.initialize()

    # Start workflow
    execution = await coordinator.start_workflow(
        workflow_type=WorkflowType.BUG_INVESTIGATION,
        description="Fix login bug"
    )

    # Get first step
    template = coordinator.get_workflow_template(WorkflowType.BUG_INVESTIGATION)
    first_step = template.steps[0]

    print(f"\nExecuting Step: {first_step.name}")

    # Execute step
    result = await coordinator.execute_step(
        workflow_id=execution.workflow_id,
        step=first_step,
        result_data={"status": "completed"}
    )

    print(f"\nResult:")
    print(f"  Step: {result['step_name']}")
    print(f"  Completed: {result['completed']}")

    assert result["completed"] is True, "Step should be marked completed"
    assert execution.current_step == 1, "Current step should increment"
    assert len(execution.completed_steps) == 1, "Should have 1 completed step"
    print("\n✅ Test passed! Step executed successfully")

    await coordinator.close()


async def test_workflow_status_tracking():
    """Test 4: Workflow status tracking"""
    print("\n" + "="*70)
    print("Test 4: Workflow Status Tracking")
    print("="*70)

    coordinator = WorkflowCoordinator(workspace_id="/Users/hue/code/dopemux-mvp")
    await coordinator.initialize()

    # Start workflow
    execution = await coordinator.start_workflow(
        workflow_type=WorkflowType.ARCHITECTURE_DECISION,
        description="Choose database"
    )

    template = coordinator.get_workflow_template(WorkflowType.ARCHITECTURE_DECISION)

    # Execute 2 steps
    for step in template.steps[:2]:
        await coordinator.execute_step(execution.workflow_id, step)

    # Check status
    status = await coordinator.get_workflow_status(execution.workflow_id)

    print(f"\nWorkflow Status:")
    print(f"  Progress: {status['completed_steps']}/{status['total_steps']}")
    print(f"  Progress %: {status['progress_pct']}%")
    print(f"  Checkpoints: {status['checkpoints_created']}")

    assert status["completed_steps"] == 2, "Should have 2 completed steps"
    assert status["progress_pct"] > 0, "Should have progress percentage"
    print("\n✅ Test passed! Workflow status tracked correctly")

    await coordinator.close()


async def test_workflow_completion():
    """Test 5: Complete workflow"""
    print("\n" + "="*70)
    print("Test 5: Complete Workflow")
    print("="*70)

    coordinator = WorkflowCoordinator(workspace_id="/Users/hue/code/dopemux-mvp")
    await coordinator.initialize()

    # Start and complete workflow
    execution = await coordinator.start_workflow(
        workflow_type=WorkflowType.BUG_INVESTIGATION,
        description="Fix issue"
    )

    template = coordinator.get_workflow_template(WorkflowType.BUG_INVESTIGATION)

    # Execute all steps
    for step in template.steps:
        await coordinator.execute_step(execution.workflow_id, step)

    # Complete workflow
    summary = await coordinator.complete_workflow(execution.workflow_id)

    print(f"\nWorkflow Summary:")
    print(f"  Completed Steps: {summary['completed_steps']}/{summary['total_steps']}")
    print(f"  Progress: {summary['progress_pct']}%")
    print(f"  Duration: {summary['duration_minutes']:.1f} min")

    assert summary["progress_pct"] == 100.0, "Should be 100% complete"
    assert execution.workflow_id not in coordinator.active_workflows, "Should be removed from active"
    print("\n✅ Test passed! Workflow completed successfully")

    await coordinator.close()


async def test_multiple_workflows():
    """Test 6: Multiple active workflows"""
    print("\n" + "="*70)
    print("Test 6: Multiple Active Workflows")
    print("="*70)

    coordinator = WorkflowCoordinator(workspace_id="/Users/hue/code/dopemux-mvp")
    await coordinator.initialize()

    # Start first workflow
    wf1 = await coordinator.start_workflow(
        WorkflowType.FEATURE_IMPLEMENTATION,
        "Feature A"
    )

    print(f"\nAfter starting workflow 1:")
    print(f"  Active Workflows: {len(coordinator.active_workflows)}")
    print(f"  Workflow IDs: {list(coordinator.active_workflows.keys())}")

    assert len(coordinator.active_workflows) == 1, "Should have 1 active after first start"

    # Start second workflow
    wf2 = await coordinator.start_workflow(
        WorkflowType.BUG_INVESTIGATION,
        "Bug B"
    )

    print(f"\nAfter starting workflow 2:")
    print(f"  Active Workflows: {len(coordinator.active_workflows)}")
    print(f"  Workflow IDs: {list(coordinator.active_workflows.keys())}")

    # Both should be active
    assert len(coordinator.active_workflows) == 2, f"Should have 2 active workflows, got {len(coordinator.active_workflows)}"

    # Complete one workflow
    template = coordinator.get_workflow_template(WorkflowType.BUG_INVESTIGATION)
    for step in template.steps:
        await coordinator.execute_step(wf2.workflow_id, step)
    await coordinator.complete_workflow(wf2.workflow_id)

    print(f"\nAfter completing workflow 2:")
    print(f"  Active Workflows: {len(coordinator.active_workflows)}")

    # After completion, only 1 should remain active
    assert len(coordinator.active_workflows) == 1, "Should have 1 active after completing 1"
    print("\n✅ Test passed! Multiple workflows managed correctly")

    await coordinator.close()


async def test_metrics_summary():
    """Test 7: Metrics summary"""
    print("\n" + "="*70)
    print("Test 7: Metrics Summary")
    print("="*70)

    coordinator = WorkflowCoordinator(workspace_id="/Users/hue/code/dopemux-mvp")
    await coordinator.initialize()

    # Start and complete first workflow
    wf1 = await coordinator.start_workflow(WorkflowType.BUG_INVESTIGATION, "B1")
    template1 = coordinator.get_workflow_template(WorkflowType.BUG_INVESTIGATION)
    for step in template1.steps:
        await coordinator.execute_step(wf1.workflow_id, step)
    await coordinator.complete_workflow(wf1.workflow_id)

    # Start second workflow (leave active)
    wf2 = await coordinator.start_workflow(WorkflowType.FEATURE_IMPLEMENTATION, "F1")

    # Get metrics
    metrics = await coordinator.get_metrics_summary()

    print(f"\nMetrics:")
    print(f"  Workflows Started: {metrics['workflows_started']}")
    print(f"  Workflows Completed: {metrics['workflows_completed']}")
    print(f"  Active Workflows: {metrics['active_workflows']}")
    print(f"  Steps Executed: {metrics['steps_executed']}")
    print(f"  Completion Rate: {metrics['completion_rate']}%")

    assert metrics["workflows_started"] == 2, "Should have started 2"
    assert metrics["workflows_completed"] == 1, "Should have completed 1"
    assert metrics["active_workflows"] == 1, "Should have 1 active"
    assert metrics["completion_rate"] == 50.0, "Should be 50% completion"
    print("\n✅ Test passed! Metrics calculated correctly")

    await coordinator.close()


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("WEEK 10: WorkflowCoordinator Test Suite")
    print("="*70)

    tests = [
        ("Load Workflow Templates", test_load_workflow_templates),
        ("Start Workflow", test_start_workflow),
        ("Execute Workflow Step", test_execute_workflow_step),
        ("Workflow Status Tracking", test_workflow_status_tracking),
        ("Complete Workflow", test_workflow_completion),
        ("Multiple Active Workflows", test_multiple_workflows),
        ("Metrics Summary", test_metrics_summary),
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
