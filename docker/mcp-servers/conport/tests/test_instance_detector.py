"""
Tests for SimpleInstanceDetector

Run with: pytest tests/test_instance_detector.py -v
"""

import os
import pytest
from instance_detector import SimpleInstanceDetector, get_instance_id, get_workspace_id


class TestSimpleInstanceDetector:
    """Test SimpleInstanceDetector class methods."""

    def setup_method(self):
        """Clear environment variables before each test."""
        os.environ.pop('DOPEMUX_INSTANCE_ID', None)
        os.environ.pop('DOPEMUX_WORKSPACE_ID', None)

    def test_get_instance_id_returns_none_when_not_set(self):
        """Test that get_instance_id returns None when env var not set."""
        instance_id = SimpleInstanceDetector.get_instance_id()
        assert instance_id is None

    def test_get_instance_id_returns_value_when_set(self):
        """Test that get_instance_id returns value when env var is set."""
        os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'
        instance_id = SimpleInstanceDetector.get_instance_id()
        assert instance_id == 'feature-auth'

    def test_get_instance_id_treats_empty_string_as_none(self):
        """Test that empty string is treated as unset (returns None)."""
        os.environ['DOPEMUX_INSTANCE_ID'] = ''
        instance_id = SimpleInstanceDetector.get_instance_id()
        assert instance_id is None

    def test_get_workspace_id_returns_env_var_when_set(self):
        """Test that get_workspace_id returns env var when set."""
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/Users/hue/code/dopemux-mvp'
        workspace_id = SimpleInstanceDetector.get_workspace_id()
        assert workspace_id == '/Users/hue/code/dopemux-mvp'

    def test_get_workspace_id_falls_back_to_cwd(self):
        """Test that get_workspace_id falls back to cwd when not set."""
        workspace_id = SimpleInstanceDetector.get_workspace_id()
        assert workspace_id == os.getcwd()

    def test_get_context_main_worktree(self):
        """Test get_context for main worktree (no instance_id)."""
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/test/workspace'
        # instance_id not set (main worktree)

        context = SimpleInstanceDetector.get_context()

        assert context['instance_id'] is None
        assert context['workspace_id'] == '/test/workspace'
        assert context['is_main_worktree'] is True
        assert context['is_multi_worktree'] is False

    def test_get_context_linked_worktree(self):
        """Test get_context for linked worktree (instance_id set)."""
        os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/test/workspace'

        context = SimpleInstanceDetector.get_context()

        assert context['instance_id'] == 'feature-auth'
        assert context['workspace_id'] == '/test/workspace'
        assert context['is_main_worktree'] is False
        assert context['is_multi_worktree'] is True

    def test_is_isolated_status_in_progress(self):
        """Test that IN_PROGRESS is isolated."""
        assert SimpleInstanceDetector.is_isolated_status('IN_PROGRESS') is True

    def test_is_isolated_status_planned(self):
        """Test that PLANNED is isolated."""
        assert SimpleInstanceDetector.is_isolated_status('PLANNED') is True

    def test_is_isolated_status_completed(self):
        """Test that COMPLETED is shared (not isolated)."""
        assert SimpleInstanceDetector.is_isolated_status('COMPLETED') is False

    def test_is_isolated_status_blocked(self):
        """Test that BLOCKED is shared (not isolated)."""
        assert SimpleInstanceDetector.is_isolated_status('BLOCKED') is False

    def test_is_isolated_status_cancelled(self):
        """Test that CANCELLED is shared (not isolated)."""
        assert SimpleInstanceDetector.is_isolated_status('CANCELLED') is False

    def test_is_isolated_status_case_insensitive(self):
        """Test that status matching is case-insensitive."""
        assert SimpleInstanceDetector.is_isolated_status('in_progress') is True
        assert SimpleInstanceDetector.is_isolated_status('In_Progress') is True
        assert SimpleInstanceDetector.is_isolated_status('completed') is False


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def setup_method(self):
        """Clear environment variables before each test."""
        os.environ.pop('DOPEMUX_INSTANCE_ID', None)
        os.environ.pop('DOPEMUX_WORKSPACE_ID', None)

    def test_get_instance_id_function(self):
        """Test convenience function get_instance_id()."""
        os.environ['DOPEMUX_INSTANCE_ID'] = 'hotfix-redis'
        assert get_instance_id() == 'hotfix-redis'

    def test_get_workspace_id_function(self):
        """Test convenience function get_workspace_id()."""
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/test/path'
        assert get_workspace_id() == '/test/path'

    def test_get_context_function(self):
        """Test convenience function get_context()."""
        os.environ['DOPEMUX_INSTANCE_ID'] = 'test'
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/workspace'

        context = SimpleInstanceDetector.get_context()

        assert context['instance_id'] == 'test'
        assert context['workspace_id'] == '/workspace'


class TestRealWorldScenarios:
    """Test realistic worktree usage scenarios."""

    def setup_method(self):
        """Clear environment variables before each test."""
        os.environ.pop('DOPEMUX_INSTANCE_ID', None)
        os.environ.pop('DOPEMUX_WORKSPACE_ID', None)

    def test_scenario_main_worktree_single_instance(self):
        """
        Scenario: User working in main worktree, single instance mode.
        Expected: instance_id=None, workspace_id=cwd
        """
        context = SimpleInstanceDetector.get_context()

        assert context['instance_id'] is None
        assert context['is_main_worktree'] is True
        assert context['workspace_id'] == os.getcwd()

    def test_scenario_feature_worktree(self):
        """
        Scenario: User working in feature worktree with env vars set.
        Expected: instance_id="feature-auth", workspace_id="/path/to/main"
        """
        os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/Users/hue/code/dopemux-mvp'

        context = SimpleInstanceDetector.get_context()

        assert context['instance_id'] == 'feature-auth'
        assert context['workspace_id'] == '/Users/hue/code/dopemux-mvp'
        assert context['is_multi_worktree'] is True

    def test_scenario_task_creation_in_progress(self):
        """
        Scenario: Creating IN_PROGRESS task in feature worktree.
        Expected: Task should be isolated (instance_id set)
        """
        os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'

        status = 'IN_PROGRESS'
        should_isolate = SimpleInstanceDetector.is_isolated_status(status)

        assert should_isolate is True
        # In actual code: final_instance_id = instance_id if should_isolate else None

    def test_scenario_task_completion_shared(self):
        """
        Scenario: Marking task as COMPLETED in feature worktree.
        Expected: Task should be shared (instance_id cleared)
        """
        os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'

        status = 'COMPLETED'
        should_isolate = SimpleInstanceDetector.is_isolated_status(status)

        assert should_isolate is False
        # In actual code: final_instance_id = None (shared across worktrees)

    def test_scenario_switch_between_worktrees(self):
        """
        Scenario: Switching from main to feature worktree (env change).
        Expected: Context changes reflect new environment.
        """
        # Start in main worktree
        context_main = SimpleInstanceDetector.get_context()
        assert context_main['is_main_worktree'] is True

        # Switch to feature worktree (user sets env vars)
        os.environ['DOPEMUX_INSTANCE_ID'] = 'feature-auth'
        os.environ['DOPEMUX_WORKSPACE_ID'] = '/Users/hue/code/dopemux-mvp'

        context_feature = SimpleInstanceDetector.get_context()
        assert context_feature['is_multi_worktree'] is True
        assert context_feature['instance_id'] == 'feature-auth'
