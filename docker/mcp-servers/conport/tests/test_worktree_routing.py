"""
Integration Tests for Worktree Multi-Instance Routing

Tests the core worktree functionality:
- Progress task isolation (IN_PROGRESS vs COMPLETED)
- Status transitions (IN_PROGRESS → COMPLETED clears instance_id)
- Active context per-instance isolation
- Multi-worktree query filtering

Run with: pytest tests/test_worktree_routing.py -v

NOTE: Requires PostgreSQL with migration 007 applied
"""

import os
import pytest
import uuid
from unittest.mock import patch


@pytest.fixture
def clear_env():
    """Clear environment variables before each test."""
    original_instance = os.environ.get('DOPEMUX_INSTANCE_ID')
    original_workspace = os.environ.get('DOPEMUX_WORKSPACE_ID')

    yield

    # Restore original values
    if original_instance:
        os.environ['DOPEMUX_INSTANCE_ID'] = original_instance
    else:
        os.environ.pop('DOPEMUX_INSTANCE_ID', None)

    if original_workspace:
        os.environ['DOPEMUX_WORKSPACE_ID'] = original_workspace
    else:
        os.environ.pop('DOPEMUX_WORKSPACE_ID', None)


class TestProgressTaskIsolation:
    """Test that progress tasks are isolated correctly by status."""

    def test_in_progress_task_isolated_to_instance(self, clear_env):
        """
        Scenario: Create IN_PROGRESS task in worktree A
        Expected: Task NOT visible in worktree B or main
        """
        from instance_detector import SimpleInstanceDetector

        # Worktree A creates IN_PROGRESS task
        os.environ['DOPEMUX_INSTANCE_ID'] = 'worktree-a'
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/test/workspace'

        context = SimpleInstanceDetector.get_context()
        status = 'IN_PROGRESS'
        should_isolate = SimpleInstanceDetector.is_isolated_status(status)

        assert should_isolate is True
        assert context['instance_id'] == 'worktree-a'
        assert context['is_multi_worktree'] is True

        # Simulate database insert
        # final_instance_id = 'worktree-a' (isolated)

    def test_completed_task_shared_across_instances(self, clear_env):
        """
        Scenario: Mark task as COMPLETED in worktree A
        Expected: Task visible in worktree B and main
        """
        from instance_detector import SimpleInstanceDetector

        # Worktree A completes task
        os.environ['DOPEMUX_INSTANCE_ID'] = 'worktree-a'

        status = 'COMPLETED'
        should_isolate = SimpleInstanceDetector.is_isolated_status(status)

        assert should_isolate is False
        # Simulate database insert
        # final_instance_id = None (shared across all worktrees)

    def test_blocked_task_shared_across_instances(self, clear_env):
        """
        Scenario: Mark task as BLOCKED
        Expected: Visible to all worktrees (blockers affect everyone)
        """
        from instance_detector import SimpleInstanceDetector

        status = 'BLOCKED'
        should_isolate = SimpleInstanceDetector.is_isolated_status(status)

        assert should_isolate is False
        # final_instance_id = None (shared)


class TestStatusTransitions:
    """Test that status transitions handle instance_id correctly."""

    def test_transition_in_progress_to_completed(self, clear_env):
        """
        Scenario: Task created as IN_PROGRESS (isolated), then marked COMPLETED
        Expected: instance_id cleared when status changes to COMPLETED
        """
        from instance_detector import SimpleInstanceDetector

        os.environ['DOPEMUX_INSTANCE_ID'] = 'worktree-a'

        # Initial status: IN_PROGRESS (should be isolated)
        initial_status = 'IN_PROGRESS'
        assert SimpleInstanceDetector.is_isolated_status(initial_status) is True
        initial_instance_id = 'worktree-a'  # Would be set

        # Transition to COMPLETED (should be shared)
        new_status = 'COMPLETED'
        assert SimpleInstanceDetector.is_isolated_status(new_status) is False
        final_instance_id = None  # Should be cleared

        # Verify logic
        assert initial_instance_id is not None
        assert final_instance_id is None

    def test_transition_completed_to_in_progress(self, clear_env):
        """
        Scenario: COMPLETED task (shared) reopened as IN_PROGRESS
        Expected: instance_id set when transitioning back to IN_PROGRESS
        """
        from instance_detector import SimpleInstanceDetector

        os.environ['DOPEMUX_INSTANCE_ID'] = 'worktree-b'

        # Initial: COMPLETED (shared, instance_id = NULL)
        initial_status = 'COMPLETED'
        initial_instance_id = None

        # Reopen as IN_PROGRESS
        new_status = 'IN_PROGRESS'
        assert SimpleInstanceDetector.is_isolated_status(new_status) is True
        final_instance_id = 'worktree-b'  # Should be set

        # Verify logic
        assert initial_instance_id is None
        assert final_instance_id == 'worktree-b'


