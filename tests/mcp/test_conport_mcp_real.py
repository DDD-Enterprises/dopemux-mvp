import asyncio
import json
import pytest
import sys
from pathlib import Path
from aiohttp import web
from unittest.mock import MagicMock, AsyncMock, patch

# Add the directory containing enhanced_server.py to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "docker/mcp-servers/conport"))

from enhanced_server import EnhancedConPortServer

@pytest.fixture
def server():
    with patch('asyncpg.create_pool'), \
         patch('redis.asyncio.from_url'), \
         patch('enhanced_server.SimpleInstanceDetector'):
        srv = EnhancedConPortServer()
        # Mock dependencies
        srv.db_pool = AsyncMock()
        srv.redis = AsyncMock()
        return srv

@pytest.mark.asyncio
async def test_mcp_discovery(server):
    # Discovery should return tool list
    request_data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    mock_request = AsyncMock()
    mock_request.json.return_value = request_data
    
    response = await server.mcp_endpoint(mock_request)
    body = json.loads(response.body)
    
    assert "result" in body
    assert "tools" in body["result"]
    tools = body["result"]["tools"]
    assert any(t["name"] == "conport_log_progress" for t in tools)
    assert any(t["name"] == "conport_get_context" for t in tools)
    print("✓ MCP Discovery works")

@pytest.mark.asyncio
async def test_mcp_tool_call_log_progress(server):
    # Tool call should invoke handler
    request_data = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "conport_log_progress",
            "arguments": {
                "workspace_id": "ws-test",
                "description": "test task"
            }
        }
    }
    
    # Mock _log_progress
    server._log_progress = AsyncMock(return_value={"status": "logged", "progress": {"id": "123"}})
    
    mock_request = AsyncMock()
    mock_request.json.return_value = request_data
    
    response = await server.mcp_endpoint(mock_request)
    body = json.loads(response.body)
    
    assert "result" in body
    assert body["result"]["status"] == "logged"
    server._log_progress.assert_called_once_with({
        "workspace_id": "ws-test",
        "description": "test task"
    })
    print("✓ MCP Tool Call (tools/call) works")

@pytest.mark.asyncio
async def test_mcp_direct_dispatch(server):
    # Direct dispatch (method name = tool name)
    request_data = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "conport_get_context",
        "params": {
            "workspace_id": "ws-test"
        }
    }
    
    # Mock _get_context
    server._get_context = AsyncMock(return_value={"workspace_id": "ws-test", "active_context": "test"})
    
    mock_request = AsyncMock()
    mock_request.json.return_value = request_data
    
    response = await server.mcp_endpoint(mock_request)
    body = json.loads(response.body)
    
    assert "result" in body
    assert body["result"]["workspace_id"] == "ws-test"
    server._get_context.assert_called_once_with("ws-test")
    print("✓ MCP Direct Dispatch works")

@pytest.mark.asyncio
async def test_mcp_unknown_method(server):
    # Unknown method should return error
    request_data = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "definitely_not_real",
        "params": {}
    }
    
    mock_request = AsyncMock()
    mock_request.json.return_value = request_data
    
    response = await server.mcp_endpoint(mock_request)
    body = json.loads(response.body)
    
    assert "error" in body
    assert body["error"]["code"] == -32601
    assert "Method not found" in body["error"]["message"]
    print("✓ MCP Unknown Method returns error")

@pytest.mark.asyncio
async def test_mcp_invalid_request(server):
    # Invalid request (missing method)
    request_data = {
        "jsonrpc": "2.0",
        "id": 5
    }
    
    mock_request = AsyncMock()
    mock_request.json.return_value = request_data
    
    response = await server.mcp_endpoint(mock_request)
    body = json.loads(response.body)
    
    assert "error" in body
    assert body["error"]["code"] == -32600
    print("✓ MCP Invalid Request returns error")
