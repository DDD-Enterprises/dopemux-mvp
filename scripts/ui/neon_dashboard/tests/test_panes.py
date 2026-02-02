"""Test pane rendering and interactions."""

import pytest
from textual.widgets import Tree

from scripts.neon_dashboard.panes.pm_hierarchy import PMHierarchyPane
from scripts.neon_dashboard.panes.task_detail import TaskDetailPane


def test_pm_hierarchy_epics_update():
    """Test epic/task tree building without Textual app context."""
    pane = PMHierarchyPane()
    
    test_epics = [
        {
            "id": "epic1",
            "name": "Test Epic",
            "completion": 75,
            "tasks": [
                {
                    "id": "task1",
                    "name": "Task 1",
                    "status": "DONE",
                    "estimate": 4,
                    "spent": 4,
                    "subtasks": [
                        {"id": "sub1", "name": "Subtask 1", "status": "DONE"}
                    ]
                },
                {
                    "id": "task2",
                    "name": "Task 2",
                    "status": "IN_PROGRESS",
                    "estimate": 6,
                    "spent": 3,
                    "subtasks": []
                }
            ]
        }
    ]
    
    # Outside Textual app context, update_epics stores pending epics
    pane.update_epics(test_epics)
    
    # Verify pending epics are stored (tree not yet mounted)
    assert pane._pending_epics is not None
    assert len(pane._pending_epics) == 1
    assert pane._pending_epics[0]["id"] == "epic1"


def test_task_detail_update():
    """Test task detail display."""
    pane = TaskDetailPane()
    
    test_task = {
        "id": "task1",
        "name": "Test Task",
        "status": "IN_PROGRESS",
        "estimate": 4,
        "spent": 2.5,
        "description": "This is a test task",
        "files": ["file1.py", "file2.py"]
    }
    
    pane.update_task(test_task)
    
    assert pane._task == test_task


def test_task_detail_placeholder():
    """Test placeholder message."""
    pane = TaskDetailPane()
    
    # Should show placeholder initially
    pane.update_task(None)
    assert pane._task is None
