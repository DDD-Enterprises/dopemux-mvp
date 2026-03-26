import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio
from unittest import IsolatedAsyncioTestCase
import sys

try:
    from pydantic import BaseModel
except ImportError:
    class MockPydantic:
        class BaseModel:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        def Field(*args, **kwargs):
            return kwargs.get('default')
        def field_validator(*args, **kwargs):
            def decorator(f): return f
            return decorator
        def model_validator(*args, **kwargs):
            def decorator(f): return f
            return decorator
    sys.modules['pydantic'] = MockPydantic

try:
    import aiohttp
except ImportError:
    sys.modules['aiohttp'] = MagicMock()

from app.adapters.conport_adapter import ConPortEventAdapter
from app.adapters.conport_insight_publisher import ConPortInsightPublisher
from task_orchestrator.models import OrchestrationTask

class TestConPortClientContract(IsolatedAsyncioTestCase):
    def setUp(self):
        client = MagicMock()
        client.log_progress = AsyncMock()
        client.log_decision = AsyncMock()
        client.update_progress = AsyncMock()
        
        # Setup returned canonical shapes
        mock_progress_entry = MagicMock()
        mock_progress_entry.id = 123
        client.log_progress.return_value = mock_progress_entry
        
        mock_decision = MagicMock()
        mock_decision.id = 456
        client.log_decision.return_value = mock_decision
        
        client.update_progress.return_value = True
        
        self.mock_conport_client = client

    async def test_conport_adapter_progress_canonical(self):
        adapter = ConPortEventAdapter(workspace_id="/test", conport_client=self.mock_conport_client)
        
        task = OrchestrationTask(id="task-1", title="Test Task", description="Test")
        
        conport_id = await adapter.create_task_in_conport(task)
        
        assert conport_id == 123
        self.mock_conport_client.log_progress.assert_called_once()
        assert task.conport_id == 123

    async def test_conport_adapter_fail_closed_if_unconfigured(self):
        adapter = ConPortEventAdapter(workspace_id="/test", conport_client=None)
        adapter.conport_client = None  # Force unconfigured to test explicit guard
        
        with pytest.raises(ValueError):
            await adapter._resilient_log_progress({"status": "TODO", "description": "test"})

    async def test_conport_insight_publisher_decision_canonical(self):
        publisher = ConPortInsightPublisher(workspace_id="/test", conport_client=self.mock_conport_client)
        
        decision_data = {
            "summary": "Use shared client",
            "rationale": "Unifies surface"
        }
        
        decision_id = await publisher._resilient_log_decision(decision_data)
        
        assert decision_id == 456
        self.mock_conport_client.log_decision.assert_called_once_with(
            summary="Use shared client",
            rationale="Unifies surface",
            tags=[]
        )

    async def test_conport_insight_publisher_fail_closed(self):
        publisher = ConPortInsightPublisher(workspace_id="/test", conport_client=None)
        publisher.conport_client = None  # Force unconfigured
        
        decision_data = {
            "summary": "Use shared client",
            "rationale": "Unifies surface"
        }
        
        with pytest.raises(ValueError):
            await publisher._resilient_log_decision(decision_data)

    async def test_conport_adapter_update_progress(self):
        adapter = ConPortEventAdapter(workspace_id="/test", conport_client=self.mock_conport_client)
        
        success = await adapter._resilient_update_progress(
            progress_id=123,
            status="IN_PROGRESS",
            description="Working on it"
        )
        
        assert success is True
        self.mock_conport_client.update_progress.assert_called_once_with(
            progress_id=123,
            updates={"status": "IN_PROGRESS", "description": "Working on it"}
        )
