"""
Tests for InstanceStateManager orphaned instance filtering.

Tests ADHD-optimized filtering: age limits, count limits, sorting.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from src.dopemux.instance_state import (
    InstanceState,
    InstanceStateManager,
)


@pytest.fixture
def temp_workspace():
    """Create temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_manager(temp_workspace):
    """Create InstanceStateManager with mocked ConPort."""
    manager = InstanceStateManager(
        workspace_id=str(temp_workspace),
        conport_port=3007
    )
    return manager


@pytest.fixture
def sample_orphaned_states(temp_workspace):
    """Create sample orphaned states with varying ages."""
    now = datetime.now()

    # Create temporary worktree directories
    worktree1 = temp_workspace / "worktree-1"
    worktree2 = temp_workspace / "worktree-2"
    worktree3 = temp_workspace / "worktree-3"
    worktree4 = temp_workspace / "worktree-4"

    for wt in [worktree1, worktree2, worktree3, worktree4]:
        wt.mkdir()

    states = [
        InstanceState(
            instance_id="inst-1",
            port_base=3000,
            worktree_path=str(worktree1),
            git_branch="feature/auth",
            created_at=now - timedelta(hours=2),
            last_active=now - timedelta(hours=1),  # 1 hour ago
            status="orphaned",
            last_focus_context="Implementing JWT tokens"
        ),
        InstanceState(
            instance_id="inst-2",
            port_base=3010,
            worktree_path=str(worktree2),
            git_branch="feature/api",
            created_at=now - timedelta(days=3),
            last_active=now - timedelta(days=2),  # 2 days ago
            status="orphaned",
            last_focus_context="Building REST endpoints"
        ),
        InstanceState(
            instance_id="inst-3",
            port_base=3020,
            worktree_path=str(worktree3),
            git_branch="bugfix/memory-leak",
            created_at=now - timedelta(days=10),
            last_active=now - timedelta(days=9),  # 9 days ago (too old)
            status="orphaned",
            last_focus_context="Debugging memory issues"
        ),
        InstanceState(
            instance_id="inst-4",
            port_base=3030,
            worktree_path=str(worktree4),
            git_branch="feature/ui",
            created_at=now - timedelta(hours=12),
            last_active=now - timedelta(hours=6),  # 6 hours ago
            status="orphaned",
            last_focus_context="Redesigning dashboard"
        ),
    ]

    return states


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_basic(mock_manager, sample_orphaned_states):
    """Test basic filtering with default parameters."""
    # Mock find_orphaned_instances to return sample data (includes 9-day-old inst-3)
    mock_manager.find_orphaned_instances = AsyncMock(return_value=sample_orphaned_states[:3])

    result = await mock_manager.find_orphaned_instances_filtered()

    # Should return 2 (inst-3 filtered out due to 7-day default age limit)
    assert len(result) == 2
    instance_ids = [s.instance_id for s in result]
    assert "inst-1" in instance_ids
    assert "inst-2" in instance_ids
    assert "inst-3" not in instance_ids  # Too old (9 days)


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_age_limit(mock_manager, sample_orphaned_states):
    """Test age filtering removes old instances."""
    # Mock to return all states including the 9-day-old one
    mock_manager.find_orphaned_instances = AsyncMock(return_value=sample_orphaned_states)

    # Filter with 7-day limit (default)
    result = await mock_manager.find_orphaned_instances_filtered(max_age_days=7)

    # Should exclude inst-3 (9 days old)
    instance_ids = [s.instance_id for s in result]
    assert "inst-3" not in instance_ids
    assert len(result) == 3  # inst-1, inst-2, inst-4


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_count_limit(mock_manager, sample_orphaned_states):
    """Test count limiting for ADHD decision reduction."""
    mock_manager.find_orphaned_instances = AsyncMock(return_value=sample_orphaned_states[:3])

    # Limit to 2 results
    result = await mock_manager.find_orphaned_instances_filtered(limit=2)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_adhd_max_3(mock_manager, sample_orphaned_states):
    """Test ADHD-optimized max 3 options."""
    mock_manager.find_orphaned_instances = AsyncMock(return_value=sample_orphaned_states[:3])

    # Use ADHD-recommended limit of 3
    result = await mock_manager.find_orphaned_instances_filtered(limit=3)

    assert len(result) <= 3


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_sorting(mock_manager, sample_orphaned_states):
    """Test sorting by most recent first."""
    # Include inst-1, inst-2, inst-4 (exclude inst-3 which is 9 days old)
    states_for_test = [sample_orphaned_states[0], sample_orphaned_states[1], sample_orphaned_states[3]]
    mock_manager.find_orphaned_instances = AsyncMock(return_value=states_for_test)

    result = await mock_manager.find_orphaned_instances_filtered(sort_by_recent=True)

    # Should be sorted: inst-1 (1h) -> inst-4 (6h) -> inst-2 (2d)
    assert len(result) == 3
    assert result[0].instance_id == "inst-1"
    assert result[1].instance_id == "inst-4"
    assert result[2].instance_id == "inst-2"


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_no_sorting(mock_manager, sample_orphaned_states):
    """Test without sorting (original order)."""
    # Use inst-1, inst-2, inst-4 (inst-3 is too old)
    states_for_test = [sample_orphaned_states[0], sample_orphaned_states[1], sample_orphaned_states[3]]
    mock_manager.find_orphaned_instances = AsyncMock(return_value=states_for_test)

    result = await mock_manager.find_orphaned_instances_filtered(sort_by_recent=False)

    # Should maintain original order and include all 3 (all within 7-day limit)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_empty(mock_manager):
    """Test with no orphaned instances."""
    mock_manager.find_orphaned_instances = AsyncMock(return_value=[])

    result = await mock_manager.find_orphaned_instances_filtered()

    assert result == []


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_custom_age(mock_manager, sample_orphaned_states):
    """Test custom age limit."""
    mock_manager.find_orphaned_instances = AsyncMock(return_value=sample_orphaned_states)

    # Very short age limit (1 day)
    result = await mock_manager.find_orphaned_instances_filtered(max_age_days=1)

    # Should only include inst-1 (1h) and inst-4 (6h)
    instance_ids = [s.instance_id for s in result]
    assert "inst-1" in instance_ids
    assert "inst-4" in instance_ids
    assert "inst-2" not in instance_ids  # 2 days old
    assert len(result) == 2


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_combination(mock_manager, sample_orphaned_states):
    """Test age + limit + sorting combination."""
    mock_manager.find_orphaned_instances = AsyncMock(return_value=sample_orphaned_states)

    # 7-day limit, max 2 results, sorted
    result = await mock_manager.find_orphaned_instances_filtered(
        max_age_days=7,
        limit=2,
        sort_by_recent=True
    )

    # Should return 2 most recent within 7 days: inst-1 and inst-4
    assert len(result) == 2
    assert result[0].instance_id == "inst-1"  # Most recent
    assert result[1].instance_id == "inst-4"  # Second most recent


@pytest.mark.asyncio
async def test_find_orphaned_instances_filtered_adhd_scenario(mock_manager, sample_orphaned_states):
    """Test typical ADHD startup scenario: show 3 most recent from last week."""
    mock_manager.find_orphaned_instances = AsyncMock(return_value=sample_orphaned_states)

    # ADHD-optimized defaults: 7 days, max 3, sorted
    result = await mock_manager.find_orphaned_instances_filtered(
        max_age_days=7,
        limit=3,
        sort_by_recent=True
    )

    # Should show 3 most recent from last 7 days
    assert len(result) == 3
    assert result[0].instance_id == "inst-1"  # 1 hour ago
    assert result[1].instance_id == "inst-4"  # 6 hours ago
    assert result[2].instance_id == "inst-2"  # 2 days ago
    assert all(s.instance_id != "inst-3" for s in result)  # Exclude 9-day-old
