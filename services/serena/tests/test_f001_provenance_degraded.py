"""
MIGRATION NOTE:
The enhanced F001 MCP payload shape has changed to include a top-level provenance envelope.
- The old flat payload (e.g. status: "all_clear") is now nested under the `result` key.
- The new top-level `status` is the envelope status: LIVE, DEGRADED, UNKNOWN, BLOCKED, or NOT_PROBED.
- Legacy fields remain available under `result` for backward compatibility.
"""

import sys
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.serena.mcp_server import SerenaV2MCPServer

@pytest.fixture
def mcp_server(tmp_path):
    server = SerenaV2MCPServer()
    server.workspace = str(tmp_path)
    return server

@pytest.fixture
def mock_conport_failing_module():
    mock_module = MagicMock()
    mock_class = MagicMock()
    mock_instance = AsyncMock()
    # Simulate ConnectionError during connect
    mock_instance.connect.side_effect = ConnectionError("Simulated connection error")
    mock_class.return_value = mock_instance
    mock_module.ConPortDBClient = mock_class

    sys.modules['conport_client_unified'] = mock_module
    yield mock_instance
    if 'conport_client_unified' in sys.modules:
        del sys.modules['conport_client_unified']

@pytest.mark.asyncio
@patch('services.serena.untracked_work_detector.UntrackedWorkDetector')
async def test_detect_enhanced_success_with_findings(MockDetector, mcp_server):
    mock_instance = MockDetector.return_value
    mock_instance.detect_with_enhancements = AsyncMock(return_value={
        "has_untracked_work": True,
        "work_name": "Test Work",
        "confidence_score": 0.9,
        "threshold_used": 0.5,
        "git_detection": {"files": ["a.py"], "branch": "main"},
        "detection_signals": [],
        "enhancements": {}
    })

    mcp_server.conport_client = MagicMock()
    mcp_server._ensure_conport_client = AsyncMock()

    result_str = await mcp_server.detect_untracked_work_enhanced_tool()
    result = json.loads(result_str)

    assert result["status"] == "LIVE"
    assert result["data_state"] == "available"
    assert result["provenance"]["degraded"] is False
    assert result["result"]["status"] == "untracked_work_detected"

@pytest.mark.asyncio
@patch('services.serena.untracked_work_detector.UntrackedWorkDetector')
async def test_detect_enhanced_success_no_findings(MockDetector, mcp_server):
    mock_instance = MockDetector.return_value
    mock_instance.detect_with_enhancements = AsyncMock(return_value={
        "has_untracked_work": False,
        "confidence_score": 0.1,
        "threshold_used": 0.5
    })

    mcp_server.conport_client = MagicMock()
    mcp_server._ensure_conport_client = AsyncMock()

    result_str = await mcp_server.detect_untracked_work_enhanced_tool()
    result = json.loads(result_str)

    assert result["status"] == "LIVE"
    assert result["data_state"] == "no_data"
    assert result["provenance"]["degraded"] is False
    assert result["result"]["status"] == "all_clear"

@pytest.mark.asyncio
@patch('services.serena.untracked_work_detector.UntrackedWorkDetector')
async def test_detect_enhanced_conport_connect_failure(MockDetector, mcp_server, mock_conport_failing_module):
    mock_instance = MockDetector.return_value
    mock_instance.detect_with_enhancements = AsyncMock(return_value={
        "has_untracked_work": False,
        "confidence_score": 0.0,
        "threshold_used": 0.5
    })

    # We do NOT mock _ensure_conport_client here, so it executes and fails
    result_str = await mcp_server.detect_untracked_work_enhanced_tool()
    result = json.loads(result_str)

    # Assert conport_client was nullified
    assert mcp_server.conport_client is None

    # Assert degraded state
    assert result["status"] == "DEGRADED"
    assert result["data_state"] == "unavailable"
    assert result["provenance"]["degraded"] is True
    assert result["provenance"]["reason"] == "conport_unavailable"
    assert result["result"]["status"] == "all_clear"

@pytest.mark.asyncio
@patch('services.serena.untracked_work_detector.UntrackedWorkDetector')
async def test_detect_enhanced_unknown_exception(MockDetector, mcp_server):
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
@patch('services.serena.untracked_work_detector.UntrackedWorkDetector')
async def test_detect_enhanced_conport_query_failure(MockDetector, mcp_server):
    mock_instance = MockDetector.return_value
    
    # We simulate that detector calls some method on conport_client which fails
    async def side_effect_detect(conport_client=None, session_number=1):
        if conport_client:
            # Simulate the detector calling a client method that fails
            await conport_client.get_tasks()
        return {
            "has_untracked_work": False,
            "confidence_score": 0.0,
            "threshold_used": 0.5
        }
        
    mock_instance.detect_with_enhancements = AsyncMock(side_effect=side_effect_detect)
    
    # Mock ConPort client so it raises an exception when get_tasks is called
    mcp_server.conport_client = MagicMock()
    mcp_server.conport_client.get_tasks = AsyncMock(side_effect=RuntimeError("Query failed"))
    mcp_server._ensure_conport_client = AsyncMock()
    
    result_str = await mcp_server.detect_untracked_work_enhanced_tool()
    result = json.loads(result_str)
    
    # Assert degraded state because the query failed
    assert result["status"] == "DEGRADED"
    assert result["data_state"] == "unavailable"
    assert result["provenance"]["degraded"] is True
    assert result["provenance"]["reason"] == "conport_unavailable"
