"""Tests for normalized PM-plane chronicle contract."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from dopemux.pm.chronicle import (
    pm_get_work_chronicle,
    pm_append_work_chronicle,
    pm_correct_work_chronicle,
    _adapter
)
from dopemux.pm.chronicle_models import PMChronicleReadResult, PMChronicleWriteReceipt

@pytest.fixture
def mock_adapter(monkeypatch):
    adapter_mock = AsyncMock()
    monkeypatch.setattr("dopemux.pm.chronicle._adapter", adapter_mock)
    return adapter_mock

@pytest.mark.asyncio
async def test_pm_get_work_chronicle_success(mock_adapter):
    """Test successful chronicle read resolves to dope-memory and preserves shape."""
    mock_adapter.search_chronicle.return_value = {
        "items": [
            {"id": "entry-1", "summary": "test1"},
            {"id": "entry-2", "summary": "test2"}
        ],
        "more_count": 5,
        "next_token": "token123"
    }

    result = await pm_get_work_chronicle(
        workspace_id="ws-1",
        canonical_id="task-1",
        linked_ids={"leantime": "lt-1"}
    )

    assert isinstance(result, PMChronicleReadResult)
    assert result.canonical_backend == "dope-memory"
    assert result.canonical_id == "task-1"
    assert result.linked_ids == {"leantime": "lt-1"}
    assert result.more_count == 5
    assert result.next_token == "token123"
    assert len(result.items) == 2
    
    # Provenance
    assert result.provenance.source == "dope-memory"
    assert result.provenance.query_mode == "work_chronicle"
    assert result.provenance.workspace_id == "ws-1"
    
    # Supporting sources
    assert len(result.supporting_sources) == 1
    assert result.supporting_sources[0].backend == "dope-memory"
    assert result.supporting_sources[0].entry_ids == ["entry-1", "entry-2"]
    
    mock_adapter.search_chronicle.assert_called_once_with(
        workspace_id="ws-1",
        session_id=None,
        category=None,
        entry_type=None,
        tags_any=None,
        time_range="week",
        top_k=3,
        cursor=None
    )

@pytest.mark.asyncio
async def test_pm_get_work_chronicle_fail_closed(mock_adapter):
    """Test read fails closed when backend is unavailable."""
    mock_adapter.search_chronicle.side_effect = httpx.HTTPError("Backend down")
    
    result = await pm_get_work_chronicle(
        workspace_id="ws-1",
        canonical_id="task-1"
    )
    
    assert isinstance(result, PMChronicleReadResult)
    assert len(result.items) == 0
    assert result.more_count == 0
    assert result.canonical_backend == "dope-memory"
    assert result.supporting_sources[0].entry_ids == []

@pytest.mark.asyncio
async def test_pm_append_work_chronicle_success(mock_adapter):
    """Test successful append."""
    mock_adapter.append_chronicle.return_value = {
        "success": True,
        "entry_id": "new-entry-1"
    }
    
    result = await pm_append_work_chronicle(
        workspace_id="ws-1",
        canonical_id="task-1",
        linked_ids={"leantime": "lt-1"},
        entry_type="task.completed",
        summary="Task was done",
        idempotency_key="idemp-1"
    )
    
    assert isinstance(result, PMChronicleWriteReceipt)
    assert result.success is True
    assert result.canonical_backend == "dope-memory"
    assert result.entry_id == "new-entry-1"
    
    mock_adapter.append_chronicle.assert_called_once()
    kwargs = mock_adapter.append_chronicle.call_args.kwargs
    assert kwargs["workspace_id"] == "ws-1"
    assert kwargs["entry_type"] == "task.completed"
    assert kwargs["summary"] == "Task was done"
    assert kwargs["idempotency_key"] == "idemp-1"
    assert kwargs["links"]["pm_canonical"] == "task-1"
    assert kwargs["links"]["leantime"] == "lt-1"

@pytest.mark.asyncio
async def test_pm_append_work_chronicle_fail_closed(mock_adapter):
    """Test append fails gracefully."""
    mock_adapter.append_chronicle.side_effect = httpx.HTTPError("Backend down")
    
    result = await pm_append_work_chronicle(
        workspace_id="ws-1",
        canonical_id="task-1",
        linked_ids={},
        entry_type="task.completed",
        summary="Task was done",
        idempotency_key="idemp-1"
    )
    
    assert result.success is False
    assert result.entry_id == "unknown"

@pytest.mark.asyncio
async def test_pm_correct_work_chronicle_success(mock_adapter):
    """Test successful correct."""
    mock_adapter.correct_chronicle.return_value = {
        "success": True,
        "entry_id": "new-corrected-entry"
    }
    
    result = await pm_correct_work_chronicle(
        workspace_id="ws-1",
        canonical_id="task-1",
        chronicle_entry_id="old-entry",
        correction_reason="Typo",
        corrected_summary="Fixed typo",
        idempotency_key="idemp-2"
    )
    
    assert isinstance(result, PMChronicleWriteReceipt)
    assert result.success is True
    assert result.entry_id == "new-corrected-entry"
    
    mock_adapter.correct_chronicle.assert_called_once_with(
        workspace_id="ws-1",
        entry_id="old-entry",
        correction_type="summary",
        corrected_summary="Fixed typo",
        corrected_tags=None,
        idempotency_key="idemp-2"
    )

@pytest.mark.asyncio
async def test_pm_correct_work_chronicle_fallback(mock_adapter, monkeypatch):
    """Test fallback to append when correct returns 404."""
    # We need to simulate HTTPStatusError with status 404
    mock_response = MagicMock(status_code=404)
    mock_adapter.correct_chronicle.side_effect = httpx.HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
    mock_adapter.append_chronicle.return_value = {
        "success": True,
        "entry_id": "fallback-entry"
    }

    result = await pm_correct_work_chronicle(
        workspace_id="ws-1",
        canonical_id="task-1",
        chronicle_entry_id="old-entry",
        correction_reason="Typo",
        corrected_summary="Fixed typo",
        idempotency_key="idemp-3"
    )

    assert result.success is True
    assert result.entry_id == "fallback-entry"
    mock_adapter.append_chronicle.assert_called_once()
    kwargs = mock_adapter.append_chronicle.call_args.kwargs
    assert kwargs["entry_type"] == "correction"
    assert kwargs["details"]["superseded_entry_id"] == "old-entry"
