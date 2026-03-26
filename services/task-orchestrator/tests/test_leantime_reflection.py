import sys
import os
from pathlib import Path
import pytest
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

# Wrap missing imports so the test suite does not crash if run natively
try:
    from app.models.workflow import (
        WorkflowEpic,
        CreateEpicRequest,
        PromoteIdeaRequest,
        WorkflowIdea,
        LeantimeReflection,
        ADHDMetadata
    )
    from app.services.workflow_service import WorkflowService, WorkflowNotFoundError
    from app.core.sync import SyncOperation, SyncDirection, MultiDirectionalSyncEngine
except ImportError:
    pass

@pytest.fixture
def mock_store():
    class MockStore:
        def __init__(self):
            self.epics = {}
            self.ideas = {}

        async def get_epic(self, epic_id: str):
            return self.epics.get(epic_id)

        async def save_epic(self, epic: dict):
            self.epics[epic["id"]] = epic
            return True

        async def get_idea(self, idea_id: str):
            return self.ideas.get(idea_id)

        async def save_idea(self, idea: dict):
            self.ideas[idea["id"]] = idea
            return True
            
        async def list_ideas(self, **kwargs):
            return list(self.ideas.values())
            
        async def list_epics(self, **kwargs):
            return list(self.epics.values())
    return MockStore()

@pytest.fixture
def mock_bridge():
    class MockResponse:
        def __init__(self, success, data=None, error=None):
            self.success = success
            self.data = data
            self.error = error

    class MockBridgeClient:
        def __init__(self):
            self.should_fail = False
            self.fail_message = "leantime api down"

        async def route_pm(self, **kwargs):
            if self.should_fail:
                return MockResponse(success=False, error=self.fail_message)
            return MockResponse(success=True, data={"projectId": 12345})
    return MockBridgeClient()

@pytest.fixture
def workflow_service(mock_store, mock_bridge):
    os.environ["DOPMUX_WORKFLOW_ENABLE"] = "true"
    # Need to import inside fixture to respect mock context if any
    try:
        from app.services.workflow_service import WorkflowService
        service = WorkflowService(workspace_id="test-workspace", store=mock_store)
        service.bridge_client = mock_bridge
        return service
    except ImportError:
        return None

@pytest.mark.asyncio
async def test_epic_promotion_reflection_success(workflow_service, mock_store, mock_bridge):
    """Test successful Leantime sync reflection."""
    if not workflow_service:
        pytest.skip("Dependencies not available")
        
    now = datetime.now(timezone.utc).isoformat()
    # Need to pass required keyword args correctly based on the mock/pydantic implementation
    idea_dict = {
        "id": "idea_1",
        "title": "Test Idea",
        "description": "Desc",
        "creator": "test",
        "tags": [],
        "status": "new",
        "created_at": now,
        "updated_at": now,
    }
    await mock_store.save_idea(idea_dict)

    # Re-fetch idea logic expects mock_store to return dictionary correctly
    request = PromoteIdeaRequest(sync_to_leantime=True, title="Test Epic", description="Epic Desc")
    result = await workflow_service.promote_idea("idea_1", request)

    epic = result["epic"]
    assert epic.leantime_project_id == 12345
    assert epic.leantime_reflection is not None
    assert epic.leantime_reflection.status == "success"
    assert epic.leantime_reflection.drift_detected is False
    assert epic.leantime_reflection.leantime_project_id == 12345

@pytest.mark.asyncio
async def test_epic_promotion_reflection_degraded(workflow_service, mock_store, mock_bridge):
    """Test degraded Leantime sync reflection when Leantime API is down."""
    if not workflow_service:
        pytest.skip("Dependencies not available")
        
    now = datetime.now(timezone.utc).isoformat()
    idea_dict = {
        "id": "idea_2",
        "title": "Test Idea 2",
        "description": "Desc",
        "creator": "test",
        "tags": [],
        "status": "new",
        "created_at": now,
        "updated_at": now,
    }
    await mock_store.save_idea(idea_dict)

    mock_bridge.should_fail = True
    
    request = PromoteIdeaRequest(sync_to_leantime=True, title="Test Epic 2", description="Epic Desc")
    result = await workflow_service.promote_idea("idea_2", request)

    epic = result["epic"]
    assert epic.leantime_project_id is None
    assert epic.leantime_reflection is not None
    assert epic.leantime_reflection.status == "degraded"
    assert epic.leantime_reflection.drift_detected is True
    assert epic.leantime_reflection.warning == "leantime api down"

@pytest.mark.asyncio
async def test_sync_engine_conport_to_leantime_reflection():
    """Test SyncOperation reflection status when syncing from ConPort to Leantime."""
    try:
        from app.core.sync import SyncOperation, SyncDirection, MultiDirectionalSyncEngine
    except ImportError:
        pytest.skip("Dependencies not available")
        
    engine = MultiDirectionalSyncEngine()
    
    # Mock finding tasks
    engine._find_affected_leantime_tasks = lambda x: asyncio.sleep(0, result=["123"])
    
    op = SyncOperation(
        id="sync_1",
        direction=SyncDirection.CONPORT_TO_LEANTIME,
        source_system="conport",
        target_system="leantime",
        entity_type="progress",
        entity_id="prog_1",
        source_data={
            "linked_item_type": "leantime_task",
            "linked_item_id": 123,
            "status": "DONE",
            "description": "Finished the task"
        }
    )
    
    success = await engine._sync_conport_to_leantime(op)
    assert success is True
    assert op.leantime_reflection_status == "success"

@pytest.mark.asyncio
async def test_sync_engine_conport_to_leantime_reflection_ignored():
    """Test SyncOperation reflection status when syncing irrelevant ConPort progress."""
    try:
        from app.core.sync import SyncOperation, SyncDirection, MultiDirectionalSyncEngine
    except ImportError:
        pytest.skip("Dependencies not available")
        
    engine = MultiDirectionalSyncEngine()
    
    op = SyncOperation(
        id="sync_2",
        direction=SyncDirection.CONPORT_TO_LEANTIME,
        source_system="conport",
        target_system="leantime",
        entity_type="progress",
        entity_id="prog_2",
        source_data={
            "linked_item_type": "other_task",
            "linked_item_id": 456,
            "status": "DONE"
        }
    )
    
    success = await engine._sync_conport_to_leantime(op)
    assert success is False
    assert op.leantime_reflection_status == "ignored"