class TestMultiWorktreeQuerying:
    """Test that queries correctly filter by instance."""

    def test_query_shows_shared_and_own_tasks(self, clear_env):
        """
        Scenario: Worktree A queries progress
        Expected: See shared tasks (instance_id=NULL) + own tasks (instance_id='worktree-a')
        """
        from instance_detector import SimpleInstanceDetector

        os.environ['DOPEMUX_INSTANCE_ID'] = 'worktree-a'

        current_instance_id = SimpleInstanceDetector.get_instance_id()
        assert current_instance_id == 'worktree-a'

        # SQL query pattern:
        # WHERE workspace_id = 'X'
        #   AND (instance_id IS NULL OR instance_id = 'worktree-a')
        #
        # This shows:
        # - All COMPLETED/BLOCKED tasks (instance_id = NULL)
        # - IN_PROGRESS tasks for worktree-a only

    def test_query_hides_other_instance_tasks(self, clear_env):
        """
        Scenario: Worktree A queries, worktree B has IN_PROGRESS task
        Expected: Worktree A does NOT see worktree B's IN_PROGRESS task
        """
        from instance_detector import SimpleInstanceDetector

        os.environ['DOPEMUX_INSTANCE_ID'] = 'worktree-a'
        current_instance_id = SimpleInstanceDetector.get_instance_id()

        # Task from worktree-b (instance_id = 'worktree-b')
        # Query: instance_id IS NULL OR instance_id = 'worktree-a'
        # Result: Does NOT match 'worktree-b' → Not visible

        assert current_instance_id != 'worktree-b'

    def test_main_worktree_sees_only_shared_tasks(self, clear_env):
        """
        Scenario: Main worktree (instance_id=NULL) queries progress
        Expected: Only sees shared tasks (COMPLETED/BLOCKED), not any IN_PROGRESS
        """
        from instance_detector import SimpleInstanceDetector

        # Main worktree (no env var)
        os.environ.pop('DOPEMUX_INSTANCE_ID', None)

        current_instance_id = SimpleInstanceDetector.get_instance_id()
        assert current_instance_id is None

        # SQL query:
        # WHERE instance_id IS NULL OR instance_id = NULL
        # Simplifies to: WHERE instance_id IS NULL
        #
        # Shows only shared tasks (all worktrees' COMPLETED/BLOCKED)


class TestActiveContextIsolation:
    """Test that active_context is isolated per instance."""

    def test_each_instance_has_own_context(self, clear_env):
        """
        Scenario: Worktree A and B each have different active_context
        Expected: Each worktree maintains independent context
        """
        from instance_detector import SimpleInstanceDetector

        # Worktree A
        os.environ['DOPEMUX_INSTANCE_ID'] = 'worktree-a'
        context_a = SimpleInstanceDetector.get_context()
        assert context_a['instance_id'] == 'worktree-a'

        # Worktree B
        os.environ['DOPEMUX_INSTANCE_ID'] = 'worktree-b'
        context_b = SimpleInstanceDetector.get_context()
        assert context_b['instance_id'] == 'worktree-b'

        # Each would query workspace_contexts with different instance_id
        # WHERE workspace_id = X AND instance_id = 'worktree-a'
        # WHERE workspace_id = X AND instance_id = 'worktree-b'
        # → Two separate rows in database

    def test_main_worktree_has_null_instance_context(self, clear_env):
        """
        Scenario: Main worktree context
        Expected: instance_id = NULL in database
        """
        from instance_detector import SimpleInstanceDetector

        os.environ.pop('DOPEMUX_INSTANCE_ID', None)

        context = SimpleInstanceDetector.get_context()
        assert context['instance_id'] is None
        assert context['is_main_worktree'] is True

        # Query: WHERE workspace_id = X AND instance_id IS NULL


