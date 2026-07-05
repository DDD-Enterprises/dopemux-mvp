import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.serena.mcp_server import SerenaV2MCPServer

@pytest.fixture
def mcp_server():
    server = SerenaV2MCPServer()
    # Mock workspace resolving to avoid filesystem issues
    server.workspace = "/Users/hue/code/dopemux-mvp"
    return server

@pytest.mark.asyncio
@patch('services.serena.mcp_server.UntrackedWorkDetector')
async def test_detect_enhanced_success_with_findings(MockDetector, mcp_server):
    # Setup mock detector
    mock_instance = MockDetector.return_value
    mock_instance.detect_with_enhancements = AsyncMock(return_value={
        "has_untracked_work": True,
        "work_name": "Test Work",
        "confidence_score": 0.9,
        "threshold_used": 0.5,
        "git_detection": {"files": ["a.py"], "branch": "main"},
        "enhancements": {}
    })
    
    # Mock ConPort client
    mcp_server.conport_client = MagicMock()
    mcp_server._ensure_conport_client = AsyncMock()
    
    result_str = await mcp_server.detect_untracked_work_enhanced_tool()
    result = json.loads(result_str)
    
    assert result["status"] == "LIVE"
    assert result["data_state"] == "available"
    assert result["provenance"]["degraded"] is False
    assert result["provenance"]["fallback_used"] is False
    assert result["result"]["status"] == "untracked_work_detected"
    assert result["authority"] == "serena"
    assert result["authority_role"] == "advisory"

@pytest.mark.asyncio
@patch('services.serena.mcp_server.UntrackedWorkDetector')
async def test_detect_enhanced_success_no_findings(MockDetector, mcp_server):
    # Setup mock detector
    mock_instance = MockDetector.return_value
    mock_instance.detect_with_enhancements = AsyncMock(return_value={
        "has_untracked_work": False,
        "confidence_score": 0.1,
        "threshold_used": 0.5
    })
    
    # Mock ConPort client
    mcp_server.conport_client = MagicMock()
    mcp_server._ensure_conport_client = AsyncMock()
    
    result_str = await mcp_server.detect_untracked_work_enhanced_tool()
    result = json.loads(result_str)
    
    assert result["status"] == "LIVE"
    assert result["data_state"] == "no_data"
    assert result["provenance"]["degraded"] is False
    assert result["result"]["status"] == "all_clear"

@pytest.mark.asyncio
@patch('services.serena.mcp_server.UntrackedWorkDetector')
async def test_detect_enhanced_conport_unavailable(MockDetector, mcp_server):
    # Setup mock detector
    mock_instance = MockDetector.return_value
    mock_instance.detect_with_enhancements = AsyncMock(return_value={
        "has_untracked_work": False,
        "confidence_score": 0.0,
        "threshold_used": 0.5
    })
    
    # ConPort is unavailable
    mcp_server.conport_client = None
    mcp_server._ensure_conport_client = AsyncMock()
    
    result_str = await mcp_server.detect_untracked_work_enhanced_tool()
    result = json.loads(result_str)
    
    assert result["status"] == "DEGRADED"
    assert result["data_state"] == "unavailable"
    assert result["provenance"]["degraded"] is True
    assert result["provenance"]["reason"] == "conport_unavailable"
    assert result["result"]["status"] == "all_clear"

@pytest.mark.asyncio
@patch('services.serena.mcp_server.UntrackedWorkDetector')
async def test_detect_enhanced_unknown_exception(MockDetector, mcp_server):
    # Setup mock detector to raise an exception
    mock_instance = MockDetector.return_value
    mock_instance.detect_with_enhancements.side_effect = RuntimeError("Database timeout")
    
    mcp_server.conport_client = MagicMock()
    mcp_server._ensure_conport_client = AsyncMock()
    
    result_str = await mcp_server.detect_untracked_work_enhanced_tool()
    result = json.loads(result_str)
    
    assert result["status"] == "DEGRADED"
    assert result["data_state"] == "unknown"
    assert result["provenance"]["degraded"] is True
    assert result["provenance"]["reason"] == "unknown_error"
    assert "error" in result["result"]

@pytest.mark.asyncio
@patch('services.serena.mcp_server.UntrackedWorkDetector')
async def test_detect_enhanced_no_write_actions(MockDetector, mcp_server):
    mock_instance = MockDetector.return_value
    mock_instance.detect_with_enhancements = AsyncMock(return_value={"has_untracked_work": False, "confidence_score": 0, "threshold_used": 0})
    mcp_server.conport_client = MagicMock()
    mcp_server._ensure_conport_client = AsyncMock()
    
    await mcp_server.detect_untracked_work_enhanced_tool()
    
    # Ensure no logging or writing was performed
    mcp_server.conport_client.log_custom_data.assert_not_called()
