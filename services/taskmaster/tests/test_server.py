import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from services.taskmaster.server import TaskMasterWrapper

@pytest.fixture
def wrapper():
    return TaskMasterWrapper()

@pytest.mark.asyncio
async def test_wrapper_initialization(wrapper):
    assert wrapper.instance_id is not None
    assert wrapper.workspace_id is not None
    assert wrapper.adhd_config["focus_duration"] > 0

@pytest.mark.asyncio
async def test_emit_task_event_no_producer(wrapper):
    # Tests that emit gracefully fails/no-ops when producer is none
    wrapper.mcp_producer = None
    # Should not raise
    await wrapper.emit_task_event("test_event", {"data": "test"})

@pytest.mark.asyncio
async def test_handle_message_json_pass_through(wrapper):
    msg = b'{"jsonrpc": "2.0", "method": "test"}'
    with patch("services.taskmaster.server.sys") as mock_sys:
        wrapper.process = MagicMock()
        wrapper.process.stdin = MagicMock()
        
        await wrapper.handle_message(msg)
        
        wrapper.process.stdin.write.assert_called_once_with(msg)
        wrapper.process.stdin.flush.assert_called_once()

@pytest.mark.asyncio
async def test_handle_response_tracked_call(wrapper):
    # Setup pending call
    wrapper.pending_calls["1"] = {
        "tool": "create_task",
        "params": {},
        "start_time": MagicMock()
    }
    wrapper.pending_calls["1"]["start_time"].timestamp.return_value = 0
    
    resp = b'{"jsonrpc": "2.0", "id": "1", "result": {}}'
    
    with patch("services.taskmaster.server.sys") as mock_sys:
        # Prevent actually calling sys.stdout/stderr things
        wrapper.mcp_producer = MagicMock()
        
        with patch.object(wrapper, "emit_task_event", new_callable=AsyncMock) as mock_emit:
            await wrapper.handle_response(resp)
            mock_emit.assert_called_once()
            
            call_args = mock_emit.call_args[0]
            assert call_args[0] == "completed"
            assert call_args[1]["tool"] == "create_task"