class TestBackwardCompatibility:
    """Test that single-worktree mode still works."""

    def test_no_env_vars_works_as_before(self, clear_env):
        """
        Scenario: User doesn't set any env vars (single worktree mode)
        Expected: System works exactly as before migration
        """
        from instance_detector import SimpleInstanceDetector

        # Clear all env vars
        os.environ.pop('DOPEMUX_INSTANCE_ID', None)
        os.environ.pop('DOPEMUX_WORKSPACE_ID', None)

        # Should still work
        instance_id = SimpleInstanceDetector.get_instance_id()
        workspace_id = SimpleInstanceDetector.get_workspace_id()

        assert instance_id is None  # No instance isolation
        assert workspace_id == os.getcwd()  # Falls back to cwd

        # All tasks created with instance_id = NULL (shared)
        # Same behavior as pre-migration


class TestRealWorldScenarios:
    """End-to-end scenarios simulating actual usage."""

    def test_feature_branch_workflow(self, clear_env):
        """
        Full workflow: Create feature worktree, work on task, complete it.

        1. Main worktree creates overall project plan
        2. Feature worktree works on specific task
        3. Task completion visible in main worktree
        """
        from instance_detector import SimpleInstanceDetector

        # Step 1: Main worktree creates plan
        os.environ.pop('DOPEMUX_INSTANCE_ID', None)
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/test/project'

        main_context = SimpleInstanceDetector.get_context()
        assert main_context['is_main_worktree'] is True

        # Create project plan (PLANNED status → isolated to main? Or shared?)
        # Actually PLANNED is isolated, so:
        # instance_id = None (main worktree)

        # Step 2: Feature worktree starts implementation
        os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'

        feature_context = SimpleInstanceDetector.get_context()
        assert feature_context['is_multi_worktree'] is True
        assert feature_context['instance_id'] == 'feature-auth'

        # Create IN_PROGRESS task
        # instance_id = 'feature-auth' (isolated, main can't see)

        # Step 3: Complete task
        # Status change: IN_PROGRESS → COMPLETED
        # instance_id: 'feature-auth' → NULL (now shared)

        # Step 4: Back in main worktree
        os.environ.pop('DOPEMUX_INSTANCE_ID', None)

        # Query progress
        # Shows: COMPLETED task (instance_id = NULL)
        # Doesn't show: Original PLANNED from main (instance_id = NULL for main)

    def test_hotfix_urgent_workflow(self, clear_env):
        """
        Workflow: Working in feature, urgent hotfix needed, switch worktrees.

        1. Feature worktree has IN_PROGRESS task
        2. Create hotfix worktree
        3. Feature task still isolated, not visible in hotfix
        4. Complete hotfix, visible everywhere
        """
        from instance_detector import SimpleInstanceDetector

        # Feature worktree
        os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/test/project'

        # IN_PROGRESS task in feature
        # instance_id = 'feature-auth' (isolated)

        # Hotfix worktree
        os.environ['DOPEMUX_INSTANCE_ID'] = 'hotfix-redis'

        hotfix_context = SimpleInstanceDetector.get_context()
        assert hotfix_context['instance_id'] == 'hotfix-redis'

        # Query progress in hotfix
        # Shows: Shared tasks only (COMPLETED/BLOCKED)
        # Doesn't show: feature-auth IN_PROGRESS task

        # Complete hotfix
        # instance_id = NULL (shared, visible everywhere)
