import pytest
from dopemux.pm.reads import (
    pm_get_project_context,
    pm_get_priority_queue,
    pm_get_blockers,
    pm_get_workflow_state,
    pm_get_sprint_snapshot,
    pm_get_decision_context,
)

@pytest.mark.asyncio
async def test_pm_get_project_context():
    result = await pm_get_project_context("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "leantime"
    assert result.provenance.source == "leantime"
    assert result.provenance.query_mode == "project_context"
    assert len(result.supporting_sources) == 1
    assert result.supporting_sources[0].backend == "leantime"
    assert result.context_data == {} # Stubbed to fail-closed empty dict

    # Test fail closed
    result = await pm_get_project_context("fail_me")
    assert result.context_data == {}

    # Test invalid input
    with pytest.raises(ValueError):
        await pm_get_project_context("")

@pytest.mark.asyncio
async def test_pm_get_priority_queue():
    result = await pm_get_priority_queue("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "leantime"
    assert result.provenance.source == "leantime"
    assert result.queue_items == [] # Stubbed to fail-closed empty list

    # Test fail closed
    result = await pm_get_priority_queue("fail_me")
    assert result.queue_items == []

    # Test invalid input
    with pytest.raises(ValueError):
        await pm_get_priority_queue("")

@pytest.mark.asyncio
async def test_pm_get_blockers():
    result = await pm_get_blockers("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "leantime"
    assert result.provenance.source == "leantime"
    assert result.active_blockers == [] # Stubbed to fail-closed empty list

    # Test fail closed
    result = await pm_get_blockers("fail_me")
    assert result.active_blockers == []

    # Test invalid input
    with pytest.raises(ValueError):
        await pm_get_blockers("")

@pytest.mark.asyncio
async def test_pm_get_workflow_state():
    result = await pm_get_workflow_state("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "leantime"
    assert result.provenance.source == "leantime"
    assert result.state == {} # Stubbed to fail-closed empty dict
    assert result.allowed_transitions == []

    # Test fail closed
    result = await pm_get_workflow_state("fail_me")
    assert result.state == {}

    # Test invalid input
    with pytest.raises(ValueError):
        await pm_get_workflow_state("")

@pytest.mark.asyncio
async def test_pm_get_sprint_snapshot():
    result = await pm_get_sprint_snapshot("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "leantime"
    assert result.provenance.source == "leantime"
    assert result.snapshot_data == {} # Stubbed to fail-closed empty dict

    # Test fail closed
    result = await pm_get_sprint_snapshot("fail_me")
    assert result.snapshot_data == {}

    # Test invalid input
    with pytest.raises(ValueError):
        await pm_get_sprint_snapshot("")

@pytest.mark.asyncio
async def test_pm_get_decision_context():
    result = await pm_get_decision_context("proj-123")
    assert result.project_id == "proj-123"
    assert result.canonical_backend == "conport"
    assert result.provenance.source == "conport"
    assert result.decisions == [] # Stubbed to fail-closed empty list

    # Test fail closed
    result = await pm_get_decision_context("fail_me")
    assert result.decisions == []

    # Test invalid input
    with pytest.raises(ValueError):
        await pm_get_decision_context("")
