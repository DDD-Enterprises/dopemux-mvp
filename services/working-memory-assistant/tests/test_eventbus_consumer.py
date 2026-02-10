"""Tests for EventBus consumer."""

import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from eventbus_consumer import EventBusConsumer


def _make_consumer(tmp_path, monkeypatch=None, **kwargs):
    """Create an EventBusConsumer with canonical ledger pointed at tmp_path."""
    ledger = tmp_path / "chronicle.sqlite"
    if monkeypatch:
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger))
    else:
        os.environ["DOPEMUX_CAPTURE_LEDGER_PATH"] = str(ledger)
    return EventBusConsumer(
        redis_url=kwargs.pop("redis_url", "redis://localhost:6379"),
        **kwargs,
    )


class TestEventBusConsumer:
    """Tests for EventBusConsumer class."""

    def test_consumer_init(self, tmp_path, monkeypatch):
        """Test consumer initialization with defaults."""
        consumer = _make_consumer(tmp_path, monkeypatch)
        assert consumer.redis_url == "redis://localhost:6379"
        assert consumer.input_stream == "activity.events.v1"
        assert consumer.output_stream == "memory.derived.v1"
        assert consumer.consumer_group == "dope-memory-ingestor"
        assert consumer._running is False

    def test_consumer_custom_streams(self, tmp_path, monkeypatch):
        """Test consumer with custom stream names."""
        consumer = _make_consumer(
            tmp_path,
            monkeypatch,
            input_stream="custom.input.v1",
            output_stream="custom.output.v1",
            consumer_group="custom-group",
        )
        assert consumer.input_stream == "custom.input.v1"
        assert consumer.output_stream == "custom.output.v1"
        assert consumer.consumer_group == "custom-group"

    def test_parse_event_basic(self, tmp_path, monkeypatch):
        """Test parsing a basic event from Redis message."""
        consumer = _make_consumer(tmp_path, monkeypatch)

        msg_data = {
            b"id": b"event-123",
            b"ts": b"2026-02-02T10:00:00Z",
            b"workspace_id": b"test-ws",
            b"instance_id": b"A",
            b"type": b"decision.logged",
            b"source": b"test-source",
            b"data": json.dumps({"title": "Test Decision"}).encode(),
        }

        event = consumer._parse_event(msg_data)

        assert event["id"] == "event-123"
        assert event["ts"] == "2026-02-02T10:00:00Z"
        assert event["workspace_id"] == "test-ws"
        assert event["instance_id"] == "A"
        assert event["type"] == "decision.logged"
        assert event["source"] == "test-source"
        assert event["data"]["title"] == "Test Decision"

    def test_parse_event_legacy_event_type(self, tmp_path, monkeypatch):
        """Test parsing event with legacy event_type field."""
        consumer = _make_consumer(tmp_path, monkeypatch)

        msg_data = {
            b"event_type": b"task.completed",
            b"timestamp": b"2026-02-02T10:00:00Z",
            b"source": b"dopecon-bridge",
            b"data": json.dumps({"task_id": "task-1"}).encode(),
        }

        event = consumer._parse_event(msg_data)

        assert event["type"] == "task.completed"
        assert event["event_type"] == "task.completed"

    def test_get_store_creates_canonical_ledger(self, tmp_path, monkeypatch):
        """Test that get_store creates the canonical ledger."""
        ledger = tmp_path / "chronicle.sqlite"
        monkeypatch.setenv("DOPEMUX_CAPTURE_LEDGER_PATH", str(ledger))
        consumer = _make_consumer(tmp_path, monkeypatch)

        store = consumer._get_store("new-workspace")

        assert store is not None
        assert ledger.exists()

    def test_get_store_reuses_existing(self, tmp_path, monkeypatch):
        """Test that get_store reuses existing store."""
        consumer = _make_consumer(tmp_path, monkeypatch)

        store1 = consumer._get_store("workspace-1")
        store2 = consumer._get_store("workspace-1")

        assert store1 is store2


class TestEventBusConsumerIntegration:
    """Integration tests that verify end-to-end processing."""

    @pytest.mark.asyncio
    async def test_process_decision_logged_event(self, tmp_path, monkeypatch):
        """Test processing a decision.logged event end-to-end."""
        consumer = _make_consumer(tmp_path, monkeypatch)

        # Mock the derived event publishing (no Redis connection)
        consumer.redis_client = AsyncMock()

        msg_data = {
            b"id": b"event-decision-1",
            b"ts": b"2026-02-02T10:00:00Z",
            b"workspace_id": b"test-ws",
            b"instance_id": b"A",
            b"type": b"decision.logged",
            b"source": b"dopequery",
            b"data": json.dumps({
                "decision_id": "d-123",
                "title": "Use SQLite for local storage",
                "choice": "SQLite",
                "rationale": "Simple, embedded, and sufficient for single-user",
            }).encode(),
        }

        await consumer._process_message(b"msg-1", msg_data)

        # Verify raw event was stored
        store = consumer._get_store("test-ws")
        # Query to verify the entry was created
        entries = store.search_work_log(
            workspace_id="test-ws",
            instance_id="A",
            query="SQLite",
            limit=10,
        )

        assert len(entries) >= 1
        assert "SQLite" in entries[0]["summary"]

    @pytest.mark.asyncio
    async def test_process_unpromoted_event(self, tmp_path, monkeypatch):
        """Test processing an event that should not be promoted."""
        consumer = _make_consumer(tmp_path, monkeypatch)

        consumer.redis_client = AsyncMock()

        # file.created events are raw-only, not promoted
        msg_data = {
            b"id": b"event-file-1",
            b"ts": b"2026-02-02T10:00:00Z",
            b"workspace_id": b"test-ws",
            b"instance_id": b"A",
            b"type": b"file.created",
            b"source": b"watcher",
            b"data": json.dumps({"path": "/src/main.py"}).encode(),
        }

        await consumer._process_message(b"msg-2", msg_data)

        # Raw event should be stored, but no work log entry
        store = consumer._get_store("test-ws")
        entries = store.search_work_log(
            workspace_id="test-ws",
            instance_id="A",
            limit=10,
        )

        # Should not find any file.created entries in work log
        file_entries = [e for e in entries if "main.py" in str(e)]
        assert len(file_entries) == 0

    @pytest.mark.asyncio
    async def test_publish_derived_event(self, tmp_path, monkeypatch):
        """Test publishing derived events to output stream."""
        consumer = _make_consumer(tmp_path, monkeypatch)

        mock_redis = AsyncMock()
        mock_redis.xadd.return_value = b"1234567890-0"
        consumer.redis_client = mock_redis

        await consumer._publish_derived_event(
            event_type="worklog.created",
            data={"entry_id": "entry-123", "category": "decision"},
            workspace_id="test-ws",
            instance_id="A",
        )

        # Verify xadd was called
        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == "memory.derived.v1"
